import pytest

from kit_demo.geo import area_rect


def test_area_basic():
    assert area_rect(2, 3) == 6.0


def test_area_returns_float():
    assert isinstance(area_rect(2, 3), float)


def test_area_zero():
    assert area_rect(0, 5) == 0.0


def test_negative_width():
    with pytest.raises(ValueError):
        area_rect(-1, 2)


def test_negative_height():
    with pytest.raises(ValueError):
        area_rect(2, -1)
