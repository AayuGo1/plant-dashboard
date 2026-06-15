import streamlit as st
import pandas as pd
import glob
import os
import warnings

# Suppress harmless openpyxl styling/validation alerts
warnings.filterwarnings("ignore", category=UserWarning)

# --- JUBILANT CORPORATE LAYOUT SETUP ---
st.set_page_config(
    page_title="Jubilant FoodWorks - Plant Operational Intelligence Center",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- BRANDED HIGH-END CUSTOM CSS INJECTION ---
st.markdown("""
    <style>
        /* Base Canvas & Background Settings */
        .block-container { padding-top: 1.5rem; padding-bottom: 3rem; background-color: #F4F7FC; }
        
        /* Premium Navigation Tabs Custom Jubilant Branding Style */
        .stTabs [data-baseweb="tab-list"] { gap: 12px; padding-left: 5px; }
        .stTabs [data-baseweb="tab"] {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-bottom: none;
            border-radius: 6px 6px 0px 0px;
            padding: 14px 28px;
            font-weight: 700;
            color: #4A5568;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            transition: all 0.25s ease-in-out;
            box-shadow: 0 -2px 5px rgba(0,0,0,0.02);
        }
        .stTabs [data-baseweb="tab"]:hover { 
            color: #E01934; 
            background-color: #FFF5F5; 
            border-top: 3px solid #E01934;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: #002D62; /* JFL Corporate Deep Navy */
            color: #FFFFFF !important;
            border-color: #002D62;
            border-top: 3px solid #FF9F1C; /* Golden Accent Ring */
            box-shadow: 0 4px 12px rgba(0,45,98,0.15);
        }
        
        /* High-End JFL Enterprise Container Style for Native Metrics */
        div[data-testid="stMetric"] {
            background-color: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-top: 4px solid #002D62 !important; /* Branded Top Border */
            padding: 22px !important;
            border-radius: 8px !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.04) !important;
            transition: transform 0.2s ease;
        }
        div[data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0, 45, 98, 0.08) !important;
        }
        
        /* Color Overrides for Data Metric Elements */
        div[data-testid="stMetricLabel"] p {
            color: #4A5568 !important;              
            font-size: 13px !important;
            font-weight: 700 !important;
            letter-spacing: 0.8px !important;
            text-transform: uppercase !important;
            font-family: 'Segoe UI', sans-serif;
        }
        div[data-testid="stMetricValue"] div {
            color: #002D62 !important;              /* High-contrast brand navy display values */
            font-size: 34px !important;
            font-weight: 800 !important;
        }
        
        /* Clean Custom Corporate Sidebar Look */
        section[data-testid="stSidebar"] {
            background-color: #FFFFFF !important;
            border-right: 1px solid #E2E8F0 !important;
        }
    </style>
""", unsafe_allow_html=True)


# --- SIDEBAR CONTROL CENTER & AUTOMATION ROUTING ---
st.sidebar.markdown("""
    <div style="background-color:#002D62; padding:18px; border-radius:6px; margin-bottom:15px; border-bottom:4px solid #FF9F1C;">
        <h3 style="color:white; margin:0; font-size:15px; font-weight:700; letter-spacing:0.5px; font-family:sans-serif;">⚙️ JFL SYSTEM PROFILE</h3>
    </div>
""", unsafe_allow_html=True)

# Live system environment input nodes
user_name = st.sidebar.text_input("System Username", value="aayush")
company_folder = st.sidebar.text_input("OneDrive Main Node", value="OneDrive")

ONEDRIVE_PATH = f"C:/Users/{user_name}/{company_folder}/PlantData/"
LOCAL_PATH = "./"

st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='color:#002D62; font-size:14px; font-weight:700;'>🛰️ Node Connection Status</h4>", unsafe_allow_html=True)

def resolve_file_pipeline(filename, is_pattern=False):
    """Smarter path resolver prioritizing active synchronized cloud directories."""
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
    st.sidebar.markdown(f"<p style='color:#28A745; font-size:13px; font-weight:600;'>● Telemetry Feed: {temp_status}</p>", unsafe_allow_html=True)
else:
    st.sidebar.markdown("<p style='color:#DC3545; font-size:13px; font-weight:600;'>■ Telemetry Feed: Interrupted</p>", unsafe_allow_html=True)

if excel_connected:
    st.sidebar.markdown(f"<p style='color:#28A745; font-size:13px; font-weight:600;'>● Plant Energy Ledger: Connected</p>", unsafe_allow_html=True)
else:
    st.sidebar.markdown("<p style='color:#DC3545; font-size:13px; font-weight:600;'>■ Plant Energy Ledger: Offline</p>", unsafe_allow_html=True)


# --- FAST VECTORIZED DATE CONVERTER ---
def fast_parse_dates(series):
    """Efficiently cleans and formats inconsistent plant logging timestamps."""
    string_series = series.astype(str).str.strip().str.split(' ').str[0]
    cleaned_dates = pd.to_datetime(string_series, errors='coerce', dayfirst=True)
    return cleaned_dates


# --- CACHED DATA PIPELINE LOADERS ---
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
        df_check = pd.read_excel(file_path, sheet_name=sheet_name, header=None, engine='openpyxl')
        discovered_idx = fallback_header_row
        
        for idx in range(min(10, len(df_check))):
            row_items = [str(x).lower() for x in df_check.iloc[idx].dropna().tolist()]
            if any('date' in item or 'stop time' in item for item in row_items):
                discovered_idx = idx
                break
                
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=discovered_idx, engine='openpyxl')
        df = df.dropna(axis=1, how='all')
        if not df.empty:
            first_col = df.columns[0]
            df = df[df[first_col].astype(str).str.strip().str.lower() != 'total']
            df.columns = [f"Saving in hrs" if "Unnamed:" in str(c) and idx==11 else str(c) for idx, c in enumerate(df.columns)]
        return df
    except:
        return None


