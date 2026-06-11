import streamlit as st
import pandas as pd
import glob

# Page configuration
st.set_page_config(page_title="Plant Dashboard", layout="wide")

# --- Helper Functions ---

def get_temp_data():
    files = glob.glob("DataLog_*.csv") # Assuming temperature logs follow this pattern
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
    # Header is at row 1 (0-indexed)
    try:
        df = pd.read_csv('Power consumption freon.xlsx - Sheet1.csv', header=1)
        # Drop columns that are completely empty
        df = df.dropna(axis=1, how='all')
        return df
    except:
        return None

def get_runtime_data():
    # Header is at row 1
    try:
        df = pd.read_csv('Power consumption freon.xlsx - Sheet2.csv', header=1)
        df = df.dropna(axis=1, how='all')
        return df
    except:
        return None

def get_compressor_data():
    # Header is at row 2
    try:
        df = pd.read_csv('Power consumption freon.xlsx - Sheet3.csv', header=2)
        df = df.dropna(axis=1, how='all')
        return df
    except:
        return None

# --- Dashboard Layout ---

st.title("Plant Management Dashboard")

tab1, tab2, tab3 = st.tabs(["Temperature Monitor", "Power Consumption", "Run Time & Compressors"])

# Tab 1: Temperature
with tab1:
    data = get_temp_data()
    if data is not None:
        latest = data.iloc[-1]
        c1, c2, c3 = st.columns(3)
        c1.metric("Dough Cooler 1", f"{latest['Dough Cooler1 Temp']:.2f}°C")
        c2.metric("Dough Cooler 2", f"{latest['Dough Cooler2 Temp']:.2f}°C")
        c3.metric("Perishable Cooler", f"{latest['Perishable Cooler Temp']:.2f}°C")
        st.line_chart(data.set_index('Time'))
    else:
        st.warning("Temperature data not found.")

# Tab 2: Power Consumption
with tab2:
    st.subheader("Power Consumption Records")
    power_df = get_power_data()
    if power_df is not None:
        st.dataframe(power_df)
    else:
        st.error("Could not load Power Consumption data.")

# Tab 3: Run Time
with tab3:
    st.subheader("Cold Storage Running Hours")
    runtime_df = get_runtime_data()
    if runtime_df is not None:
        st.dataframe(runtime_df)
    
    st.subheader("Compressor Activity")
    comp_df = get_compressor_data()
    if comp_df is not None:
        st.dataframe(comp_df)
    else:
        st.error("Could not load Run Time or Compressor data.")
