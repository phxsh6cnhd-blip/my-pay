import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# 1. 페이지 설정
st.set_page_config(page_title="알바 매니저 Pro", page_icon="💰", layout="wide")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { background-color: #27ae60 !important; color: white !important; }
    .off-section button { background-color: #c0392b !important; color: white !important; }
    .earn-box { background-color: #ffffff; padding: 25px; border-radius: 20px; text-align: center; border: 2px solid #27ae60; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 설정
HOURLY_WAGE = 15000 
TEMP_FILE = "temp_work_v21.csv"
DATA_FILE = "work_log_final_v2.csv"

# 파일 초기화
if not os.path.exists(TEMP_FILE):
    pd.DataFrame(columns=["날짜", "출근시간"]).to_csv(TEMP_FILE, index=False)
if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=["날짜", "근무시간_h", "급여_원", "Tip_원", "합계_원"]).to_csv(DATA_FILE, index=False)

# 세션 상태로 메뉴 관리
if 'menu_index' not in st.session_state:
    st.session_state.menu_index = 0

# --- 사이드바 메뉴 ---
with st.sidebar:
    st.title("📂 메뉴")
    menu_options = ["🚀 실시간 대시보드", "🧾 주급 정산소"]
    menu = st.radio("이동", menu_options, index=st.session_state.menu_index)
    st.session_state.menu_index = menu_options.index(menu)
    
    st.write(f"현재 시급: **{HOURLY_WAGE:,}원**")
    if st.button("🧹 데이터 강제 리셋"):
        if os.path.exists(TEMP_FILE): os.remove(TEMP_FILE)
        st.rerun()

# --- 1. 실시간 대시보드 ---
if menu == "🚀 실시간 대시보드":
    st.title("💸 실시간 수익 대시보드")
    temp_df = pd.read_csv(TEMP_FILE)
    is_working = not temp_df.empty

    if is_working:
        calc_time = str(temp_df.iloc[-1]["출근시간"])
        now = datetime.now()
        start_dt = datetime.strptime(f"{now.date()} {calc_time}", "%Y-%m-%d %H:%M")
        
        # 새벽 근무 보정 (현재 새벽인데 출근은 밤 20시 등일 때)
        if now < start_dt - timedelta(hours=6): 
            start_dt -= timedelta(days=1)
            
        # --- 시간 계산 로직 (중요!) ---
        if now < start_dt:
            # 아직 출근 시간 전인 경우
            worked_hours = 0.0
            current_money = 0
            status_msg = f"⏳ {calc_time} 근무 시작 대기 중"
        else:
            # 출근 시간 이후인 경우
            elapsed = now - start_dt
            worked_hours = elapsed.total_seconds() / 3600
            current_money = int(worked_hours * HOURLY_WAGE)
            status_msg = f"🔥 현재 {worked_hours:.1f}시간째 근무 중"

        st.markdown(f"""
            <div class="earn-box">
                <p style="margin-bottom:5px; color:#555;">💰 {calc_time} 출근 기준</p>
                <h1 style="color:#27ae60; font-size:3.2em; margin:0;">{current_money:,} 원</h1>
                <p style="color:#888; margin-top:10px;">{status_msg}</p>
            </div>
        """, unsafe_allow_html=True)
        st.write("")
        st.progress(min(current_money / 150000, 1.0))

        st.markdown("---")
        st.subheader("🏁 퇴근 기록")
        c1, c2 = st.columns(2)
        with c1: off_h = st.selectbox("퇴근 시", range(0, 24), index=now.hour)
        with c2: off_min = st.selectbox("퇴근 분", [0, 30], index=0 if now.minute < 30 else 1)
        tip_val = st.select_slider("오늘 받은 tip (원)", options=[i for i in range(0, 100001, 10000)], value=0)

        st.markdown('<div class="off-section">', unsafe_allow_html=True)
        if st.button("🚨 퇴근하고 주급 정산소로 저장"):
            off_dt = now.replace(hour=off_h, minute=off_min, second=0, microsecond=0)
            if off_dt <= start_dt: off_dt += timedelta(days=1)
            
            final_hours = round((off_dt - start_dt).total_seconds() / 3600, 1)
            final_wage = int(final_hours * HOURLY_WAGE)
            
            new_record = pd.DataFrame([[
                now.strftime("%m/%d"), 
                final_hours, final_wage, tip_val, (final_wage + tip_val)
            ]], columns=["날짜", "근무시간_h", "급여_원", "Tip_원", "합계_원"])
            
            data_df = pd.read_csv(DATA_FILE)
            pd.concat([data_df, new_record], ignore_index=True).to_csv(DATA_FILE, index=False)
            
            os.remove(TEMP_FILE)
            st.session_state.menu_index = 1
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

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
                input_time = f"{h:02d}:{m:02d}"
                if st.button("입력 시간 출근"):
                    pd.DataFrame([[datetime.now().date(), input_time]], columns=["날짜", "출근시간"]).to_csv(TEMP_FILE, index=False)
                    st.rerun()
        st.info("20:00 이전 언제든 버튼을 눌러도 급여는 20:00부터 계산됩니다.")

# --- 2. 주급 정산소 ---
elif menu == "🧾 주급 정산소":
    st.title("🧾 주급 정산소")
    data_df = pd.read_csv(DATA_FILE)
    if data_df.empty:
        st.warning("아직 저장된 정산 기록이 없습니다.")
    else:
        total_h = data_df["근무시간_h"].sum()
        total_all = data_df["합계_원"].sum()
        
        st.table(data_df)
        st.markdown(f"""
            <div style="background-color:#f8f9fa; padding:20px; border-radius:15px; border:1px solid #dee2e6;">
                <h3 style="margin-top:0;">📊 이번 주 누적 합계</h3>
                <p style="font-size:1.1em;">총 근무: <b>{total_h:.1f}시간</b></p>
                <h2 style="color:#27ae60; margin-top:10px;">총 예상 수령액: {total_all:,}원</h2>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        if st.button("🗑️ 전체 기록 삭제"):
            pd.DataFrame(columns=["날짜", "근무시간_h", "급여_원", "Tip_원", "합계_원"]).to_csv(DATA_FILE, index=False)
            st.rerun()
