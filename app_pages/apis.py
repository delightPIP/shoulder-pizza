import streamlit as st

from core.api_status import APIS, check_all, key_status, muscle_table
from core.translate import QUOTA_FLAG
from core.ui import footer

st.title("사용한 API 정보")
st.markdown("어깨PIZZA는 아래 **무료 API**를 불러와요. 하나가 실패해도 앱은 멈추지 않고 대체 방법으로 보여 줘요.")

if st.button("지금 연결 확인하기", key="check_apis", icon=":material/wifi_tethering:"):
    with st.spinner("API를 하나씩 불러 보는 중이에요..."):
        st.session_state.api_checks = check_all()
checks = st.session_state.get("api_checks", {})

for api in APIS:
    with st.container(border=True):
        head = st.container(horizontal=True, vertical_alignment="center")
        head.subheader(api["name"])
        result = checks.get(api["id"])
        if result:
            badge = ":green-badge[:material/check: 연결됨]" if result["ok"] else ":red-badge[:material/close: 실패]"
            head.markdown(f"{badge} {result['detail']} · {result['ms']}ms")
        st.markdown(api["role"])
        st.markdown(
            f"- **쓰는 곳**: {api['where']}\n"
            f"- **키**: {key_status(api)}\n"
            f"- **무료 조건**: {api['limits']}\n"
            f"- **캐시**: {api['cache']}\n"
            f"- **실패하면**: {api['fallback']}"
        )
        with st.expander("호출 주소와 파라미터"):
            st.code(api["endpoint"], language=None)
            st.caption(api["params"])
            if api["id"] == "api_ninjas":
                rows = "\n".join(f"| {k} | `{m}` |" for k, m in muscle_table())
                st.markdown(f"| 피자 종류 | muscle |\n| --- | --- |\n{rows}")
        st.link_button("공식 문서", api["docs"], icon=":material/open_in_new:")

if st.session_state.get(QUOTA_FLAG):
    st.warning("이번 세션에서 번역 한도를 넘어 원문으로 보여 드리고 있어요.", icon=":material/translate:")
st.caption("키와 이메일 값은 화면에 보여 주지 않아요. '연결 확인'을 누를 때만 각 API를 한 번씩 불러요.")

footer()