# --- JUBILANT FOODWORKS ENTERPRISE BANNER ---
st.markdown("""
    <div style="background-color:#FFFFFF; padding:24px; border-radius:10px; margin-bottom:30px; border-left:10px solid #E01934; box-shadow: 0 4px 15px rgba(0,0,0,0.05); display: flex; align-items: center; justify-content: space-between;">
        <div>
            <h1 style="color:#002D62; margin:0; font-size:30px; font-family:'Segoe UI', sans-serif; font-weight:800; letter-spacing:-0.5px;">JUBILANT FOODWORKS LIMITED</h1>
            <p style="color:#718096; margin:6px 0 0 0; font-size:14px; font-weight:600; font-family:'Segoe UI', sans-serif; text-transform: uppercase; letter-spacing: 0.5px;">🏭 Supply Chain Operations & Automated Telemetry Analytics Hub</p>
        </div>
        <div style="background-color: #002D62; padding: 12px 20px; border-radius: 6px; border: 1px solid #FF9F1C;">
            <span style="color: #FFFFFF; font-family: sans-serif; font-weight: 800; font-size: 15px; letter-spacing: 1px;">JFL-INTELLIGENCE</span>
        </div>
    </div>
""", unsafe_allow_html=True)


# --- INITIATE NAVIGATION GRIDS ---
tab_thermal, tab_power, tab_runtime, tab_compressor = st.tabs([
    "🌡️ Cold Storage Thermal Profiles", 
    "⚡ Energy Management & Savings", 
    "⚙️ Plant Asset Duty Cycles", 
    "📉 Compressor Optimization Analytics"
])


