from datetime import date, datetime, timedelta

import pytest

from core.schedule import TZ
from core.store import FileStore
from mailer import send_due as sd

USER = {"uid": "u1", "email": "pizza@example.com", "window_start": "09:00", "window_end": "18:00",
        "slices": "3", "pizza_type": "shoulder", "active": "true"}
DAY = date(2026, 10, 22)


def at(h, m=0, day=DAY):
    return datetime(day.year, day.month, day.day, h, m, tzinfo=TZ)


def log(i, status, ts="", day=DAY):
    return {"date": day.isoformat(), "slice_idx": str(i), "status": status, "ts": ts}


def kinds(mails):
    return [(m["idx"], m["kind"]) for m in mails]


def test_nothing_before_first_slice():
    assert sd.due_mails(USER, [], set(), at(8, 59)) == []


def test_slice_is_due_at_its_time_until_grace_ends():
    assert kinds(sd.due_mails(USER, [], set(), at(9, 0))) == [(0, "slice")]
    assert kinds(sd.due_mails(USER, [], set(), at(9, 59))) == [(0, "slice")]
    assert sd.due_mails(USER, [], set(), at(10, 0)) == []  # 60분 지나면 보내지 않는다
    assert kinds(sd.due_mails(USER, [], set(), at(13, 35))) == [(1, "slice")]


def test_already_sent_is_not_sent_again():
    sent = {("u1", "2026-10-22", "0", "slice")}
    assert sd.due_mails(USER, [], sent, at(9, 5)) == []


def test_eaten_or_rested_slice_is_skipped():
    assert sd.due_mails(USER, [log(1, "eaten")], set(), at(13, 35)) == []
    assert sd.due_mails(USER, [log(1, "rest")], set(), at(13, 35)) == []
    assert kinds(sd.due_mails(USER, [log(1, "opened")], set(), at(13, 35))) == [(1, "slice")]


def test_window_crossing_midnight_uses_yesterday():
    night = {**USER, "window_start": "22:00", "window_end": "02:00"}
    mails = sd.due_mails(night, [], set(), at(0, 10, DAY + timedelta(days=1)))
    assert [(m["day"], m["idx"]) for m in mails] == [(DAY, 1)]


def test_snooze_sends_one_reminder_after_30_minutes():
    ts = at(13, 40).isoformat()
    logs = [log(1, "snoozed", ts)]
    sent = {("u1", "2026-10-22", "1", "slice")}
    assert sd.due_mails(USER, logs, sent, at(14, 5)) == []
    assert kinds(sd.due_mails(USER, logs, sent, at(14, 10))) == [(1, f"snooze@{ts}")]
    assert sd.due_mails(USER, logs, sent | {("u1", "2026-10-22", "1", f"snooze@{ts}")}, at(14, 15)) == []


def test_message_links_use_uid_not_email():
    mail = {"day": DAY, "idx": 1, "n": 3, "at": at(13, 30), "kind": "slice"}
    msg = sd.build_message(USER, mail, "https://pizza.streamlit.app/", "bot@example.com")
    body = msg.get_body(("plain",)).get_content()
    assert "https://pizza.streamlit.app/?u=u1&slice=1" in body
    assert "https://pizza.streamlit.app/?unsub=u1" in body
    assert "pizza%40example.com" not in body and "u=pizza" not in body
    assert msg["To"] == "pizza@example.com"
    assert msg["List-Unsubscribe"] == "<https://pizza.streamlit.app/?unsub=u1>"
    assert "의료 조언이 아닙니다" in body
    assert "2번째 조각" in msg["Subject"]


@pytest.fixture
def env(monkeypatch, tmp_path):
    values = {"APP_URL": "https://pizza.streamlit.app"}
    monkeypatch.setattr(sd, "get_secret", lambda name, default=None: values.get(name, default))
    monkeypatch.setattr(sd, "service_account_info", lambda: None)
    monkeypatch.setattr(sd, "local_store_path", lambda: tmp_path / "store.json")
    store = FileStore(tmp_path / "store.json")
    store.save_user(USER)
    return values, store


def test_skips_quietly_without_secrets(env, monkeypatch, capsys):
    monkeypatch.setattr(sd.smtplib, "SMTP_SSL", lambda *a, **k: pytest.fail("메일을 보내면 안 된다"))
    assert sd.main([]) == 0
    assert "건너뜁니다" in capsys.readouterr().out


class FakeSMTP:
    sent = []

    def __init__(self, host, port, timeout=None):
        assert (host, port) == ("smtp.gmail.com", 465)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def login(self, user, password):
        assert (user, password) == ("bot@example.com", "app-password")

    def send_message(self, msg):
        FakeSMTP.sent.append(msg)


def test_sends_once_and_records(env, monkeypatch, capsys):
    values, store = env
    values.update({"GMAIL_ADDRESS": "bot@example.com", "GMAIL_APP_PASSWORD": "app-password"})
    FakeSMTP.sent = []
    monkeypatch.setattr(sd.smtplib, "SMTP_SSL", FakeSMTP)
    monkeypatch.setattr(sd, "datetime", type("FixedDT", (datetime,), {"now": classmethod(lambda cls, tz=None: at(9, 3))}))

    assert sd.main(["--local"]) == 0
    assert len(FakeSMTP.sent) == 1
    assert ("u1", "2026-10-22", "0", "slice") in store.sent_keys()
    assert sd.main(["--local"]) == 0  # 다시 돌려도 같은 조각은 보내지 않는다
    assert len(FakeSMTP.sent) == 1
    out = capsys.readouterr().out
    assert "pizza@example.com" not in out  # 공개 로그에 메일 주소를 남기지 않는다


def test_dry_run_does_not_send(env, monkeypatch, capsys):
    monkeypatch.setattr(sd.smtplib, "SMTP_SSL", lambda *a, **k: pytest.fail("메일을 보내면 안 된다"))
    monkeypatch.setattr(sd, "datetime", type("FixedDT", (datetime,), {"now": classmethod(lambda cls, tz=None: at(9, 3))}))
    assert sd.main(["--local", "--dry-run"]) == 0
    assert "보낼 메일 1통" in capsys.readouterr().out


def test_inactive_user_gets_nothing(env, monkeypatch, capsys):
    _, store = env
    store.save_user({**USER, "active": "false"})
    monkeypatch.setattr(sd, "datetime", type("FixedDT", (datetime,), {"now": classmethod(lambda cls, tz=None: at(9, 3))}))
    assert sd.main(["--local", "--dry-run"]) == 0
    assert "보낼 메일 0통" in capsys.readouterr().out
