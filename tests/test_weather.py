import pytest
import requests

from core import weather as w
from core.effects import effect_html


@pytest.mark.parametrize("code, expected", [
    (0, w.CLEAR), (1, w.CLOUDY), (3, w.CLOUDY), (45, w.FOG), (48, w.FOG),
    (51, w.RAIN), (61, w.RAIN), (67, w.RAIN), (80, w.RAIN), (82, w.RAIN),
    (71, w.SNOW), (77, w.SNOW), (85, w.SNOW), (86, w.SNOW),
    (95, w.STORM), (99, w.STORM), (None, w.CLOUDY),
])
def test_classify_weather_codes(code, expected):
    assert w.classify_code(code) == expected


def test_dust_thresholds():
    assert not w.is_dusty(80, 35)
    assert w.is_dusty(81, None)
    assert w.is_dusty(None, 36)
    assert not w.is_dusty(None, None)


def test_priority_storm_snow_rain_over_dust_over_fog_and_clear():
    assert w.classify(95, pm25=100) == w.STORM
    assert w.classify(71, pm25=100) == w.SNOW
    assert w.classify(61, pm25=100) == w.RAIN
    assert w.classify(45, pm25=100) == w.DUSTY
    assert w.classify(0, pm10=200) == w.DUSTY
    assert w.classify(45) == w.FOG
    assert w.classify(0, 10, 5) == w.CLEAR


@pytest.mark.parametrize("category", [w.RAIN, w.SNOW, w.STORM, w.DUSTY])
def test_bad_weather_means_indoor_moves(category):
    a = w.advice(category)
    assert a["indoor"] and a["posture"] == "chair" and a["extra"] == []
    assert "창문은 닫" in a["message"]


def test_clear_prefers_standing_and_eyes_prefer_far_gaze():
    assert w.advice(w.CLEAR, pizza_key="shoulder")["posture"] == "stand"
    eyes = w.advice(w.CLEAR, pizza_key="eyes")
    assert eyes["prefer"] == ["Eye_Far_Gaze"] and "먼 곳" in eyes["message"]


def test_cloudy_and_fog_have_no_restriction():
    for c in (w.CLOUDY, w.FOG):
        a = w.advice(c)
        assert a["message"] == "" and not a["indoor"]


def test_temperature_notes():
    assert w.temp_flag(5) == "cold" and w.temp_flag(28) == "hot" and w.temp_flag(15) is None
    assert "쌀쌀" in w.advice(w.CLOUDY, temp=-2)["temp_note"]
    assert "더워요" in w.advice(w.CLEAR, temp=31)["temp_note"]


def test_no_health_claims_in_messages():
    texts = [w.advice(c, t, k)[f] for c in w.LABELS for t in (-5, 15, 35) for k in ("eyes", "back")
             for f in ("message", "temp_note")]
    for banned in ("아파", "통증", "좋아져", "낫", "효과"):
        assert not any(banned in t for t in texts)


class Resp:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


