import streamlit as st
import pandas as pd
import glob
import os
import warnings

# Suppress harmless openpyxl styling/validation warnings
warnings.filterwarnings("ignore", category=UserWarning)

# Configure wide premium responsive structural layout
st.set_page_config(
    page_title="Plant Operational Intelligence Hub",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MODERN STYLING INJECTION ---
st.markdown("""
    <style>
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] {
            background-color: #F8F9FA;
            border: 1px solid #E6E8EC;
            border-radius: 6px 6px 0px 0px;
            padding: 10px 20px;
            font-weight: 600;
            color: #4A4A6A;
        }
        .stTabs [data-baseweb="tab"]:hover { color: #00D2FF; }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: #1E1E2F;
            color: white;
            border-color: #1E1E2F;
        }
        .kpi-card {
            background-color: #FFFFFF;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            border-left: 5px solid #00D2FF;
            text-align: left;
        }
    </style>
""", unsafe_allow_html=True)


# --- SIDEBAR CONTROL CENTER & PATH RESOLVER ---
st.sidebar.markdown("""
    <div style="background-color:#1E1E2F; padding:15px; border-radius:8px; margin-bottom:20px;">
        <h3 style="color:white; margin:0; font-size:16px;">⚙️ System Configuration</h3>
    </div>
""", unsafe_allow_html=True)

# Interactive OneDrive Path adjustments
user_name = st.sidebar.text_input("Windows Username Shortcut", value="YourName")
company_name = st.sidebar.text_input("OneDrive Company Name", value="CompanyName")

ONEDRIVE_PATH = f"C:/Users/{user_name}/OneDrive - {company_name}/Plant_Reports/"
LOCAL_PATH = "./"

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Live Data Source Pipeline")

def get_valid_file_path(filename, search_pattern=False):
    """Checks OneDrive first; if folder structure isn't verified, falls back locally."""
    if search_pattern:
        onedrive_files = glob.glob(os.path.join(ONEDRIVE_PATH, filename))
        if onedrive_files:
            return onedrive_files, "Cloud Sync Enabled"
        local_files = glob.glob(os.path.join(LOCAL_PATH, filename))
        return local_files, "Local Fallback Active" if local_files else "Missing"
    else:
        onedrive_file = os.path.join(ONEDRIVE_PATH, filename)
        if os.path.exists(onedrive_file):
            return onedrive_file, "Cloud Sync Enabled"
        return os.path.join(LOCAL_PATH, filename), "Local Active"

# Network/File pipeline checks to display visual status indicators on sidebar
temp_files, temp_status = get_valid_file_path("DataLog_*.csv", search_pattern=True)
excel_file, excel_status = get_valid_file_path('Power consumption freon.xlsx')
excel_exists = os.path.exists(excel_file)

if temp_status == "Cloud Sync Enabled" or temp_status == "Local Fallback Active":
    st.sidebar.success(f"🌡️ Telemetry Logs: {temp_status}")
else:
    st.sidebar.error("❌ Telemetry Logs: File Data Interrupted")

if excel_exists:
    st.sidebar.success(f"⚡ Energy Asset: Connected")
else:
    st.sidebar.error("❌ Energy Asset: Workbook Missing")


# --- ENGINE TO REPAIR MIXED DATE FORMATS ---
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
    return pd.to_datetime(val, errors='coerce')


# --- DATA PIPELINE LOADERS ---
@st.cache_data
def load_temperature_data():
    files, _ = get_valid_file_path("DataLog_*.csv", search_pattern=True)
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
                df[col] = pd.to_numeric(df[col], errors='coerce').ffill().bfill()
            df['Time'] = pd.to_datetime(df['Time'], dayfirst=True, errors='coerce')
            df['Time'] = df['Time'].apply(lambda x: x.replace(month=7) if pd.notnull(x) else x)
            all_dfs.append(df)
            
    if not all_dfs:
        return None
    return pd.concat(all_dfs, ignore_index=True).drop_duplicates(subset=['Time']).sort_values(by='Time')

@st.cache_data
def load_excel_sheet(sheet_name, row_header):
    file_path, _ = get_valid_file_path('Power consumption freon.xlsx')
    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=row_header, engine='openpyxl')
        df = df.dropna(axis=1, how='all')
        if not df.empty:
            first_col = df.columns[0]
            df = df[df[first_col].astype(str).str.strip().str.lower() != 'total']
        return df
    except:
        return None


