import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from collections import Counter

# 1. 페이지 설정
st.set_page_config(page_title="이주여성폭력 통합 분석 대시보드", layout="wide")

# 2. 제목 및 정보
st.title("📊 폭력유형 및 출신국별 상담 키워드 분석")
st.subheader('Libra Lab | M&E Center, Ajou')
st.markdown("---")

# 3. 데이터 로드
file_path = "상담데이터_WordString.xlsx"

@st.cache_data
def load_data():
    df = pd.read_excel(file_path, engine='openpyxl')
    return df

try:
    df = load_data()
    
    # 기초 리스트 생성
    all_types = df['폭력유형'].unique().tolist()
    all_countries = df['출신국'].value_counts().index.tolist()
    total_country_count = len(all_countries) # 전체 국가 수

    # ---------------------------------------------------------
    # 4. 사이드바 다중 슬라이서 (Default: 빈 리스트)
    # ---------------------------------------------------------
    st.sidebar.header("🔍 분석 필터 설정")
    st.sidebar.info("💡 아래에서 선택하셔요.")
    
    # [필터 1] 폭력유형 (Multi-select)
    selected_types = st.sidebar.multiselect(
        "📂 폭력 유형 선택 (복수선택 가능):",
        options=all_types
    )
    
    # [필터 2] 출신국 (Multi-select)
    selected_countries = st.sidebar.multiselect(
        "🌍 출신국 선택 (복수선택 가능):",
        options=all_countries
    )

    # 5. 선택 상태에 따른 데이터 필터링 로직 (Default 처리)
    # ---------------------------------------------------------
    filtered_df = df.copy()

    # 폭력유형 필터 적용
    if selected_types:
        filtered_df = filtered_df[filtered_df['폭력유형'].isin(selected_types)]
        display_types = ", ".join(selected_types)
    else:
        display_types = "전체 유형"

    # 출신국 필터 적용
    if selected_countries:
        filtered_df = filtered_df[filtered_df['출신국'].isin(selected_countries)]
        display_country_count = len(selected_countries)
    else:
        display_country_count = total_country_count # 미선택 시 전체 국가 수 표시

    dataset = filtered_df[['WordString']].drop_duplicates()

    # 6. 상단 설명 박스 (동적 수치 반영)
    st.markdown(f"""
    <div style="background-color: #2E86C1; padding: 20px; border-radius: 10px;">   
    <h4 style="color: white; margin-top: 0;">📋 분석 범위: "{display_types}"</h4>   
    <p style="color: white; line-height: 1.6;">
        <b>- 분석 대상:</b> {display_country_count}개 국가 출신 이주여성의 "{display_types}" 상담 데이터 (총 {len(dataset)}건)<br>
        <b>- 분석 방법:</b> 이주여성의 상담 내용 중 키워드(명사)를 추출하여 그 빈도를 시각화하였습니다.<br>
        <b>- 특징:</b> 슬라이서의 선택에 따라 Word Cloud와 Output을 자동으로 Update합니다.
    </p>
    </div>
    """, unsafe_allow_html=True)

    st.write("")

    # 7. 워드클라우드 분석 로직
    exclude_words = ['신고', '요청', '문의', '선생님']
    all_words = " ".join(dataset['WordString'].astype(str).dropna()).split()
    word_list = [w for w in all_words if w not in exclude_words]
    word_counts = Counter(word_list)

    # 8. 시각화 및 출력
    if word_counts:
        target_words = ['남편', '경찰', '폭력', '피해']
        def my_color_func(word, **kwargs):
            return "rgb(0,164,239)" if word in target_words else "rgb(150, 150, 150)"

        wordcloud = WordCloud(
            font_path='MALGUN.TTF',
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
        <div style="background-color: #d4edda; border-color: #c3e6cb; padding: 20px; border-radius: 10px; border: 1px solid #c3e6cb; color: #155724;">
            <p style="margin-bottom: 10px;">현재 선택(또는 전체) 조건 하에서의 위기 신호 분석 결과입니다.</p>
            <ul style="list-style-type: none; padding-left: 0;">
                <li style="margin-bottom: 8px;">
                    ● <b>가장 빈도가 높은 키워드:</b> 
                    <span style="font-size: 28px; color: #00A4EF; font-weight: bold; border-bottom: 3px solid #00A4EF; margin-left: 5px;">
                        '{most_common_word}'
                    </span>
                </li>
                <li style="margin-bottom: 8px;">
                    ● <b>위기 징후 알림:</b> <i>파란색으로 강조된 단어({', '.join(target_words)})들은</i> 긴급 개입 신호로 분류됩니다.
                </li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.warning("데이터가 존재하지 않습니다. 필터 조건을 확인해 주세요.")

except Exception as e:
    st.error(f"데이터 처리 오류: {e}")
