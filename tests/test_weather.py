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
    assert a["indoor"] and a["posture"] == "chair"
    assert "안에서" in a["message"]


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
