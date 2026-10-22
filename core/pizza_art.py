"""피자 일러스트 (SVG 문자열). 나무 도마 위에서, 먹은 조각만 손그림 피자로 채워진다.

손으로 그린 느낌: 원 둘레를 살짝 흔든 곡선 + 잉크 외곽선. 조각은 직선으로 잘라 사이로 도마가 보인다.
st.image(svg, alt=...)로 그린다. 이미지로 넣기 때문에 스크립트는 쓰지 않고 CSS 애니메이션만 쓴다.
"""
import math
from datetime import date

from core.palette import (
    BASIL, CHEESE, CHEESE_HI, CRUST, CRUST_HI, INK, PAPER, REST, TOMATO, WOOD, WOOD_DARK,
)
from core.pizza_types import PIZZA_TYPES

C = 160  # 중심
BOARD_R, CRUST_R, SAUCE_R, CHEESE_R = 156, 140, 127, 120
TAG_R = 184
GAP = 1.1  # 조각 사이 틈 (도)
WEEKDAYS = "월화수목금토일"
PEPPERONI = "#b8262f"
FONT = "'IBM Plex Sans KR', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif"

STYLE = """
<style>
.fresh { transform-box: view-box; transform-origin: 160px 160px;
  animation: pop .7s cubic-bezier(.2, 1.6, .4, 1) both; }
.next { animation: march 1.4s linear infinite; }
.steam { animation: steam 2.6s ease-in-out infinite; opacity: 0; }
.steam.s2 { animation-delay: .9s; } .steam.s3 { animation-delay: 1.8s; }
@keyframes pop { from { transform: scale(.4) rotate(-18deg); opacity: 0; } to { transform: none; opacity: 1; } }
@keyframes march { to { stroke-dashoffset: -34; } }
@keyframes steam { 0% { transform: translateY(10px); opacity: 0; } 40% { opacity: .8; }
  100% { transform: translateY(-16px); opacity: 0; } }
@media (prefers-reduced-motion: reduce) { .fresh, .next, .steam { animation: none; } .steam { opacity: .6; } }
</style>
"""


# --- 손그림 도구 -----------------------------------------------------------------

def _pt(r: float, deg: float, cx: float = C, cy: float = C) -> tuple[float, float]:
    rad = math.radians(deg)
    return cx + r * math.cos(rad), cy + r * math.sin(rad)


