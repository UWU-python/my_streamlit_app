# -*- coding: utf-8 -*-
import streamlit as st
import requests
from datetime import datetime, timedelta

api_key = st.secrets["API_KEY"]

# ----------------------------
# 알레르기 코드 매핑
# ----------------------------
ALLERGY_MAP = {
    "1": "달걀", "2": "우유", "3": "밀", "4": "메밀", "5": "땅콩",
    "6": "대두", "7": "호두", "8": "닭고기", "9": "쇠고기",
    "10": "돼지고기", "11": "복숭아", "12": "토마토",
    "13": "아황산류", "14": "조개류(굴,전복,홍합 포함)", "15": "참치",
    "16": "고등어", "17": "게", "18": "새우", "19": "오징어", "20": "조개류"
}

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
    """급식 메뉴 + 알레르기 정보 가져오기"""
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
                menu = item["DDISH_NM"].replace("<br/>", "\n")
                allergy_codes = item.get("ALLERG_NM", "")
                menus.append((menu, allergy_codes))
        return menus
    except:
        return []

# ----------------------------
# Streamlit UI
# ----------------------------
st.title("전국 학교 급식 정보 🥗")

# ----------------------------
# 사이드바 입력 위젯 (항상 표시)
# ----------------------------
# 지역 선택
regions = {
    "서울": "B10", "부산": "C10", "대구": "D10", "인천": "I10",
    "광주": "G10", "대전": "E10", "울산": "U10", "세종": "S10",
    "경기": "J10", "강원": "H10", "충북": "K10", "충남": "M10",
    "전북": "F10", "전남": "N10", "경북": "O10", "경남": "P10", "제주": "Q10"
}
region_name = st.sidebar.selectbox("지역 선택", list(regions.keys()))
region_code = regions[region_name]

# 학교급 선택
school_levels = {"초등학교": "E", "중학교": "M", "고등학교": "H"}
school_level_name = st.sidebar.selectbox("학교급 선택", list(school_levels.keys()))
school_level_code = school_levels[school_level_name]

# 학교 이름 입력
school_name = st.sidebar.text_input("학교 이름 입력", "")

# 날짜 선택
selected_date = st.sidebar.date_input("날짜 선택", value=datetime.today())
date_str = selected_date.strftime("%Y%m%d")

# 즐겨찾기 초기화
if "favorites" not in st.session_state:
    st.session_state["favorites"] = []

# 검색 버튼
search_button = st.sidebar.button("급식 검색하기")

# ----------------------------
# 검색 버튼 클릭 시 처리
# ----------------------------
if search_button:
    if not school_name:
        st.warning("학교 이름을 입력해주세요.")
    else:
        # 학교 코드 가져오기
        schools = get_schools(region_code, school_level_code)
        school_code = next((s["code"] for s in schools if s["name"] == school_name), None)
        if school_code:
            menus = get_lunch_menu(region_code, school_code, date_str)
            if menus:
                # 즐겨찾기 버튼
                if school_name not in st.session_state["favorites"]:
                    if st.button("즐겨찾기 추가"):
                        st.session_state["favorites"].append(school_name)
                        st.success(f"{school_name} 즐겨찾기 추가 완료!")
                else:
                    if st.button("즐겨찾기 제거"):
                        st.session_state["favorites"].remove(school_name)
                        st.info(f"{school_name} 즐겨찾기에서 제거됨.")

                # 메뉴 출력
                st.subheader(f"{school_name} {selected_date.strftime('%Y년 %m월 %d일')} 급식 메뉴")
                for menu, allergy in menus:
                    if allergy:
                        st.text(f"{menu}\n(알레르기: {allergy})")
                    else:
                        st.text(menu)

                # 점심 시간 기준 알림 (학교급별 기본 점심 시간)
                lunch_hours = {"E": 11, "M": 12, "H": 12}  # 초등, 중, 고
                lunch_minutes = {"E": 50, "M": 20, "H": 30}
                lunch_time = datetime.combine(selected_date, datetime.strptime(f"{lunch_hours[school_level_code]}:{lunch_minutes[school_level_code]}", "%H:%M").time())
                now = datetime.now()
                if now < lunch_time:
                    remaining = lunch_time - now
                    hours, remainder = divmod(remaining.seconds, 3600)
                    minutes, _ = divmod(remainder, 60)
                    st.info(f"오늘 점심까지 약 {hours}시간 {minutes}분 남았습니다! 미리 메뉴 확인하세요 🍽️")
                    st.markdown("**오늘 메뉴 미리보기로 아침 계획 세우기 👍**")
            else:
                st.warning("급식 정보가 없습니다.")
        else:
            st.error("학교 정보를 찾을 수 없습니다. 지역과 학교명을 다시 확인해주세요.")

# ----------------------------
# 즐겨찾기 목록 표시
# ----------------------------
if st.session_state["favorites"]:
    st.sidebar.markdown("### 즐겨찾기 학교")
    for fav in st.session_state["favorites"]:
        st.sidebar.text(fav)
