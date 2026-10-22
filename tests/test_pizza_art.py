import xml.etree.ElementTree as ET
from datetime import date, timedelta

import pytest

from core.pizza_art import calendar_svg, pizza_svg

NS = {"s": "http://www.w3.org/2000/svg"}


def slices(svg, kind):
    root = ET.fromstring(svg)
    return [g for g in root.iter("{http://www.w3.org/2000/svg}g") if kind in g.get("class", "").split()]


@pytest.mark.parametrize("n", [1, 3, 4, 5])
def test_empty_pan_before_eating(n):
    svg = pizza_svg(n, [None] * n)
    assert len(slices(svg, "empty")) == n
    assert slices(svg, "eaten") == []


def test_eaten_slices_are_filled_with_toppings():
    svg = pizza_svg(3, ["eaten", None, "rest"], ["shoulder", None, None])
    assert [g.get("data-i") for g in slices(svg, "eaten")] == ["0"]
    assert [g.get("data-i") for g in slices(svg, "rest")] == ["2"]
    assert len(slices(svg, "empty")) == 1
    assert "#b8262f" in svg  # 어깨 피자 토핑(페퍼로니)
    assert "쉼" in svg


def test_fresh_slice_pops_and_next_slice_is_highlighted():
    svg = pizza_svg(4, ["eaten", "eaten", None, None], highlight=2, fresh=1)
    fresh = [g for g in slices(svg, "fresh")]
    assert [g.get("data-i") for g in fresh] == ["1"]
    assert 'class="next"' in svg


def test_highlight_is_ignored_for_finished_slice():
    assert 'class="next"' not in pizza_svg(3, ["eaten", None, None], highlight=0)


def test_times_are_labelled():
    svg = pizza_svg(3, [None] * 3, times=["09:00", "13:30", "18:00"])
    for t in ("09:00", "13:30", "18:00"):
        assert t in svg


def test_faces():
    happy = pizza_svg(3, ["eaten"] * 3, face="happy")
    frown = pizza_svg(3, ["eaten", None, None], face="frown")
    assert 'class="steam' in happy and 'class="steam' not in frown  # 김은 완성 피자에만
    ET.fromstring(happy)
    ET.fromstring(frown)


def test_motion_respects_reduced_motion_and_has_no_script():
    svg = pizza_svg(3, ["eaten", None, None], fresh=0)
    assert "prefers-reduced-motion" in svg and "<script" not in svg


def test_every_topping_renders():
    for key in ("shoulder", "head", "eyes", "good", "back", None, "unknown"):
        ET.fromstring(pizza_svg(3, ["eaten"] * 3, [key] * 3))


def test_calendar_has_one_cell_per_day():
    today = date(2026, 10, 22)
    days = [(today - timedelta(days=29 - k), k % 4, 3) for k in range(30)]
    svg = calendar_svg(days, today)
    root = ET.fromstring(svg)
    labels = [t.text for t in root.iter("{http://www.w3.org/2000/svg}text") if t.text and "/" in t.text]
    assert len(labels) == 30 and labels[-1] == "10/22"
