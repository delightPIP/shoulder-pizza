"""피자 일러스트 (SVG 문자열). 빈 피자판에서 시작해 먹은 조각만 채워진다.

st.image(svg, alt=...)로 그린다. 이미지로 넣기 때문에 스크립트는 쓰지 않고 CSS 애니메이션만 쓴다.
"""
import math
from datetime import date

from core.pizza_types import PIZZA_TYPES

C = 160  # 중심
PAN_R, CRUST_R, SAUCE_R, CHEESE_R = 150, 138, 125, 117
WEEKDAYS = "월화수목금토일"

COLORS = {
    "pan": "#cfc8bd", "pan_rim": "#a89f92", "pan_inner": "#e9e3d8", "outline": "#b8ad9d",
    "crust": "#dc9b4a", "crust_edge": "#b97a32", "sauce": "#cf3f2a", "cheese": "#f7cf5d",
    "cheese_hi": "#fbe08f", "rest": "#e4e0d9", "rest_text": "#8a8174", "next": "#d9482b",
    "ink": "#5a2e16", "label": "#6b4b33",
}

STYLE = """
<style>
.fresh { transform-box: view-box; transform-origin: 160px 160px;
  animation: pop .7s cubic-bezier(.2, 1.6, .4, 1) both; }
.next { animation: march 1.2s linear infinite; }
.steam { animation: steam 2.4s ease-in-out infinite; opacity: .0; }
.steam.s2 { animation-delay: .8s; } .steam.s3 { animation-delay: 1.6s; }
@keyframes pop { from { transform: scale(.35) rotate(-20deg); opacity: 0; } to { transform: none; opacity: 1; } }
@keyframes march { to { stroke-dashoffset: -32; } }
@keyframes steam { 0% { transform: translateY(8px); opacity: 0; } 40% { opacity: .7; }
  100% { transform: translateY(-18px); opacity: 0; } }
@media (prefers-reduced-motion: reduce) { .fresh, .next, .steam { animation: none; } .steam { opacity: .5; } }
</style>
"""


def _pt(r: float, deg: float, cx: float = C, cy: float = C) -> tuple[float, float]:
    rad = math.radians(deg)
    return cx + r * math.cos(rad), cy + r * math.sin(rad)


def _wedge(r: float, a0: float, a1: float, n: int, **attrs) -> str:
    extra = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in attrs.items())
    if n == 1:
        return f'<circle cx="{C}" cy="{C}" r="{r}" {extra}/>'
    x0, y0 = _pt(r, a0)
    x1, y1 = _pt(r, a1)
    large = 1 if a1 - a0 > 180 else 0
    return f'<path d="M{C} {C} L{x0:.1f} {y0:.1f} A{r} {r} 0 {large} 1 {x1:.1f} {y1:.1f} Z" {extra}/>'


# --- 토핑 ---------------------------------------------------------------------

def _pepperoni(x, y):
    return (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="#b8262f"/>'
            f'<circle cx="{x - 3:.1f}" cy="{y - 2:.1f}" r="1.6" fill="#8e1b22"/>'
            f'<circle cx="{x + 3:.1f}" cy="{y + 3:.1f}" r="1.6" fill="#8e1b22"/>')


def _olive(x, y):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.5" fill="none" stroke="#2d2a26" stroke-width="3.5"/>'


def _corn(x, y):
    return (f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="4.5" ry="3.5" fill="#ffd23f" stroke="#e0a800"/>'
            f'<ellipse cx="{x + 8:.1f}" cy="{y + 4:.1f}" rx="4.5" ry="3.5" fill="#ffd23f" stroke="#e0a800"/>')


