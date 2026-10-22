import streamlit as st

from core.pizza_art import pizza_svg
from core.pizza_types import label
from core.progress import COMPLETE, EATEN, ONGOING, OVER, REST, daily_eaten, eaten_count, next_pending, streak, topping_summary
from core.schedule import minutes_until
from core.ui import footer, get_store, now, slice_label, today_context
from core.weather import advice

user = st.session_state.user
if not user:  # 로그아웃 상태에서 들어온 경우
    st.switch_page("app_pages/landing.py")
t = today_context(user)
weather = st.session_state.get("weather")
fresh = st.session_state.pop("fresh_slice", None)
eaten = eaten_count(t.statuses)

if st.session_state.pop("just_baked", False):
    st.toast("피자 반죽 완료! 첫 조각을 기다려요.", icon="🍕")
if fresh is not None:
    st.toast(f"조각 완성! {eaten}/{t.n}", icon="🍕")
if st.session_state.pop("snoozed", False):
    st.toast("30분 뒤에 다시 알려 드릴게요.", icon=":material/snooze:")

st.title("오늘의 피자")
if weather:
    a = advice(weather["category"], weather["temp"], user["pizza_type"])
    line = f"{a['icon']} {user['city']} {a['label']}"
    if weather["temp"] is not None:
        line += f" · {weather['temp']:.0f}℃"
    if weather["pm25"] is not None:
        line += f" · 초미세먼지 {weather['pm25']:.0f}㎍/㎥ (참고용)"
    st.caption(line)
    if a["message"] or a["temp_note"]:
        st.caption(" ".join(x for x in (a["message"], a["temp_note"]) if x))

st.progress(eaten / t.n, text=f"{eaten} / {t.n} 조각 완성")

nxt = next_pending(t.statuses) if t.result == ONGOING else None
face = {COMPLETE: "happy", OVER: "frown"}.get(t.result)
st.image(pizza_svg(t.n, t.statuses, t.toppings, times=t.times, highlight=nxt, fresh=fresh, face=face),
         width=340, alt=f"오늘의 피자: {t.n}조각 중 {eaten}조각 완성")

if t.result == COMPLETE:
    if not st.session_state.get(f"celebrated:{t.day}"):
        st.balloons()
        st.session_state[f"celebrated:{t.day}"] = True
    history = get_store().logs(user["uid"], until=t.day)
    done_days = {d for d, c in daily_eaten(history).items() if c >= t.n}
    with st.container(border=True):
        st.subheader("한 판 완성! 따끈따끈한 어깨 피자가 나왔어요")
        summary = topping_summary(t.logs)
        st.markdown("오늘의 토핑: " + " + ".join(f"**{label(k)}** {c}조각" for k, c in summary.items()))
        st.metric("연속으로 구운 날", f"{streak(done_days, t.day)}일")
        st.page_link("app_pages/record.py", label="기록 보러 가기", icon=":material/calendar_month:")

elif t.result == OVER:
    with st.container(border=True):
        st.markdown(f"오늘은 {eaten}조각을 먹었어요." if eaten else "오늘은 조각을 먹지 못했어요.")
        st.subheader("괜찮아, 내일 또 맛있게 구워보자. 인상 피자^^")

else:

    @st.fragment(run_every=30)  # 초 단위 숫자 (문자열 "30s"는 내부에서 pandas를 불러온다)
    def countdown():
        due = t.dts[nxt]
        left = minutes_until(due, now())
        if left == 0:
            st.success(f"지금 {nxt + 1}번째 조각을 먹을 시간이에요!", icon=":material/local_pizza:")
            if not st.session_state.get(f"toasted:{t.day}:{nxt}"):
                st.toast("한 조각 먹을 시간이에요", icon="🍕")
                st.session_state[f"toasted:{t.day}:{nxt}"] = True
        else:
            h, m = divmod(left, 60)
            st.info(f"다음 조각({t.times[nxt]})까지 {f'{h}시간 ' if h else ''}{m}분 남았어요",
                    icon=":material/schedule:")

    countdown()
    if st.button("지금 한 조각 먹기", key="eat_now", type="primary", icon=":material/local_pizza:", width="stretch"):
        st.session_state.current_slice = nxt
        st.switch_page("app_pages/slice.py")
    st.caption("알림 메일은 조각 시각에 맞춰 보내요. 몇 분 늦을 수 있어요.")

st.subheader("오늘의 조각")
for i, hhmm in enumerate(t.times):
    status = t.statuses[i]
    row = st.container(horizontal=True, vertical_alignment="center", border=True)
    mark = {EATEN: ":green-badge[:material/check: 완성]", REST: ":gray-badge[쉼]"}.get(status, ":orange-badge[빈 판]")
    topping = f" · {label(t.toppings[i])}" if t.toppings[i] else ""
    row.markdown(f"**{hhmm}** {slice_label(i, t.n)} {mark}{topping}")
    if status is None and t.result == ONGOING:
        if row.button("먹으러 가기", key=f"go_{i}", icon=":material/arrow_forward:"):
            st.session_state.current_slice = i
            st.switch_page("app_pages/slice.py")

footer()
