"""날씨 (Open-Meteo, 키 없음): 호출, 분류, 추천 규칙. SPEC 7장.

날씨는 동작 선택 기준과 분위기로만 쓴다. 건강 상태를 단정하는 문구는 쓰지 않는다.
"""
import requests
import streamlit as st

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
TIMEOUT = 5

CITIES = {
    "서울": (37.5665, 126.9780), "부산": (35.1796, 129.0756), "대구": (35.8714, 128.6014),
    "인천": (37.4563, 126.7052), "광주": (35.1595, 126.8526), "대전": (36.3504, 127.3845),
    "울산": (35.5384, 129.3114), "세종": (36.4800, 127.2890), "수원": (37.2636, 127.0286),
    "춘천": (37.8813, 127.7298), "전주": (35.8242, 127.1480), "제주": (33.4996, 126.5312),
}
DEFAULT_CITY = "서울"

CLEAR, CLOUDY, FOG, RAIN, SNOW, STORM, DUSTY = "clear", "cloudy", "fog", "rain", "snow", "storm", "dusty"
LABELS = {
    CLEAR: ("맑음", ":material/sunny:"), CLOUDY: ("흐림", ":material/cloud:"),
    FOG: ("안개", ":material/foggy:"), RAIN: ("비", ":material/rainy:"),
    SNOW: ("눈", ":material/ac_unit:"), STORM: ("뇌우", ":material/thunderstorm:"),
    DUSTY: ("미세먼지 나쁨", ":material/masks:"),
}
INDOOR = {RAIN, SNOW, STORM, DUSTY}

# 환경부 '나쁨' 기준 (확인 필요). Open-Meteo 대기질은 모델 추정치라 참고용이다.
PM25_BAD = 36
PM10_BAD = 81
COLD = 5  # ℃ 이하 (가안)
HOT = 28  # ℃ 이상 (가안)

# 추운 날 먼저 보여 줄 '몸을 데우는' 동작: 로컬 id, API Ninjas 이름에 들어가는 단어
WARM_UP_IDS = ["Shoulder_Circles", "Upward_Stretch", "Shoulder_Raise", "Wrist_Circles"]
WARM_UP_WORDS = ("dynamic", "circle", "swing", "rotation", "roll")


def classify_code(code: int | None) -> str:
    """WMO weather_code → 하늘 상태."""
    if code is None:
        return CLOUDY
    if code == 0:
        return CLEAR
    if code in (45, 48):
        return FOG
    if 51 <= code <= 67 or 80 <= code <= 82:
        return RAIN
    if 71 <= code <= 77 or code in (85, 86):
        return SNOW
    if 95 <= code <= 99:
        return STORM
    return CLOUDY


def is_dusty(pm10: float | None, pm25: float | None) -> bool:
    return (pm25 is not None and pm25 >= PM25_BAD) or (pm10 is not None and pm10 >= PM10_BAD)


def classify(code: int | None, pm10: float | None = None, pm25: float | None = None) -> str:
    """우선순위: 뇌우 > 눈 > 비 > 미세먼지 > 안개 > 맑음·흐림."""
    sky = classify_code(code)
    if sky in (STORM, SNOW, RAIN):
        return sky
    if is_dusty(pm10, pm25):
        return DUSTY
    return sky


def temp_flag(temp: float | None) -> str | None:
    if temp is None:
        return None
    if temp <= COLD:
        return "cold"
    if temp >= HOT:
        return "hot"
    return None


