import pytest

from kit_demo.shapes import total_area


def test_total_area_basic():
    assert total_area([(2, 3), (1, 1)]) == 7.0


def test_total_area_empty():
    assert total_area([]) == 0.0


def test_total_area_negative_side_raises():
    with pytest.raises(ValueError):
        total_area([(2, -3)])
