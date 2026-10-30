from kit_demo.words import word_count


def test_empty():
    assert word_count("") == {}


def test_basic():
    assert word_count("The the cat, THE dog!") == {"the": 3, "cat": 1, "dog": 1}


def test_apostrophes_digits():
    assert word_count("Don't stop 2 2") == {"don't": 1, "stop": 1, "2": 2}
