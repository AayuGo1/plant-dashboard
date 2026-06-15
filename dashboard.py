import streamlit as st
import pandas as pd
import glob
import os
import warnings

# Suppress harmless openpyxl styling/validation alerts
warnings.filterwarnings("ignore", category=UserWarning)

# --- MODERN WEB LAYOUT SETUP ---
st.set_page_config(
    page_title="Plant Operational Intelligence Center",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- PREMIUM BRANDING STYLING ---
st.markdown("""
    <style>
        .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] {
            background-color: #F0F2F6;
            border: 1px solid #DFE3E8;
            border-radius: 6px 6px 0px 0px;
            padding: 12px 24px;
            font-weight: 600;
            color: #2E3A59;
            transition: all 0.3s ease;
        }
        .stTabs [data-baseweb="tab"]:hover { color: #00D2FF; background-color: #E4E7EB; }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: #1E1E2F;
            color: #FFFFFF;
            border-color: #1E1E2F;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }
        div[data-testid="stMetric"] {
            background-color: #FFFFFF;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.03);
        }
    </style>
""", unsafe_allow_html=True)


# --- SIDEBAR MASTER PIPELINE MANAGER ---
st.sidebar.markdown("""
    <div style="background-color:#1E1E2F; padding:15px; border-radius:8px; margin-bottom:15px; border-left:4px solid #00D2FF;">
        <h3 style="color:white; margin:0; font-size:16px; font-weight:600;">🛠️ Automation Config</h3>
    </div>
""", unsafe_allow_html=True)

user_name = st.sidebar.text_input("Windows Username", value="aayush")
company_folder = st.sidebar.text_input("OneDrive Company Folder", value="OneDrive")

ONEDRIVE_PATH = f"C:/Users/{user_name}/{company_folder}/PlantData/"
LOCAL_PATH = "./"

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎛️ Network Connection Nodes")

def resolve_file_pipeline(filename, is_pattern=False):
    """Smarter path resolver prioritizing active synchronized directories."""
    if is_pattern:
        cloud_nodes = glob.glob(os.path.join(ONEDRIVE_PATH, filename))
        if cloud_nodes: return cloud_nodes, "Cloud Sync Active"
        local_nodes = glob.glob(os.path.join(LOCAL_PATH, filename))
        return local_nodes, "Local Node Fallback" if local_nodes else "Disconnected"
    else:
        cloud_node = os.path.join(ONEDRIVE_PATH, filename)
        if os.path.exists(cloud_node): return cloud_node, "Cloud Sync Active"
        return os.path.join(LOCAL_PATH, filename), "Local Active"

# Network telemetry check flags for status gauges
temp_nodes, temp_status = resolve_file_pipeline("DataLog_*.csv", is_pattern=True)
excel_node, excel_status = resolve_file_pipeline('Power consumption freon.xlsx')
excel_connected = os.path.exists(excel_node)

if temp_status != "Disconnected":
    st.sidebar.success(f"🌡️ Temperature Feed: {temp_status}")
else:
    st.sidebar.error("❌ Temperature Feed: Signal Interrupted")

if excel_connected:
    st.sidebar.success(f"⚡ Freon/Ammonia Hub: Connected")
else:
    st.sidebar.error("❌ Freon/Ammonia Hub: Workbook Offline")


# --- FAST VECTORIZED DATE CONVERTER ---
def fast_parse_dates(series):
    """Efficiently cleans and formats inconsistent plant logging timestamps."""
    string_series = series.astype(str).str.strip().str.split(' ').str[0]
    cleaned_dates = pd.to_datetime(string_series, errors='coerce', dayfirst=True)
    return cleaned_dates


# --- CACHED HIGH-SPEED DATA PIPELINES ---
@st.cache_data
def load_cached_telemetry():
    files, _ = resolve_file_pipeline("DataLog_*.csv", is_pattern=True)
    if not files: return None
    
    target_columns = ['Time', 'Dough Cooler2 Temp', 'Dough Cooler1 Temp', 'Perishable Cooler Temp']
    loaded_frames = []
    
    for file in files:
        df = pd.read_csv(file)
        df.columns = df.columns.str.strip()
        if all(c in df.columns for c in target_columns):
            sub_df = df[target_columns].copy()
            for c in target_columns[1:]:
                if sub_df[c].dtype == object:
                    sub_df[c] = sub_df[c].astype(str).str.replace(r'.*NOP.*', '0', regex=True)
                sub_df[c] = pd.to_numeric(sub_df[c], errors='coerce').ffill().bfill()
            sub_df['Time'] = pd.to_datetime(sub_df['Time'], dayfirst=True, errors='coerce')
            loaded_frames.append(sub_df)
            
    if not loaded_frames: return None
    return pd.concat(loaded_frames, ignore_index=True).drop_duplicates(subset=['Time']).sort_values(by='Time')

@st.cache_data
def load_dynamic_excel_sheet(sheet_name, fallback_header_row):
    file_path, _ = resolve_file_pipeline('Power consumption freon.xlsx')
    if not os.path.exists(file_path): return None
    try:
        # Step 1: Read raw without header rules to self-detect alignment offsets
        df_check = pd.read_excel(file_path, sheet_name=sheet_name, header=None, engine='openpyxl')
        discovered_idx = fallback_header_row
        
        for idx in range(min(10, len(df_check))):
            row_items = [str(x).lower() for x in df_check.iloc[idx].dropna().tolist()]
            if any('date' in item or 'stop time' in item for item in row_items):
                discovered_idx = idx
                break
                
        # Step 2: Extract data from discovered index row
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=discovered_idx, engine='openpyxl')
        df = df.dropna(axis=1, how='all')
        if not df.empty:
            first_col = df.columns[0]
            df = df[df[first_col].astype(str).str.strip().str.lower() != 'total']
            # Clean up messy column names showing up as Unnamed pointers
            df.columns = [f"Saving in hrs" if "Unnamed:" in str(c) and idx==11 else str(c) for idx, c in enumerate(df.columns)]
        return df
    except:
        return None


