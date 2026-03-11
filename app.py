import streamlit as st
import pandas as pd
from datetime import datetime
import os

# 1. 페이지 설정
st.set_page_config(page_title="주급 매니저", page_icon="💰", layout="wide")

# 2. 데이터 파일 설정 (v13: 상세 날짜 저장 기능 추가)
DATA_FILE = "work_log_v13.csv"
if not os.path.exists(DATA_FILE):
    # '상세날짜' 컬럼 추가
    df = pd.DataFrame(columns=["정산날짜", "총일한시간", "출근일수", "상세날짜", "tip합계", "최종정산금"])
    df.to_csv(DATA_FILE, index=False)

TEMP_FILE = "temp_log_v13.csv"
if not os.path.exists(TEMP_FILE):
    df_temp = pd.DataFrame(columns=["날짜", "일한시간", "tip"])
    df_temp.to_csv(TEMP_FILE, index=False)

st.title("💰 주급 정산 시스템")
st.markdown("---")

# 3. 메뉴 선택
menu = st.sidebar.selectbox("메뉴", ["➕ 오늘 기록하기", "🧾 주급 정산소"])

if menu == "➕ 오늘 기록하기":
    st.subheader("📝 업무 기록")
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("날짜", datetime.now())
        work_time = st.number_input("일한 시간 (h)", min_value=0.0, value=8.0, step=0.5)
    with col2:
        tip_options = [i for i in range(0, 100001, 10000)]
        tip_val = st.select_slider("tip 선택 (원)", options=tip_options, value=0)
        st.write(f"선택된 금액: **{tip_val:,}원**")

    if st.button("💾 저장하기"):
        new_row = pd.DataFrame([[date, work_time, tip_val]], columns=["날짜", "일한시간", "tip"])
        new_row.to_csv(TEMP_FILE, mode='a', header=False, index=False)
        st.success(f"✅ {date} 저장 완료")

elif menu == "🧾 주급 정산소":
    st.subheader("🔍 정산 대기 내역")
    
    if os.path.exists(TEMP_FILE):
        temp_df = pd.read_csv(TEMP_FILE)
        
        if not temp_df.empty:
            # 중복 날짜 제외 정렬 및 리스트화
            unique_days = sorted(temp_df["날짜"].unique())
            working_days_count = len(unique_days)
            # 3/11, 3/12 형식으로 변환
            date_list_str = ", ".join([datetime.strptime(d, '%Y-%m-%d').strftime('%m/%d') for d in unique_days])
            
            total_hours = temp_df["일한시간"].sum()
            tip_total = temp_df["tip"].sum()
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Total Hours", f"{total_hours} h")
            with c2:
                st.metric("Working Days", f"{working_days_count} 일")
            with c3:
                st.metric("tip", f"{tip_total:,} 원")
            
            st.markdown("---")
            st.write(f"📅 **출근 예정일:** {date_list_str}")
            st.table(temp_df)
            
            st.subheader("💰 최종 정산 금액")
            final_pay = st.number_input("받은 총 금액 (원)", min_value=0, step=1000)
            
            if st.button("✅ 정산 완료"):
                today_str = datetime.now().strftime("%Y-%m-%d")
                # 상세 날짜 문자열 포함해서 저장
                summary_row = pd.DataFrame([[today_str, total_hours, working_days_count, date_list_str, tip_total, final_pay]], 
                                           columns=["정산날짜", "총일한시간", "출근일수", "상세날짜", "tip합계", "최종정산금"])
                summary_row.to_csv(DATA_FILE, mode='a', header=False, index=False)
                
                os.remove(TEMP_FILE)
                st.success(f"🎉 {today_str} 정산 완료")
                st.rerun()
        else:
            st.info("내역이 없습니다.")

    # 4. 과거 정산 기록 리스트 (상세 날짜 확인 버튼 추가)
    st.markdown("---")
    with st.expander("📁 과거 기록 보기"):
        if os.path.exists(DATA_FILE):
            history_df = pd.read_csv(DATA_FILE)
            if not history_df.empty:
                for i, row in history_df.iterrows():
                    # 메인 정보 한 줄
                    st.write(f"📅 **{row['정산날짜']} 정산** | ⏱ {row['총일한시간']}h (**{int(row['출근일수'])}일**) | 💵 **{int(row['최종정산금']):3,}원**")
                    # 상세 날짜를 누르면 보이게!
                    with st.popover("📅 출근 날짜 확인"):
                        st.write(f"이 기간에 일한 날짜: **{row['상세날짜']}**")
                    st.markdown("---")
            else:
                st.write("기록된 정산 내역이 없습니다.")

# 초기화 버튼
if st.sidebar.button("🧹 전체 데이터 초기화"):
    if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
    if os.path.exists(TEMP_FILE): os.remove(TEMP_FILE)
    st.rerun()