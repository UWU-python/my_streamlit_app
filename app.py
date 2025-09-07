# -*- coding: utf-8 -*-
import streamlit as st
import requests
from datetime import datetime
import urllib.parse

# 🔒 API 키는 절대 코드에 직접 쓰지 말고, Streamlit Secrets에서 불러오기
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
    response = requests.get(url)
    if response.status_code != 200:
        return []
    try:
        data = response.json()
        if "schoolInfo" not in data:
            return []
        rows = data["schoolInfo"][1]["row"]
        return rows
    except Exception:
        return []

# ------------------------------------------------------------------------------------------
# 급식 API 호출
# ------------------------------------------------------------------------------------------
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
    "18": "조개류",
}

def replace_allergy_numbers(menu_text):
    """메뉴 안의 알레르기 숫자를 이름으로 치환"""
    import re
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
        if meal_info:
            rows = meal_info[1]["row"]
            menus = []
            for r in rows:
                menu_text = replace_allergy_numbers(r["DDISH_NM"])
                menus.append(menu_text)
            return menus
    except Exception as e:
        st.error(f"API 요청 오류: {e}")
        return None
    return None

# ------------------------------------------------------------------------------------------
# Streamlit UI
# ------------------------------------------------------------------------------------------
st.title("전국 학교 급식 정보 🥗")

school_name = st.text_input("학교 이름을 입력하세요 (예: 강남초등학교)")
selected_date = st.date_input("날짜를 선택하세요", value=datetime.today())
search_button = st.button("급식 검색하기")

if search_button:
    with st.spinner("학교와 급식 정보를 불러오는 중입니다..."):
        results = search_school(api_key, school_name)
        if results:
            # 주소에서 시/도 추출
            options = [
                f"{r['SCHUL_NM']} ({r['ORG_RDNMA'].split()[0]})"
                for r in results
            ]
            choice = st.selectbox("학교를 선택하세요", options)
            st.success(f"✅ 선택된 학교: {choice}")

            # 실제 코드 값 추출
            selected = results[options.index(choice)]
            office_code = selected["ATPT_OFCDC_SC_CODE"]
            school_code = selected["SD_SCHUL_CODE"]

            # 날짜 변환
            date_str = selected_date.strftime("%Y%m%d")

            # 급식 정보 가져오기
            menu_data = get_school_lunch_menu(api_key, office_code, school_code, date_str)
            if menu_data:
                st.subheader(f"{choice} {selected_date.strftime('%Y년 %m월 %d일')} 급식")
                st.markdown("메뉴 이름을 클릭하면 Google 검색 결과로 이동됩니다 🔎")

                for menu in menu_data:
                    # 줄 단위로 나눠서 링크 생성
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
            st.error("학교 정보를 찾을 수 없습니다. 다시 입력해 주세요.")

st.markdown("---")
st.markdown("이 앱은 NEIS 급식 API 데이터를 바탕으로 제작되었습니다.")
