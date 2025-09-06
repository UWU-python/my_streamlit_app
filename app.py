# -*- coding: utf-8 -*-

# Streamlit, requests, pandas, datetime 라이브러리를 불러옵니다.
# streamlit: 웹 앱의 UI를 만듭니다.
# requests: API를 호출하여 데이터를 가져옵니다.
# pandas: 데이터를 표 형태로 다루기 쉽게 해줍니다.
# datetime: 날짜 정보를 다루기 위해 필요합니다.
import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ------------------------------------------------------------------------------------------
# 함수 정의
# ------------------------------------------------------------------------------------------

# (실제 API) 학교 정보를 검색하는 함수
# 실제 API를 사용하면 학교 이름을 기반으로 학교 코드와 교육청 코드를 가져와야 합니다.
# 여기서는 예시를 위해 몇몇 학교의 더미 데이터를 사용합니다.
DUMMY_SCHOOLS = {
    "강남초등학교": {"office_code": "B10", "school_code": "7021319"},
    "서초중학교": {"office_code": "B10", "school_code": "7000109"},
    "성북고등학교": {"office_code": "B10", "school_code": "7010467"}
}
def get_school_info(school_name):
    """
    학교 이름을 기반으로 교육청 코드와 학교 코드를 반환합니다.
    (실제로는 교육청 API를 통해 검색해야 합니다)
    """
    return DUMMY_SCHOOLS.get(school_name)

# (실제 API) 급식 정보를 가져오는 함수
def get_school_lunch_menu(office_code, school_code, date_str):
    """
    교육청 코드, 학교 코드, 날짜를 기반으로 급식 메뉴를 가져옵니다.
    """
    # API 요청 URL을 설정합니다.
    # 이 URL은 실제 API의 엔드포인트에 따라 변경해야 합니다.
    # 여기서는 예시를 위한 가짜 API URL을 사용합니다.
    url = f"https://api.example.com/school_lunch_menu?office_code={office_code}&school_code={school_code}&date={date_str}"
    
    try:
        # requests.get()을 사용하여 API에 GET 요청을 보냅니다.
        response = requests.get(url)
        # HTTP 응답 코드가 200 (성공)이 아니면 예외를 발생시킵니다.
        response.raise_for_status()
        
        # 응답 받은 데이터를 JSON 형식으로 변환합니다.
        data = response.json()
        
        # API 응답 구조에 따라 급식 메뉴 데이터를 추출합니다.
        # 여기서는 예시로 고정된 더미 데이터를 반환합니다.
        # 실제 API 데이터는 이 부분을 수정해야 합니다.
        if school_code in DUMMY_SCHOOLS.values():
            return {
                "date": date_str,
                "menu": "쌀밥, 김치찌개, 소불고기, 시금치나물, 깍두기, 우유"
            }
        
    except requests.exceptions.RequestException as e:
        # API 요청 중 오류가 발생하면 에러 메시지를 반환합니다.
        st.error(f"API 요청 중 오류가 발생했습니다: {e}")
        return None
        
    return None

# ------------------------------------------------------------------------------------------
# Streamlit UI 구성
# ------------------------------------------------------------------------------------------

# 페이지 제목을 설정합니다.
st.title("전국 학교 급식 정보 🥗")

# 사이드바에 제목을 추가합니다.
st.sidebar.header("학교 및 날짜 선택")

# 사이드바에 텍스트 입력 위젯을 추가합니다.
school_name = st.sidebar.text_input("학교 이름을 입력하세요", "예: 강남초등학교")

# 사이드바에 날짜 입력 위젯을 추가합니다.
# `value`는 기본값으로 오늘 날짜를 설정합니다.
selected_date = st.sidebar.date_input("날짜를 선택하세요", value=datetime.today())

# 검색 버튼을 추가합니다.
search_button = st.sidebar.button("급식 검색하기")

# ------------------------------------------------------------------------------------------
# 사용자 입력에 따른 동작 처리
# ------------------------------------------------------------------------------------------

# 사용자가 버튼을 클릭하면 다음 코드가 실행됩니다.
if search_button:
    # 사용자에게 진행 상황을 알리기 위해 로딩 스피너를 보여줍니다.
    with st.spinner("정보를 불러오는 중입니다..."):
        # `get_school_info` 함수를 호출하여 학교 정보를 가져옵니다.
        school_info = get_school_info(school_name)

        if school_info:
            # 날짜 형식을 'YYYYMMDD'로 변환합니다.
            date_str = selected_date.strftime("%Y%m%d")
            
            # `get_school_lunch_menu` 함수를 호출하여 급식 메뉴를 가져옵니다.
            menu_data = get_school_lunch_menu(
                school_info["office_code"],
                school_info["school_code"],
                date_str
            )
            
            if menu_data:
                # 데이터를 성공적으로 가져왔을 경우, UI에 표시합니다.
                st.subheader(f"{school_name} {selected_date.strftime('%Y년 %m월 %d일')} 급식 메뉴")
                st.markdown(f"**{menu_data['menu']}**")
            else:
                st.warning("선택하신 날짜의 급식 정보가 없습니다.")
        else:
            # 학교 정보를 찾지 못한 경우 경고 메시지를 보여줍니다.
            st.error("입력하신 학교 정보를 찾을 수 없습니다. 다시 시도해 주세요.")

# ------------------------------------------------------------------------------------------
# 추가 정보 및 푸터
# ------------------------------------------------------------------------------------------
st.markdown("---")
st.markdown("이 앱은 교육청 급식 정보 API의 예제를 바탕으로 제작되었습니다.")