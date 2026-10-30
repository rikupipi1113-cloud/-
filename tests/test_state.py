import copy
import json
import multiprocessing as multiprocessing
import os
import subprocess
import sys
import pytest
from es_research.state import *
from es_research.demo import run

@pytest.fixture
def store(tmp_path):
    s=Store(tmp_path/'state.json'); s.create(initial('test-001','setup test only',True)); return s

def submitted(store):
    s=store.begin(0); s=store.complete(s['revision'],[dict(kind='hypothesis',claim='UNPROVEN',verification='unreviewed',data={})]); return store.submit(s['revision'])

def review_for(s,verdict='accepted'):
    return dict(cycle_id=s['cycle_id'],report_sha256=s['report']['sha256'],report_revision=s['report']['revision'],verdict=verdict,reviewer='MOCK',comments='test only',next_instruction='mock next task')

def test_roundtrip_schema_and_no_overwrite(store):
    assert store.read()==initial('test-001','setup test only',True)
    with pytest.raises(FileExistsError): store.create(initial())
    invalid=store.read(); invalid['status']='unknown'
    with pytest.raises(Exception): validate(invalid)
    invalid=store.read(); invalid['unexpected']=1
    with pytest.raises(Exception): validate(invalid)

def test_unapproved_duplicate_and_stale(store):
    s=store.begin(0)
    with pytest.raises(ValueError): store.begin(s['revision'])
    with pytest.raises(ValueError): store.complete(0,[])
    s=store.recover(s['revision'])
    with pytest.raises(ValueError): store.begin(s['revision'])

def test_initial_unapproved(tmp_path):
    s=Store(tmp_path/'s.json'); s.create(initial())
    with pytest.raises(ValueError): s.begin(0)

def test_review_binding_and_gate(store):
    s=submitted(store); assert confirmed_results(s)==[]
    with pytest.raises(ValueError): store.next_cycle(s['revision'],'test-002')
    for key,value in [('cycle_id','old'),('report_sha256','0'*64),('report_revision',0)]:
        r=review_for(s); r[key]=value
        with pytest.raises(ValueError): store.review(s['revision'],r)
    s=store.review(s['revision'],review_for(s))
    assert confirmed_results(s)==[]  # accepted hypothesis is still not a lemma
    with pytest.raises(ValueError): store.next_cycle(s['revision'],'test-001')
    s=store.next_cycle(s['revision'],'test-002')
    assert s['history'][0]['results'][0]['verification']=='unreviewed'
    assert s['status']=='pending' and s['instruction_approved']

def test_rejected_review_blocks_next(store):
    s=submitted(store); s=store.review(s['revision'],review_for(s,'changes_requested'))
    with pytest.raises(ValueError): store.next_cycle(s['revision'],'test-002')

def test_worker_lock_blocks_recovery(store):
    s=store.begin(0)
    with store.lock(worker=True):
        with pytest.raises(RuntimeError): store.recover(s['revision'])
    assert store.recover(s['revision'])['status']=='failed'

def test_atomic_interrupted_replace(store,monkeypatch):
    original=store.path.read_bytes(); real=os.replace
    def fail(src,dst):
        if Path(dst)==store.path: raise OSError('simulated interrupted write')
        return real(src,dst)
    monkeypatch.setattr(os,'replace',fail)
    with pytest.raises(OSError): store.begin(0)
    assert store.path.read_bytes()==original
    assert store.read()['status']=='pending'

def test_corruption_backup_explicit_restore(store):
    store.begin(0); store.path.write_text('{broken')
    with pytest.raises(ValueError): store.read()
    assert store.restore_backup()['status']=='failed'
    assert list(store.path.parent.glob('*.corrupt-*'))
    with pytest.raises(ValueError): store.restore_backup()

def test_actual_killed_worker(store):
    code='from es_research.state import Store; import os,sys; s=Store(sys.argv[1]);\nwith s.lock(worker=True):\n s.begin(0)\n os._exit(19)\n'
    r=subprocess.run([sys.executable,'-c',code,str(store.path)],env={**os.environ,'PYTHONPATH':str(ROOT/'src')})
    assert r.returncode==19
    assert store.read()['status']=='running'
    assert store.recover(1)['status']=='failed'

def test_demo(tmp_path):
    s=run(tmp_path/'mock'); assert s['status']=='failed'
    assert s['history'][0]['status']=='reviewed'
    assert s['results'][0]['verification']=='unreviewed'


def test_concurrent_begin_only_one(store):
    code="from es_research.state import Store; import sys; Store(sys.argv[1]).begin(0)"
    workers=[subprocess.Popen([sys.executable,'-c',code,str(store.path)],stdout=subprocess.PIPE,stderr=subprocess.PIPE) for _ in range(2)]
    outputs=[w.communicate() for w in workers]
    assert sorted(w.returncode for w in workers)==[0,1]
    assert store.read()['status']=='running'

def test_tampered_report_rejected(store):
    s=submitted(store); s['report']['payload']['task']='tampered'
    with pytest.raises(ValueError): validate(s)


def test_result_normalizes_json_keys_and_rejects_nan(store):
    s=store.begin(0)
    bad=[dict(kind='experiment',claim='invalid numerical data',verification='unreviewed',data={'x':float('nan')})]
    with pytest.raises(ValueError): store.complete(s['revision'],bad)
    good=[dict(kind='experiment',claim='key normalization',verification='python_exact',data={'factors':{2:1,11:1}})]
    s=store.complete(s['revision'],good); s=store.submit(s['revision'])
    assert store.read()['report']['sha256']==s['report']['sha256']