def _mushroom(x, y):
    return (f'<rect x="{x - 2.5:.1f}" y="{y:.1f}" width="5" height="7" rx="2" fill="#d9c3a2"/>'
            f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="8" ry="5" fill="#e8d5b9" stroke="#b99b74"/>')


def _pepper(x, y):
    return (f'<path d="M{x - 7:.1f} {y:.1f} q7 -9 14 0" fill="none" stroke="#3f9a45" '
            f'stroke-width="3.2" stroke-linecap="round"/>')


def _basil(x, y):
    return f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="7" ry="3.5" fill="#4f9d3a" transform="rotate(-30 {x:.1f} {y:.1f})"/>'


TOPPINGS = {
    "pepperoni": [_pepperoni], "olive": [_olive], "corn": [_corn], "mushroom": [_mushroom],
    "supreme": [_pepperoni, _pepper, _olive],
}
# 조각 안 토핑 위치: (반지름 비율, 조각 각도 안에서의 비율)
SPOTS = [(0.42, 0.5), (0.7, 0.28), (0.72, 0.74), (0.9, 0.5)]


def _toppings(pizza_key: str | None, a0: float, a1: float) -> str:
    topping = PIZZA_TYPES.get(pizza_key or "", {}).get("topping")
    makers = TOPPINGS.get(topping, [_basil])
    out = []
    for k, (rf, af) in enumerate(SPOTS):
        x, y = _pt(CHEESE_R * rf, a0 + (a1 - a0) * af)
        out.append(makers[k % len(makers)](x, y))
    return "".join(out)


# --- 얼굴 ---------------------------------------------------------------------

def _face(kind: str) -> str:
    ink = COLORS["ink"]
    plate = f'<circle cx="{C}" cy="{C + 6}" r="56" fill="#fbe7a8" stroke="#e3b84f" stroke-width="3" opacity=".95"/>'
    if kind == "happy":
        return plate + (
            f'<path d="M128 156 q10 -13 20 0 M172 156 q10 -13 20 0" stroke="{ink}" stroke-width="5" '
            f'fill="none" stroke-linecap="round"/>'
            f'<path d="M132 178 q28 26 56 0" stroke="{ink}" stroke-width="5" fill="none" stroke-linecap="round"/>'
            f'<circle cx="122" cy="176" r="7" fill="#f28c8c" opacity=".55"/>'
            f'<circle cx="198" cy="176" r="7" fill="#f28c8c" opacity=".55"/>'
        )
    # frown: 인상 쓴 피자 😎 (미간 주름, 처진 눈썹, 선글라스, 시무룩한 입)
    return plate + (
        f'<path d="M122 136 L148 144 M198 136 L172 144" stroke="{ink}" stroke-width="5" stroke-linecap="round"/>'
        f'<path d="M156 130 v9 M164 130 v9" stroke="{ink}" stroke-width="3" stroke-linecap="round"/>'
        '<g class="sunglasses">'
        f'<path d="M112 152 H208" stroke="{ink}" stroke-width="4" stroke-linecap="round"/>'
        '<path d="M116 152 h38 v8 q0 16 -19 16 q-19 0 -19 -16 Z" fill="#231a14"/>'
        '<path d="M166 152 h38 v8 q0 16 -19 16 q-19 0 -19 -16 Z" fill="#231a14"/>'
        '<path d="M124 157 l9 0 M174 157 l9 0" stroke="#ffffff" stroke-width="3" stroke-linecap="round" opacity=".7"/>'
        '</g>'
        f'<path d="M138 198 q22 -16 44 0" stroke="{ink}" stroke-width="5" fill="none" stroke-linecap="round"/>'
    )


def _steam() -> str:
    paths = []
    for i, x in enumerate((128, 160, 192), 1):
        paths.append(f'<path class="steam s{i}" d="M{x} 4 q-8 -10 0 -20 q8 -10 0 -20" stroke="#bfb3a3" '
                     f'stroke-width="4" fill="none" stroke-linecap="round"/>')
    return "".join(paths)


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
    """n조각 피자. statuses[i]: None(빈 판) / "eaten"(완성) / "rest"(쉼)."""
    toppings = toppings or [None] * n
    step = 360 / n
    parts = [f'<circle cx="{C}" cy="{C}" r="{PAN_R}" fill="{COLORS["pan"]}" stroke="{COLORS["pan_rim"]}" stroke-width="5"/>',
             f'<circle cx="{C}" cy="{C}" r="{PAN_R - 9}" fill="{COLORS["pan_inner"]}"/>']
    for i in range(n):
        a0, a1 = -90 + step * i, -90 + step * (i + 1)
        status = statuses[i] if i < len(statuses) else None
        cls = "slice fresh" if i == fresh and status == "eaten" else "slice"
        if status == "eaten":
            mid = (a0 + a1) / 2
            hx, hy = _pt(CHEESE_R * 0.55, mid)
            parts.append(
                f'<g class="{cls} eaten" data-i="{i}">'
                + _wedge(CRUST_R, a0, a1, n, fill=COLORS["crust"], stroke=COLORS["crust_edge"], stroke_width=2)
                + _wedge(SAUCE_R, a0, a1, n, fill=COLORS["sauce"])
                + _wedge(CHEESE_R, a0, a1, n, fill=COLORS["cheese"], stroke="#fff3cf", stroke_width=2)
                + f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="7" fill="{COLORS["cheese_hi"]}"/>'
                + _toppings(toppings[i], a0, a1)
                + "</g>"
            )
        elif status == "rest":
            tx, ty = _pt(CRUST_R * 0.6, (a0 + a1) / 2)
            parts.append(
                f'<g class="{cls} rest" data-i="{i}">'
                + _wedge(CRUST_R, a0, a1, n, fill=COLORS["rest"], stroke=COLORS["pan_rim"], stroke_width=2)
                + f'<text x="{tx:.1f}" y="{ty + 6:.1f}" font-size="18" text-anchor="middle" '
                  f'fill="{COLORS["rest_text"]}" font-family="sans-serif">쉼</text></g>'
            )
        else:  # 빈 피자판: 조각 자리만 점선으로
            parts.append(f'<g class="{cls} empty" data-i="{i}">'
                         + _wedge(CRUST_R, a0, a1, n, fill="none", stroke=COLORS["outline"],
                                  stroke_width=2, stroke_dasharray="6 6") + "</g>")
    if highlight is not None and 0 <= highlight < n and (statuses[highlight] if highlight < len(statuses) else None) is None:
        a0, a1 = -90 + step * highlight, -90 + step * (highlight + 1)
        parts.append(_wedge(CRUST_R, a0, a1, n, fill="rgba(217,72,43,.07)", stroke=COLORS["next"],
                            stroke_width=4, stroke_dasharray="10 6", **{"class": "next"}))
    if times:
        for i, t in enumerate(times[:n]):
            x, y = _pt(PAN_R + 22, -90 + step * (i + 0.5))
            parts.append(f'<text x="{x:.1f}" y="{y + 5:.1f}" font-size="15" font-weight="700" text-anchor="middle" '
                         f'fill="{COLORS["label"]}" font-family="sans-serif">{t}</text>')
    if face:
        parts.append(_face(face))
    if face == "happy":
        parts.append(_steam())
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-45 -45 410 410" width="340" height="340">'
            f'{STYLE}{"".join(parts)}</svg>')


