import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from deta import Deta

# width configuration, change max_width value
css = '''
<style>
    section.main > div {max-width: 80rem}
</style>
'''
st.markdown(css, unsafe_allow_html=True)

# Connect to Deta Base with your Data Key
deta = Deta(st.secrets["data_key"])
drive = deta.Drive("Bachelorarbeit")

filename = "V1_gesamt.csv"
url = "https://drive.deta.sh/v1/Bachelorarbeit/measured_data/files/download?name={V1_gesamt}"
headers = {"X-Api-Key": st.secrets["data_key"]}
# load data in cache
@st.cache_data
def load_data(name: str) -> pd.DataFrame:
    data = pd.read_csv(url, sep="\t", index_col=[0], storage_optionos = headers)
    return data

dataset = load_data(filename)


# sidebar
st.sidebar.title("Einstellungen")
# Choose test series:
test_series = st.sidebar.selectbox("Choose test series:", ["1", "2", "3"])

# Choose presented data or diagrams
measurements = st.sidebar.multiselect("Choose presented measurements:", [
    "Pressure", "Temperature", "Position", "Flow"])


# dashboard
st.title("Visualize Test Data")
st.write("Streamlit dashboard of measured test data from the press test bench")
st.write("---")

# Chosen test series:
st.write(f"### Test series: &ensp;{test_series}")

max_test_cycle = int(dataset["autoCounter"].iloc[-1])
test_cycle = st.slider("Choose test cycle:", 1, max_test_cycle)


cycle_df = pd.DataFrame(dataset.loc[dataset["autoCounter"] == test_cycle])
time = range(10, cycle_df.shape[0]*10+10, 10)
cycle_df["Time"] = time
# st.write(cycle_df)

st.write("Parameters:")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric(label="Friction [N]", value=cycle_df["F_FrictionStatic"].iloc[1], delta="-1")
col2.metric(label="Cy. int. Leakage [µm]", value=cycle_df["TV2_hi [µm]"].iloc[1], delta="-1")
col3.metric(label="Cy. ext. Leakage [µm]", value=cycle_df["TV3_he [µm]"].iloc[1], delta="-1")
col4.metric(label="Pos. Offset [mm]", value=round(cycle_df["POS1_offset"].iloc[1],4), delta="-1")
col5.metric(label="Ext. Leakage [l/min*bar]", value=round(cycle_df["K_Le [l/min.bar]"].iloc[1],4), delta="-1")

# col1, col2, col3 = st.columns(3)

if "Pressure" in measurements:
    pressure_df = pd.DataFrame(cycle_df[["Time", "i_PS1_filt [Pa]", "i_PS2_filt [Pa]", "i_PS3_filt [Pa]"]])
    pressure_df.rename(columns={"i_PS1_filt [Pa]": "PS1 [bar]", "i_PS2_filt [Pa]": "PS2 [bar]", "i_PS3_filt [Pa]": "PS3 [bar]"}, inplace=True)
    pressure_df["PS1 [bar]"] = pressure_df["PS1 [bar]"] * 1e-5
    pressure_df["PS2 [bar]"] = pressure_df["PS2 [bar]"] * 1e-5
    pressure_df["PS3 [bar]"] = pressure_df["PS3 [bar]"] * 1e-5
    st.line_chart(pressure_df, x = "Time", height=600)

if "Position" in measurements:
    position_df = pd.DataFrame(cycle_df[["Time", "i_POS1_cal [m]"]])
    # position_df.rename(columns={"i_PS1_filt [Pa]": "PS1 [bar]"}, inplace=True)
    st.line_chart(position_df, x = "Time")

if "Flow" in measurements:
    position_df = pd.DataFrame(cycle_df[["Time", "i_FS4_cal_m3/s"]])
    # position_df.rename(columns={"i_PS1_filt [Pa]": "PS1 [bar]"}, inplace=True)
    st.line_chart(position_df, x = "Time")

if "Temperature" in measurements:
    temperature_df = pd.DataFrame(cycle_df[["Time", "i_TS1_cal"]])
    temperature_df["i_TS1_cal"] = temperature_df["i_TS1_cal"] - 273.15
    st.line_chart(temperature_df, x = "Time")






