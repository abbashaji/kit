def area_rect(w: float, h: float) -> float:
    """Return the area of a rectangle; ValueError on negative sides."""
    if w < 0 or h < 0:
        raise ValueError("sides must be non-negative")
    return float(w * h)
