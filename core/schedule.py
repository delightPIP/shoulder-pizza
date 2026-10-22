"""알림 시각 계산. 순수 함수만 둔다. 앱(pizza 페이지)과 메일러가 함께 쓴다."""
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Seoul")
MIN_GAP = 30  # 조각 사이 최소 간격(분)
ROUND_TO = 5  # 분 단위 반올림


def _to_minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def _round(minutes: float) -> int:
    return int(minutes / ROUND_TO + 0.5) * ROUND_TO


def slice_minutes(start: str, end: str, n: int) -> list[int]:
    """시작 시각 0시 기준 분. 자정을 넘기면 1440 이상이 될 수 있다."""
    s, e = _to_minutes(start), _to_minutes(end)
    if e <= s:
        e += 24 * 60
    if n <= 1 or (e - s) < MIN_GAP * (n - 1):
        return [s]
    return [_round(s + (e - s) * i / (n - 1)) for i in range(n)]


def slice_times(start: str, end: str, n: int) -> list[str]:
    """알림 시각을 "HH:MM" 문자열로 돌려준다. 자정을 넘기면 다음 날 시각으로 표시한다."""
    return [f"{(m // 60) % 24:02d}:{m % 60:02d}" for m in slice_minutes(start, end, n)]


def slice_datetimes(day: date, start: str, end: str, n: int) -> list[datetime]:
    """day 하루의 알림 시각(Asia/Seoul). 자정을 넘긴 조각은 다음 날 날짜가 된다."""
    base = datetime.combine(day, time(0, 0), tzinfo=TZ)
    return [base + timedelta(minutes=m) for m in slice_minutes(start, end, n)]


def pizza_day(now: datetime, start: str, end: str, grace: int = 60) -> date:
    """now가 속한 '피자 하루'의 날짜. 자정을 넘기는 시간대라면 새벽은 전날 피자에 속한다."""
    s, e = _to_minutes(start), _to_minutes(end)
    local = now.astimezone(TZ)
    now_min = local.hour * 60 + local.minute
    if e <= s and now_min <= e + grace and now_min < s:
        return local.date() - timedelta(days=1)
    return local.date()


def minutes_until(target: datetime, now: datetime) -> int:
    """target까지 남은 분(올림). 이미 지났으면 0."""
    seconds = (target - now).total_seconds()
    return max(0, int(-(-seconds // 60)))