def calendar_svg(days: list[tuple[date, int, int]], today: date) -> str:
    """최근 날짜들의 미니 피자 달력. days: (날짜, 먹은 조각 수, 조각 수). 월요일 시작 7칸."""
    cell, r = 52, 18
    first = days[0][0]
    offset = first.weekday()
    rows = (offset + len(days) + 6) // 7
    width, height = cell * 7, 26 + cell * rows
    parts = [f'<text x="{c * cell + cell / 2}" y="16" font-size="13" text-anchor="middle" fill="{COLORS["label"]}" '
             f'font-family="sans-serif">{WEEKDAYS[c]}</text>' for c in range(7)]
    for k, (d, eaten, total) in enumerate(days):
        pos = offset + k
        cx, cy = (pos % 7) * cell + cell / 2, 26 + (pos // 7) * cell + r + 2
        ring = COLORS["next"] if d == today else COLORS["pan_rim"]
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{COLORS["pan_inner"]}" stroke="{ring}" stroke-width="2"/>')
        ratio = min(1.0, eaten / total) if total else 0.0
        if ratio >= 1:
            parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r - 2}" fill="{COLORS["cheese"]}" stroke="{COLORS["crust"]}" stroke-width="3"/>'
                         f'<circle cx="{cx - 5}" cy="{cy - 4}" r="3" fill="#b8262f"/><circle cx="{cx + 5}" cy="{cy + 4}" r="3" fill="#b8262f"/>')
        elif ratio > 0:
            a1 = -90 + 360 * ratio
            x1, y1 = _pt(r - 2, a1, cx, cy)
            large = 1 if ratio > 0.5 else 0
            parts.append(f'<path d="M{cx} {cy} L{cx} {cy - r + 2} A{r - 2} {r - 2} 0 {large} 1 {x1:.1f} {y1:.1f} Z" '
                         f'fill="{COLORS["cheese"]}" stroke="{COLORS["crust"]}" stroke-width="2"/>')
        parts.append(f'<text x="{cx}" y="{cy + r + 12}" font-size="10" text-anchor="middle" fill="{COLORS["label"]}" '
                     f'font-family="sans-serif">{d.month}/{d.day}</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height + 8}" width="{width}" '
            f'height="{height + 8}">{"".join(parts)}</svg>')