# --- CONTROL PANEL SYSTEM HEADER ---
st.markdown("""
    <div style="background-color:#1E1E2F; padding:24px; border-radius:12px; margin-bottom:25px; border-left:8px solid #00D2FF; box-shadow: 0 4px 15px rgba(0,0,0,0.08);">
        <h1 style="color:#FFFFFF; margin:0; font-size:32px; font-family:sans-serif; font-weight:700; letter-spacing:-0.5px;">🏭 Plant Operations Intelligence Hub</h1>
        <p style="color:#A3A3C2; margin:6px 0 0 0; font-size:15px; font-family:sans-serif;">High-Efficiency Telemetry Data Pipelines & Automated Infrastructure Asset Audits</p>
    </div>
""", unsafe_allow_html=True)


# --- GENERATE CLEAN NAVIGATION GRIDS ---
tab_thermal, tab_power, tab_runtime, tab_compressor = st.tabs([
    "🌡️ Thermal Monitoring", 
    "⚡ Energy & Savings Balance", 
    "⚙️ Asset Duty Cycles", 
    "📉 Compressor Optimization Suite"
])


# ==========================================================
# TAB 1: REAL-TIME THERMAL SNAPSHOTS
# ==========================================================
with tab_thermal:
    st.markdown("### 📊 Cryogenic & Cold Storage Thermal Profiles")
    temp_df = load_cached_telemetry()

    if temp_df is not None and not temp_df.empty:
        latest = temp_df.iloc[-1]
        
        k1, k2, k3 = st.columns(3)
        with k1:
            st.markdown("<div style='margin-bottom: -15px; font-size:13px; color:#555; font-weight:bold;'>❄️ DOUGH COOLER 1</div>", unsafe_allow_html=True)
            st.metric(label="Live Temperature Stream", value=f"{latest['Dough Cooler1 Temp']:.2f} °C", delta="Normal Node")
        with k2:
            st.markdown("<div style='margin-bottom: -15px; font-size:13px; color:#555; font-weight:bold;'>❄️ DOUGH COOLER 2</div>", unsafe_allow_html=True)
            st.metric(label="Live Temperature Stream", value=f"{latest['Dough Cooler2 Temp']:.2f} °C", delta="Normal Node")
        with k3:
            st.markdown("<div style='margin-bottom: -15px; font-size:13px; color:#555; font-weight:bold;'>🥩 PERISHABLE STORAGE</div>", unsafe_allow_html=True)
            st.metric(label="Live Temperature Stream", value=f"{latest['Perishable Cooler Temp']:.2f} °C", delta="System Load Alert", delta_color="inverse")
        
        st.markdown("<br><h5 style='color:#1E1E2F;'>📈 Continuous Thermal Profile Stream (5-Min Snapshots)</h5>", unsafe_allow_html=True)
        st.line_chart(temp_df.set_index('Time'), color=["#0068C9", "#29B6F6", "#FF4B4B"])
    else:
        st.warning("⚠️ Telemetry matrix idling. Paste your 'DataLog_*.csv' files into your designated directory path to activate streaming.")


