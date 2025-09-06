# -*- coding: utf-8 -*-
import streamlit as st
import requests
from datetime import datetime
import urllib.parse

# 🔒 API 키는 Streamlit Secrets에서 불러오기
api_key = st.secrets["API_KEY"]

# ------------------------------------------------------------------------------------------
# 함수 정의
# ------------------------------------------------------------------------------------------

def search_school(school_name):
    """학교 이름으로 NEIS API에서 학교 코드 검색"""
    url = (
        f"https://open.neis.go.kr/hub/schoolInfo"
        f"?KEY={api_key}&Type=json&pIndex=1&pSize=100&SCHUL_NM={urllib.parse.quote(school_name)}"
    )
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        school_info = data.get("schoolInfo")
        if school_info:
            rows = school_info[1]["row"]
            return [
                {"name": row["SCHUL_NM"], "office_code": row["ATPT_OFCDC_SC_CODE"], "school_code": row["SD_SCHUL_CODE"]}
                for row in rows
            ]
    except Exception as e:
        st.error(f"학교 검색 오류: {e}")
        return []
    return []

def get_school_lunch_menu(office_code, school_code, date_str):
    """급식 메뉴 API 호출"""
    url = (
        f"https://open.neis.go.kr/hub/mealServiceDietInfo"
        f"?KEY={api_key}&Type=json&pIndex=1&pSize=100"
        f"&ATPT_OFCDC_SC_CODE={office_code}"
        f"&SD_SCHUL_CODE={school_code}"
        f"&MLSV_YMD={date_str}"
    )
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        meal_info = data.get("mealServiceDietInfo")
        if meal_info:
            menus = meal_info[1]["row"][0]["DDISH_NM"]
            return menus
    except Exception as e:
        st.error(f"급식 API 오류: {e}")
        return None
    return None

# ------------------------------------------------------------------------------------------
# Streamlit UI
# ------------------------------------------------------------------------------------------

st.title("전국 학교 급식 정보 🥗")

# 학교 검색 입력
school_name = st.text_input("학교 이름을 입력하세요 (예: 강남초등학교 / 서초중학교 / 성북고등학교)")
selected_date = st.date_input("날짜를 선택하세요", value=datetime.today())
search_button = st.button("급식 검색하기")

if search_button:
    with st.spinner("정보를 불러오는 중입니다..."):
        schools = search_school(school_name)
        if schools:
            # 검색 결과 여러 학교 중 선택 (라벨 제거)
            school_options = [s["name"] for s in schools]
            selected_school = st.selectbox("", school_options)

            school_info = next(s for s in schools if s["name"] == selected_school)
            date_str = selected_date.strftime("%Y%m%d")
            menu_data = get_school_lunch_menu(
                school_info["office_code"],
                school_info["school_code"],
                date_str
            )

            if menu_data:
                st.subheader(f"{selected_school} {selected_date.strftime('%Y년 %m월 %d일')} 급식 메뉴 🍽️")
                st.caption("👉 메뉴이름을 클릭하면 검색결과로 이동됩니다 (Google)")

                # 급식 메뉴 가공 (줄바꿈 & HTML 태그 제거)
                menus = menu_data.replace("<br/>", "\n").split("\n")
                for menu in menus:
                    clean_line = menu.strip()
                    if clean_line:
                        query = urllib.parse.quote(clean_line)
                        search_url = f"https://www.google.com/search?q={query}"
                        st.markdown(f"- [메뉴이름: {clean_line} (Google)]({search_url})", unsafe_allow_html=True)
            else:
                st.warning("급식 정보가 없습니다.")
        else:
            st.error("학교를 찾을 수 없습니다. 정확한 이름을 입력하세요.")

st.markdown("---")
st.markdown("이 앱은 NEIS 급식 API 데이터를 바탕으로 제작되었습니다.")
