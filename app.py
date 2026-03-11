import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import time

# 1. 페이지 설정
st.set_page_config(page_title="알바 매니저 Pro", page_icon="💰", layout="wide")

# CSS: 가시성 개선 및 버튼 디자인
st.markdown("""
    <style>
    .big-start-btn .stButton > button {
        height: 5em !important;
        font-size: 1.5em !important;
        font-weight: bold !important;
        border-radius: 20px !important;
        width: 100%;
    }
    .earn-box { 
        background-color: #ffffff; 
        padding: 25px; 
        border-radius: 20px; 
        text-align: center; 
        border: 2px solid #27ae60; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .off-save-btn .stButton > button {
        background-color: #c0392b !important;
        color: white !important;
        height: 3.5em !important;
        font-weight: bold !important;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

def get_now():
    return datetime.utcnow() + timedelta(hours=9)

TEMP_FILE = "temp_work_v32.csv"
DATA_FILE = "work_log_final_v3.csv"
HOURLY_WAGE = 15000

# 파일 초기화
for f, cols in [(TEMP_FILE, ["날짜", "출근시간"]), (DATA_FILE, ["날짜", "근무시간_h", "급여_원", "Tip_원", "합계_원", "메모"])]:
    if not os.path.exists(f): pd.DataFrame(columns=cols).to_csv(f, index=False)

if 'menu_index' not in st.session_state: st.session_state.menu_index = 0

# --- 사이드바 ---
with st.sidebar:
    st.title("📂 메뉴")
    menu = st.radio("이동", ["🚀 실시간 대시보드", "🧾 주급 정산소"], index=st.session_state.menu_index)
    st.session_state.menu_index = ["🚀 실시간 대시보드", "🧾 주급 정산소"].index(menu)
    if st.button("🧹 데이터 강제 리셋"):
        if os.path.exists(TEMP_FILE): os.remove(TEMP_FILE)
        st.rerun()

# --- 1. 실시간 대시보드 ---
if menu == "🚀 실시간 대시보드":
    st.title("💸 수익 대시보드")
    temp_df = pd.read_csv(TEMP_FILE)
    
    if not temp_df.empty:
        # 실시간 업데이트를 위한 컨테이너 생성
        placeholder = st.empty()
        
        calc_time = str(temp_df.iloc[-1]["출근시간"])
        
        # --- 실시간 루프 (이 영역이 초당 업데이트됨) ---
        # 사용자가 퇴근 버튼을 누르기 전까지는 계속 실행되지만, 
        # 스트림릿 구조상 다른 위젯 조작 시 루프가 재시작됩니다.
        with placeholder.container():
            now = get_now()
            start_dt = datetime.strptime(f"{now.date()} {calc_time}", "%Y-%m-%d %H:%M")
            if now < start_dt - timedelta(hours=6): start_dt -= timedelta(days=1)
            
            worked_seconds = (now - start_dt).total_seconds()
            is_future = now < start_dt
            
            # 수익 계산 (초 단위 비례 계산)
            current_money = 0 if is_future else int((worked_seconds / 3600) * HOURLY_WAGE)
            worked_hours_display = 0.0 if is_future else worked_seconds / 3600

            st.markdown(f"""<div class="earn-box">
                <p style="color:#555; font-size:1.1em;">💰 {calc_time} 출근 기준</p>
                <h1 style="color:#27ae60; font-size:3.5em; margin:10px 0;">{current_money:,} 원</h1>
                <p style="color:#888;">{"⏳ 근무 대기 중" if is_future else f"🔥 {worked_hours_display:.4f}시간째 실시간 근무 중"}</p>
            </div>""", unsafe_allow_html=True)
            
            # 매우 짧은 대기 후 다시 새로고침 유도 (이게 핵심)
            time.sleep(1)
            st.rerun()

        # --- 퇴근 기록 영역 (루프 밖이 아니라 같이 렌더링되게 하려면 위쪽에 배치 가능) ---
    else:
        st.subheader("📅 오늘 근무 시작")
        st.markdown('<div class="big-start-btn">', unsafe_allow_html=True)
        if st.button("🚀 20:00 정시 출근", type="primary"):
            pd.DataFrame([[get_now().date(), "20:00"]], columns=["날짜", "출근시간"]).to_csv(TEMP_FILE, index=False)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.write("")
        with st.popover("➕ 정시 외 출근 시간 입력"):
            h = st.number_input("시", 0, 23, 19); m = st.number_input("분", 0, 59, 0)
            if st.button("입력 시간으로 출근"):
                pd.DataFrame([[get_now().date(), f"{h:02d}:{m:02d}"]], columns=["날짜", "출근시간"]).to_csv(TEMP_FILE, index=False)
                st.rerun()

    # 퇴근 설정 UI (출근 상태일 때만 표시)
    if not temp_df.empty:
        st.markdown("---")
        st.subheader("🏁 퇴근 및 정산")
        
        time_options = []
        for h in [22, 23, 0, 1, 2, 3, 4, 5, 6]:
            time_options.append(f"{h:02d}:00")
            if h != 6: time_options.append(f"{h:02d}:30")
        
        now = get_now()
        current_t_str = now.strftime("%H:%M")
        default_idx = 0
        if current_t_str in time_options:
            default_idx = time_options.index(current_t_str)

        sel_off_time = st.selectbox("퇴근 시간 선택", time_options, index=default_idx)
        tip = st.select_slider("오늘 받은 tip", options=[i for i in range(0, 100001, 10000)], value=0)
        memo = st.text_input("메모", placeholder="특이사항 입력")

        st.markdown('<div class="off-save-btn">', unsafe_allow_html=True)
        if st.button("🚨 퇴근하고 기록 저장"):
            calc_time = str(temp_df.iloc[-1]["출근시간"])
            start_dt = datetime.strptime(f"{now.date()} {calc_time}", "%Y-%m-%d %H:%M")
            if now < start_dt - timedelta(hours=6): start_dt -= timedelta(days=1)
            
            h_val, m_val = map(int, sel_off_time.split(":"))
            off_dt = now.replace(hour=h_val, minute=m_val, second=0, microsecond=0)
            if off_dt <= start_dt: off_dt += timedelta(days=1)
            
            f_hours = round((off_dt - start_dt).total_seconds() / 3600, 1)
            f_wage = int(f_hours * HOURLY_WAGE)
            
            new_rec = pd.DataFrame([[now.strftime("%m/%d"), f_hours, f_wage, tip, (f_wage+tip), memo]], 
                                   columns=["날짜", "근무시간_h", "급여_원", "Tip_원", "합계_원", "메모"])
            pd.concat([pd.read_csv(DATA_FILE), new_rec], ignore_index=True).to_csv(DATA_FILE, index=False)
            os.remove(TEMP_FILE)
            st.session_state.menu_index = 1
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 2. 주급 정산소 (기존과 동일) ---
elif menu == "🧾 주급 정산소":
    st.title("🧾 주급 정산소")
    df = pd.read_csv(DATA_FILE)
    if df.empty:
        st.warning("아직 저장된 기록이 없습니다.")
    else:
        for i, row in df.iterrows():
            with st.expander(f"📅 {row['날짜']} | {row['근무시간_h']}h | {row['합계_원']:,}원"):
                with st.form(f"edit_{i}"):
                    new_h = st.number_input("근무 시간 수정", value=float(row['근무시간_h']), step=0.5)
                    new_tip = st.number_input("Tip 수정", value=int(row['Tip_원']), step=5000)
                    new_memo = st.text_input("메모", value=str(row['메모']) if pd.notna(row['메모']) else "")
                    if st.form_submit_button("💾 저장"):
                        df.at[i, '근무시간_h'] = new_h
                        df.at[i, '급여_원'] = int(new_h * HOURLY_WAGE)
                        df.at[i, 'Tip_원'] = new_tip
                        df.at[i, '합계_원'] = int(new_h * HOURLY_WAGE) + new_tip
                        df.at[i, '메모'] = new_memo
                        df.to_csv(DATA_FILE, index=False)
                        st.rerun()
                if st.button(f"🗑️ 삭제", key=f"del_{i}"):
                    df.drop(i).to_csv(DATA_FILE, index=False)
                    st.rerun()
        st.markdown(f"### 📊 이번 주 합계: {df['합계_원'].sum():,}원")
