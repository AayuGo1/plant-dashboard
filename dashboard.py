import streamlit as st
import pandas as pd
import glob
import os

# Configure wide responsive structural grid
st.set_page_config(page_title="Plant Operational Intelligence Hub", layout="wide")

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
        
        # Strip trailing text summary rows if they exist in the workbook sheets
        if not df.empty:
            first_col = df.columns[0]
            df = df[df[first_col].astype(str).str.strip().str.lower() != 'total']
            
        return df
    except Exception as e:
        st.sidebar.error(f"Error loading {sheet_name}: {e}")
        return None


# --- MAIN UI CONSOLE RENDER ---

# Distinct Dark Header Branding Component
st.markdown("""
    <div style="background-color:#1E1E2F;padding:24px;border-radius:12px;margin-bottom:30px;border-left:8px solid #00D2FF">
        <h1 style="color:#FFFFFF;margin:0;font-size:32px;font-family:sans-serif;letter-spacing:-0.5px;">🏭 Plant Operations Intelligence Hub</h1>
        <p style="color:#A3A3C2;margin:6px 0 0 0;font-size:15px;">Thermal Management Telemetry & Infrastructure Energy Audits</p>
    </div>
""", unsafe_allow_html=True)

# ==========================================================
# SYSTEM FRAME 1: TEMPERATURE TELEMETRY PANEL (TOP BANNER)
# ==========================================================
st.markdown("### 📊 Cryogenic & Cold Storage Thermal Profiles")
temp_df = load_temperature_data()

