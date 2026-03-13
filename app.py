import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from streamlit_autorefresh import st_autorefresh

# 1. 페이지 설정
st.set_page_config(page_title="알바 매니저 Pro", page_icon="💰", layout="wide")

# CSS 유지
st.markdown("""
    <style>
    .big-start-btn .stButton > button { height: 5em !important; font-size: 1.5em !important; font-weight: bold !important; border-radius: 20px !important; width: 100%; }
    .earn-box { background-color: #ffffff; padding: 25px; border-radius: 20px; text-align: center; border: 2px solid #27ae60; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }
    .off-save-btn .stButton > button { background-color: #c0392b !important; color: white !important; height: 4em !important; font-weight: bold !important; width: 100%; font-size: 1.2em !important; }
    </style>
    """, unsafe_allow_html=True)

def get_now():
    return datetime.utcnow() + timedelta(hours=9)

TEMP_FILE = "temp_work_data.csv"
DATA_FILE = "work_history_database.csv"
HOURLY_WAGE = 15000

# 파일 초기화
if not os.path.exists(TEMP_FILE): pd.DataFrame(columns=["날짜", "출근시간"]).to_csv(TEMP_FILE, index=False)
if not os.path.exists(DATA_FILE): pd.DataFrame(columns=["날짜", "근무시간_h", "급여_원", "Tip_원", "합계_원", "메모"]).to_csv(DATA_FILE, index=False)

if 'menu_index' not in st.session_state: st.session_state.menu_index = 0

# --- 사이드바 ---
with st.sidebar:
    st.title("📂 메뉴")
    menu = st.radio("이동", ["🚀 실시간 대시보드", "🧾 주급 정산소"], index=st.session_state.menu_index)
    st.session_state.menu_index = ["🚀 실시간 대시보드", "🧾 주급 정산소"].index(menu)

# --- 1. 실시간 대시보드 ---
if menu == "🚀 실시간 대시보드":
    st.title("💸 수익 대시보드")
    temp_df = pd.read_csv(TEMP_FILE)
    
    if not temp_df.empty:
        st_autorefresh(interval=1000, key="earn_refresh")
        calc_date = str(temp_df.iloc[-1]["날짜"])
        calc_time = str(temp_df.iloc[-1]["출근시간"])
        now = get_now()
        start_dt = datetime.strptime(f"{calc_date} {calc_time}", "%Y-%m-%d %H:%M")
        
        diff_seconds = (now - start_dt).total_seconds()
        
        # [수정] 근무 시간이 24시간을 초과하지 않도록 제한
        if diff_seconds > 86400: diff_seconds = 86400
        elif diff_seconds < 0: diff_seconds = 0 # 미래 시간 설정 방지
        
        current_money = int((diff_seconds / 3600) * HOURLY_WAGE)
        worked_hours = diff_seconds / 3600

        st.markdown(f"""<div class="earn-box">
            <p style="color:#555; font-size:1.1em;">💰 {calc_date} {calc_time} 출근 기준</p>
            <h1 style="color:#27ae60; font-size:3.5em; margin:10px 0;">{current_money:,} 원</h1>
            <p style="color:#888;">{f"🔥 {worked_hours:.4f}시간째 근무 중 (최대 24h)"}</p>
        </div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("🏁 퇴근 및 정산")
        # 퇴근 시간 선택 (야간 근무 대응)
        time_options = [f"{h:02d}:{m}" for h in range(24) for m in ["00", "30"]]
        sel_off_time = st.selectbox("퇴근 시간 선택", time_options, index=0)
        tip = st.select_slider("오늘 받은 tip", options=[i for i in range(0, 100001, 10000)], value=0)
        
        if st.button("🚨 퇴근하고 기록 저장"):
            h_val, m_val = map(int, sel_off_time.split(":"))
            off_dt = start_dt.replace(hour=h_val, minute=m_val)
            
            # [핵심] 퇴근 시간이 출근보다 작으면 자동으로 '다음날'로 인식
            if off_dt <= start_dt:
                off_dt += timedelta(days=1)
            
            f_hours = (off_dt - start_dt).total_seconds() / 3600
            if f_hours > 24: f_hours = 24 # 최대 24시간 제한
            
            f_wage = int(f_hours * HOURLY_WAGE)
            new_rec = pd.DataFrame([[start_dt.strftime("%m/%d"), round(f_hours, 1), f_wage, tip, (f_wage+tip), ""]], 
                                   columns=["날짜", "근무시간_h", "급여_원", "Tip_원", "합계_원", "메모"])
            
            pd.concat([pd.read_csv(DATA_FILE), new_rec], ignore_index=True).to_csv(DATA_FILE, index=False)
            os.remove(TEMP_FILE)
            st.rerun()
    else:
        # 출근 기록 화면 (생략 - 기존 코드와 동일)
        st.info("출근 전입니다. 날짜와 시간을 선택해 출근 버튼을 눌러주세요.")
        sel_date = st.date_input("근무 날짜", value=get_now().date())
        if st.button("🚀 정시 출근 (20:00)"):
            pd.DataFrame([[sel_date, "20:00"]], columns=["날짜", "출근시간"]).to_csv(TEMP_FILE, index=False)
            st.rerun()

# --- 2. 주급 정산소 ---
elif menu == "🧾 주급 정산소":
    st.title("🧾 주급 정산소")
    df = pd.read_csv(DATA_FILE)
    if not df.empty:
        # 수정 모드에서도 24시간 제한 로직 적용 가능
        for i, row in df.sort_index(ascending=False).iterrows():
            with st.expander(f"📅 {row['날짜']} | {row['근무시간_h']}h | {row['합계_원']:,}원"):
                with st.form(f"edit_{i}"):
                    # [수정] 수정 시에도 최대 24시간까지만 입력 가능하도록 설정
                    new_h = st.number_input("근무 시간 수정 (최대 24)", value=float(row['근무시간_h']), min_value=0.0, max_value=24.0, step=0.5)
                    new_tip = st.number_input("Tip 수정", value=int(row['Tip_원']), step=5000)
                    if st.form_submit_button("💾 저장"):
                        df.at[i, '근무시간_h'] = new_h
                        df.at[i, '급여_원'] = int(new_h * HOURLY_WAGE)
                        df.at[i, 'Tip_원'] = new_tip
                        df.at[i, '합계_원'] = int(new_h * HOURLY_WAGE) + new_tip
                        df.to_csv(DATA_FILE, index=False)
                        st.rerun()
