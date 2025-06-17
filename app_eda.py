import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
if platform.system() == 'Windows':
    plt.rcParams['font.family'] = 'Malgun Gothic'
elif platform.system() == 'Darwin':  # macOS
    plt.rcParams['font.family'] = 'AppleGothic'
else:  # Linux (e.g. Streamlit Cloud, Ubuntu 등)
    plt.rcParams['font.family'] = 'NanumGothic'

# 마이너스 부호 깨짐 방지
plt.rcParams['axes.unicode_minus'] = False
# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 인구 통계 분석 대시보드")

        # 로그인 환영 메시지
        if st.session_state.get("logged_in"):
            user_email = st.session_state.get("user_email", "사용자")
            st.success(f"👋 {user_email}님, 환영합니다!")

        # 소개 구분선
        st.markdown("---")

        # 프로젝트 소개
        st.header("📊 프로젝트 개요")
        st.markdown("""
        이 대시보드는 **전국 시도별 인구 통계 데이터를 시각화하고 탐색**할 수 있도록 제작되었습니다.  
        데이터는 공개된 정부 통계 자료를 기반으로 하며, 연도별·성별·시도별 인구 변화 추이를 직관적으로 분석할 수 있습니다.
        """)

        # 데이터셋 설명
        st.header("📁 데이터셋 정보")
        st.markdown("""
        - **데이터셋명**: `population_trends.csv`  
        - **출처**: 대한민국 통계청 (KOSIS)  
        - **데이터 기간**: 2000년 ~ 2023년  
        - **주요 변수**:
            - `년도`: 기준 연도  
            - `시도`: 행정 구역 단위 (예: 서울특별시, 부산광역시 등)  
            - `성별`: 남자 / 여자  
            - `인구수`: 해당 시점의 총 인구 수
        """)

        # 사용자 가이드
        st.markdown("---")
        st.info("📌 왼쪽 사이드바에서 EDA, 시각화, 예측 등을 선택해 인구 데이터를 탐색해보세요.")
# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📈 Population Trends EDA")
        uploaded = st.file_uploader("Upload population_trends.csv", type="csv")
        if not uploaded:
            st.info("Please upload population_trends.csv file.")
            return

        df = pd.read_csv(uploaded)

        # Preprocessing
        df.replace('-', 0, inplace=True)
        df[['인구', '출생아수(명)', '사망자수(명)']] = df[['인구', '출생아수(명)', '사망자수(명)']].apply(pd.to_numeric)

        tabs = st.tabs(["기초 통계", "연도별 추이", "지역별 분석", "변화량 분석", "시각화"])

        # 1. 기초 통계
        with tabs[0]:
            st.header("📊 Basic Statistics & Structure")
            st.subheader("DataFrame Structure")
            buffer = st.empty()
            with st.expander("df.info()"):
                import io
                buf = io.StringIO()
                df.info(buf=buf)
                st.text(buf.getvalue())

            st.subheader("Descriptive Statistics")
            st.dataframe(df.describe())

            st.subheader("Missing / Duplicates")
            st.write("- Missing values:")
            st.dataframe(df.isnull().sum())
            st.write(f"- Duplicated rows: {df.duplicated().sum()}")

        # 2. 연도별 추이
        with tabs[1]:
            st.header("📈 Yearly Population Trend (National)")

            national = df[df['지역'] == '전국']
            fig, ax = plt.subplots()
            sns.lineplot(data=national, x='연도', y='인구', ax=ax)
            ax.set_title("Total Population Trend")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            
            # Forecast 2035
            recent = national[national['연도'] >= national['연도'].max() - 2]
            birth_avg = recent['출생아수(명)'].mean()
            death_avg = recent['사망자수(명)'].mean()
            delta = birth_avg - death_avg
            pred_2035 = national['인구'].iloc[-1] + delta * (2035 - national['연도'].iloc[-1])
            ax.axhline(pred_2035, color='red', linestyle='--')
            ax.text(2033, pred_2035, f"Predicted 2035: {int(pred_2035):,}", color='red')
            st.pyplot(fig)

        # 3. 지역별 인구 변화량
        with tabs[2]:
            st.header("🏙️ Regional Change (Last 5 Years)")

            latest_year = df['연도'].max()
            prev_year = latest_year - 5
            df_latest = df[df['연도'] == latest_year].set_index('지역')
            df_prev = df[df['연도'] == prev_year].set_index('지역')

            diff = df_latest['인구'] - df_prev['인구']
            diff = diff.drop("전국", errors='ignore').sort_values(ascending=False)

            fig, ax = plt.subplots(figsize=(8, 10))
            sns.barplot(x=diff.values / 1000, y=diff.index, ax=ax)
            ax.set_xlabel("Change (Thousands)")
            ax.set_title("5-year Population Change by Region")
            for i, val in enumerate(diff.values / 1000):
                ax.text(val, i, f"{val:.1f}", va='center')
            st.pyplot(fig)

            # 변화율
            rate = ((df_latest['인구'] - df_prev['인구']) / df_prev['인구'] * 100).drop("전국", errors='ignore').sort_values(ascending=False)
            fig2, ax2 = plt.subplots(figsize=(8, 10))
            sns.barplot(x=rate.values, y=rate.index, ax=ax2)
            ax2.set_xlabel("Change Rate (%)")
            ax2.set_title("5-year Population Growth Rate by Region")
            for i, val in enumerate(rate.values):
                ax2.text(val, i, f"{val:.2f}%", va='center')
            st.pyplot(fig2)

        # 4. 변화량 분석
        with tabs[3]:
            st.header("📉 Top 100 Population Change (Region & Year)")

            df_sorted = df[df['지역'] != '전국'].copy()
            df_sorted['증감'] = df_sorted.groupby('지역')['인구'].diff()

            top100 = df_sorted.sort_values(by='증감', ascending=False).head(100)
            top100_display = top100[['연도', '지역', '증감']].copy()

            # 💡 숫자형 그대로 두고 포맷은 Styler로 적용
            styled_df = top100_display.style.format({'증감': '{:,.0f}'}).background_gradient(cmap='coolwarm', subset=['증감'])

            st.dataframe(styled_df)


        # 5. 시각화
        with tabs[4]:
            st.header("🎨 Heatmap & Stacked Area Chart")

            pivot = df.pivot(index='연도', columns='지역', values='인구')
            pivot = pivot.drop(columns='전국', errors='ignore')
            pivot = pivot.fillna(0)

            fig, ax = plt.subplots(figsize=(10, 6))
            pivot.plot.area(ax=ax, stacked=True, cmap="tab20")
            ax.set_title("Population Stacked Area")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            st.pyplot(fig)


# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()
