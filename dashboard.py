import streamlit as st
import pandas as pd
import glob
import os

# Page configuration
st.set_page_config(page_title="Plant Management Dashboard", layout="wide")

# --- Data Loading Functions ---

def get_temp_data():
    files = glob.glob("DataLog_*.csv")
    all_data = []
    target_cols = ['Time', 'Dough Cooler1 Temp', 'Dough Cooler2 Temp', 'Perishable Cooler Temp']
    
    for file in files:
        df = pd.read_csv(file)
        df.columns = df.columns.str.strip()
        if all(col in df.columns for col in target_cols):
            df = df[target_cols].copy()
            for col in target_cols[1:]:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            df['Time'] = pd.to_datetime(df['Time'], errors='coerce')
            all_data.append(df)
            
    return pd.concat(all_data, ignore_index=True).drop_duplicates(subset=['Time']).sort_values(by='Time') if all_data else None

def get_power_data():
    # Sheet 1: Headers are on row 1 (0-indexed)
    try:
        df = pd.read_csv('Power consumption freon.xlsx - Sheet1.csv', header=1)
        return df.dropna(axis=1, how='all')
    except Exception as e:
        return None

def get_runtime_data():
    # Sheet 2: Headers are on row 2
    try:
        df = pd.read_csv('Power consumption freon.xlsx - Sheet2.csv', header=2)
        return df.dropna(axis=1, how='all')
    except Exception as e:
        return None

def get_compressor_data():
    # Sheet 3: Headers are on row 2
    try:
        df = pd.read_csv('Power consumption freon.xlsx - Sheet3.csv', header=2)
        return df.dropna(axis=1, how='all')
    except Exception as e:
        return None

# --- Main Dashboard ---

st.title("Plant Management Dashboard")

# Add a directory check in case files aren't found
if not os.path.exists('Power consumption freon.xlsx - Sheet1.csv'):
    st.error("Data files not found in the working directory. Please ensure all CSV files are in the same folder as app.py.")

tab1, tab2, tab3 = st.tabs(["Temperature Monitor", "Power Consumption", "Run Time & Compressors"])

with tab1:
    st.subheader("Real-Time Temperature")
    data = get_temp_data()
    if data is not None:
        latest = data.iloc[-1]
        c1, c2, c3 = st.columns(3)
        c1.metric("Dough Cooler 1", f"{latest['Dough Cooler1 Temp']:.2f}°C")
        c2.metric("Dough Cooler 2", f"{latest['Dough Cooler2 Temp']:.2f}°C")
        c3.metric("Perishable Cooler", f"{latest['Perishable Cooler Temp']:.2f}°C")
        st.line_chart(data.set_index('Time'))
    else:
        st.warning("Temperature data not available.")

with tab2:
    st.subheader("Power Consumption")
    p_data = get_power_data()
    if p_data is not None:
        st.dataframe(p_data, use_container_width=True)
    else:
        st.error("Power Consumption file not found or empty.")

with tab3:
    st.subheader("Cold Storage Run Time")
    r_data = get_runtime_data()
    if r_data is not None:
        st.dataframe(r_data, use_container_width=True)
    
    st.subheader("Compressor Status")
    c_data = get_compressor_data()
    if c_data is not None:
        st.dataframe(c_data, use_container_width=True)
