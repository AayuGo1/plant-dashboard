import streamlit as st
import pandas as pd
import glob
import os

# Clean, wide layout for industrial metrics tracking
st.set_page_config(page_title="Plant Operations Dashboard", layout="wide")

# --- CUSTOM ENGINE TO FIX MIXED DATE FORMATS IN POWER CONSUMPTION SHEET ---
def clean_power_sheet_date(val):
    val = str(val).strip()
    if not val or val == 'nan':
        return pd.NaT
    if '/' in val:
        return pd.to_datetime(val, dayfirst=True, errors='coerce')
    if '-' in val:
        parts = val.split('-')
        if len(parts) == 3:
            # Resolves export formatting quirk where April 1-12 looks like '2026-01-04'
            if parts[0] == '2026' and parts[2] == '04':
                return pd.Timestamp(year=2026, month=4, day=int(parts[1]))
            else:
                return pd.to_datetime(val, errors='coerce')
    return pd.to_datetime(val, errors='coerce')


# --- DATA LOADING FUNCTIONS WITH ENFORCED FILTERS ---

@st.cache_data
def load_temperature_data():
    files = glob.glob("DataLog_*.csv")
    if not files:
        return None
    
    all_dfs = []
    target_cols = ['Time', 'Dough Cooler2 Temp', 'Dough Cooler1 Temp', 'Perishable Cooler Temp']
    
    for file in files:
        df = pd.read_csv(file)
        df.columns = df.columns.str.strip() # Remove invisible header whitespaces
        
        if all(col in df.columns for col in target_cols):
            df = df[target_cols].copy()
            
            # Convert values to numbers; automatically clean NOP strings to NaN
            for col in target_cols[1:]:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                # Bridge sensor drop-outs smoothly with forward and backward fill padding
                df[col] = df[col].ffill().bfill()
            
            # Map raw timestamp strings using day-first convention
            df['Time'] = pd.to_datetime(df['Time'], dayfirst=True, errors='coerce')
            
            # Enforce exact shift to July 2026 (01-06 becomes July 1st, 02-06 July 2nd, etc.)
            df['Time'] = df['Time'].apply(lambda x: x.replace(month=7) if pd.notnull(x) else x)
            all_dfs.append(df)
            
    if not all_dfs:
        return None
        
    combined = pd.concat(all_dfs, ignore_index=True)
    return combined.drop_duplicates(subset=['Time']).sort_values(by='Time')


@st.cache_data
def load_power_data():
    try:
        df = pd.read_csv('Power consumption freon.xlsx - Sheet1.csv', header=1)
        df = df.dropna(axis=1, how='all')
        df['Date'] = df['Date'].apply(clean_power_sheet_date)
        return df.dropna(subset=['Date']).sort_values(by='Date')
    except:
        return None


@st.cache_data
def load_runtime_data():
    try:
        df = pd.read_csv('Power consumption freon.xlsx - Sheet2.csv', header=2)
        df = df.dropna(axis=1, how='all')
        first_col = df.columns[0]
        df[first_col] = pd.to_datetime(df[first_col], errors='coerce')
        return df.dropna(subset=[first_col]).sort_values(by=first_col)
    except:
        return None


@st.cache_data
def load_compressor_data():
    try:
        df = pd.read_csv('Power consumption freon.xlsx - Sheet3.csv', header=2)
        df = df.dropna(axis=1, how='all')
        df = df[df.iloc[:, 0] != 'Date']
        df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
        return df.dropna(subset=[df.columns[0]]).sort_values(by=df.columns[0])
    except:
        return None


# --- MAIN DASHBOARD LAYOUT ---

st.title("🏭 Plant Operations Master Dashboard")
st.markdown("---")

# SECTION 1: TOP-LEVEL TEMPERATURE TRACKING (July 1 to July 6, 2026)
st.header("📈 Temperature Monitoring System (July 2026)")
temp_data = load_temperature_data()

if temp_data is not None:
    # Live KPI status block using the final recorded entry row
    latest_reading = temp_data.iloc[-1]
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Latest Dough Cooler 1", f"{latest_reading['Dough Cooler1 Temp']:.2f} °C")
    kpi2.metric("Latest Dough Cooler 2", f"{latest_reading['Dough Cooler2 Temp']:.2f} °C")
    kpi3.metric("Latest Perishable Cooler", f"{latest_reading['Perishable Cooler Temp']:.2f} °C")
    
    # Large format line trend chart spanning full container width
    st.line_chart(temp_data.set_index('Time'))
else:
    st.error("Error: Temperature log files (`DataLog_*.csv`) could not be loaded or parsed.")

st.markdown("---")

# SECTION 2: SIDE-BY-SIDE COLUMNS DIRECTLY BELOW THE CHART
st.header("⚡ Energy & Equipment Utilization Analytics")

col_power, col_runtime = st.columns(2)

# Left Column - Power Ledger
with col_power:
    st.subheader("Daily Power Consumption & Value Savings")
    power_data = load_power_data()
    if power_data is not None:
        st.dataframe(power_data, use_container_width=True, hide_index=True)
    else:
        st.error("Could not find or load Power consumption data.")

# Right Column - Runtime Ledger & Compressor Cycles
with col_runtime:
    st.subheader("Cold Storage Unit Active Run Times (KWH)")
    runtime_data = load_runtime_data()
    if runtime_data is not None:
        st.dataframe(runtime_data, use_container_width=True, hide_index=True)
    else:
        st.error("Could not find or load Equipment Run Time data.")
        
    st.markdown("### Equipment Sequence Tracking")
    st.subheader("Compressor Transition Matrix")
    compressor_data = load_compressor_data()
    if compressor_data is not None:
        st.dataframe(compressor_data, use_container_width=True, hide_index=True)
    else:
        st.error("Could not find or load Compressor transition logs.")
