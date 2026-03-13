import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from streamlit_autorefresh import st_autorefresh

# 1. 페이지 설정
st.set_page_config(page_title="알바 매니저 Pro", page_icon="💰", layout="wide")

# CSS: 디자인 가이드
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

TEMP_FILE = "temp_work_data.csv"
DATA_FILE = "work_history_database.csv"
HOURLY_WAGE = 15000

# 파일 초기화 함수
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
    # [부활] 데이터 강제 리셋 버튼
    if st.button("🧹 데이터 강제 리셋 (전체삭제)"):
        if os.path.exists(TEMP_FILE): os.remove(TEMP_FILE)
        if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
        st.cache_resource.clear()
        st.rerun()
    
    # [유지] 백업 버튼
    if os.path.exists(DATA_FILE):
        df_bak = pd.read_csv(DATA_FILE)
        csv_data = df_bak.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 내역 백업(CSV)", csv_data, f"pay_backup_{get_now().strftime('%m%d')}.csv", "text/csv")

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
        
        # 24시간 제한 로직
        diff_sec = max(0, min((now - start_dt).total_seconds(), 86400))
        current_money = int((diff_sec / 3600) * HOURLY_WAGE)
        worked_hours_display = diff_sec / 3600

        st.markdown(f"""<div class="earn-box">
            <p style="color:#555; font-size:1.1em;">💰 {calc_date} {calc_time} 출근 기준</p>
            <h1 style="color:#27ae60; font-size:3.5em; margin:10px 0;">{current_money:,} 원</h1>
            <p style="color:#888;">{f"🔥 실시간 근무 현황" if start_dt.date() == now.date() else "📅 과거 기록 모드"}</p>
        </div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("🏁 퇴근 및 정산")
        time_options = [f"{h:02d}:{m}" for h in range(24) for m in ["00", "30"]]
        sel_off_time = st.selectbox("퇴근 시간 선택", time_options, index=0)
        tip = st.select_slider("오늘 받은 tip", options=[i for i in range(0, 100001, 10000)], value=0)
        memo = st.text_input("메모", placeholder="특이사항 입력")

        if st.button("🚨 기록 저장 및 퇴근하기"):
            h_val, m_val = map(int, sel_off_time.split(":"))
            off_dt = start_dt.replace(hour=h_val, minute=m_val)
            if off_dt <= start_dt: off_dt += timedelta(days=1)
            
            f_hours = round((off_dt - start_dt).total_seconds() / 3600, 1)
            f_wage = int(f_hours * HOURLY_WAGE)
            
            new_rec = pd.DataFrame([[start_dt.strftime("%m/%d"), f_hours, f_wage, tip, (f_wage+tip), memo]], 
                                   columns=["날짜", "근무시간_h", "급여_원", "Tip_원", "합계_원", "메모"])
            
            main_df = pd.read_csv(DATA_FILE)
            pd.concat([main_df, new_rec], ignore_index=True).to_csv(DATA_FILE, index=False)
            if os.path.exists(TEMP_FILE): os.remove(TEMP_FILE)
            st.session_state.menu_index = 1
            st.rerun()
    else:
        st.subheader("📅 근무 시작")
        sel_date = st.date_input("근무 날짜", value=get_now().date())
        st.markdown('<div class="big-start-btn">', unsafe_allow_html=True)
        if st.button(f"🚀 {sel_date.strftime('%m/%d')} 20:00 정시 출근 등록", type="primary"):
            pd.DataFrame([[sel_date, "20:00"]], columns=["날짜", "출근시간"]).to_csv(TEMP_FILE, index=False)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 2. 주급 정산소 ---
elif menu == "🧾 주급 정산소":
    st.title("🧾 주급 정산소")
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        if df.empty:
            st.warning("저장된 내역이 없습니다.")
        else:
            # 1. 상단 요약
            total_rev = df['합계_원'].sum()
            total_hrs = df['근무시간_h'].sum()
            c1, c2 = st.columns(2)
            c1.metric("💰 이번 주 총 수익", f"{total_rev:,} 원")
            c2.metric("⏱️ 총 근무 시간", f"{total_hrs:.1f} 시간")
            st.write("---")

            # 2. 상세 리스트 (이 부분 절대 누락 안 함!)
            st.subheader("🗓️ 상세 근무 기록")
            for i, row in df.sort_index(ascending=False).iterrows():
                with st.expander(f"📅 {row['날짜']} | {row['근무시간_h']}h | {row['합계_원']:,}원"):
                    with st.form(f"edit_form_{i}"):
                        u_h = st.number_input("시간 수정", value=float(row['근무시간_h']), step=0.1, max_value=24.0)
                        u_t = st.number_input("Tip 수정", value=int(row['Tip_원']), step=1000)
                        u_m = st.text_input("메모", value=str(row['메모']) if pd.notna(row['메모']) else "")
                        if st.form_submit_button("💾 수정 저장"):
                            df.at[i, '근무시간_h'] = u_h
                            df.at[i, '급여_원'] = int(u_h * HOURLY_WAGE)
                            df.at[i, 'Tip_원'] = u_t
                            df.at[i, '합계_원'] = int(u_h * HOURLY_WAGE) + u_t
                            df.at[i, '메모'] = u_m
                            df.to_csv(DATA_FILE, index=False)
                            st.rerun()
                    if st.button(f"🗑️ 삭제", key=f"del_btn_{i}"):
                        df.drop(i).reset_index(drop=True).to_csv(DATA_FILE, index=False)
                        st.rerun()
