"""Exact arithmetic only. Finite checks are not proofs of the conjecture."""
from fractions import Fraction
from sympy import factorint, isprime, primerange

def positive_integer(value):
    if type(value) is not int or value <= 0:
        raise ValueError("expected a positive Python integer")
    return value

def verify_solution(n, x, y, z):
    for v in (n, x, y, z): positive_integer(v)
    if n < 2: raise ValueError("n must be >= 2")
    return 4*x*y*z == n*(x*y+x*z+y*z)

def exact_sum(x, y, z):
    for v in (x,y,z): positive_integer(v)
    return sum((Fraction(1,v) for v in (x,y,z)), Fraction())

def congruent(a, b, modulus):
    positive_integer(modulus)
    if type(a) is not int or type(b) is not int: raise ValueError("integers required")
    return (a-b) % modulus == 0

def primes_below(limit):
    positive_integer(limit)
    return [int(p) for p in primerange(2, limit)]

def prime(n):
    positive_integer(n)
    return bool(isprime(n))

def factors(n):
    positive_integer(n)
    return {int(k):int(v) for k,v in factorint(n).items()}
