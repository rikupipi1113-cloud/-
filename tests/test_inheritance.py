import copy
import json
import os
import subprocess
import sys
from datetime import datetime,timedelta
from pathlib import Path
import pytest
from jsonschema.exceptions import ValidationError
from es_research.memory import Memory,Blocked
from es_research.exchange import GitExchange
from es_research.scheduler import dispatch,resume_session,review_ready,slot_for
from es_research.inheritance_demo import run,review_for
from es_research.bounded import run_bounded
from es_research.state import ROOT

AT=datetime.fromisoformat('2026-10-30T00:00:00+09:00')
CFG=dict(enabled=True,mode='mock',timezone='Asia/Tokyo')

@pytest.fixture
def lab(tmp_path):
    remote=tmp_path/'shared.git'
    subprocess.run(['git','init','--bare','-q',str(remote)],check=True)
    m=Memory(tmp_path/'memory');m.initialize('mock','MOCK initial fixture task')
    x=GitExchange(remote);x.publish_local(m,tmp_path)
    return m,x,tmp_path

def start(m,x,at=AT):
    return dispatch(m,CFG,x,m.context()['context_sha256'],at=at)

def submit(m,x):
    with start(m,x):
        m.add_record(m.load()['state']['revision'],'hypothesis','Not proved','Unverified question, not a theorem.')
        m.complete(m.load()['state']['revision'],'Mock finite fixture report',at=AT+timedelta(minutes=1))
        m.submit(m.load()['state']['revision'])
    return m.load()

def accept(m):
    return m.apply_review(m.load()['state']['revision'],review_for(m),source_confirmed=True)

def test_three_cycle_inheritance(tmp_path):
    s=run(tmp_path/'three')
    assert s['cycles']==3 and s['history_preserved'] and s['all_contexts_matched']
    m=Memory(tmp_path/'three/memory');context=m.context()
    assert len(context['cycles'])==3
    assert all(c['instruction'] for c in context['cycle_bodies'])
    assert all(len(c['inherited_ids'])>0 for c in context['cycles'][1:])
    assert any(r['kind']=='failed_approach' for r in context['records'])
    assert len([r for r in context['records'] if r['kind']=='open_problem'])==3
    assert len(m.replay()['state']['records'])==s['records']
    assert not m.confirmed()
    print(json.dumps(s))

def test_corrupt_projection_blocks_then_repairs_without_history_loss(lab):
    m,x,p=lab;submit(m,x);before=m.replay()
    (m.root/'latest.json').write_text('{broken')
    with pytest.raises(ValueError):m.load()
    with pytest.raises(ValueError):
        with dispatch(m,CFG,x,'0'*64,at=AT+timedelta(hours=6)):pass
    m.repair_projection();assert m.load()==before
    assert list((m.root/'quarantine').iterdir())
    print('corrupt projection: start refused; replay restored identical journal head')

def test_corrupt_journal_or_missing_evidence_stops(lab):
    m,x,p=lab
    event=next((m.root/'events').glob('*.json'));raw=event.read_bytes();event.write_text('{}')
    with pytest.raises(Blocked):m.load()
    event.write_bytes(raw)
    key=m.load()['state']['instruction'];(m.root/'objects'/key).write_text('corrupt')
    with pytest.raises(Blocked):m.load()
    with pytest.raises(Blocked):m.repair_projection()
    print('corrupt journal/evidence: fail closed; no automatic fallback')

def test_committed_journal_interrupted_projection_is_not_replayed(lab,monkeypatch):
    m,x,p=lab
    import es_research.memory as module
    actual=module.atomic_json
    def interrupted(path,value):raise OSError('simulated crash after durable event')
    monkeypatch.setattr(module,'atomic_json',interrupted)
    with pytest.raises(OSError):
        with start(m,x):pass
    monkeypatch.setattr(module,'atomic_json',actual)
    with pytest.raises(Blocked):m.load()
    fixed=m.repair_projection();assert fixed['state']['status']=='running'
    with pytest.raises(Blocked):
        with start(m,x):pass
    print('post-journal crash: explicit repair retained started cycle; duplicate start blocked')

