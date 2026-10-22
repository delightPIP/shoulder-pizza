from collections import Counter
from datetime import timedelta

import streamlit as st

from core.pizza_art import calendar_svg
from core.pizza_types import label
from core.progress import EATEN, daily_eaten, streak
from core.style import ticket_stub
from core.ui import footer, get_store, today_context

DAYS = 30
user = st.session_state.user
t = today_context(user)
since = t.day - timedelta(days=DAYS - 1)
logs = get_store().logs(user["uid"], since=since, until=t.day)

per_day = daily_eaten(logs)
done_days = {d for d, c in per_day.items() if c >= t.n}

st.title("단골 도장판")
st.caption(f"최근 {DAYS}일 동안 구운 피자예요.")
stats = st.container(horizontal=True, gap="small")  # 휴대폰에서도 한 줄에 나란히
stats.metric("연속 기록", f"{streak(done_days, t.day)}일")
stats.metric("완성", f"{len(done_days)}판")
stats.metric("먹은 조각", f"{sum(per_day.values())}조각")

with st.container(key="ticket-stamps"):
    ticket_stub("도장판", f"{since.month}/{since.day} ~ {t.day.month}/{t.day.day}")
    days = [(since + timedelta(days=k), per_day.get(since + timedelta(days=k), 0), t.n) for k in range(DAYS)]
    with st.container(horizontal_alignment="center"):
        st.image(calendar_svg(days, t.day), width="content", alt=f"최근 {DAYS}일 동안 날짜별로 채운 피자 조각")
    st.caption("한 판을 다 채운 날에는 토마토 도장을 찍어요. 덜 채운 날은 먹은 만큼 치즈가 차요. 굵은 테두리가 오늘이에요.")

st.subheader("어떤 피자를 많이 먹었나요?")
eaten = {(r["date"], r["slice_idx"]): r["pizza_type"] for r in logs if r["status"] == EATEN and r["pizza_type"]}
counts = Counter(eaten.values())
if counts:
    # 막대 차트(st.bar_chart)는 pandas가 필요해 가벼운 막대로 그린다
    top = max(counts.values())
    for key, c in counts.most_common():
        st.progress(c / top, text=f"{label(key)} {c}조각")
else:
    st.caption("아직 먹은 조각이 없어요. 오늘의 피자에서 첫 조각을 구워 보세요.")

footer()
