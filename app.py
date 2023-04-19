import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
from deta import Deta

# --- CONSTANTS/PARAMETERS ---

rename_dict = {"i_POS1_cal [m]": "position",
               "i_FS4_cal_m3/s": "flow FS4",
               "i_PS1_filt [Pa]": "pressure PS1",
               "i_PS2_filt [Pa]": "pressure PS2",
               "i_PS3_filt [Pa]": "pressure PS3",
               "loadF": "load",
               "i_TS1_cal": "temp T1",
               "sv_compressionLength": "compression length [mm]",
               "F_FrictionStatic": "friction [N]",
               "TV2_hi [µm]": "Cy. int. leakage [µm]",
               "TV3_he [µm]": "Cy. ext. leakage [µm]",
               "POS1_offset": "position offset [mm]",
               "K_Le [l/min.bar]": "ext. leakage [l/min.bar]"
                }

type_dict = {"autoCounter": "int16",
             "o_SV1": "int8",
             "o_SV2": "int8",
             "compression length [mm]": "int8",
            }  

error_thresholds = {"friction [N]": 1500, 
                    "Cy. int. leakage [µm]": 25, 
                    "Cy. ext. leakage [µm]": 20,
                    "position offset [mm]": 1,
                    "ext. leakage [l/min.bar]": 0.0005} 


# --- STREAMLIT CONFIGURATION ---

# width configuration, change max_width value
css = '''
<style>
    section.main > div {max-width: 80rem}
</style>
'''
st.markdown(css, unsafe_allow_html=True)


# --- LOAD DATA ---

url = "https://drive.deta.sh/v1/a0fgji9w6tz/measured_data/files/download?name=" # name of the file has to be added to the url
headers = {"X-Api-Key": st.secrets["data_key"]}

# load data in cache
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    data = pd.read_csv(path, sep="\t", index_col=[0], storage_options = headers)
    # manipulate dataset for easier handling, unit and dtype conversion
    # unnecessary columns
    data.drop(columns=["Ventilueberdeckung [%]", "sv_loadLength"], inplace=True)
    # renaming columns
    data.rename(columns=rename_dict, inplace=True)
    for key, value in type_dict.items():
        data[key] = data[key].astype(value)
    # timestamp nm to ms
    data["Timestamp UTC"] = (data["Timestamp UTC"].values*1e-6)
    data["Timestamp UTC"] = data["Timestamp UTC"].round()
    # position m to mm
    data["position"] = data["position"].values*1e3
    # pressure Pa to bar
    for i in range(3):
        data[f"pressure PS{i+1}"] = data[f"pressure PS{i+1}"].values*1e-5
        data[f"pressure PS{i+1}"] = data[f"pressure PS{i+1}"].round(4)
    return data


# --- STREAMLIT DASHBOARD ---

### sidebar

st.sidebar.title("Einstellungen")
# Choose test series:
test_series = st.sidebar.selectbox("Choose test series:", list(range(1,7)))
# load dataset
dataset = load_data(f"{url}V{test_series}_data.csv")

st.sidebar.write("---")
st.sidebar.write("#### Error thresholds:")
error_threshold_df = pd.DataFrame.from_dict(error_thresholds, columns=["value"], orient="index")
error_threshold_df.index.name="Error"
st.sidebar.dataframe(error_threshold_df, use_container_width=True)


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

# adding time column
start_time = cycle_df["Timestamp UTC"].iloc[0]
cycle_df["time"] = cycle_df["Timestamp UTC"].apply(lambda x: x - start_time)

# with st.expander("Click to see dataframe"):
#     st.write(cycle_df)

### Diyplay the error parameters of the chosen test cycle

# checking which parameter is above its error threshold
error_check = []
for key, value in error_thresholds.items():
    if cycle_df[key].iloc[0] > value:
        error_check.append(":red[Error]")
    else:
        error_check.append(":green[Good]")

st.write("#### Error parameters:")
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric(label="Friction [N]", value=round(cycle_df["friction [N]"].iloc[0], 2))
    st.write(error_check[0])
with col2:
    st.metric(label="Cy. int. Leakage [µm]", value=round(cycle_df["Cy. int. leakage [µm]"].iloc[0], 2))
    st.write(error_check[1])
with col3:
    st.metric(label="Cy. ext. Leakage [µm]", value=round(cycle_df["Cy. ext. leakage [µm]"].iloc[0], 2))
    st.write(error_check[2])
with col4:
    st.metric(label="Pos. Offset [mm]", value=round(cycle_df["position offset [mm]"].iloc[0],4))
    st.write(error_check[3])
with col5:
    st.metric(label="Ext. Leakage [l/min*bar]", value=round(cycle_df["ext. leakage [l/min.bar]"].iloc[0],4))
    st.write(error_check[4])

"---"

# Choose presented data or diagrams
measurements = st.multiselect("Choose presented measurements:", [
    "PS1", "PS2", "PS3", "Position", "Flow"])

axes = []
time_domain = cycle_df["time"].iloc[-1]

ps1_bool = "PS1" in measurements
ps2_bool = "PS2" in measurements
ps3_bool = "PS3" in measurements

if ps1_bool or ps2_bool or ps3_bool:
    pressure_df = pd.DataFrame([])
    pressure_df["time"] = cycle_df["time"]
    if "PS1" in measurements:
        pressure_df["PS1"] = cycle_df["pressure PS1"]
    if "PS2" in measurements:
        pressure_df["PS2"] = cycle_df["pressure PS2"]
    if "PS3" in measurements:
        pressure_df["PS3"] = cycle_df["pressure PS3"]
    # melt dataframe
    if len(pressure_df.columns) > 1:
        melted = pd.melt(pressure_df, id_vars='time', var_name="Pressure", value_name='value')


    y1_axis = alt.Chart(melted).mark_line().encode(
        x=alt.X("time", axis=alt.Axis(title='Time [ms]', titleY=40), scale=alt.Scale(domain=(0,time_domain))),
        y=alt.Y("value", axis=alt.Axis(title='Pressure [bar]'), scale=alt.Scale(domain=(0,220))),
        color = alt.Color("Pressure", legend=alt.Legend(orient="left"), title="")
    )
    axes.append(y1_axis)

if "Position" in measurements:
    position_df = pd.melt(cycle_df[["time", "position"]], id_vars="time", var_name="Position", value_name="value")
    y2_axis = alt.Chart(position_df).mark_line().encode(
        x=alt.X("time", axis=alt.Axis(title='Time [ms]', titleY=40), scale=alt.Scale(domain=(0,time_domain))),
        y=alt.Y("value", axis=alt.Axis(title='Position [mm]'), scale=alt.Scale(domain=(0,400))),
        color = alt.Color("Position")
    )
    axes.append(y2_axis)

if "Flow" in measurements:
    flow_df = pd.melt(cycle_df[["time", "flow FS4"]], id_vars="time", var_name="Flow", value_name="value")
    y3_axis = alt.Chart(flow_df).mark_line(color="purple").encode(
        x=alt.X("time", axis=alt.Axis(title='Time [ms]', titleY=40), scale=alt.Scale(domain=(0,time_domain))),
        y=alt.Y("value", axis=alt.Axis(title='Flow [l/min*bar]', offset = 60), scale=alt.Scale(domain=(0,0.0005))),
        color = alt.Color("Flow")
    )
    axes.append(y3_axis)

if len(axes) > 0:
    chart = alt.layer(*(axes)).resolve_scale(
        y='independent'
    ).interactive(bind_y=False).properties(height=480)

    st.altair_chart(chart, use_container_width=True)

if test_series == 3:
    st.write("Hallo das ist ein Test")