def advice(category: str, temp: float | None = None, pizza_key: str | None = None) -> dict:
    """화면 문구, 기본 자세, 먼저 보여 줄 동작 (SPEC 7.3, 가안)."""
    label, icon = LABELS[category]
    flag = temp_flag(temp)
    message, prefer, prefer_words, extra, short_first = "", [], (), [], False
    if category == DUSTY:
        message = "미세먼지가 나쁜 날이에요. 창문은 닫고 짧고 가볍게 움직여요."
        short_first = True
    elif category in INDOOR:
        message = "오늘은 안에서 구워요. 창문은 닫아 두세요."
    elif category == CLEAR:
        if pizza_key == "eyes":
            message = "날씨가 맑아요. 창밖 먼 곳을 바라보며 한 조각 어때요?"
            prefer = ["Eye_Far_Gaze"]
        elif flag is None:  # 맑고 춥지도 덥지도 않으면 바깥 조각을 제안한다
            message = "날씨가 맑아요. 잠깐 밖에 나가 걸어 보는 건 어때요?"
            extra = ["Outdoor_Walk"]
        else:
            message = "날씨가 맑아요. 창가에서 서서 한 조각 어때요?"
    if flag == "cold":  # 몸을 데우는 동작 먼저
        prefer = prefer + WARM_UP_IDS
        prefer_words = WARM_UP_WORDS
    elif flag == "hot":
        short_first = True
    temp_note = {"cold": "쌀쌀해요. 몸을 데우는 동작부터 천천히 해요.",
                 "hot": "더워요. 시원한 곳에서 짧게 해요."}.get(flag, "")
    return {
        "category": category, "label": label, "icon": icon,
        "message": message, "temp_note": temp_note,
        "posture": "stand" if category == CLEAR and pizza_key != "eyes" else "chair",
        "prefer": prefer, "prefer_words": prefer_words, "extra": extra, "short_first": short_first,
        "indoor": category in INDOOR,
    }


def arrange(items: list[dict], tip: dict | None, posture: str | None, lookup) -> list[dict]:
    """날씨 추천에 맞게 동작 순서를 바꾼다. lookup(id)는 로컬 동작을 찾아 준다 (바깥 조각용).

    1. 바깥 조각(extra)은 '서서'를 골랐을 때 맨 앞에 넣는다
    2. 먼저 보여 줄 동작(prefer id, API 이름의 prefer_words)을 앞으로
    3. short_first면 짧은 동작을 앞으로 (로컬은 seconds, API는 설명 길이)
    """
    if not tip:
        return items
    out = list(items)
    if tip["short_first"]:
        out.sort(key=lambda i: i.get("seconds", 30) if i["source"] == "local" else len(" ".join(i["steps_en"])) / 10)
    words = tip["prefer_words"]

    def preferred(i: dict) -> bool:
        return i["id"] in tip["prefer"] or (i["source"] == "ninjas" and any(w in i["id"] for w in words))

    out.sort(key=lambda i: 0 if preferred(i) else 1)  # 안정 정렬이라 앞 순서가 유지된다
    if posture in (None, "stand"):
        extras = [x for x in (lookup(e) for e in tip["extra"]) if x and x["id"] not in {i["id"] for i in out}]
        out = extras + out
    return out


def fetch_weather(lat: float, lon: float) -> dict:
    """현재 날씨와 대기질. 날씨가 실패하면 예외, 대기질만 실패하면 미세먼지 값을 비운다."""
    params = {"latitude": lat, "longitude": lon, "timezone": "Asia/Seoul"}
    r = requests.get(FORECAST_URL, params={**params, "current": "temperature_2m,precipitation,weather_code"},
                     timeout=TIMEOUT)
    r.raise_for_status()
    current = r.json()["current"]
    pm10 = pm25 = None
    try:
        a = requests.get(AIR_URL, params={**params, "current": "pm10,pm2_5"}, timeout=TIMEOUT)
        a.raise_for_status()
        air = a.json()["current"]
        pm10, pm25 = air.get("pm10"), air.get("pm2_5")
    except Exception:
        pass
    code = current.get("weather_code")
    return {
        "temp": current.get("temperature_2m"), "precip": current.get("precipitation"),
        "code": code, "pm10": pm10, "pm25": pm25,
        "category": classify(code, pm10, pm25), "time": current.get("time"),
    }


@st.cache_data(ttl=600, max_entries=32, show_spinner=False)
def _cached_weather(city: str) -> dict:
    lat, lon = CITIES[city]
    return fetch_weather(lat, lon)  # 실패는 캐시하지 않는다


def current_weather(city: str | None) -> dict | None:
    """실패하면 None. 화면은 날씨 없이 기본 테마로 동작한다."""
    try:
        return _cached_weather(city if city in CITIES else DEFAULT_CITY)
    except Exception:
        return None
