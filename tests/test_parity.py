from kit_demo.parity import is_even, is_odd


def test_is_even():
    assert is_even(0)
    assert is_even(2)
    assert is_even(-4)
    assert not is_even(1)
    assert not is_even(-3)


def test_is_odd():
    assert is_odd(1)
    assert is_odd(-3)
    assert not is_odd(0)
    assert not is_odd(2)
    assert not is_odd(-4)
