import streamlit as st
import pandas as pd
import glob

# Page configuration
st.set_page_config(page_title="Plant Management Dashboard", layout="wide")

# --- Helper Functions ---

def get_temp_data():
    files = glob.glob("DataLog_*.csv")
    all_data = []
    target_cols = ['Time', 'Dough Cooler2 Temp', 'Dough Cooler1 Temp', 'Perishable Cooler Temp']
    
    for file in files:
        df = pd.read_csv(file)
        df.columns = df.columns.str.strip()
        
        if all(col in df.columns for col in target_cols):
            df = df[target_cols].copy()
            # Convert to numeric, handle 'NOP' as NaN, then forward fill
            for col in target_cols[1:]:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                df[col] = df[col].ffill() 
                
            # Parse time correctly
            df['Time'] = pd.to_datetime(df['Time'], errors='coerce', dayfirst=False)
            all_data.append(df)
            
    if not all_data: return None
    return pd.concat(all_data, ignore_index=True).drop_duplicates(subset=['Time']).sort_values(by='Time')

def get_power_data():
    # Sheet 1: Headers are on row 1
    try:
        df = pd.read_csv('Power consumption freon.xlsx - Sheet1.csv', header=1)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df.dropna(axis=1, how='all')
    except: return None

def get_runtime_data():
    # Sheet 2: Headers are on row 2
    try:
        df = pd.read_csv('Power consumption freon.xlsx - Sheet2.csv', header=2)
        # Runtime date column is the first one
        df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
        return df.dropna(axis=1, how='all')
    except: return None

def get_compressor_data():
    # Sheet 3: Headers are on row 2
    try:
        df = pd.read_csv('Power consumption freon.xlsx - Sheet3.csv', header=2)
        df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
        return df.dropna(axis=1, how='all')
    except: return None

# --- Main Interface ---

st.title("Plant Management Dashboard")

tab1, tab2, tab3 = st.tabs(["Temperature Monitor", "Power Consumption", "Run Time & Compressors"])

with tab1:
    st.subheader("Temperature Trends (June 2026)")
    data = get_temp_data()
    if data is not None:
        st.line_chart(data.set_index('Time'))
    else:
        st.warning("Temperature data not found.")

with tab2:
    st.subheader("Power Consumption")
    p_data = get_power_data()
    if p_data is not None:
        st.dataframe(p_data, use_container_width=True)
    else:
        st.error("Power Consumption data missing.")

with tab3:
    st.subheader("Cold Storage Run Time")
    r_data = get_runtime_data()
    if r_data is not None:
        st.dataframe(r_data, use_container_width=True)
    
    st.subheader("Compressor Activity")
    c_data = get_compressor_data()
    if c_data is not None:
        st.dataframe(c_data, use_container_width=True)
