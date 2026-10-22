import math
import time

import streamlit as st

from core.card import render_card
from core.exercises import build_candidates
from core.pizza_types import ORDER, REST, label
from core.progress import EATEN, OPENED, SNOOZED, gave_up, next_pending
from core.progress import REST as REST_STATUS
from core.ui import POSTURE_LABEL, add_log, footer, today_context
from core.weather import advice

user = st.session_state.user
t = today_context(user)
weather = st.session_state.get("weather")

if gave_up(t.logs):
    st.title("한 조각 먹기")
    st.info("오늘은 여기까지 하기로 했어요. 내일 또 맛있게 구워 봐요.", icon=":material/bedtime:")
    st.page_link("app_pages/pizza.py", label="오늘의 피자", icon=":material/local_pizza:")
    footer()
    st.stop()

idx = st.session_state.get("current_slice")
if idx is None or not 0 <= idx < t.n or t.statuses[idx] is not None:
    idx = next_pending(t.statuses)
if idx is None:
    st.title("한 조각 먹기")
    st.success("오늘 조각을 모두 챙겼어요. 피자를 보러 갈까요?", icon=":material/local_pizza:")
    st.page_link("app_pages/pizza.py", label="오늘의 피자", icon=":material/local_pizza:")
    footer()
    st.stop()
st.session_state.current_slice = idx

if st.session_state.pop("opened_from_mail", False):
    add_log(user, t.day, idx, OPENED)

st.title(f"{idx + 1}번째 조각")

type_key = f"type:{t.day}:{idx}"
if st.session_state.get(type_key) not in ORDER:
    st.session_state[type_key] = user["pizza_type"] if user["pizza_type"] in ORDER else "shoulder"
choice = st.pills("지금 컨디션은 어때요?", ORDER, format_func=label, key=type_key, required=True)
header = f"{t.times[idx]} 조각 · {label(choice)}"

if choice == REST:
    with st.container(border=True):
        st.caption(header)
        st.subheader("오늘은 휴무")
        st.markdown("무리하지 말고 쉬어요. 이 조각은 '쉼'으로 남겨 둘게요.")
        st.warning("통증이 계속되면 전문의와 상담하세요.", icon=":material/health_and_safety:")
    if st.button("쉼으로 표시하고 돌아가기", key="rest_done", type="primary"):
        add_log(user, t.day, idx, REST_STATUS, pizza_type=REST)
        st.session_state.pop("current_slice", None)
        st.switch_page("app_pages/pizza.py")
    footer()
    st.stop()

tip = advice(weather["category"], weather["temp"], choice) if weather else None
posture_key = f"posture:{t.day}:{idx}"
if st.session_state.get(posture_key) not in POSTURE_LABEL:
    st.session_state[posture_key] = tip["posture"] if tip else "chair"
posture = st.segmented_control("자세", list(POSTURE_LABEL), format_func=POSTURE_LABEL.get, key=posture_key,
                               required=True)
if tip and (tip["message"] or tip["temp_note"]):
    st.caption(f"{tip['icon']} {tip['label']} · " + " ".join(x for x in (tip["message"], tip["temp_note"]) if x))

cache = st.session_state.setdefault("candidates", {})
if (choice, posture) not in cache:
    with st.spinner("오늘의 동작을 고르는 중이에요..."):
        cache[(choice, posture)] = build_candidates(choice, posture, seed=t.day.toordinal())
items, source, note = cache[(choice, posture)]
if tip and tip["prefer"]:
    items = sorted(items, key=lambda i: 0 if i["id"] in tip["prefer"] else 1)

if not items:
    st.warning("이 자세로 할 수 있는 동작이 없어요. 다른 자세를 골라 보세요.")
    footer()
    st.stop()

cursor_key = f"cursor:{choice}:{posture}"
cursor = st.session_state.get(cursor_key, 0) % len(items)
item = items[cursor]
if note:
    st.caption(note)
render_card(item, header=header, key=f"card:{item['id']}")

# 30초 타이머 (동작마다 따로)
timer_key = f"timer:{t.day}:{idx}:{item['id']}"
seconds = int(item.get("seconds") or 30)
if timer_key not in st.session_state:
    st.button(f"{seconds}초 타이머 시작", key="timer_start", icon=":material/timer:",
              on_click=lambda: st.session_state.update({timer_key: time.time() + seconds}))
elif st.session_state[timer_key] > time.time():

    @st.fragment(run_every=1)
    def timer():
        left = st.session_state.get(timer_key, 0) - time.time()
        if left <= 0:
            st.rerun()  # 앱 전체를 다시 그려 타이머를 끝낸다
        st.progress(1 - left / seconds, text=f"{math.ceil(left)}초 남았어요. 천천히 숨 쉬어요.")

    timer()
else:
    st.success("다 했어요! '다 먹었어요'를 눌러 조각을 채워요.", icon=":material/check_circle:")

row = st.container(horizontal=True)
if row.button(f"다른 동작 ({cursor + 1}/{len(items)})", key="next_move", icon=":material/refresh:",
              disabled=len(items) < 2):
    st.session_state[cursor_key] = cursor + 1
    st.rerun()
if row.button("다 먹었어요", key="done", type="primary", icon=":material/check_circle:"):
    add_log(user, t.day, idx, EATEN, pizza_type=choice, exercise_id=item["id"],
            weather=weather["category"] if weather else "")
    st.session_state.fresh_slice = idx
    st.session_state.pop("current_slice", None)
    st.switch_page("app_pages/pizza.py")
if row.button("30분 뒤 다시", key="snooze", icon=":material/snooze:"):
    add_log(user, t.day, idx, SNOOZED, pizza_type=choice)
    st.session_state.snoozed = True
    st.session_state.pop("current_slice", None)
    st.switch_page("app_pages/pizza.py")

footer()
