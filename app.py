import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# 1. 페이지 설정
st.set_page_config(page_title="알바 매니저 Pro", page_icon="💰", layout="wide")

# CSS: 가시성 개선 및 버튼 크기 조절
st.markdown("""
    <style>
    /* 출근 버튼 박스 크기 키우기 */
    .big-start-btn .stButton > button {
        height: 5em !important;
        font-size: 1.5em !important;
        font-weight: bold !important;
        border-radius: 20px !important;
    }
    /* 수익 대시보드 박스 */
    .earn-box { 
        background-color: #ffffff; 
        padding: 25px; 
        border-radius: 20px; 
        text-align: center; 
        border: 2px solid #27ae60; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    /* 퇴근 저장 버튼 */
    .off-save-btn .stButton > button {
        background-color: #c0392b !important;
        color: white !important;
        height: 3.5em !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

def get_now():
    return datetime.utcnow() + timedelta(hours=9)

TEMP_FILE = "temp_work_v32.csv"
DATA_FILE = "work_log_final_v3.csv"

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
        calc_time = str(temp_df.iloc[-1]["출근시간"])
        now = get_now()
        start_dt = datetime.strptime(f"{now.date()} {calc_time}", "%Y-%m-%d %H:%M")
        if now < start_dt - timedelta(hours=6): start_dt -= timedelta(days=1)
        
        is_future = now < start_dt
        worked_hours = 0.0 if is_future else (now - start_dt).total_seconds() / 3600
        current_money = int(worked_hours * 15000)
        
        st.markdown(f"""<div class="earn-box">
            <p style="color:#555; font-size:1.1em;">💰 {calc_time} 출근 기준</p>
            <h1 style="color:#27ae60; font-size:3em; margin:10px 0;">{current_money:,} 원</h1>
            <p style="color:#888;">{"⏳ 근무 대기 중" if is_future else f"🔥 {worked_hours:.1f}시간째 근무 중"}</p>
        </div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("🏁 퇴근 시간 선택")
        
        # 아이폰에서 가장 편한 휠(Selectbox) 방식
        time_options = []
        for h in [22, 23, 0, 1, 2, 3, 4, 5, 6]:
            time_options.append(f"{h:02d}:00")
            if h != 6: time_options.append(f"{h:02d}:30")
        
        # 현재 시간과 가장 가까운 인덱스 찾기
        current_t_str = now.strftime("%H:%M")
        default_idx = 0
        if current_t_str in time_options:
            default_idx = time_options.index(current_t_str)

        sel_off_time = st.selectbox("퇴근 시간을 드르륵 돌려서 골라주세요 👇", time_options, index=default_idx)

        with st.expander("➕ 그 외 시간 직접 입력"):
            custom_t = st.time_input("시간 선택", value=now.time())
            if st.button("직접 입력한 시간으로 적용"):
                sel_off_time = custom_t.strftime("%H:%M")

        st.info(f"선택된 퇴근 시간: **{sel_off_time}**")
        
        tip = st.select_slider("오늘 받은 tip", options=[i for i in range(0, 100001, 10000)], value=0)
        memo = st.text_input("메모", placeholder="특이사항 입력")

        st.write("")
        st.markdown('<div class="off-save-btn">', unsafe_allow_html=True)
        if st.button("🚨 퇴근하고 기록 저장"):
            h_val, m_val = map(int, sel_off_time.split(":"))
            off_dt = now.replace(hour=h_val, minute=m_val, second=0, microsecond=0)
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
        # 출근 버튼을 화면에 꽉 차고 크게 만듦
        st.markdown('<div class="big-start-btn">', unsafe_allow_html=True)
        if st.button("🚀 20:00 정시 출근", type="primary"): # type="primary"로 초록색(기본) 적용
            pd.DataFrame([[get_now().date(), "20:00"]], columns=["날짜", "출근시간"]).to_csv(TEMP_FILE, index=False)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.write("")
        with st.popover("➕ 정시 외 출근 시간 입력"):
            h = st.number_input("시", 0, 23, 19); m = st.number_input("분", 0, 59, 0)
            if st.button("입력 시간으로 출근"):
                pd.DataFrame([[get_now().date(), f"{h:02d}:{m:02d}"]], columns=["날짜", "출근시간"]).to_csv(TEMP_FILE, index=False)
                st.rerun()

# --- 2. 주급 정산소 ---
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
                        df.at[i, '급여_원'] = int(new_h * 15000)
                        df.at[i, 'Tip_원'] = new_tip
                        df.at[i, '합계_원'] = int(new_h * 15000) + new_tip
                        df.at[i, '메모'] = new_memo
                        df.to_csv(DATA_FILE, index=False)
                        st.rerun()
                if st.button(f"🗑️ 삭제", key=f"del_{i}"):
                    df.drop(i).to_csv(DATA_FILE, index=False)
                    st.rerun()
        st.markdown(f"### 📊 이번 주 합계: {df['합계_원'].sum():,}원")