def test_stale_review_and_wrong_source(lab):
    m,x,p=lab;submit(m,x);r=review_for(m);rev=m.load()['state']['revision']
    for key,value in [('cycle_id','old-cycle'),('memory_head','0'*64),('report_sha256','0'*64)]:
        wrong={**r,key:value}
        with pytest.raises(Blocked):m.apply_review(rev,wrong,source_confirmed=True)
    with pytest.raises(Blocked):m.apply_review(rev,r)
    with pytest.raises(Blocked):m.apply_review(rev,{**r,'reviewer_kind':'chatgpt'},source_confirmed=True)
    m.apply_review(rev,r,source_confirmed=True)
    with pytest.raises(Blocked):m.apply_review(m.load()['state']['revision'],r,source_confirmed=True)
    print('old report/head/cycle, unconfirmed source, mock boundary and replayed review: refused')

def test_unfinished_chatgpt_review_blocks_next(lab):
    m,x,p=lab;submit(m,x);x.publish_local(m,p);before=m.load()
    with pytest.raises(Blocked):
        with start(m,x,AT+timedelta(hours=6)):pass
    assert m.load()==before and not m.confirmed()
    with pytest.raises(ValidationError):m.apply_review(before['state']['revision'],{'comments':'partial'},True)
    print('awaiting_review and partial review: next research blocked')

def test_duplicate_schedule_and_revision_conflict(lab):
    m,x,p=lab
    with start(m,x):
        with pytest.raises(Blocked):
            with start(m,x):pass
    revision=m.load()['state']['revision']
    m.checkpoint(revision,'progress')
    with pytest.raises(Blocked):m.checkpoint(revision,'stale progress')
    assert m.text(m.load()['state']['cycles'][-1]['checkpoint'])=='progress'
    print('duplicate worker lock and stale revision: refused; current checkpoint retained')

def test_same_slot_after_review_refused(lab):
    m,x,p=lab;submit(m,x);accept(m);x.publish_local(m,p)
    with pytest.raises(Blocked):
        with start(m,x):pass
    assert len(m.load()['state']['cycles'])==1
    print('reviewed cycle does not authorize duplicate schedule slot')

def test_sync_failure_blocks_before_mutation(lab):
    m,x,p=lab;submit(m,x);accept(m);before=m.load()
    missing=GitExchange(p/'missing.git',timeout=2)
    with pytest.raises(Blocked,match='sync failed'):
        with start(m,missing,AT+timedelta(hours=6)):pass
    assert m.load()==before
    with pytest.raises(Blocked,match='not synchronized'):
        with start(m,x,AT+timedelta(hours=6)):pass
    assert m.load()==before
    print('unreachable and stale shared repository: start refused without journal update')

def test_context_ack_must_cover_latest_full_history(lab):
    m,x,p=lab;old=m.context()['context_sha256'];submit(m,x);accept(m);x.publish_local(m,p)
    with pytest.raises(Blocked,match='acknowledgement'):
        with dispatch(m,CFG,x,old,at=AT+timedelta(hours=6)):pass
    with start(m,x,AT+timedelta(hours=6)) as current:
        assert current['state']['cycles'][-1]['inherited_ids']==[r['id'] for r in current['state']['records']]
    print('old context acknowledgement rejected; all earlier record ids inherited')

