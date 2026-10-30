"""Linux-only locked, atomic state store. No external AI or scheduler is invoked."""
import copy
import fcntl
import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT/'automation/state.schema.json').read_text())
REVIEW_SCHEMA = json.loads((ROOT/'automation/review.schema.json').read_text())

def now(): return datetime.now(timezone.utc).isoformat()
def canonical(value): return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def digest(value): return hashlib.sha256(canonical(value)).hexdigest()
def initial(cycle_id='setup-000', task='環境構築のみ。研究開始は未承認。', approved=False):
    return dict(schema_version=1,revision=0,cycle_id=cycle_id,status='pending',started_at=None,ended_at=None,task=task,instruction_approved=approved,results=[],review=None,report=None,history=[])

def validate(s):
    Draft202012Validator(SCHEMA,format_checker=FormatChecker()).validate(s)
    status=s['status']
    if status!='pending' and not s['started_at']: raise ValueError('start time required')
    if status in ('completed','awaiting_review','reviewed','failed') and not s['ended_at']: raise ValueError('end time required')
    if status in ('awaiting_review','reviewed'):
        r=s['report']
        if not r or set(r)!={'revision','payload','sha256'}: raise ValueError('invalid report')
        if r['sha256']!=digest(r['payload']): raise ValueError('report hash mismatch')
        expected={k:s[k] for k in ('cycle_id','task','started_at','ended_at','results')}
        if r['payload']!=expected or r['revision']>s['revision']: raise ValueError('report does not match state')
    if status=='reviewed':
        r=s['review']
        if not r or r['cycle_id']!=s['cycle_id'] or r['report_sha256']!=s['report']['sha256'] or r['report_revision']!=s['report']['revision']: raise ValueError('review binding mismatch')
    elif s['review'] is not None: raise ValueError('review only allowed in reviewed state')
    seen={s['cycle_id']}
    for previous in s['history']:
        record={**previous,'history':[]}
        validate(record)
        if record['cycle_id'] in seen: raise ValueError('duplicate historical cycle')
        seen.add(record['cycle_id'])
    if status=='pending' and (s['started_at'] or s['ended_at'] or s['results'] or s['report']): raise ValueError('pending state must be empty')
    if status=='running' and s['ended_at']: raise ValueError('running cycle cannot have ended')
    return s

def atomic_json(path,value):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.'+path.name+'.',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f: f.write(canonical(value)+b'\n'); f.flush(); os.fsync(f.fileno())
        os.replace(name,path)
        d=os.open(path.parent,os.O_DIRECTORY)
        try: os.fsync(d)
        finally: os.close(d)
    finally:
        if os.path.exists(name): os.unlink(name)

class Store:
    def __init__(self,path): self.path=Path(path)
    @contextmanager
    def lock(self,worker=False):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with open(str(self.path)+('.worker.lock' if worker else '.lock'),'a') as f:
            try: fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError: raise RuntimeError('another process owns the lock') from None
            try: yield
            finally: fcntl.flock(f,fcntl.LOCK_UN)
    def read(self): return validate(json.loads(self.path.read_text()))
    def create(self,s):
        with self.lock():
            if self.path.exists(): raise FileExistsError(self.path)
            validate(s); atomic_json(self.path,s)
    def update(self,expected_revision,mutate):
        with self.lock():
            old=self.read()
            if old['revision']!=expected_revision: raise ValueError('stale revision')
            s=copy.deepcopy(old); mutate(s); s['revision']+=1; validate(s)
            atomic_json(str(self.path)+'.bak',old)
            atomic_json(self.path,s)
            return s
    def begin(self,revision):
        def mutate(s):
            if s['status']!='pending' or not s['instruction_approved']: raise ValueError('approved pending instruction required')
            s.update(status='running',started_at=now())
        return self.update(revision,mutate)
    def complete(self,revision,results):
        def mutate(s):
            if s['status']!='running': raise ValueError('not running')
            s.update(status='completed',ended_at=now(),results=json.loads(json.dumps(results,allow_nan=False)))
        return self.update(revision,mutate)
    def submit(self,revision):
        def mutate(s):
            if s['status']!='completed': raise ValueError('not completed')
            payload={k:s[k] for k in ('cycle_id','task','started_at','ended_at','results')}
            s.update(status='awaiting_review',report=dict(revision=s['revision']+1,payload=payload,sha256=digest(payload)))
        return self.update(revision,mutate)
    def review(self,revision,review):
        Draft202012Validator(REVIEW_SCHEMA).validate(review)
        def mutate(s):
            if s['status']!='awaiting_review': raise ValueError('not awaiting review')
            if (review['cycle_id'],review['report_sha256'],review['report_revision'])!=(s['cycle_id'],s['report']['sha256'],s['report']['revision']): raise ValueError('stale or mismatched review')
            s.update(status='reviewed',review=review)
        return self.update(revision,mutate)
    def next_cycle(self,revision,cycle_id):
        def mutate(s):
            if s['status']!='reviewed' or s['review']['verdict']!='accepted' or not s['review']['next_instruction']: raise ValueError('accepted next instruction required')
            used={h['cycle_id'] for h in s['history']}|{s['cycle_id']}
            if cycle_id in used: raise ValueError('duplicate cycle id')
            old=copy.deepcopy(s); old.pop('history')
            history=s['history']+[old]
            fresh=initial(cycle_id,s['review']['next_instruction'],True)
            fresh.update(history=history,revision=s['revision']); s.clear(); s.update(fresh)
        return self.update(revision,mutate)
    def recover(self,revision):
        # Must also own the worker lock: never mark an active conforming worker failed.
        with self.lock(worker=True):
            def mutate(s):
                if s['status']!='running': raise ValueError('only interrupted running cycles can be recovered')
                s.update(status='failed',ended_at=now())
                s['results'].append(dict(kind='failure',claim='Interrupted worker; manual diagnosis required',verification='unreviewed',data={}))
            return self.update(revision,mutate)
    def restore_backup(self):
        # Explicit operator recovery; never silently fall back from corrupt state.
        with self.lock(worker=True),self.lock():
            try: self.read()
            except (ValueError,KeyError,TypeError): pass
            else: raise ValueError('valid primary must not be overwritten')
            backup=validate(json.loads(Path(str(self.path)+'.bak').read_text()))
            raw=self.path.read_bytes()
            evidence=self.path.with_name(self.path.name+'.corrupt-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
            with evidence.open('xb') as f: f.write(raw); f.flush(); os.fsync(f.fileno())
            # Backup may predate a committed begin/review: fail closed, never replay.
            backup.update(status='failed',started_at=backup['started_at'] or now(),ended_at=now(),review=None,report=None,instruction_approved=False,revision=backup['revision']+1)
            backup['results'].append(dict(kind='failure',claim='Restored backup; primary corruption preserved; manual reconciliation required',verification='unreviewed',data={'evidence_file':evidence.name}))
            validate(backup); atomic_json(self.path,backup)
            return backup

def confirmed_results(s):
    validate(s)
    if s['status']!='reviewed' or s['review']['verdict']!='accepted': return []
    return [r for r in s['results'] if r['kind']=='lemma' and r['verification']=='lean_kernel']