# ==========================================================
# TAB 2: POWER LOAD BALANCES & SAVINGS
# ==========================================================
with tab_power:
    st.markdown("### 🔋 Core Load Distribution & Operational Savings Ledger")
    power_sheet = load_dynamic_excel_sheet('Sheet1', fallback_header_row=1)

    if power_sheet is not None and not power_sheet.empty:
        p_df = power_sheet.copy()
        p_df['Date'] = fast_parse_dates(p_df['Date'])
        p_df = p_df.dropna(subset=['Date']).sort_values(by='Date')
        
        # Safe numeric parsing across primary columns
        p_df['Dunkin Blast'] = pd.to_numeric(p_df['Dunkin Blast'], errors='coerce').fillna(0)
        p_df['CLC Blast'] = pd.to_numeric(p_df['CLC Blast'], errors='coerce').fillna(0)
        
        # Detect the correct Savings tracker column dynamically
        savings_col = [c for c in p_df.columns if 'savings' in str(c).lower()]
        savings_title = savings_col[0] if savings_col else 'Savings'
        p_df[savings_title] = pd.to_numeric(p_df[savings_title], errors='coerce').fillna(0)
        
        filtered_p_df = p_df[p_df['Dunkin Blast'] < 500000].copy()
        
        if not filtered_p_df.empty:
            # Vectorized metrics summaries
            dunkin_tot = filtered_p_df['Dunkin Blast'].sum()
            clc_tot = filtered_p_df['CLC Blast'].sum()
            savings_tot = filtered_p_df[savings_title].sum()
            
            sm1, sm2, sm3 = st.columns(3)
            with sm1:
                st.metric("Dunkin Blast Accumulated Power", f"{dunkin_tot:,.1f} kWh", delta="Infrastructure Load")
            with sm2:
                st.metric("CLC Blast Accumulated Power", f"{clc_tot:,.1f} kWh", delta="Infrastructure Load")
            with sm3:
                st.metric("Net Financial Optimization Total", f"INR {savings_tot:,.2f}", delta="Calculated Efficiency Balance", delta_color="inverse")
            
            g_col1, g_col2 = st.columns(2)
            with g_col1:
                st.markdown("<h5 style='color:#1E1E2F;'>⚡ Load Demand Contrast (Area Metric Draw)</h5>", unsafe_allow_html=True)
                st.area_chart(filtered_p_df.set_index('Date')[['Dunkin Blast', 'CLC Blast']], color=["#1A5F7A", "#57C5B6"])
            with g_col2:
                st.markdown("<h5 style='color:#1E1E2F;'>💰 Daily Financial Optimization Tracking</h5>", unsafe_allow_html=True)
                st.bar_chart(filtered_p_df.set_index('Date')[savings_title], color="#28A745")
                
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("🔍 Expand Detailed Energy Distribution Log (Sheet 1 Raw)"):
                st.dataframe(filtered_p_df, use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ 'Power consumption freon.xlsx' (Sheet 1) is currently empty or file pointer path is broken.")


# ==========================================================
# TAB 3: ASSET OPERATIONAL RUN TIME DUTY CYCLES
# ==========================================================
with tab_runtime:
    st.markdown("### ⚙️ Cold Storage Unit Active Duty Cycles")
    runtime_sheet = load_dynamic_excel_sheet('Sheet2', fallback_header_row=2)

    if runtime_sheet is not None and not runtime_sheet.empty:
        r_df = runtime_sheet.copy()
        f_col = r_df.columns[0]
        
        r_df = r_df[r_df[f_col].astype(str).str.contains('Date|From|Total|Running') == False]
        r_df[f_col] = fast_parse_dates(r_df[f_col])
        r_df = r_df.dropna(subset=[f_col]).sort_values(by=f_col)
        
        kwh_fields = [c for c in r_df.columns if 'KWH' in str(c).upper()]
        for field in kwh_fields:
            r_df[field] = pd.to_numeric(r_df[field], errors='coerce').fillna(0)
            
        if kwh_fields and not r_df.empty:
            st.markdown(f"<h5 style='color:#1E1E2F;'>⚡ Active Load Consumption Volume Chart ({kwh_fields[0]})</h5>", unsafe_allow_html=True)
            st.bar_chart(r_df.set_index(f_col)[kwh_fields[0]], color="#FF9F43")
            
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("🔍 Expand Active Duty Asset Ledger (Sheet 2 Raw)"):
            st.dataframe(r_df, use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ 'Power consumption freon.xlsx' (Sheet 2) is currently empty or file pointer path is broken.")


# ==========================================================
# TAB 4: NEW COMPRESSOR OPTIMIZATION & GRAPHICAL SUITE
# ==========================================================
with tab_compressor:
    st.markdown("### 📉 Compressor Machinery Optimization Analytics Suite")
    compressor_sheet = load_dynamic_excel_sheet('Sheet3', fallback_header_row=3)

    if compressor_sheet is not None and not compressor_sheet.empty:
        c_df = compressor_sheet.copy()
        
        # Clean out multi-level descriptive headers sitting in data rows
        c_df = c_df[c_df.iloc[:, 0].astype(str).str.strip().str.lower().str.contains('date|total|stop|start') == False]
        c_df.iloc[:, 0] = fast_parse_dates(c_df.iloc[:, 0])
        c_df = c_df.dropna(subset=[c_df.columns[0]]).sort_values(by=c_df.columns[0])
        
        # Locate the exact savings index column
        savings_hr_col = [c for c in c_df.columns if 'saving' in str(c).lower() or 'hrs' in str(c).lower()]
        
        if savings_hr_col:
            target_hr_col = savings_hr_col[0]
            c_df[target_hr_col] = pd.to_numeric(c_df[target_hr_col], errors='coerce').fillna(0)
            
            # CRITICAL: Vectorized cumulative running total calculation row
            c_df['Cumulative Saved Run Hours'] = c_df[target_hr_col].cumsum()
            
            # Display metrics cards
            tot_saved_hours = c_df[target_hr_col].sum()
            avg_saved_hours = c_df[target_hr_col].mean()
            
            m1, m2 = st.columns(2)
            with m1:
                st.metric("Total Accumulated Saved Machinery Run Time", f"{tot_saved_hours:,.1f} Hours", delta="Optimization Gain", delta_color="inverse")
            with m2:
                st.metric("Average Daily Breaks/Savings Window", f"{avg_saved_hours:.1f} Hours / Day", delta="Machinery Rest Standard")
            
            # NEW COMPRESSOR GRAPHICAL ANALYTICS LAYOUT
            st.markdown("---")
            graph_col1, graph_col2 = st.columns(2)
            
            with graph_col1:
                st.markdown("<h5 style='color:#1E1E2F;'>🕒 Chart A: Daily Maintenance Optimization Windows (Hours)</h5>", unsafe_allow_html=True)
                st.line_chart(c_df.set_index(c_df.columns[0])[target_hr_col], color="#9B5DE5")
                st.caption("Tracks day-by-day downtime allocation and optimization intervals across June.")
                
            with graph_col2:
                st.markdown("<h5 style='color:#1E1E2F;'>📈 Chart B: Progressive Running Sum (Cumulative Hours Saved)</h5>", unsafe_allow_html=True)
                st.area_chart(c_df.set_index(c_df.columns[0])['Cumulative Saved Run Hours'], color="#F15BB5")
                st.caption("Demonstrates the absolute accumulated volume of saved operating hours over the month layout.")
        else:
            st.warning("⚠️ Optimization column ('Saving in hrs') not detected in Sheet 3 header layers.")
            
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("🔍 Expand Compressor Runtime Ledger (Sheet 3 Raw)"):
            st.dataframe(c_df, use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ 'Power consumption freon.xlsx' (Sheet 3) is currently empty or file pointer path is broken.")
