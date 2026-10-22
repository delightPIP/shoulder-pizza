import pytest

from core import exercises as ex


def raw(name, difficulty="beginner", equipments=(), instructions="Sit tall. Breathe.", muscle="neck"):
    return {"name": name, "type": "stretching", "muscle": muscle, "difficulty": difficulty,
            "equipments": list(equipments), "instructions": instructions, "safety_info": "Stop if it hurts."}


# --- 정렬과 필터 (2026-10-22 실제 응답 이름 사용) ---

def test_drops_expert_tools_and_non_stretches():
    raws = [
        raw("Side Neck Stretch", "intermediate"),
        raw("Neck-SMR", "intermediate", ["muscle roller"]),
        raw("Behind Head Chest Stretch", equipments=["partner"]),
        raw("Alternating lunge jump"),
        raw("Superman"),
        raw("Scissor Kick"),
        raw("Toe Touchers"),
        raw("One Handed Hang"),
        raw("Some Expert Stretch", "expert"),
        raw("Standing leg swing", equipments=["chair"]),
        raw("Wall Calf Stretch", equipments=["Wall"]),
    ]
    names = [r["name"] for r in ex.filter_and_sort(raws)]
    assert names == ["Standing leg swing", "Wall Calf Stretch", "Side Neck Stretch"]


def test_beginner_first_and_duplicates_removed():
    raws = [raw("B Stretch", "intermediate"), raw("A Stretch"), raw("b stretch", "intermediate")]
    assert [r["name"] for r in ex.filter_and_sort(raws)] == ["A Stretch", "B Stretch"]


@pytest.mark.parametrize("text, expected", [
    ("Stand next to a chair or other support, holding on with one hand.", ["stand"]),
    ("Sit on a stable chair or bench with your feet flat.", ["chair"]),
    ("Sit or stand upright and bring your hands together.", ["chair", "stand"]),
    ("Lie on your back with your knees bent.", ["lying"]),
    ("Start on your hands and knees, with your hands beneath your shoulders.", ["floor"]),
    ("Raise your arms overhead.", []),
])
def test_infer_postures_from_first_sentence(text, expected):
    assert ex.infer_postures(text + " Then stand up slowly.") == expected


def test_normalize_splits_steps():
    item = ex.normalize_ninjas(raw("Chin To Chest Stretch", instructions="Sit upright. Lower your chin."))
    assert item["steps_en"] == ["Sit upright.", "Lower your chin."]
    assert item["postures"] == ["chair"]
    assert item["safety_en"] == "Stop if it hurts."


# --- 로컬 데이터 ---

def test_local_eyes_only_eye_moves():
    items = ex.local_candidates("eyes")
    assert items and all("eyes" in i["tags"] for i in items)


def test_local_posture_filter_lying_includes_floor():
    items = ex.local_candidates("back", "lying")
    assert items and all(set(i["postures"]) & {"lying", "floor"} for i in items)


def test_local_good_has_body_moves_without_eyes():
    items = ex.local_candidates("good")
    assert len(items) == 24 and not any("eyes" in i["tags"] for i in items)


def test_local_rest_is_empty():
    assert ex.local_candidates("closed") == []


# --- 후보 만들기 ---

@pytest.fixture
def ninjas(monkeypatch):
    calls = []
    data = {"neck": [raw("Chin To Chest Stretch", "intermediate", instructions="Sit upright. Lower chin.")],
            "middle_back": [raw("Upper Back Stretch", instructions="Stand tall. Reach forward.")],
            "chest": [raw("Elbows Back", instructions="Stand upright. Pull elbows back.")]}

    def fake(muscle):
        calls.append(muscle)
        if muscle not in data:
            raise RuntimeError("down")
        return data[muscle]

    monkeypatch.setattr(ex, "_cached_ninjas", fake)
    return calls, data


def test_shoulder_calls_mapped_muscles(ninjas):
    calls, _ = ninjas
    items, source, note = ex.build_candidates("shoulder")
    assert calls == ["neck", "middle_back", "chest"]
    assert source == "ninjas" and note == ""
    assert [i["name_en"] for i in items] == ["Upper Back Stretch", "Elbows Back", "Chin To Chest Stretch"]


def test_posture_filter_applies_to_api_items(ninjas):
    items, source, _ = ex.build_candidates("shoulder", "chair")
    assert [i["name_en"] for i in items] == ["Chin To Chest Stretch"]


def test_falls_back_to_local_when_api_fails(ninjas):
    calls, data = ninjas
    data.clear()
    items, source, note = ex.build_candidates("back")
    assert calls == ["lower_back", "middle_back"]
    assert source == "local" and note == "기본 동작으로 보여 드려요"
    assert items and all("back" in i["tags"] for i in items)


def test_falls_back_to_local_when_everything_is_filtered(ninjas):
    _, data = ninjas
    data["neck"] = [raw("Neck-SMR", equipments=["muscle roller"])]
    items, source, note = ex.build_candidates("head")
    assert source == "local" and note


def test_eyes_and_rest_never_call_api(ninjas):
    calls, _ = ninjas
    assert ex.build_candidates("eyes")[1] == "local"
    assert ex.build_candidates("closed") == ([], "none", "")
    assert calls == []


def test_good_picks_two_muscles(ninjas):
    calls, _ = ninjas
    ex.build_candidates("good", seed=1)
    assert len(calls) == 2 and len(set(calls)) == 2
