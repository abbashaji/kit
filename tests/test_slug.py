from kit_demo.slug import slugify


def test_basic():
    assert slugify("Hello World") == "hello-world"


def test_runs_and_edges():
    assert slugify("  --Hello,   World!!  ") == "hello-world"


def test_empty_and_symbols_only():
    assert slugify("") == ""
    assert slugify("!!!") == ""


def test_digits_kept():
    assert slugify("Cell 007 v2") == "cell-007-v2"
