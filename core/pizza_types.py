"""피자 종류(컨디션) 정의와 API Ninjas `muscle`·로컬 데이터 태그 매핑 (SPEC 5장, 8.1.1)."""

# name: 피자 종류 이름. 미정이라 None이고, 정해지면 채운다. 화면에는 항상 condition을 같이 보여 준다.
# muscles: API Ninjas `muscle` 후보. 비어 있으면 API를 호출하지 않는다.
# tags: data/*.json의 tags. None이면 전체.
# topping: 피자 그림에 올라갈 토핑 모양.
PIZZA_TYPES = {
    "shoulder": {
        "name": None,
        "condition": "어깨가 뻐근해요",
        "muscles": ["neck", "middle_back", "chest"],
        "tags": ["shoulder", "neck"],
        "topping": "pepperoni",
    },
    "head": {
        "name": None,
        "condition": "머리가 굳은 것 같아요",
        "muscles": ["neck"],
        "tags": ["neck", "energy"],
        "topping": "olive",
    },
    "eyes": {
        "name": None,
        "condition": "눈이 침침해요",
        "muscles": [],  # API Ninjas에 해당 부위가 없다. eyes_ko.json만 쓴다
        "tags": ["eyes"],
        "topping": "corn",
    },
    "good": {
        "name": None,
        "condition": "컨디션이 좋아요",
        "muscles": ["neck", "middle_back", "chest", "lower_back", "lats", "hamstrings"],
        "tags": None,
        "topping": "supreme",
    },
    "back": {
        "name": None,
        "condition": "허리가 뻐근해요",
        "muscles": ["lower_back", "middle_back"],
        "tags": ["back"],
        "topping": "mushroom",
    },
    "closed": {
        "name": None,
        "condition": "아파요 (통증·저림)",
        "muscles": [],  # 휴무: 어떤 API도 호출하지 않는다
        "tags": [],
        "topping": None,
    },
}

ORDER = ["shoulder", "head", "eyes", "good", "back", "closed"]
REST = "closed"


def label(key: str) -> str:
    t = PIZZA_TYPES[key]
    return f"{t['name']} — {t['condition']}" if t["name"] else t["condition"]


def ninjas_params(key: str, attempt: int = 0) -> dict | None:
    """attempt번째 호출에 쓸 API Ninjas 파라미터. 후보가 여럿이면 번갈아 쓴다."""
    muscles = PIZZA_TYPES[key]["muscles"]
    if not muscles:
        return None
    return {"type": "stretching", "muscle": muscles[attempt % len(muscles)]}
