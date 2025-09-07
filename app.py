# -*- coding: utf-8 -*-
import streamlit as st
import requests
from datetime import datetime
import urllib.parse
import re

# 🔒 API 키는 절대 코드에 직접 쓰지 말고, Streamlit Secrets에서 불러오기
api_key = st.secrets["API_KEY"]

# ------------------------------------------------------------------------------------------
# 알레르기 번호 → 이름 매핑 (교육부 기준)
# ------------------------------------------------------------------------------------------
allergy_map = {
    "1": "난류", "2": "우유", "3": "메밀", "4": "땅콩", "5": "대두",
    "6": "밀", "7": "고등어", "8": "게", "9": "새우", "10": "돼지고기",
    "11": "복숭아", "12": "토마토", "13": "아황산류", "14": "호두",
    "15": "닭고기", "16": "쇠고기", "17": "오징어", "18": "조개류",
    "19": "잣"
}

def convert_allergy_numbers(menu_item):
    """급식 메뉴 안의 숫자를 알레르기 이름으로 변환"""
    match = re.search(r"\(([\d\.]+)\)", menu_item)
    if not match:
        return menu_item
    
    numbers = match.group(1).split(".")
    allergy_names = [allergy_map.get(num, num) for num in numbers]
    new_text = f"(알레르기: {', '.join(allergy_names)})"
    
    return menu_item.replace(match.group(0), new_text)

# ------------------------------------------------------------------------------------------
# 함수 정의
# ------------------------------------------------------------------------------------------

def get_school_info(school_name):
    """학교 이름을 기반으로 교육청 코드와 학교 코드를 검색"""
    url = (
        f"https://open.neis.go.kr/hub/schoolInfo"
        f"?KEY={api_key}"
        f"&Type=json&pIndex=1&pSize=100"
        f"&SCHUL_NM={urllib.parse.quote(school_name)}"
    )

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        info = data.get("schoolInfo")
        if info:
            school_data = info[1]["row"][0]
            return {
                "office_code": school_data["ATPT_OFCDC_SC_CODE"],
                "school_code": school_data["SD_SCHUL_CODE"],
                "name": school_data["SCHUL_NM"],
            }
    except Exception as e:
        st.error(f"학교 정보 API 오류: {e}")
        return None

    return None

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

        meal_info = data.get("mealServiceDietInfo")
        if meal_info:
            rows = meal_info[1]["row"]
            menus = [row["DDISH_NM"] for row in rows]
            return {"date": date_str, "menus": menus}

    except Exception as e:
        st.error(f"API 요청 오류: {e}")
        return None

    return None

# ------------------------------------------------------------------------------------------
# Streamlit UI
# ------------------------------------------------------------------------------------------

st.title("전국 학교 급식 정보 🥗")

school_name = st.text_input("학교 이름을 입력하세요 (예: 강남초등학교, 서초중학교, 성북고등학교)")
selected_date = st.date_input("날짜를 선택하세요", value=datetime.today())
search_button = st.button("급식 검색하기")

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
                st.subheader(f"{school_info['name']} {selected_date.strftime('%Y년 %m월 %d일')} 급식 메뉴 🍽️")
                menus = menu_data["menus"]

                for menu in menus:
                    # 줄 단위로 나눠서 각각 변환 후 출력
                    lines = menu.split("<br/>")
                    for line in lines:
                        clean_line = line.strip()
                        if clean_line:
                            clean_line = convert_allergy_numbers(clean_line)  # ✅ 알레르기 변환 적용
                            query = urllib.parse.quote(clean_line)
                            search_url = f"https://www.google.com/search?q={query}"
                            st.markdown(f"- [{clean_line} (Google)]({search_url})", unsafe_allow_html=True)

                    st.markdown("---")
            else:
                st.warning("급식 정보가 없습니다.")
        else:
            st.error("학교 정보를 찾을 수 없습니다. 다시 시도해 주세요.")

st.markdown("---")
st.markdown("이 앱은 NEIS 급식 API 데이터를 바탕으로 제작되었습니다. 메뉴를 클릭하면 검색 결과로 이동됩니다.")
