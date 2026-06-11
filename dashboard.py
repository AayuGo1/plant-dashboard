import streamlit as st
import pandas as pd
import glob
import os

# Set advanced, wide container layout with dark/light responsive styling
st.set_page_config(page_title="Plant Operations Intelligence Console", layout="wide")

# --- CUSTOM ENGINE TO REPAIR MIXED DATE FORMATS IN POWER CONSUMPTION DATA ---
def parse_power_sheet_date(val):
    val = str(val).strip()
    if not val or val == 'nan' or val.lower() == 'date':
        return pd.NaT
    
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
            
            # Clean numerical telemetry data & strip out hidden NOP strings
            for col in target_cols[1:]:
                if df[col].dtype == object:
                    df[col] = df[col].astype(str).str.replace(r'.*NOP.*', '', regex=True)
                
                df[col] = pd.to_numeric(df[col], errors='coerce')
                df[col] = df[col].ffill().bfill()
            
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

# Custom Hero Header block with dark themed branding accents
st.markdown("""
    <div style="background-color:#1E1E2F;padding:24px;border-radius:12px;margin-bottom:25px;border-left:8px solid #FF4B4B">
        <h1 style="color:#FFFFFF;margin:0;font-size:32px;font-family:sans-serif;">🏭 Plant Operations Intelligence Console</h1>
        <p style="color:#A3A3C2;margin:5px 0 0 0;font-size:15px;">Real-time Telemetry, System Utilization, & Financial Energy Auditing</p>
    </div>
""", unsafe_allowed_html=True)

# ==========================================================
# SECTION 1: TEMPERATURE TELEMETRY CONTROL CENTRE (FULL WIDTH)
# ==========================================================
st.markdown("### 📈 Cryogenic & Thermal Zone Profiles")
temp_df = load_temperature_data()

if temp_df is not None:
    # Stylized Dynamic Stat Cards
    latest_row = temp_df.iloc[-1]
    kpi1, kpi2, kpi3 = st.columns(3)
    
    with kpi1:
        st.markdown(f"""
            <div style="background-color:#F0F2F6;padding:16px;border-radius:10px;text-align:center;border-bottom:4px solid #0068C9">
                <span style="color:#555;font-size:14px;font-weight:bold;text-transform:uppercase;">Dough Cooler 1</span>
                <h2 style="margin:5px 0;color:#111;">{latest_row['Dough Cooler1 Temp']:.2f} °C</h2>
            </div>
        """, unsafe_allowed_html=True)
        
    with kpi2:
        st.markdown(f"""
            <div style="background-color:#F0F2F6;padding:16px;border-radius:10px;text-align:center;border-bottom:4px solid #83C9FF">
                <span style="color:#555;font-size:14px;font-weight:bold;text-transform:uppercase;">Dough Cooler 2</span>
                <h2 style="margin:5px 0;color:#111;">{latest_row['Dough Cooler2 Temp']:.2f} °C</h2>
            </div>
        """, unsafe_allowed_html=True)
        
    with kpi3:
        st.markdown(f"""
            <div style="background-color:#F0F2F6;padding:16px;border-radius:10px;text-align:center;border-bottom:4px solid #FF2B2B">
                <span style="color:#555;font-size:14px;font-weight:bold;text-transform:uppercase;">Perishable Storage</span>
                <h2 style="margin:5px 0;color:#111;">{latest_row['Perishable Cooler Temp']:.2f} °C</h2>
            </div>
        """, unsafe_allowed_html=True)
    
    # Render chart immediately below metric panels
    st.markdown("<br>", unsafe_allowed_html=True)
    st.line_chart(temp_df.set_index('Time'), height=320)
else:
    st.error("Missing Temperature Logs: Ensure all 'DataLog_*.csv' files are in your directory.")

st.markdown("<hr style='border:1px solid #E6E6E6;margin:30px 0;'>", unsafe_allowed_html=True)


# ==========================================================
# SECTION 2: STACKED ENERGY & LOGISTICS PROFILE (CREATIVE VIEW)
# ==========================================================

# Data compilation layers
raw_power = load_excel_sheet('Sheet1', row_header=1)
raw_runtime = load_excel_sheet('Sheet2', row_header=2)
raw_compressor = load_excel_sheet('Sheet3', row_header=3)

