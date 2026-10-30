from fractions import Fraction
import pytest
import sympy as sp
import numpy as np
import mpmath as mp
from es_research.math import *

def test_known_solutions_and_rejection():
    for row in [(2,1,2,2),(3,1,4,12),(4,2,3,6),(5,2,4,20)]:
        assert verify_solution(*row)
        assert exact_sum(*row[1:]) == Fraction(4,row[0])
    assert not verify_solution(5,2,4,21)

@pytest.mark.parametrize('bad',[0,-1,True,1.0])
def test_reject_invalid(bad):
    with pytest.raises(ValueError): verify_solution(2,bad,2,2)

def test_exact_and_number_theory():
    assert sp.Rational(1,3)+sp.Rational(1,6)==sp.Rational(1,2)
    assert primes_below(20)==[2,3,5,7,11,13,17,19]
    assert prime(97) and not prime(91)
    assert factors(360)=={2:3,3:2,5:1}
    assert congruent(17,2,5) and not congruent(17,3,5)
    assert np.array([1,2,3],dtype=np.int64).sum()==6
    assert mp.mp.dps>=15  # availability only, not a proof
