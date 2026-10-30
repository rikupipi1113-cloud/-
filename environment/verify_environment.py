import importlib.metadata
import json
import re
import sys
from pathlib import Path
from fractions import Fraction
from es_research.math import verify_solution, exact_sum, primes_below, factors, congruent, prime
from es_research.state import Store, atomic_json, confirmed_results
import sympy
root=Path(__file__).resolve().parents[1]
s=Store(root/'automation/cycle_state.json').read()
assert s['status']=='pending' and not s['instruction_approved']
assert confirmed_results(s)==[]
source=(root/'lean/ErdosStrausResearch.lean').read_text()
assert not re.search(r'\b(sorry|admit|axiom)\b',source)
known=[(2,1,2,2),(3,1,4,12),(4,2,3,6),(5,2,4,20)]
results=[]
for n,x,y,z in known:
 assert verify_solution(n,x,y,z) and exact_sum(x,y,z)==Fraction(4,n)
 results.append(dict(n=n,x=x,y=y,z=z,identity_lhs=4*x*y*z,identity_rhs=n*(x*y+x*z+y*z)))
assert sympy.Rational(1,3)+sympy.Rational(1,6)==sympy.Rational(1,2)
r=dict(python=sys.version,executable=sys.executable,venv_isolated=sys.prefix!=sys.base_prefix,packages={k:importlib.metadata.version(k) for k in ['pytest','sympy','numpy','mpmath','jsonschema','cmake']},known_solutions=results,primes_below_20=primes_below(20),factorization_360=factors(360),congruence_17_2_mod5=congruent(17,2,5),prime_97=prime(97),production_state=s,lean_source_has_no_placeholders=True)
assert r['venv_isolated']
atomic_json(root/'reports/environment_checks.json',r)
print(json.dumps(r,ensure_ascii=False,indent=2))