def _wobbly(r: float, amp: float, seed: float, cx: float = C, cy: float = C, n: int = 44) -> str:
    """둘레를 살짝 흔든 닫힌 곡선 (Catmull-Rom → 베지어). 같은 seed면 항상 같은 모양."""
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n
        d = r + amp * (0.6 * math.sin(3 * a + seed) + 0.4 * math.sin(7 * a + seed * 1.7))
        pts.append((cx + d * math.cos(a), cy + d * math.sin(a)))
    out = [f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"]
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        out.append(f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}")
    return " ".join(out) + " Z"


def _wedge_path(r: float, a0: float, a1: float, n: int) -> str:
    if n == 1:
        return f"M{C - r} {C} A{r} {r} 0 1 1 {C + r} {C} A{r} {r} 0 1 1 {C - r} {C} Z"
    x0, y0 = _pt(r, a0)
    x1, y1 = _pt(r, a1)
    large = 1 if a1 - a0 > 180 else 0
    return f"M{C} {C} L{x0:.1f} {y0:.1f} A{r} {r} 0 {large} 1 {x1:.1f} {y1:.1f} Z"


def _angles(i: int, n: int) -> tuple[float, float]:
    step = 360 / n
    gap = GAP if n > 1 else 0
    return -90 + step * i + gap, -90 + step * (i + 1) - gap


# --- 토핑 (잉크 외곽선) -------------------------------------------------------------

def _pepperoni(x, y):
    return (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9.5" fill="{PEPPERONI}" stroke="{INK}" stroke-width="2"/>'
            f'<circle cx="{x - 3:.1f}" cy="{y - 2:.1f}" r="1.7" fill="#7d1720"/>'
            f'<circle cx="{x + 3.5:.1f}" cy="{y + 3:.1f}" r="1.7" fill="#7d1720"/>'
            f'<path d="M{x - 5:.1f} {y - 5:.1f} q3 -2 6 -1" stroke="#fff" stroke-width="1.6" fill="none" '
            f'stroke-linecap="round" opacity=".7"/>')


def _olive(x, y):
    return (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6.5" fill="#2d2a26" stroke="{INK}" stroke-width="1.5"/>'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.6" fill="{CHEESE}"/>')


def _corn(x, y):
    return "".join(
        f'<circle cx="{x + dx:.1f}" cy="{y + dy:.1f}" r="3.6" fill="#FFF176" stroke="{INK}" stroke-width="1.3"/>'
        for dx, dy in ((0, 0), (9, 4), (-6, 8), (4, -8))
    )


def _mushroom(x, y):
    return (f'<rect x="{x - 3:.1f}" y="{y - 1:.1f}" width="6" height="9" rx="2.5" fill="#EBD8BC" '
            f'stroke="{INK}" stroke-width="1.6"/>'
            f'<path d="M{x - 9:.1f} {y + 1:.1f} q9 -14 18 0 z" fill="#F4E6D2" stroke="{INK}" stroke-width="1.8" '
            f'stroke-linejoin="round"/>')


def _pepper(x, y):
    d = f"M{x - 8:.1f} {y + 2:.1f} q8 -11 16 0"
    return (f'<path d="{d}" stroke="{INK}" stroke-width="6.5" fill="none" stroke-linecap="round"/>'
            f'<path d="{d}" stroke="#58A35E" stroke-width="3.5" fill="none" stroke-linecap="round"/>')


def _basil(x, y):
    return (f'<g transform="rotate(-28 {x:.1f} {y:.1f})">'
            f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="8" ry="4.2" fill="{BASIL}" stroke="{INK}" stroke-width="1.5"/>'
            f'<path d="M{x - 6:.1f} {y:.1f} H{x + 6:.1f}" stroke="#9BD3A5" stroke-width="1.2"/></g>')


TOPPINGS = {
    "pepperoni": [_pepperoni], "olive": [_olive], "corn": [_corn], "mushroom": [_mushroom],
    "supreme": [_pepperoni, _pepper, _olive],
}
# 조각 안 토핑 위치: (반지름 비율, 조각 각도 안에서의 비율)
SPOTS = [(0.40, 0.5), (0.68, 0.27), (0.70, 0.75), (0.88, 0.52)]


def _toppings(pizza_key: str | None, a0: float, a1: float) -> str:
    topping = PIZZA_TYPES.get(pizza_key or "", {}).get("topping")
    makers = TOPPINGS.get(topping, [_basil])
    out = []
    for k, (rf, af) in enumerate(SPOTS):
        x, y = _pt(CHEESE_R * rf, a0 + (a1 - a0) * af)
        out.append(makers[k % len(makers)](x, y))
    return f'<g data-topping="{topping or "basil"}">{"".join(out)}</g>'


# --- 도마, 얼굴, 김 ---------------------------------------------------------------

def _board() -> str:
    grain = "".join(
        f'<path d="M{_pt(r, a)[0]:.1f} {_pt(r, a)[1]:.1f} A{r} {r} 0 0 1 {_pt(r, a + span)[0]:.1f} '
        f'{_pt(r, a + span)[1]:.1f}" stroke="{WOOD_DARK}" stroke-width="1.8" fill="none" stroke-linecap="round" '
        f'opacity=".6"/>'
        for r, a, span in ((150, 200, 50), (147, 300, 40), (151, 40, 60), (148, 110, 35),
                           (60, 190, 80), (96, 20, 70), (118, 250, 55), (78, 320, 60))
    )
    flour = "".join(
        f'<circle cx="{_pt(60 + (k * 37) % 85, k * 47)[0]:.1f}" cy="{_pt(60 + (k * 37) % 85, k * 47)[1]:.1f}" '
        f'r="{1.2 + (k % 3) * 0.6:.1f}" fill="#fff" opacity=".7"/>'
        for k in range(16)
    )
    return (f'<path d="{_wobbly(BOARD_R, 1.6, 0.4)}" fill="{WOOD}" stroke="{INK}" stroke-width="3.5"/>'
            f'<path d="{_wobbly(BOARD_R - 9, 1.2, 1.3)}" fill="none" stroke="{WOOD_DARK}" stroke-width="2"/>'
            f'{grain}{flour}')


def _face(kind: str) -> str:
    plate = f'<path d="{_wobbly(54, 1.4, 2.2, C, C + 6)}" fill="{CHEESE_HI}" stroke="{INK}" stroke-width="3"/>'
    if kind == "happy":
        return plate + (
            f'<path d="M128 156 q10 -13 20 0 M172 156 q10 -13 20 0" stroke="{INK}" stroke-width="5" '
            f'fill="none" stroke-linecap="round"/>'
            f'<path d="M132 178 q28 26 56 0" stroke="{INK}" stroke-width="5" fill="none" stroke-linecap="round"/>'
            f'<ellipse cx="122" cy="176" rx="8" ry="5" fill="{TOMATO}" opacity=".35"/>'
            f'<ellipse cx="198" cy="176" rx="8" ry="5" fill="{TOMATO}" opacity=".35"/>'
        )
    # frown: 인상 쓴 피자 😎 (미간 주름, 처진 눈썹, 선글라스, 시무룩한 입)
    return plate + (
        f'<path d="M122 136 L148 144 M198 136 L172 144" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>'
        f'<path d="M156 130 v9 M164 130 v9" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>'
        '<g class="sunglasses">'
        f'<path d="M112 152 H208" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>'
        f'<path d="M116 152 h38 v8 q0 16 -19 16 q-19 0 -19 -16 Z" fill="{INK}"/>'
        f'<path d="M166 152 h38 v8 q0 16 -19 16 q-19 0 -19 -16 Z" fill="{INK}"/>'
        '<path d="M124 157 l9 0 M174 157 l9 0" stroke="#ffffff" stroke-width="3" stroke-linecap="round" opacity=".75"/>'
        '</g>'
        f'<path d="M138 198 q22 -16 44 0" stroke="{INK}" stroke-width="5" fill="none" stroke-linecap="round"/>'
    )


def _steam() -> str:
    return "".join(
        f'<path class="steam s{i}" d="M{x} -2 q-8 -10 0 -20 q8 -10 0 -20" stroke="{INK}" stroke-width="3.5" '
        f'fill="none" stroke-linecap="round" opacity=".55"/>'
        for i, x in enumerate((128, 160, 192), 1)
    )


def _tag(x: float, y: float, text: str) -> str:
    """가격표 모양 시각 태그."""
    return (f'<rect x="{x - 28:.1f}" y="{y - 12:.1f}" width="56" height="24" rx="12" fill="{PAPER}" '
            f'stroke="{INK}" stroke-width="2"/>'
            f'<text x="{x:.1f}" y="{y + 4.5:.1f}" font-size="13" font-weight="700" text-anchor="middle" '
            f'fill="{INK}" font-family="{FONT}">{text}</text>')


# --- 피자 ---------------------------------------------------------------------

def pizza_svg(
    n: int,
    statuses: list[str | None],
    toppings: list[str | None] | None = None,
    *,
    times: list[str] | None = None,
    highlight: int | None = None,
    fresh: int | None = None,
    face: str | None = None,
) -> str:
    """n조각 피자. statuses[i]: None(빈 도마) / "eaten"(완성) / "rest"(쉼)."""
    toppings = toppings or [None] * n
    clips, parts = [], [_board()]
    for i in range(n):
        a0, a1 = _angles(i, n)
        status = statuses[i] if i < len(statuses) else None
        cls = "slice fresh" if i == fresh and status == "eaten" else "slice"
        clips.append(f'<clipPath id="c{i}"><path d="{_wedge_path(CRUST_R + 6, a0, a1, n)}"/></clipPath>')
        if status == "eaten":
            mid = (a0 + a1) / 2
            bx, by = _pt(CHEESE_R * 0.55, mid)
            parts.append(
                f'<g class="{cls} eaten" data-i="{i}"><g clip-path="url(#c{i})">'
                f'<path d="{_wobbly(CRUST_R, 2.2, 0.9)}" fill="{CRUST}" stroke="{INK}" stroke-width="3"/>'
                f'<path d="{_wobbly(CRUST_R - 6, 1.8, 2.1)}" fill="none" stroke="{CRUST_HI}" stroke-width="3"/>'
                f'<path d="{_wobbly(SAUCE_R, 2.4, 1.7)}" fill="{TOMATO}"/>'
                f'<path d="{_wobbly(CHEESE_R, 3.2, 3.1)}" fill="{CHEESE}" stroke="{INK}" stroke-width="1.4"/>'
                f'<ellipse cx="{bx:.1f}" cy="{by:.1f}" rx="8" ry="5" fill="{CHEESE_HI}"/>'
                + _toppings(toppings[i], a0, a1)
                + "</g>"
                + "".join(f'<path d="M{C} {C} L{_pt(CRUST_R, a)[0]:.1f} {_pt(CRUST_R, a)[1]:.1f}" stroke="{INK}" '
                          f'stroke-width="2.5" stroke-linecap="round"/>' for a in ((a0, a1) if n > 1 else ()))
                + "</g>"
            )
        elif status == "rest":
            tx, ty = _pt(CRUST_R * 0.58, (a0 + a1) / 2)
            parts.append(
                f'<g class="{cls} rest" data-i="{i}"><g clip-path="url(#c{i})">'
                f'<path d="{_wobbly(CRUST_R, 2.2, 0.9)}" fill="{REST}" stroke="{INK}" stroke-width="3"/></g>'
                f'<text x="{tx:.1f}" y="{ty + 6:.1f}" font-size="18" font-weight="700" text-anchor="middle" '
                f'fill="{INK}" opacity=".6" font-family="{FONT}">쉼</text></g>'
            )
        else:  # 빈 도마: 자를 자리만 점선으로
            parts.append(f'<g class="{cls} empty" data-i="{i}"><path d="{_wedge_path(CRUST_R, a0, a1, n)}" '
                         f'fill="none" stroke="{INK}" stroke-width="2.4" stroke-dasharray="0.1 7" '
                         f'stroke-linecap="round" opacity=".7"/></g>')
    if highlight is not None and 0 <= highlight < n and (statuses[highlight] if highlight < len(statuses) else None) is None:
        a0, a1 = _angles(highlight, n)
        parts.append(f'<path class="next" d="{_wedge_path(CRUST_R + 2, a0, a1, n)}" fill="{TOMATO}" fill-opacity=".1" '
                     f'stroke="{TOMATO}" stroke-width="4" stroke-dasharray="11 6" stroke-linecap="round"/>')
    if times:
        step = 360 / n
        for i, t in enumerate(times[:n]):
            parts.append(_tag(*_pt(TAG_R, -90 + step * (i + 0.5)), t))
    if face:
        parts.append(_face(face))
    if face == "happy":
        parts.append(_steam())
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-50 -50 420 420" width="340" height="340">'
            f'{STYLE}<defs>{"".join(clips)}</defs>{"".join(parts)}</svg>')


# --- 단골 도장판 (30일) --------------------------------------------------------------

def _stamp(cx: float, cy: float, r: float, rotate: float) -> str:
    """토마토 잉크 도장: 이중 원 + 피자 조각."""
    tri = f"M{cx - 7:.1f} {cy - 6:.1f} L{cx + 8:.1f} {cy - 6:.1f} L{cx:.1f} {cy + 9:.1f} Z"
    return (f'<g transform="rotate({rotate} {cx} {cy})" opacity=".92">'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{TOMATO}" stroke-width="3"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r - 5}" fill="none" stroke="{TOMATO}" stroke-width="1.4" '
            f'stroke-dasharray="2 2.5"/>'
            f'<path d="{tri}" fill="{TOMATO}" stroke="{TOMATO}" stroke-width="1.5" stroke-linejoin="round"/>'
            f'<circle cx="{cx - 1:.1f}" cy="{cy - 2:.1f}" r="1.8" fill="{PAPER}"/></g>')


def calendar_svg(days: list[tuple[date, int, int]], today: date) -> str:
    """최근 날짜들의 단골 도장판. days: (날짜, 먹은 조각 수, 조각 수). 월요일 시작 7칸."""
    cell, r = 52, 18
    offset = days[0][0].weekday()
    rows = (offset + len(days) + 6) // 7
    width, height = cell * 7, 26 + cell * rows
    parts = [f'<text x="{c * cell + cell / 2}" y="16" font-size="13" font-weight="700" text-anchor="middle" '
             f'fill="{INK}" font-family="{FONT}">{WEEKDAYS[c]}</text>' for c in range(7)]
    for k, (d, eaten, total) in enumerate(days):
        pos = offset + k
        cx, cy = (pos % 7) * cell + cell / 2, 26 + (pos // 7) * cell + r + 2
        is_today = d == today
        ring = 'stroke-width="2.5"' if is_today else 'stroke-width="1.6" stroke-dasharray="3 3.5"'
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{PAPER}" stroke="{INK}" {ring}/>')
        ratio = min(1.0, eaten / total) if total else 0.0
        if ratio >= 1:
            parts.append(_stamp(cx, cy, r - 1, -14 + (k * 23) % 28))
        elif ratio > 0:
            x1, y1 = _pt(r - 4, -90 + 360 * ratio, cx, cy)
            large = 1 if ratio > 0.5 else 0
            parts.append(f'<path d="M{cx} {cy} L{cx} {cy - r + 4} A{r - 4} {r - 4} 0 {large} 1 {x1:.1f} {y1:.1f} Z" '
                         f'fill="{CHEESE}" stroke="{INK}" stroke-width="1.4" stroke-linejoin="round"/>')
        parts.append(f'<text x="{cx}" y="{cy + r + 12}" font-size="10" text-anchor="middle" '
                     f'font-weight="{700 if is_today else 400}" fill="{TOMATO if is_today else INK}" '
                     f'font-family="{FONT}">{d.month}/{d.day}</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height + 8}" width="{width}" '
            f'height="{height + 8}">{"".join(parts)}</svg>')
