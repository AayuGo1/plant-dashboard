import streamlit as st
import pandas as pd
import glob
import os

# Clean, wide layout execution for plant telemetry
st.set_page_config(page_title="Plant Operations Dashboard", layout="wide")

# --- CUSTOM ENGINE TO REPAIR MIXED DATE FORMATS IN POWER CONSUMPTION DATA ---
def parse_power_sheet_date(val):
    val = str(val).strip()
    if not val or val == 'nan' or val.lower() == 'date':
        return pd.NaT
    if '/' in val:
        return pd.to_datetime(val, dayfirst=True, errors='coerce')
    if '-' in val:
        parts = val.split('-')
        if len(parts) == 3:
            # Resolves formatting quirk where April 1-12 logs read as '2026-01-04'
            if parts[0] == '2026' and parts[2] == '04':
                return pd.Timestamp(year=2026, month=4, day=int(parts[1]))
            else:
                return pd.to_datetime(val, errors='coerce')
    return pd.to_datetime(val, errors='coerce')


# --- DATA PIPELINE LOADERS ---

@st.cache_data
def load_temperature_data():
    files = glob.glob("DataLog_*.csv")
    if not files:
        return None
    
    all_dfs = []
    target_cols = ['Time', 'Dough Cooler2 Temp', 'Dough Cooler1 Temp', 'Perishable Cooler Temp']
    
    for file in files:
        df = pd.read_csv(file)
        df.columns = df.columns.str.strip()
        
        if all(col in df.columns for col in target_cols):
            df = df[target_cols].copy()
            
            # Clean numerical telemetry data & strip out hidden NOP strings with variable spacing
            for col in target_cols[1:]:
                if df[col].dtype == object:
                    df[col] = df[col].astype(str).str.replace(r'.*NOP.*', '', regex=True)
                
                df[col] = pd.to_numeric(df[col], errors='coerce')
                # Bridge sensor drop-outs smoothly with forward and backward fill padding
                df[col] = df[col].ffill().bfill()
            
            # Enforce strict day-first timestamp parsing
            df['Time'] = pd.to_datetime(df['Time'], dayfirst=True, errors='coerce')
            
            # HARD OVERRIDE: Re-align files (01-06 to 06-06) strictly into July 1st - July 6th, 2026
            df['Time'] = df['Time'].apply(lambda x: x.replace(month=7) if pd.notnull(x) else x)
            all_dfs.append(df)
            
    if not all_dfs:
        return None
        
    combined = pd.concat(all_dfs, ignore_index=True)
    return combined.drop_duplicates(subset=['Time']).sort_values(by='Time')


@st.cache_data
def load_power_data():
    try:
        # Real headers are on row index 1 (Date, Dunkin Blast, Total, Savings...)
        df = pd.read_csv('Power consumption freon.xlsx - Sheet1.csv', header=1)
        df = df.dropna(axis=1, how='all')
        df['Date'] = df['Date'].apply(parse_power_sheet_date)
        return df.dropna(subset=['Date']).sort_values(by='Date')
    except:
        return None


# --- SCREEN RENDER ---

st.title("🏭 Plant Operations Master Dashboard")
st.markdown("---")

# UPPER BLOCK: TEMPERATURE CHRONOLOGY (July 1 to July 6, 2026)
st.header("📈 Temperature Monitoring System (July 2026)")
temp_df = load_temperature_data()

if temp_df is not None:
    # Live KPI telemetry readout blocks
    latest_row = temp_df.iloc[-1]
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Latest Dough Cooler 1", f"{latest_row['Dough Cooler1 Temp']:.2f} °C")
    kpi2.metric("Latest Dough Cooler 2", f"{latest_row['Dough Cooler2 Temp']:.2f} °C")
    kpi3.metric("Latest Perishable Cooler", f"{latest_row['Perishable Cooler Temp']:.2f} °C")
    
    # Full container width trend monitoring chart
    st.line_chart(temp_df.set_index('Time'))
else:
    st.error("Missing Data Error: Ensure all DataLog_*.csv files are located in the execution directory.")

st.markdown("---")

# LOWER BLOCK: POWER CONSUMPTION DATA DISPLAY (Directly below temperature chart)
st.header("⚡ Power Consumption Data Ledger")
power_df = load_power_data()

if power_df is not None:
    st.markdown("### Daily Power Consumption & Operational Value Savings Matrix")
    st.dataframe(power_df, use_container_width=True, hide_index=True)
else:
    st.error("Unable to load Power Consumption log structures. Verify that 'Power consumption freon.xlsx - Sheet1.csv' is saved alongside app.py.")
