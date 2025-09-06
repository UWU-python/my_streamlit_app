# -*- coding: utf-8 -*-
import streamlit as st
import requests
from datetime import datetime, timedelta

api_key = st.secrets["API_KEY"]

# ----------------------------
# 함수 정의
# ----------------------------

def get_schools(region_code, school_level):
    """지역 코드와 학교급으로 학교 리스트 가져오기"""
    url = (
        f"https://open.neis.go.kr/hub/schoolInfo"
        f"?KEY={api_key}&Type=json&pIndex=1&pSize=1000"
        f"&ATPT_OFCDC_SC_CODE={region_code}"
        f"&SD_SCHUL_SC_CODE={school_level}"
    )
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        schools = []
        if "schoolInfo" in data:
            for item in data["schoolInfo"][1]["row"]:
                schools.append({"name": item["SCHUL_NM"], "code": item["SD_SCHUL_CODE"]})
        return schools
    except:
        return []

def get_lunch_menu(office_code, school_code, date_str):
    url = (
        f"https://open.neis.go.kr/hub/mealServiceDietInfo"
        f"?KEY={api_key}&Type=json&pIndex=1&pSize=100"
        f"&ATPT_OFCDC_SC_CODE={office_code}&SD_SCHUL_CODE={school_code}"
        f"&MLSV_YMD={date_str}"
    )
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        meal_info = data.get("mealServiceDietInfo")
        menus = []
        if meal_info:
            for item in meal_info[1]["row"]:
                menu = item["DDISH_NM"]
                # <br/> 대신 줄바꿈으로 처리
                menu = menu.replace("<br/>", "\n")
                menus.append(menu)
        return menus
    except:
        return []

# ----------------------------
# Streamlit UI
# ----------------------------

st.title("전국 학교 급식 정보 🥗")

# 1. 지역 선택
regions = {
    "서울": "B10", "부산": "C10", "대구": "D10", "인천": "I10",
    "광주": "G10", "대전": "E10", "울산": "U10", "세종": "S10",
    "경기": "J10", "강원": "H10", "충북": "K10", "충남": "M10",
    "전북": "F10", "전남": "N10", "경북": "O10", "경남": "P10", "제주": "Q10"
}
region_name = st.sidebar.selectbox("지역 선택", list(regions.keys()))
region_code = regions[region_name]

# 2. 학교급 선택
school_levels = {"초등학교": "E", "중학교": "M", "고등학교": "H"}
school_level_name = st.sidebar.selectbox("학교급 선택", list(school_levels.keys()))
school_level_code = school_levels[school_level_name]

# 3. 학교 리스트 가져오기
schools = get_schools(region_code, school_level_code)
school_names = [s["name"] for s in schools]

# 4. 학교 선택 또는 직접 입력
school_name_input = st.sidebar.text_input("학교 이름 직접 입력", "")
school_name_select = st.sidebar.selectbox("또는 학교 선택", school_names)
school_name = school_name_input if school_name_input else school_name_select

# 5. 날짜 선택
selected_date = st.sidebar.date_input("날짜 선택", value=datetime.today())
date_str = selected_date.strftime("%Y%m%d")

# 6. 급식 검색
if st.sidebar.button("급식 검색하기"):
    school_code = next((s["code"] for s in schools if s["name"] == school_name), None)
    if school_code:
        menus = get_lunch_menu(region_code, school_code, date_str)
        if menus:
            st.subheader(f"{school_name} {selected_date.strftime('%Y년 %m월 %d일')} 급식 메뉴")
            # 급식1, 급식2 구분
            for i, menu in enumerate(menus, start=1):
                st.markdown(f"### 급식 {i}")
                st.text(menu)
        else:
            st.warning("급식 정보가 없습니다.")
    else:
        st.error("학교 정보를 찾을 수 없습니다.")


