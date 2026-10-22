"""사용하는 무료 API 정보와 연결 확인. 'API 정보' 페이지가 쓴다. 키 값은 절대 보여 주지 않는다."""
import time

import requests

from core import exercises, translate, weather
from core.config import get_secret
from core.pizza_types import ORDER, PIZZA_TYPES, label

APIS = [
    {
        "id": "open_meteo",
        "name": "Open-Meteo",
        "role": "오늘 날씨와 미세먼지로 화면 효과(햇살·비·눈·안개)와 추천 자세·안내 문구를 바꿔요.",
        "where": "모든 화면의 날씨 효과, 오늘의 피자, 한 조각 먹기",
        "endpoint": "GET https://api.open-meteo.com/v1/forecast\nGET https://air-quality-api.open-meteo.com/v1/air-quality",
        "params": "latitude, longitude (동네 좌표), current=temperature_2m,precipitation,weather_code / pm10,pm2_5, "
                  "timezone=Asia/Seoul",
        "key": None,
        "limits": "비상업용 무료. 상업적으로 쓰려면 유료 플랜이 필요해요 (출시 전 약관 확인).",
        "cache": "10분",
        "fallback": "날씨 없이 기본 화면으로 보여 줘요. 미세먼지는 모델 추정치라 참고용이에요.",
        "docs": "https://open-meteo.com/en/docs",
    },
    {
        "id": "api_ninjas",
        "name": "API Ninjas Exercises",
        "role": "피자 종류(컨디션)에 맞는 스트레칭 동작을 불러와요.",
        "where": "한 조각 먹기의 운동 카드",
        "endpoint": "GET https://api.api-ninjas.com/v1/exercises",
        "params": "type=stretching, muscle=피자 종류별 부위 (아래 표). 헤더 X-Api-Key",
        "key": "API_NINJAS_KEY",
        "limits": "무료 키 필요. 한 번에 최대 10개(실제 호출 기준), 상업적 이용 불가, 이미지는 유료.",
        "cache": "1일 (부위별)",
        "fallback": "실패하거나 결과가 없으면 미리 고른 한국어 동작 24개로 보여 줘요.",
        "docs": "https://api-ninjas.com/api/exercises",
    },
    {
        "id": "mymemory",
        "name": "MyMemory 번역",
        "role": "API Ninjas의 영어 동작 이름·설명·주의사항을 한국어로 자동 번역해요.",
        "where": "한 조각 먹기의 운동 카드 (보이는 동작 1개만, 주의사항은 펼칠 때만)",
        "endpoint": "GET https://api.mymemory.translated.net/get",
        "params": "q=문장 (500바이트 이하), langpair=en|ko, de=운영자 이메일 (선택)",
        "key": "MYMEMORY_EMAIL",
        "limits": "키 없이 하루 5,000자, 이메일을 넣으면 하루 50,000자. 서버 전체가 함께 써요.",
        "cache": "7일 (문장 단위)",
        "fallback": "번역하지 못하면 영어 원문으로 보여 줘요. 한도를 넘으면 그 세션에서는 더 부르지 않아요.",
        "docs": "https://mymemory.translated.net/doc/spec.php",
    },
    {
        "id": "free_exercise_db",
        "name": "free-exercise-db",
        "role": "동작 사진과 한국어 대체 동작 데이터의 원본이에요.",
        "where": "운동 카드의 사진 (이름이 같은 동작만), 대체 동작",
        "endpoint": "GET https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json",
        "params": "없음 (공개 JSON 파일과 사진 주소)",
        "key": None,
        "limits": "Unlicense (자유 이용)",
        "cache": "7일",
        "fallback": "사진 없이 보여 줘요.",
        "docs": "https://github.com/yuhonas/free-exercise-db",
    },
]


def key_status(api: dict) -> str:
    """키·설정 상태. 값은 보여 주지 않는다."""
    if api["key"] is None:
        return "키 필요 없음"
    if api["id"] == "mymemory":
        return "이메일 설정됨 (하루 50,000자)" if get_secret(api["key"]) else "이메일 없음 (하루 5,000자)"
    return "키 설정됨" if get_secret(api["key"]) else "키 없음 — 기본 동작으로만 보여 줘요"


def muscle_table() -> list[tuple[str, str]]:
    return [(label(k), ", ".join(PIZZA_TYPES[k]["muscles"]) or "호출 안 함") for k in ORDER]


def _timed(fn) -> dict:
    started = time.perf_counter()
    try:
        detail = fn()
        ok = True
    except Exception as e:  # 화면에는 오류 종류만 보여 준다
        detail, ok = f"실패 ({type(e).__name__})", False
    return {"ok": ok, "detail": detail, "ms": int((time.perf_counter() - started) * 1000)}


def _check_open_meteo() -> str:
    lat, lon = weather.CITIES[weather.DEFAULT_CITY]
    w = weather.fetch_weather(lat, lon)
    label_ko = weather.LABELS[w["category"]][0]
    return f"{weather.DEFAULT_CITY} {label_ko} {w['temp']:.0f}℃"


def _check_ninjas() -> str:
    api_key = get_secret("API_NINJAS_KEY")
    if not api_key:
        raise RuntimeError("no key")
    items = exercises.fetch_ninjas({"type": "stretching", "muscle": "neck"}, api_key)
    return f"neck 스트레칭 {len(items)}개"


def _check_mymemory() -> str:
    return f'"Stretch slowly." → "{translate.request_translation("Stretch slowly.", get_secret("MYMEMORY_EMAIL"))}"'


def _check_free_db() -> str:
    r = requests.head(exercises.FREE_DB_URL, timeout=exercises.TIMEOUT, allow_redirects=True)
    r.raise_for_status()
    return f"HTTP {r.status_code}"


CHECKS = {
    "open_meteo": _check_open_meteo,
    "api_ninjas": _check_ninjas,
    "mymemory": _check_mymemory,
    "free_exercise_db": _check_free_db,
}


def check_all() -> dict[str, dict]:
    """버튼을 눌렀을 때만 부른다. 번역은 짧은 문장 하나라 한도에 거의 영향이 없다."""
    return {api_id: _timed(fn) for api_id, fn in CHECKS.items()}
