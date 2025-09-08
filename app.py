import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import os
import json

# 🔹 세션 상태 기본값 설정 (오류 방지)
if "region" not in st.session_state:
    st.session_state.region = None
if "school_code" not in st.session_state:
    st.session_state.school_code = None
if "ratings" not in st.session_state:
    st.session_state.ratings = {}  # 맛 평가 저장용

# 🔹 NEIS API 키 (환경변수에서 불러오기)
NEIS_API_KEY = os.getenv("NEIS_API_KEY")

# 🔹 지역 교육청 코드 매핑
region_map = {
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
    "제주": "T10"
}

# 🔹 학교 검색 함수
def search_school(region, school_name):
    url = f"https://open.neis.go.kr/hub/schoolInfo?KEY={NEIS_API_KEY}&Type=json&pIndex=1&pSize=100&SCHUL_NM={school_name}&ATPT_OFCDC_SC_CODE={region_map[region]}"
    res = requests.get(url)
    data = res.json()
    if "schoolInfo" in data:
        rows = data["schoolInfo"][1]["row"]
        return pd.DataFrame(rows)
    return None

# 🔹 급식 불러오기
def get_meal(region, school_code, date):
    url = f"https://open.neis.go.kr/hub/mealServiceDietInfo?KEY={NEIS_API_KEY}&Type=json&pIndex=1&pSize=10&ATPT_OFCDC_SC_CODE={region_map[region]}&SD_SCHUL_CODE={school_code}&MLSV_YMD={date}"
    res = requests.get(url)
    data = res.json()
    if "mealServiceDietInfo" in data:
        rows = data["mealServiceDietInfo"][1]["row"]
        meals = rows[0]["DDISH_NM"].split("<br/>")
        # 알레르기 숫자 제거
        clean_meals = []
        for m in meals:
            clean_meals.append(''.join([c for c in m if not c.isdigit()]))
        return clean_meals
    return None

# 🔹 맛 평가 저장 함수
def save_rating(menu, rating):
    st.session_state.ratings[menu] = rating

# 🔹 앱 시작
st.title("🍽️ 오늘의 급식 확인하기")

# 오늘 날짜
today = datetime.now().strftime("%Y%m%d")

# 지역 선택
region = st.selectbox("지역 선택", list(region_map.keys()))
school_name = st.text_input("학교 이름 입력")

if st.button("학교 검색"):
    schools = search_school(region, school_name)
    if schools is not None:
        st.session_state.region = region
        st.session_state.schools = schools
        st.write("학교를 선택하세요:")
        for i, row in schools.iterrows():
            if st.button(row["SCHUL_NM"]):
                st.session_state.school_code = row["SD_SCHUL_CODE"]
    else:
        st.error("학교를 찾을 수 없습니다.")

# 🔹 급식 보여주기
if st.session_state.region and st.session_state.school_code:
    meals = get_meal(st.session_state.region, st.session_state.school_code, today)
    if meals:
        st.subheader("🍴 오늘의 급식 메뉴")
        for menu in meals:
            st.markdown(f"- [{menu} (Google)](https://www.google.com/search?q={menu})")
            
            # 맛 평가 기능
            rating = st.radio(
                f"👉 {menu} 맛 평가:",
                ["아직 안 먹음", "맛있음 😋", "그냥 그럼 😐", "별로임 😣"],
                key=f"rating_{menu}"
            )
            if rating != "아직 안 먹음":
                save_rating(menu, rating)

        st.subheader("📊 맛 평가 결과")
        if st.session_state.ratings:
            for menu, rating in st.session_state.ratings.items():
                st.write(f"{menu} ➝ {rating}")
        else:
            st.write("아직 평가가 없습니다.")
    else:
        st.warning("오늘은 급식 정보가 없습니다.")
