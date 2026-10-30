import Mathlib.Data.Nat.Prime.Basic
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Ring

-- Infrastructure checks only; no universal Erdos-Straus claim.
theorem nat_add_check (n : ℕ) : n + 0 = n := by simp
theorem int_square_identity (a b : ℤ) : (a + b)^2 = a^2 + 2*a*b + b^2 := by ring
theorem six_divides_twelve : (6 : ℕ) ∣ 12 := by norm_num
theorem two_is_prime : Nat.Prime 2 := Nat.prime_two
-- 4xyz = n(xy+xz+yz), for n=2, x=1, y=z=2.
theorem known_solution_two : (4 : ℕ)*1*2*2 = 2*(1*2+1*2+2*2) := by norm_num
#print axioms nat_add_check
#print axioms int_square_identity
#print axioms six_divides_twelve
#print axioms two_is_prime
#print axioms known_solution_two
