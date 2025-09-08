import streamlit as st
import requests
import datetime
import sqlite3

# NEIS API 키
API_KEY = "YOUR_API_KEY"

# 알레르기 코드 매핑
ALLERGY_MAP = {
    "1": "난류",
    "2": "우유",
    "3": "메밀",
    "4": "땅콩",
    "5": "대두",
    "6": "밀",
    "7": "고등어",
    "8": "게",
    "9": "새우",
    "10": "돼지고기",
    "11": "복숭아",
    "12": "토마토",
    "13": "아황산류",
    "14": "호두",
    "15": "닭고기",
    "16": "쇠고기",
    "17": "오징어",
    "18": "조개류(굴, 전복, 홍합 포함)",
    "19": "잣",
}

# 지역 코드 매핑
REGION_CODES = {
    "서울": "B10",
    "부산": "C10",
    "대구": "D10",
    "인천": "E10",
    "광주": "F10",
    "대전": "G10",
    "울산": "H10",
    "세종": "I10",
    "경기": "J10",
    "강원": "K10",
    "충북": "M10",
    "충남": "N10",
    "전북": "P10",
    "전남": "Q10",
    "경북": "R10",
    "경남": "S10",
    "제주": "T10",
}

# ------------------ DB 관련 함수 ------------------

def init_db():
    conn = sqlite3.connect("votes.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            date TEXT,
            school_code TEXT,
            good INTEGER,
            bad INTEGER,
            PRIMARY KEY (date, school_code)
        )
    """)
    conn.commit()
    conn.close()

def get_votes(date, school_code):
    conn = sqlite3.connect("votes.db")
    c = conn.cursor()
    c.execute("SELECT good, bad FROM votes WHERE date=? AND school_code=?", (date, school_code))
    row = c.fetchone()
    conn.close()
    if row:
        return {"good": row[0], "bad": row[1]}
    else:
        return {"good": 0, "bad": 0}

def update_vote(date, school_code, vote_type):
    votes = get_votes(date, school_code)
    if vote_type == "good":
        votes["good"] += 1
    else:
        votes["bad"] += 1

    conn = sqlite3.connect("votes.db")
    c = conn.cursor()
    c.execute("REPLACE INTO votes (date, school_code, good, bad) VALUES (?, ?, ?, ?)",
              (date, school_code, votes["good"], votes["bad"]))
    conn.commit()
    conn.close()
    return votes

# ------------------ 급식 관련 함수 ------------------

def get_school_list(region, school_name):
    url = "https://open.neis.go.kr/hub/schoolInfo"
    params = {
        "KEY": API_KEY,
        "Type": "json",
        "ATPT_OFCDC_SC_CODE": REGION_CODES.get(region),
        "SCHUL_NM": school_name,
    }
    res = requests.get(url, params=params).json()
    if "schoolInfo" not in res:
        return []
    schools = res["schoolInfo"][1]["row"]
    return [
        {
            "학교명": s["SCHUL_NM"],
            "학교코드": s["SD_SCHUL_CODE"],
            "지역": region,
        }
        for s in schools
    ]

def get_meal(region, school_code, date):
    url = "https://open.neis.go.kr/hub/mealServiceDietInfo"
    params = {
        "KEY": API_KEY,
        "Type": "json",
        "ATPT_OFCDC_SC_CODE": REGION_CODES.get(region),
        "SD_SCHUL_CODE": school_code,
        "MLSV_YMD": date,
    }
    res = requests.get(url, params=params).json()
    if "mealServiceDietInfo" not in res:
        return None
    meals = res["mealServiceDietInfo"][1]["row"]
    return meals

def convert_allergy(menu):
    for num, name in ALLERGY_MAP.items():
        menu = menu.replace(f"({num})", f"({name})")
    return menu

# ------------------ Streamlit UI ------------------

st.title("📌 오늘의 급식")

# 지역 선택
region = st.selectbox("지역을 선택하세요", list(REGION_CODES.keys()))

# 학교명 입력
school_name = st.text_input("학교 이름 입력 (예: 서울고등학교)")

# 검색하기
if st.button("검색하기"):
    schools = get_school_list(region, school_name)

    if not schools:
        st.error("검색 결과가 없습니다.")
    else:
        st.write("학교를 선택하세요:")
        for i, s in enumerate(schools):
            if st.button(f"{s['학교명']} ({s['지역']})", key=f"school_{i}"):
                st.session_state.selected_school = s["학교명"]
                st.session_state.school_code = s["학교코드"]
                st.session_state.region = s["지역"]

# 선택된 학교 급식 표시
if "selected_school" in st.session_state:
    st.subheader(f"🏫 {st.session_state.selected_school}")

    today = datetime.date.today().strftime("%Y%m%d")
    meals = get_meal(st.session_state.region, st.session_state.school_code, today)

    if not meals:
        st.warning("오늘은 급식 정보가 없습니다.")
    else:
        for meal in meals:
            meal_name = meal["MMEAL_SC_NM"]  # 조식/중식/석식
            menu_items = meal["DDISH_NM"].split("<br/>")
            menu_items = [convert_allergy(m.strip()) for m in menu_items]

            st.markdown(f"### 🍴 {meal_name} ({today})")
            st.write("\n".join(menu_items))

        # ------------------ 맛 평가 ------------------
        init_db()
        votes = get_votes(today, st.session_state.school_code)

        st.markdown("### 오늘 급식 맛 평가 🍴")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("👍 맛있어요"):
                votes = update_vote(today, st.session_state.school_code, "good")
        with col2:
            if st.button("👎 별로예요"):
                votes = update_vote(today, st.session_state.school_code, "bad")

        total_votes = votes["good"] + votes["bad"]
        if total_votes > 0:
            st.progress(int((votes["good"] / total_votes) * 100))
        st.write(f"👍 맛있어요: {votes['good']} 표")
        st.write(f"👎 별로예요: {votes['bad']} 표")