# ==========================================================
# SYSTEM TAB 1: REAL-TIME THERMAL SNAPSHOTS
# ==========================================================
with tab_thermal:
    st.markdown("<h4 style='color:#002D62; font-family: sans-serif; font-weight:700;'>📊 Live Cold Chain Temperature Matrix</h4>", unsafe_allow_html=True)
    temp_df = load_cached_telemetry()

    if temp_df is not None and not temp_df.empty:
        latest = temp_df.iloc[-1]
        
        k1, k2, k3 = st.columns(3)
        with k1:
            st.metric(
                label="❄️ DOUGH COOLER 1", 
                value=f"{latest['Dough Cooler1 Temp']:.2f} °C", 
                delta="Streaming Online", 
                delta_color="normal"
            )
        with k2:
            st.metric(
                label="❄️ DOUGH COOLER 2", 
                value=f"{latest['Dough Cooler2 Temp']:.2f} °C", 
                delta="Streaming Online", 
                delta_color="normal"
            )
        with k3:
            st.metric(
                label="🥩 PERISHABLE STORAGE UNIT", 
                value=f"{latest['Perishable Cooler Temp']:.2f} °C", 
                delta="Thermal Load Shift Alert", 
                delta_color="inverse"
            )
        
        st.markdown("<br><h5 style='color:#002D62; font-weight:700;'>📈 Continuous Thermodynamic Stream Logs (5-Min Interval Tracks)</h5>", unsafe_allow_html=True)
        st.line_chart(temp_df.set_index('Time'), color=["#002D62", "#29B6F6", "#E01934"])
    else:
        st.warning("⚠️ Telemetry matrix idling. Paste your 'DataLog_*.csv' files into your designated directory path to activate streaming.")


