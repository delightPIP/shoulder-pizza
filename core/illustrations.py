"""가게 일러스트: 줄무늬 차양, 기지개 켜는 피자 조각 마스코트, 메뉴판 도장. 모두 SVG 문자열."""
from core.palette import BASIL, CHEESE, CHEESE_HI, CRUST, CRUST_HI, INK, INK_SOFT, PAPER, TOMATO

FONT = "'IBM Plex Sans KR', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif"


def _svg(view: str, width: int, height: int, body: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view}" width="{width}" height="{height}">'
            f'{body}</svg>')


def awning(stripes: int = 10) -> str:
    """가게 차양: 토마토·흰색 줄무늬, 아래는 물결 모양."""
    w, h, sw = 400, 64, 400 / stripes
    parts = []
    for k in range(stripes):
        x = k * sw
        fill = TOMATO if k % 2 == 0 else PAPER
        parts.append(f'<path d="M{x:.1f} 0 H{x + sw:.1f} V44 A{sw / 2:.1f} {sw / 2.6:.1f} 0 0 1 {x:.1f} 44 Z" '
                     f'fill="{fill}" stroke="{INK}" stroke-width="2.5" stroke-linejoin="round"/>')
    parts.append(f'<path d="M0 1.5 H{w}" stroke="{INK}" stroke-width="3"/>')
    return _svg(f"-2 -2 {w + 4} {h + 6}", w, h, "".join(parts))


def _slice_body() -> str:
    """조각 몸통: 아래로 뾰족한 삼각형 + 위쪽 크러스트."""
    return (
        f'<path d="M42 70 Q100 52 158 70 L104 196 Q100 202 96 196 Z" fill="{CHEESE}" stroke="{INK}" '
        f'stroke-width="3.5" stroke-linejoin="round"/>'
        f'<path d="M40 70 Q100 46 160 70 L156 84 Q100 64 44 84 Z" fill="{CRUST}" stroke="{INK}" '
        f'stroke-width="3.5" stroke-linejoin="round"/>'
        f'<path d="M58 72 Q100 60 142 72" stroke="{CRUST_HI}" stroke-width="3" fill="none" stroke-linecap="round"/>'
        f'<path d="M88 176 q-4 10 2 14" stroke="{INK}" stroke-width="2.5" fill="{CHEESE_HI}" stroke-linecap="round"/>'
        f'<circle cx="74" cy="104" r="9" fill="{TOMATO}" stroke="{INK}" stroke-width="2.5"/>'
        f'<circle cx="122" cy="150" r="8" fill="{TOMATO}" stroke="{INK}" stroke-width="2.5"/>'
        f'<ellipse cx="128" cy="100" rx="7" ry="3.6" fill="{BASIL}" stroke="{INK}" stroke-width="1.8" '
        f'transform="rotate(-25 128 100)"/>'
    )


def mascot(pose: str = "stretch", size: int = 200) -> str:
    """기지개 켜는 피자 조각 ("어깨 펴자"). pose: stretch(두 팔 쭉) / rest(쉬는 중)."""
    if pose == "rest":
        body = (
            f'<g transform="rotate(-80 100 130) translate(0 10)">{_slice_body()}'
            f'<path d="M80 120 q6 6 12 0 M108 120 q6 6 12 0" stroke="{INK}" stroke-width="3.5" fill="none" '
            f'stroke-linecap="round"/>'
            f'<path d="M94 140 q6 3 12 0" stroke="{INK}" stroke-width="3" fill="none" stroke-linecap="round"/></g>'
            f'<text x="150" y="58" font-size="22" font-weight="700" fill="{INK_SOFT}" font-family="{FONT}">z</text>'
            f'<text x="166" y="38" font-size="16" font-weight="700" fill="{INK_SOFT}" font-family="{FONT}">z</text>'
            f'<path d="M20 206 H184" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>'
        )
    else:
        # 팔: 어깨(크러스트 양 끝)에서 바깥으로 나갔다가 팔꿈치에서 꺾여 위로 쭉
        arm_ink = f'stroke="{INK}" stroke-width="11" fill="none" stroke-linecap="round" stroke-linejoin="round"'
        arm_fill = f'stroke="{CHEESE}" stroke-width="5.5" fill="none" stroke-linecap="round" stroke-linejoin="round"'
        arms = "M46 78 L22 62 L30 20 M154 78 L178 62 L170 20"
        body = (
            f'<path d="{arms}" {arm_ink}/><path d="{arms}" {arm_fill}/>'
            f'<circle cx="30" cy="17" r="8" fill="{CHEESE_HI}" stroke="{INK}" stroke-width="3"/>'
            f'<circle cx="170" cy="17" r="8" fill="{CHEESE_HI}" stroke="{INK}" stroke-width="3"/>'
            + _slice_body()
            + f'<path d="M80 118 q6 -7 12 0 M108 118 q6 -7 12 0" stroke="{INK}" stroke-width="3.5" fill="none" '
              f'stroke-linecap="round"/>'
              f'<path d="M93 130 q7 12 14 0 z" fill="#7d1720" stroke="{INK}" stroke-width="2.5" stroke-linejoin="round"/>'
              f'<path d="M12 14 l-8 -4 M14 30 l-9 2 M188 14 l8 -4 M186 30 l9 2" stroke="{INK}" stroke-width="2.5" '
              f'stroke-linecap="round"/>'
        )
    return _svg("0 0 200 214", size, int(size * 1.07), body)


def stamp(kind: str, size: int = 52) -> str:
    """메뉴판 도장. done: 토마토 '완성' / rest: 잉크 '쉼'."""
    color, word, rot = (TOMATO, "완성", -12) if kind == "done" else (INK_SOFT, "쉼", 8)
    return _svg(
        "0 0 60 60", size, size,
        f'<g transform="rotate({rot} 30 30)" opacity=".92">'
        f'<circle cx="30" cy="30" r="26" fill="none" stroke="{color}" stroke-width="3.2"/>'
        f'<circle cx="30" cy="30" r="20" fill="none" stroke="{color}" stroke-width="1.4" stroke-dasharray="2 2.6"/>'
        f'<text x="30" y="35.5" font-size="{15 if len(word) > 1 else 18}" font-weight="700" text-anchor="middle" '
        f'fill="{color}" font-family="{FONT}">{word}</text></g>',
    )
