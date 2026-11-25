import os
import random
from hmac import compare_digest

import streamlit as st


# 위쪽 규칙부터 확인해. 한 문장에 여러 표현이 있으면 먼저 맞는 규칙을 써.
# 새 답변을 추가할 때는 (주제, (키워드들), (답변들)) 형식으로 한 줄을 추가해.
CHAT_RULES = [
    ("joke", ("농담", "아재개그", "웃겨줘", "웃긴 얘기"), (
        "수학책이 고민이 많은 이유는? 문제가 너무 많아서!",
        "세상에서 가장 뜨거운 과일은? 천도복숭아!",
        "세상에서 가장 억울한 도형은? 원통!",
    )),
    ("game", ("밸런스", "밸런스게임", "게임하자", "게임 하자"), (
        "밸런스 게임! 평생 여름 vs 평생 겨울. 뭐 고를래?",
        "밸런스 게임! 평생 집에서 놀기 vs 평생 밖에서 놀기. 뭐 고를래?",
        "밸런스 게임! 여행 계획표 꽉 채우기 vs 아무 계획 없이 떠나기. 뭐 고를래?",
    )),
    ("choose", ("골라줘", "골라 줘", "선택장애", "결정 못"), (
        "후보를 ‘치킨 vs 떡볶이’처럼 적어줘. 내가 하나 골라볼게.",
    )),
    ("number", ("숫자 뽑아", "랜덤 숫자", "번호 뽑아"), (
        "1부터 100까지 뽑아봤어. 결과는 {number}!",
    )),
    ("compliment", ("칭찬해", "칭찬 해", "잘했다고"), (
        "여기까지 해낸 거, 한 번쯤 네가 직접 인정해줘도 돼. 잘했어!",
        "스스로 잘한 걸 알아봐 달라고 말한 것도 좋은 일이야. 오늘 뭘 해냈어?",
    )),
    ("encourage", ("응원해", "힘내라고", "할 수 있을까"), (
        "지금 당장 다 잘할 필요는 없어. 일단 손댈 수 있는 것부터 해보자. 내가 응원할게!",
        "떨려도 한 걸음은 갈 수 있어. 오늘 목표는 어느 정도야?",
    )),
    ("celebrate", ("축하해줘", "생일", "합격했", "성공했", "수상", "끝냈"), (
        "오, 축하해! 오늘은 그 기분 좀 오래 즐겨도 되겠다. 어떻게 기념할 거야?",
        "그건 같이 기뻐할 소식이네! 제일 먼저 누구한테 말하고 싶었어?",
    )),
    ("sad", ("우울", "슬퍼", "속상", "울었", "눈물", "외로"), (
        "지금 마음이 좀 무거운가 보네. 무슨 일이었는지 얘기해도 돼.",
        "말로 풀고 싶으면 들어줄게. 지금 제일 크게 느껴지는 감정은 뭐야?",
    )),
    ("angry", ("짜증", "화나", "화가", "열받", "빡쳐"), (
        "많이 답답했겠다. 어떤 일이 제일 신경 쓰였어?",
        "일단 털어놔도 돼. 처음 어디서부터 일이 꼬였어?",
    )),
    ("worry", ("걱정", "불안", "긴장", "떨려", "스트레스", "고민"), (
        "머리에서 계속 맴도는 게 있나 보네. 지금 제일 걱정되는 게 뭐야?",
        "얘기하면서 정리해볼까? 당장 할 수 있는 일부터 같이 생각해보자.",
    )),
    ("tired", ("피곤", "지쳤", "힘들", "기운 없"), (
        "오늘 좀 지쳤구나. 무슨 일 있었어?",
        "오늘 에너지를 많이 썼나 보네. 지금 제일 하고 싶은 게 뭐야?",
    )),
    ("sleep", ("졸려", "잠 안", "잠이 안", "잘 자", "잘자", "자러"), (
        "오늘 하루 고생했어. 눕기 전에 내일 해야 할 일 하나만 적어두면 마음이 좀 가벼울지도 몰라.",
        "이제 슬슬 쉬어갈 시간이네. 오늘 하루에서 제일 기억나는 장면은 뭐야?",
    )),
    ("study", ("과제", "시험", "공부", "발표", "팀플", "수업", "학교"), (
        "할 게 쌓이면 시작하기가 더 어렵지. 지금 제일 급한 건 뭐야?",
        "일단 오늘 할 것 하나만 꼽자. 자료 찾기, 내용 정리, 발표 연습 중 뭐가 남았어?",
    )),
    ("work", ("회사", "출근", "퇴근", "일하기", "알바", "직장", "업무"), (
        "일 얘기구나. 오늘은 좀 한가했어, 정신없이 지나갔어?",
        "오늘 일하면서 제일 기억에 남은 일이 뭐야?",
    )),
    ("career", ("취업", "면접", "자소서", "인턴", "지원서"), (
        "준비할 게 여러 가지겠네. 지원할 곳 찾기, 서류 쓰기, 면접 중 어디까지 왔어?",
        "어떤 일을 해보고 싶은데? 마음에 드는 공고가 있었어?",
    )),
    ("food", ("배고", "뭐 먹", "뭐먹", "메뉴", "점심", "저녁", "밥 추천", "야식", "맛집"), (
        "든든한 거랑 가벼운 거 중 뭐가 당겨? 하나 골라주면 메뉴 추천해볼게.",
        "따뜻한 국물, 매운 음식, 가벼운 한 끼 중에 지금 뭐가 제일 당겨?",
    )),
    ("coffee", ("카페", "커피", "아메리카노", "라떼", "디저트"), (
        "커피 한 잔 할래? 깔끔하게 아메리카노, 달달하게 바닐라라떼. 오늘은 어느 쪽이야?",
        "카페 가면 늘 같은 메뉴 시켜, 아니면 신메뉴에 도전하는 편이야?",
    )),
    ("music", ("노래", "음악", "플레이리스트"), (
        "지금은 신나는 노래가 좋아, 차분한 노래가 좋아?",
        "요즘 반복해서 듣는 곡 있어? 어떤 분위기인지 궁금해.",
    )),
    ("movie", ("영화", "드라마", "넷플릭스", "볼거리", "애니"), (
        "부담 없이 웃기는 거랑 몰입해서 보는 거 중에 오늘은 뭐가 좋아?",
        "코미디, 액션, 추리 중 하나 골라봐. 보기 좋은 분위기부터 같이 찾아보자.",
    )),
    ("exercise", ("운동", "헬스", "웨이트", "유산소", "러닝", "산책"), (
        "오늘은 몸을 좀 쓰고 싶은 날이야, 편하게 쉬고 싶은 날이야?",
        "요즘 자주 하는 운동 있어? 운동 끝났을 때 기분 좋은 종목 하나만 골라봐.",
    )),
    ("travel", ("여행", "놀러", "바다", "휴가"), (
        "여행 간다면 바다 보며 쉬기 vs 도시 골목 구경하기. 어디 쪽이 더 당겨?",
        "여행하면 먹는 거, 풍경, 숙소 중에 뭐가 제일 중요해?",
    )),
    ("weather", ("날씨", "비 오", "비오", "눈 오", "더워", "추워"), (
        "그런 날엔 실내에서 보내는 게 좋아, 그래도 잠깐 나가고 싶어?",
        "지금 있는 곳은 날씨가 어때? 날씨 따라 오늘 계획도 바뀌었어?",
    )),
    ("weekend", ("주말", "쉬는 날", "쉬는날", "약속"), (
        "이번엔 쉬고 싶은 주말이야, 밖에서 뭐라도 하고 싶은 주말이야?",
        "주말에 딱 하나만 한다면 뭐 하고 싶어?",
    )),
    ("friends", ("친구", "친해", "사람 만나", "인간관계", "싸웠"), (
        "사람 사이에선 같은 말도 다르게 들리더라. 어떤 일이 있었어?",
        "친구 얘기구나. 좋은 소식이야, 마음에 걸리는 일이야?",
    )),
    ("pets", ("고양이", "강아지", "반려동물", "냥이", "댕댕이"), (
        "동물 얘기 좋지. 고양이랑 강아지 중에 누구한테 더 마음이 가?",
        "같이 지내는 동물 있어? 어떤 성격인지 궁금하다.",
    )),
    ("hobby", ("취미", "독서", "책 읽", "그림", "사진 찍"), (
        "요즘 시간 가는 줄 모르고 하는 게 있어?",
        "혼자 조용히 하는 취미랑 사람들하고 같이하는 취미 중 어느 쪽이 좋아?",
    )),
    ("season", ("봄", "여름", "가을", "겨울"), (
        "그 계절에 제일 하고 싶은 거 하나만 꼽으면 뭐야?",
        "계절마다 생각나는 음식이 있잖아. 넌 그 계절 하면 뭐가 떠올라?",
    )),
    ("bored", ("심심", "재밌는 거", "재미있는 거", "놀아줘"), (
        "밸런스 게임! 평생 여름 vs 평생 겨울. 뭐 고를래?",
        "밸런스 게임! 평생 집에서 놀기 vs 평생 밖에서 놀기. 뭐 고를래?",
    )),
    ("good", ("기분 좋", "행복", "신나", "재밌었", "잘됐"), (
        "오, 좋은 일 있었어? 뭐가 제일 좋았는지 궁금하다.",
        "오늘의 좋은 장면 하나만 고르면 뭐야?",
    )),
    ("thanks", ("고마", "감사", "땡큐"), (
        "언제든지. 또 떠오르는 얘기 있으면 해줘!",
        "나도 같이 얘기해서 좋았어.",
    )),
    ("intro", ("누구야", "이름", "뭐야 너", "정체"), (
        "나는 잡담 챗봇이야. 메뉴 골라주기, 밸런스 게임, 농담 같은 걸 할 수 있어.",
    )),
    ("help", ("도움말", "뭐 할 수", "사용법", "어떻게 써"), (
        "‘메뉴 추천해줘’, ‘농담해줘’, ‘밸런스 게임 하자’, ‘커피 vs 차’ 같은 말을 해봐. 일상 얘기도 좋아.",
    )),
    ("bye", ("바이", "이따 봐", "다음에 봐", "나 갈게"), (
        "좋아, 다음에 또 얘기하자!",
        "잘 가! 나중에 오늘 무슨 일 있었는지 알려줘.",
    )),
    ("hello", ("안녕", "하이", "반가워", "반갑"), (
        "안녕! 오늘 하루 어땠어?",
        "반가워! 오늘 가장 기억나는 일이 뭐야?",
        "하이! 지금 뭐 하고 있었어?",
    )),
]

