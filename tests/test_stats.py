import pytest

from kit_demo.stats import mean, median


def test_mean():
    assert mean([1, 2, 3, 4]) == 2.5


def test_median_odd_even():
    assert median([3, 1, 2]) == 2
    assert median([4, 1, 3, 2]) == 2.5


@pytest.mark.parametrize("f", [mean, median])
def test_empty_raises(f):
    with pytest.raises(ValueError):
        f([])
