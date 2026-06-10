import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import glob

# --- PAGE SETUP ---
st.set_page_config(page_title="Plant Monitoring", layout="wide")
st.title("🌡️ Plant Temperature Monitoring")

# --- DATA LOADING (Dynamic) ---
def load_and_combine_data():
    # Automatically find all .xlsx files in the current directory
    files = glob.glob("*.xlsx")
    data_frames = []
    
    for file in files:
        df = pd.read_excel(file, engine='openpyxl')
        df.columns = df.columns.str.strip() # Remove spaces from headers
        data_frames.append(df)
            
    if data_frames:
        combined_df = pd.concat(data_frames, ignore_index=True)
        # Ensure Timestamp is handled correctly
        combined_df['Timestamp'] = pd.to_datetime(combined_df['Timestamp'])
        return combined_df.sort_values('Timestamp')
    else:
        return None

# --- UI & LOGIC ---
df = load_and_combine_data()

if df is not None:
    # Display the last available readings
    cols = st.columns(3)
    # Using 'Dough Cooler 1' and 'Dough Cooler 2' as keys
    coolers = {"Dough Cooler 1": cols[0], "Dough Cooler 2": cols[1]}

    for name, col in coolers.items():
        if name in df.columns:
            # Get the most recent value
            val = pd.to_numeric(df[name], errors='coerce').iloc[-1]
            with col:
                st.metric(name, f"{val:.2f}°C" if pd.notnull(val) else "N/A")
                if pd.notnull(val) and val > 5.0:
                    st.error("⚠️ THRESHOLD EXCEEDED")
        else:
            st.error(f"Column '{name}' not found in data.")

    # Visualization
    st.subheader("Historical Temperature Trends")
    df_melted = df.melt(id_vars="Timestamp", var_name="Cooler", value_name="Temperature")
    fig = px.line(df_melted, x="Timestamp", y="Temperature", color="Cooler", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No Excel files found in the repository. Please upload your DataLog files.")