if temp_df is not None:
    # Modern Custom KPI blocks
    latest_row = temp_df.iloc[-1]
    kpi1, kpi2, kpi3 = st.columns(3)
    
    with kpi1:
        st.markdown(f"""
            <div style="background-color:#F8F9FA;padding:18px;border-radius:12px;text-align:center;box-shadow:0 2px 4px rgba(0,0,0,0.05);border-top:4px solid #0068C9">
                <span style="color:#6C757D;font-size:13px;font-weight:600;text-transform:uppercase;">Dough Cooler 1</span>
                <h2 style="margin:8px 0 0 0;color:#1A1D20;font-size:28px;">{latest_row['Dough Cooler1 Temp']:.2f} °C</h2>
            </div>
        """, unsafe_allow_html=True)
        
    with kpi2:
        st.markdown(f"""
            <div style="background-color:#F8F9FA;padding:18px;border-radius:12px;text-align:center;box-shadow:0 2px 4px rgba(0,0,0,0.05);border-top:4px solid #29B6F6">
                <span style="color:#6C757D;font-size:13px;font-weight:600;text-transform:uppercase;">Dough Cooler 2</span>
                <h2 style="margin:8px 0 0 0;color:#1A1D20;font-size:28px;">{latest_row['Dough Cooler2 Temp']:.2f} °C</h2>
            </div>
        """, unsafe_allow_html=True)
        
    with kpi3:
        st.markdown(f"""
            <div style="background-color:#F8F9FA;padding:18px;border-radius:12px;text-align:center;box-shadow:0 2px 4px rgba(0,0,0,0.05);border-top:4px solid #FF4B4B">
                <span style="color:#6C757D;font-size:13px;font-weight:600;text-transform:uppercase;">Perishable Storage</span>
                <h2 style="margin:8px 0 0 0;color:#1A1D20;font-size:28px;">{latest_row['Perishable Cooler Temp']:.2f} °C</h2>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.line_chart(temp_df.set_index('Time'), height=320)
else:
    st.error("Missing Data Error: Verify that 'DataLog_*.csv' files populate your root project folder.")

st.markdown("<hr style='border:1px solid #E6E8EC;margin:40px 0;'>", unsafe_allow_html=True)


# ==========================================================
# SYSTEM FRAME 2: STACKED WORKBOOK COMPILATION (BELOW CHARTS)
# ==========================================================
st.markdown("### ⚡ Infrastructure Asset Metrics (`Power consumption freon.xlsx`)")

# Ingest all sheets directly from the target file source
power_sheet = load_excel_sheet('Sheet1', row_header=1)
runtime_sheet = load_excel_sheet('Sheet2', row_header=2)
compressor_sheet = load_excel_sheet('Sheet3', row_header=3)

# --------------------------------------------------------
# STACK LAYER A: EXCEL SHEET 1 - POWER RECORD INFRASTRUCTURE
# --------------------------------------------------------
with st.container():
    st.markdown("#### 🔋 Core Load Distribution & Operational Savings (Sheet 1)")
    
    if power_sheet is not None:
        p_df = power_sheet.copy()
        p_df['Date'] = p_df['Date'].apply(parse_power_sheet_date)
        p_df = p_df.dropna(subset=['Date']).sort_values(by='Date')
        
        # Ensure numerical casting to prevent chart data type errors
        p_df['Dunkin Blast'] = pd.to_numeric(p_df['Dunkin Blast'], errors='coerce').fillna(0)
        p_df['CLC Blast'] = pd.to_numeric(p_df['CLC Blast'], errors='coerce').fillna(0)
        p_df['Savings'] = pd.to_numeric(p_df['Savings'], errors='coerce').fillna(0)
        
        # Quality Control: Filter out values that represent absolute historical totals instead of daily deltas
        filtered_p_df = p_df[p_df['Dunkin Blast'] < 500000].copy()
        
        dunkin_sum = filtered_p_df['Dunkin Blast'].sum()
        clc_sum = filtered_p_df['CLC Blast'].sum()
        savings_sum = filtered_p_df['Savings'].sum()
        
        sm1, sm2, sm3 = st.columns(3)
        sm1.metric("Dunkin Blast Load Accumulation", f"{dunkin_sum:,.1f} kWh")
        sm2.metric("CLC Blast Load Accumulation", f"{clc_sum:,.1f} kWh")
        sm3.metric("Net Financial Optimization", f"INR {savings_sum:,.2f}")
        
        # Plot full screen area projection chart
        st.markdown("##### Comparative Infrastructure Draw Profiles")
        chart_power_data = filtered_p_df.set_index('Date')[['Dunkin Blast', 'CLC Blast']]
        st.area_chart(chart_power_data, height=250)
        
        # Plot savings block columns
        st.markdown("##### Daily Financial Efficiency Margins")
        st.bar_chart(filtered_p_df.set_index('Date')['Savings'], color="#66BB6A", height=180)
            
        with st.expander("¼ View Detailed Sheet 1 Row Ledger"):
            st.dataframe(filtered_p_df, use_container_width=True, hide_index=True)
    else:
        st.error("Sheet 1 could not be extracted from the target file repository.")

st.markdown("<hr style='border:1px dashed #E6E8EC;margin:35px 0;'>", unsafe_allow_html=True)


# --------------------------------------------------------
# STACK LAYER B: EXCEL SHEET 2 - EQUIPMENT RUNTIME METRICS
# --------------------------------------------------------
with st.container():
    st.markdown("#### ⚙️ Cold Storage Unit Active Duty Cycles (Sheet 2)")
    
    if runtime_sheet is not None:
        r_df = runtime_sheet.copy()
        first_col = r_df.columns[0]
        r_df = r_df[r_df[first_col].astype(str).str.contains('Date|From|Total') == False]
        r_df[first_col] = r_df[first_col].apply(parse_power_sheet_date)
        r_df = r_df.dropna(subset=[first_col]).sort_values(by=first_col)
        
        # Dynamically identify columns containing numeric run capacity data
        kwh_cols = [c for c in r_df.columns if 'KWH' in c]
        for col in kwh_cols:
            r_df[col] = pd.to_numeric(r_df[col], errors='coerce').fillna(0)
            
        if kwh_cols:
            st.markdown("##### Measured Running Capacity Performance (KWH Logs)")
            st.bar_chart(r_df.set_index(first_col)[kwh_cols[0]], color="#FFA726", height=220)
            
        with st.expander("¼ View Detailed Sheet 2 Operational Logs"):
            st.dataframe(r_df, use_container_width=True, hide_index=True)
    else:
        st.error("Sheet 2 could not be extracted from the target file repository.")

st.markdown("<hr style='border:1px dashed #E6E8EC;margin:35px 0;'>", unsafe_allow_html=True)


# --------------------------------------------------------
# STACK LAYER C: EXCEL SHEET 3 - COMPRESSOR TRACKING (SAVINGS)
# --------------------------------------------------------
with st.container():
    st.markdown("#### 📉 Compressor Maintenance Optimization (Sheet 3)")
    
    if compressor_sheet is not None:
        c_df = compressor_sheet.copy()
        c_df = c_df[c_df.iloc[:, 0].astype(str).str.strip().str.lower().str.contains('date|total') == False]
        c_df.iloc[:, 0] = c_df.iloc[:, 0].apply(parse_power_sheet_date)
        c_df = c_df.dropna(subset=[c_df.columns[0]]).sort_values(by=c_df.columns[0])
        
        # Ensure 'Saving in hrs' column is cast completely to numbers to prevent plotting glitches
        if 'Saving in hrs' in c_df.columns:
            c_df['Saving in hrs'] = pd.to_numeric(c_df['Saving in hrs'], errors='coerce').fillna(0)
            st.markdown("##### Calculated Maintenance Savings Windows (Hours)")
            st.line_chart(c_df.set_index(c_df.columns[0])['Saving in hrs'], color="#AB47BC", height=200)
            
        with st.expander("¼ View Detailed Sheet 3 Data Ledger"):
            st.dataframe(c_df, use_container_width=True, hide_index=True)
    else:
        st.error("Sheet 3 could not be extracted from the target file repository.")

st.markdown("<hr style='border:1px solid #E6E8EC;margin:40px 0;'>", unsafe_allow_html=True)


# ==========================================================
# SYSTEM FRAME 3: COMPRESSOR DAILY WORKING TIMINGS & LINE GRAPH
# ==========================================================
st.markdown("### 🌀 Compressor Daily Working Timings")

if compressor_sheet is not None:
    comp_timing_df = compressor_sheet.copy()
    
    # Standardize column header strings
    comp_timing_df.columns = comp_timing_df.columns.str.strip()
    date_col = comp_timing_df.columns[0]
    
    # Purge dirty tracking text rows & clean dates
    comp_timing_df = comp_timing_df[comp_timing_df[date_col].astype(str).str.lower().str.contains('date|total') == False]
    comp_timing_df[date_col] = comp_timing_df[date_col].apply(parse_power_sheet_date)
    comp_timing_df = comp_timing_df.dropna(subset=[date_col]).sort_values(by=date_col)
    
    # Automatically locate column keeping track of operational running hours
    run_hours_col = None
    for col in comp_timing_df.columns:
        if 'run' in col.lower() or 'working' in col.lower() or 'operating' in col.lower() or 'hrs' in col.lower() or 'hours' in col.lower():
            if 'saving' not in col.lower():  # Skip the savings metrics column
                run_hours_col = col
                break
                
    # Fallback plan if column names are completely custom/generic
    if not run_hours_col and len(comp_timing_df.columns) > 1:
        run_hours_col = comp_timing_df.columns[1]

    if run_hours_col:
        # Cast data values directly to clean floats
        comp_timing_df[run_hours_col] = pd.to_numeric(comp_timing_df[run_hours_col], errors='coerce').fillna(0)
        
        # Format the DataFrame specifically to show "How many hours it worked on which day"
        summary_display_df = comp_timing_df[[date_col, run_hours_col]].copy()
        summary_display_df.columns = ['Operational Date', 'Hours Worked (hrs)']
        
        # --- RENDER KPI SUMMARY CARD ---
        total_worked_hours = summary_display_df['Hours Worked (hrs)'].sum()
        st.metric(label="Total Combined Compressor Production Load", value=f"{total_worked_hours:,.1f} Hours")
        
        # --- RENDER RUNTIME LINE GRAPH ---
        st.markdown("##### 📈 Compressor Daily Run-Time Trend Graph")
        chart_data = summary_display_df.set_index('Operational Date')['Hours Worked (hrs)']
        st.line_chart(chart_data, color="#00D2FF", height=280)
        
        # --- RENDER DAY-BY-DAY DATAFRAME LEDGER ---
        st.markdown("##### 📅 Detailed Running Timings Log")
        st.caption("Breakdown tracking exactly how many hours the compressor asset worked on each individual day:")
        st.dataframe(summary_display_df, use_container_width=True, hide_index=True)
    else:
        st.warning("Could not identify a valid runtime hours column inside Sheet 3.")
else:
    st.error("Compressor Timing Error: Unable to display metrics because Sheet 3 could not be parsed.")
