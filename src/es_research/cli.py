import argparse
import json
from .state import Store

def main():
    p=argparse.ArgumentParser(description='Manual state inspection and recovery; no scheduler')
    p.add_argument('action',choices=['show','recover','restore-backup','apply-review'])
    p.add_argument('--state',default='automation/cycle_state.json')
    p.add_argument('--revision',type=int)
    p.add_argument('--review-file')
    p.add_argument('--confirm-review-source',action='store_true')
    a=p.parse_args(); store=Store(a.state)
    if a.action=='show': s=store.read()
    elif a.action=='restore-backup': s=store.restore_backup()
    elif a.revision is None: p.error('--revision required')
    elif a.action=='recover': s=store.recover(a.revision)
    else:
        if not a.confirm_review_source or not a.review_file: p.error('review file and explicit source confirmation required')
        s=store.review(a.revision,json.loads(open(a.review_file).read()))
    print(json.dumps(s,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
