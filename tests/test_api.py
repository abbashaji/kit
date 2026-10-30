from kit_demo import api


def test_slugify():
    assert isinstance(api.slugify("Hello World"), str)


def test_caesar():
    assert isinstance(api.caesar("abc", 1), str)


def test_to_roman():
    assert isinstance(api.to_roman(4), str)


def test_c_to_f():
    assert api.c_to_f(0) == 32
