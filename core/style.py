"""가게 전체 스타일 (사용자가 직접 요청한 디자인 개편이라 CSS를 쓴다).

원칙
- 힘을 주는 곳은 도마 위 손그림 피자 한 곳. 나머지는 흰 종이와 잉크 선으로 조용하게.
- 빨강(토마토)은 주 행동과 도장에만. 그라데이션·흐린 그림자 대신 인쇄물 같은 딱딱한 잉크 그림자.
- 주문 티켓(st.container key="ticket-…"): 흰 종이, 잉크 테두리, 위쪽 절취선과 양옆 홈.
- 메뉴판 줄(key="menu-…"): 점선 밑줄. 테마로 안 되는 것만 여기서 하고 Streamlit 내부 클래스는 쓰지 않는다.
"""
import html

import streamlit as st

from core.palette import BASIL, CHEESE, DOUGH, INK, INK_SOFT, PAPER, TOMATO

CSS = f"""
<style>
:root {{
  --ink: {INK}; --ink-soft: {INK_SOFT}; --paper: {PAPER}; --dough: {DOUGH};
  --tomato: {TOMATO}; --cheese: {CHEESE}; --basil: {BASIL};
}}

/* 상단: 빨간 체크 식탁보 띠 */
[data-testid="stHeader"] {{ background: var(--paper); }}
[data-testid="stHeader"]::before {{
  content: ""; position: absolute; inset: 0 0 auto 0; height: 12px;
  background-color: #fff;
  background-image: linear-gradient(90deg, rgba(200,50,31,.55) 50%, transparent 50%),
                    linear-gradient(rgba(200,50,31,.55) 50%, transparent 50%);
  background-size: 16px 16px; border-bottom: 2px solid var(--ink);
}}

h1 {{ letter-spacing: -0.01em; line-height: 1.08 !important; }}
[data-testid="stCaptionContainer"] {{ color: var(--ink-soft); }}
[data-testid="stElementToolbar"] {{ display: none; }}  /* 일러스트 위의 전체 화면 버튼 숨김 */

/* 버튼: 잉크 테두리 + 딱딱한 그림자, 누르면 그림자만큼 눌린다 */
[data-testid^="stBaseButton-primary"], [data-testid^="stBaseButton-secondary"] {{
  border: 2px solid var(--ink) !important; box-shadow: 3px 3px 0 var(--ink);
  font-weight: 700; transition: transform .06s ease, box-shadow .06s ease;
}}
[data-testid^="stBaseButton-secondary"] {{ background: #fff !important; color: var(--ink) !important; }}
[data-testid^="stBaseButton-primary"]:active, [data-testid^="stBaseButton-secondary"]:active {{
  transform: translate(3px, 3px); box-shadow: 0 0 0 var(--ink);
}}
[data-testid^="stBaseButton-primary"]:disabled, [data-testid^="stBaseButton-secondary"]:disabled {{
  box-shadow: none; opacity: .5;
}}
button:focus-visible, a:focus-visible {{ outline: 3px solid var(--cheese) !important; outline-offset: 2px; }}

/* 고르기 버튼(컨디션·자세·조각 수): 고른 것은 치즈색 */
[data-testid="stButtonGroup"] button[role="radio"] {{
  border: 2px solid var(--ink) !important; background: #fff; color: var(--ink); font-weight: 500;
}}
[data-testid="stButtonGroup"] button[role="radio"][aria-checked="true"] {{
  background: var(--cheese) !important; color: var(--ink) !important; font-weight: 700;
  box-shadow: 2px 2px 0 var(--ink);
}}

/* 입력칸 */
[data-baseweb="input"], [data-baseweb="select"] > div {{
  border: 2px solid var(--ink) !important; background: #fff !important;
}}

/* 주문 티켓 */
[class*="st-key-ticket"], [data-testid="stForm"] {{
  background: #fff; border: 2px solid var(--ink); border-radius: .55rem;
  box-shadow: 5px 5px 0 var(--ink); padding: 1rem 1.1rem 1.1rem; position: relative;
}}
[class*="st-key-ticket"]:has(.sp-stub)::before, [class*="st-key-ticket"]:has(.sp-stub)::after,
[data-testid="stForm"]:has(.sp-stub)::before, [data-testid="stForm"]:has(.sp-stub)::after {{
  content: ""; position: absolute; top: 3.15rem; width: 18px; height: 18px; border-radius: 50%;
  background: var(--paper); border: 2px solid var(--ink);
}}
[class*="st-key-ticket"]:has(.sp-stub)::before, [data-testid="stForm"]:has(.sp-stub)::before {{
  left: -11px; clip-path: inset(0 0 0 50%);
}}
[class*="st-key-ticket"]:has(.sp-stub)::after, [data-testid="stForm"]:has(.sp-stub)::after {{
  right: -11px; clip-path: inset(0 50% 0 0);
}}
.sp-stub {{
  display: flex; justify-content: space-between; align-items: baseline; gap: .75rem;
  height: 2.6rem; margin: -.15rem 0 .35rem; padding-bottom: .5rem;
  border-bottom: 2px dashed rgba(43, 26, 18, .45);
  font-family: 'Do Hyeon', sans-serif; font-size: 1.25rem; color: var(--ink);
}}
.sp-stub small {{ font-family: 'IBM Plex Sans KR', sans-serif; font-size: .85rem; color: var(--ink-soft); }}
.sp-stub b {{ font-weight: 400; color: var(--tomato); }}

/* 메뉴판 줄 */
[class*="st-key-menu"] {{ border-bottom: 2px dotted var(--ink); padding: .5rem .1rem .55rem; }}

/* 알림 상자와 접는 상자 */
[data-testid="stAlertContainer"] {{ border: 2px solid var(--ink); background: #fff !important; color: var(--ink) !important; }}
[data-testid="stExpander"] details {{ border: 2px dashed rgba(43, 26, 18, .5) !important; background: transparent; }}

/* 진행 막대: 반죽 위로 치즈가 차오른다 */
[data-testid="stProgressBarTrack"] {{ height: .9rem !important; border: 2px solid var(--ink); border-radius: 999px;
  background: var(--dough) !important; overflow: hidden; }}
[data-testid="stProgressBarTrack"] > div {{ background: var(--cheese) !important; border-radius: 0 !important; }}

/* 숫자 카드(기록) */
[data-testid="stMetric"] {{ background: #fff; border: 2px solid var(--ink); border-radius: .55rem; padding: .55rem .7rem;
  box-shadow: 3px 3px 0 var(--ink); min-width: 0; flex: 1 1 0; }}
[data-testid="stMetricValue"] {{ font-family: 'Do Hyeon', sans-serif; font-size: 1.7rem; }}

/* 페이지 바로가기 */
[data-testid="stPageLink-NavLink"] {{ border: 2px solid var(--ink); border-radius: 999px; background: #fff; }}

[data-testid="stSidebar"] {{ border-right: 2px solid var(--ink); }}

@media (prefers-reduced-motion: reduce) {{ * {{ transition: none !important; }} }}
</style>
"""


def apply() -> None:
    st.html(CSS)


def ticket_stub(left: str, right: str = "", *, accent: str = "") -> None:
    """주문 티켓 머리 (절취선 위). left는 간판 글꼴, right는 작은 글씨, accent는 토마토색 강조."""
    accent_html = f" <b>{html.escape(accent)}</b>" if accent else ""
    st.html(f'<div class="sp-stub"><span>{html.escape(left)}{accent_html}</span>'
            f'<small>{html.escape(right)}</small></div>')
