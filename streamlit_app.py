import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import itertools
import os

# 📌 NanumGothic 폰트 설정
FONT_PATH = os.path.join("font", "NanumGothic.ttf")
if os.path.exists(FONT_PATH):
    nanum_font = fm.FontProperties(fname=FONT_PATH)
    plt.rcParams['font.family'] = nanum_font.get_name()  # 전역 설정만 사용
else:
    nanum_font = None
    st.warning("한글 폰트 파일(font/NanumGothic.ttf)을 찾을 수 없습니다. 일부 글자가 깨질 수 있습니다.")

# 해수 밀도 계산 함수 (ρ, kg/m³)
def seawater_density(S, T):
    rho_w = 999.842594 + 6.793952e-2 * T - 9.095290e-3 * T**2 + 1.001685e-4 * T**3
    rho = rho_w + 0.824493 * S - 0.0040899 * T * S + 0.000076438 * T**2 * S
    return rho

# 📊 Streamlit 앱
st.title("수온-염분도 (T-S Diagram)")

st.subheader("사용 방법")
st.markdown("""
1. 해양자료센터에서 받은 파일에서 깊이, 수온, 염분 자료만을 복사하여 CSV 파일 만듭니다.  
2. 제작된 파을을 업로드하세요. 여러 파일을 업로드하여 비교도 가능합니다.
""")

uploaded_files = st.file_uploader("CSV 파일 업로드", type=["csv"], accept_multiple_files=True)

if uploaded_files:
    data_list = []

    for file in uploaded_files:
        try:
            df = pd.read_csv(file)
            column_mapping = {col.strip().lower(): col for col in df.columns}
            required = ['depth', 'temperature', 'salinity']

            if all(key in column_mapping for key in required):
                depth_col = column_mapping['depth']
                temp_col = column_mapping['temperature']
                sal_col = column_mapping['salinity']

                df = df[[depth_col, temp_col, sal_col]].rename(columns={
                    depth_col: 'depth',
                    temp_col: 'temperature',
                    sal_col: 'salinity'
                })
                df = df.sort_values(by='depth')
                data_list.append((file.name, df))
            else:
                st.warning(f"'{file.name}' 파일에는 'Depth', 'Temperature', 'Salinity' 열이 모두 있어야 합니다.")
        except Exception as e:
            st.error(f"'{file.name}' 읽기 실패: {e}")

    if data_list:
        all_sal = pd.concat([df['salinity'] for _, df in data_list])
        all_temp = pd.concat([df['temperature'] for _, df in data_list])

        S_range = np.linspace(all_sal.min() - 0.5, all_sal.max() + 0.5, 100)
        T_range = np.linspace(all_temp.min() - 1, all_temp.max() + 1, 100)
        S_grid, T_grid = np.meshgrid(S_range, T_range)

        rho_grid = seawater_density(S_grid, T_grid)
        sg_grid = rho_grid / 1000  # 비중

        min_sg = np.floor(sg_grid.min() * 1000) / 1000
        max_sg = np.ceil(sg_grid.max() * 1000) / 1000
        levels = np.arange(min_sg, max_sg + 0.001, 0.001)

        fig, ax = plt.subplots(figsize=(8, 6))

        # 등비중선 등고선
        cs = ax.contour(S_grid, T_grid, sg_grid,
                        levels=levels,
                        colors='gray', alpha=0.5)
        ax.clabel(cs, fmt="%.3f", fontsize=8)  # ❗ fontproperties 넣지 마!

        color_cycle = itertools.cycle(plt.rcParams['axes.prop_cycle'].by_key()['color'])

        for filename, df in data_list:
            color = next(color_cycle)
            ax.plot(df['salinity'], df['temperature'], '-o', label=filename, color=color)

            for _, row in df.iterrows():
                ax.text(row['salinity'], row['temperature'],
                        f"{int(row['depth'])}m",
                        fontsize=8, color=color,
                        fontproperties=nanum_font)

        ax.set_title("수온-염분도", fontproperties=nanum_font)
        ax.set_xlabel("염분 (PSU)", fontproperties=nanum_font)
        ax.set_ylabel("수온 (°C)", fontproperties=nanum_font)
        ax.grid(True)
        ax.legend(prop=nanum_font)

        st.pyplot(fig)
else:
    st.info("CSV 파일을 업로드하면 다중 T-S 다이어그램이 표시됩니다.")
