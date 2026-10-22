import json
from pathlib import Path

from core.pizza_types import ORDER, PIZZA_TYPES, condition, label, ninjas_params

DATA = Path(__file__).resolve().parent.parent / "data"


def test_all_types_listed_in_order():
    assert set(ORDER) == set(PIZZA_TYPES)


def test_names_are_actions_and_conditions_stay_for_choosing():
    assert label("shoulder") == "어깨 쫙 펴는 피자"
    assert condition("shoulder") == "어깨가 뻐근해요"
    assert all(PIZZA_TYPES[k]["name"] and PIZZA_TYPES[k]["condition"] for k in ORDER)


def test_names_make_no_health_promises():
    for k in ORDER:
        for banned in ("낫", "사라", "치료", "효과", "좋아져", "아파", "통증"):
            assert banned not in label(k), (k, banned)


def test_ninjas_params_rotate_muscles_and_always_stretching():
    assert ninjas_params("shoulder", 0) == {"type": "stretching", "muscle": "neck"}
    assert ninjas_params("shoulder", 1)["muscle"] == "middle_back"
    assert ninjas_params("shoulder", 3)["muscle"] == "neck"
    assert ninjas_params("back", 1) == {"type": "stretching", "muscle": "middle_back"}
    for key in ORDER:
        p = ninjas_params(key)
        assert p is None or (p["type"] == "stretching" and "difficulty" not in p)


def test_eyes_and_rest_never_call_api():
    assert ninjas_params("eyes") is None
    assert ninjas_params("closed") is None


def test_traps_is_not_used():
    # 2026-10-22 실호출에서 traps 스트레칭은 0건이었다
    assert all("traps" not in t["muscles"] for t in PIZZA_TYPES.values())


def test_local_data_covers_every_type_with_tags():
    items = json.loads((DATA / "stretches_ko.json").read_text(encoding="utf-8"))
    items += json.loads((DATA / "eyes_ko.json").read_text(encoding="utf-8"))
    tags = {t for item in items for t in item["tags"]}
    for key, t in PIZZA_TYPES.items():
        if t["tags"]:
            assert tags & set(t["tags"]), key
