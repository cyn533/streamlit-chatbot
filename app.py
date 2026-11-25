import os

import streamlit as st


st.set_page_config(page_title="잡담 챗봇")
st.title("잡담 챗봇")

if not st.session_state.get("unlocked"):
    with st.form("login"):
        password = st.text_input("비밀번호", type="password")
        submitted = st.form_submit_button("입장")

    if submitted:
        expected_password = os.getenv("CHAT_PASSWORD")
        if expected_password and password == expected_password:
            st.session_state.unlocked = True
            st.rerun()
        st.error("비밀번호를 확인해줘.")

    st.stop()


def reply_to(message):
    replies = [
        (("피곤", "힘들"), "오늘 좀 지쳤구나. 무슨 일 있었어?"),
        (("과제", "시험", "공부"), "요즘 할 게 많나 보네. 뭐가 제일 신경 쓰여?"),
        (("심심",), "그럼 밸런스 게임 어때? 평생 여름 vs 평생 겨울!"),
        (("여름", "겨울"), "오, 그 계절을 고른 이유가 뭐야?"),
        (("안녕", "하이"), "안녕! 오늘 하루 어땠어?"),
    ]
    for keywords, reply in replies:
        if any(keyword in message for keyword in keywords):
            return reply
    return "그랬구나. 조금 더 얘기해줄래?"


if "messages" not in st.session_state:
    st.session_state.messages = [
        ("assistant", "안녕! 오늘 있었던 일이나 지금 기분을 얘기해줘.")
    ]

for role, message in st.session_state.messages:
    with st.chat_message(role):
        st.text(message)

if message := st.chat_input("메시지를 입력해"):
    reply = reply_to(message)
    st.session_state.messages.extend([
        ("user", message),
        ("assistant", reply),
    ])
    st.rerun()