def test_actual_codex_worker_crash_preserves_checkpoint(lab):
    m,x,p=lab
    code='''from es_research.memory import Memory
from es_research.exchange import GitExchange
from es_research.scheduler import dispatch
from datetime import datetime
import sys,os
m=Memory(sys.argv[1]);x=GitExchange(sys.argv[2])
with dispatch(m,dict(enabled=True,mode='mock',timezone='Asia/Tokyo'),x,m.context()['context_sha256'],at=datetime.fromisoformat('2026-10-30T00:00:00+09:00')):
 m.checkpoint(m.load()['state']['revision'],'durable work before simulated Codex termination')
 os._exit(23)
'''
    r=subprocess.run([sys.executable,'-c',code,str(m.root),x.remote],timeout=20)
    assert r.returncode==23
    assert m.load()['state']['status']=='running'
    assert 'durable work' in m.text(m.load()['state']['cycles'][-1]['checkpoint'])
    m.recover(m.load()['state']['revision']);assert m.load()['state']['status']=='failed'
    with pytest.raises(Blocked):
        with start(m,x,AT+timedelta(hours=6)):pass
    print('real subprocess exit=23: checkpoint preserved; failed recovery blocks next cycle (worker simulation, not AI invocation)')

def test_checkpoint_pause_resume_same_cycle_and_deadline(lab):
    m,x,p=lab
    with start(m,x):m.checkpoint(m.load()['state']['revision'],'resume from fixture 2',paused=True)
    with resume_session(m,x,m.context()['context_sha256'],at=AT+timedelta(minutes=10)):
        assert len(m.load()['state']['cycles'])==1
        m.checkpoint(m.load()['state']['revision'],'fixture 2 done',paused=True)
    with pytest.raises(Blocked,match='expired'):
        with resume_session(m,x,m.context()['context_sha256'],at=AT+timedelta(hours=5)):pass
    print('checkpoint resume keeps cycle id and initial deadline; expired window refused')

def test_unreviewed_or_accepted_hypothesis_is_not_lemma(lab):
    m,x,p=lab;submit(m,x);r=review_for(m);r['accepted_lemma_ids']=['record-000001']
    with pytest.raises(Blocked,match='cannot be promoted'):m.apply_review(m.load()['state']['revision'],r,True)
    accept(m);assert not m.confirmed()
    print('review cannot promote hypothesis/experiment to formally verified lemma')

def test_new_version_retains_original_and_failure(lab):
    m,x,p=lab
    with start(m,x):
        m.add_record(m.load()['state']['revision'],'hypothesis','old','old hypothesis')
        m.add_record(m.load()['state']['revision'],'hypothesis','new','revised hypothesis',supersedes='record-000001')
    c=m.context();assert [r['text'] for r in c['records']]==['old hypothesis','revised hypothesis']
    print('superseded full text retained in current context and immutable events')

def test_invalid_formal_proof_never_registered(lab):
    m,x,p=lab
    with start(m,x):
        with pytest.raises(Blocked):m.add_record(m.load()['state']['revision'],'lemma','bad','claim')
        with pytest.raises(Blocked):m.add_record(m.load()['state']['revision'],'lemma','bad','claim',evidence=dict(proof='theorem x : True := by sorry',lean_log='Build completed successfully',toolchain='v4.19.0'))
    assert not m.load()['state']['records']

def test_production_cannot_be_enabled_by_mock_configuration(tmp_path):
    m=Memory(tmp_path/'prod');m.initialize()
    with pytest.raises(Blocked,match='disabled'):
        with dispatch(m,dict(enabled=False,timezone='Asia/Tokyo',mode='production'),None,'0'*64,at=AT):pass
    with pytest.raises(Blocked):
        with dispatch(m,CFG,None,m.context()['context_sha256'],at=AT):pass
    assert m.load()['state']['status']=='pending'
    print('production remains disabled and unapproved; mock config cannot bypass mode gate')

