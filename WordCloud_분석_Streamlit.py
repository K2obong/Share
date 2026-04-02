import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from collections import Counter
import streamlit_authenticator as stauth

# 1. 페이지 설정
st.set_page_config(page_title="이주여성 상담데이터 분석", layout="wide")

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

stauth.Hasher.hash_passwords(credentials)

authenticator = stauth.Authenticate(
    credentials,
    "libra_dashboard",
    "libra_key_32_characters_long_for_security",
    cookie_expiry_days=30
)

# ---------------------------------------------------------
# [공통 영역] 로그인 전/후 모두 표시되는 상단 헤더
# ---------------------------------------------------------
st.write("") 
st.title("📊 이주여성 상담데이터 분석")
st.subheader('Libra Lab | M&E Center')

if not st.session_state.get("authentication_status"):
    st.info("🔒 본 시스템은 리브라 연구소 전용 분석 도구입니다.\n\n" 
            "🚩인가된 계정으로 로그인해 주세요.")
else:
    st.success("📝 본 연구는 다누리 콜센터의 2025년 상담데이터를 기반으로 이주여성들의 폭력 현황을 분석한 결과입니다.\n\n"
               "🚩 학술적인 목적으로 제작되었으며, 다른 목적의 사용은 공식적인 Approval이 필요합니다.")

st.markdown("---")

# 0-1. 로그인 화면 출력
authenticator.login(location='main')

if st.session_state["authentication_status"] is False:
    st.error("사용자 이름 또는 비밀번호가 올바르지 않습니다.")
    st.stop()
elif st.session_state["authentication_status"] is None:
    st.warning("로그인이 필요합니다. 아이디와 비밀번호를 입력해 주세요.")
    st.stop()

