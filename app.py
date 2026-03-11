import streamlit as st
import pandas as pd
from datetime import datetime
import os

# 1. 페이지 설정 및 디자인 CSS
st.set_page_config(page_title="알바 매니저 Pro", page_icon="💰", layout="wide")

# 버튼 및 대시보드 커스텀 디자인
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold; font-size: 1.1em; transition: 0.3s; }
    /* 출근 버튼 - 선명한 초록 */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { background-color: #27ae60; color: white; border: none; }
    /* 퇴근 버튼 - 선명한 빨강 */
    .off-section button { background-color: #c0392b !important; color: white !important; border: none; }
    /* 수익 박스 디자인 */
    .earn-box { background-color: #ffffff; padding: 25px; border-radius: 20px; text-align: center; border: 2px solid #27ae60; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_stdio=True)

# 설정값
HOURLY_WAGE = 15000 
TEMP_FILE = "temp_work_v16.csv"

if not os.path.exists(TEMP_FILE):
    pd.DataFrame(columns=["날짜", "출근시간"]).to_csv(TEMP_FILE, index=False)

# 현재 상태 확인
temp_df = pd.read_csv(TEMP_FILE)
is_working = not temp_df.empty

st.title("💸 실시간 수익 대시보드")

if is_working:
    # --- 출근 중인 상태 ---
    try:
        start_time_str = str(temp_df.iloc[-1]["출근시간"])
        # 오늘 날짜와 결합하여 계산용 datetime 생성
        start_dt = datetime.strptime(f"{datetime.now().date()} {start_time_str}", "%Y-%m-%d %H:%M")
        
        now = datetime.now()
        elapsed = now - start_dt
        worked_hours = max(elapsed.total_seconds() / 3600, 0)
        current_money = int(worked_hours * HOURLY_WAGE)

        # 대시보드 표시
        st.markdown(f"""
            <div class="earn-box">
                <p style="margin-bottom:5px; color:#555;">오늘 현재까지 벌고 있는 돈</p>
                <h1 style="color:#27ae60; font-size:3.5em; margin:0;">{current_money:,} 원</h1>
                <p style="color:#888; margin-top:10px;">⏱ {start_time_str} 출근 | {worked_hours:.1f}시간째 근무 중</p>
            </div>
        """, unsafe_allow_stdio=True)
        
        st.write("")
        st.progress(min(current_money / 150000, 1.0))
        st.caption(f"오늘 목표 달성률: {int(min(current_money / 150000, 1.0) * 100)}% (15만원 기준)")
    except Exception as e:
        st.error(f"시간 계산 중 에러 발생: {e}")
        if st.button("기록 리셋"):
            os.remove(TEMP_FILE)
            st.rerun()

    st.markdown("---")
    
    # 퇴근 섹션
    st.subheader("🏁 퇴근 기록")
    c1, c2 = st.columns(2)
    with c1:
        off_h = st.selectbox("시간", range(0, 24), index=now.hour)
    with c2:
        off_min = st.selectbox("분", [0, 30], index=0 if now.minute < 30 else 1)
    
    st.markdown('<div class="off-section">', unsafe_allow_stdio=True)
    if st.button("🚨 퇴근하고 최종 저장"):
        # 여기에 나중에 주급 정산소로 데이터를 넘기는 코드를 추가하면 됨
        os.remove(TEMP_FILE)
        st.success("퇴근 완료! 고생하셨습니다.")
        st.balloons()
        st.rerun()
    st.markdown('</div>', unsafe_allow_stdio=True)

else:
    # --- 출근 전 상태 ---
    st.subheader("📅 오늘 근무 시작")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 20:00 정시 출근"):
            new_row = pd.DataFrame([[datetime.now().date(), "20:00"]], columns=["날짜", "출근시간"])
            new_row.to_csv(TEMP_FILE, index=False)
            st.rerun()
            
    with col2:
        with st.popover("➕ 정시 외 출근"):
            h = st.number_input("시", 0, 23, 19)
            m = st.number_input("분", 0, 59, 0)
            if st.button("입력 시간으로 출근"):
                new_row = pd.DataFrame([[datetime.now().date(), f"{h:02d}:{m:02d}"]], columns=["날짜", "출근시간"])
                new_row.to_csv(TEMP_FILE, index=False)
                st.rerun()
    
    st.info("출근 버튼을 누르면 실시간 수익 카운팅이 시작됩니다.")

# 사이드바
with st.sidebar:
    st.markdown("### ⚙️ 설정")
    st.write(f"현재 시급: **{HOURLY_WAGE:,}원**")
    if st.button("🧹 강제 초기화 (에러 시 클릭)"):
        if os.path.exists(TEMP_FILE): os.remove(TEMP_FILE)
        st.rerun()
