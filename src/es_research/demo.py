"""Infrastructure simulation: fake review is always confined to a new scratch dir."""
import argparse
import json
from pathlib import Path
from .math import verify_solution, exact_sum, primes_below, factors
from .state import Store, initial, atomic_json

def run(directory):
    d=Path(directory); d.mkdir(parents=True,exist_ok=False)
    store=Store(d/'cycle_state.json'); store.create(initial('mock-001','既知の小解の検証のみ',True))
    with store.lock(worker=True):
        s=store.begin(0)
        assert verify_solution(2,1,2,2)
        results=[dict(kind='experiment',claim='n=2, (1,2,2) satisfies integer identity',verification='python_exact',data=dict(n=2,x=1,y=2,z=2,rational=str(exact_sum(1,2,2)),primes=primes_below(20),factors=factors(360)))]
        s=store.complete(s['revision'],results); s=store.submit(s['revision'])
    atomic_json(d/'report.json',s['report'])
    assert not __import__('es_research.state',fromlist=['confirmed_results']).confirmed_results(s)
    review=dict(cycle_id=s['cycle_id'],report_sha256=s['report']['sha256'],report_revision=s['report']['revision'],verdict='accepted',reviewer='MOCK ONLY - not ChatGPT',comments='Interface test only; no mathematical review occurred.',next_instruction='MOCK ONLY: repeat known-solution check')
    atomic_json(d/'review.json',review)
    s=store.review(s['revision'],review)
    s=store.next_cycle(s['revision'],'mock-002')
    with store.lock(worker=True): s=store.begin(s['revision'])
    # Worker lock released, simulating terminated worker; retained running state.
    s=store.recover(s['revision'])
    atomic_json(d/'summary.json',dict(mock_only=True,first_cycle='reviewed',second_cycle=s['status'],unreviewed_results_promoted=False))
    return s

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('directory'); args=parser.parse_args()
    print(json.dumps(run(args.directory),ensure_ascii=False,indent=2))
