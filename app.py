# -*- coding: utf-8 -*-
import streamlit as st
import requests
from datetime import datetime

# 🔒 API 키는 절대 코드에 직접 쓰지 말고, Streamlit Secrets에서 불러오기
api_key = st.secrets["API_KEY"]

# ------------------------------------------------------------------------------------------
# 함수 정의
# ------------------------------------------------------------------------------------------

# 학교 정보 (예시용 더미 데이터)
DUMMY_SCHOOLS = {
    "강남초등학교": {"office_code": "B10", "school_code": "7021319"},
    "서초중학교": {"office_code": "B10", "school_code": "7000109"},
    "성북고등학교": {"office_code": "B10", "school_code": "7010467"}
}

def get_school_info(school_name):
    """학교 이름을 기반으로 교육청 코드와 학교 코드를 반환"""
    return DUMMY_SCHOOLS.get(school_name)

def get_school_lunch_menu(office_code, school_code, date_str):
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

        # 응답 JSON 구조에 맞춰 데이터 추출
        meal_info = data.get("mealServiceDietInfo")
        if meal_info:
            menu = meal_info[1]["row"][0]["DDISH_NM"]  # 실제 급식 메뉴
            return {"date": date_str, "menu": menu}

    except Exception as e:
        st.error(f"API 요청 오류: {e}")
        return None

    return None

# ------------------------------------------------------------------------------------------
# Streamlit UI
# ------------------------------------------------------------------------------------------

st.title("전국 학교 급식 정보 🥗")
st.sidebar.header("학교 및 날짜 선택")

school_name = st.sidebar.text_input("학교 이름을 입력하세요", "예: 강남초등학교")
selected_date = st.sidebar.date_input("날짜를 선택하세요", value=datetime.today())
search_button = st.sidebar.button("급식 검색하기")

if search_button:
    with st.spinner("정보를 불러오는 중입니다..."):
        school_info = get_school_info(school_name)
        if school_info:
            date_str = selected_date.strftime("%Y%m%d")
            menu_data = get_school_lunch_menu(
                school_info["office_code"],
                school_info["school_code"],
                date_str
            )
            if menu_data:
                st.subheader(f"{school_name} {selected_date.strftime('%Y년 %m월 %d일')} 급식 메뉴")
                st.markdown(f"**{menu_data['menu']}**")
            else:
                st.warning("급식 정보가 없습니다.")
        else:
            st.error("학교 정보를 찾을 수 없습니다. 다시 시도해 주세요.")

st.markdown("---")
st.markdown("이 앱은 NEIS 급식 API 데이터를 바탕으로 제작되었습니다.")