# ---------------------------------------------------------
# [분석 영역] 로그인 성공 시 실행
# ---------------------------------------------------------
if st.session_state["authentication_status"]:
    
    authenticator.logout("로그아웃", "sidebar")
    st.sidebar.write(f"환영합니다, **{st.session_state['name']}**님!")

    # 데이터 경로 (PC 환경 유지)
    file_path = "./상담데이터_WordString.xlsx"  # 🚩 Github에서는 "./상담데이터_WordString.xlsx"로 수정要
    
    @st.cache_data
    def load_data():
        return pd.read_excel(file_path, engine='openpyxl')

    try:
        df = load_data()
        
        # 1. 기초 데이터 및 사이드바 필터
        all_types = df['폭력유형'].unique().tolist()
        all_countries = df['출신국'].value_counts().index.tolist()
        
        st.sidebar.header("🔍 분석 필터 설정")
        selected_types = st.sidebar.multiselect("📂 폭력 유형 선택:", options=all_types)
        selected_countries = st.sidebar.multiselect("🌍 출신국 선택:", options=all_countries)

        # 2. 데이터 필터링 로직
        filtered_df = df.copy()
        if selected_types:
            filtered_df = filtered_df[filtered_df['폭력유형'].isin(selected_types)]
            display_types = ", ".join(selected_types)
        else:
            display_types = ", ".join(all_types)

        if selected_countries:
            filtered_df = filtered_df[filtered_df['출신국'].isin(selected_countries)]
            display_countries = ", ".join(selected_countries)
        else:
            # 미선택 시 상담건수 순 정렬
            display_countries = ", ".join(all_countries)

        # 3. [핵심] 워드클라우드용 데이터 가공 (요약 박스보다 먼저 실행되어야 함)
        dataset = filtered_df[['WordString']].drop_duplicates()
        exclude_words = ['신고', '요청', '문의', '선생님']
        all_words = " ".join(dataset['WordString'].astype(str).dropna()).split()
        word_list = [w for w in all_words if w not in exclude_words]
        word_counts = Counter(word_list)

        # 4. 상단 요약 박스 (이제 word_list를 정상 참조함)
        st.markdown(f"""
        <div style="background-color: #2E86C1; padding: 25px; border-radius: 12px; border-left: 8px solid #154360;">   
            <h4 style="color: white; margin-top: 0; border-bottom: 1px solid rgba(255,255,255,0.3); padding-bottom: 10px;">📋 분석 요약 보고 (Analysis Summary)</h4>   
            <div style="color: white; line-height: 1.8; font-size: 15px;">
                <p style="margin: 5px 0;"><b>● 대상 국가:</b> <span style="color: #cde9fa;">{display_countries}</span></p>
                <p style="margin: 5px 0;"><b>● 폭력 유형:</b> <span style="color: #cde9fa;">{display_types}</span></p>
                <p style="margin: 5px 0;"><b>● 해당 상담건수:</b> <span style="font-size: 18px; font-weight: bold; color: #F1C40F;">{filtered_df['상담번호'].nunique():,}건</span></p>
                <p style="margin: 5px 0;"><b>● 사용된 단어 갯수(중복):</b> <span style="font-size: 18px; font-weight: bold; color: #F1C40F;">{len(word_list):,}개</span></p>
                <p style="margin: 8px 0 0 0; padding-top: 8px; border-top: 1px dashed rgba(255,255,255,0.2); font-style: italic; font-size: 14px;">
                    <b>- Key Word 분석 방법:</b> 상담 문장(Text)에서 의미있는 단어만을 추출, 그 단어들의 갯수(중복)를 단어의 크기에 반영하였음.....Python>WordCloud</p>
                    <b>- 분석필터 설정방법:</b> '폭력유형'과 '출신국'을 선택(복수 선택 가능) → 필터설정에 따라 분석값들이 실시간으로 변경됨
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # [핵심 수정] 세션 간 여백 및 구분선 추가
        st.write("")         # 첫 번째 줄바꿈
        # st.write("")         # 두 번째 줄바꿈 (여백을 더 넓게 하려면 추가)
        st.markdown("---")   # 명확한 세션 구분을 위한 수평선
        st.write("")         # 워드클라우드와의 간격 확보
        
        # 워드클라우드 섹션 제목 추가 (선택 사항: 더 전문적으로 보입니다)
        st.subheader("☁️ 주요 상담 키워드 시각화 (Word Cloud)")
        st.markdown(f"""        
                <p style="margin: 5px 0;"><b>● 대상 국가:</b> <span style="color: #5CC1FF;">{display_countries}</span></p>
                <p style="margin: 5px 0;"><b>● 폭력 유형:</b> <span style="color: #5CC1FF;">{display_types}</span></p>
                <p style="margin: 5px 0;"><b>● 해당 상담건수:</b> <span style="font-size: 18px; font-weight: bold; color: #F1C40F;">{filtered_df['상담번호'].nunique():,}건</span></p>
                <p style="margin: 5px 0;"><b>● 사용된 단어 갯수(중복):</b> <span style="font-size: 18px; font-weight: bold; color: #F1C40F;">{len(word_list):,}개</span></p>
        """, unsafe_allow_html=True)

        # 5. 워드클라우드 시각화
        if word_counts:
            target_words = ['남편', '경찰', '폭력', '피해']
            def my_color_func(word, **kwargs):
                return "rgb(0,164,239)" if word in target_words else "rgb(150, 150, 150)"

            wordcloud = WordCloud(
                font_path='MALGUN.TTF',   # 🚩 Github에서는 MALGUN.TTF로 수정要
                background_color='white',
                width=1000, height=500
            ).generate_from_frequencies(word_counts).recolor(color_func=my_color_func)

            fig, ax = plt.subplots(figsize=(12, 6))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig)
            
            # 6. 결과 해석 및 단어 빈도 표
            most_common_word = word_counts.most_common(1)[0][0]
            st.markdown(f"""
            <div style="background-color: #d4edda; padding: 20px; border-radius: 10px; border: 1px solid #c3e6cb; color: #155724;">
                ● <b>가장 빈도가 높은 키워드:</b> <span style="font-size: 24px; color: #00A4EF; font-weight: bold;">'{most_common_word}'</span><br>
                ● <b>관심단어 강조:</b> 파란색 단어들은 연구자가 관심갖고 있는 주제이므로 사전에 지정한 색으로 표시되었습니다. (예: {target_words} 등)<br>
                ● <b>의미없는 단어 삭제:</b> 추출된 단어들 중 {exclude_words} 등과 같이 의미없이 반복되는 것들은 사전에 삭제되었습니다. 
            </div>
            """, unsafe_allow_html=True)


            # ---------------------------------------------------------
            # 9-2. [수정] 폭력유형별 출신국가 교차 분석 (상담건수 합계순 정렬)
            # ---------------------------------------------------------
            st.markdown("---")
            st.subheader("📌 폭력유형 × 출신국가별 상담건수 분석")
            st.info("💡 폭력유형과 출신국 선택에 따라 분석값이 연동됨.")
            st.markdown(f"""        
                <p style="margin: 5px 0;"><b>● 대상 국가:</b> <span style="color: #5CC1FF;">{display_countries}</span></p>
                <p style="margin: 5px 0;"><b>● 폭력 유형:</b> <span style="color: #5CC1FF;">{display_types}</span></p>
                <p style="margin: 5px 0;"><b>● 해당 상담건수:</b> <span style="font-size: 18px; font-weight: bold; color: #F1C40F;">{filtered_df['상담번호'].nunique():,}건</span></p>
                <p style="margin: 5px 0;"><b>● 사용된 단어 갯수(중복):</b> <span style="font-size: 18px; font-weight: bold; color: #F1C40F;">{len(word_list):,}개</span></p>
            """, unsafe_allow_html=True)

            # 1. 피벗 테이블 생성 (Unique Count 기반)
            cross_table = filtered_df.pivot_table(
                index='출신국', 
                columns='폭력유형', 
                values='상담번호', 
                aggfunc='nunique', 
                fill_value=0
            )

            # 2-0. [열 정렬] 폭력유형(Column)을 전체 합계가 큰 순서대로 왼쪽부터 정렬
            # 각 열의 합계를 구한 뒤 내림차순으로 열 이름을 정렬합니다.
            col_order = cross_table.sum(axis=0).sort_values(ascending=False).index
            cross_table = cross_table[col_order]

            # 2. [핵심] 행 단위 합계를 계산하여 정렬용 임시 컬럼 생성
            cross_table['합계'] = cross_table.sum(axis=1)

            # 3. '합계' 컬럼을 기준으로 내림차순 정렬 (상담건수 많은 국가가 위로)
            cross_table = cross_table.sort_values(by='합계', ascending=False)

            # 4. 전체 합계(열 단위 합계)를 가장 아래 행에 추가
            # [주의] 정렬 후에 추가해야 '전체 합계' 행이 중간에 섞이지 않습니다.
            cross_table.loc['합계'] = cross_table.sum()

            # 5. 천 단위 콤마 포맷팅 적용
            formatted_cross_table = cross_table.style.format("{:,.0f}")

            # 6. 표의 높이를 데이터 개수에 맞춰 충분히 확보
            # 국가 수(행 개수)에 따라 높이를 계산합니다. 
            # 보통 한 행당 35~40픽셀 정도 잡으면 스크롤 없이 쾌적합니다.
            row_count = len(cross_table)
            dynamic_height = (row_count * 37) + 10 # 행 높이 + 헤더/마진 여유분

            # 7. 교차표 출력
            st.dataframe(
                formatted_cross_table, 
                width=700,       # Browser의 가로폭만큼 늘리려면, 'stretch', 
                height=dynamic_height # 세로 길이를 데이터 양에 맞춰 확장 (스크롤 방지)     # 기존값 400
            )
            st.write("")

            # ---------------------------------------------------------
            # 9-3. [수정] 상담방법별 출신국 교차 분석 (상담건수 합계순 정렬)
            # ---------------------------------------------------------
            st.markdown("---")
            st.subheader("📌 상담방법 × 출신국별 상담건수 분석")
            st.info("💡 폭력유형과 출신국 선택에 따라 분석값이 연동됨.")
            st.markdown(f"""        
                <p style="margin: 5px 0;"><b>● 대상 국가:</b> <span style="color: #5CC1FF;">{display_countries}</span></p>
                <p style="margin: 5px 0;"><b>● 폭력 유형:</b> <span style="color: #5CC1FF;">{display_types}</span></p>
                <p style="margin: 5px 0;"><b>● 해당 상담건수:</b> <span style="font-size: 18px; font-weight: bold; color: #F1C40F;">{filtered_df['상담번호'].nunique():,}건</span></p>
                <p style="margin: 5px 0;"><b>● 사용된 단어 갯수(중복):</b> <span style="font-size: 18px; font-weight: bold; color: #F1C40F;">{len(word_list):,}개</span></p>
            """, unsafe_allow_html=True)

            # 1. 피벗 테이블 생성 (Unique Count 기반)
            cross_table = filtered_df.pivot_table(
                index='출신국', 
                columns='상담방법', 
                values='상담번호', 
                aggfunc='nunique', 
                fill_value=0
            )

            # 2-0. [열 정렬] 폭력유형(Column)을 전체 합계가 큰 순서대로 왼쪽부터 정렬
            # 각 열의 합계를 구한 뒤 내림차순으로 열 이름을 정렬합니다.
            col_order = cross_table.sum(axis=0).sort_values(ascending=False).index
            cross_table = cross_table[col_order]

            # 2. [핵심] 행 단위 합계를 계산하여 정렬용 임시 컬럼 생성
            cross_table['합계'] = cross_table.sum(axis=1)

            # 3. '합계' 컬럼을 기준으로 내림차순 정렬 (상담건수 많은 국가가 위로)
            cross_table = cross_table.sort_values(by='합계', ascending=False)

            # 4. 전체 합계(열 단위 합계)를 가장 아래 행에 추가
            # [주의] 정렬 후에 추가해야 '전체 합계' 행이 중간에 섞이지 않습니다.
            cross_table.loc['합계'] = cross_table.sum()

            # 5. 천 단위 콤마 포맷팅 적용
            formatted_cross_table = cross_table.style.format("{:,.0f}")

            # 6. 표의 높이를 데이터 개수에 맞춰 충분히 확보
            # 국가 수(행 개수)에 따라 높이를 계산합니다. 
            # 보통 한 행당 35~40픽셀 정도 잡으면 스크롤 없이 쾌적합니다.
            row_count = len(cross_table)
            dynamic_height = (row_count * 38) + 5 # 행 높이 + 헤더/마진 여유분

            # 7. 교차표 출력
            st.dataframe(
                formatted_cross_table, 
                width=700,       # Browser의 가로폭만큼 늘리려면, 'stretch', 
                height=dynamic_height # 세로 길이를 데이터 양에 맞춰 확장 (스크롤 방지)     # 기존값 400
            )
            st.write("")

            # ---------------------------------------------------------
            # 9-4. [수정] 의뢰인별 출신국 교차 분석 (상담건수 합계순 정렬)
            # ---------------------------------------------------------
            st.markdown("---")
            st.subheader("📌 의뢰인 × 출신국별 상담건수 분석")
            st.info("💡 폭력유형과 출신국 선택에 따라 분석값이 연동됨.")
            st.markdown(f"""        
                <p style="margin: 5px 0;"><b>● 대상 국가:</b> <span style="color: #5CC1FF;">{display_countries}</span></p>
                <p style="margin: 5px 0;"><b>● 폭력 유형:</b> <span style="color: #5CC1FF;">{display_types}</span></p>
                <p style="margin: 5px 0;"><b>● 해당 상담건수:</b> <span style="font-size: 18px; font-weight: bold; color: #F1C40F;">{filtered_df['상담번호'].nunique():,}건</span></p>
                <p style="margin: 5px 0;"><b>● 사용된 단어 갯수(중복):</b> <span style="font-size: 18px; font-weight: bold; color: #F1C40F;">{len(word_list):,}개</span></p>
            """, unsafe_allow_html=True)

            # 1. 피벗 테이블 생성 (Unique Count 기반)
            cross_table = filtered_df.pivot_table(
                index='출신국', 
                columns='의뢰인', 
                values='상담번호', 
                aggfunc='nunique', 
                fill_value=0
            )

            # 2-0. [열 정렬] 폭력유형(Column)을 전체 합계가 큰 순서대로 왼쪽부터 정렬
            # 각 열의 합계를 구한 뒤 내림차순으로 열 이름을 정렬합니다.
            col_order = cross_table.sum(axis=0).sort_values(ascending=False).index
            cross_table = cross_table[col_order]

            # 2. [핵심] 행 단위 합계를 계산하여 정렬용 임시 컬럼 생성
            cross_table['합계'] = cross_table.sum(axis=1)

            # 3. '합계' 컬럼을 기준으로 내림차순 정렬 (상담건수 많은 국가가 위로)
            cross_table = cross_table.sort_values(by='합계', ascending=False)

            # 4. 전체 합계(열 단위 합계)를 가장 아래 행에 추가
            # [주의] 정렬 후에 추가해야 '전체 합계' 행이 중간에 섞이지 않습니다.
            cross_table.loc['합계'] = cross_table.sum()

            # 5. 천 단위 콤마 포맷팅 적용
            formatted_cross_table = cross_table.style.format("{:,.0f}")

            # 6. 표의 높이를 데이터 개수에 맞춰 충분히 확보
            # 국가 수(행 개수)에 따라 높이를 계산합니다. 
            # 보통 한 행당 35~40픽셀 정도 잡으면 스크롤 없이 쾌적합니다.
            row_count = len(cross_table)
            dynamic_height = (row_count * 38) + 5 # 행 높이 + 헤더/마진 여유분

            # 7. 교차표 출력
            st.dataframe(
                formatted_cross_table, 
                width='stretch',       # Browser의 가로폭만큼 늘리려면, 'stretch'
                height=dynamic_height # 세로 길이를 데이터 양에 맞춰 확장 (스크롤 방지)     # 기존값 400
            )
            st.write("")



            # 10. 사용된 단어 빈도 TOP 100 표 출력 (에러 해결 버전)
            # ---------------------------------------------------------
            st.markdown("---") 
            st.subheader("📋 사용된 단어의 갯수(상위 100개)")
            st.markdown(f"""        
                <p style="margin: 5px 0;"><b>● 대상 국가:</b> <span style="color: #5CC1FF;">{display_countries}</span></p>
                <p style="margin: 5px 0;"><b>● 폭력 유형:</b> <span style="color: #5CC1FF;">{display_types}</span></p>
                <p style="margin: 5px 0;"><b>● 해당 상담건수:</b> <span style="font-size: 18px; font-weight: bold; color: #F1C40F;">{filtered_df['상담번호'].nunique():,}건</span></p>
                <p style="margin: 5px 0;"><b>● 사용된 단어 갯수(중복):</b> <span style="font-size: 18px; font-weight: bold; color: #F1C40F;">{len(word_list):,}개</span></p>
            """, unsafe_allow_html=True)



            # 1. 데이터프레임 생성
            df_top100 = pd.DataFrame(word_counts.most_common(100), columns=['단어', '빈도수(회)'])
            df_top100.index = df_top100.index + 1
            
            # [핵심 수정] 모든 컬럼이 아닌 '빈도수(회)' 컬럼에만 콤마 포맷을 지정합니다.
            # 이렇게 하면 문자열인 '단어' 컬럼은 건드리지 않아 에러가 나지 않습니다.
            formatted_df = df_top100.style.format({
                "빈도수(회)": "{:,}"
            })
            
            st.dataframe(
                formatted_df, 
                width=250,             #  Browser 전체폭만큼 넓히려면, width='stretch', 
                height=735
            )

            # [추가] 최하단 격려 문구 (중간 크기 글자)
            st.write("") # 표와의 간격을 위한 여백
            st.write("") 
            
            # 방법 1: subheader 사용 (가장 표준적인 중간 크기)
            # st.subheader("홧띵~ 🍻")
            
            # 만약 글자를 가운데로 정렬하고 싶으시다면 아래 HTML 방식도 좋습니다.
            st.markdown("<h3 style='text-align: center; color: #2E86C1; font-size:62px; font-weight: bold;'>홧띵~ 🍻</h3>", unsafe_allow_html=True)

        else:
            st.warning("데이터가 존재하지 않습니다.")

    except Exception as e:
        st.error(f"데이터 처리 오류: {e}")