# --- PANEL A: POWER AUDITING LAYER (STACKED STEP 1) ---
st.markdown("### ⚡ Financial Performance & Energy Consumption Profile")

if raw_power is not None:
    power_df = raw_power.copy()
    power_df['Date'] = power_df['Date'].apply(parse_power_sheet_date)
    power_df = power_df.dropna(subset=['Date']).sort_values(by='Date')
    
    # Upper Analytics Strip within section
    total_dunkin = pd.to_numeric(power_df['Dunkin Blast'], errors='coerce').sum()
    total_clc = pd.to_numeric(power_df['CLC Blast'], errors='coerce').sum()
    net_savings = pd.to_numeric(power_df['Savings'], errors='coerce').sum()
    
    sub_col1, sub_col2, sub_col3 = st.columns(3)
    sub_col1.metric("Cumulative Dunkin Blast Draw", f"{total_dunkin:,.1f} kWh")
    sub_col2.metric("Cumulative CLC Blast Draw", f"{total_clc:,.1f} kWh")
    sub_col3.metric("Net Financial Optimization (Savings)", f"INR {net_savings:,.2f}")
    
    # Stacked Area Visualization for Energy Allocations
    st.markdown("#### Chronological Load Distribution Pattern")
    chart_power_data = power_df.set_index('Date')[['Dunkin Blast', 'CLC Blast']]
    st.area_chart(chart_power_data, height=260)
    
    # Financial Net-Benefit Bar Chart
    if 'Savings' in power_df.columns:
        st.markdown("#### Daily Financial Variance Ledger")
        st.bar_chart(power_df.set_index('Date')['Savings'], color="#29B6F6", height=180)
        
    with st.expander("👁️ Review Comprehensive Energy Data Logs"):
        st.dataframe(power_df, use_container_width=True, hide_index=True)
else:
    st.error("Power Consumption dataset ('Sheet1') could not be initialized.")

st.markdown("<br><br>", unsafe_allowed_html=True)


# --- PANEL B: RUNTIME METRIC GRID (STACKED STEP 2) ---
st.markdown("### ⚙️ Machine Duty Cycles & Maintenance Intervals")

if raw_runtime is not None:
    runtime_df = raw_runtime.copy()
    first_col = runtime_df.columns[0]
    runtime_df = runtime_df[runtime_df[first_col].astype(str).str.contains('Date|From') == False]
    runtime_df[first_col] = runtime_df[first_col].apply(parse_power_sheet_date)
    runtime_df = runtime_df.dropna(subset=[first_col]).sort_values(by=first_col)
    
    # Visualizing Cold Storage Runtime patterns via Bar Chart directly below
    st.markdown("#### Cold Storage Operating Capacity Tracking (KWH Log)")
    if 'KWH' in runtime_df.columns:
        st.bar_chart(runtime_df.set_index(first_col)['KWH'], color="#FF9F43", height=220)
        
    with st.expander("👁️ Review Detailed Cold Storage Run Ledgers"):
        st.dataframe(runtime_df, use_container_width=True, hide_index=True)
else:
    st.error("Equipment runtime profiles ('Sheet2') could not be initialized.")

st.markdown("<br><br>", unsafe_allowed_html=True)


# --- PANEL C: COMPRESSOR SEQUENCING MATRIX (STACKED STEP 3) ---
st.markdown("### 📉 Compressor Optimization Efficiency")

if raw_compressor is not None:
    compressor_df = raw_compressor.copy()
    compressor_df = compressor_df[compressor_df.iloc[:, 0].astype(str).str.strip().str.lower() != 'date']
    compressor_df.iloc[:, 0] = compressor_df.iloc[:, 0].apply(parse_power_sheet_date)
    compressor_df = compressor_df.dropna(subset=[compressor_df.columns[0]]).sort_values(by=compressor_df.columns[0])
    
    if 'Saving in hrs' in compressor_df.columns:
        st.markdown("#### Extracted Optimization Window Durations (Hours)")
        st.line_chart(compressor_df.set_index(compressor_df.columns[0])['Saving in hrs'], color="#66BB6A", height=200)
        
    with st.expander("👁️ Review Mechanical Sequencing Data Rows"):
        st.dataframe(compressor_df, use_container_width=True, hide_index=True)
else:
    st.error("Compressor sequencing log matrices ('Sheet3') could not be initialized.")
