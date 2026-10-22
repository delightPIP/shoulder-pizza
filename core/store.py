"""기록 저장소 (SPEC 9장). Google Sheets가 연결되면 Sheets를, 아니면 로컬 JSON 파일을 쓴다.

앱과 메일러가 같이 쓰므로 Streamlit에 의존하지 않는다. 값은 모두 문자열로 저장한다
(Sheets가 "09:00"을 시각으로 바꾸지 않도록 RAW로 쓴다).
"""
import json
import threading
from datetime import date
from pathlib import Path

USERS = "users"
LOGS = "logs"
SENDS = "sends"
COLUMNS = {
    USERS: ["uid", "email", "nickname", "city", "window_start", "window_end", "slices",
            "pizza_type", "consent_privacy", "consent_app_notice", "active", "created_at"],
    LOGS: ["uid", "date", "slice_idx", "pizza_type", "exercise_id", "status", "weather", "ts"],
    SENDS: ["uid", "date", "slice_idx", "kind", "sent_at"],
}


def _row(table: str, data: dict) -> dict:
    return {c: "" if data.get(c) is None else str(data.get(c)) for c in COLUMNS[table]}


def is_true(value) -> bool:
    return str(value).strip().lower() == "true"


class _Base:
    backend = ""

    def _all(self, table: str) -> list[dict]:
        raise NotImplementedError

    def _append(self, table: str, row: dict) -> None:
        raise NotImplementedError

    def _replace(self, table: str, index: int, row: dict) -> None:
        raise NotImplementedError

    def find_user(self, *, email: str | None = None, uid: str | None = None) -> dict | None:
        for user in self._all(USERS):
            if (email and user["email"].lower() == email.lower()) or (uid and user["uid"] == uid):
                return user
        return None

    def save_user(self, user: dict) -> dict:
        row = _row(USERS, user)
        for i, existing in enumerate(self._all(USERS)):
            if existing["uid"] == row["uid"]:
                self._replace(USERS, i, row)
                return row
        self._append(USERS, row)
        return row

    def active_users(self) -> list[dict]:
        return [u for u in self._all(USERS) if is_true(u["active"])]

    def add_log(self, log: dict) -> None:
        self._append(LOGS, _row(LOGS, log))

    def logs(self, uid: str, since: date | None = None, until: date | None = None) -> list[dict]:
        out = []
        for row in self._all(LOGS):
            if row["uid"] != uid:
                continue
            d = date.fromisoformat(row["date"])
            if (since and d < since) or (until and d > until):
                continue
            out.append(row)
        return out

    def add_send(self, send: dict) -> None:
        self._append(SENDS, _row(SENDS, send))

    def sent_keys(self) -> set[tuple[str, str, str, str]]:
        return {(r["uid"], r["date"], r["slice_idx"], r["kind"]) for r in self._all(SENDS)}


class FileStore(_Base):
    """로컬 개발용. 한 파일에 세 표를 담는다. Streamlit Cloud에서는 재시작하면 사라질 수 있다."""

    backend = "file"
    _lock = threading.Lock()

    def __init__(self, path: Path):
        self.path = Path(path)

    def _load(self) -> dict:
        if not self.path.exists():
            return {t: [] for t in COLUMNS}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return {t: data.get(t, []) for t in COLUMNS}

    def _save(self, data: dict) -> None:
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    def _all(self, table):
        return [_row(table, r) for r in self._load()[table]]

    def _append(self, table, row):
        with self._lock:
            data = self._load()
            data[table].append(row)
            self._save(data)

    def _replace(self, table, index, row):
        with self._lock:
            data = self._load()
            data[table][index] = row
            self._save(data)


class SheetsStore(_Base):
    """Google Sheets. 시트(users, logs, sends)가 없으면 머리글과 함께 만든다."""

    backend = "sheets"

    def __init__(self, spreadsheet):
        self.spreadsheet = spreadsheet
        self._sheets = {}

    def _ws(self, table):
        if table not in self._sheets:
            existing = {ws.title: ws for ws in self.spreadsheet.worksheets()}
            ws = existing.get(table)
            if ws is None:
                ws = self.spreadsheet.add_worksheet(title=table, rows=1000, cols=len(COLUMNS[table]))
                ws.append_row(COLUMNS[table], value_input_option="RAW")
            self._sheets[table] = ws
        return self._sheets[table]

    def _all(self, table):
        records = self._ws(table).get_all_records(numericise_ignore=["all"])
        return [_row(table, r) for r in records]

    def _append(self, table, row):
        self._ws(table).append_row([row[c] for c in COLUMNS[table]], value_input_option="RAW")

    def _replace(self, table, index, row):
        # 1행은 머리글이라 index 0이 2행이다
        self._ws(table).update(
            values=[[row[c] for c in COLUMNS[table]]], range_name=f"A{index + 2}", value_input_option="RAW"
        )


def make_store(sheet_id: str | None, service_account: dict | None, file_path: Path) -> _Base:
    if sheet_id and service_account:
        import gspread

        client = gspread.service_account_from_dict(service_account)
        return SheetsStore(client.open_by_key(sheet_id))
    return FileStore(file_path)
