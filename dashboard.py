import streamlit as st
import pandas as pd
import glob
import os
import warnings

# Suppress harmless openpyxl styling/validation alerts
warnings.filterwarnings("ignore", category=UserWarning)

# --- JUBILANT PREMIUM DARK MODE CONFIGURATION ---
st.set_page_config(
    page_title="Jubilant FoodWorks - Plant Operational Intelligence Hub",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ENTERPRISE DARK THEME CUSTOM CSS INJECTION ---
st.markdown("""
    <style>
        /* Base Canvas & Background Dark Settings */
        .block-container { padding-top: 1.5rem; padding-bottom: 3rem; background-color: #0B0F19; }
        
        /* Premium Navigation Tabs - JFL Dark Theme Custom Style */
        .stTabs [data-baseweb="tab-list"] { gap: 12px; padding-left: 5px; background-color: transparent; }
        .stTabs [data-baseweb="tab"] {
            background-color: #131B2E;
            border: 1px solid #1E293B;
            border-bottom: none;
            border-radius: 6px 6px 0px 0px;
            padding: 14px 28px;
            font-weight: 700;
            color: #94A3B8;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            transition: all 0.25s ease-in-out;
        }
        .stTabs [data-baseweb="tab"]:hover { 
            color: #E01934; 
            background-color: #1A243D; 
            border-top: 3px solid #E01934;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: #002D62; /* JFL Corporate Deep Navy Main Accent */
            color: #FFFFFF !important;
            border-color: #1E293B;
            border-top: 3px solid #FF9F1C; /* Corporate Gold Trim Ring */
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        }
        
        /* High-End JFL Card Containers (Dark Theme Optimization) */
        div[data-testid="stMetric"] {
            background-color: #131B2E !important;
            border: 1px solid #1E293B !important;
            border-top: 4px solid #002D62 !important; 
            padding: 22px !important;
            border-radius: 8px !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25) !important;
            transition: transform 0.2s ease;
        }
        div[data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 15px rgba(0, 212, 255, 0.08) !important;
        }
        
        /* Color Overrides for Complete Text Readability */
        div[data-testid="stMetricLabel"] p {
            color: #94A3B8 !important;              
            font-size: 13px !important;
            font-weight: 700 !important;
            letter-spacing: 0.8px !important;
            text-transform: uppercase !important;
            font-family: 'Segoe UI', sans-serif;
        }
        div[data-testid="stMetricValue"] div {
            color: #FFFFFF !important;              /* Crisp clear white display values */
            font-size: 34px !important;
            font-weight: 800 !important;
        }
        
        /* Custom Clean Dark Corporate Sidebar Look */
        section[data-testid="stSidebar"] {
            background-color: #0B0F19 !important;
            border-right: 1px solid #1E293B !important;
        }
    </style>
""", unsafe_allow_html=True)


# --- SIDEBAR CONTROL CENTER & FILE PIPELINE ---
st.sidebar.markdown("""
    <div style="background-color:#002D62; padding:18px; border-radius:6px; margin-bottom:15px; border-bottom:4px solid #FF9F1C;">
        <h3 style="color:white; margin:0; font-size:14px; font-weight:700; letter-spacing:0.5px; font-family:sans-serif;">CONFIG PANEL</h3>
    </div>
""", unsafe_allow_html=True)

user_name = st.sidebar.text_input("Windows User Profile", value="aayush")
company_folder = st.sidebar.text_input("OneDrive Path Segment", value="OneDrive")

ONEDRIVE_PATH = f"C:/Users/{user_name}/{company_folder}/PlantData/"
LOCAL_PATH = "./"

st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='color:#FFFFFF; font-size:13px; font-weight:700; text-transform: uppercase; letter-spacing:0.5px;'>Active Pipeline Nodes</h4>", unsafe_allow_html=True)

def resolve_file_pipeline(filename, is_pattern=False):
    """Smarter path resolver prioritizing active synchronized cloud directories."""
    if is_pattern:
        cloud_nodes = glob.glob(os.path.join(ONEDRIVE_PATH, filename))
        if cloud_nodes: return cloud_nodes, "Cloud Link Active"
        local_nodes = glob.glob(os.path.join(LOCAL_PATH, filename))
        return local_nodes, "Local Fallback" if local_nodes else "Disconnected"
    else:
        cloud_node = os.path.join(ONEDRIVE_PATH, filename)
        if os.path.exists(cloud_node): return cloud_node, "Cloud Link Active"
        return os.path.join(LOCAL_PATH, filename), "Local Active"

# Telemetry data link validation
temp_nodes, temp_status = resolve_file_pipeline("DataLog_*.csv", is_pattern=True)
excel_node, excel_status = resolve_file_pipeline('Power consumption freon.xlsx')
excel_connected = os.path.exists(excel_node)

if temp_status != "Disconnected":
    st.sidebar.markdown(f"<p style='color:#28A745; font-size:13px; font-weight:600;'>● Real-Time Temperature Feed: Connected</p>", unsafe_allow_html=True)
else:
    st.sidebar.markdown("<p style='color:#DC3545; font-size:13px; font-weight:600;'>■ Real-Time Temperature Feed: Data Offline</p>", unsafe_allow_html=True)

if excel_connected:
    st.sidebar.markdown(f"<p style='color:#28A745; font-size:13px; font-weight:600;'>● Infrastructure Energy Logs: Connected</p>", unsafe_allow_html=True)
else:
    st.sidebar.markdown("<p style='color:#DC3545; font-size:13px; font-weight:600;'>■ Infrastructure Energy Logs: File Missing</p>", unsafe_allow_html=True)


# --- CACHED DATA PIPELINE LOADERS ---
def fast_parse_dates(series):
    string_series = series.astype(str).str.strip().str.split(' ').str[0]
    return pd.to_datetime(string_series, errors='coerce', dayfirst=True)

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


# --- JUBILANT FOODWORKS MASTER DARK BANNER ---
st.markdown("""
    <div style="background-color:#131B2E; padding:24px; border-radius:10px; margin-bottom:30px; border-left:10px solid #E01934; box-shadow: 0 4px 20px rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: space-between; border-top: 1px solid #1E293B; border-right: 1px solid #1E293B;">
        <div>
            <h1 style="color:#FFFFFF; margin:0; font-size:28px; font-family:'Segoe UI', sans-serif; font-weight:800; letter-spacing:-0.5px;">JUBILANT FOODWORKS LIMITED</h1>
            <p style="color:#94A3B8; margin:4px 0 0 0; font-size:13px; font-weight:600; font-family:'Segoe UI', sans-serif; text-transform: uppercase; letter-spacing: 0.5px;">Supply Chain Operations & Infrastructure Telemetry Control Hub</p>
        </div>
        <div style="background-color: #002D62; padding: 10px 18px; border-radius: 4px; border: 1px solid #FF9F1C;">
            <span style="color: #FFFFFF; font-family: Arial, sans-serif; font-weight: 700; font-size: 13px; letter-spacing: 1px; text-transform: uppercase;">Internal Node Monitor</span>
        </div>
    </div>
""", unsafe_allow_html=True)


# --- PRIMARY TAB NAVIGATION GRIDS ---
tab_thermal, tab_power, tab_runtime, tab_compressor = st.tabs([
    "🌡️ Cold Storage Thermal Profiles", 
    "⚡ Energy Management & Savings", 
    "⚙️ Plant Asset Duty Cycles", 
    "📉 Compressor Optimization Analytics"
])


# ==========================================================
# TAB 1: COLD STORAGE THERMAL PROFILES (DARK)
# ==========================================================
with tab_thermal:
    st.markdown("<h4 style='color:#FFFFFF; font-weight:700; font-size:18px;'>Live Cold Chain Temperature Log Matrix</h4>", unsafe_allow_html=True)
    temp_df = load_cached_telemetry()

    if temp_df is not None and not temp_df.empty:
        latest = temp_df.iloc[-1]
        
        k1, k2, k3 = st.columns(3)
        with k1:
            st.metric(label="Dough Cooler 1", value=f"{latest['Dough Cooler1 Temp']:.2f} °C", delta="Telemetry Stream Stable")
        with k2:
            st.metric(label="Dough Cooler 2", value=f"{latest['Dough Cooler2 Temp']:.2f} °C", delta="Telemetry Stream Stable")
        with k3:
            st.metric(label="Perishable Storage Room", value=f"{latest['Perishable Cooler Temp']:.2f} °C", delta="Thermal Load Variance Alert", delta_color="inverse")
        
        st.markdown("<br><h5 style='color:#94A3B8; font-weight:700; font-size:14px;'>Continuous Thermodynamic Stream Data (5-Minute Sampling Resolution)</h5>", unsafe_allow_html=True)
        st.line_chart(temp_df.set_index('Time'), color=["#00D2FF", "#29B6F6", "#E01934"])
    else:
        st.warning("System idling. Verify presence of telemetry 'DataLog_*.csv' source files to populate records.")


# ==========================================================
# TAB 2: ENERGY MANAGEMENT & SAVINGS (DARK)
# ==========================================================
with tab_power:
    st.markdown("<h4 style='color:#FFFFFF; font-weight:700; font-size:18px;'>Core Power Load Distribution & Grid Efficiencies</h4>", unsafe_allow_html=True)
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
                st.metric("Dunkin' Blast Line Consumption", f"{dunkin_tot:,.1f} kWh", delta="Grid Line A Load")
            with sm2:
                st.metric("CLC Blast Line Consumption", f"{clc_tot:,.1f} kWh", delta="Grid Line B Load")
            with sm3:
                st.metric("Calculated Operational Savings", f"INR {savings_tot:,.2f}", delta="Net Utility Recovery", delta_color="inverse")
            
            g_col1, g_col2 = st.columns(2)
            with g_col1:
                st.markdown("<h5 style='color:#94A3B8; font-weight:700; font-size:14px;'>Comparative Secondary Draw Profiles (Area Distribution Metric)</h5>", unsafe_allow_html=True)
                st.area_chart(filtered_p_df.set_index('Date')[['Dunkin Blast', 'CLC Blast']], color=["#00D2FF", "#FF9F1C"])
            with g_col2:
                st.markdown("<h5 style='color:#94A3B8; font-weight:700; font-size:14px;'>Daily Cost Optimization Margins</h5>", unsafe_allow_html=True)
                st.bar_chart(filtered_p_df.set_index('Date')[savings_title], color="#28A745")
                
            if os.path.exists(ONEDRIVE_PATH):
                filtered_p_df.to_csv(os.path.join(ONEDRIVE_PATH, "Clean_Daily_Power_Metrics.csv"), index=False)
                
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("🔍 Open Full Audited Infrastructure Energy Spreadsheet (Sheet 1 Raw Ledger)"):
                st.dataframe(filtered_p_df, use_container_width=True, hide_index=True)
    else:
        st.info("Energy logging source workbook ('Power consumption freon.xlsx' Sheet 1) not parsed.")


# ==========================================================
# TAB 3: PLANT ASSET DUTY CYCLES (DARK)
# ==========================================================
with tab_runtime:
    st.markdown("<h4 style='color:#FFFFFF; font-weight:700; font-size:18px;'>Active Infrastructure Component Load Capacity Logs</h4>", unsafe_allow_html=True)
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
            st.markdown(f"<h5 style='color:#94A3B8; font-weight:700; font-size:14px;'>Active Power Draw Threshold Volume ({kwh_fields[0]})</h5>", unsafe_allow_html=True)
            st.bar_chart(r_df.set_index(f_col)[kwh_fields[0]], color="#E01934")
            
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("🔍 Open Plant Asset Active Duty Ledger (Sheet 2 Raw Data)"):
            st.dataframe(r_df, use_container_width=True, hide_index=True)
    else:
        st.info("Component run-hour logging sheet (Sheet 2) not parsed.")


# ==========================================================
# TAB 4: COMPRESSOR OPTIMIZATION ANALYTICS (DARK)
# ==========================================================
with tab_compressor:
    st.markdown("<h4 style='color:#FFFFFF; font-weight:700; font-size:18px;'>Refrigeration Compressor Group Rest Allocation & Optimization Analytics</h4>", unsafe_allow_html=True)
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
            
            # Progressive running summation computation
            c_df['Cumulative Maintenance Rest Hours'] = c_df[target_hr_col].cumsum()
            
            tot_saved_hours = c_df[target_hr_col].sum()
            avg_saved_hours = c_df[target_hr_col].mean()
            
            m1, m2 = st.columns(2)
            with m1:
                st.metric("Total Accumulated Rest Window Allocation", f"{tot_saved_hours:,.1f} Hours", delta="Optimization Asset Yield Recovery")
            with m2:
                st.metric("Mean Daily Component Relief Window", f"{avg_saved_hours:.1f} Hours / Day", delta="Standard Maintenance Benchmarked")
            
            st.markdown("---")
            graph_col1, graph_col2 = st.columns(2)
            
            with graph_col1:
                st.markdown("<h5 style='color:#94A3B8; font-weight:700; font-size:14px;'>Machinery Structural Relief Allocation (Daily Rest Hours)</h5>", unsafe_allow_html=True)
                st.line_chart(c_df.set_index(c_df.columns[0])[target_hr_col], color="#00D2FF")
                st.caption("Day-by-day downtime interval mapping across the operational cycle.")
                
            with graph_col2:
                st.markdown("<h5 style='color:#94A3B8; font-weight:700; font-size:14px;'>Progressive Total Machinery Rest Accumulation (Running Balance)</h5>", unsafe_allow_html=True)
                st.area_chart(c_df.set_index(c_df.columns[0])['Cumulative Maintenance Rest Hours'], color="#FF9F1C")
                st.caption("Demonstrates the absolute cumulative volume of optimized component resting metrics.")
        else:
            st.warning("Optimization target column ('Saving in hrs') not detected in Sheet 3 header data layout.")
            
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("🔍 Open Full Compressor Machinery Runtime Ledger (Sheet 3 Raw Data)"):
            st.dataframe(c_df, use_container_width=True, hide_index=True)
    else:
        st.info("Compressor cycle management sheet (Sheet 3) not parsed.")
