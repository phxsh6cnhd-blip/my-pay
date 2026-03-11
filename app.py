import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# 1. 페이지 설정 및 강제 격자 디자인 (CSS)
st.set_page_config(page_title="알바 매니저 Pro", page_icon="💰", layout="wide")

st.markdown("""
    <style>
    /* 버튼들을 가로로 정렬하는 컨테이너 */
    .grid-container {
        display: grid;
        grid-template-columns: repeat(4, 1fr); /* 무조건 4열 고정 */
        gap: 8px;
        padding: 10px 0;
    }
    .stButton>button { 
        width: 100%; 
        border-radius: 12px; 
        height: 3.5em; 
        font-weight: bold; 
        background-color: white !important; 
        color: #333 !important; 
        border: 1px solid #ddd !important;
    }
    /* 출근/퇴근 메인 버튼 스타일 */
    .main-btn button { background-color: #27ae60 !important; color: white !important; border: none !important; }
    .off-btn button { background-color: #c0392b !important; color: white !important; border: none !important; }
    
    .earn-box { background-color: #ffffff; padding: 25px; border-radius: 20px; text-align: center; border: 2px solid #27ae60; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .selected-time { background-color: #e8f5e9; padding: 10px; border-radius: 10px; text-align: center; border: 2px solid #27ae60; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

def get_now():
    return datetime.utcnow() + timedelta(hours=9)

TEMP_FILE = "temp_work_v27.csv"
DATA_FILE = "work_log_final_v3.csv"

# 파일 초기화
for f, cols in [(TEMP_FILE, ["날짜", "출근시간"]), (DATA_FILE, ["날짜", "근무시간_h", "급여_원", "Tip_원", "합계_원", "메모"])]:
    if not os.path.exists(f): pd.DataFrame(columns=cols).to_csv(f, index=False)

if 'menu_index' not in st.session_state: st.session_state.menu_index = 0
if 'sel_off_time' not in st.session_state: st.session_state.sel_off_time = "미선택"

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
        calc_time = str(temp_df.iloc[-1]["출근시간"])
        now = get_now()
        start_dt = datetime.strptime(f"{now.date()} {calc_time}", "%Y-%m-%d %H:%M")
        if now < start_dt - timedelta(hours=6): start_dt -= timedelta(days=1)
        
        is_future = now < start_dt
        worked_hours = 0.0 if is_future else (now - start_dt).total_seconds() / 3600
        current_money = int(worked_hours * 15000)
        
        st.markdown(f"""<div class="earn-box">
            <p style="color:#555;">💰 {calc_time} 출근 기준</p>
            <h1 style="color:#27ae60; font-size:3.2em; margin:0;">{current_money:,} 원</h1>
            <p style="color:#888;">{"⏳ 대기 중" if is_future else f"🔥 {worked_hours:.1f}시간째 근무"}</p>
        </div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("🏁 퇴근 시간 선택")
        
        # 시간 리스트 (22:00 ~ 06:00)
        time_slots = []
        for h in [22, 23, 0, 1, 2, 3, 4, 5]:
            time_slots.append(f"{h:02d}:00")
            time_slots.append(f"{h:02d}:30")
        time_slots.append("06:00")

        # --- 아이폰용 강제 4열 그리드 구현 ---
        # 4개씩 묶어서 컬럼을 생성하되, 모바일에서도 안 깨지게 gap 조절
        for i in range(0, len(time_slots), 4):
            cols = st.columns(4) # st.columns 내부에 버튼을 넣으면 폰에선 한 줄로 보일 수 있음
            # 그래서 columns 가로 비율을 아주 작게 강제 설정
            for j in range(4):
                if i + j < len(time_slots):
                    t = time_slots[i + j]
                    is_selected = (st.session_state.sel_off_time == t)
                    label = f"✅{t}" if is_selected else t
                    if cols[j].button(label, key=f"btn_{t}"):
                        st.session_state.sel_off_time = t
                        st.rerun()

        with st.expander("➕ 그 외 시간 입력"):
            custom_t = st.time_input("퇴근 시간", value=now.time())
            if st.button("입력 시간 확정"):
                st.session_state.sel_off_time = custom_t.strftime("%H:%M")

        st.markdown(f"""<div class="selected-time">
            <small>선택된 퇴근 시간</small>
            <h3 style="margin:0; color:#27ae60;">{st.session_state.sel_off_time}</h3>
        </div>""", unsafe_allow_html=True)

        tip = st.select_slider("오늘 받은 tip", options=[i for i in range(0, 100001, 10000)], value=0)
        memo = st.text_input("메모", placeholder="특이사항")

        st.write("")
        st.markdown('<div class="off-btn">', unsafe_allow_html=True)
        if st.button("🚨 퇴근하고 기록 저장"):
            if st.session_state.sel_off_time == "미선택":
                st.error("시간을 선택해주세요!")
            else:
                h_val, m_val = map(int, st.session_state.sel_off_time.split(":"))
                off_dt = now.replace(hour=h_val, minute=m_val, second=0, microsecond=0)
                if off_dt <= start_dt: off_dt += timedelta(days=1)
                f_hours = round((off_dt - start_dt).total_seconds() / 3600, 1
