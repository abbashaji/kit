def _check(xs: list[float]) -> None:
    if not xs:
        raise ValueError("xs must not be empty")


def mean(xs: list[float]) -> float:
    _check(xs)
    return sum(xs) / len(xs)


def median(xs: list[float]) -> float:
    _check(xs)
    s = sorted(xs)
    n = len(s)
    mid = n // 2
    return float(s[mid]) if n % 2 else (s[mid - 1] + s[mid]) / 2
