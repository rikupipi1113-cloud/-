"""Manual stage-2 tooling. Does not register schedules, run AI, or push GitHub."""
import argparse
import json
from pathlib import Path
from .memory import Memory,Blocked,read_json
from .exchange import GitExchange
from .scheduler import RESEARCH_HOURS,REVIEW_HOURS
from .inheritance_demo import run
from .state import ROOT

def main():
    p=argparse.ArgumentParser()
    p.add_argument('action',choices=['status','context','export','probe-shared','plan','apply-review','repair','recover','demo'])
    p.add_argument('--root',default=str(ROOT/'research/memory-v2'))
    p.add_argument('--output')
    p.add_argument('--review')
    p.add_argument('--revision',type=int)
    p.add_argument('--confirm-source',action='store_true')
    a=p.parse_args();m=Memory(a.root)
    try:
        if a.action=='status':result=m.load()
        elif a.action=='context':result=m.context()
        elif a.action=='export':
            if not a.output:p.error('--output required')
            # Exclusive creation preserves earlier handoffs.
            result=dict(protocol=2,handoff=m.handoff(),context=m.context(),files={str(f.relative_to(m.root)):f.read_text() for folder in ['events','objects'] for f in sorted((m.root/folder).iterdir()) if f.is_file() and not f.name.endswith('.tmp')})
            result['files']['latest.json']=(m.root/'latest.json').read_text()
            out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
            with out.open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
            result=dict(exported=str(out),memory_head=result['handoff']['memory_head'])
        elif a.action=='plan':
            config=read_json(ROOT/'automation/stage2/schedule.json')
            result=dict(config=config,research_hours_jst=RESEARCH_HOURS,review_hours_jst=REVIEW_HOURS,registered=False,production_ready=False)
        elif a.action=='probe-shared':
            config=read_json(ROOT/'automation/stage2/schedule.json')
            receipt=GitExchange(config['remote'],config['ref']).read_handoff()
            if receipt['handoff']!=m.handoff():raise Blocked('shared memory differs from local memory')
            result=dict(shared_handoff_matched=True,commit=receipt['commit'],independent_chatgpt_verified=False)
        elif a.action=='repair':result=m.repair_projection()
        elif a.action=='recover':
            if a.revision is None:p.error('--revision required')
            result=m.recover(a.revision)
        elif a.action=='apply-review':
            if not a.review or a.revision is None:p.error('--review and --revision required')
            result=m.apply_review(a.revision,read_json(a.review),source_confirmed=a.confirm_source)
        else:
            if not a.output:p.error('--output required for new simulation directory')
            result=run(a.output)
    except Exception as error:
        print(json.dumps(dict(blocked=True,error_type=type(error).__name__,reason=str(error)),ensure_ascii=False,indent=2))
        raise SystemExit(2)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
