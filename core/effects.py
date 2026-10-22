"""날씨 화면 효과 (SPEC 7.4). CSS 애니메이션 오버레이로, 화면 클릭을 막지 않는다.

prefers-reduced-motion이면 움직임을 끄고 색 톤만 남긴다.
"""
from core.weather import CLEAR, CLOUDY, DUSTY, FOG, RAIN, SNOW, STORM

BASE_CSS = """
.sp-fx { position: fixed; inset: 0; pointer-events: none; z-index: 0; overflow: hidden; }
.sp-tone { position: absolute; inset: 0; }
.sp-drop { position: absolute; top: -10vh; width: 3px; height: 22px; border-radius: 3px;
  background: #4F79B5; opacity: .45; animation: sp-fall linear infinite; }
.sp-flake { position: absolute; top: -6vh; border-radius: 50%; background: #fff;
  border: 1.5px solid rgba(43,26,18,.55); animation: sp-snow linear infinite; }
.sp-sun { position: absolute; top: 64px; right: 18px; width: 96px; height: 96px; opacity: .9; }
.sp-cloud { position: absolute; width: 150px; height: 70px; opacity: .75; animation: sp-float 70s linear infinite; }
.sp-haze { position: absolute; inset: 0; }
.sp-flash { position: absolute; inset: 0; background: rgba(255,255,255,0); animation: sp-flash 9s infinite; }
@keyframes sp-fall { to { transform: translateY(125vh); } }
@keyframes sp-snow { to { transform: translate(40px, 112vh); } }
@keyframes sp-float { from { transform: translateX(-180px); } to { transform: translateX(110vw); } }
@keyframes sp-flash { 0%, 93%, 100% { background: rgba(255,255,255,0); } 95% { background: rgba(255,255,255,.35); } }
@media (prefers-reduced-motion: reduce) {
  .sp-fx * { animation: none !important; }
  .sp-drop, .sp-flake, .sp-flash { display: none; }
}
"""

INK = "#2B1A12"
# 잉크 선으로 그린 해와 구름 (일러스트와 같은 그림체)
SUN_SVG = (
    '<svg class="sp-sun" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">'
    + "".join(f'<path d="M50 50 m0 -44 v12" transform="rotate({a} 50 50)" stroke="{INK}" stroke-width="4" '
              f'stroke-linecap="round"/>' for a in range(0, 360, 45))
    + f'<circle cx="50" cy="50" r="22" fill="#FFC93C" stroke="{INK}" stroke-width="4"/></svg>'
)
CLOUD_SVG = (
    '<svg viewBox="0 0 150 70" xmlns="http://www.w3.org/2000/svg" width="150" height="70">'
    f'<path d="M22 58 h104 a20 20 0 0 0 -6 -39 a28 28 0 0 0 -52 -4 a22 22 0 0 0 -40 18 a13 13 0 0 0 -6 25 z" '
    f'fill="#fff" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/></svg>'
)


def _rain(count: int = 36) -> str:
    return "".join(
        f'<i class="sp-drop" style="left:{(i * 53) % 100}%;animation-duration:{0.7 + (i % 5) * 0.15:.2f}s;'
        f'animation-delay:{(i * 0.37) % 1.6:.2f}s"></i>'
        for i in range(count)
    )


def _snow(count: int = 32) -> str:
    return "".join(
        f'<i class="sp-flake" style="left:{(i * 37) % 100}%;width:{4 + i % 5}px;height:{4 + i % 5}px;'
        f'animation-duration:{6 + (i % 6)}s;animation-delay:{(i * 0.7) % 8:.1f}s"></i>'
        for i in range(count)
    )


def _tone(color: str) -> str:
    return f'<div class="sp-tone" style="background:{color}"></div>'


def _haze(color: str) -> str:
    return f'<div class="sp-haze" style="background:{color}"></div>'


def _clouds() -> str:
    return "".join(f'<div class="sp-cloud" style="top:{12 + i * 30}%;animation-delay:-{i * 23}s">{CLOUD_SVG}</div>'
                   for i in range(2))


LAYERS = {
    CLEAR: lambda: SUN_SVG,
    CLOUDY: lambda: _tone("rgba(120,130,145,.08)") + _clouds(),
    FOG: lambda: _haze("rgba(210,214,218,.28)"),
    DUSTY: lambda: _haze("rgba(205,180,120,.22)"),
    RAIN: lambda: _tone("rgba(90,110,140,.08)") + _rain(),
    SNOW: lambda: _tone("rgba(200,215,235,.12)") + _snow(),
    STORM: lambda: _tone("rgba(40,50,70,.16)") + _rain(48) + '<div class="sp-flash"></div>',
}


def effect_html(category: str | None) -> str:
    """st.html로 넣을 오버레이. 분류가 없으면 빈 문자열 (기본 테마)."""
    if category not in LAYERS:
        return ""
    return f'<style>{BASE_CSS}</style><div class="sp-fx sp-{category}" aria-hidden="true">{LAYERS[category]()}</div>'
