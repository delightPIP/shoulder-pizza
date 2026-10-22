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
    assert "괜찮아, 내일 또 맛있게 구워보자. 인상 피자 😎" in texts(at)


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


def test_slice_count_can_be_changed_repeatedly_up_to_eight(tmp_path):
    """주문서 위젯의 두 번째 선택부터 무시되던 버그 회귀 테스트."""
    from datetime import time

    at = AppTest.from_file(APP, default_timeout=20).run()
    at.text_input[0].input("eight@example.com")
    at.button[0].click().run()
    at.time_input[0].set_value(time(8, 0)).run()
    at.time_input[0].set_value(time(7, 0)).run()
    at.time_input[1].set_value(time(22, 0)).run()
    for _ in range(2):
        at.button(key="ob_next").click().run()
    at.checkbox(key="ob_privacy").check().run()
    for _ in range(2):
        at.button(key="ob_next").click().run()
    options = at.get("button_group")[-1]
    assert [o.content for o in options.proto.options] == [f"{n}조각" for n in range(3, 9)]
    for pick in (5, 4, 8):
        at.get("button_group")[-1].set_value(pick)
        at.run()
        assert at.session_state["ob"]["slices"] == pick
    at.button(key="ob_bake").click().run()
    assert not at.exception
    saved = store_of(tmp_path).find_user(email="eight@example.com")
    assert (saved["slices"], saved["window_start"], saved["window_end"]) == ("8", "07:00", "22:00")


def test_give_up_shows_failure_screen_and_blocks_slices(tmp_path):
    user, day = make_user(tmp_path)
    at = AppTest.from_file(APP, default_timeout=20)
    at.session_state["user"] = user
    at.run()
    at.button(key="give_up").click().run()
    assert "남은 3조각은" in texts(at)  # 확인 창
    at.button(key="give_up_yes").click().run()
    assert not at.exception
    assert "괜찮아, 내일 또 맛있게 구워보자. 인상 피자 😎" in texts(at)
    assert "오늘은 여기까지 하기로 했어요" in texts(at)
    assert [r["status"] for r in store_of(tmp_path).logs("u1")] == ["gave_up"]
    at.switch_page("app_pages/slice.py").run()
    assert "오늘은 여기까지 하기로 했어요" in texts(at)


def test_give_up_can_be_cancelled(tmp_path):
    user, _ = make_user(tmp_path)
    at = AppTest.from_file(APP, default_timeout=20)
    at.session_state["user"] = user
    at.run()
    at.button(key="give_up").click().run()
    at.button(key="give_up_no").click().run()
    assert "인상 피자" not in texts(at)
    assert store_of(tmp_path).logs("u1") == []


def test_api_page_is_reachable_before_login_and_checks_fail_gracefully(tmp_path):
    at = AppTest.from_file(APP, default_timeout=20).run()
    at.switch_page("app_pages/apis.py").run()
    assert not at.exception
    page = texts(at)
    for name in ("Open-Meteo", "API Ninjas Exercises", "MyMemory 번역", "free-exercise-db"):
        assert name in page
    at.button(key="check_apis").click().run()  # 오프라인이라 모두 실패해도 멈추지 않는다
    assert not at.exception
    assert texts(at).count("실패") >= 4


def test_settings_is_one_page_and_can_turn_mails_back_on(tmp_path):
    user, _ = make_user(tmp_path)
    store_of(tmp_path).save_user({**user, "active": "false"})  # 메일 수신 거부했던 사용자
    at = AppTest.from_file(APP, default_timeout=20)
    at.session_state["user"] = {**user, "active": "false"}
    at.run()
    at.switch_page("app_pages/onboarding.py").run()
    assert not at.exception
    page = texts(at)
    for question in ("몇 시부터 몇 시까지 알려줄까요?", "어느 동네에 계세요?", "어떤 피자가 좋을지 선택해봐요.",
                     "몇 조각으로 잘라줄까요?"):
        assert question in page  # 단계 없이 한 화면에 모두
    assert not at.get("progress")
    at.toggle(key="ob_active").set_value(True).run()
    at.get("button_group")[-1].set_value(6)
    at.run()
    at.button(key="ob_save").click().run()
    assert not at.exception
    saved = store_of(tmp_path).find_user(uid="u1")
    assert (saved["slices"], saved["active"]) == ("6", "true")
    assert "오늘의 피자" in texts(at)


def test_future_slices_wait_for_their_time(tmp_path):
    user, _ = make_user(tmp_path)
    at = AppTest.from_file(APP, default_timeout=20)
    at.session_state["user"] = user
    at.run()
    keys = {b.key for b in at.button}
    assert "go_0" in keys  # 시각이 된 첫 조각
    assert "go_2" not in keys  # 아직 안 된 조각은 버튼 대신 알림 예정
    assert "알림 예정" in texts(at)


def test_slice_page_shows_disclaimer_once_and_hides_storage_note(tmp_path):
    user, _ = make_user(tmp_path)
    at = AppTest.from_file(APP, default_timeout=20)
    at.session_state["user"] = user
    at.run()
    at.button(key="eat_now").click().run()
    assert texts(at).count("의료 조언이 아닙니다") == 1
    assert "임시" not in texts(at)
    at.switch_page("app_pages/apis.py").run()
    assert "기록 저장소" in texts(at)
