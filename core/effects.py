"""날씨 화면 효과 (SPEC 7.4). CSS 애니메이션 오버레이로, 화면 클릭을 막지 않는다.

prefers-reduced-motion이면 움직임을 끄고 색 톤만 남긴다.
"""
from core.weather import CLEAR, CLOUDY, DUSTY, FOG, RAIN, SNOW, STORM

BASE_CSS = """
.sp-fx { position: fixed; inset: 0; pointer-events: none; z-index: 0; overflow: hidden; }
.sp-tone { position: absolute; inset: 0; }
.sp-drop { position: absolute; top: -12vh; width: 2px; height: 64px; border-radius: 2px;
  background: linear-gradient(to bottom, rgba(120,150,200,0), rgba(90,125,185,.45));
  animation: sp-fall linear infinite; }
.sp-flake { position: absolute; top: -6vh; border-radius: 50%; background: #fff;
  box-shadow: 0 0 4px rgba(140,160,190,.6); animation: sp-snow linear infinite; }
.sp-sun { position: absolute; top: -140px; right: -140px; width: 420px; height: 420px; border-radius: 50%;
  background: radial-gradient(circle, rgba(255,205,90,.55) 0%, rgba(255,205,90,.18) 45%, rgba(255,205,90,0) 70%);
  animation: sp-pulse 6s ease-in-out infinite; }
.sp-haze { position: absolute; inset: -20%; animation: sp-drift 24s ease-in-out infinite alternate; }
.sp-cloud { position: absolute; width: 380px; height: 120px; border-radius: 120px;
  background: rgba(150,160,175,.18); filter: blur(18px); animation: sp-float 40s linear infinite; }
.sp-flash { position: absolute; inset: 0; background: rgba(255,255,255,.0); animation: sp-flash 9s infinite; }
@keyframes sp-fall { to { transform: translateY(125vh); } }
@keyframes sp-snow { to { transform: translate(40px, 112vh); } }
@keyframes sp-pulse { 50% { transform: scale(1.08); opacity: .8; } }
@keyframes sp-drift { to { transform: translateX(6%); } }
@keyframes sp-float { from { transform: translateX(-420px); } to { transform: translateX(110vw); } }
@keyframes sp-flash { 0%, 93%, 100% { background: rgba(255,255,255,0); } 95% { background: rgba(255,255,255,.35); } }
@media (prefers-reduced-motion: reduce) {
  .sp-fx * { animation: none !important; }
  .sp-drop, .sp-flake, .sp-flash, .sp-cloud { display: none; }
}
"""


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
    return (f'<div class="sp-haze" style="background:radial-gradient(ellipse at 30% 40%, {color}, transparent 60%),'
            f'radial-gradient(ellipse at 75% 65%, {color}, transparent 55%)"></div>')


def _clouds() -> str:
    return "".join(f'<i class="sp-cloud" style="top:{8 + i * 22}%;animation-delay:-{i * 13}s"></i>' for i in range(3))


LAYERS = {
    CLEAR: lambda: '<div class="sp-sun"></div>',
    CLOUDY: lambda: _tone("rgba(120,130,145,.08)") + _clouds(),
    FOG: lambda: _tone("rgba(200,205,210,.18)") + _haze("rgba(255,255,255,.35)"),
    DUSTY: lambda: _tone("rgba(190,165,110,.16)") + _haze("rgba(205,180,120,.30)"),
    RAIN: lambda: _tone("rgba(90,110,140,.08)") + _rain(),
    SNOW: lambda: _tone("rgba(200,215,235,.12)") + _snow(),
    STORM: lambda: _tone("rgba(40,50,70,.16)") + _rain(48) + '<div class="sp-flash"></div>',
}


def effect_html(category: str | None) -> str:
    """st.html로 넣을 오버레이. 분류가 없으면 빈 문자열 (기본 테마)."""
    if category not in LAYERS:
        return ""
    return f'<style>{BASE_CSS}</style><div class="sp-fx sp-{category}" aria-hidden="true">{LAYERS[category]()}</div>'