# --- MAIN HEADER DESIGN BLOCK ---
st.markdown("""
    <div style="background-color:#1E1E2F; padding:24px; border-radius:12px; margin-bottom:25px; border-left:8px solid #00D2FF; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
        <h1 style="color:#FFFFFF; margin:0; font-size:34px; font-family:sans-serif; font-weight:700; letter-spacing:-0.5px;">🏭 Plant Operations Intelligence Hub</h1>
        <p style="color:#A3A3C2; margin:6px 0 0 0; font-size:16px; font-family:sans-serif;">Real-Time Thermal Telemetry Monitoring & Infrastructure Energy Audits</p>
    </div>
""", unsafe_allow_html=True)


# --- INITIALIZE TAB NAVIGATION ---
tab_thermal, tab_power, tab_runtime, tab_compressor = st.tabs([
    "🌡️ Thermal Monitoring", 
    "⚡ Energy & Savings", 
    "⚙️ Asset Duty Cycles", 
    "📉 Compressor Optimization"
])


# ==========================================================
# SYSTEM TAB 1: TEMPERATURE TELEMETRY PANEL
# ==========================================================
with tab_thermal:
    st.markdown("### 📊 Cryogenic & Cold Storage Thermal Profiles")
    temp_df = load_temperature_data()

    if temp_df is not None and not temp_df.empty:
        latest_row = temp_df.iloc[-1]
        
        # Premium responsive KPI metric display blocks
        kpi1, kpi2, kpi3 = st.columns(3)
        with kpi1:
            st.markdown(f"""
                <div class="kpi-card" style="border-left-color: #0068C9;">
                    <span style="color:#6C757D; font-size:12px; font-weight:600; text-transform:uppercase; letter-spacing:1px;">❄️ Dough Cooler 1</span>
                    <h2 style="margin:8px 0 0 0; color:#1A1D20; font-size:32px; font-weight:700;">{latest_row['Dough Cooler1 Temp']:.2f} °C</h2>
                    <p style="margin:4px 0 0 0; color:#28A745; font-size:12px; font-weight:500;">● Active Streaming</p>
                </div>
            """, unsafe_allow_html=True)
        with kpi2:
            st.markdown(f"""
                <div class="kpi-card" style="border-left-color: #29B6F6;">
                    <span style="color:#6C757D; font-size:12px; font-weight:600; text-transform:uppercase; letter-spacing:1px;">❄️ Dough Cooler 2</span>
                    <h2 style="margin:8px 0 0 0; color:#1A1D20; font-size:32px; font-weight:700;">{latest_row['Dough Cooler2 Temp']:.2f} °C</h2>
                    <p style="margin:4px 0 0 0; color:#28A745; font-size:12px; font-weight:500;">● Active Streaming</p>
                </div>
            """, unsafe_allow_html=True)
        with kpi3:
            st.markdown(f"""
                <div class="kpi-card" style="border-left-color: #FF4B4B;">
                    <span style="color:#6C757D; font-size:12px; font-weight:600; text-transform:uppercase; letter-spacing:1px;">🥩 Perishable Storage</span>
                    <h2 style="margin:8px 0 0 0; color:#1A1D20; font-size:32px; font-weight:700;">{latest_row['Perishable Cooler Temp']:.2f} °C</h2>
                    <p style="margin:4px 0 0 0; color:#28A745; font-size:12px; font-weight:500;">● Active Streaming</p>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br><h5 style='color:#2E3A59;'>📈 Continuous Temperature Baseline Analytics</h5>", unsafe_allow_html=True)
        st.line_chart(temp_df.set_index('Time'), color=["#0068C9", "#29B6F6", "#FF4B4B"])
    else:
        st.warning("⚠️ Displaying structural frames. Please ensure your 'DataLog_*.csv' telemetry logs are added to the folder path.")


# ==========================================================
# SYSTEM TAB 2: POWER CONSUMPTION & METRICS
# ==========================================================
with tab_power:
    st.markdown("### 🔋 Core Load Distribution & Operational Savings")
    power_sheet = load_excel_sheet('Sheet1', row_header=1)

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
            
            # Premium native metric row
            sm1, sm2, sm3 = st.columns(3)
            with sm1:
                st.container(border=True).metric("Dunkin Blast Accumulated Draw", f"{dunkin_sum:,.1f} kWh", delta="System Load")
            with sm2:
                st.container(border=True).metric("CLC Blast Accumulated Draw", f"{clc_sum:,.1f} kWh", delta="System Load")
            with sm3:
                st.container(border=True).metric("Net Financial Optimization Balance", f"INR {savings_sum:,.2f}", delta="Efficiency Savings", delta_color="inverse")
            
            # Side-by-side analytical graphical distribution grid
            graph_col1, graph_col2 = st.columns(2)
            with graph_col1:
                st.markdown("<h5 style='color:#2E3A59;'>⚡ Comparative Infrastructure Heavy Draw Profiles</h5>", unsafe_allow_html=True)
                st.area_chart(filtered_p_df.set_index('Date')[['Dunkin Blast', 'CLC Blast']], color=["#1A5F7A", "#57C5B6"])
            with graph_col2:
                st.markdown("<h5 style='color:#2E3A59;'>💰 Daily Financial Efficiency Margins</h5>", unsafe_allow_html=True)
                st.bar_chart(filtered_p_df.set_index('Date')['Savings'], color="#28A745")
            
            # OneDrive background sync logic validation
            if os.path.exists(ONEDRIVE_PATH):
                filtered_p_df.to_csv(os.path.join(ONEDRIVE_PATH, "Clean_Daily_Power_Metrics.csv"), index=False)
                
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("🔍 View Detailed Energy Ledger (Sheet 1 Raw)"):
                st.dataframe(filtered_p_df, use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ 'Power consumption freon.xlsx' (Sheet 1) not discovered or layout values are currently empty.")


# ==========================================================
# SYSTEM TAB 3: ASSET DUTY CYCLES
# ==========================================================
with tab_runtime:
    st.markdown("### ⚙️ Cold Storage Unit Active Duty Cycles")
    runtime_sheet = load_excel_sheet('Sheet2', row_header=2)

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
            st.markdown(f"<h5 style='color:#2E3A59;'>⚡ Measured Running Capacity Draw Performance ({kwh_cols[0]})</h5>", unsafe_allow_html=True)
            st.bar_chart(r_df.set_index(first_col)[kwh_cols[0]], color="#FF9F43")
            
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("🔍 View Detailed Operational Running Duty Logs (Sheet 2 Raw)"):
            st.dataframe(r_df, use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ 'Power consumption freon.xlsx' (Sheet 2) not discovered or layout values are currently empty.")


# ==========================================================
# SYSTEM TAB 4: COMPRESSOR MAINTENANCE OPTIMIZATION
# ==========================================================
with tab_compressor:
    st.markdown("### 📉 Compressor Machinery Optimization Analytics")
    compressor_sheet = load_excel_sheet('Sheet3', row_header=3)

    if compressor_sheet is not None and not compressor_sheet.empty:
        c_df = compressor_sheet.copy()
        c_df = c_df[c_df.iloc[:, 0].astype(str).str.strip().str.lower().str.contains('date|total') == False]
        c_df.iloc[:, 0] = c_df.iloc[:, 0].apply(parse_power_sheet_date)
        c_df = c_df.dropna(subset=[c_df.columns[0]]).sort_values(by=c_df.columns[0])
        
        if 'Saving in hrs' in c_df.columns:
            c_df['Saving in hrs'] = pd.to_numeric(c_df['Saving in hrs'], errors='coerce').fillna(0)
            
            st.markdown("<h5 style='color:#2E3A59;'>📉 Calculated Maintenance Savings Windows (Total Hours)</h5>", unsafe_allow_html=True)
            st.line_chart(c_df.set_index(c_df.columns[0])['Saving in hrs'], color="#9B5DE5")
            
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("🔍 View Detailed Compressor Runtime Ledger (Sheet 3 Raw)"):
            st.dataframe(c_df, use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ 'Power consumption freon.xlsx' (Sheet 3) not discovered or layout values are currently empty.")
