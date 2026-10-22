import re

import streamlit as st

from core.illustrations import awning, mascot
from core.style import ticket_stub
from core.ui import footer, get_store

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

st.image(awning(), width="stretch", alt="")  # 가게 차양 (장식)

left, right = st.columns([3, 2], vertical_alignment="center")
with left:
    st.title("어깨PIZZA")
    st.subheader("조각 내어 맛보는 스트레칭 한판 피자")
    st.markdown(
        "매일매일 차갑게 식어 굳어버리는 당신의 어깨 피자,\n\n"
        "식으면 섭섭하잖아요.  \n"
        "오늘은 **따끈따끈하게** 맛있는 피자를 구워봐요!"
    )
with right, st.container(horizontal_alignment="center"):
    st.image(mascot("stretch", 210), width=210, alt="두 팔을 쭉 뻗고 기지개 켜는 피자 조각")

with st.form("login", border=False):
    ticket_stub("주문 접수", "메일 주소로 들어와요")
    email = st.text_input("메일 주소", placeholder="pizza@example.com", max_chars=120)
    st.caption("처음이면 피자 주문서부터 함께 써요. 비밀번호는 없어요.")
    submitted = st.form_submit_button("피자 가게 들어가기", type="primary", icon=":material/local_pizza:",
                                      width="stretch")

if submitted:
    email = email.strip().lower()
    if not EMAIL_RE.match(email):
        st.error("메일 주소 형식이 맞지 않아요. pizza@example.com처럼 입력해 주세요.")
    else:
        user = get_store().find_user(email=email)
        if user:
            st.session_state.user = user
            st.switch_page("app_pages/pizza.py")
        st.session_state.pending_email = email
        st.switch_page("app_pages/onboarding.py")

footer()
