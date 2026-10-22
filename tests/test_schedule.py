from datetime import date, datetime

from core.schedule import TZ, minutes_until, slice_datetimes, slice_times


def test_three_slices_in_workday():
    assert slice_times("09:00", "18:00", 3) == ["09:00", "13:30", "18:00"]


def test_four_slices_in_workday():
    assert slice_times("09:00", "18:00", 4) == ["09:00", "12:00", "15:00", "18:00"]


def test_five_slices_round_to_five_minutes():
    assert slice_times("09:00", "18:00", 5) == ["09:00", "11:15", "13:30", "15:45", "18:00"]


def test_window_crossing_midnight():
    assert slice_times("22:00", "02:00", 3) == ["22:00", "00:00", "02:00"]


def test_rounding_to_five_minutes():
    # 09:00~12:10, 3조각 → 중간 10:35 (385분이 아니라 5분 단위로 반올림)
    assert slice_times("09:00", "12:10", 3) == ["09:00", "10:35", "12:10"]


def test_single_slice():
    assert slice_times("09:00", "18:00", 1) == ["09:00"]


def test_window_too_short_falls_back_to_first_slice():
    # 30분 간격을 지킬 수 없으면 첫 조각만 남긴다
    assert slice_times("09:00", "09:45", 3) == ["09:00"]


def test_same_start_and_end_means_24_hours():
    assert slice_times("08:00", "08:00", 3) == ["08:00", "20:00", "08:00"]


def test_datetimes_roll_over_to_next_day():
    got = slice_datetimes(date(2026, 10, 22), "22:00", "02:00", 3)
    assert [d.strftime("%m-%d %H:%M") for d in got] == ["10-22 22:00", "10-23 00:00", "10-23 02:00"]
    assert all(d.tzinfo == TZ for d in got)


def test_minutes_until():
    now = datetime(2026, 10, 22, 12, 0, tzinfo=TZ)
    assert minutes_until(datetime(2026, 10, 22, 13, 30, tzinfo=TZ), now) == 90
    assert minutes_until(datetime(2026, 10, 22, 12, 0, 30, tzinfo=TZ), now) == 1  # 올림
    assert minutes_until(datetime(2026, 10, 22, 11, 0, tzinfo=TZ), now) == 0  # 지났으면 0
