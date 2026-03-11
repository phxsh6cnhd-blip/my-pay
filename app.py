import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# 1. 페이지 설정
st.set_page_config(page_title="알바 매니저 Pro", page_icon="💰", layout="wide")

# CSS: 아이폰에서도 무조건 가로 4열로 정렬되게 강제함
st.markdown("""
    <style>
    /* 버튼 컨테이너를 가로로 배치 */
    [data-testid="column"] {
        min-width: 20% !important; /* 한 줄에 최대 4~5개가 들어가도록 너비 제한 */
        flex: 1 1 20% !important;
    }
    .stButton>button { 
        width: 100%; 
        border-radius: 10px; 
        height: 3.2em; 
        font-weight: bold; 
        background-color: white !important; 
        color: #333 !important; 
        border: 1px solid #ddd !important;
        font-size: 0.9em !important;
        padding: 0px !important;
    }
    /* 메인 버튼 스타일 */
    .main-btn button { background-color: #27ae60 !important; color: white !important; border: none !important; }
    .off-btn button { background-color: #c0392b !important; color: white !important; border: none !important; }
    
    .earn-box { background-color: #ffffff; padding: 20px; border-radius: 20px; text-align: center; border: 2px solid #27ae60; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .selected-time { background-color: #e8f5e9; padding: 10px; border-radius: 10px; text-align: center; border: 2px solid #27ae60; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

def get_now():
    return datetime.utcnow() + timedelta(hours=9)

TEMP_FILE = "temp_work_v28.csv"
DATA_FILE = "work_log_final_v3.csv"

for f, cols in [(TEMP_FILE, ["날짜", "출근시간"]),