FOOD_CHOICES = [
    (("국물", "따뜻"), "쌀국수나 국밥 어때? 따뜻한 국물로 가자."),
    (("매운", "매콤", "매워"), "매콤하게 떡볶이나 매운 순두부찌개 어때?"),
    (("가볍", "샐러드", "간단"), "샌드위치나 포케 어때? 가볍게 먹기 좋아."),
    (("든든", "고기"), "제육덮밥이나 국밥 어때? 한 끼 든든하게 먹기 좋아."),
]

SHORT_ANSWERS = {
    "응": "오케이. 그중에서 제일 먼저 떠오르는 거 하나만 얘기해줄래?",
    "어": "좋아. 조금만 더 풀어서 얘기해줘도 돼.",
    "아니": "그럼 다른 쪽이야? 지금은 어떤 얘기가 하고 싶어?",
    "몰라": "그럴 수도 있지. 그럼 오늘 먹은 것 중에 제일 맛있었던 거부터 얘기해볼까?",
    "그냥": "그냥인 날도 있지. 오늘 하루를 한 단어로 표현하면 뭐야?",
    "ㅋㅋ": "ㅋㅋ 뭐가 제일 웃겼어?",
    "ㅇㅇ": "좋아. 그 얘기 조금만 더 들려줘.",
}

