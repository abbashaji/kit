"""Temperature conversion helpers."""


def c_to_f(c: float) -> float:
    """Convert degrees Celsius to degrees Fahrenheit."""
    return float(c) * 9.0 / 5.0 + 32.0


def f_to_c(f: float) -> float:
    """Convert degrees Fahrenheit to degrees Celsius."""
    return (float(f) - 32.0) * 5.0 / 9.0
