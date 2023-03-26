import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from deta import Deta

# ----------------------------------------------------------------
# Constants/Parameters
# ----------------------------------------------------------------

error_thresholds = {"F_FrictionStatic": 1500, 
                    "TV2_hi [µm]": 25, 
                    "TV3_he [µm]": 20,
                    "POS1_offset": 1,
                    "K_Le [l/min.bar]": 0.0005}

# ----------------------------------------------------------------
# Streamlit style configuration
# ----------------------------------------------------------------

# width configuration, change max_width value
css = '''
<style>
    section.main > div {max-width: 80rem}
</style>
'''
st.markdown(css, unsafe_allow_html=True)

# ----------------------------------------------------------------
# Load data method
# ----------------------------------------------------------------

url = "https://drive.deta.sh/v1/a0fgji9w6tz/measured_data/files/download?name=" # name of the file has to be added to the url
headers = {"X-Api-Key": st.secrets["data_key"]}

# load data in cache
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    data = pd.read_csv(path, sep="\t", index_col=[0], storage_options = headers)
    return data


#----------------------------------------------------------------
# Streamlit dashboard
# ----------------------------------------------------------------

### sidebar

st.sidebar.title("Einstellungen")
# Choose test series:
test_series = st.sidebar.selectbox("Choose test series:", list(range(1,7)))
# load dataset
dataset = load_data(f"{url}V{test_series}_data.csv")

# Choose presented data or diagrams
measurements = st.sidebar.multiselect("Choose presented measurements:", [
    "Pressure", "Position", "Flow", "Temperature"])

st.sidebar.write("---")
st.sidebar.write("Error threshholds:")
for key, value in error_thresholds.items():
    st.sidebar.write(f"{key}: {value}")


### dashboard

st.title("Visualize Test Data")
st.write("Streamlit dashboard of measured test data from the press test bench. For further controls open the sidebar on the left.")
st.write("---")

# Chosen test series:
st.write(f"### Test series: &ensp;{test_series}")

# slider for choosing which test cycle is going to be displayed
max_test_cycle = int(dataset["autoCounter"].iloc[-1])
test_cycle = st.slider("Choose test cycle:", 1, max_test_cycle)

# creating dataframe of chosen test cycle from the dataset
cycle_df = pd.DataFrame(dataset.loc[dataset["autoCounter"] == test_cycle])
time = range(10, cycle_df.shape[0]*10+10, 10)
cycle_df["Time"] = time

### Diyplay the error parameters of the chosen test cycle

# checking which parameter is above its error threshold
error_check = []
for key, value in error_thresholds.items():
    if cycle_df[key].iloc[1] > value:
        error_check.append(":red[Error]")
    else:
        error_check.append(":green[Good]")

st.write("#### Error parameters:")
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric(label="Friction [N]", value=round(cycle_df["F_FrictionStatic"].iloc[1], 2))
    st.write(error_check[0])
with col2:
    st.metric(label="Cy. int. Leakage [µm]", value=round(cycle_df["TV2_hi [µm]"].iloc[1], 2))
    st.write(error_check[1])
with col3:
    st.metric(label="Cy. ext. Leakage [µm]", value=round(cycle_df["TV3_he [µm]"].iloc[1], 2))
    st.write(error_check[2])
with col4:
    st.metric(label="Pos. Offset [mm]", value=round(cycle_df["POS1_offset"].iloc[1],4))
    st.write(error_check[3])
with col5:
    st.metric(label="Ext. Leakage [l/min*bar]", value=round(cycle_df["K_Le [l/min.bar]"].iloc[1],4))
    st.write(error_check[4])

"---"

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