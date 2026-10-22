"""조각 실행 화면의 운동 카드. API Ninjas 결과는 보이는 동작 1개만 번역한다."""
import streamlit as st

from core.exercises import DIFFICULTY_KO, MUSCLE_KO, POSTURE_KO, TAG_KO, photos_for
from core.translate import translate, translate_lines

DISCLAIMER = "의료 조언이 아닙니다. 통증이 있으면 멈추세요."
EYES_NOTE = "눈이 계속 불편하면 안과 상담을 받아 보세요."
NOTICE_SHOWN = "mt_notice_shown"
VISIBLE_STEPS = 3


def _numbered(lines: list[str], start: int = 1) -> str:
    return "\n".join(f"{i}. {line}" for i, line in enumerate(lines, start))


def _badges(item: dict) -> str:
    if item["source"] == "local":
        parts = [f":orange-badge[{TAG_KO.get(t, t)}]" for t in item["tags"]]
        parts += [f":blue-badge[{POSTURE_KO[p]}]" for p in item["postures"] if p in POSTURE_KO]
    else:
        parts = [f":orange-badge[{MUSCLE_KO.get(item['muscle'], item['muscle'])}]"]
        if item["difficulty"] in DIFFICULTY_KO:
            parts.append(f":green-badge[{DIFFICULTY_KO[item['difficulty']]}]")
        parts += [f":blue-badge[{POSTURE_KO[p]}(추정)]" for p in item["postures"] if p in POSTURE_KO]
    return " ".join(parts)


def _steps(lines: list[str], key: str) -> None:
    st.markdown(_numbered(lines[:VISIBLE_STEPS]))
    if len(lines) > VISIBLE_STEPS:
        with st.expander("더 보기", key=f"{key}_more"):
            st.markdown(_numbered(lines[VISIBLE_STEPS:], VISIBLE_STEPS + 1))


def render_card(item: dict, *, header: str, key: str) -> None:
    is_api = item["source"] == "ninjas"
    if is_api:
        # 번역을 먼저 계산해 실패하면 카드 위에 안내를 1회 띄운다
        name, ok_name = translate(item["name_en"])
        steps, ok_steps = translate_lines(item["steps_en"])
        translated = ok_name and ok_steps
        if not translated and not st.session_state.get(NOTICE_SHOWN):
            st.info("번역 한도를 넘어 원문으로 보여 드려요", icon=":material/translate:")
            st.session_state[NOTICE_SHOWN] = True
        images = photos_for(item["name_en"])
    else:
        name, steps, translated, images = item["name"], item["steps"], True, item["images"]

    with st.container(border=True):
        st.caption(header)
        st.subheader(name)
        if is_api:
            st.caption(item["name_en"])
        st.markdown(_badges(item))
        if images:
            st.image(images, caption=["시작 자세", "늘리는 자세"][: len(images)], width=200,
                     alt=[f"{item['name_en']} 시작 자세", f"{item['name_en']} 늘리는 자세"][: len(images)])
        _steps(steps, key)

        if is_api:
            row = st.container(horizontal=True, vertical_alignment="center")
            row.caption(":material/translate: 자동 번역" if translated else ":material/translate: 원문")
            show_original = row.toggle("원문 보기", key=f"{key}_orig")
            if show_original:
                st.markdown(_numbered(item["steps_en"]))
            if item["safety_en"]:
                safety = st.expander("주의사항 (꼭 읽어 주세요)", icon=":material/warning:",
                                     key=f"{key}_safety", on_change="rerun")
                with safety:
                    if safety.open:  # 펼쳤을 때만 번역한다
                        text, _ = translate(item["safety_en"])
                        st.markdown(text)
                        if show_original:
                            st.caption(item["safety_en"])

        st.caption(f":material/health_and_safety: {DISCLAIMER}")
        if "eyes" in item["tags"]:
            st.caption(EYES_NOTE)
    st.caption(source_line(item, bool(images)))


def source_line(item: dict, has_photo: bool) -> str:
    if item["source"] == "ninjas":
        line = "출처: API Ninjas · 번역 MyMemory"
        return line + " · 사진 free-exercise-db" if has_photo else line
    if item["id"].startswith("Eye_"):
        return "출처: 어깨PIZZA"
    return "출처: free-exercise-db (Unlicense)"
