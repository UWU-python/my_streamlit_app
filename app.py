import streamlit as st
import requests
import pandas as pd
import datetime
import sqlite3

# ==========================
# DB 관련 함수
# ==========================
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
    conn = sqlite3.connect("votes.db")
    c = conn.cursor()
    votes = get_votes(date, school_code)
    if vote_type == "good":
        votes["good"] += 1
    else:
        votes["bad"] += 1
    c.execute("REPLACE INTO votes (date, school_code, good, bad) VALUES (?, ?, ?, ?)",
              (date, school_code, votes["good"], votes["bad"]))
    conn.commit()
    conn.close()
    return votes


# ==========================
# 급식 조회 관련
# ==========================
def get_school_list(region, school_name):
    url = f"https://open.neis.go.kr/hub/schoolInfo?ATPT_OFCDC_SC_NM={region}&SCHUL_NM={school_name}&Type=json&KEY=인증키"
    response = requests.get(url)
    data = response.json()

    if "schoolInfo" not in data:
        return []

    schools = data["schoolInfo"][1]["row"]
    return [
        {
            "학교명": s["SCHUL_NM"],
            "학교코드": s["SD_SCHUL_CODE"],
            "지역": s["ATPT_OFCDC_SC_NM"]
        }
        for s in schools
    ]

def get_meal(date, school_code, region):
    url = f"https://open.neis.go.kr/hub/mealServiceDietInfo?ATPT_OFCDC_SC_NM={region}&SD_SCHUL_CODE={school_code}&MLSV_YMD={date}&Type=json&KEY=인증키"
    response = requests.get(url)
    data = response.json()

    if "mealServiceDietInfo" not in data:
        return None

    meals = data["mealServiceDietInfo"][1]["row"]
    return meals


# ==========================
# Streamlit 앱 시작
# ==========================
st.title("🍱 우리 학교 급식 조회기")

region = st.text_input("지역 입력 (예: 서울특별시)")
school_name = st.text_input("학교 이름 입력")

if st.button("검색하기"):
    schools = get_school_list(region, school_name)

    if not schools:
        st.error("검색 결과가 없습니다.")
    else:
        for s in schools:
            if st.button(f"{s['학교명']} ({s['지역']})"):
                st.session_state.selected_school = s

# 선택된 학교가 있을 때
if "selected_school" in st.session_state:
    school = st.session_state.selected_school
    school_code = school["학교코드"]
    region = school["지역"]

    today = datetime.date.today()
    date_str = today.strftime("%Y%m%d")

    meals = get_meal(date_str, school_code, region)

    st.subheader(f"📌 {school['학교명']} 오늘 급식")
    if not meals:
        st.warning("오늘 급식 정보가 없습니다.")
    else:
        for meal in meals:
            st.markdown(f"🍴 **{meal['MMEAL_SC_NM']}**")
            st.write(meal["DDISH_NM"].replace("<br/>", "\n"))

    # ==========================
    # 맛 평가 기능 추가
    # ==========================
    init_db()
    votes = get_votes(date_str, school_code)

    st.markdown("### 오늘 급식 맛 평가 🍴")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("👍 맛있어요"):
            votes = update_vote(date_str, school_code, "good")
    with col2:
        if st.button("👎 별로예요"):
            votes = update_vote(date_str, school_code, "bad")

    total_votes = votes["good"] + votes["bad"]
    if total_votes > 0:
        st.progress(int((votes["good"] / total_votes) * 100))
    st.write(f"👍 맛있어요: {votes['good']} 표")
    st.write(f"👎 별로예요: {votes['bad']} 표")
