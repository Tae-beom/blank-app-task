import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# σₜ (밀도 이상) 계산 함수
# 염분(S, PSU)과 수온(T, °C)으로 σₜ 값을 계산
# 해양학에서 사용되는 밀도 공식(UNESCO 1983)을 단순화한 버전
def sigma_t(S, T):
    rho_w = 999.842594 + 6.793952e-2*T - 9.095290e-3*T**2 + 1.001685e-4*T**3
    rho = rho_w + 0.824493*S - 0.0040899*T*S + 0.000076438*T**2*S
    return rho - 1000  # σₜ 값 반환 (밀도-1000)

# Streamlit 앱 제목
st.title("T-S Diagram")

# 사용 방법 안내 (한글)
st.subheader("사용 방법")
st.write("1. CSV 파일을 업로드합니다.")
st.write("2. CSV에는 'Depth', 'Temperature', 'Salinity' 열이 있어야 합니다.")
st.write("3. 업로드 후, 수심별로 연결된 T-S 다이어그램과 등밀도선이 표시됩니다.")

# CSV 파일 업로드
uploaded_file = st.file_uploader("CSV 파일 업로드:", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # 열 이름을 모두 소문자로 변환하여 대소문자 문제 해결
    df.columns = [c.strip().lower() for c in df.columns]

    # 필수 열이 있는지 확인
    if all(col in df.columns for col in ['depth', 'temperature', 'salinity']):
        # 깊이 기준으로 데이터 정렬 (깊이에 따라 순서대로 연결되도록)
        df = df.sort_values(by='depth')

        # 등밀도선(σₜ) 계산을 위한 격자 생성
        S_range = np.linspace(df['salinity'].min()-0.5, df['salinity'].max()+0.5, 100)
        T_range = np.linspace(df['temperature'].min()-1, df['temperature'].max()+1, 100)
        S_grid, T_grid = np.meshgrid(S_range, T_range)
        sigma_grid = sigma_t(S_grid, T_grid)

        # Matplotlib으로 그래프 생성
        fig, ax = plt.subplots(figsize=(7, 6))

        # 등밀도선 그리기 (회색 선)
        cs = ax.contour(S_grid, T_grid, sigma_grid,
                        levels=np.arange(20, 30, 0.5),
                        colors='gray', alpha=0.5)
        ax.clabel(cs, fmt="%.1f", fontsize=8)

        # 수심별 데이터 점과 연결선 표시
        ax.plot(df['salinity'], df['temperature'], '-o', color='b', label="Profile")

        # 각 점에 수심 레이블 추가
        for _, row in df.iterrows():
            ax.text(row['salinity'], row['temperature'], f"{int(row['depth'])}m", fontsize=8)

        # 그래프 제목과 축 레이블 (영어로 표시)
        ax.set_title("Temperature-Salinity (T-S) Diagram with Isopycnals")
        ax.set_xlabel("Salinity (PSU)")
        ax.set_ylabel("Temperature (°C)")

        # Y축을 뒤집지 않음 (위쪽이 높은 수온, 아래쪽이 낮은 수온)
        ax.grid(True)
        ax.legend()

        # Streamlit에 그래프 출력
        st.pyplot(fig)
    else:
        st.error("CSV 파일에 'Depth', 'Temperature', 'Salinity' 열이 필요합니다. (대소문자 무관)")
else:
    st.info("CSV 파일을 업로드하면 T-S 다이어그램이 표시됩니다.")
