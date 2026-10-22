from collections import Counter
from datetime import timedelta

import streamlit as st

from core.pizza_art import calendar_svg
from core.pizza_types import label
from core.progress import EATEN, daily_eaten, streak
from core.ui import footer, get_store, today_context

DAYS = 30
user = st.session_state.user
t = today_context(user)
since = t.day - timedelta(days=DAYS - 1)
logs = get_store().logs(user["uid"], since=since, until=t.day)

per_day = daily_eaten(logs)
done_days = {d for d, c in per_day.items() if c >= t.n}

st.title("기록")
cols = st.columns(3)
cols[0].metric("연속으로 구운 날", f"{streak(done_days, t.day)}일")
cols[1].metric(f"최근 {DAYS}일 완성한 판", f"{len(done_days)}판")
cols[2].metric(f"최근 {DAYS}일 먹은 조각", f"{sum(per_day.values())}조각")

st.subheader("피자 달력")
days = [(since + timedelta(days=k), per_day.get(since + timedelta(days=k), 0), t.n) for k in range(DAYS)]
st.image(calendar_svg(days, t.day), width="content", alt=f"최근 {DAYS}일 동안 날짜별로 채운 피자 조각")
st.caption("다 채운 날은 페퍼로니 피자, 덜 채운 날은 먹은 만큼만 채워져요. 빨간 테두리가 오늘이에요.")

st.subheader("어떤 피자를 많이 먹었나요?")
eaten = {(r["date"], r["slice_idx"]): r["pizza_type"] for r in logs if r["status"] == EATEN and r["pizza_type"]}
counts = Counter(eaten.values())
if counts:
    # 막대 차트(st.bar_chart)는 pandas가 필요해 가벼운 막대로 그린다
    top = max(counts.values())
    for key, c in counts.most_common():
        st.progress(c / top, text=f"{label(key)} · {c}조각")
else:
    st.caption("아직 먹은 조각이 없어요. 첫 조각을 구워 볼까요?")

footer()
