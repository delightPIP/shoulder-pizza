import uuid
from datetime import time

import streamlit as st

from core.pizza_art import pizza_svg
from core.pizza_types import ORDER, REST, condition, label
from core.schedule import slice_times
from core.style import ticket_stub
from core.ui import footer, get_store, now, obj
from core.weather import CITIES, DEFAULT_CITY

STEPS = 5
SLICE_OPTIONS = list(range(3, 9))  # 3~8조각
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
        "slices": min(max(int(src.get("slices") or 3), SLICE_OPTIONS[0]), SLICE_OPTIONS[-1]),
        "privacy": src.get("consent_privacy") == "true",
        "app_notice": src.get("consent_app_notice") == "true",
        "active": src.get("active", "true") != "false",
    }
    st.session_state.ob_step = 1
ob = st.session_state.ob
step = st.session_state.ob_step


def go(delta: int) -> None:
    st.session_state.ob_step = min(STEPS, max(1, st.session_state.ob_step + delta))


def bind(name: str, value) -> str:
    """위젯 key를 고정하고 처음 한 번만 값을 넣는다.

    value=/default=에 바뀐 값을 매번 넘기면 Streamlit이 다른 위젯으로 보고 방금 고른 값을 버린다
    (두 번째 선택부터 안 눌리는 버그). 단계를 넘기면 위젯 값은 사라지므로 ob에서 다시 채운다.
    """
    key = f"ob_{name}"
    if key not in st.session_state:
        st.session_state[key] = value
    return key


FIELDS = ("start", "end", "city", "app_notice", "privacy", "pizza_type", "slices", "active")


def section_time() -> None:
    st.subheader("몇 시부터 몇 시까지 알려줄까요?")
    c1, c2 = st.columns(2)
    start = c1.time_input("시작", key=bind("start", time.fromisoformat(ob["start"])), step=300)
    end = c2.time_input("끝", key=bind("end", time.fromisoformat(ob["end"])), step=300)
    ob["start"], ob["end"] = start.strftime("%H:%M"), end.strftime("%H:%M")
    st.caption("끝나는 시각이 시작보다 이르면 다음 날 새벽까지로 계산해요.")


def section_city() -> None:
    st.subheader("어느 동네에 계세요?")
    ob["city"] = st.selectbox("동네", list(CITIES), key=bind("city", ob["city"]))
    st.caption("날씨에 맞는 스트레칭을 골라 드려요.")


def section_notice() -> None:
    st.subheader("알림 메일과 동의" if existing else "앱 서비스는 준비 중이에요, 메일로 알려드릴게요.")
    st.markdown(f"받는 주소: **{email}**")
    if existing:  # 수신 거부했던 사용자도 여기서 다시 켤 수 있다
        ob["active"] = st.toggle("조각 알림 메일 받기", key=bind("active", ob["active"]))
    ob["app_notice"] = st.checkbox("앱이 나오면 메일로 알려 주세요 (선택)", key=bind("app_notice", ob["app_notice"]))
    ob["privacy"] = st.checkbox("개인정보 수집·이용에 동의해요 (필수)", key=bind("privacy", ob["privacy"]))
    with st.expander("무엇을 받고 어떻게 쓰나요?"):
        st.markdown(
            "- 받는 정보: 메일 주소, 동네, 알림 시간대, 피자 종류와 스트레칭 기록\n"
            "- 쓰는 곳: 조각 알림 메일 보내기, 오늘의 피자와 기록 보여 주기\n"
            "- 보관: 체험 기간이 끝나면 지워요. 메일 아래 링크로 언제든 알림을 끌 수 있어요\n"
            "- 동의하지 않으면 서비스를 쓸 수 없어요"
        )


def section_type() -> None:
    st.subheader("어떤 피자가 좋을지 선택해봐요.")
    options = [k for k in ORDER if k != REST]  # 휴무는 조각마다 고른다
    picked = st.pills("지금 컨디션", options, format_func=condition, key=bind("pizza_type", ob["pizza_type"]),
                      required=True, label_visibility="collapsed")
    ob["pizza_type"] = picked or ob["pizza_type"]
    st.markdown(f":material/local_pizza: {obj(label(ob['pizza_type']))} 구워 드릴게요.")
    st.caption("컨디션에 따라 맞춤 스트레칭을 안내할게요. 조각을 열 때마다 바꿀 수도 있어요.")


def section_slices() -> None:
    st.subheader("몇 조각으로 잘라줄까요?")
    ob["slices"] = st.segmented_control(
        "조각 수", SLICE_OPTIONS, key=bind("slices", ob["slices"]), required=True,
        format_func=lambda n: f"{n}조각", label_visibility="collapsed",
    ) or SLICE_OPTIONS[0]
    st.caption(f"하루에 {SLICE_OPTIONS[0]}~{SLICE_OPTIONS[-1]}번 알려 드려요.")
    times = slice_times(ob["start"], ob["end"], ob["slices"])
    with st.container(horizontal_alignment="center"):
        st.image(pizza_svg(len(times), [None] * len(times), times=times), width=300,
                 alt=f"{len(times)}조각으로 자른 빈 피자판")
    if len(times) < ob["slices"]:
        st.warning("시간대가 짧아 조각 사이 30분을 지킬 수 없어요. 첫 조각만 알려 드릴게요. 시간대를 늘려 보세요.")
    else:
        st.caption("알림 시각: " + " · ".join(times))


SECTIONS = [section_time, section_city, section_notice, section_type, section_slices]
STUBS = ["알림 시간", "동네", "알림 메일", "피자 종류", "조각 수"]


def save() -> None:
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
        "active": "true" if ob["active"] else "false",
        "created_at": existing["created_at"] if existing else now().isoformat(timespec="seconds"),
    })
    st.session_state.user = user
    st.session_state.pending_email = None
    del st.session_state["ob"]
    for name in FIELDS:
        st.session_state.pop(f"ob_{name}", None)
    st.session_state["settings_saved" if existing else "just_baked"] = True
    st.switch_page("app_pages/pizza.py")


if existing:
    # 가입한 사용자: 한 화면에서 모두 보고 바로 저장한다
    st.title("설정")
    st.caption("바꾸고 싶은 것만 고치고 저장하세요. 오늘 먹은 조각 기록은 그대로 남아요.")
    for i, section in enumerate(SECTIONS):
        with st.container(key=f"ticket-set-{i}"):
            ticket_stub(STUBS[i])
            section()
    if st.button("저장하기", key="ob_save", type="primary", icon=":material/save:", width="stretch",
                 disabled=not ob["privacy"]):
        save()
else:
    st.title("피자 주문서")
    with st.container(key="ticket-step"):
        ticket_stub(STUBS[step - 1], f"{step} / {STEPS}")
        SECTIONS[step - 1]()
    row = st.container(horizontal=True, horizontal_alignment="distribute")
    if step > 1:
        row.button("이전", key="ob_prev", icon=":material/arrow_back:", on_click=go, args=(-1,))
    else:
        row.space()
    if step < STEPS:
        row.button("다음", key="ob_next", type="primary", on_click=go, args=(1,),
                   disabled=step == 3 and not ob["privacy"])
    elif row.button("피자 굽기", key="ob_bake", type="primary", icon=":material/local_pizza:"):
        save()

footer()
