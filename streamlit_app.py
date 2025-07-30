import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 밀도 계산을 위한 함수 (σ_t)
# UNESCO (1983) 식을 간단화한 근사식
def sigma_t(S, T):
    """
    염분(S, ‰)과 수온(T, °C)으로부터 σ_t(kg/m^3-1000) 계산
    """
    # 순수한 물의 밀도 (25°C 기준) 근사
    rho_w = 999.842594 + 6.793952e-2*T - 9.095290e-3*T**2 + 1.001685e-4*T**3
    # 염분 보정 (단순화된 다항식)
    rho = rho_w + 0.824493*S - 0.0040899*T*S + 0.000076438*T**2*S
    return rho - 1000  # σ_t (1000을 빼서 해양학 표기)

# Streamlit 제목
st.title("수온-염분도(T-S Diagram) 그리기 (등밀도선 포함)")

# 사용법 안내
st.subheader("사용 방법")
st.write("1. CSV 파일을 업로드합니다.")
st.write("2. CSV에는 'Depth', 'Temperature', 'Salinity' 열이 있어야 합니다.")
st.write("3. 수심별로 연결된 T-S 다이어그램과 등밀도선이 표시됩니다.")

# CSV 업로드
uploaded_file = st.file_uploader("CSV 파일 입력 :", type=["csv"])

if uploaded_file is not None:
    # 데이터 읽기
    df = pd.read_csv(uploaded_file)

    # 열 확인
    if all(col in df.columns for col in ['Depth', 'Temperature', 'Salinity']):
        df = df.sort_values(by="Depth")  # 깊이 순 정렬

        # T-S 범위 정의 (등밀도선 계산용)
        S_range = np.linspace(df['Salinity'].min()-0.5, df['Salinity'].max()+0.5, 100)
        T_range = np.linspace(df['Temperature'].min()-1, df['Temperature'].max()+1, 100)
        S_grid, T_grid = np.meshgrid(S_range, T_range)
        sigma_grid = sigma_t(S_grid, T_grid)

        # Matplotlib 그래프 생성
        fig, ax = plt.subplots(figsize=(7,6))

        # 등밀도선(σ_t) 그리기
        cs = ax.contour(S_grid, T_grid, sigma_grid, levels=np.arange(20, 30, 0.5), colors='gray', alpha=0.5)
        ax.clabel(cs, fmt="%.1f", fontsize=8)

        # 데이터 점과 선
        ax.plot(df['Salinity'], df['Temperature'], '-o', color='b', label="Profile")
        for i, row in df.iterrows():
            ax.text(row['Salinity'], row['Temperature'], f"{int(row['Depth'])}m", fontsize=8)

        # 축, 제목 설정
        ax.set_title("T-S Diagram (등밀도선 포함)")
        ax.set_xlabel("염분 (Salinity, ‰)")
        ax.set_ylabel("수온 (Temperature, °C)")
        ax.invert_yaxis()  # 수온 깊이감 표현을 위해 Y축 반전
        ax.grid(True)
        ax.legend()

        # 그래프 출력
        st.pyplot(fig)
    else:
        st.error("CSV 파일에 'Depth', 'Temperature', 'Salinity' 열이 있어야 합니다.")
else:
    st.info("CSV 파일을 업로드하면 T-S 다이어그램이 표시됩니다.")
