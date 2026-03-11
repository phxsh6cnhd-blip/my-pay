import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# 1. 페이지 설정 및 디자인 CSS
st.set_page_config(page_title="알바 매니저 Pro", page_icon="💰", layout="wide")

# 버튼 색상 및 UI 디자인 커스텀
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; font-weight: bold; }
    /* 출근 버튼 (초록계열) */
    div.stButton > button:first-child { background-color: #2ecc71; color: white; border: none; }
    /* 퇴근 버튼 (빨간계열) */
    .off-button > div > div > button { background-color: #e74c3c !important; color: white !important; }
    .earn-box { background-color: #f0f2f6; padding: 20px; border-radius: 15px; text-align: center; border-left: 5px solid #2ecc71; }
    </style>
    """, unsafe_allow_stdio=True)

# 시급 설정 (1.5만원)
HOURLY_WAGE = 15000 
TEMP_FILE = "temp_work_v15.csv"

if not os.path.exists(TEMP_FILE):
    pd.DataFrame(columns=["날짜", "출근시간"]).to_csv(TEMP_FILE, index=False)

# 현재 출근 상태 확인
temp_df = pd.read_csv(TEMP_FILE)
is_working = not temp_df.empty

# --- 메인 화면 ---
st.title("💸 실시간 수익 대시보드")

if is_working:
    # 1. 실시간 수익 계산
    start_time_str = temp_df.iloc[-1]["출근시간"]
    start_dt = datetime.strptime(f"{datetime.now().date()} {start_time_str}", "%Y-%m-%d %H:%M")
    
    now = datetime.now()
    elapsed = now - start_dt
    # 일한 시간 (소수점 첫째자리까지)
    worked_hours = elapsed.total_seconds() / 3600
    current_money = int(worked_hours * HOURLY_WAGE)

    # 대시보드 레이아웃
    st.markdown(f"""
        <div class="earn-box">
            <p style="margin-bottom:0px; font-size:1.2em;">오늘 현재까지 벌고 있는 돈</p>
            <h1 style="color:#2ecc71; font-size:3.5em; margin-top:0px;">{current_money:,} 원</h1>
            <p style="color:#666;">⏱ {start_time_str} 출근 | {worked_hours:.1f}시간째 근무 중</p>
        </div>
    """, unsafe_allow_stdio=True)
    
    st.write("")
    # 수익 그래프 시각화 (목표금액 15만원 기준)
    progress_val = min(current_money / 150000, 1.0)
    st.progress(progress_val)
    st.caption(f"오늘의 목표 달성률: {int(progress_val * 100)}%")

    st.markdown("---")
    
    # 2. 퇴근하기 섹션
    st.subheader("🏁 퇴근 처리")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        off_h = st.selectbox("시간", range(0, 24), index=now.hour)
    with col_t2:
        off_m = st.selectbox("분", [0, 30], index=0 if now.minute < 30 else 1)
    
    st.write("")
    # 퇴근 버튼은 빨간색 스타일 적용
    st.markdown('<div class="off-button">', unsafe_allow_stdio=True)
    if st.button("🚨 퇴근하고 기록 저장"):
        # (여기에 최종 저장 로직을 넣으면 됨)
        os.remove(TEMP_FILE)
        st.success("고생하셨습니다! 퇴근 기록이 완료되었습니다.")
        st.balloons()
        st.rerun()
    st.markdown('</div>', unsafe_allow_stdio=True)

else:
    # 3. 출근하기 섹션
    st.subheader("📅 오늘 근무 시작")
    c1, c2 = st.columns(2)
    
    with c1:
        if st.button("🚀 20:00 정시 출근"):
            new_row = pd.DataFrame([[datetime.now().date(), "20:00"]], columns=["날짜", "출근시간"])
            new_row.to_csv(TEMP_FILE, index=False)
            st.rerun()
            
    with c2:
        with st.popover("➕ 정시 외 출근"):
            h = st.number_input("시", 0, 23, 19)
            m = st.number_input("분", 0, 59, 0)
            if st.button("입력 시간으로 출근"):
                new_row = pd.DataFrame([[datetime.now().date(), f"{h:02d}:{m:02d}"]], columns=["날짜", "출근시간"])
                new_row.to_csv(TEMP_FILE, index=False)
                st.rerun()
    
    st.info("현재 대기 중... 출근 버튼을 누르면 수익 카운팅이 시작됩니다.")

# 과거 기록이나 주급 정산소 메뉴는 사이드바에 유지
with st.sidebar:
    st.markdown("### ⚙️ 설정")
    st.write(f"현재 시급: **{HOURLY_WAGE:,}원**")
    if st.button("🧹 기록 초기화"):
        if os.path.exists(TEMP_FILE): os.remove(TEMP_FILE)
        st.rerun()
