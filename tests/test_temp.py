import pytest

from kit_demo.temp import c_to_f, f_to_c


def test_c_to_f_boiling():
    result = c_to_f(100)
    assert result == 212.0
    assert isinstance(result, float)


def test_f_to_c_freezing():
    result = f_to_c(32)
    assert result == 0.0
    assert isinstance(result, float)


def test_c_to_f_zero():
    assert c_to_f(0) == 32.0


def test_minus_forty_is_equal():
    assert c_to_f(-40) == -40.0
    assert f_to_c(-40) == -40.0


@pytest.mark.parametrize("c", [-273.15, -10.5, 0.0, 36.6, 100.0])
def test_round_trip(c):
    assert f_to_c(c_to_f(c)) == pytest.approx(c)
