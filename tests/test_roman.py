import pytest

from kit_demo.roman import from_roman, to_roman


@pytest.mark.parametrize(
    "n, s",
    [
        (1, "I"),
        (4, "IV"),
        (9, "IX"),
        (14, "XIV"),
        (40, "XL"),
        (90, "XC"),
        (400, "CD"),
        (1994, "MCMXCIV"),
        (2024, "MMXXIV"),
        (3888, "MMMDCCCLXXXVIII"),
        (3999, "MMMCMXCIX"),
    ],
)
def test_known_values(n, s):
    assert to_roman(n) == s
    assert from_roman(s) == n


def test_round_trip_all():
    for n in range(1, 4000):
        assert from_roman(to_roman(n)) == n


@pytest.mark.parametrize("n", [0, -1, 4000, 10000])
def test_to_roman_out_of_range(n):
    with pytest.raises(ValueError):
        to_roman(n)


@pytest.mark.parametrize("s", ["", "IIII", "VX", "IC", "IIX", "MMMM", "ABC", "iv"])
def test_from_roman_invalid(s):
    with pytest.raises(ValueError):
        from_roman(s)
