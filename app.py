# -*- coding: utf-8 -*-
import streamlit as st
import requests
from datetime import datetime
import re

api_key = st.secrets["API_KEY"]

# ----------------------------
# 알레르기 코드 매핑
# ----------------------------
ALLERGY_MAP = {
    "1": "달걀", "2": "우유", "3": "밀", "4": "메밀", "5": "땅콩",
    "6": "대두", "7": "호두", "8": "닭고기", "9": "쇠고기",
    "10": "돼지고기", "11": "복숭아", "12": "토마토",
    "13": "아황산류", "14": "조개류", "15": "참치",
    "16": "고등어", "17": "게", "18": "새우", "19": "오징어", "20": "조개류"
}

# ----------------------------
# NEIS API 호출 함수
# ----------------------------
@st.cache_data(ttl=60)
def get_schools(region_code, school_level):
    try:
        url = (
            f"https://open.neis.go.kr/hub/schoolInfo"
            f"?KEY={api_key}&Type=json&pIndex=1&pSize=1000"
            f"&ATPT_OFCDC_SC_CODE={region_code}"
            f"&SD_SCHUL_SC_CODE={school_level}"
        )
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        schools = []
        if "schoolInfo" in data:
            for item in data["schoolInfo"][1]["row"]:
                schools.append({"name": item["SCHUL_NM"], "code": item["SD_SCHUL_CODE"]})
        return schools
    except Exception as e:
        print("학교 정보 API 호출 오류:", e)
        return []

@st.cache_data(ttl=60)
def get_lunch_menu(office_code, school_code, date_str):
    try:
        url = (
            f"https://open.neis.go.kr/hub/mealServiceDietInfo"
            f"?KEY={api_key}&Type=json&pIndex=1&pSize=100"
            f"&ATPT_OFCDC_SC_CODE={office_code}&SD_SCHUL_CODE={school_code}"
            f"&MLSV_YMD={date_str}"
        )
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        meal_info = data.get("mealServiceDietInfo")
        menus = []
        if meal_info:
            for item in meal_info[1]["row"]:
                menu = item["DDISH_NM"].replace("<br/>", "\n")

                # 숫자 괄호 → 알레르기 이름
                def replace_allergy(match):
                    codes = match.group(1).split(".")
                    names = [ALLERGY_MAP.get(code, code) for code in codes]
                    return f"({' , '.join(names)})"

                menu = re.sub(r"\(([\d.]+)\)", replace_allergy, menu)
                menus.append(menu)
        return menus
    except Exception as e:
        print("급식 API 호출 오류:", e)
        return []

# ----------------------------
# Streamlit UI
# ----------------------------
st.title("전국 학교 급식 정보 🥗")

# ----------------------------
# 사이드바 입력
# ----------------------------
regions = {
    "서울": "B10", "부산": "C10", "대구": "D10", "인천": "I10",
    "광주": "G10", "대전": "E10", "울산": "U10", "세종": "S10",
    "경기": "J10", "강원": "H10", "충북": "K10", "충남": "M10",
    "전북": "F10", "전남": "N10", "경북": "O10", "경남": "P10", "제주": "Q10"
}
region_name = st.sidebar.selectbox("지역 선택", list(regions.keys()))
region_code = regions[region_name]

school_levels = {"초등학교": "E", "중학교": "M", "고등학교": "H"}
school_level_name = st.sidebar.selectbox("학교급 선택", list(school_levels.keys()))
school_level_code = school_levels[school_level_name]

school_name = st.sidebar.text_input(
    "학교 이름 입력", 
    value="", 
    help="예: 강남초등학교 / 서초중학교 / 성북고등학교"
)
selected_date = st.sidebar.date_input("날짜 선택", value=datetime.today())
date_str = selected_date.strftime("%Y%m%d")

search_button = st.sidebar.button("급식 검색하기")

# ----------------------------
# 투표 초기화
# ----------------------------
if "likes" not in st.session_state:
    st.session_state["likes"] = {}
if "dislikes" not in st.session_state:
    st.session_state["dislikes"] = {}
if "vote_count" not in st.session_state:
    st.session_state["vote_count"] = 0  # 오늘 하루 투표 횟수

# ----------------------------
# 검색 버튼 클릭 시 처리
# ----------------------------
if search_button:
    if not school_name:
        st.warning("학교 이름을 입력해주세요. 예: 강남초등학교")
    else:
        schools = get_schools(region_code, school_level_code)
        school_code = next((s["code"] for s in schools if s["name"] == school_name), None)
        if school_code:
            menus = get_lunch_menu(region_code, school_code, date_str)
            if menus:
                st.subheader(f"{school_name} {selected_date.strftime('%Y년 %m월 %d일')} 급식 메뉴")
                
                for menu in menus:
                    # 메뉴 줄바꿈 유지 + 가독성
                    display_menu = menu.replace("\n", "  \n")
                    st.markdown(f"**{display_menu}**")
                    
                    # 메뉴별 좋아요/나빠요 초기화
                    if menu not in st.session_state["likes"]:
                        st.session_state["likes"][menu] = 0
                    if menu not in st.session_state["dislikes"]:
                        st.session_state["dislikes"][menu] = 0
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"👍 좋아요", key=f"like_{menu}"):
                            if st.session_state["vote_count"] < 5:
                                st.session_state["likes"][menu] += 1
                                st.session_state["vote_count"] += 1
                            else:
                                st.warning("오늘 투표는 5번까지 가능합니다!")
                    with col2:
                        if st.button(f"👎 나빠요", key=f"dislike_{menu}"):
                            if st.session_state["vote_count"] < 5:
                                st.session_state["dislikes"][menu] += 1
                                st.session_state["vote_count"] += 1
                            else:
                                st.warning("오늘 투표는 5번까지 가능합니다!")
                    
                    st.text(f"좋아요: {st.session_state['likes'][menu]} | 나빠요: {st.session_state['dislikes'][menu]}")
                    st.markdown("---")  # 메뉴별 구분선
                
                st.info(f"오늘 남은 투표 가능 횟수: {5 - st.session_state['vote_count']}")
            else:
                st.warning("급식 정보가 없습니다.")
        else:
            st.error("학교 정보를 찾을 수 없습니다. 지역과 학교명을 다시 확인해주세요.")