def test_fetch_weather_without_air_quality(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        if url == w.AIR_URL:
            raise requests.Timeout("slow")
        assert params["current"] == "temperature_2m,precipitation,weather_code"
        assert params["timezone"] == "Asia/Seoul"
        return Resp({"current": {"temperature_2m": 14.3, "precipitation": 0.0, "weather_code": 0,
                                 "time": "2026-10-22T16:30"}})

    monkeypatch.setattr(w.requests, "get", fake_get)
    got = w.fetch_weather(37.5, 127.0)
    assert got["temp"] == 14.3 and got["pm25"] is None and got["category"] == w.CLEAR


def test_fetch_weather_with_dust(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        if url == w.AIR_URL:
            return Resp({"current": {"pm10": 90, "pm2_5": 20}})
        return Resp({"current": {"temperature_2m": 10, "precipitation": 0, "weather_code": 1}})

    monkeypatch.setattr(w.requests, "get", fake_get)
    assert w.fetch_weather(37.5, 127.0)["category"] == w.DUSTY


def test_current_weather_returns_none_on_failure(monkeypatch):
    w._cached_weather.clear()

    def boom(*a, **k):
        raise requests.ConnectionError("down")

    monkeypatch.setattr(w.requests, "get", boom)
    assert w.current_weather("서울") is None
    w._cached_weather.clear()


@pytest.mark.parametrize("category", list(w.LABELS))
def test_effects_never_block_clicks_and_respect_reduced_motion(category):
    html = effect_html(category)
    assert "pointer-events: none" in html
    assert "prefers-reduced-motion" in html
    assert f"sp-{category}" in html
    assert "<script" not in html


def test_no_effect_without_weather():
    assert effect_html(None) == ""


# --- 날씨별 동작 순서 (arrange) ---

def local(id_, seconds=30, source="local"):
    return {"id": id_, "source": source, "seconds": seconds, "steps_en": []}


def api(name, text="Stand tall."):
    return {"id": name.lower(), "source": "ninjas", "steps_en": [text]}


WALK = local("Outdoor_Walk", 300)


def lookup(id_):
    return WALK if id_ == "Outdoor_Walk" else None


def ids(items):
    return [i["id"] for i in items]


def test_mild_clear_day_suggests_walking_outside_when_standing():
    tip = w.advice(w.CLEAR, temp=18, pizza_key="shoulder")
    assert tip["extra"] == ["Outdoor_Walk"] and "밖에 나가" in tip["message"]
    items = [local("A"), local("B")]
    assert ids(w.arrange(items, tip, "stand", lookup)) == ["Outdoor_Walk", "A", "B"]
    assert ids(w.arrange(items, tip, "chair", lookup)) == ["A", "B"]  # 의자를 고르면 넣지 않는다


def test_no_outdoor_walk_when_cold_hot_or_eyes():
    assert w.advice(w.CLEAR, temp=2)["extra"] == []
    assert w.advice(w.CLEAR, temp=31)["extra"] == []
    assert w.advice(w.CLEAR, temp=18, pizza_key="eyes")["extra"] == []


def test_cold_day_puts_warm_up_moves_first():
    tip = w.advice(w.CLOUDY, temp=1)
    items = [local("Cat_Stretch"), local("Shoulder_Circles"), local("Upward_Stretch")]
    assert ids(w.arrange(items, tip, "chair", lookup))[:2] == ["Shoulder_Circles", "Upward_Stretch"]
    api_items = [api("Chin To Chest Stretch"), api("Dynamic chest stretch"), api("Standing leg swing")]
    assert ids(w.arrange(api_items, tip, "chair", lookup)) == [
        "dynamic chest stretch", "standing leg swing", "chin to chest stretch"]
    assert "몸을 데우는" in tip["temp_note"]


@pytest.mark.parametrize("category, temp", [(w.DUSTY, 15), (w.CLOUDY, 31)])
def test_dusty_or_hot_day_puts_short_moves_first(category, temp):
    tip = w.advice(category, temp=temp)
    assert tip["short_first"]
    items = [local("Long", 40), local("Short", 20), local("Mid", 30)]
    assert ids(w.arrange(items, tip, "chair", lookup)) == ["Short", "Mid", "Long"]
    api_items = [api("Long", "x " * 200), api("Short", "x")]
    assert ids(w.arrange(api_items, tip, "chair", lookup)) == ["short", "long"]


def test_clear_eyes_still_puts_far_gaze_first():
    tip = w.advice(w.CLEAR, temp=18, pizza_key="eyes")
    items = [local("Eye_Slow_Blink"), local("Eye_Far_Gaze")]
    assert ids(w.arrange(items, tip, "chair", lookup)) == ["Eye_Far_Gaze", "Eye_Slow_Blink"]


def test_arrange_without_weather_keeps_order():
    items = [local("A"), local("B")]
    assert w.arrange(items, None, "stand", lookup) == items


def test_outdoor_walk_is_not_a_normal_candidate():
    from core.exercises import local_by_id, local_candidates

    assert local_by_id("Outdoor_Walk")["name"] == "잠깐 밖에 나가 걷기"
    for key in ("shoulder", "good", "back", "head"):
        assert "Outdoor_Walk" not in ids(local_candidates(key))
