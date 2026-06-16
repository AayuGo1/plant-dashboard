import streamlit as st
import pandas as pd
import glob
import os

# Configure wide responsive structural grid
st.set_page_config(page_title="Plant Operational Intelligence Hub", layout="wide")

# --- PATH CONFIGURATION ---
# 1. CHANGE THIS to your exact Windows username if you want OneDrive sync to work:
ONEDRIVE_PATH = "C:/Users/YourName/OneDrive - CompanyName/Plant_Reports/"

# 2. Local fallback folder (right next to your dashboard.py script)
LOCAL_PATH = "./"


# --- AUTOMATIC PATH RESOLVER ---
def get_valid_file_path(filename, search_pattern=False):
    """Checks OneDrive first; if not found, falls back to the local dashboard folder."""
    if search_pattern:
        # Handling wildcard lookups for DataLog_*.csv
        onedrive_files = glob.glob(os.path.join(ONEDRIVE_PATH, filename))
        if onedrive_files:
            return onedrive_files
        return glob.glob(os.path.join(LOCAL_PATH, filename))
    else:
        # Handling explicit excel workbook lookups
        onedrive_file = os.path.join(ONEDRIVE_PATH, filename)
        if os.path.exists(onedrive_file):
            return onedrive_file
        return os.path.join(LOCAL_PATH, filename)


# --- CUSTOM ENGINE TO REPAIR MIXED DATE FORMATS IN POWER CONSUMPTION DATA ---
def parse_power_sheet_date(val):
    val = str(val).strip()
    if not val or val == 'nan' or val.lower() == 'date' or val.lower() == 'total':
        return pd.NaT
    
    if ' ' in val:
        val = val.split(' ')[0]
        
    if '/' in val:
        return pd.to_datetime(val, dayfirst=True, errors='coerce')
    if '-' in val:
        parts = val.split('-')
        if len(parts) == 3:
            if len(parts[0]) == 4 and parts[2] == '04':
                return pd.Timestamp(year=2026, month=4, day=int(parts[1]))
            elif len(parts[2]) == 4 and parts[1] == '04':
                return pd.Timestamp(year=2026, month=4, day=int(parts[0]))
            else:
                return pd.to_datetime(val, errors='coerce')
    return pd.to_datetime(val, errors='coerce')


# --- DATA PIPELINE LOADERS ---

@st.cache_data
def load_temperature_data():
    files = get_valid_file_path("DataLog_*.csv", search_pattern=True)
    if not files:
        return None
    
    all_dfs = []
    target_cols = ['Time', 'Dough Cooler2 Temp', 'Dough Cooler1 Temp', 'Perishable Cooler Temp']
    
    for file in files:
        df = pd.read_csv(file)
        df.columns = df.columns.str.strip()
        
        if all(col in df.columns for col in target_cols):
            df = df[target_cols].copy()
            
            for col in target_cols[1:]:
                if df[col].dtype == object:
                    df[col] = df[col].astype(str).str.replace(r'.*NOP.*', '', regex=True)
                df[col] = pd.to_numeric(df[col], errors='coerce')
                df[col] = df[col].ffill().bfill()
            
            df['Time'] = pd.to_datetime(df['Time'], dayfirst=True, errors='coerce')
            df['Time'] = df['Time'].apply(lambda x: x.replace(month=7) if pd.notnull(x) else x)
            all_dfs.append(df)
            
    if not all_dfs:
        return None
        
    return pd.concat(all_dfs, ignore_index=True).drop_duplicates(subset=['Time']).sort_values(by='Time')


@st.cache_data
def load_excel_sheet(sheet_name, row_header):
    excel_file = get_valid_file_path('Power consumption freon.xlsx')
    if not os.path.exists(excel_file):
        return None
    try:
        df = pd.read_excel(excel_file, sheet_name=sheet_name, header=row_header, engine='openpyxl')
        df = df.dropna(axis=1, how='all')
        if not df.empty:
            first_col = df.columns[0]
            df = df[df[first_col].astype(str).str.strip().str.lower() != 'total']
        return df
    except Exception as e:
        return None