def test_jst_schedule_windows_and_review_slot(lab):
    assert slot_for(datetime.fromisoformat('2026-10-29T15:00:00+00:00'),'research')==AT.isoformat()
    for h in [0,6,12,18]:assert slot_for(AT.replace(hour=h),'research')
    for h in [5,11,17,23]:assert slot_for(AT.replace(hour=h),'review')
    for at in [AT+timedelta(minutes=5),AT+timedelta(hours=1)]:
        with pytest.raises(Blocked):slot_for(at,'research')
    m,x,p=lab
    with pytest.raises(Blocked):review_ready(m,at=AT+timedelta(hours=5))
    submit(m,x);assert review_ready(m,at=AT+timedelta(hours=5))
    with pytest.raises(Blocked):review_ready(m,at=AT+timedelta(hours=11))
    print('JST research/review hours, missed-run refusal and matching review window verified')

def test_bounded_process_timeout_is_not_success(tmp_path):
    result=run_bounded([sys.executable,'-c','import time;print("checkpoint candidate",flush=True);time.sleep(10)'],tmp_path/'worker.log',seconds=.2,grace=.2)
    assert result['timed_out'] and result['returncode']!=0
    assert 'checkpoint candidate' in (tmp_path/'worker.log').read_text()
    with pytest.raises(FileExistsError):run_bounded([sys.executable,'-c','print(1)'],tmp_path/'worker.log',seconds=1)
    print('timeout terminates local test process group; preserves exclusive log; not an AI runtime guarantee')

def test_sync_write_helper_refuses_network_and_production(lab):
    m,x,p=lab
    with pytest.raises(Blocked):GitExchange('https://github.com/rikupipi1113-cloud/-.git').publish_local(m,p)
    prod=Memory(p/'prod');prod.initialize()
    with pytest.raises(Blocked):x.publish_local(prod,p)
    print('simulation publisher cannot push to GitHub or publish production state')

def test_concurrent_scheduler_processes_admit_once(lab):
    m,x,p=lab
    code='''import sys
from datetime import datetime
from es_research.memory import Memory,Blocked
from es_research.exchange import GitExchange
from es_research.scheduler import dispatch
m=Memory(sys.argv[1]);x=GitExchange(sys.argv[2]);ack=sys.argv[3]
try:
 with dispatch(m,dict(enabled=True,mode='mock',timezone='Asia/Tokyo'),x,ack,at=datetime.fromisoformat('2026-10-30T00:00:00+09:00')):pass
except Blocked:sys.exit(8)
'''
    ack=m.context()['context_sha256']
    workers=[subprocess.Popen([sys.executable,'-c',code,str(m.root),x.remote,ack],stdout=subprocess.PIPE,stderr=subprocess.PIPE) for _ in range(2)]
    for worker in workers:worker.communicate(timeout=20)
    assert sorted(w.returncode for w in workers)==[0,8]
    assert len(m.load()['state']['cycles'])==1
    print('two real dispatcher subprocesses: exactly one admitted, one blocked')

def test_delayed_dispatch_does_not_extend_research_budget(lab):
    m,x,p=lab
    with start(m,x,AT+timedelta(minutes=4)):
        c=m.load()['state']['cycles'][-1]
        assert c['started_at']==(AT+timedelta(minutes=4)).isoformat()
        assert c['deadline']==(AT+timedelta(hours=5)).isoformat()
    print('4 minute late start: deadline remains original slot +5h')

def test_closed_cycle_and_records_cannot_be_rewritten(lab):
    m,x,p=lab;submit(m,x);accept(m);x.publish_local(m,p)
    with start(m,x,AT+timedelta(hours=6)):pass
    latest=m.load()
    event_path=m.root/'events'/f"{latest['state']['revision']:08d}.json"
    # Trusted writer mutation is still detected during replay if previous record text changes.
    from es_research.state import canonical,digest
    e=json.loads(event_path.read_text());e['state']['records'][0]['title']='silently overwritten'
    e['sha256']=digest({k:v for k,v in e.items() if k!='sha256'});event_path.write_bytes(canonical(e))
    with pytest.raises(Blocked,match='overwritten'):m.load()
    print('rewritten historical record rejected even with recomputed current-event hash')
