"""앱 흐름 테스트 (AppTest). 네트워크는 모두 끊어 대체 경로로 동작하는지 확인한다."""
from datetime import timedelta

import pytest
import requests
from streamlit.testing.v1 import AppTest

from core import exercises, translate, ui, weather
from core.schedule import TZ, pizza_day
from core.store import FileStore

APP = "../app.py"


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    monkeypatch.setenv("SHOULDERPIZZA_STORE_PATH", str(tmp_path / "store.json"))
    monkeypatch.delenv("GOOGLE_SHEET_ID", raising=False)
    calls = []

    def no_network(*args, **kwargs):
        calls.append(args[0] if args else kwargs.get("url"))
        raise requests.ConnectionError("offline")

    monkeypatch.setattr(requests, "get", no_network)
    for cached in (weather._cached_weather, exercises._cached_ninjas, translate._cached, ui._store):
        cached.clear()
    yield calls


def store_of(tmp_path):
    return FileStore(tmp_path / "store.json")


def make_user(tmp_path, *, slices=3):
    """지금 시각이 시간대 안에 들도록 사용자를 만든다 (테스트 시각과 상관없이 진행 중인 하루)."""
    from datetime import datetime

    now = datetime.now(TZ)
    start = (now - timedelta(minutes=30)).replace(minute=(now.minute // 5) * 5)
    end = start + timedelta(hours=6)
    user = {"uid": "u1", "email": "pizza@example.com", "city": "서울",
            "window_start": start.strftime("%H:%M"), "window_end": end.strftime("%H:%M"),
            "slices": slices, "pizza_type": "shoulder", "consent_privacy": "true",
            "consent_app_notice": "false", "active": "true", "created_at": "2026-10-22T09:00:00+09:00"}
    saved = store_of(tmp_path).save_user(user)
    return saved, pizza_day(now, saved["window_start"], saved["window_end"])


def texts(at):
    return " ".join(str(e.value) for kind in ("title", "subheader", "markdown", "caption", "info", "success",
                                              "warning", "error") for e in getattr(at, kind))


def test_new_user_goes_from_landing_through_onboarding_to_empty_pizza(tmp_path):
    at = AppTest.from_file(APP, default_timeout=20).run()
    assert not at.exception
    assert "식으면 섭섭하잖아요" in texts(at)

    at.text_input[0].input("Pizza@Example.com")
    at.button[0].click().run()  # 폼 제출
    assert not at.exception
    assert "몇 시부터 몇 시까지 알려줄까요?" in texts(at)

    at.button(key="ob_next").click().run()  # 1 → 2
    assert "어느 동네에 계세요?" in texts(at)
    at.button(key="ob_next").click().run()  # 2 → 3
    assert "앱 서비스는 준비 중이에요, 메일로 알려드릴게요." in texts(at)
    assert at.button(key="ob_next").disabled  # 개인정보 동의 전에는 다음으로 못 간다
    at.checkbox(key="ob_privacy").check().run()
    at.button(key="ob_next").click().run()  # 3 → 4
    assert "어떤 피자가 좋을지 선택해봐요." in texts(at)
    at.button(key="ob_next").click().run()  # 4 → 5
    assert "몇 조각으로 잘라줄까요?" in texts(at)
    at.button(key="ob_bake").click().run()
    assert not at.exception
    assert "오늘의 피자" in texts(at)

    user = store_of(tmp_path).find_user(email="pizza@example.com")
    assert user and user["consent_privacy"] == "true" and user["active"] == "true"


def test_eating_a_slice_fills_the_pizza(tmp_path, offline):
    user, day = make_user(tmp_path)
    at = AppTest.from_file(APP, default_timeout=20)
    at.session_state["user"] = user
    at.run()
    assert not at.exception
    assert "0 / 3 조각 완성" in at.get("progress")[0].proto.text

    at.button(key="eat_now").click().run()  # 조각 실행 페이지로
    assert not at.exception
    assert "1번째 조각" in texts(at)
    assert "기본 동작으로 보여 드려요" in texts(at)  # API Ninjas가 실패해 로컬 동작으로 대체
    assert "의료 조언이 아닙니다. 통증이 있으면 멈추세요." in texts(at)
    assert any("api-ninjas" in str(c) for c in offline)  # 실제로 호출을 시도했다

    at.button(key="done").click().run()
    assert not at.exception
    assert "1 / 3 조각 완성" in at.get("progress")[0].proto.text
    logs = store_of(tmp_path).logs("u1")
    assert [(r["slice_idx"], r["status"], r["pizza_type"]) for r in logs] == [("0", "eaten", "shoulder")]


def test_rest_never_calls_exercise_api(tmp_path, offline):
    user, day = make_user(tmp_path)
    at = AppTest.from_file(APP, default_timeout=20)
    at.session_state["user"] = user
    at.session_state[f"type:{day}:0"] = "closed"
    at.run()
    at.button(key="eat_now").click().run()
    assert "오늘은 휴무" in texts(at)
    assert "통증이 계속되면 전문의와 상담하세요." in texts(at)
    assert not any("api-ninjas" in str(c) or "mymemory" in str(c) for c in offline)
    at.button(key="rest_done").click().run()
    assert store_of(tmp_path).logs("u1")[0]["status"] == "rest"


def test_full_pizza_celebrates(tmp_path):
    user, day = make_user(tmp_path)
    s = store_of(tmp_path)
    for i, kind in enumerate(["shoulder", "eyes", "back"]):
        s.add_log({"uid": "u1", "date": day.isoformat(), "slice_idx": i, "status": "eaten", "pizza_type": kind})
    at = AppTest.from_file(APP, default_timeout=20)
    at.session_state["user"] = user
    at.run()
    assert not at.exception
    assert "한 판 완성!" in texts(at)
    assert at.get("balloons")


def test_unfinished_day_ends_with_frown_pizza(tmp_path):
    user, day = make_user(tmp_path)
    s = store_of(tmp_path)
    s.add_log({"uid": "u1", "date": day.isoformat(), "slice_idx": 0, "status": "eaten", "pizza_type": "shoulder"})
    for i in (1, 2):
        s.add_log({"uid": "u1", "date": day.isoformat(), "slice_idx": i, "status": "rest", "pizza_type": "closed"})
    at = AppTest.from_file(APP, default_timeout=20)
    at.session_state["user"] = user
    at.run()
    assert not at.exception
    assert "괜찮아, 내일 또 맛있게 구워보자. 인상 피자^^" in texts(at)


def test_mail_link_opens_slice_and_logs_opened(tmp_path):
    make_user(tmp_path)
    at = AppTest.from_file(APP, default_timeout=20)
    at.query_params["u"] = "u1"
    at.query_params["slice"] = "1"
    at.run()
    assert not at.exception
    assert "2번째 조각" in texts(at)
    assert [r["status"] for r in store_of(tmp_path).logs("u1")] == ["opened"]


def test_unsubscribe_link_stops_mails(tmp_path):
    make_user(tmp_path)
    at = AppTest.from_file(APP, default_timeout=20)
    at.query_params["unsub"] = "u1"
    at.run()
    assert not at.exception
    assert store_of(tmp_path).find_user(uid="u1")["active"] == "false"


def test_record_page_renders(tmp_path):
    user, day = make_user(tmp_path)
    store_of(tmp_path).add_log({"uid": "u1", "date": day.isoformat(), "slice_idx": 0, "status": "eaten",
                                "pizza_type": "eyes"})
    at = AppTest.from_file(APP, default_timeout=20)
    at.session_state["user"] = user
    at.run()
    at.switch_page("app_pages/record.py").run()
    assert not at.exception
    assert "피자 달력" in texts(at)
