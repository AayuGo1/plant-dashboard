import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

st.set_page_config(page_title="Plant Monitoring", layout="wide")
st.title("🌡️ Plant Temperature Monitoring (Multi-Source)")

# --- DATA LOADING (Multiple Files) ---
def load_and_combine_data():
    files = ['plant_data_1.xlsx', 'plant_data_2.xlsx']
    data_frames = []
    
    for file in files:
        if os.path.exists(file):
            df = pd.read_excel(file, engine='openpyxl')
            df.columns = df.columns.str.strip()
            data_frames.append(df)
            
    if data_frames:
        # Combine all files into one master list
        combined_df = pd.concat(data_frames, ignore_index=True)
        combined_df['Timestamp'] = pd.to_datetime(combined_df['Timestamp'])
        return combined_df.sort_values('Timestamp')
    else:
        st.error("No data files found!")
        return None

# --- LOGGING FUNCTION ---
def log_alarm(name, temp):
    with open("alarm_log.txt", "a") as f:
        f.write(f"{datetime.now()}: {name} exceeded limit at {temp:.2f}°C\n")

# --- UI & LOGIC ---
df = load_and_combine_data()

if df is not None:
    # Display the raw data in a table
    with st.expander("View Raw Data"):
        st.dataframe(df)

    # Metrics
    cols = st.columns(3)
    coolers = {"Dough Cooler 1": cols[0], "Dough Cooler 2": cols[1]}

    for name, col in coolers.items():
        if name in df.columns:
            val = pd.to_numeric(df[name], errors='coerce').iloc[-1]
            with col:
                st.metric(name, f"{val:.2f}°C" if pd.notnull(val) else "N/A")
                if pd.notnull(val) and val > 5.0:
                    st.error("⚠️ THRESHOLD EXCEEDED")
                    log_alarm(name, val)

    # Visualization
    st.subheader("Historical Trends (Combined Files)")
    df_melted = df.melt(id_vars="Timestamp", var_name="Cooler", value_name="Temperature")
    fig = px.line(df_melted, x="Timestamp", y="Temperature", color="Cooler", template="plotly_dark")
    fig.update_yaxes(range=[-5, 15])
    st.plotly_chart(fig, use_container_width=True)

    if st.button("Refresh Dashboard"):
        st.rerun()
