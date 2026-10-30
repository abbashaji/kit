from kit_demo.fizz import fizzbuzz


def test_empty():
    assert fizzbuzz(0) == []
    assert fizzbuzz(-3) == []


def test_basic():
    assert fizzbuzz(5) == ["1", "2", "Fizz", "4", "Buzz"]


def test_fizzbuzz():
    r = fizzbuzz(15)
    assert r[14] == "FizzBuzz"
    assert r[2] == "Fizz"
    assert r[9] == "Buzz"
