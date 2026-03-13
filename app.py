import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from streamlit_autorefresh import st_autorefresh

# 1. 페이지 설정
st.set_page_config(page_title="알바 매니저 Pro", page_icon="💰", layout="wide")

# CSS: 디자인 유지
st.markdown("""
    <style>
    .big-start-btn .stButton > button { height: 5em !important; font-size: 1.5em !important; font-weight: bold !important; border-radius: 20px !important; width: 100%; }
    .earn-box { background-color: #ffffff; padding: 25px; border-radius: 20px; text-align: center; border: 2px solid #27ae60; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }
    .off-save-btn .stButton > button { background-color: #c0392b !important; color: white !important; height: 4em !important; font-weight: bold !important; width: 100%; font-size: 1.2em !important; }
    [data-testid="stMetricValue"] { font-size: 1.8em !important; }
    </style>
    """, unsafe_allow_html=True)

def get_now():
    return datetime.utcnow() + timedelta(hours=9)

# 파일 버전 관리 (기존 파일 유지 시 이름 변경 주의)
TEMP_FILE = "temp_work_data.csv"
DATA_FILE = "work_history_database.csv"
HOURLY_WAGE = 15000

# 파일 초기화 함수 (데이터 유실 방지 보강)
def init_files():
    if not os.path.exists(TEMP_FILE):
        pd.DataFrame(columns=["날짜", "출근시간"]).to_csv(TEMP_FILE, index=False)
    if not os.path.exists(DATA_FILE):
        pd.DataFrame(columns=["날짜", "근무시간_h", "급여_원", "Tip_원", "합계_원", "메모"]).to_csv(DATA_FILE, index=False)

init_files()

if 'menu_index' not in st.session_state: st.session_state.menu_index = 0

# --- 사이드바 ---
with st.sidebar:
    st.title("📂 메뉴")
    menu = st.radio("이동", ["🚀 실시간 대시보드", "🧾 주급 정산소"], index=st.session_state.menu_index)
    st.session_state.menu_index = ["🚀 실시간 대시보드", "🧾 주급 정산소"].index(menu)
    
    st.write("---")
    # 백업 버튼 사이드바에도 배치
    if os.path.exists(DATA_FILE):
        df_backup = pd.read_csv(DATA_FILE)
        csv_data = df_backup.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 데이터 전체 백업(CSV)", csv_data, f"work_backup_{get_now().strftime('%m%d')}.csv", "text/csv")

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
        
        worked_seconds = (now - start_dt).total_seconds()
        is_future = now < start_dt
        current_money = 0 if is_future else int((worked_seconds / 3600) * HOURLY_WAGE)
        worked_hours_display = 0.0 if is_future else worked_seconds / 3600

        st.markdown(f"""<div class="earn-box">
            <p style="color:#555; font-size:1.1em;">💰 {calc_date} {calc_time} 출근 기준</p>
            <h1 style="color:#27ae60; font-size:3.5em; margin:10px 0;">{current_money:,} 원</h1>
            <p style="color:#888;">{"⏳ 근무 대기 중" if is_future else f"🔥 {worked_hours_display:.4f}시간째 실시간 근무 중"}</p>
        </div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("🏁 퇴근 및 정산")
        time_options = [f"{h:02d}:{m}" for h in [22, 23, 0, 1, 2, 3, 4, 5, 6] for m in ["00", "30"]]
        current_t_str = now.strftime("%H:%M")
        default_idx = 0
        for i, opt in enumerate(time_options):
            if opt <= current_t_str: default_idx = i

        sel_off_time = st.selectbox("퇴근 시간 선택", time_options, index=default_idx)
        tip = st.select_slider("오늘 받은 tip", options=[i for i in range(0, 100001, 10000)], value=0)
        memo = st.text_input("메모", placeholder="특이사항 입력")

        if st.button("🚨 퇴근하고 기록 저장"):
            h_val, m_val = map(int, sel_off_time.split(":"))
            off_dt = now.replace(hour=h_val, minute=m_val, second=0, microsecond=0)
            if off_dt <= start_dt: off_dt += timedelta(days=1)
            
            f_hours = round((off_dt - start_dt).total_seconds() / 3600, 1)
            f_wage = int(f_hours * HOURLY_WAGE)
            
            new_rec = pd.DataFrame([[start_dt.strftime("%m/%d"), f_hours, f_wage, tip, (f_wage+tip), memo]], 
                                   columns=["날짜", "근무시간_h", "급여_원", "Tip_원", "합계_원", "메모"])
            
            # 저장 전 파일 재로딩 (충돌 방지)
            main_df = pd.read_csv(DATA_FILE)
            pd.concat([main_df, new_rec], ignore_index=True).to_csv(DATA_FILE, index=False)
            
            if os.path.exists(TEMP_FILE): os.remove(TEMP_FILE)
            st.session_state.menu_index = 1
            st.rerun()

    else:
        st.subheader("📅 오늘 근무 시작")
        sel_date = st.date_input("근무 날짜 선택", value=get_now().date())
        if st.button(f"🚀 {sel_date.strftime('%m/%d')} 20:00 정시 출근", type="primary"):
            pd.DataFrame([[sel_date, "20:00"]], columns=["날짜", "출근시간"]).to_csv(TEMP_FILE, index=False)
            st.rerun()
        
        with st.popover("➕ 직접 입력"):
            h = st.number_input("시", 0, 23, 19); m = st.number_input("분", 0, 59, 0)
            if st.button("기록"):
                pd.DataFrame([[sel_date, f"{h:02d}:{m:02d}"]], columns=["날짜", "출근시간"]).to_csv(TEMP_FILE, index=False)
                st.rerun()

# --- 2. 주급 정산소 ---
elif menu == "🧾 주급 정산소":
    st.title("🧾 주급 정산소")
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        if df.empty:
            st.warning("저장된 내역이 없습니다.")
        else:
            total_rev = df['합계_원'].sum()
            total_hrs = df['근무시간_h'].sum()
            
            c1, c2 = st.columns(2)
            c1.metric("💰 총 수익", f"{total_rev:,} 원")
            c2.metric("⏱️ 총 시간", f"{total_hrs:.1f} 시간")
            
            st.write("---")
            for i, row in df.sort_index(ascending=False).iterrows():
                with st.expander(f"📅 {row['날짜']} | {row['근무시간_h']}h | {row['합계_원']:,}원"):
                    # 수정/삭제 로직 유지
                    if st.button(f"🗑️ 삭제", key=f"del_{i}"):
                        df.drop(i).reset_index(drop=True).to_csv(DATA_FILE, index=False)
                        st.rerun()
