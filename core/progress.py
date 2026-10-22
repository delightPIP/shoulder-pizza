"""오늘의 피자 진행 상태 계산. 순수 함수만 둔다 (logs → 조각 상태 → 하루 결과)."""
from collections import Counter
from datetime import date, datetime, timedelta

EATEN = "eaten"
REST = "rest"
OPENED = "opened"
SNOOZED = "snoozed"
GAVE_UP = "gave_up"  # "오늘은 더 이상 못하겠어요": 그날을 실패로 마감한다 (slice_idx는 -1)

ONGOING = "ongoing"
COMPLETE = "complete"  # 한 판을 모두 먹었다
OVER = "over"  # 하루가 끝났는데 다 채우지 못했다

GRACE_MINUTES = 60  # 마지막 조각 시각 뒤 이만큼 지나면 하루가 끝난 것으로 본다


def slice_statuses(logs: list[dict], n: int) -> list[str | None]:
    """조각별 상태. 먹었으면 eaten, 쉬었으면 rest, 아니면 None. 먹은 기록이 쉼보다 우선한다."""
    statuses: list[str | None] = [None] * n
    for row in logs:
        i = int(row["slice_idx"])
        if not 0 <= i < n:
            continue
        if row["status"] == EATEN:
            statuses[i] = EATEN
        elif row["status"] == REST and statuses[i] is None:
            statuses[i] = REST
    return statuses


def slice_toppings(logs: list[dict], n: int) -> list[str | None]:
    """먹은 조각에 올라간 피자 종류 (그림의 토핑 모양을 정한다)."""
    toppings: list[str | None] = [None] * n
    for row in logs:
        i = int(row["slice_idx"])
        if 0 <= i < n and row["status"] == EATEN:
            toppings[i] = row.get("pizza_type") or None
    return toppings


def gave_up(logs: list[dict]) -> bool:
    return any(row["status"] == GAVE_UP for row in logs)


def day_result(statuses: list[str | None], slice_dts: list[datetime], now: datetime,
               given_up: bool = False) -> str:
    if statuses and all(s == EATEN for s in statuses):
        return COMPLETE
    if given_up:
        return OVER
    if statuses and all(s is not None for s in statuses):
        return OVER  # 모두 처리했지만 쉰 조각이 있다
    if slice_dts and now > slice_dts[-1] + timedelta(minutes=GRACE_MINUTES):
        return OVER
    return ONGOING


def next_pending(statuses: list[str | None]) -> int | None:
    for i, s in enumerate(statuses):
        if s is None:
            return i
    return None


def eaten_count(statuses: list[str | None]) -> int:
    return sum(1 for s in statuses if s == EATEN)


def topping_summary(logs: list[dict]) -> Counter:
    """오늘 완성된 피자의 토핑 구성: 피자 종류별로 먹은 조각 수."""
    seen: dict[int, str] = {}
    for row in logs:
        if row["status"] == EATEN:
            seen[int(row["slice_idx"])] = row.get("pizza_type") or ""
    return Counter(v for v in seen.values() if v)


def daily_eaten(logs: list[dict]) -> dict[date, int]:
    """날짜별 먹은 조각 수 (같은 조각을 여러 번 기록해도 한 번만 센다)."""
    per_day: dict[date, set[int]] = {}
    for row in logs:
        if row["status"] == EATEN:
            per_day.setdefault(date.fromisoformat(row["date"]), set()).add(int(row["slice_idx"]))
    return {d: len(s) for d, s in per_day.items()}


def streak(completed_days: set[date], today: date) -> int:
    """오늘(아직 못 채웠으면 어제)부터 거꾸로 이어진 '한 판 완성' 연속 일수."""
    day = today if today in completed_days else today - timedelta(days=1)
    count = 0
    while day in completed_days:
        count += 1
        day -= timedelta(days=1)
    return count
