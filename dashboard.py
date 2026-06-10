import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob

st.set_page_config(page_title="Plant Monitoring", layout="wide")
st.title("🌡️ Plant Temperature Monitoring")

def load_and_combine_data():
    files = glob.glob("*.xlsx")
    data_frames = []
    
    for file in files:
        df = pd.read_excel(file, engine='openpyxl')
        df.columns = df.columns.str.strip()
        data_frames.append(df)
            
    if data_frames:
        combined_df = pd.concat(data_frames, ignore_index=True)
        
        # SMART DETECTION: Find the time column
        time_cols = ['Timestamp', 'Time', 'Date']
        found_time = next((col for col in time_cols if col in combined_df.columns), None)
        
        if found_time:
            combined_df['Timestamp'] = pd.to_datetime(combined_df[found_time])
        else:
            # If no time column, use the first column as time
            combined_df['Timestamp'] = pd.to_datetime(combined_df.iloc[:, 0])
            
        return combined_df.sort_values('Timestamp')
    return None

df = load_and_combine_data()

if df is not None:
    cols = st.columns(3)
    # Ensure these names match your Excel file headers EXACTLY
    coolers = {"Dough Cooler 1": cols[0], "Dough Cooler 2": cols[1]}

    for name, col in coolers.items():
        if name in df.columns:
            val = pd.to_numeric(df[name], errors='coerce').iloc[-1]
            with col:
                st.metric(name, f"{val:.2f}°C" if pd.notnull(val) else "N/A")
                if pd.notnull(val) and val > 5.0:
                    st.error("⚠️ THRESHOLD EXCEEDED")
        else:
            st.warning(f"Column '{name}' missing. Check your Excel headers.")
            st.write("Available columns:", list(df.columns))

    st.subheader("Historical Trends")
    fig = px.line(df.melt(id_vars="Timestamp", var_name="Cooler", value_name="Temperature"), 
                  x="Timestamp", y="Temperature", color="Cooler", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("No data files loaded. Ensure Excel files are in the repository.")
