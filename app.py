import streamlit as st
import pandas as pd
from datetime import datetime
import os

# 1. 페이지 설정
st.set_page_config(page_title="알바 매니저 Pro", page_icon="💰", layout="wide")

# UI 디자인 커스텀
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold; }
    /* 출근 버튼 - 초록 */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { background-color: #27ae60 !important; color: white !important; }
    /* 퇴근 버튼 - 빨강 */
    .off-section button { background-color: #c0392b !important; color: white !important; }
    .earn-box { background-color: #ffffff; padding: 25px; border-radius: 20px; text-align: center; border: 2px solid #27ae60; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 설정 및 파일 경로
HOURLY_WAGE = 15000 
TEMP_FILE = "temp_work_v17.csv"
DATA_FILE = "work_log_final.csv"

# 파일 초기화
if not os.path.exists(TEMP_FILE):
    pd.DataFrame(columns=["날짜", "출근시간"]).to_csv(TEMP_FILE, index=False)
if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=["정산날짜", "총일한시간", "출근일수", "상세날짜", "tip합계", "최종정산금"]).to_csv(DATA_FILE, index=False)

# --- 사이드바 메뉴 ---
with st.sidebar:
    st.title("📂 메뉴")
    menu = st.radio("이동할 화면을 선택하세요", ["🚀 실시간 대시보드", "🧾 주급 정산소"])
    st.markdown("---")
    st.write(f"현재 시급: **{HOURLY_WAGE:,}원**")
    if st.button("🧹 데이터 강제 리셋"):
        if os.path.exists(TEMP_FILE): os.remove(TEMP_FILE)
        st.rerun()

# --- 1. 실시간 대시보드 화면 ---
if menu == "🚀 실시간 대시보드":
    st.title("💸 실시간 수익 대시보드")
    
    temp_df = pd.read_csv(TEMP_FILE)
    is_working = not temp_df.empty

    if is_working:
        try:
            start_time_str = str(temp_df.iloc[-1]["출근시간"])
            start_dt = datetime.strptime(f"{datetime.now().date()} {start_time_str}", "%Y-%m-%d %H:%M")
            now = datetime.now()
            elapsed = now - start_dt
            worked_hours = max(elapsed.total_seconds() / 3600, 0)
            current_money = int(worked_hours * HOURLY_WAGE)

            st.markdown(f"""
                <div class="earn-box">
                    <p style="margin-bottom:5px; color:#555;">지금까지 벌고 있는 돈</p>
                    <h1 style="color:#27ae60; font-size:3.2em; margin:0;">{current_money:,} 원</h1>
                    <p style="color:#888; margin-top:10px;">⏱ {start_time_str} 출근 | {worked_hours:.1f}시간째 근무 중</p>
                </div>
            """, unsafe_allow_html=True)
            st.write("")
            st.progress(min(current_money / 150000, 1.0))

            st.markdown("---")
            st.subheader("🏁 퇴근 및 기록")
            c1, c2 = st.columns(2)
            with c1: off_h = st.selectbox("퇴근 시", range(0, 24), index=now.hour)
            with c2: off_min = st.selectbox("퇴근 분", [0, 30], index=0 if now.minute < 30 else 1)
            tip_val = st.select_slider("오늘 받은 tip (원)", options=[i for i in range(0, 100001, 10000)], value=0)

            st.markdown('<div class="off-section">', unsafe_allow_html=True)
            if st.button("🚨 퇴근하고 기록 저장"):
                os.remove(TEMP_FILE)
                st.success("퇴근 완료! 고생하셨습니다.")
                st.balloons()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True) # <- 여기서 오타 수정됨!

        except:
            st.error("데이터 형식 에러! 사이드바에서 리셋을 눌러주세요.")

    else:
        st.subheader("📅 오늘 근무 시작")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 20:00 정시 출근"):
                pd.DataFrame([[datetime.now().date(), "20:00"]], columns=["날짜", "출근시간"]).to_csv(TEMP_FILE, index=False)
                st.rerun()
        with col2:
            with st.popover("➕ 정시 외 출근"):
                h = st.number_input("시", 0, 23, 19); m = st.number_input("분", 0, 59, 0)
                if st.button("입력 시간 출근"):
                    pd.DataFrame([[datetime.now().date(), f"{h:02d}:{m:02d}"]], columns=["날짜", "출근시간"]).to_csv(TEMP_FILE, index=False)
                    st.rerun()
        st.info("출근 버튼을 누르면 수익 카운팅이 시작됩니다.")

# --- 2. 주급 정산소 화면 ---
elif menu == "🧾 주급 정산소":
    st.title("🧾 주급 정산소")
    data_df = pd.read_csv(DATA_FILE)
    if data_df.empty:
        st.warning("아직 저장된 정산 기록이 없습니다.")
    else:
        st.dataframe(data_df, use_container_width=True)
    
    if st.button("🗑️ 모든 기록 삭제"):
        pd.DataFrame(columns=["정산날짜", "총일한시간", "출근일수", "상세날짜", "tip합계", "최종정산금"]).to_csv(DATA_FILE, index=False)
        st.rerun()
