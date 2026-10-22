from datetime import date

import pytest

from core.store import COLUMNS, FileStore, SheetsStore


class FakeWorksheet:
    def __init__(self, title):
        self.title = title
        self.rows = []

    def append_row(self, values, value_input_option=None):
        assert value_input_option == "RAW"
        self.rows.append(list(values))

    def get_all_records(self, numericise_ignore=None):
        header, *body = self.rows
        return [dict(zip(header, r)) for r in body]

    def update(self, values, range_name, value_input_option=None):
        row = int(range_name[1:]) - 1
        self.rows[row] = list(values[0])


class FakeSpreadsheet:
    def __init__(self):
        self.sheets = []

    def worksheets(self):
        return self.sheets

    def add_worksheet(self, title, rows, cols):
        ws = FakeWorksheet(title)
        self.sheets.append(ws)
        return ws


@pytest.fixture(params=["file", "sheets"])
def store(request, tmp_path):
    if request.param == "file":
        return FileStore(tmp_path / "store.json")
    return SheetsStore(FakeSpreadsheet())


USER = {"uid": "u1", "email": "Pizza@Example.com", "window_start": "09:00", "window_end": "18:00",
        "slices": 3, "pizza_type": "shoulder", "active": "true"}


def test_user_upsert_and_lookup(store):
    store.save_user(USER)
    assert store.find_user(email="pizza@example.com")["uid"] == "u1"  # 대소문자 무시
    assert store.find_user(uid="u1")["window_start"] == "09:00"  # 문자열 그대로
    store.save_user({**USER, "slices": 5})
    assert store.find_user(uid="u1")["slices"] == "5"
    assert len(store.active_users()) == 1
    store.save_user({**USER, "active": "false"})
    assert store.active_users() == []
    assert store.find_user(email="nobody@example.com") is None


def test_logs_filtered_by_user_and_date(store):
    store.add_log({"uid": "u1", "date": "2026-10-21", "slice_idx": 0, "status": "eaten"})
    store.add_log({"uid": "u1", "date": "2026-10-22", "slice_idx": 1, "status": "eaten"})
    store.add_log({"uid": "u2", "date": "2026-10-22", "slice_idx": 0, "status": "eaten"})
    today = store.logs("u1", since=date(2026, 10, 22), until=date(2026, 10, 22))
    assert [r["slice_idx"] for r in today] == ["1"]
    assert len(store.logs("u1")) == 2
    assert set(today[0]) == set(COLUMNS["logs"])


def test_sends(store):
    store.add_send({"uid": "u1", "date": "2026-10-22", "slice_idx": 0, "kind": "slice", "sent_at": "x"})
    assert ("u1", "2026-10-22", "0", "slice") in store.sent_keys()


def test_sheets_creates_header_once():
    ss = FakeSpreadsheet()
    s = SheetsStore(ss)
    s.save_user(USER)
    s.save_user(USER)
    users = next(ws for ws in ss.sheets if ws.title == "users")
    assert users.rows[0] == COLUMNS["users"]
    assert len(users.rows) == 2
