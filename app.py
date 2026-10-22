"""어깨PIZZA 진입점. 실행: streamlit run app.py

로그인 상태에 따라 페이지를 고르고, 메일 링크(?u=&slice=)와 수신 거부(?unsub=)를 처리한다.
"""
import streamlit as st

from core.effects import effect_html
from core.ui import get_store
from core.weather import DEFAULT_CITY, current_weather

st.set_page_config(page_title="어깨PIZZA", page_icon="🍕", layout="centered")

st.session_state.setdefault("user", None)
st.session_state.setdefault("pending_email", None)
st.session_state.setdefault("fx_on", True)

store = get_store()
params = st.query_params

if "unsub" in params:
    user = store.find_user(uid=params["unsub"])
    st.title("어깨PIZZA")
    if user:
        store.save_user({**user, "active": "false"})
        st.success("알림 메일을 그만 보낼게요. 다시 받으려면 로그인한 뒤 '설정'에서 피자를 다시 구워 주세요.",
                   icon=":material/mail:")
    else:
        st.warning("이미 처리됐거나 잘못된 링크예요.")
    st.stop()

if "u" in params:  # 알림 메일 링크로 들어온 경우
    user = store.find_user(uid=params["u"])
    if user:
        st.session_state.user = user
        if params.get("slice", "").isdigit():
            st.session_state.current_slice = int(params["slice"])
            st.session_state.goto_slice = True
            st.session_state.opened_from_mail = True
    st.query_params.clear()

user = st.session_state.user

if user is None:
    # 로그인 전에는 메뉴를 숨긴다. 페이지 이동은 st.switch_page로 한다 (주문서를 마치면 바로 피자로 가도록 피자도 등록)
    nav = st.navigation([
        st.Page("app_pages/landing.py", title="어깨PIZZA", icon=":material/local_pizza:", default=True),
        st.Page("app_pages/onboarding.py", title="피자 주문서", icon=":material/edit_note:"),
        st.Page("app_pages/pizza.py", title="오늘의 피자", icon=":material/local_pizza:"),
        st.Page("app_pages/apis.py", title="API 정보", icon=":material/api:"),
    ], position="hidden")
else:
    pizza = st.Page("app_pages/pizza.py", title="오늘의 피자", icon=":material/local_pizza:")
    slice_page = st.Page("app_pages/slice.py", title="한 조각 먹기", icon=":material/self_improvement:")
    record = st.Page("app_pages/record.py", title="기록", icon=":material/calendar_month:")
    settings = st.Page("app_pages/onboarding.py", title="설정", icon=":material/edit_note:")
    apis = st.Page("app_pages/apis.py", title="API 정보", icon=":material/api:")
    nav = st.navigation([pizza, slice_page, record, settings, apis], position="top")

    with st.sidebar:
        st.caption(f":material/mail: {user['email']}")
        st.toggle("날씨 화면 효과", key="fx_on")
        if st.button("로그아웃", icon=":material/logout:"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    if st.session_state.pop("goto_slice", False):
        st.switch_page(slice_page)

weather = current_weather(user["city"] if user else DEFAULT_CITY)
st.session_state.weather = weather
if weather and st.session_state.fx_on:
    st.html(effect_html(weather["category"]))

nav.run()
