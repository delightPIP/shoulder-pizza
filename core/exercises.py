"""동작 데이터: API Ninjas Exercises(영어, 메인)와 로컬 JSON(한국어, 대체). SPEC 8장."""
import json
import random
import re
from functools import lru_cache

import requests
import streamlit as st

from core.config import ROOT, get_secret
from core.pizza_types import PIZZA_TYPES, REST, ninjas_params
from core.translate import split_sentences

NINJAS_URL = "https://api.api-ninjas.com/v1/exercises"
FREE_DB_URL = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json"
FREE_DB_IMG = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/{id}/{n}.jpg"
TIMEOUT = 5

# 2026-10-22 실호출: 빈 equipments는 [] 로 온다. 사무실에서 바로 할 수 있는 도구만 허용한다.
ALLOWED_EQUIPMENT = {"chair", "wall", "towel", "exercise mat"}
# type=stretching에도 스트레칭이 아닌 동작이 섞여 있다 (가안, 이름의 단어 앞부분으로 거른다)
NOT_STRETCH = ("jump", "kick", "squat", "superman", "lunge", "vacuum", "touchers", "hang", "smr")

MUSCLE_KO = {
    "neck": "목", "traps": "승모근·어깨", "lower_back": "허리", "middle_back": "등", "chest": "가슴",
    "lats": "광배근·등", "abdominals": "복부", "glutes": "엉덩이", "hamstrings": "허벅지 뒤",
    "quadriceps": "허벅지 앞", "calves": "종아리", "forearms": "손목·팔뚝", "biceps": "팔 앞",
    "triceps": "팔 뒤", "abductors": "골반 바깥", "adductors": "허벅지 안쪽",
}
TAG_KO = {
    "neck": "목", "shoulder": "어깨", "back": "허리·등", "legs": "다리", "energy": "기분 전환",
    "tired": "피로", "wrist": "손목", "eyes": "눈", "outdoor": "바깥",
}
DIFFICULTY_KO = {"beginner": "쉬움", "intermediate": "보통", "expert": "어려움"}
POSTURE_KO = {"chair": "의자", "stand": "서서", "floor": "바닥", "lying": "누워서"}
# 화면의 자세 필터 → 해당하는 동작 자세
POSTURE_FILTERS = {"chair": {"chair"}, "stand": {"stand"}, "lying": {"lying", "floor"}}

_POSTURE_PATTERNS = [
    ("lying", r"\b(lie|lying|lay|on your back|on your stomach|supine|prone)\b"),
    ("floor", r"\b(kneel|kneeling|all fours|hands and knees)\b"),
    ("chair", r"\b(sit|sits|seated|sitting)\b"),  # "stand next to a chair"는 의자 자세가 아니다
    ("stand", r"\b(stand|standing)\b"),
]


def norm_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


def infer_postures(instructions: str) -> list[str]:
    """설명의 첫 문장에서 자세를 추정한다 (샘플 10개 확인, 추정이라 틀릴 수 있다)."""
    first = (split_sentences(instructions) or [""])[0].lower()
    return [p for p, pattern in _POSTURE_PATTERNS if re.search(pattern, first)]


# --- 로컬 데이터 ---------------------------------------------------------------

@lru_cache(maxsize=1)
def load_local() -> tuple[dict, ...]:
    items = []
    for name in ("stretches_ko.json", "eyes_ko.json", "outdoor_ko.json"):
        for raw in json.loads((ROOT / "data" / name).read_text(encoding="utf-8")):
            items.append({
                "source": "local",
                "id": raw["id"],
                "name": raw["name_ko"],
                "name_en": raw["id"].replace("_", " "),
                "steps": raw["steps_ko"],
                "steps_en": [],
                "tags": raw["tags"],
                "postures": raw["postures"],
                "seconds": raw.get("seconds", 30),
                "images": raw.get("images", []),
                "muscle": None,
                "difficulty": None,
                "safety_en": "",
            })
    return tuple(items)


def local_candidates(pizza_key: str, posture: str | None = None) -> list[dict]:
    tags = PIZZA_TYPES[pizza_key]["tags"]
    if tags == []:
        return []  # 휴무
    # 바깥 동작(outdoor)은 날씨가 좋을 때만 따로 꺼내 쓴다 (core/weather.py arrange)
    items = [i for i in load_local() if "outdoor" not in i["tags"] and (tags is None or set(i["tags"]) & set(tags))]
    if tags is None:
        items = [i for i in items if "eyes" not in i["tags"]]  # '컨디션 좋아요'는 몸 동작 위주
    if posture:
        items = [i for i in items if set(i["postures"]) & POSTURE_FILTERS[posture]]
    return items


