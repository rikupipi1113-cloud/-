"""V2 append-only journal, content-addressed evidence and fail-closed projection.
V1 Store is deliberately untouched. File owners are trusted; hashes are not signatures.
"""
import copy
import fcntl
import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from jsonschema import Draft202012Validator, FormatChecker
from .state import atomic_json, canonical, digest

KINDS = ['lemma','hypothesis','failed_approach','experiment','prior_work','open_problem','instruction','review']
STATUSES = ['pending','running','completed','awaiting_review','reviewed','failed']
HEX = re.compile(r'^[a-f0-9]{64}$')

class Blocked(ValueError): pass

def utc(): return datetime.now(timezone.utc)
def stamp(): return utc().isoformat()
def moment(value):
    d=datetime.fromisoformat(value)
    if d.tzinfo is None: raise Blocked('timezone required')
    return d

def read_json(path):
    def constant(v): raise Blocked('non-finite JSON: '+v)
    return json.loads(Path(path).read_text(),parse_constant=constant)

def exclusive_file(path, data):
    """Publish complete file without replacing any existing pathname."""
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f: f.write(data); f.flush(); os.fsync(f.fileno())
        os.link(name,path)
        d=os.open(path.parent,os.O_DIRECTORY)
        try: os.fsync(d)
        finally: os.close(d)
    finally: os.unlink(name)

