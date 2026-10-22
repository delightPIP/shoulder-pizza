"""비밀값과 설정 읽기. st.secrets를 먼저 보고, 없으면 환경변수(.env)를 읽는다."""
import json
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def get_secret(name: str, default=None):
    try:
        import streamlit as st

        if name in st.secrets:  # secrets.toml이 없으면 예외가 나므로 감싼다
            return st.secrets[name]
    except Exception:
        pass
    value = os.environ.get(name)
    return value if value else default


def service_account_info() -> dict | None:
    """Google 서비스 계정 정보. secrets의 표(table)나 한 줄 JSON 문자열 둘 다 받는다."""
    raw = get_secret("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not raw:
        return None
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None
    return dict(raw)


def local_store_path() -> Path:
    """Google Sheets가 연결되지 않았을 때 쓰는 로컬 파일 (테스트에서 바꿀 수 있다)."""
    return Path(os.environ.get("SHOULDERPIZZA_STORE_PATH") or ROOT / ".local_store.json")
