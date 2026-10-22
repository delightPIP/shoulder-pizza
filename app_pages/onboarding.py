import uuid
from datetime import time

import streamlit as st

from core.pizza_art import pizza_svg
from core.pizza_types import ORDER, REST, label
from core.schedule import slice_times
from core.ui import footer, get_store, now
from core.weather import CITIES, DEFAULT_CITY

STEPS = 5
existing = st.session_state.user
email = existing["email"] if existing else st.session_state.pending_email
if not email:
    st.switch_page("app_pages/landing.py")

if "ob" not in st.session_state:
    src = existing or {}
    st.session_state.ob = {
        "start": src.get("window_start") or "09:00",
        "end": src.get("window_end") or "18:00",
        "city": src.get("city") if src.get("city") in CITIES else DEFAULT_CITY,
        "pizza_type": src.get("pizza_type") if src.get("pizza_type") in ORDER else "shoulder",
        "slices": int(src.get("slices") or 3),
        "privacy": src.get("consent_privacy") == "true",
        "app_notice": src.get("consent_app_notice") == "true",
    }
    st.session_state.ob_step = 1
ob = st.session_state.ob
step = st.session_state.ob_step


def go(delta: int) -> None:
    st.session_state.ob_step = min(STEPS, max(1, st.session_state.ob_step + delta))


st.title("주문서 고치기" if existing else "피자 주문서")
st.progress(step / STEPS, text=f"{step} / {STEPS}")

with st.container(border=True):
    if step == 1:
        st.subheader("몇 시부터 몇 시까지 알려줄까요?")
        c1, c2 = st.columns(2)
        start = c1.time_input("시작", value=time.fromisoformat(ob["start"]), step=300)
        end = c2.time_input("끝", value=time.fromisoformat(ob["end"]), step=300)
        ob["start"], ob["end"] = start.strftime("%H:%M"), end.strftime("%H:%M")
        st.caption("끝나는 시각이 시작보다 이르면 다음 날 새벽까지로 계산해요.")

    elif step == 2:
        st.subheader("어느 동네에 계세요?")
        cities = list(CITIES)
        ob["city"] = st.selectbox("동네", cities, index=cities.index(ob["city"]))
        st.caption("날씨에 맞는 스트레칭을 골라 드려요.")

    elif step == 3:
        st.subheader("앱 서비스는 준비 중이에요, 메일로 알려드릴게요.")
        st.markdown(f"받는 주소: **{email}**")
        ob["app_notice"] = st.checkbox("앱이 나오면 메일로 알려 주세요 (선택)", value=ob["app_notice"])
        ob["privacy"] = st.checkbox("개인정보 수집·이용에 동의해요 (필수)", value=ob["privacy"], key="ob_privacy")
        with st.expander("무엇을 받고 어떻게 쓰나요?"):
            st.markdown(
                "- 받는 정보: 메일 주소, 동네, 알림 시간대, 피자 종류와 스트레칭 기록\n"
                "- 쓰는 곳: 조각 알림 메일 보내기, 오늘의 피자와 기록 보여 주기\n"
                "- 보관: 체험 기간이 끝나면 지워요. 메일 아래 링크로 언제든 알림을 끌 수 있어요\n"
                "- 동의하지 않으면 서비스를 쓸 수 없어요"
            )

    elif step == 4:
        st.subheader("어떤 피자가 좋을지 선택해봐요.")
        options = [k for k in ORDER if k != REST]  # 휴무는 조각마다 고른다
        picked = st.pills("피자 종류", options, format_func=label, default=ob["pizza_type"],
                          required=True, label_visibility="collapsed")
        ob["pizza_type"] = picked or ob["pizza_type"]
        st.caption("컨디션에 따라 맞춤 스트레칭을 안내할게요. 조각을 열 때마다 바꿀 수도 있어요.")

    else:
        st.subheader("몇 조각으로 잘라줄까요?")
        ob["slices"] = st.segmented_control("조각 수", [3, 4, 5], default=ob["slices"], required=True,
                                            format_func=lambda n: f"{n}조각", label_visibility="collapsed") or 3
        st.caption("하루에 3~5번 알려 드려요.")
        times = slice_times(ob["start"], ob["end"], ob["slices"])
        st.image(pizza_svg(len(times), [None] * len(times), times=times), width=300,
                 alt=f"{len(times)}조각으로 자른 빈 피자판")
        if len(times) < ob["slices"]:
            st.warning("시간대가 짧아 조각 사이 30분을 지킬 수 없어요. 첫 조각만 알려 드릴게요. 시간대를 늘려 보세요.")
        else:
            st.caption("알림 시각: " + " · ".join(times))

row = st.container(horizontal=True, horizontal_alignment="distribute")
if step > 1:
    row.button("이전", key="ob_prev", icon=":material/arrow_back:", on_click=go, args=(-1,))
else:
    row.space()
if step < STEPS:
    row.button("다음", key="ob_next", type="primary", on_click=go, args=(1,),
               disabled=step == 3 and not ob["privacy"])
elif row.button("피자 굽기", key="ob_bake", type="primary", icon=":material/local_pizza:"):
    if not ob["privacy"]:
        st.error("개인정보 수집·이용에 동의해야 시작할 수 있어요.")
        st.stop()
    user = get_store().save_user({
        **(existing or {}),
        "uid": existing["uid"] if existing else uuid.uuid4().hex,
        "email": email,
        "city": ob["city"],
        "window_start": ob["start"],
        "window_end": ob["end"],
        "slices": ob["slices"],
        "pizza_type": ob["pizza_type"],
        "consent_privacy": "true",
        "consent_app_notice": "true" if ob["app_notice"] else "false",
        "active": "true",
        "created_at": existing["created_at"] if existing else now().isoformat(timespec="seconds"),
    })
    st.session_state.user = user
    st.session_state.pending_email = None
    del st.session_state["ob"]
    st.session_state.just_baked = True
    st.switch_page("app_pages/pizza.py")

footer()
