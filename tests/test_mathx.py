from kit_demo.mathx import gcd, lcm


def test_gcd():
    assert gcd(12, 18) == 6
    assert gcd(0, 5) == 5
    assert gcd(5, 0) == 5
    assert gcd(0, 0) == 0
    assert gcd(7, 13) == 1


def test_lcm():
    assert lcm(4, 6) == 12
    assert lcm(0, 5) == 0
    assert lcm(5, 0) == 0
    assert lcm(0, 0) == 0
    assert lcm(3, 7) == 21