def local_by_id(exercise_id: str) -> dict | None:
    return next((i for i in load_local() if i["id"] == exercise_id), None)


# --- API Ninjas ----------------------------------------------------------------

def is_usable(raw: dict) -> bool:
    if raw.get("difficulty") == "expert":
        return False
    equipments = {e.lower() for e in raw.get("equipments") or []}
    if not equipments <= ALLOWED_EQUIPMENT:
        return False
    tokens = norm_name(raw.get("name", "")).split()
    return not any(tok.startswith(word) for tok in tokens for word in NOT_STRETCH)


def filter_and_sort(raws: list[dict]) -> list[dict]:
    """expert·도구 필요·스트레칭이 아닌 동작을 버리고, 중복을 빼고, beginner를 앞으로 정렬한다."""
    seen, out = set(), []
    for raw in raws:
        key = norm_name(raw.get("name", ""))
        if not key or key in seen or not is_usable(raw):
            continue
        seen.add(key)
        out.append(raw)
    return sorted(out, key=lambda r: 0 if r.get("difficulty") == "beginner" else 1)


def normalize_ninjas(raw: dict) -> dict:
    instructions = raw.get("instructions") or ""
    return {
        "source": "ninjas",
        "id": norm_name(raw["name"]),
        "name": None,  # 화면에 보일 때 번역한다
        "name_en": raw["name"],
        "steps": [],
        "steps_en": split_sentences(instructions),
        "tags": [],
        "postures": infer_postures(instructions),
        "seconds": 30,
        "images": [],
        "muscle": raw.get("muscle"),
        "difficulty": raw.get("difficulty"),
        "safety_en": raw.get("safety_info") or "",
    }


def fetch_ninjas(params: dict, api_key: str) -> list[dict]:
    r = requests.get(NINJAS_URL, params=params, headers={"X-Api-Key": api_key}, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list):
        raise ValueError("unexpected response")
    return data


@st.cache_data(ttl=60 * 60 * 24, max_entries=64, show_spinner=False)
def _cached_ninjas(muscle: str) -> list[dict]:
    api_key = get_secret("API_NINJAS_KEY")
    if not api_key:
        raise RuntimeError("API_NINJAS_KEY 없음")
    return fetch_ninjas({"type": "stretching", "muscle": muscle}, api_key)  # 실패는 캐시하지 않는다


def build_candidates(pizza_key: str, posture: str | None = None, seed: int = 0) -> tuple[list[dict], str, str]:
    """(동작 목록, 출처 "ninjas"|"local"|"none", 안내 문구). API가 실패하거나 0개면 로컬 동작을 준다."""
    if pizza_key == REST:
        return [], "none", ""  # 휴무: 어떤 API도 호출하지 않는다
    local = local_candidates(pizza_key, posture)
    if ninjas_params(pizza_key) is None:
        return local, "local", ""  # 눈 피자: API에 해당 부위가 없다
    muscles = list(PIZZA_TYPES[pizza_key]["muscles"])
    if len(muscles) > 3:  # '컨디션 좋아요'는 6개 중 무작위 2개
        muscles = random.Random(seed).sample(muscles, 2)
    raws = []
    for muscle in muscles:
        try:
            raws += _cached_ninjas(muscle)
        except Exception:
            continue
    items = [normalize_ninjas(r) for r in filter_and_sort(raws)]
    if posture:  # 자세를 추정하지 못한 동작은 남긴다
        items = [i for i in items if not i["postures"] or set(i["postures"]) & POSTURE_FILTERS[posture]]
    if items:
        return items, "ninjas", ""
    return local, "local", "기본 동작으로 보여 드려요"


# --- 사진 (free-exercise-db, 이름이 같을 때만) ----------------------------------

@st.cache_data(ttl=60 * 60 * 24 * 7, show_spinner=False)
def _photo_index() -> dict[str, str]:
    r = requests.get(FREE_DB_URL, timeout=TIMEOUT)
    r.raise_for_status()
    return {norm_name(e["name"]): e["id"] for e in r.json()}


def photos_for(name_en: str) -> list[str]:
    try:
        exercise_id = _photo_index().get(norm_name(name_en))
    except Exception:
        return []
    return [FREE_DB_IMG.format(id=exercise_id, n=n) for n in (0, 1)] if exercise_id else []
