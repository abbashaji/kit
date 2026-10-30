import sys
import types

# Fake contract provider (C-015) injected BEFORE importing kit_demo.shapes.
_fake_geo = types.ModuleType("kit_demo.geo")


def _fake_area_rect(w: float, h: float) -> float:
    if w < 0 or h < 0:
        raise ValueError("negative side")
    return w * h


_fake_geo.area_rect = _fake_area_rect
sys.modules["kit_demo.geo"] = _fake_geo

from kit_demo.shapes import total_area  # noqa: E402


def test_empty_is_zero_float():
    result = total_area([])
    assert result == 0.0
    assert isinstance(result, float)


def test_single_rect():
    assert total_area([(2, 3)]) == 6.0


def test_multiple_rects():
    assert total_area([(1, 2), (3, 4), (0.5, 2)]) == 15.0
