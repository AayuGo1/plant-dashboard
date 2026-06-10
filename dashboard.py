import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob
from datetime import datetime

# --- PAGE SETUP ---
st.set_page_config(page_title="Plant Temperature Dashboard", layout="wide")
st.title("🌡️ Plant Temperature Monitoring (Multi-Source)")

# --- DYNAMIC DATA LOADING ---
def load_and_combine_data():
    # Automatically finds all .xlsx files in the folder
    files = glob.glob("*.xlsx")
    data_frames = []
    
    for file in files:
        if os.path.exists(file):
            df = pd.read_excel(file, engine='openpyxl')
            # Clean headers to prevent spacing errors
            df.columns = df.columns.str.strip()
            data_frames.append(df)
            
    if data_frames:
        combined_df = pd.concat(data_frames, ignore_index=True)
        
        # Smart detection for time columns
        time_cols = ['Timestamp', 'Time', 'Date']
        found_time = next((col for col in time_cols if col in combined_df.columns), None)
        
        if found_time:
            combined_df['Timestamp'] = pd.to_datetime(combined_df[found_time])
        else:
            combined_df['Timestamp'] = pd.to_datetime(combined_df.iloc[:, 0])
            
        return combined_df.sort_values('Timestamp')
    return None

# --- UI & LOGIC ---
df = load_and_combine_data()

if df is not None:
    # Display Metrics
    cols = st.columns(3)
    coolers = {"Dough Cooler 1": cols[0], "Dough Cooler 2": cols[1]}

    for name, col in coolers.items():
        if name in df.columns:
            # Force numeric, treat errors as NaN
            val = pd.to_numeric(df[name], errors='coerce').iloc[-1]
            with col:
                st.metric(name, f"{val:.2f}°C" if pd.notnull(val) else "N/A")
                # Visual Alert
                if pd.notnull(val) and val > 5.0:
                    st.error("⚠️ THRESHOLD EXCEEDED")
        else:
            st.warning(f"Column '{name}' not found.")

    # Visualization
    st.subheader("Historical Temperature Trends")
    df_melted = df.melt(id_vars="Timestamp", var_name="Cooler", value_name="Temperature")
    fig = px.line(df_melted, x="Timestamp", y="Temperature", color="Cooler", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    # Allow users to see the underlying data structure
    with st.expander("View Raw Data Table"):
        st.dataframe(df)
else:
    st.error("No Excel files found. Please upload your DataLog files to the repository.")
