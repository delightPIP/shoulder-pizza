import requests

from core import api_status


def test_every_api_has_required_fields_and_a_check():
    for api in api_status.APIS:
        for field in ("name", "role", "where", "endpoint", "params", "limits", "cache", "fallback", "docs"):
            assert api[field]
        assert api["id"] in api_status.CHECKS


def test_key_status_never_reveals_values(monkeypatch):
    secret = "super-secret-key-1234567890"
    monkeypatch.setattr(api_status, "get_secret", lambda name, default=None: secret)
    for api in api_status.APIS:
        assert secret not in api_status.key_status(api)
    ninjas = next(a for a in api_status.APIS if a["id"] == "api_ninjas")
    assert api_status.key_status(ninjas) == "키 설정됨"
    monkeypatch.setattr(api_status, "get_secret", lambda name, default=None: None)
    assert api_status.key_status(ninjas).startswith("키 없음")


def test_checks_report_failures_without_raising(monkeypatch):
    def boom(*a, **k):
        raise requests.ConnectionError("down")

    monkeypatch.setattr(requests, "get", boom)
    monkeypatch.setattr(requests, "head", boom)
    monkeypatch.setattr(api_status, "get_secret", lambda name, default=None: "k")
    results = api_status.check_all()
    assert set(results) == {"open_meteo", "api_ninjas", "mymemory", "free_exercise_db"}
    assert all(not r["ok"] and r["detail"].startswith("실패") for r in results.values())


def test_muscle_table_matches_pizza_types():
    table = dict(api_status.muscle_table())
    assert table["어깨 쫙 펴는 피자 (어깨가 뻐근해요)"] == "neck, middle_back, chest"
    assert table["눈 쉬어 가는 피자 (눈이 침침해요)"] == "호출 안 함"
