import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from streamlit_autorefresh import st_autorefresh

# 1. 페이지 설정
st.set_page_config(page_title="알바 매니저 Pro", page_icon="💰", layout="wide")

# CSS (디자인 유지)
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
        # 출근 정보 로드
        calc_date = str(temp_df.iloc[-1]["날짜"])
        calc_time = str(temp_df.iloc[-1]["출근시간"])
        start_dt = datetime.strptime(f"{calc_date} {calc_time}", "%Y-%m-%d %H:%M")
        now = get_now()

        # 오늘 날짜와 출근 날짜가 같을 때만 실시간 갱신 활성화
        is_today_work = start_dt.date() == now.date()
        if is_today_work:
            st_autorefresh(interval=1000, key="earn_refresh")

        # 실시간/과거 시간 차이 계산
        diff_seconds = (now - start_dt).total_seconds()
        # 24시간 제한 및 과거 기록 시 마이너스 방지
        display_seconds = max(0, min(diff_seconds, 86400))
        
        current_money = int((display_seconds / 3600) * HOURLY_WAGE)
        worked_hours = display_seconds / 3600

        st.markdown(f"""<div class="earn-box">
            <p style="color:#555; font-size:1.1em;">💰 {calc_date} {calc_time} 출근 기록 중</p>
            <h1 style="color:#27ae60; font-size:3.5em; margin:10px 0;">{current_money:,} 원</h1>
            <p style="color:#888;">{f"🔥 실시간 근무 현황" if is_today_work else "📅 과거 기록 입력 모드"}</p>
        </div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("🏁 퇴근 시간 직접 입력 (중요)")
        
        # 퇴근 시간 선택 (모든 시간 옵션)
        time_options = [f"{h:02d}:{m}" for h in range(24) for m in ["00", "30"]]
        sel_off_time = st.selectbox("실제 퇴근했던 시간을 선택하세요", time_options, index=0)
        tip = st.select_slider("오늘 받은 tip", options=[i for i in range(0, 100001, 10000)], value=0)
        memo = st.text_input("메모", placeholder="특이사항")

        if st.button("🚨 위 퇴근 시간으로 최종 저장"):
            h_val, m_val = map(int, sel_off_time.split(":"))
            # 선택한 퇴근 시간으로 datetime 객체 생성
            off_dt = start_dt.replace(hour=h_val, minute=m_val)
            
            # 야간 근무 처리: 퇴근 시간이 출근보다 숫자가 작으면 다음날로 인식
            if off_dt <= start_dt:
                off_dt += timedelta(days=1)
            
            # 최종 근무 시간 계산 (여기서 다시 한번 정확히 계산)
            final_hours = (off_dt - start_dt).total_seconds() / 3600
            
            if final_hours > 24:
                st.error("근무 시간은 24시간을 초가할 수 없습니다. 퇴근 시간을 다시 확인해주세요.")
            else:
                f_wage = int(final_hours * HOURLY_WAGE)
                new_rec = pd.DataFrame([[start_dt.strftime("%m/%d"), round(final_hours, 1), f_wage, tip, (f_wage+tip), memo]], 
                                       columns=["날짜", "근무시간_h", "급여_원", "Tip_원", "합계_원", "메모"])
                
                pd.concat([pd.read_csv(DATA_FILE), new_rec], ignore_index=True).to_csv(DATA_FILE, index=False)
                os.remove(TEMP_FILE)
                st.success("기록이 완료되었습니다!")
                st.rerun()
    else:
        st.subheader("📅 근무 기록 시작")
        sel_date = st.date_input("근무 날짜", value=get_now().date())
        st.markdown('<div class="big-start-btn">', unsafe_allow_html=True)
        if st.button(f"🚀 {sel_date.strftime('%m/%d')} 출근 등록", type="primary"):
            pd.DataFrame([[sel_date, "20:00"]], columns=["날짜", "출근시간"]).to_csv(TEMP_FILE, index=False)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 2. 주급 정산소 (생략 - 기존과 동일) ---
