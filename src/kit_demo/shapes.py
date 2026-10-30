from kit_demo.geo import area_rect


def total_area(rects: list[tuple[float, float]]) -> float:
    return float(sum(area_rect(w, h) for w, h in rects))
