import streamlit as st

from core.illustrations import stamp
from core.pizza_art import pizza_svg
from core.pizza_types import label
from core.progress import (
    COMPLETE, EATEN, GAVE_UP, ONGOING, OVER, REST,
    daily_eaten, eaten_count, gave_up, next_pending, streak, topping_summary,
)
from core.schedule import minutes_until
from core.style import ticket_stub
from core.ui import add_log, footer, get_store, korean_date, now, slice_label, today_context, topic
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
if st.session_state.pop("settings_saved", False):
    st.toast("설정을 저장했어요.", icon=":material/save:")
if fresh is not None:
    st.toast(f"조각 완성! {eaten}/{t.n}", icon="🍕")
if st.session_state.pop("snoozed", False):
    st.toast("30분 뒤에 다시 알려 드릴게요.", icon=":material/snooze:")

st.title("오늘의 피자")
st.caption(korean_date(t.day))
if weather:
    a = advice(weather["category"], weather["temp"], user["pizza_type"])
    line = f"{a['icon']} {topic(user['city'])} 지금 {a['label']}"
    line += f", {weather['temp']:.0f}℃예요." if weather["temp"] is not None else "이에요."
    st.markdown(line)
    notes = [a["message"], a["temp_note"]] if t.result == ONGOING else []  # 하루가 끝났으면 권유하지 않는다
    if weather["pm25"] is not None:
        notes.append(f"초미세먼지 {weather['pm25']:.0f}㎍/㎥ (참고용)")
    if any(notes):
        st.caption("  \n".join(x for x in notes if x))

nxt = next_pending(t.statuses) if t.result == ONGOING else None
face = {COMPLETE: "happy", OVER: "frown"}.get(t.result)
with st.container(horizontal_alignment="center"):
    st.image(pizza_svg(t.n, t.statuses, t.toppings, times=t.times, highlight=nxt, fresh=fresh, face=face),
             width=360, alt=f"오늘의 피자: {t.n}조각 중 {eaten}조각 완성")
st.progress(eaten / t.n, text=f"{eaten} / {t.n} 조각 완성")

if t.result == COMPLETE:
    if not st.session_state.get(f"celebrated:{t.day}"):
        st.balloons()
        st.session_state[f"celebrated:{t.day}"] = True
    history = get_store().logs(user["uid"], until=t.day)
    done_days = {d for d, c in daily_eaten(history).items() if c >= t.n}
    days = streak(done_days, t.day)
    with st.container(key="ticket-done"):
        ticket_stub("한 판 완성!", korean_date(t.day))
        st.markdown("따끈따끈한 어깨 피자가 나왔어요. 오늘 하루도 몸을 잘 챙겼어요.")
        summary = topping_summary(t.logs)
        st.markdown("오늘의 토핑 " + " ".join(f":orange-badge[{label(k)} ×{c}]" for k, c in summary.items()))
        st.markdown(f":material/local_fire_department: **{days}일** 연속으로 한 판을 구웠어요"
                    if days > 1 else ":material/local_fire_department: 내일도 구우면 연속 기록이 시작돼요")
        st.page_link("app_pages/record.py", label="단골 도장판 보기", icon=":material/calendar_month:")

elif t.result == OVER:
    with st.container(key="ticket-over"):
        ticket_stub("오늘 영업 끝", korean_date(t.day))
        if gave_up(t.logs):
            st.markdown("오늘은 여기까지 하기로 했어요. 쉬는 것도 중요해요.")
        st.markdown(f"오늘은 {eaten}조각을 먹었어요." if eaten else "오늘은 조각을 먹지 못했어요.")
        st.markdown("괜찮아, 내일 또 맛있게 구워보자.")
        st.subheader("인상 피자 😎")  # 마지막 한마디는 간판 글꼴로 크게

else:

    @st.fragment(run_every=30)  # 초 단위 숫자 (문자열 "30s"는 내부에서 pandas를 불러온다)
    def countdown():
        left = minutes_until(t.dts[nxt], now())
        if left == 0:
            st.markdown(f":material/local_pizza: 지금 {nxt + 1}번째 조각을 먹을 시간이에요!")
            if not st.session_state.get(f"toasted:{t.day}:{nxt}"):
                st.toast("한 조각 먹을 시간이에요", icon="🍕")
                st.session_state[f"toasted:{t.day}:{nxt}"] = True
        else:
            h, m = divmod(left, 60)
            st.markdown(f":material/schedule: 다음 조각까지 {f'{h}시간 ' if h else ''}{m}분 남았어요.")

    # 확인 창이 열려 있는지는 세션에 둔다 (창 안 버튼을 누른 실행에서도 창과 버튼이 있어야 클릭이 처리된다)
    def close_give_up():
        st.session_state.pop("confirm_give_up", None)

    def give_up():
        add_log(user, t.day, -1, GAVE_UP)
        close_give_up()
        st.rerun()

    @st.dialog("오늘은 여기까지 할까요?", icon=":material/sentiment_dissatisfied:", on_dismiss=close_give_up)
    def confirm_give_up():
        st.markdown(f"남은 {t.n - eaten}조각은 오늘 먹지 않은 걸로 남기고, 오늘 알림 메일도 멈출게요.")
        row = st.container(horizontal=True)
        row.button("네, 오늘은 못하겠어요", key="give_up_yes", type="primary", on_click=give_up)
        row.button("조금 더 해 볼게요", key="give_up_no", on_click=close_give_up)

    with st.container(key="ticket-next"):
        ticket_stub("다음 조각", slice_label(nxt, t.n), accent=t.times[nxt])
        countdown()
        if st.button("지금 한 조각 먹기", key="eat_now", type="primary", icon=":material/local_pizza:",
                     width="stretch"):
            st.session_state.current_slice = nxt
            st.switch_page("app_pages/slice.py")
        st.caption("알림 메일은 조각 시각에 맞춰 보내요. 몇 분 늦을 수 있어요.")
    st.button("오늘은 더 이상 못하겠어요", key="give_up", type="tertiary", icon=":material/sentiment_dissatisfied:",
              on_click=lambda: st.session_state.update(confirm_give_up=True))
    if st.session_state.get("confirm_give_up"):
        confirm_give_up()

st.subheader("오늘의 메뉴판")
for i, hhmm in enumerate(t.times):
    status = t.statuses[i]
    row = st.container(key=f"menu-{i}", horizontal=True, vertical_alignment="center",
                       horizontal_alignment="distribute")
    text = row.container(gap=None)
    text.markdown(f"**{hhmm}** {slice_label(i, t.n)}")
    if t.toppings[i]:
        text.caption(label(t.toppings[i]))
    if status in (EATEN, REST):
        row.image(stamp("done" if status == EATEN else "rest"), width=48,
                  alt="완성 도장" if status == EATEN else "쉼 도장")
    elif t.result == ONGOING:
        if t.dts[i] <= t.now:  # 시각이 된 조각만 바로 먹으러 간다 (미리 먹기는 '지금 한 조각 먹기')
            if row.button("먹으러 가기", key=f"go_{i}", icon=":material/arrow_forward:"):
                st.session_state.current_slice = i
                st.switch_page("app_pages/slice.py")
        else:
            row.caption(":material/notifications: 알림 예정")

# 휴대폰에서는 상단 메뉴가 사이드바 안으로 숨어서 바로가기를 둔다
links = st.container(horizontal=True, horizontal_alignment="center")
links.page_link("app_pages/record.py", label="단골 도장판", icon=":material/calendar_month:")
links.page_link("app_pages/onboarding.py", label="설정", icon=":material/edit_note:")

footer()