FALLBACKS = (
    "그 얘기에서 네가 제일 신경 쓰는 부분이 뭐야?",
    "어떤 상황이었는지 한 문장만 더 설명해줄래?",
    "조금 더 얘기해줘도 좋아. 아니면 농담이나 밸런스 게임으로 분위기 바꿔볼까?",
)


def choose_reply(options, last_reply):
    alternatives = [option for option in options if option != last_reply]
    return random.choice(alternatives or options)


def compact(text):
    return "".join(text.casefold().split())


def reply_to(message, previous_topic=None, last_reply=""):
    plain = message.casefold().strip(" .?!~")
    key = compact(plain)
    if key in SHORT_ANSWERS:
        return SHORT_ANSWERS[key], previous_topic

    options = [option.strip() for option in plain.split(" vs ")]
    if len(options) >= 2 and all(options):
        return f"내 선택은 {random.choice(options)}! 넌 처음부터 마음이 기울던 쪽이 있었어?", None

    if previous_topic == "food" and len(key) <= 18:
        for keywords, reply in FOOD_CHOICES:
            if any(keyword in key for keyword in keywords):
                return reply, None

    if previous_topic in ("game", "bored") and len(key) <= 18:
        for choice in ("여름", "겨울", "집", "밖", "계획대로", "즉흥"):
            if choice in key and (choice in last_reply or choice in ("계획대로", "즉흥")):
                return f"{choice} 쪽을 골랐구나. 그게 더 좋은 이유가 뭐야?", None

    if previous_topic == "music":
        if any(word in key for word in ("신나는", "신난", "신나게", "업비트")):
            return "그럼 신나는 곡으로 가자. 데이식스 ‘한 페이지가 될 수 있게’ 어때?", None
        if any(word in key for word in ("차분", "잔잔", "조용")):
            return "차분한 분위기면 아이유 ‘밤편지’ 어때?", None

    if previous_topic == "movie":
        if "코미디" in key or "웃기는" in key:
            return "가볍게 웃고 싶다면 영화 ‘극한직업’ 어때?", None
        if "추리" in key or "몰입" in key:
            return "단서 맞춰보는 재미로 ‘나이브스 아웃’ 어때?", None
        if "액션" in key:
            return "움직임이 시원한 액션이면 ‘미션 임파서블: 폴아웃’ 어때?", None

    for topic, keywords, replies in CHAT_RULES:
        if any(compact(keyword) in key for keyword in keywords):
            reply = choose_reply(replies, last_reply)
            if topic == "number":
                reply = reply.format(number=random.randint(1, 100))
            return reply, topic

    return choose_reply(FALLBACKS, last_reply), previous_topic