class Memory:
    def __init__(self,root): self.root=Path(root)
    @contextmanager
    def lock(self, name='journal'):
        self.root.mkdir(parents=True,exist_ok=True)
        with (self.root/(name+'.lock')).open('a') as f:
            try: fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError: raise Blocked('busy: '+name) from None
            try: yield
            finally: fcntl.flock(f,fcntl.LOCK_UN)
    def blob(self,text):
        raw=text.encode(); key=hashlib.sha256(raw).hexdigest(); path=self.root/'objects'/key
        try: exclusive_file(path,raw)
        except FileExistsError:
            if path.read_bytes()!=raw: raise Blocked('object collision/corruption')
        return key
    def text(self,key):
        if not isinstance(key,str) or not HEX.fullmatch(key): raise Blocked('invalid object id')
        data=(self.root/'objects'/key).read_bytes()
        if hashlib.sha256(data).hexdigest()!=key: raise Blocked('corrupt object: '+key)
        return data.decode()
    def schema(self,name):
        return read_json(Path(__file__).resolve().parents[2]/'automation/stage2'/name)
    def validate(self,s):
        Draft202012Validator(self.schema('memory.schema.json'),format_checker=FormatChecker()).validate(s)
        canonical(s)
        ids=set()
        for r in s['records']:
            if r['id'] in ids: raise Blocked('duplicate record id')
            if r['supersedes'] is not None and r['supersedes'] not in ids: raise Blocked('unknown superseded record')
            ids.add(r['id']); self.text(r['body'])
            for key in r['evidence'].values(): self.text(key)
        for c in s['cycles']:
            if len(set(c['inherited_ids']))!=len(c['inherited_ids']): raise Blocked('duplicate inherited ids')
            for key in ('report','review','checkpoint','instruction'):
                if c[key]: self.text(c[key])
        for key in ('instruction',):
            if s[key]: self.text(s[key])
        if len({c['id'] for c in s['cycles']})!=len(s['cycles']): raise Blocked('duplicate cycle id')
        if s['cycles'] and s['status']!=s['cycles'][-1]['status']: raise Blocked('cycle/state status mismatch')
        if s['slots']!=[c['slot'] for c in s['cycles']]: raise Blocked('slot history mismatch')
        for c in s['cycles']:
            moment(c['started_at']);moment(c['deadline']);moment(c['slot'])
            if c['ended_at']: moment(c['ended_at'])
        return s
    def replay(self):
        events=sorted((self.root/'events').glob('*.json'))
        if not events: raise Blocked('journal missing')
        previous=None; state=None; seen_ids=set()
        for seq,path in enumerate(events,1):
            if path.name!=f'{seq:08d}.json': raise Blocked('journal gap')
            event=read_json(path)
            if set(event)!={'seq','previous','operation','time','state','sha256'}: raise Blocked('event shape')
            body={k:v for k,v in event.items() if k!='sha256'}
            if event['seq']!=seq or event['previous']!=previous or digest(body)!=event['sha256']: raise Blocked('journal hash mismatch')
            moment(event['time']); state=self.validate(event['state'])
            if state['revision']!=seq: raise Blocked('revision mismatch')
            current_ids={r['id'] for r in state['records']}
            if not seen_ids<=current_ids: raise Blocked('record removed from journal')
            if seq>1:
                if state['records'][:len(old['records'])]!=old['records']: raise Blocked('record overwritten')
                frozen=len(old['cycles']) if len(state['cycles'])>len(old['cycles']) else max(0,len(old['cycles'])-1)
                if state['cycles'][:frozen]!=old['cycles'][:frozen]: raise Blocked('closed cycle overwritten')
                if len(state['cycles'])<len(old['cycles']): raise Blocked('cycle deleted')
            old=copy.deepcopy(state); seen_ids=current_ids;previous=event['sha256']
        return dict(head=previous,state=state)
    def load(self):
        expected=self.replay()
        if read_json(self.root/'latest.json')!=expected: raise Blocked('projection differs from journal; explicit repair required')
        return expected
    def _commit(self,old,operation,state):
        state['revision']=(old['state']['revision'] if old else 0)+1
        self.validate(state)
        event=dict(seq=state['revision'],previous=old['head'] if old else None,operation=operation,time=stamp(),state=state)
        event['sha256']=digest(event)
        exclusive_file(self.root/'events'/f"{state['revision']:08d}.json",canonical(event)+b'\n')
        current=dict(head=event['sha256'],state=state)
        atomic_json(self.root/'latest.json',current)
        return current
    def initialize(self,mode='production',task='Initial research instruction is not approved'):
        if mode not in ('mock','production'): raise Blocked('invalid mode')
        with self.lock():
            if (self.root/'latest.json').exists() or list((self.root/'events').glob('*.json')): raise Blocked('memory already exists')
            instruction=self.blob(task)
            s=dict(schema_version=2,revision=0,mode=mode,status='pending',instruction=instruction,bootstrap_approved=(mode=='mock'),cycles=[],records=[],slots=[])
            return self._commit(None,'initialize',s)
    def change(self,revision,operation,mutate):
        with self.lock():
            old=self.load()
            if old['state']['revision']!=revision: raise Blocked('update conflict')
            s=copy.deepcopy(old['state']); mutate(s,old)
            return self._commit(old,operation,s)
    def repair_projection(self):
        with self.lock('worker'),self.lock():
            recovered=self.replay()
            path=self.root/'latest.json'
            if path.exists():
                raw=path.read_bytes()
                exclusive_file(self.root/'quarantine'/('latest-'+hashlib.sha256(raw).hexdigest()+'.json'),raw)
            atomic_json(path,recovered)
            return recovered
    def context(self):
        current=self.load(); s=current['state']
        # Includes ALL versions, unresolved claims and failures, never just a summary.
        context=dict(memory_head=current['head'],revision=s['revision'],mode=s['mode'],status=s['status'],
                     instruction=self.text(s['instruction']),cycles=s['cycles'],cycle_bodies=[{key:self.text(c[key]) if c[key] else None for key in ('report','review','checkpoint','instruction')} for c in s['cycles']],
                     records=[{**r,'text':self.text(r['body']),'evidence_text':{k:self.text(v) for k,v in r['evidence'].items()}} for r in s['records']])
        context['context_sha256']=digest(context)
        return context
    def handoff(self):
        c=self.context()
        return dict(protocol=2,memory_head=c['memory_head'],context_sha256=c['context_sha256'],instruction_sha256=digest(c['instruction']),last_review=c['cycles'][-1]['review'] if c['cycles'] else None)
    def start(self,revision,slot,cycle_id,transport,ack,at=None,deadline_at=None):
        at=at or utc()
        def mutate(s,old):
            if s['status'] not in ('pending','reviewed'): raise Blocked('previous work or review is incomplete')
            if s['cycles']:
                last=s['cycles'][-1]
                if last['status']!='reviewed' or not last['review']: raise Blocked('review missing')
                review=json.loads(self.text(last['review']))
                if review['verdict']!='accepted' or not review['next_instruction']: raise Blocked('next instruction not approved')
                if s['instruction']!=review['next_instruction']: raise Blocked('instruction mismatch')
            elif not s['bootstrap_approved']: raise Blocked('initial instruction not approved')
            if slot in s['slots'] or any(c['id']==cycle_id for c in s['cycles']): raise Blocked('duplicate slot/cycle')
            if not re.fullmatch(r'[A-Za-z0-9_-]+',cycle_id): raise Blocked('invalid cycle id')
            c=self.context()
            if ack!=c['context_sha256']: raise Blocked('inheritance acknowledgement mismatch')
            receipt=transport.read_handoff()
            if receipt['handoff']!=self.handoff(): raise Blocked('shared memory not synchronized')
            if s['mode']=='production':
                # Disabled until an actual reviewer round trip and initial approval are proven.
                raise Blocked('production integration has not been approved')
            deadline=(deadline_at or at+timedelta(hours=5)).isoformat()
            cycle=dict(id=cycle_id,slot=slot,status='running',started_at=at.isoformat(),ended_at=None,deadline=deadline,
                       inherited_head=old['head'],inherited_ids=[r['id'] for r in s['records']],context_sha256=ack,
                       sync_commit=receipt['commit'],instruction=s['instruction'],report=None,review=None,checkpoint=None,paused=False)
            s['cycles'].append(cycle); s['slots'].append(slot);s['status']='running'
        return self.change(revision,'start',mutate)
    def add_record(self,revision,kind,title,text,evidence=None,supersedes=None):
        if kind not in KINDS: raise Blocked('unknown kind')
        def mutate(s,old):
            if s['status']!='running' or s['cycles'][-1]['paused']: raise Blocked('research is not running')
            body=self.blob(text); ev={k:self.blob(v) for k,v in (evidence or {}).items()}
            if kind=='lemma':
                if not {'proof','lean_log','toolchain'}<=set(ev): raise Blocked('lemma evidence missing')
                if re.search(r'\b(sorry|admit|axiom)\b',evidence['proof']) or 'sorryAx' in evidence['lean_log']: raise Blocked('incomplete formal proof')
                if 'Build completed successfully' not in evidence['lean_log']: raise Blocked('successful Lean log required')
            r=dict(id=f"record-{len(s['records'])+1:06d}",cycle_id=s['cycles'][-1]['id'],kind=kind,title=title,body=body,
                   evidence=ev,supersedes=supersedes,verification='lean_kernel' if kind=='lemma' else 'unreviewed')
            s['records'].append(r)
        return self.change(revision,'record',mutate)
    def checkpoint(self,revision,progress,paused=False):
        def mutate(s,old):
            if s['status']!='running': raise Blocked('not running')
            s['cycles'][-1].update(checkpoint=self.blob(progress),paused=paused)
        return self.change(revision,'checkpoint',mutate)
    def resume(self,revision,ack,transport,at=None):
        at=at or utc()
        def mutate(s,old):
            if s['status']!='running' or not s['cycles'][-1]['paused']: raise Blocked('not paused')
            c=s['cycles'][-1]
            if at>=moment(c['deadline']): raise Blocked('research window expired')
            if self.context()['context_sha256']!=ack: raise Blocked('resume context mismatch')
            receipt=transport.read_handoff()
            if receipt['handoff']['memory_head']!=c['inherited_head'] or receipt['commit']!=c['sync_commit']: raise Blocked('shared parent changed')
            c['paused']=False
        return self.change(revision,'resume',mutate)
    def complete(self,revision,summary,at=None):
        at=at or utc()
        def mutate(s,old):
            if s['status']!='running' or s['cycles'][-1]['paused']: raise Blocked('not running')
            if at>moment(s['cycles'][-1]['deadline']): raise Blocked('research window expired; checkpoint/recover only')
            c=s['cycles'][-1]
            report=dict(cycle_id=c['id'],parent_head=c['inherited_head'],records=s['records'],summary=summary,finished_at=at.isoformat())
            c.update(report=self.blob(json.dumps(report,ensure_ascii=False,sort_keys=True)),ended_at=at.isoformat(),status='completed')
            s['status']='completed'
        return self.change(revision,'complete',mutate)
    def submit(self,revision):
        def mutate(s,old):
            if s['status']!='completed': raise Blocked('not completed')
            s['status']='awaiting_review';s['cycles'][-1]['status']='awaiting_review'
        return self.change(revision,'submit',mutate)
    def apply_review(self,revision,review,source_confirmed=False):
        Draft202012Validator(self.schema('review.schema.json'),format_checker=FormatChecker()).validate(review)
        def mutate(s,old):
            if not source_confirmed: raise Blocked('review source not confirmed')
            if s['status']!='awaiting_review': raise Blocked('not awaiting review')
            c=s['cycles'][-1]
            if (review['cycle_id'],review['report_sha256'],review['memory_head'])!=(c['id'],c['report'],old['head']): raise Blocked('stale review')
            if (s['mode']=='mock')!=(review['reviewer_kind']=='mock'): raise Blocked('mock/production boundary')
            eligible={r['id'] for r in s['records'] if r['kind']=='lemma' and r['verification']=='lean_kernel'}
            if not set(review['accepted_lemma_ids'])<=eligible: raise Blocked('hypothesis or experiment cannot be promoted to lemma')
            raw=copy.deepcopy(review)
            if raw['next_instruction']: raw['next_instruction']=self.blob(raw['next_instruction'])
            c.update(review=self.blob(json.dumps(raw,ensure_ascii=False,sort_keys=True)),status='reviewed');s['status']='reviewed'
            if raw['next_instruction']: s['instruction']=raw['next_instruction']
        return self.change(revision,'review',mutate)
    def confirmed(self):
        s=self.load()['state']; accepted=set()
        for c in s['cycles']:
            if c['status']=='reviewed' and c['review']:
                r=json.loads(self.text(c['review']))
                if r['verdict']=='accepted': accepted.update(r['accepted_lemma_ids'])
        superseded={r['supersedes'] for r in s['records'] if r['supersedes']}
        return [r for r in s['records'] if r['id'] in accepted and r['id'] not in superseded]
    def recover(self,revision,reason='Interrupted worker; manual reconciliation required'):
        with self.lock('worker'):
            def mutate(s,old):
                if s['status']!='running': raise Blocked('not running')
                c=s['cycles'][-1];c.update(status='failed',ended_at=stamp())
                body=self.blob(reason)
                s['records'].append(dict(id=f"record-{len(s['records'])+1:06d}",cycle_id=c['id'],kind='failed_approach',title='Worker interrupted',body=body,evidence={},supersedes=None,verification='unreviewed'))
                s['status']='failed'
            return self.change(revision,'recover',mutate)
