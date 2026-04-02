import warnings
warnings.filterwarnings("ignore", category=UserWarning)  # 모든 UserWarning(사용자 경고)을 화면에 표시하지 않도록 설정합니다.

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from collections import Counter
import streamlit_authenticator as stauth

# [필수] 1. 페이지 설정은 무조건 최상단
st.set_page_config(page_title="이주여성폭력 통합 분석 대시보드", layout="wide")

# 0. 사용자 데이터 및 인증 설정
names = ["King", "Kang"]
usernames = ["king", "kang"]
passwords = ["king5678", "kang9819"]

credentials = {
    "usernames": {
        usernames[0]: {"name": names[0], "password": passwords[0]},
        usernames[1]: {"name": names[1], "password": passwords[1]}
    }
}

# 비밀번호 해싱 처리 (최신 버전 방식)
stauth.Hasher.hash_passwords(credentials)

authenticator = stauth.Authenticate(
    credentials,
    "libra_dashboard",
    "libra_key_32_characters_long_for_security",
    cookie_expiry_days=30
)

# 로그인 전에도 Web App의 Title이 보여야 하므로 if문 바깥에 배치합니다.
st.write("") # 상단 여백
st.title("📊 폭력유형 및 출신국별 상담 키워드 분석")
st.subheader('Libra Lab | M&E Center, Ajou')

# [핵심 수정] 로그인 상태에 따른 메시지 분기 로직
if not st.session_state.get("authentication_status"):
    # 로그인 전 메시지
    st.info("🔒 본 시스템은 리브라 연구소 전용 분석 도구입니다. \n\n" "인가된 계정으로 로그인해 주세요.")
else:
    # 로그인 성공 후 메시지
    st.success("📝 본 연구는 다누리 콜센터의 2025년 상담데이터를 기반으로 이주여성들의 폭력 현황을 분석한 결과입니다.\n\n "
               "학술적인 목적으로 제작되었으며, 다른 목적의 사용은 공식적인 Approval이 필요합니다.")

st.markdown("---")

# 0-1. 로그인 화면 출력
authenticator.login(location='main')

# 세션 상태에 따른 분기 처리
if st.session_state["authentication_status"] is False:
    st.error("사용자 이름 또는 비밀번호가 올바르지 않습니다.")
    st.stop()
elif st.session_state["authentication_status"] is None:
    st.warning("로그인이 필요합니다. 아이디와 비밀번호를 입력해 주세요.")
    st.stop()

