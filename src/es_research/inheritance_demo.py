"""Three MOCK cycles using a real, local bare Git repository and fresh readers."""
import argparse
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from .exchange import GitExchange
from .memory import Memory, Blocked
from .scheduler import dispatch, review_ready
from .state import atomic_json, ROOT
from .math import verify_solution

def review_for(memory):
    current=memory.load();c=current['state']['cycles'][-1]
    return dict(protocol=2,cycle_id=c['id'],report_sha256=c['report'],memory_head=current['head'],reviewer_kind='mock',reviewer='MOCK reviewer; not ChatGPT',verdict='accepted',accepted_lemma_ids=[],comments='Infrastructure simulation only; hypotheses stay unproven.',next_instruction='Continue the unresolved finite-check question; do not infer a general proof.',reviewed_at=datetime.now().astimezone().isoformat())

def run(root):
    root=Path(root).resolve();root.mkdir(parents=True,exist_ok=False)
    remote=root/'shared.git';subprocess.run(['git','init','--bare','-q',str(remote)],check=True)
    m=Memory(root/'memory');m.initialize('mock','MOCK: record a finite-check hypothesis, no general research')
    exchange=GitExchange(remote);audit=[]
    audit_path=root/'execution.jsonl'
    def record(event,**data):
        row=dict(event=event,**data)
        with audit_path.open('a') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
        audit.append(row)
    base=datetime.fromisoformat('2026-10-30T00:00:00+09:00')
    proof=(ROOT/'lean/ErdosStrausResearch.lean').read_text()
    # Actual audited build output provided by the caller, not manufactured by the demo.
    lean_log=(ROOT/'environment/stage2/lean_audit.txt').read_text()
    for index in range(3):
        exchange.publish_local(m,root)
        # A new Git reader parses and verifies the entire package and all prior objects.
        reader=exchange.read_handoff()
        context=m.context()
        assert reader['context']==context
        if index:
            assert len(context['cycles'])==index
            assert any(r['kind']=='hypothesis' for r in context['records'])
            assert any(r['kind']=='open_problem' for r in context['records'])
        at=base+timedelta(hours=6*index)
        config=dict(enabled=True,mode='mock',timezone='Asia/Tokyo')
        record('inheritance_read',cycle=index+1,source_cycles=[c['id'] for c in context['cycles']],record_ids=[r['id'] for r in context['records']],context_sha256=context['context_sha256'],sync_commit=reader['commit'])
        with dispatch(m,config,exchange,context['context_sha256'],at=at):
            def add(kind,title,text,**kwargs):
                m.add_record(m.load()['state']['revision'],kind,title,text,**kwargs)
            if index==0:
                add('hypothesis','MOCK unresolved question','Can the existing exact validator reject every deliberately perturbed example in a specified finite fixture? This is unproven until the fixture is defined.')
                add('open_problem','Fixture completeness','Which small fixtures and perturbations should be included? General existence is outside this simulation.')
                add('lemma','Existing infrastructure lemmas',proof,evidence=dict(proof=proof,lean_log=lean_log,toolchain=(ROOT/'lean/lean-toolchain').read_text()))
                add('prior_work','Source provenance','Existing stage-1 smoke proofs only; no survey or novelty claim. Evidence: lean/ErdosStrausResearch.lean.')
            elif index==1:
                add('failed_approach','Rejected approximate comparison','A float tolerance could accept a wrong candidate. Use the integer equality instead. This is a recorded design failure, not a new mathematical result.')
                old=next(r for r in context['records'] if r['kind']=='open_problem')
                add('open_problem','Refined fixture question','The n=2 and n=3 fixtures have been checked; coverage beyond these fixtures is unresolved.',supersedes=old['id'])
            else:
                assert len(context['cycle_bodies'])==2
                add('open_problem','Continuation from both cycles','Read cycle 1 question and cycle 2 failure. Still unresolved: fixture completeness. No general proof claim.')
            n,x,y,z=[(2,1,2,2),(3,1,4,12),(4,2,3,6)][index]
            assert verify_solution(n,x,y,z)
            add('experiment','Known example exact check',json.dumps(dict(input=[n,x,y,z],identity_lhs=4*x*y*z,identity_rhs=n*(x*y+x*z+y*z),valid=True,range='one pre-existing fixture only',seed=None)))
            m.checkpoint(m.load()['state']['revision'],json.dumps(dict(completed_fixture=index+1,next='submit finite fixture report')),paused=False)
            m.complete(m.load()['state']['revision'],f'MOCK cycle {index+1}: inherited prior context and checked one known fixture',at=at+timedelta(minutes=1))
            m.submit(m.load()['state']['revision'])
        assert not m.confirmed() # even the existing Lean evidence remains unreviewed for research reuse
        ready=review_ready(m,at=at+timedelta(hours=5))
        exchange.publish_local(m,root)
        review_reader=exchange.read_handoff()
        assert review_reader['context']==m.context()
        review=review_for(m);atomic_json(root/f'review-{index+1}.json',review)
        m.apply_review(m.load()['state']['revision'],review,source_confirmed=True)
        record('mock_review_applied',cycle=index+1,head=m.load()['head'],review_slot=ready['slot'],confirmed_lemmas=len(m.confirmed()))
    exchange.publish_local(m,root)
    result=dict(mock_only=True,real_chatgpt_roundtrip=False,cycles=3,records=len(m.load()['state']['records']),status=m.load()['state']['status'],history_preserved=True,all_contexts_matched=True,unreviewed_lemmas_promoted=False,final_head=m.load()['head'])
    atomic_json(root/'summary.json',result);record('summary',**result)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory');a=p.parse_args();print(json.dumps(run(a.directory),ensure_ascii=False,indent=2))
