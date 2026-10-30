import pytest

from kit_demo.lru import LRU


def test_get_missing_returns_none():
    assert LRU(2).get("x") is None


def test_put_and_get():
    c = LRU(2)
    c.put("a", 1)
    assert c.get("a") == 1


def test_evicts_least_recently_used():
    c = LRU(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)
    assert c.get("a") is None
    assert c.get("b") == 2
    assert c.get("c") == 3


def test_get_refreshes_recency():
    c = LRU(2)
    c.put("a", 1)
    c.put("b", 2)
    assert c.get("a") == 1
    c.put("c", 3)
    assert c.get("b") is None
    assert c.get("a") == 1


def test_put_existing_updates_and_refreshes():
    c = LRU(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("a", 10)
    c.put("c", 3)
    assert c.get("a") == 10
    assert c.get("b") is None


@pytest.mark.parametrize("cap", [0, -1])
def test_invalid_capacity_raises(cap):
    with pytest.raises(ValueError):
        LRU(cap)
