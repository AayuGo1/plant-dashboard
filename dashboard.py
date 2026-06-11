import streamlit as st
import pandas as pd
import glob
import os

# Clean, wide layout execution for plant telemetry
st.set_page_config(page_title="Plant Operations Master Dashboard", layout="wide")

# --- CUSTOM ENGINE TO REPAIR MIXED DATE FORMATS IN POWER CONSUMPTION DATA ---
def parse_power_sheet_date(val):
    val = str(val).strip()
    if not val or val == 'nan' or val.lower() == 'date':
        return pd.NaT
    
    # If Excel already parsed it as a timestamp string yyyy-mm-dd hh:mm:ss
    if ' ' in val:
        val = val.split(' ')[0]
        
    if '/' in val:
        return pd.to_datetime(val, dayfirst=True, errors='coerce')
    if '-' in val:
        parts = val.split('-')
        if len(parts) == 3:
            # Resolves formatting quirk where April 1-12 logs read as '2026-01-04'
            if len(parts[0]) == 4 and parts[2] == '04':
                return pd.Timestamp(year=2026, month=4, day=int(parts[1]))
            # Handles flipped year order parts if strings read '04-01-2026'
            elif len(parts[2]) == 4 and parts[1] == '04':
                return pd.Timestamp(year=2026, month=4, day=int(parts[0]))
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
def load_excel_sheet(sheet_name, row_header):
    excel_file = 'Power consumption freon.xlsx'
    if not os.path.exists(excel_file):
        return None
    try:
        df = pd.read_excel(excel_file, sheet_name=sheet_name, header=row_header, engine='openpyxl')
        df = df.dropna(axis=1, how='all')
        return df
    except Exception as e:
        st.sidebar.error(f"Error loading {sheet_name}: {e}")
        return None


# --- SCREEN RENDER ---

st.title("🏭 Plant Operations Master Dashboard")
st.markdown("---")

# --- SECTION 1: TEMPERATURE TELEMETRY GRAPH ---
st.header("📈 Temperature Monitoring System (July 2026)")
temp_df = load_temperature_data()

if temp_df is not None:
    # Live KPI status readout blocks using the last row recorded
    latest_row = temp_df.iloc[-1]
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Latest Dough Cooler 1", f"{latest_row['Dough Cooler1 Temp']:.2f} °C")
    kpi2.metric("Latest Dough Cooler 2", f"{latest_row['Dough Cooler2 Temp']:.2f} °C")
    kpi3.metric("Latest Perishable Cooler", f"{latest_row['Perishable Cooler Temp']:.2f} °C")
    
    # Large format line trend chart spanning full container width
    st.line_chart(temp_df.set_index('Time'))
else:
    st.error("Missing Temperature Logs: Ensure all 'DataLog_*.csv' files are in your directory.")

st.markdown("---")


# --- SECTION 2: POWER AND EQUIPMENT PERFORMANCE DASHBOARD ---
st.header("⚡ Power Consumption & Equipment Performance Dashboard")

# Load all required sheets directly from the Excel binary workbook
power_df = load_excel_sheet('Sheet1', row_header=1)
runtime_df = load_excel_sheet('Sheet2', row_header=2)
compressor_df = load_excel_sheet('Sheet3', row_header=3)

# Filter out bad rows from Sheet3 if header keywords get repeated as strings
if compressor_df is not None:
    compressor_df = compressor_df[compressor_df.iloc[:, 0].astype(str).str.strip().str.lower() != 'date']

# Structure the lower half cleanly into a two-column layout
col_left, col_right = st.columns(2)

# LEFT COLUMN: POWER TRACKING
with col_left:
    st.subheader("Daily Power Consumption & Value Savings Ledger")
    if power_df is not None:
        # Dynamic cleaning of dates for the table view
        power_df['Date'] = power_df['Date'].apply(parse_power_sheet_date)
        power_df = power_df.dropna(subset=['Date']).sort_values(by='Date')
        
        # Display clean data table without index noise
        st.dataframe(power_df, use_container_width=True, hide_index=True)
    else:
        st.error("Unable to load Power Consumption ('Sheet1') data.")

# RIGHT COLUMN: SYSTEM RUNTIME & COMPRESSOR ACTIVATION MATRIX
with col_right:
    st.subheader("Cold Storage Active Running Hours (KWH)")
    if runtime_df is not None:
        first_col = runtime_df.columns[0]
        runtime_df = runtime_df[runtime_df[first_col].astype(str).str.contains('Date|From') == False]
        runtime_df[first_col] = runtime_df[first_col].apply(parse_power_sheet_date)
        runtime_df = runtime_df.dropna(subset=[first_col]).sort_values(by=first_col)
        
        st.dataframe(runtime_df, use_container_width=True, hide_index=True)
    else:
        st.error("Unable to load Equipment Run Time ('Sheet2') data.")
        
    st.markdown("---")
    
    st.subheader("Compressor Transition Matrix & Hourly Savings")
    if compressor_df is not None:
        compressor_df.iloc[:, 0] = compressor_df.iloc[:, 0].apply(parse_power_sheet_date)
        compressor_df = compressor_df.dropna(subset=[compressor_df.columns[0]]).sort_values(by=compressor_df.columns[0])
        
        st.dataframe(compressor_df, use_container_width=True, hide_index=True)
    else:
        st.error("Unable to load Compressor Sequence ('Sheet3') data.")
