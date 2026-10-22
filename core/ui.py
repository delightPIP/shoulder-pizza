"""페이지들이 같이 쓰는 도우미: 저장소, 오늘의 피자 상태, 기록 남기기, 하단 문구."""
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import streamlit as st

from core.config import get_secret, local_store_path, service_account_info
from core.progress import day_result, slice_statuses, slice_toppings
from core.schedule import TZ, pizza_day, slice_datetimes, slice_times
from core.store import make_store

POSTURE_LABEL = {"chair": "의자", "stand": "서서", "lying": "누워서"}
DISCLAIMER = "의료 조언이 아닙니다. 통증이 있으면 멈추세요."


@st.cache_resource(show_spinner=False)
def _store(sheet_id: str, path: str):
    return make_store(sheet_id or None, service_account_info() if sheet_id else None, Path(path))


def get_store():
    return _store(get_secret("GOOGLE_SHEET_ID") or "", str(local_store_path()))


def now() -> datetime:
    return datetime.now(TZ)


def slice_label(i: int, n: int) -> str:
    if i == 0:
        return "시작 한 조각"
    if i == n - 1:
        return "마무리 한 조각"
    return "한 조각 더"


@dataclass
class Today:
    day: date
    now: datetime
    times: list[str]
    dts: list[datetime]
    logs: list[dict]
    statuses: list[str | None]
    toppings: list[str | None]
    result: str

    @property
    def n(self) -> int:
        return len(self.times)


def _logs_key(uid: str, day: date) -> str:
    return f"logs:{uid}:{day.isoformat()}"


def day_logs(uid: str, day: date) -> list[dict]:
    """하루치 기록. Sheets 읽기 한도를 아끼려고 세션에 담아 두고, 쓸 때만 비운다."""
    key = _logs_key(uid, day)
    if key not in st.session_state:
        st.session_state[key] = get_store().logs(uid, since=day, until=day)
    return st.session_state[key]


def today_context(user: dict) -> Today:
    current = now()
    start, end, n = user["window_start"], user["window_end"], int(user["slices"])
    day = pizza_day(current, start, end)
    times = slice_times(start, end, n)
    dts = slice_datetimes(day, start, end, n)
    logs = day_logs(user["uid"], day)
    statuses = slice_statuses(logs, len(times))
    return Today(day, current, times, dts, logs, statuses, slice_toppings(logs, len(times)),
                 day_result(statuses, dts, current))


def add_log(user: dict, day: date, slice_idx: int, status: str, *, pizza_type: str = "",
            exercise_id: str = "", weather: str = "") -> None:
    get_store().add_log({
        "uid": user["uid"], "date": day.isoformat(), "slice_idx": slice_idx, "pizza_type": pizza_type,
        "exercise_id": exercise_id, "status": status, "weather": weather, "ts": now().isoformat(timespec="seconds"),
    })
    st.session_state.pop(_logs_key(user["uid"], day), None)


def footer(sources: str = "날씨 Open-Meteo · 동작 API Ninjas, free-exercise-db · 번역 MyMemory") -> None:
    st.divider()
    st.caption(f":material/health_and_safety: {DISCLAIMER}  \n데이터: {sources}")
    if get_store().backend == "file":
        st.caption("기록은 이 서버에 임시로 저장돼요 (Google Sheets 미연결).")
