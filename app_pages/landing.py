import re

import streamlit as st

from core.pizza_art import pizza_svg
from core.ui import footer, get_store

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

st.title("어깨PIZZA")
st.subheader("조각 내어 맛보는 스트레칭 한판 피자")

left, right = st.columns([3, 2], vertical_alignment="center")
with left:
    st.markdown(
        "매일매일 차갑게 식어 굳어버리는 당신의 어깨 피자,\n\n"
        "식으면 섭섭하잖아요.  \n"
        "오늘은 **따끈따끈하게** 맛있는 피자를 구워봐요!"
    )
with right:
    st.image(pizza_svg(4, ["eaten"] * 4, ["shoulder", "good", "back", "head"], face="happy"),
             width=240, alt="김이 나는 웃는 피자")

with st.form("login", border=True):
    email = st.text_input("메일 주소", placeholder="pizza@example.com", max_chars=120)
    st.caption("메일 주소로 로그인해요. 처음이면 피자 주문서부터 함께 써요. 비밀번호는 없어요.")
    submitted = st.form_submit_button("피자 가게 들어가기", type="primary", icon=":material/local_pizza:",
                                      width="stretch")

if submitted:
    email = email.strip().lower()
    if not EMAIL_RE.match(email):
        st.error("메일 주소를 다시 확인해 주세요.")
    else:
        user = get_store().find_user(email=email)
        if user:
            st.session_state.user = user
            st.switch_page("app_pages/pizza.py")
        st.session_state.pending_email = email
        st.switch_page("app_pages/onboarding.py")

footer()
