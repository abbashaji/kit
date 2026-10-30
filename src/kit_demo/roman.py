"""Roman numeral conversion for 1..3999."""

_PAIRS = (
    (1000, "M"),
    (900, "CM"),
    (500, "D"),
    (400, "CD"),
    (100, "C"),
    (90, "XC"),
    (50, "L"),
    (40, "XL"),
    (10, "X"),
    (9, "IX"),
    (5, "V"),
    (4, "IV"),
    (1, "I"),
)

_VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def to_roman(n: int) -> str:
    """Convert an integer in 1..3999 to a Roman numeral."""
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError("n must be an int")
    if n < 1 or n > 3999:
        raise ValueError("n must be between 1 and 3999")
    parts = []
    for value, symbol in _PAIRS:
        count, n = divmod(n, value)
        parts.append(symbol * count)
    return "".join(parts)


def from_roman(s: str) -> int:
    """Convert a valid (canonical) Roman numeral to an integer."""
    if not isinstance(s, str):
        raise TypeError("s must be a str")
    if not s or any(ch not in _VALUES for ch in s):
        raise ValueError(f"invalid Roman numeral: {s!r}")
    total = 0
    for i, ch in enumerate(s):
        value = _VALUES[ch]
        if i + 1 < len(s) and _VALUES[s[i + 1]] > value:
            total -= value
        else:
            total += value
    if total < 1 or total > 3999 or to_roman(total) != s:
        raise ValueError(f"invalid Roman numeral: {s!r}")
    return total
