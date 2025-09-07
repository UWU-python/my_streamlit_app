# -*- coding: utf-8 -*-
import streamlit as st
import requests
from datetime import datetime
import urllib.parse
import re

# 🔒 API 키는 Streamlit Secrets에서 불러오기
api_key = st.secrets["API_KEY"]

# ------------------------------------------------------------------------------------------
# 학교 검색 함수
# ------------------------------------------------------------------------------------------
def search_school(api_key, school_name):
    """학교 이름으로 검색"""
    url = (
        "https://open.neis.go.kr/hub/schoolInfo"
        f"?KEY={api_key}&Type=json&pIndex=1&pSize=100&SCHUL_NM={school_name}"
    )
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if "schoolInfo" not in data:
            return []
        return data["schoolInfo"][1]["row"]
    except Exception:
        return []

# ------------------------------------------------------------------------------------------
# 급식 API 호출
# ------------------------------------------------------------------------------------------
ALLERGY_MAP = {
    "1": "난류", "2": "우유", "3": "메밀", "4": "땅콩", "5": "대두", "6": "밀",
    "7": "고등어", "8": "게", "9": "새우", "10": "돼지고기", "11": "복숭아", "12": "토마토",
    "13": "아황산류", "14": "호두", "15": "닭고기", "16": "쇠고기", "17": "오징어",
    "18": "조개류",
}

def replace_allergy_numbers(menu_text):
    """메뉴 안의 알레르기 숫자를 이름으로 치환"""
    def repl(match):
        nums = match.group(0).strip("()").split(".")
        names = [ALLERGY_MAP.get(n, n) for n in nums]
        return "(" + ", ".join(names) + ")"
    return re.sub(r"\(([\d\.]+)\)", repl, menu_text)

def get_school_lunch_menu(api_key, office_code, school_code, date_str):
    """급식 메뉴 API 호출"""
    url = (
        f"https://open.neis.go.kr/hub/mealServiceDietInfo"
        f"?KEY={api_key}"
        f"&Type=json&pIndex=1&pSize=100"
        f"&ATPT_OFCDC_SC_CODE={office_code}"
        f"&SD_SCHUL_CODE={school_code}"
        f"&MLSV_YMD={date_str}"
    )
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        meal_info = data.get("mealServiceDietInfo")
        if not meal_info or len(meal_info) < 2 or "row" not in meal_info[1]:
            return None
        rows = meal_info[1]["row"]

        menus = []
        for r in rows:
            menu_text = replace_allergy_numbers(r.get("DDISH_NM", ""))
            menus.append(menu_text)
        return menus
    except Exception as e:
        st.error(f"API 요청 오류: {e}")
        return None

# ------------------------------------------------------------------------------------------
# Streamlit UI
# ------------------------------------------------------------------------------------------
st.title("전국 학교 급식 정보 🥗")

# Session state 초기화
if "search_clicked" not in st.session_state:
    st.session_state.search_clicked = False
if "school_results" not in st.session_state:
    st.session_state.school_results = []
if "selected_school" not in st.session_state:
    st.session_state.selected_school = None

school_name = st.text_input("학교 이름을 입력하세요 (예: 강남초등학교)")
selected_date = st.date_input("날짜를 선택하세요", value=datetime.today())

# 버튼 클릭 시 session state 업데이트
if st.button("급식 검색하기"):
    st.session_state.search_clicked = True
    st.session_state.school_results = search_school(api_key, school_name)

# 학교 검색 후 UI 표시
if st.session_state.search_clicked:
    results = st.session_state.school_results
    if results:
        options = [
            f"{r['SCHUL_NM']} ({r['ORG_RDNMA'].split()[0]})"
            for r in results
        ]
        # 이전 선택 유지
        if st.session_state.selected_school not in options:
            st.session_state.selected_school = options[0]
        choice = st.selectbox("학교를 선택하세요", options, index=options.index(st.session_state.selected_school))
        st.session_state.selected_school = choice
        st.success(f"✅ 선택된 학교: {choice}")

        # 선택된 학교 안전하게 매칭
        office_code, school_code = None, None
        for r in results:
            if r['SCHUL_NM'] in choice and r['ORG_RDNMA'].split()[0] in choice:
                office_code = r["ATPT_OFCDC_SC_CODE"]
                school_code = r["SD_SCHUL_CODE"]
                break

        if office_code and school_code:
            date_str = selected_date.strftime("%Y%m%d")
            menu_data = get_school_lunch_menu(api_key, office_code, school_code, date_str)
            if menu_data:
                st.subheader(f"{choice} {selected_date.strftime('%Y년 %m월 %d일')} 급식")
                st.markdown("메뉴 이름을 클릭하면 Google 검색 결과로 이동됩니다 🔎")

                for menu in menu_data:
                    lines = menu.split("<br/>")
                    for line in lines:
                        clean_line = line.strip()
                        if clean_line:
                            query = urllib.parse.quote(clean_line)
                            search_url = f"https://www.google.com/search?q={query}"
                            st.markdown(f"- [{clean_line} (Google)]({search_url})", unsafe_allow_html=True)
                    st.markdown("---")
            else:
                st.warning("급식 정보가 없습니다.")
        else:
            st.error("학교 코드 추출에 실패했습니다.")
    else:
        st.error("학교 정보를 찾을 수 없습니다. 다시 입력해 주세요.")

st.markdown("---")
st.markdown("이 앱은 NEIS 급식 API 데이터를 바탕으로 제작되었습니다.")
