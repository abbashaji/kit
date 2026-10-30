import pytest

from kit_demo.queue_ import Queue


def test_fifo_order():
    q = Queue()
    q.enqueue(1)
    q.enqueue(2)
    q.enqueue(3)
    assert q.dequeue() == 1
    assert q.dequeue() == 2
    assert q.dequeue() == 3


def test_len_tracks_size():
    q = Queue()
    assert len(q) == 0
    q.enqueue("a")
    q.enqueue("b")
    assert len(q) == 2
    q.dequeue()
    assert len(q) == 1


def test_is_empty():
    q = Queue()
    assert q.is_empty()
    q.enqueue(1)
    assert not q.is_empty()
    q.dequeue()
    assert q.is_empty()


def test_dequeue_empty_raises():
    q = Queue()
    with pytest.raises(IndexError):
        q.dequeue()


def test_peek_empty_raises():
    q = Queue()
    with pytest.raises(IndexError):
        q.peek()


def test_peek_is_non_destructive():
    q = Queue()
    q.enqueue("x")
    q.enqueue("y")
    assert q.peek() == "x"
    assert q.peek() == "x"
    assert len(q) == 2
    assert q.dequeue() == "x"