# --- MAIN UI CONSOLE RENDER ---

st.markdown("""
    <div style="background-color:#1E1E2F;padding:24px;border-radius:12px;margin-bottom:30px;border-left:8px solid #00D2FF">
        <h1 style="color:#FFFFFF;margin:0;font-size:32px;font-family:sans-serif;letter-spacing:-0.5px;">🏭 Plant Operations Intelligence Hub</h1>
        <p style="color:#A3A3C2;margin:6px 0 0 0;font-size:15px;">Thermal Management Telemetry & Infrastructure Energy Audits</p>
    </div>
""", unsafe_allow_html=True)

# ==========================================================
# SYSTEM FRAME 1: TEMPERATURE TELEMETRY PANEL
# ==========================================================
st.markdown("### 📊 Cryogenic & Cold Storage Thermal Profiles")
temp_df = load_temperature_data()

if temp_df is not None and not temp_df.empty:
    latest_row = temp_df.iloc[-1]
    kpi1, kpi2, kpi3 = st.columns(3)
    
    with kpi1:
        st.markdown(f"""<div style="background-color:#F8F9FA;padding:18px;border-radius:12px;text-align:center;border-top:4px solid #0068C9"><span style="color:#6C757D;font-size:13px;font-weight:600;text-transform:uppercase;">Dough Cooler 1</span><h2 style="margin:8px 0 0 0;color:#1A1D20;font-size:28px;">{latest_row['Dough Cooler1 Temp']:.2f} °C</h2></div>""", unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"""<div style="background-color:#F8F9FA;padding:18px;border-radius:12px;text-align:center;border-top:4px solid #29B6F6"><span style="color:#6C757D;font-size:13px;font-weight:600;text-transform:uppercase;">Dough Cooler 2</span><h2 style="margin:8px 0 0 0;color:#1A1D20;font-size:28px;">{latest_row['Dough Cooler2 Temp']:.2f} °C</h2></div>""", unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"""<div style="background-color:#F8F9FA;padding:18px;border-radius:12px;text-align:center;border-top:4px solid #FF4B4B"><span style="color:#6C757D;font-size:13px;font-weight:600;text-transform:uppercase;">Perishable Storage</span><h2 style="margin:8px 0 0 0;color:#1A1D20;font-size:28px;">{latest_row['Perishable Cooler Temp']:.2f} °C</h2></div>""", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.line_chart(temp_df.set_index('Time'))
else:
    st.warning("⚠️ Displaying structural frames. Please add your 'DataLog_*.csv' telemetry files to your folder.")

st.markdown("<hr style='border:1px solid #E6E8EC;margin:40px 0;'>", unsafe_allow_html=True)


# ==========================================================
# SYSTEM FRAME 2: INFRASTRUCTURE ASSET METRICS
# ==========================================================
st.markdown("### ⚡ Infrastructure Asset Metrics")

power_sheet = load_excel_sheet('Sheet1', row_header=1)
runtime_sheet = load_excel_sheet('Sheet2', row_header=2)
compressor_sheet = load_excel_sheet('Sheet3', row_header=3)

# --- LAYER A: SHEET 1 POWER ---
st.markdown("#### 🔋 Core Load Distribution & Operational Savings (Sheet 1)")
if power_sheet is not None and not power_sheet.empty:
    p_df = power_sheet.copy()
    p_df['Date'] = p_df['Date'].apply(parse_power_sheet_date)
    p_df = p_df.dropna(subset=['Date']).sort_values(by='Date')
    
    p_df['Dunkin Blast'] = pd.to_numeric(p_df['Dunkin Blast'], errors='coerce').fillna(0)
    p_df['CLC Blast'] = pd.to_numeric(p_df['CLC Blast'], errors='coerce').fillna(0)
    p_df['Savings'] = pd.to_numeric(p_df['Savings'], errors='coerce').fillna(0)
    
    filtered_p_df = p_df[p_df['Dunkin Blast'] < 500000].copy()
    
    if not filtered_p_df.empty:
        dunkin_sum = filtered_p_df['Dunkin Blast'].sum()
        clc_sum = filtered_p_df['CLC Blast'].sum()
        savings_sum = filtered_p_df['Savings'].sum()
        
        sm1, sm2, sm3 = st.columns(3)
        sm1.metric("Dunkin Blast Load Accumulation", f"{dunkin_sum:,.1f} kWh")
        sm2.metric("CLC Blast Load Accumulation", f"{clc_sum:,.1f} kWh")
        sm3.metric("Net Financial Optimization", f"INR {savings_sum:,.2f}")
        
        st.markdown("##### Comparative Infrastructure Draw Profiles")
        st.area_chart(filtered_p_df.set_index('Date')[['Dunkin Blast', 'CLC Blast']])
        
        st.markdown("##### Daily Financial Efficiency Margins")
        st.bar_chart(filtered_p_df.set_index('Date')['Savings'])
        
        # Safe save to OneDrive if folder path exists
        if os.path.exists(ONEDRIVE_PATH):
            filtered_p_df.to_csv(os.path.join(ONEDRIVE_PATH, "Clean_Daily_Power_Metrics.csv"), index=False)
            
        with st.expander("¼ View Detailed Sheet 1 Ledger"):
            st.dataframe(filtered_p_df, use_container_width=True, hide_index=True)
else:
    st.info("ℹ️ 'Power consumption freon.xlsx' (Sheet1) not detected or empty.")

st.markdown("<hr style='border:1px dashed #E6E8EC;margin:35px 0;'>", unsafe_allow_html=True)


# --- LAYER B: SHEET 2 RUNTIME ---
st.markdown("#### ⚙️ Cold Storage Unit Active Duty Cycles (Sheet 2)")
if runtime_sheet is not None and not runtime_sheet.empty:
    r_df = runtime_sheet.copy()
    first_col = r_df.columns[0]
    r_df = r_df[r_df[first_col].astype(str).str.contains('Date|From|Total') == False]
    r_df[first_col] = r_df[first_col].apply(parse_power_sheet_date)
    r_df = r_df.dropna(subset=[first_col]).sort_values(by=first_col)
    
    kwh_cols = [c for c in r_df.columns if 'KWH' in c]
    for col in kwh_cols:
        r_df[col] = pd.to_numeric(r_df[col], errors='coerce').fillna(0)
        
    if kwh_cols and not r_df.empty:
        st.markdown("##### Measured Running Capacity Performance (KWH Logs)")
        st.bar_chart(r_df.set_index(first_col)[kwh_cols[0]])
        
    with st.expander("¼ View Detailed Sheet 2 Logs"):
        st.dataframe(r_df, use_container_width=True, hide_index=True)
else:
    st.info("ℹ️ 'Power consumption freon.xlsx' (Sheet2) not detected or empty.")

st.markdown("<hr style='border:1px dashed #E6E8EC;margin:35px 0;'>", unsafe_allow_html=True)


# --- LAYER C: SHEET 3 COMPRESSOR SAVINGS ---
st.markdown("#### 📉 Compressor Maintenance Optimization (Sheet 3)")
if compressor_sheet is not None and not compressor_sheet.empty:
    c_df = compressor_sheet.copy()
    c_df = c_df[c_df.iloc[:, 0].astype(str).str.strip().str.lower().str.contains('date|total') == False]
    c_df.iloc[:, 0] = c_df.iloc[:, 0].apply(parse_power_sheet_date)
    c_df = c_df.dropna(subset=[c_df.columns[0]]).sort_values(by=c_df.columns[0])
    
    if 'Saving in hrs' in c_df.columns:
        c_df['Saving in hrs'] = pd.to_numeric(c_df['Saving in hrs'], errors='coerce').fillna(0)
        st.markdown("##### Calculated Maintenance Savings Windows (Hours)")
        st.line_chart(c_df.set_index(c_df.columns[0])['Saving in hrs'])
        
    with st.expander("¼ View Detailed Sheet 3 Data Ledger"):
        st.dataframe(c_df, use_container_width=True, hide_index=True)
else:
    st.info("ℹ️ 'Power consumption freon.xlsx' (Sheet3) not detected or empty.")
