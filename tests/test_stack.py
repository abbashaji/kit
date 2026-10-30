import pytest

from kit_demo.stack import Stack


def test_new_stack_is_empty():
    s = Stack()
    assert s.is_empty()
    assert len(s) == 0


def test_push_and_len():
    s = Stack()
    s.push(1)
    s.push(2)
    assert len(s) == 2
    assert not s.is_empty()


def test_pop_is_lifo():
    s = Stack()
    s.push(1)
    s.push(2)
    assert s.pop() == 2
    assert s.pop() == 1
    assert s.is_empty()


def test_peek_does_not_remove():
    s = Stack()
    s.push("a")
    assert s.peek() == "a"
    assert len(s) == 1


def test_pop_empty_raises():
    with pytest.raises(IndexError):
        Stack().pop()


def test_peek_empty_raises():
    with pytest.raises(IndexError):
        Stack().peek()