# ---------------------------------------------------------
# 로그인 성공 시에만 아래 코드가 실행 (전체 들여쓰기 적용)
# ---------------------------------------------------------
if st.session_state["authentication_status"]:
    
    # 로그아웃 버튼과 환영 메시지
    authenticator.logout("로그아웃", "sidebar")
    st.sidebar.write(f"환영합니다, **{st.session_state['name']}**님!")

    # 2. 제목 및 정보
    st.title("📊 폭력유형 및 출신국별 상담 키워드 분석")
    st.subheader('Libra Lab | M&E Center, Ajou')
    st.markdown("---")

    # 3. 데이터 로드 설정
    # [Tip] PC에서는 아래 경로를 쓰고, GitHub 올릴 땐 파일명만 남기세요.
    file_path = r"C:\King Cho\OneDrive - Loyalty\건강가정진흥원(KIHF)\강복정\이주여성폭력\상담데이터_WordString.xlsx" 
    
    @st.cache_data
    def load_data():
        # 엔진을 명시하여 엑셀 로딩 최적화
        return pd.read_excel(file_path, engine='openpyxl')

    try:
        df = load_data()
        
        # 기초 리스트 생성
        all_types = df['폭력유형'].unique().tolist()
        all_countries = df['출신국'].value_counts().index.tolist()
        total_country_count = len(all_countries)

        # 4. 사이드바 다중 슬라이서
        st.sidebar.header("🔍 분석 필터 설정")
        selected_types = st.sidebar.multiselect("📂 폭력 유형 선택:", options=all_types)
        selected_countries = st.sidebar.multiselect("🌍 출신국 선택:", options=all_countries)

        # 5. 필터링 로직
        filtered_df = df.copy()
        if selected_types:
            filtered_df = filtered_df[filtered_df['폭력유형'].isin(selected_types)]
            display_types = ", ".join(selected_types)
        else:
            display_types = "전체 유형"

        if selected_countries:
            filtered_df = filtered_df[filtered_df['출신국'].isin(selected_countries)]
            display_country_count = len(selected_countries)
        else:
            display_country_count = total_country_count

        dataset = filtered_df[['WordString']].drop_duplicates()


        # 6. 워드클라우드 로직
        exclude_words = ['신고', '요청', '문의', '선생님']
        all_words = " ".join(dataset['WordString'].astype(str).dropna()).split()
        word_list = [w for w in all_words if w not in exclude_words]
        word_counts = Counter(word_list)


        # ---------------------------------------------------------
        # 7. [수정] 상단 설명 박스 (동적 지표 반영)
        # ---------------------------------------------------------
        
        # [로직 1] 대상 국가 나열 (미선택 시 상담건수 순 정렬)
        if selected_countries:
            display_countries = ", ".join(selected_countries)
        else:
            # 전체 국가를 상담건수(Unique Count)가 많은 순으로 나열
            top_countries = df['출신국'].value_counts().index.tolist()
            display_countries = ", ".join(top_countries)

        # [로직 2] 폭력 유형 나열
        if selected_types:
            display_types = ", ".join(selected_types)
        else:
            display_types = ", ".join(all_types)

        # [로직 3] 해당 상담건수 (상담번호의 Unique Count)
        # filtered_df는 이미 5번 섹션에서 필터링된 데이터입니다.
        unique_consultation_count = filtered_df['상담번호'].nunique()

        # [로직 4] 사용된 단어의 총 갯수 (중복 포함)
        # word_list는 불용어를 제외하고 추출된 모든 단어의 리스트입니다.
        total_word_count = len(word_list)

        # HTML 기반 디자인 출력
        st.markdown(f"""
        <div style="background-color: #2E86C1; padding: 25px; border-radius: 12px; border-left: 8px solid #154360;">   
            <h4 style="color: white; margin-top: 0; border-bottom: 1px solid rgba(255,255,255,0.3); padding-bottom: 10px;">📋 분석 요약 보고 (Analysis Summary)</h4>   
            <div style="color: white; line-height: 1.8; font-size: 15px;">
                <p style="margin: 5px 0;"><b>● 대상 국가:</b> <span style="color: #D4E6F1;">{display_countries}</span></p>
                <p style="margin: 5px 0;"><b>● 폭력 유형:</b> <span style="color: #D4E6F1;">{display_types}</span></p>
                <p style="margin: 5px 0;"><b>● 해당 상담건수:</b> <span style="font-size: 18px; font-weight: bold; color: #F1C40F;">{unique_consultation_count:,}건</span> (Unique Count)</p>
                <p style="margin: 5px 0;"><b>● 사용된 단어 갯수:</b> <span style="font-size: 18px; font-weight: bold; color: #F1C40F;">{total_word_count:,}개</span> (중복 포함)</p>
            </div>
        </div>
        """, unsafe_allow_html=True)


        # 8. 시각화 출력
        if word_counts:
            target_words = ['남편', '경찰', '폭력', '피해']
            def my_color_func(word, **kwargs):
                return "rgb(0,164,239)" if word in target_words else "rgb(150, 150, 150)"

            # [중요] GitHub 환경이면 font_path='MALGUN.TTF'로 수정 필수
            wordcloud = WordCloud(
                font_path='C:/Windows/Fonts/malgun.ttf', 
                background_color='white',
                width=1000, height=500
            ).generate_from_frequencies(word_counts).recolor(color_func=my_color_func)

            fig, ax = plt.subplots(figsize=(12, 6))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig)
            
            # 9. 결과 상세 해석
            most_common_word = word_counts.most_common(1)[0][0]
            st.markdown(f"""
            <div style="background-color: #d4edda; padding: 20px; border-radius: 10px; border: 1px solid #c3e6cb; color: #155724;">
                ● <b>가장 빈도가 높은 키워드:</b> 
                <span style="font-size: 24px; color: #00A4EF; font-weight: bold; border-bottom: 3px solid #00A4EF;">'{most_common_word}'</span><br>
                ● <b>위기 징후 알림:</b> <i>파란색 강조 단어({', '.join(target_words)})</i>는 긴급 개입 신호입니다.
            </div>
            """, unsafe_allow_html=True)

            # ---------------------------------------------------------
            # 10. [추가] 사용된 단어 빈도 TOP 100 표 출력
            # ---------------------------------------------------------
            st.markdown("---") # 구분선
            st.subheader("📋 사용된 단어의 갯수(상위 100개)")

            # Counter 객체에서 상위 100개 추출하여 데이터프레임 변환
            top_100_words = word_counts.most_common(100)
            df_top100 = pd.DataFrame(top_100_words, columns=['단어', '빈도수(회)'])
        
            # 인덱스를 1부터 시작하도록 설정 (순위 표시 효과)
            df_top100.index = df_top100.index + 1

            # 두 가지 방식 중 선택 가능합니다.
        
            # 방식 A: 깔끔한 정적 테이블 (스크롤 없이 전체 나열)
            # st.table(df_top100) 

            # 방식 B: 대화형 데이터프레임 (스크롤 가능, 정렬 가능 - 추천)
            st.dataframe(
                df_top100, 
                width='stretch', # 화면 너비에 맞춤(2026년 최신 표준)
                height=400                # 높이 조절 (너무 길어지지 않게)
            )

        else:
            st.warning("데이터가 존재하지 않습니다.")

    except Exception as e:
        st.error(f"데이터 처리 오류: {e}")    