def app_password():
    password = os.getenv("CHAT_PASSWORD")
    if password:
        return password
    try:
        return st.secrets.get("CHAT_PASSWORD", "")
    except FileNotFoundError:
        return ""


st.set_page_config(page_title="잡담 챗봇", page_icon="💬")
st.title("💬 잡담 챗봇")

if not st.session_state.get("unlocked"):
    with st.form("login"):
        password = st.text_input("비밀번호", type="password")
        submitted = st.form_submit_button("입장")

    if submitted:
        expected = app_password()
        if expected and compare_digest(password.encode(), expected.encode()):
            st.session_state.unlocked = True
            st.rerun()
        st.error("비밀번호를 확인해줘.")

    st.stop()

with st.expander("어떤 말을 해볼까?"):
    st.markdown(
        " - **일상** · 배고파 / 과제 너무 많아 / 오늘 좀 피곤해\n"
        " - **추천** · 메뉴 추천해줘 / 노래 추천해줘 / 영화 추천해줘\n"
        " - **놀기** · 농담해줘 / 밸런스 게임 하자 / 숫자 뽑아줘\n"
        " - **고르기** · 치킨 vs 떡볶이"
    )
    if st.button("대화 초기화"):
        st.session_state.pop("messages", None)
        st.session_state.pop("topic", None)
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = [
        ("assistant", "안녕! 지금 기분이나 오늘 있었던 일을 얘기해줘.")
    ]

for role, message in st.session_state.messages:
    with st.chat_message(role):
        st.text(message)

if message := st.chat_input("메시지를 입력해"):
    last_reply = st.session_state.messages[-1][1]
    reply, topic = reply_to(message, st.session_state.get("topic"), last_reply)
    st.session_state.messages.extend([
        ("user", message),
        ("assistant", reply),
    ])
    st.session_state.topic = topic
    st.rerun()
