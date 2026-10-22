"""영어 → 한국어 자동 번역 (MyMemory, 무료). 문장 단위로 번역하고 문장마다 캐시한다.

한도: 키 없이 하루 5,000자, de(이메일)를 붙이면 하루 50,000자. q는 최대 500바이트.
실패하면 원문을 그대로 돌려주고, 한도를 넘었으면 그 세션에서는 더 호출하지 않는다.
"""
import html
import logging
import re

import requests
import streamlit as st

from core.config import get_secret

URL = "https://api.mymemory.translated.net/get"
MAX_BYTES = 500
TIMEOUT = 5
CACHE_TTL = 60 * 60 * 24 * 7  # 7일
QUOTA_FLAG = "mt_quota_finished"

logger = logging.getLogger("shoulderpizza.translate")


class TranslateError(Exception):
    def __init__(self, message: str, quota: bool = False):
        super().__init__(message)
        self.quota = quota


def _nbytes(s: str) -> int:
    return len(s.encode("utf-8"))


def _pack(tokens: list[str]) -> list[str]:
    """토큰을 공백으로 이어 붙이되 한 덩어리가 MAX_BYTES를 넘지 않게 묶는다."""
    chunks, buf = [], ""
    for tok in tokens:
        cand = f"{buf} {tok}" if buf else tok
        if _nbytes(cand) <= MAX_BYTES:
            buf = cand
        else:
            if buf:
                chunks.append(buf)
            buf = tok
    if buf:
        chunks.append(buf)
    return chunks


def _fit(sentence: str) -> list[str]:
    if _nbytes(sentence) <= MAX_BYTES:
        return [sentence]
    tokens = []
    for piece in re.split(r"(?<=[,;:])\s+", sentence):  # 쉼표 단위 → 그래도 길면 단어 단위
        if _nbytes(piece) <= MAX_BYTES:
            tokens.append(piece)
            continue
        for word in piece.split():
            while _nbytes(word) > MAX_BYTES:  # 공백 없는 아주 긴 덩어리는 글자 수로 자른다
                cut = MAX_BYTES
                while _nbytes(word[:cut]) > MAX_BYTES:
                    cut -= 1
                tokens.append(word[:cut])
                word = word[cut:]
            if word:
                tokens.append(word)
    return _pack(tokens)


def split_sentences(text: str | None) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    out = []
    for s in re.split(r"(?<=[.!?])\s+", text):
        s = s.strip()
        if s:
            out.extend(_fit(s))
    return out


def request_translation(sentence: str, email: str | None = None) -> str:
    """한 문장을 번역한다. 실패하면 TranslateError (한도 초과면 quota=True)."""
    params = {"q": sentence, "langpair": "en|ko"}
    if email:
        params["de"] = email
    try:
        r = requests.get(URL, params=params, timeout=TIMEOUT)
        data = r.json()
    except (requests.RequestException, ValueError) as e:
        raise TranslateError(type(e).__name__) from None
    status = str(data.get("responseStatus"))
    text = ((data.get("responseData") or {}).get("translatedText") or "").strip()
    # 한도를 넘으면 경고 문장을 translatedText에 담아 보내는 경우가 있어 함께 막는다
    if data.get("quotaFinished") is True or status == "429" or text.upper().startswith("MYMEMORY WARNING"):
        raise TranslateError("quota", quota=True)
    if r.status_code != 200 or status != "200" or not text:
        raise TranslateError(f"status {status}")
    return html.unescape(text)


@st.cache_data(ttl=CACHE_TTL, max_entries=5000, show_spinner=False)
def _cached(sentence: str) -> str:
    # 캐시에 없을 때만 실행된다. 예외는 캐시되지 않으므로 실패한 문장은 다음에 다시 시도한다.
    logger.info("MyMemory 호출 (%d bytes)", _nbytes(sentence))
    return request_translation(sentence, get_secret("MYMEMORY_EMAIL"))


def translate(text: str | None, state=None) -> tuple[str, bool]:
    """(번역문, 성공 여부). 실패한 문장은 원문으로 남긴다. 예외를 밖으로 내보내지 않는다."""
    state = st.session_state if state is None else state
    out, ok = [], True
    for sentence in split_sentences(text):
        if state.get(QUOTA_FLAG):
            out.append(sentence)
            ok = False
            continue
        try:
            out.append(_cached(sentence))
        except TranslateError as e:
            out.append(sentence)
            ok = False
            if e.quota:
                state[QUOTA_FLAG] = True
        except Exception:  # 어떤 경우에도 화면까지 올리지 않는다
            out.append(sentence)
            ok = False
    return " ".join(out), ok


def translate_lines(lines: list[str], state=None) -> tuple[list[str], bool]:
    results = [translate(line, state) for line in lines]
    return [t for t, _ in results], all(ok for _, ok in results)
