"""피자 종류(컨디션) 정의와 API Ninjas `muscle`·로컬 데이터 태그 매핑 (SPEC 5장, 8.1.1)."""

# name: 피자 이름. 불편한 상태와 반대로 '몸을 펴는 행동'으로 짓는다 (효과를 약속하는 말은 쓰지 않는다).
# condition: 고르는 곳(주문서, 한 조각 먹기)에 보이는 컨디션 문구.
# muscles: API Ninjas `muscle` 후보. 비어 있으면 API를 호출하지 않는다.
# tags: data/*.json의 tags. None이면 전체.
# topping: 피자 그림에 올라갈 토핑 모양.
PIZZA_TYPES = {
    "shoulder": {
        "name": "어깨 쫙 펴는 피자",
        "condition": "어깨가 뻐근해요",
        "muscles": ["neck", "middle_back", "chest"],
        "tags": ["shoulder", "neck"],
        "topping": "pepperoni",
    },
    "head": {
        "name": "머리 환기하는 피자",
        "condition": "머리가 굳은 것 같아요",
        "muscles": ["neck"],
        "tags": ["neck", "energy"],
        "topping": "olive",
    },
    "eyes": {
        "name": "눈 쉬어 가는 피자",
        "condition": "눈이 침침해요",
        "muscles": [],  # API Ninjas에 해당 부위가 없다. eyes_ko.json만 쓴다
        "tags": ["eyes"],
        "topping": "corn",
    },
    "good": {
        "name": "오늘도 쌩쌩 피자",
        "condition": "컨디션이 좋아요",
        "muscles": ["neck", "middle_back", "chest", "lower_back", "lats", "hamstrings"],
        "tags": None,
        "topping": "supreme",
    },
    "back": {
        "name": "허리 쭉 펴는 피자",
        "condition": "허리가 뻐근해요",
        "muscles": ["lower_back", "middle_back"],
        "tags": ["back"],
        "topping": "mushroom",
    },
    "closed": {
        "name": "푹 쉬어 가는 날",
        "condition": "아파요 (통증·저림)",
        "muscles": [],  # 휴무: 어떤 API도 호출하지 않는다
        "tags": [],
        "topping": None,
    },
}

ORDER = ["shoulder", "head", "eyes", "good", "back", "closed"]
REST = "closed"


def label(key: str) -> str:
    """피자 이름 (메뉴판, 축하 카드, 기록처럼 결과를 보여 주는 곳)."""
    return PIZZA_TYPES[key]["name"]


def condition(key: str) -> str:
    """컨디션 문구 (고르는 곳)."""
    return PIZZA_TYPES[key]["condition"]


def ninjas_params(key: str, attempt: int = 0) -> dict | None:
    """attempt번째 호출에 쓸 API Ninjas 파라미터. 후보가 여럿이면 번갈아 쓴다."""
    muscles = PIZZA_TYPES[key]["muscles"]
    if not muscles:
        return None
    return {"type": "stretching", "muscle": muscles[attempt % len(muscles)]}
