import pytest
import requests

from core import translate as tr


class FakeResponse:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code

    def json(self):
        if isinstance(self._data, Exception):
            raise self._data
        return self._data


def ok_response(text):
    return FakeResponse({"responseData": {"translatedText": text, "match": 0.85},
                         "quotaFinished": False, "responseStatus": 200})


@pytest.fixture(autouse=True)
def clear_cache():
    tr._cached.clear()
    yield
    tr._cached.clear()


@pytest.fixture
def calls(monkeypatch):
    """requests.get을 가로채 호출 기록을 남긴다. responses에 넣은 순서대로 돌려준다."""
    log = {"n": 0, "params": [], "responses": []}

    def fake_get(url, params=None, timeout=None):
        log["n"] += 1
        log["params"].append(params)
        assert timeout == tr.TIMEOUT
        resp = log["responses"].pop(0) if log["responses"] else ok_response("번역")
        if isinstance(resp, Exception):
            raise resp
        return resp

    monkeypatch.setattr(tr.requests, "get", fake_get)
    monkeypatch.setattr(tr, "get_secret", lambda name, default=None: None)
    return log


# --- 문장 분할 ---

def test_split_empty():
    assert tr.split_sentences("") == []
    assert tr.split_sentences(None) == []
    assert tr.split_sentences("   ") == []


def test_split_sentences():
    text = "Sit tall. Slowly tilt your head! Hold for 20 seconds? Repeat."
    assert tr.split_sentences(text) == ["Sit tall.", "Slowly tilt your head!", "Hold for 20 seconds?", "Repeat."]


def test_long_sentence_is_split_under_500_bytes_without_losing_words():
    sentence = ", ".join(f"keep your shoulders relaxed number {i}" for i in range(30)) + "."
    assert len(sentence.encode()) > 500
    parts = tr.split_sentences(sentence)
    assert len(parts) > 1
    assert all(len(p.encode()) <= 500 for p in parts)
    assert " ".join(parts).split() == sentence.split()


def test_long_sentence_without_commas_splits_by_words():
    sentence = " ".join(["stretch"] * 120) + "."
    parts = tr.split_sentences(sentence)
    assert all(len(p.encode()) <= 500 for p in parts)
    assert " ".join(parts) == sentence


def test_one_giant_word_is_cut():
    parts = tr.split_sentences("a" * 1200)
    assert [len(p) for p in parts] == [500, 500, 200]


# --- 응답 처리 ---

STATE = dict


def test_success(calls):
    calls["responses"] = [ok_response("고개를 어깨 쪽으로 부드럽게 기울이세요.")]
    assert tr.translate("Gently tilt your head towards your shoulder.", STATE()) == (
        "고개를 어깨 쪽으로 부드럽게 기울이세요.", True)
    assert calls["params"][0] == {"q": "Gently tilt your head towards your shoulder.", "langpair": "en|ko"}


def test_html_entities_are_unescaped(calls):
    calls["responses"] = [ok_response("어깨를 &#39;툭&#39; 내려요")]
    assert tr.translate("Drop it.", STATE())[0] == "어깨를 '툭' 내려요"


def test_email_is_added_only_when_set(calls, monkeypatch):
    monkeypatch.setattr(tr, "get_secret", lambda name, default=None: "ops@example.com")
    tr.translate("Hello.", STATE())
    assert calls["params"][0]["de"] == "ops@example.com"


def test_quota_finished_returns_original_and_stops_calling(calls):
    state = STATE()
    calls["responses"] = [FakeResponse({"responseData": {"translatedText": "MYMEMORY WARNING: YOU USED ALL"},
                                        "quotaFinished": True, "responseStatus": 429})]
    assert tr.translate("Sit tall.", state) == ("Sit tall.", False)
    assert state[tr.QUOTA_FLAG] is True
    assert tr.translate("Breathe slowly.", state) == ("Breathe slowly.", False)
    assert calls["n"] == 1  # 한도를 넘은 뒤에는 호출하지 않는다


@pytest.mark.parametrize("status", [429, 403])
def test_error_status_returns_original(calls, status):
    calls["responses"] = [FakeResponse({"responseData": {"translatedText": "x"}, "responseStatus": status},
                                       status_code=200)]
    assert tr.translate("Sit tall.", STATE()) == ("Sit tall.", False)


def test_warning_text_with_status_200_is_treated_as_quota(calls):
    state = STATE()
    calls["responses"] = [FakeResponse({"responseData": {"translatedText": "MYMEMORY WARNING: ..."},
                                        "quotaFinished": False, "responseStatus": 200})]
    assert tr.translate("Sit tall.", state) == ("Sit tall.", False)
    assert state[tr.QUOTA_FLAG] is True


@pytest.mark.parametrize("error", [requests.Timeout("slow"), requests.ConnectionError("down")])
def test_timeout_and_network_errors_return_original(calls, error):
    calls["responses"] = [error]
    assert tr.translate("Sit tall.", STATE()) == ("Sit tall.", False)


def test_broken_json_returns_original(calls):
    calls["responses"] = [FakeResponse(ValueError("not json"), status_code=502)]
    assert tr.translate("Sit tall.", STATE()) == ("Sit tall.", False)


def test_partial_failure_keeps_successful_sentences(calls):
    calls["responses"] = [ok_response("똑바로 앉아요."), requests.Timeout("slow")]
    assert tr.translate("Sit tall. Breathe.", STATE()) == ("똑바로 앉아요. Breathe.", False)


# --- 캐시 ---

def test_same_sentence_is_called_once(calls):
    state = STATE()
    tr.translate("Sit tall.", state)
    tr.translate("Sit tall.", state)
    tr.translate_lines(["Sit tall.", "Sit tall."], state)
    assert calls["n"] == 1


def test_failures_are_not_cached(calls):
    calls["responses"] = [requests.Timeout("slow"), ok_response("똑바로 앉아요.")]
    assert tr.translate("Sit tall.", STATE())[1] is False
    assert tr.translate("Sit tall.", STATE()) == ("똑바로 앉아요.", True)
    assert calls["n"] == 2


def test_translate_lines(calls):
    calls["responses"] = [ok_response("하나."), ok_response("둘.")]
    assert tr.translate_lines(["One.", "Two."], STATE()) == (["하나.", "둘."], True)
