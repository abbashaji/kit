import pytest

from kit_demo.cipher import caesar


def test_basic_shift():
    assert caesar("abc", 1) == "bcd"


def test_wraparound():
    assert caesar("xyz", 3) == "abc"
    assert caesar("XYZ", 3) == "ABC"


def test_preserves_case_and_other_chars():
    assert caesar("Hello, World! 123", 5) == "Mjqqt, Btwqi! 123"


def test_negative_shift():
    assert caesar("bcd", -1) == "abc"
    assert caesar("abc", -3) == "xyz"


def test_large_shift():
    assert caesar("abc", 26) == "abc"
    assert caesar("abc", 53) == "bcd"
    assert caesar("abc", -53) == "zab"


def test_zero_and_empty():
    assert caesar("Hi", 0) == "Hi"
    assert caesar("", 7) == ""


@pytest.mark.parametrize("k", [-30, -1, 0, 1, 13, 25, 100])
def test_roundtrip(k):
    t = "The Quick Brown Fox, jumps over 13 lazy dogs!"
    assert caesar(caesar(t, k), -k) == t
