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
    plt.rcParams['font.family'] = nanum_font.get_name()
else:
    nanum_font = None
    st.warning("한글 폰트 파일(font/NanumGothic.ttf)을 찾을 수 없습니다. 일부 글자가 깨질 수 있습니다.")

# 해수 밀도 계산 함수 (ρ, kg/m³)
def seawater_density(S, T):
    rho_w = 999.842594 + 6.793952e-2 * T - 9.095290e-3 * T**2 + 1.001685e-4 * T**3
    rho = rho_w + 0.824493 * S - 0.0040899 * T * S + 0.000076438 * T**2 * S
    return rho

# 📥 파일을 읽어 DataFrame으로 반환 (확장자에 따라 분기)
def read_uploaded_file(file):
    """업로드된 파일의 확장자에 따라 CSV 또는 Excel로 읽어 DataFrame 반환"""
    filename = file.name.lower()

    if filename.endswith(".csv"):
        # CSV 파일
        return pd.read_csv(file)

    elif filename.endswith((".xlsx", ".xls")):
        # Excel 파일 - 시트가 여러 개일 수 있으므로 처리
        xls = pd.ExcelFile(file)
        if len(xls.sheet_names) == 1:
            return pd.read_excel(xls, sheet_name=xls.sheet_names[0])
        else:
            # 시트가 여러 개일 경우 사용자가 선택
            sheet = st.selectbox(
                f"'{file.name}' 파일에서 사용할 시트를 선택하세요.",
                xls.sheet_names,
                key=f"sheet_{file.name}"
            )
            return pd.read_excel(xls, sheet_name=sheet)
    else:
        raise ValueError("지원하지 않는 파일 형식입니다. (csv, xlsx, xls 만 가능)")


# 📊 Streamlit 앱
st.title("수온-염분도 (T-S Diagram)")

st.markdown("""
#### 사용 방법

1. 해양자료센터에서 받은 파일에서 **깊이(Depth)**, **수온(Temperature)**, **염분(Salinity)** 자료만을 복사하여
   **CSV (.csv)** 또는 **엑셀 (.xlsx, .xls)** 파일을 만듭니다.  
   (열 이름은 `Depth`, `Temperature`, `Salinity`로 지정하며, **대소문자는 무관**합니다.)  
2. 제작된 파일을 업로드하세요. **여러 파일을 동시에 업로드하여 비교**도 가능합니다.
3. 엑셀 파일에 시트가 여러 개인 경우, 사용할 시트를 선택할 수 있습니다.
""")

# ✅ CSV + Excel 업로드 지원
uploaded_files = st.file_uploader(
    "CSV 또는 Excel 파일 업로드",
    type=["csv", "xlsx", "xls"],
    accept_multiple_files=True
)

if uploaded_files:
    data_list = []

    for file in uploaded_files:
        try:
            df = read_uploaded_file(file)   # ⭐ 확장자에 따라 자동 분기
            column_mapping = {str(col).strip().lower(): col for col in df.columns}
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

                # 숫자형으로 변환하면서 결측치 제거 (엑셀에 빈 셀이 있을 수 있음)
                df = df.apply(pd.to_numeric, errors='coerce').dropna()
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
        ax.clabel(cs, fmt="%.3f", fontsize=8)

        color_cycle = itertools.cycle(plt.rcParams['axes.prop_cycle'].by_key()['color'])

        for filename, df in data_list:
            color = next(color_cycle)
            ax.plot(df['salinity'], df['temperature'], '-o', label=filename, color=color)

            for _, row in df.iterrows():
                ax.annotate(
                    f"{int(row['depth'])}m",
                    xy=(row['salinity'], row['temperature']),
                    xytext=(6, 2),
                    textcoords='offset points',
                    fontsize=8, color=color,
                    fontproperties=nanum_font
                )

        ax.set_title("수온-염분도", fontproperties=nanum_font)
        ax.set_xlabel("염분 (PSU)", fontproperties=nanum_font)
        ax.set_ylabel("수온 (°C)", fontproperties=nanum_font)
        ax.grid(True)
        ax.legend(prop=nanum_font)

        st.pyplot(fig)
else:
    st.info("CSV 또는 Excel 파일을 업로드하면 다중 T-S 다이어그램이 표시됩니다.")
