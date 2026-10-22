from datetime import date, datetime

from core.progress import (
    COMPLETE, EATEN, ONGOING, OVER, REST,
    daily_eaten, day_result, eaten_count, next_pending, slice_statuses, slice_toppings, streak,
    topping_summary,
)
from core.schedule import TZ, slice_datetimes


def log(i, status, pizza_type="shoulder", day="2026-10-22"):
    return {"slice_idx": str(i), "status": status, "pizza_type": pizza_type, "date": day}


def test_statuses_before_anything_is_empty_pan():
    assert slice_statuses([], 3) == [None, None, None]


def test_eaten_wins_over_rest_and_ignores_other_statuses():
    logs = [log(0, REST), log(0, EATEN), log(1, "opened"), log(2, "snoozed"), log(9, EATEN)]
    assert slice_statuses(logs, 3) == [EATEN, None, None]


def test_toppings_follow_eaten_pizza_type():
    logs = [log(0, EATEN, "eyes"), log(1, REST, "closed")]
    assert slice_toppings(logs, 3) == ["eyes", None, None]


DTS = slice_datetimes(date(2026, 10, 22), "09:00", "18:00", 3)
NOON = datetime(2026, 10, 22, 12, 0, tzinfo=TZ)


def test_complete_when_all_eaten():
    assert day_result([EATEN] * 3, DTS, NOON) == COMPLETE


def test_over_when_all_handled_but_some_rested():
    assert day_result([EATEN, REST, EATEN], DTS, NOON) == OVER


def test_over_after_last_slice_plus_grace():
    late = datetime(2026, 10, 22, 19, 1, tzinfo=TZ)  # 18:00 + 60분 지남
    assert day_result([EATEN, None, None], DTS, late) == OVER
    assert day_result([EATEN, None, None], DTS, datetime(2026, 10, 22, 18, 59, tzinfo=TZ)) == ONGOING


def test_next_pending_and_count():
    assert next_pending([EATEN, None, None]) == 1
    assert next_pending([EATEN, REST, EATEN]) is None
    assert eaten_count([EATEN, REST, EATEN]) == 2


def test_topping_summary_counts_each_slice_once():
    logs = [log(0, EATEN, "shoulder"), log(0, EATEN, "shoulder"), log(1, EATEN, "eyes"), log(2, REST, "closed")]
    assert topping_summary(logs) == {"shoulder": 1, "eyes": 1}


def test_daily_eaten():
    logs = [log(0, EATEN, day="2026-10-21"), log(0, EATEN, day="2026-10-21"), log(1, EATEN, day="2026-10-22")]
    assert daily_eaten(logs) == {date(2026, 10, 21): 1, date(2026, 10, 22): 1}


def test_streak_counts_back_from_today_or_yesterday():
    d = date(2026, 10, 22)
    done = {date(2026, 10, 20), date(2026, 10, 21)}
    assert streak(done, d) == 2  # 오늘 아직 못 채워도 어제까지 이어진 기록
    assert streak(done | {d}, d) == 3
    assert streak({date(2026, 10, 19)}, d) == 0
