from kit_demo.pal import is_palindrome


def test_empty():
    assert is_palindrome("")


def test_simple():
    assert is_palindrome("racecar")
    assert not is_palindrome("hello")


def test_ignores_case_and_punct():
    assert is_palindrome("A man, a plan, a canal: Panama")


def test_only_punct():
    assert is_palindrome("!?")