# ==========================================================
# SYSTEM TAB 2: POWER LOAD BALANCES & SAVINGS
# ==========================================================
with tab_power:
    st.markdown("<h4 style='color:#002D62; font-family: sans-serif; font-weight:700;'>🔋 Core Power Load Distribution Ledger</h4>", unsafe_allow_html=True)
    power_sheet = load_dynamic_excel_sheet('Sheet1', fallback_header_row=1)

    if power_sheet is not None and not power_sheet.empty:
        p_df = power_sheet.copy()
        p_df['Date'] = fast_parse_dates(p_df['Date'])
        p_df = p_df.dropna(subset=['Date']).sort_values(by='Date')
        
        p_df['Dunkin Blast'] = pd.to_numeric(p_df['Dunkin Blast'], errors='coerce').fillna(0)
        p_df['CLC Blast'] = pd.to_numeric(p_df['CLC Blast'], errors='coerce').fillna(0)
        
        savings_col = [c for c in p_df.columns if 'savings' in str(c).lower()]
        savings_title = savings_col[0] if savings_col else 'Savings'
        p_df[savings_title] = pd.to_numeric(p_df[savings_title], errors='coerce').fillna(0)
        
        filtered_p_df = p_df[p_df['Dunkin Blast'] < 500000].copy()
        
        if not filtered_p_df.empty:
            dunkin_tot = filtered_p_df['Dunkin Blast'].sum()
            clc_tot = filtered_p_df['CLC Blast'].sum()
            savings_tot = filtered_p_df[savings_title].sum()
            
            sm1, sm2, sm3 = st.columns(3)
            with sm1:
                st.metric("Dunkin' Blast Total Consumption", f"{dunkin_tot:,.1f} kWh", delta="JFL Grid Line A")
            with sm2:
                st.metric("CLC Blast Total Consumption", f"{clc_tot:,.1f} kWh", delta="JFL Grid Line B")
            with sm3:
                st.metric("Calculated Financial Optimization", f"INR {savings_tot:,.2f}", delta="Net Operational Savings", delta_color="inverse")
            
            g_col1, g_col2 = st.columns(2)
            with g_col1:
                st.markdown("<h5 style='color:#002D62; font-weight:700;'>⚡ Heavy Grid Load Comparison (Area Distribution)</h5>", unsafe_allow_html=True)
                st.area_chart(filtered_p_df.set_index('Date')[['Dunkin Blast', 'CLC Blast']], color=["#002D62", "#FF9F1C"])
            with g_col2:
                st.markdown("<h5 style='color:#002D62; font-weight:700;'>💰 Daily Cost Optimization Yield Trails</h5>", unsafe_allow_html=True)
                st.bar_chart(filtered_p_df.set_index('Date')[savings_title], color="#28A745")
                
            if os.path.exists(ONEDRIVE_PATH):
                filtered_p_df.to_csv(os.path.join(ONEDRIVE_PATH, "Clean_Daily_Power_Metrics.csv"), index=False)
                
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("🔍 Open Full Audited Infrastructure Energy Spreadsheet (Sheet 1 Raw)"):
                st.dataframe(filtered_p_df, use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ 'Power consumption freon.xlsx' (Sheet 1) is currently empty or file pointer path is broken.")


# ==========================================================
# SYSTEM TAB 3: ASSET OPERATIONAL RUN TIME DUTY CYCLES
# ==========================================================
with tab_runtime:
    st.markdown("<h4 style='color:#002D62; font-family: sans-serif; font-weight:700;'>⚙️ Infrastructure Plant Capacity & Duty Cycles</h4>", unsafe_allow_html=True)
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
            st.markdown(f"<h5 style='color:#002D62; font-weight:700;'>⚡ Measured Hourly Capacity Draw Tracking ({kwh_fields[0]})</h5>", unsafe_allow_html=True)
            st.bar_chart(r_df.set_index(f_col)[kwh_fields[0]], color="#E01934")
            
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("🔍 Open Plant Asset Active Duty Ledger (Sheet 2 Raw)"):
            st.dataframe(r_df, use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ 'Power consumption freon.xlsx' (Sheet 2) is currently empty or file pointer path is broken.")


# ==========================================================
# SYSTEM TAB 4: COMPRESSOR MACHINERY OPTIMIZATION GRAPHICS
# ==========================================================
with tab_compressor:
    st.markdown("<h4 style='color:#002D62; font-family: sans-serif; font-weight:700;'>📉 Compressor Plant Machinery Maintenance & Optimization Suite</h4>", unsafe_allow_html=True)
    compressor_sheet = load_dynamic_excel_sheet('Sheet3', fallback_header_row=3)

    if compressor_sheet is not None and not compressor_sheet.empty:
        c_df = compressor_sheet.copy()
        
        c_df = c_df[c_df.iloc[:, 0].astype(str).str.strip().str.lower().str.contains('date|total|stop|start') == False]
        c_df.iloc[:, 0] = fast_parse_dates(c_df.iloc[:, 0])
        c_df = c_df.dropna(subset=[c_df.columns[0]]).sort_values(by=c_df.columns[0])
        
        savings_hr_col = [c for c in c_df.columns if 'saving' in str(c).lower() or 'hrs' in str(c).lower()]
        
        if savings_hr_col:
            target_hr_col = savings_hr_col[0]
            c_df[target_hr_col] = pd.to_numeric(c_df[target_hr_col], errors='coerce').fillna(0)
            
            # COMPILE PROGRESSIVE CUMULATIVE VALUES FOR EXECUTIVE REVIEW
            c_df['Cumulative Saved Run Hours'] = c_df[target_hr_col].cumsum()
            
            tot_saved_hours = c_df[target_hr_col].sum()
            avg_saved_hours = c_df[target_hr_col].mean()
            
            m1, m2 = st.columns(2)
            with m1:
                st.metric("Total Accumulated Saved Machinery Run Time", f"{tot_saved_hours:,.1f} Hours", delta="Optimization Growth Balance", delta_color="inverse")
            with m2:
                st.metric("Average Daily Structural Rest Windows", f"{avg_saved_hours:.1f} Hours / Day", delta="Machinery Resting Standard")
            
            st.markdown("---")
            graph_col1, graph_col2 = st.columns(2)
            
            with graph_col1:
                st.markdown("<h5 style='color:#002D62; font-weight:700;'>🕒 Chart A: Daily Maintenance Optimization Windows (Hours)</h5>", unsafe_allow_html=True)
                st.line_chart(c_df.set_index(c_df.columns[0])[target_hr_col], color="#002D62")
                st.caption("Tracks day-by-day machinery structural relief windows across June operational cycles.")
                
            with graph_col2:
                st.markdown("<h5 style='color:#002D62; font-weight:700;'>📈 Chart B: Progressive Running Sum (Cumulative Hours Saved)</h5>", unsafe_allow_html=True)
                st.area_chart(c_df.set_index(c_df.columns[0])['Cumulative Saved Run Hours'], color="#FF9F1C")
                st.caption("Demonstrates the absolute accumulated running volume of saved operating hours across the month.")
        else:
            st.warning("⚠️ Optimization metric tracking column ('Saving in hrs') not detected in Sheet 3 header lines.")
            
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("🔍 Open Full Compressor Machinery Runtime Ledger (Sheet 3 Raw)"):
            st.dataframe(c_df, use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ 'Power consumption freon.xlsx' (Sheet 3) is currently empty or file pointer path is broken.")
