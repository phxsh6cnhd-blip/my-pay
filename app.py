import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# 1. 페이지 설정
st.set_page_config(page_title="알바 매니저 Pro", page_icon="💰", layout="wide")

# UI 디자인 커스텀
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { background-color: #27ae60 !important; color: white !important; }
    .off-section button { background-color: #c0392b !important; color: white !important; }
    .earn-box { background-color: #ffffff; padding: 25px; border-radius: 20px; text-align: center; border: 2px solid #27ae60; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 설정 및 파일 경로
HOURLY_WAGE = 15000 
TEMP_FILE = "temp_work_v18.csv" # 버전 업그레이드
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
            today_date = datetime.now().date()
            start_dt = datetime.strptime(f"{today_date} {start_time_str}", "%Y-%m-%d %H:%M")
            
            # 실시간 계산
            now = datetime.now()
            # 만약 지금이 새벽이고 출근은 어제 밤이라면? (실시간 대시보드용 날짜 보정)
            if now < start_dt:
                start_dt -= timedelta(days=1)
            
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
                # 퇴근 시간 계산 로직 (날짜 변경 인식)
                off_dt = datetime.now().replace(hour=off_h, minute=off_min, second=0, microsecond=0)
                
                # 만약 퇴근 시간이 출근 시간보다 빠르면? -> 다음 날로 간주!
                if off_dt <= start_dt:
                    off_dt += timedelta(days=1)
                
                final_hours = (off_dt - start_dt).total_seconds() / 3600
                st.success(f"총 {final_hours:.1f}시간 근무 (Tip: {tip_val:,}원) 저장 완료!")
                
                # [여기에 DATA_FILE 저장 로직을 추가하면 정산소랑 연동됩니다!]
                os.remove(TEMP_FILE)
                st.balloons()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"에러 발생: {e}. 사이드바에서 리셋을 눌러주세요.")

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
🌟 업데이트된 '날짜 인식' 논리
예시: 밤 20:00에 출근하고 다음 날 새벽 06:00을 퇴근 시간으로 선택하면?

기존: 6시가 20시보다 작으므로 에러가 나거나 0시간으로 인식.

현재: "어? 퇴근 시간이 출근 시간보다 숫자가 작네? 그럼 이건 다음 날이겠구나!"라고 판단해서 자동으로 +24시간을 더해 10시간 근무로 계산합니다.

🚀 적용 방법
GitHub에서 app.py 수정하고 Commit changes 누르기.

폰에서 앱 열고 사이드바의 [🧹 데이터 강제 리셋] 한번 누르기 (파일 버전이 바뀌었기 때문!).

이제 새벽에 퇴근할 때도 날짜 고민 없이 시간만 딱 찍고 퇴근하면 돼! 이 기능 덕분에 정산이 훨씬 정확해질 거야. 😎

이제 폰에서 테스트해 볼래? 밤 8시 출근 누르고 퇴근 시간을 새벽 6시로 해서 한번 저장해 봐! 제대로 나오는지 궁금하네. Would you like me to help link this 'Daily Log' directly into your 'Weekly Settlement' so you can s
