import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="알바 매니저 Pro", page_icon="💰", layout="wide")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { background-color: #27ae60 !important; color: white !important; }
    .off-section button { background-color: #c0392b !important; color: white !important; }
    .earn-box { background-color: #ffffff; padding: 25px; border-radius: 20px; text-align: center; border: 2px solid #27ae60; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .time-btn button { height: 2.5em !important; background-color: #f0f2f6 !important; color: black !important; border: 1px solid #ddd !important; }
    </style>
    """, unsafe_allow_html=True)

# 한국 시간 보정
def get_now():
    return datetime.utcnow() + timedelta(hours=9)

# 파일 설정
TEMP_FILE = "temp_work_v23.csv"
DATA_FILE = "work_log_final_v3.csv"

for f, cols in [(TEMP_FILE, ["날짜", "출근시간"]), (DATA_FILE, ["날짜", "근무시간_h", "급여_원", "Tip_원", "합계_원", "메모"])]:
    if not os.path.exists(f): pd.DataFrame(columns=cols).to_csv(f, index=False)

if 'menu_index' not in st.session_state: st.session_state.menu_index = 0
if 'off_h' not in st.session_state: st.session_state.off_h = get_now().hour
if 'off_m' not in st.session_state: st.session_state.off_m = 0 if get_now().minute < 30 else 30

# --- 사이드바 ---
with st.sidebar:
    st.title("📂 메뉴")
    menu = st.radio("이동", ["🚀 실시간 대시보드", "🧾 주급 정산소"], index=st.session_state.menu_index)
    st.session_state.menu_index = ["🚀 실시간 대시보드", "🧾 주급 정산소"].index(menu)
    st.write(f"시급: **15,000원**")
    if st.button("🧹 데이터 강제 리셋"):
        if os.path.exists(TEMP_FILE): os.remove(TEMP_FILE)
        st.rerun()

# --- 1. 실시간 대시보드 ---
if menu == "🚀 실시간 대시보드":
    st.title("💸 실시간 수익 대시보드")
    temp_df = pd.read_csv(TEMP_FILE)
    
    if not temp_df.empty:
        calc_time = str(temp_df.iloc[-1]["출근시간"])
        now = get_now()
        start_dt = datetime.strptime(f"{now.date()} {calc_time}", "%Y-%m-%d %H:%M")
        if now < start_dt - timedelta(hours=6): start_dt -= timedelta(days=1)
        
        # 실시간 계산
        is_future = now < start_dt
        worked_hours = 0.0 if is_future else (now - start_dt).total_seconds() / 3600
        current_money = int(worked_hours * 15000)
        
        st.markdown(f"""<div class="earn-box">
            <p style="color:#555;">💰 {calc_time} 출근 기준</p>
            <h1 style="color:#27ae60; font-size:3.2em; margin:0;">{current_money:,} 원</h1>
            <p style="color:#888;">{"⏳ 대기 중" if is_future else f"🔥 {worked_hours:.1f}시간째 근무 중"}</p>
        </div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("🏁 퇴근 시간 선택 (버튼으로 조절)")
        
        # 시간 선택 버튼 UI
        col_h1, col_h2, col_h3 = st.columns([1, 2, 1])
        with col_h1: 
            if st.button("➖ 시", key="h_minus"): st.session_state.off_h = (st.session_state.off_h - 1) % 24
        with col_h2: st.markdown(f"<h2 style='text-align:center;'>{st.session_state.off_h:02d} 시</h2>", unsafe_allow_html=True)
        with col_h3:
            if st.button("➕ 시", key="h_plus"): st.session_state.off_h = (st.session_state.off_h + 1) % 24
            
        col_m1, col_m2, col_m3 = st.columns([1, 2, 1])
        with col_m1:
            if st.button("00분"): st.session_state.off_m = 0
        with col_m2: st.markdown(f"<h2 style='text-align:center;'>{st.session_state.off_m:02d} 분</h2>", unsafe_allow_html=True)
        with col_m3:
            if st.button("30분"): st.session_state.off_m = 30

        tip = st.select_slider("오늘 받은 tip (원)", options=[i for i in range(0, 100001, 10000)], value=0)
        memo = st.text_input("메모 (선택사항)", placeholder="특이사항 입력")

        st.markdown('<div class="off-section">', unsafe_allow_html=True)
        if st.button("🚨 퇴근하고 기록 저장"):
            off_dt = now.replace(hour=st.session_state.off_h, minute=st.session_state.off_m, second=0, microsecond=0)
            if off_dt <= start_dt: off_dt += timedelta(days=1)
            f_hours = round((off_dt - start_dt).total_seconds() / 3600, 1)
            f_wage = int(f_hours * 15000)
            
            new_rec = pd.DataFrame([[now.strftime("%m/%d"), f_hours, f_wage, tip, (f_wage+tip), memo]], 
                                   columns=["날짜", "근무시간_h", "급여_원", "Tip_원", "합계_원", "메모"])
            pd.concat([pd.read_csv(DATA_FILE), new_rec], ignore_index=True).to_csv(DATA_FILE, index=False)
            os.remove(TEMP_FILE)
            st.session_state.menu_index = 1
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.subheader("📅 오늘 근무 시작")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🚀 20:00 정시 출근"):
                pd.DataFrame([[get_now().date(), "20:00"]], columns=["날짜", "출근시간"]).to_csv(TEMP_FILE, index=False)
                st.rerun()
        with c2:
            with st.popover("➕ 정시 외 출근"):
                h = st.number_input("시", 0, 23, 19); m = st.number_input("분", 0, 59, 0)
                if st.button("입력 시간 출근"):
                    pd.DataFrame([[get_now().date(), f"{h:02d}:{m:02d}"]], columns=["날짜", "출근시간"]).to_csv(TEMP_FILE, index=False)
                    st.rerun()

# --- 2. 주급 정산소 ---
elif menu == "🧾 주급 정산소":
    st.title("🧾 주급 정산소")
    df = pd.read_csv(DATA_FILE)
    if df.empty: st.warning("기록이 없습니다.")
    else:
        for i, row in df.iterrows():
            with st.expander(f"📅 {row['날짜']} | {row['근무시간_h']}h | {row['합계_원']:,}원"):
                with st.form(f"edit_{i}"):
                    new_h = st.number_input("근무 시간 수정 (h)", value=float(row['근무시간_h']), step=0.5)
                    new_tip = st.number_input("Tip 수정 (원)", value=int(row['Tip_원']), step=5000)
                    new_memo = st.text_input("메모 수정", value=str(row['메모']) if pd.notna(row['메모']) else "")
                    if st.form_submit_button("💾 수정 내용 저장"):
                        df.at[i, '근무시간_h'] = new_h
                        df.at[i, '급여_원'] = int(new_h * 15000)
                        df.at[i, 'Tip_원'] = new_tip
                        df.at[i, '합계_원'] = int(new_h * 15000) + new_tip
                        df.at[i, '메모'] = new_memo
                        df.to_csv(DATA_FILE, index=False)
                        st.rerun()
                if st.button(f"🗑️ 이 기록 삭제", key=f"del_{i}"):
                    df.drop(i).to_csv(DATA_FILE, index=False)
                    st.rerun()
        
        st.markdown(f"""<div style="background-color:#f8f9fa; padding:20px; border-radius:15px; border:1px solid #dee2e6; margin-top:20px;">
            <h3>📊 이번 주 누적: {df['합계_원'].sum():,}원</h3>
            <p>총 {df['근무시간_h'].sum():.1f}시간 근무</p>
        </div>""", unsafe_allow_html=True)
        if st.button("🗑️ 전체 데이터 초기화"):
            pd.DataFrame(columns=df.columns).to_csv(DATA_FILE, index=False)
            st.rerun()
