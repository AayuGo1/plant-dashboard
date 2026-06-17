import os
import glob
import warnings
import requests
import io
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

warnings.filterwarnings("ignore", category=UserWarning)

# ─────────────────────────────────────────────────────────────
#  GITHUB CONFIGURATION
# ─────────────────────────────────────────────────────────────
GITHUB_USER   = "AayuGo1"
GITHUB_REPO   = "plant-dashboard"
GITHUB_BRANCH = "main"

RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}"
API_BASE = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents?ref={GITHUB_BRANCH}"

# ─────────────────────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="JFL – Plant Operations Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="auto"
)

st.markdown("""
<style>
html, body, [class*="css"] { font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif; }
.block-container { padding: 1.5rem 2.5rem 3rem; background: #F4F6F9; }

section[data-testid="stSidebar"] { background: #002D62 !important; border-right: none !important; }
section[data-testid="stSidebar"] * { color: #CBD5E0 !important; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #FFFFFF !important; }
section[data-testid="stSidebar"] input {
    background: #001840 !important; border: 1px solid #1E3A8A !important;
    color: #FFFFFF !important; border-radius: 4px !important; font-size: 12px !important;
}
section[data-testid="stSidebar"] label {
    color: #94A3B8 !important; font-size: 10px !important; font-weight: 700 !important;
    text-transform: uppercase !important; letter-spacing: 0.8px !important;
}

.jfl-header-container {
    background: #FFFFFF; border-radius: 8px; padding: 24px; margin-bottom: 24px;
    border: 1px solid #E2E8F0; border-left: 6px solid #E01934;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);
}
.jfl-header-title { font-size: 24px; font-weight: 800; color: #002D62; letter-spacing: -0.5px; }
.jfl-header-subtitle { font-size: 11px; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; color: #64748B; margin-top: 4px; }
.jfl-header-meta-box { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 10px 16px; }
.jfl-meta-label { font-size: 9px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; color: #94A3B8; margin-bottom: 2px; }
.jfl-meta-value { font-size: 13px; font-weight: 700; color: #002D62; }

.stTabs [data-baseweb="tab-list"] { gap: 0; background: #FFFFFF; border-bottom: 2px solid #E2E8F0; padding: 0 8px; border-radius: 6px 6px 0 0; }
.stTabs [data-baseweb="tab"] { background: transparent; border: none; border-bottom: 3px solid transparent; padding: 14px 22px; font-size: 12.5px; font-weight: 700; color: #64748B; }
.stTabs [data-baseweb="tab"]:hover { color: #002D62; }
.stTabs [data-baseweb="tab"][aria-selected="true"] { color: #002D62 !important; border-bottom: 3px solid #E01934 !important; background: transparent !important; }

div[data-testid="stMetric"] { background: #FFFFFF !important; border: 1px solid #E2E8F0 !important; border-radius: 8px !important; padding: 20px 22px !important; box-shadow: 0 1px 4px rgba(0,0,0,0.05) !important; border-left: 5px solid #002D62 !important; }
div[data-testid="stMetricLabel"] p { color: #64748B !important; font-size: 10.5px !important; font-weight: 700 !important; letter-spacing: 0.7px !important; text-transform: uppercase !important; }
div[data-testid="stMetricValue"] div { color: #0F172A !important; font-size: 26px !important; font-weight: 800 !important; }
div[data-testid="stMetricDelta"] div { font-size: 11.5px !important; font-weight: 600 !important; }

.sec-title { font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 1px; margin: 28px 0 12px 0; padding-bottom: 8px; border-bottom: 1px solid #E2E8F0; }
.alert-warn { background: #FFFBEB; border: 1px solid #FDE68A; border-left: 4px solid #F59E0B; border-radius: 6px; padding: 12px 16px; font-size: 13px; color: #92400E; margin-bottom:12px; }
.alert-ok   { background: #F0FDF4; border: 1px solid #BBF7D0; border-left: 4px solid #16A34A; border-radius: 6px; padding: 12px 16px; font-size: 13px; color: #14532D; margin-bottom:12px; }
.alert-info { background: #EFF6FF; border: 1px solid #BFDBFE; border-left: 4px solid #3B82F6; border-radius: 6px; padding: 12px 16px; font-size: 13px; color: #1E3A8A; margin-bottom:12px; }
.status-pill { display: inline-block; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 700; }
.status-ok  { background:#D1FAE5; color:#065F46; border:1px solid #A7F3D0; }
.status-err { background:#FEE2E2; color:#991B1B; border:1px solid #FCA5A5; }

@media (max-width: 991px) {
    .block-container { padding: 1rem 1.25rem 2rem !important; }
    .jfl-header-title { font-size: 18px !important; }
    div[data-testid="stMetricValue"] div { font-size: 22px !important; }
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  GITHUB FILE FETCHER
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def list_github_files():
    try:
        r = requests.get(API_BASE, timeout=10)
        r.raise_for_status()
        return [(f["name"], f["download_url"]) for f in r.json() if isinstance(f, dict) and "name" in f and "download_url" in f]
    except Exception as e:
        st.sidebar.error(f"GitHub connection issue: {e}")
        return []

@st.cache_data(ttl=300)
def fetch_file_bytes(url: str) -> bytes:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.content

def read_excel_from_github(url: str, **kwargs):
    return pd.read_excel(io.BytesIO(fetch_file_bytes(url)), **kwargs)

def read_csv_from_github(url: str, **kwargs):
    return pd.read_csv(io.BytesIO(fetch_file_bytes(url)), **kwargs)

# ─────────────────────────────────────────────────────────────
#  DATE PARSER ASSISTANT
# ─────────────────────────────────────────────────────────────
def fast_parse_dates(series):
    cleansed = series.astype(str).str.strip().str.split(' ').str[0]
    parsed_df = pd.to_datetime(cleansed, errors='coerce', format='%Y-%m-%d')
    if parsed_df.isna().all():
        parsed_df = pd.to_datetime(cleansed, errors='coerce', dayfirst=True)
    return parsed_df

# ─────────────────────────────────────────────────────────────
#  PROCESSED ENERGY FILE LOADER - ENHANCED & ROBUST
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_processed_energy_data():
    all_files = list_github_files()
    target_files = [
        (name, url) for name, url in all_files
        if "PROCESSED_DAILY_VARS_Active_Energy_Report" in name and (name.endswith(".xlsx") or name.endswith(".csv"))
    ]
    if not target_files:
        return None
        
    # Get the latest file
    name, url = sorted(target_files)[-1]
    
    try:
        if name.endswith(".csv"):
            df = read_csv_from_github(url)
        else:
            # Read Excel without assuming header row initially to inspect structure
            raw_df = read_excel_from_github(url, header=None)
            
            # Identify the header row dynamically
            header_row_idx = 0
            for i, row in raw_df.iterrows():
                if any('date' in str(x).lower() for x in row if pd.notna(x)):
                    header_row_idx = i
                    break
            
            # Read again with correct header
            df = read_excel_from_github(url, header=header_row_idx)
            
        # Clean column names
        df.columns = [str(c).strip() for c in df.columns]
        
        # Identify Date Column
        date_col = next((c for c in df.columns if 'date' in c.lower()), None)
        if not date_col:
            # Fallback: assume first column is date if it looks like dates
            if pd.api.types.is_datetime64_any_dtype(df.iloc[:,0]) or '2026' in str(df.iloc[0,0]):
                date_col = df.columns[0]
                df.rename(columns={date_col: 'Date'}, inplace=True)
                date_col = 'Date'
            else:
                return None

        # Parse Dates
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])
        df = df.sort_values(by=date_col).reset_index(drop=True)
        
        if df.empty:
            return None

        # Identify Register Columns (V1 - V9) and Consumption Columns
        # Based on the sample data, V1-V9 are cumulative registers
        register_cols = []
        consump_cols_map = {} # Map register to its consumption column if it exists
        
        for i in range(1, 10):
            v_col = f"V{i}"
            # Check for exact match or close match in columns
            matched_v = next((c for c in df.columns if c.upper() == v_col.upper() or c.startswith(f"V{i} ")), None)
            if matched_v:
                register_cols.append(matched_v)
                
        # Calculate Consumption from Registers if consumption columns are empty/missing
        # We will create standardized consumption columns: 'calc_consump_v1' ... 'calc_consump_v9'
        
        calculated_consumption = {}
        
        for reg_col in register_cols:
            # Extract the index number from column name e.g. "V1 - DUNKIN BLAST" -> 1
            # Or just use the order if naming is inconsistent. 
            # Let's rely on the column name containing V1, V2 etc.
            v_num = None
            for i in range(1, 10):
                if f"V{i}" in reg_col.upper():
                    v_num = i
                    break
            
            if v_num:
                # Calculate Diff
                diffs = df[reg_col].diff()
                # Handle negative diffs (meter reset) or NaNs
                diffs = diffs.where(diffs >= 0, other=np.nan) # Simple check, might need more complex logic for resets
                calculated_consumption[f'calc_consump_v{v_num}'] = diffs.fillna(0)
                
        # Add calculated columns to DF
        for col_name, series in calculated_consumption.items():
            df[col_name] = series
            
        # Define Zone Mappings based on standard JFL naming conventions found in sample
        # V1: Dunkin Blast, V6: Dunkin Rack -> Dunkin
        # V3: CLC Blast, V8: CLC Rack -> CLC
        # V2: BMC Blast, V7: BMC Rack -> BMC
        # V4: Deep1, V5: Deep2, V9: Deep Rack -> Deep
        
        def get_zone_consumption(v_nums):
            total = pd.Series(np.zeros(len(df)), index=df.index)
            for v in v_nums:
                col = f'calc_consump_v{v}'
                if col in df.columns:
                    total += df[col]
            return total
            
        df['Dunkin Consumption'] = get_zone_consumption([1, 6])
        df['CLC Consumption'] = get_zone_consumption([3, 8])
        df['BMC Consumption'] = get_zone_consumption([2, 7])
        df['Deep Consumption'] = get_zone_consumption([4, 5, 9])
        
        # Also keep individual V channels for detailed view
        df['V1_Consumption'] = df.get('calc_consump_v1', pd.Series(0, index=df.index))
        df['V2_Consumption'] = df.get('calc_consump_v2', pd.Series(0, index=df.index))
        df['V3_Consumption'] = df.get('calc_consump_v3', pd.Series(0, index=df.index))
        df['V4_Consumption'] = df.get('calc_consump_v4', pd.Series(0, index=df.index))
        df['V5_Consumption'] = df.get('calc_consump_v5', pd.Series(0, index=df.index))
        df['V6_Consumption'] = df.get('calc_consump_v6', pd.Series(0, index=df.index))
        df['V7_Consumption'] = df.get('calc_consump_v7', pd.Series(0, index=df.index))
        df['V8_Consumption'] = df.get('calc_consump_v8', pd.Series(0, index=df.index))
        df['V9_Consumption'] = df.get('calc_consump_v9', pd.Series(0, index=df.index))

        return df
        
    except Exception as e:
        st.sidebar.error(f"Failed parsing processed energy file {name}: {e}")
        import traceback
        st.sidebar.text(traceback.format_exc())
        return None

# ─────────────────────────────────────────────────────────────
#  TEMPERATURE DATA LOADER 
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_temperature_data():
    all_files = list_github_files()
    csv_files = [(n, u) for n, u in all_files if n.startswith("DataLog_") and n.endswith(".csv")]
    if not csv_files:
        return None

    frames = []
    for name, url in sorted(csv_files):
        try:
            df = read_csv_from_github(url)
            df.columns = [str(c).strip() for c in df.columns]
            
            time_col = next((c for c in df.columns if 'time' in c.lower()), None)
            c1_col = next((c for c in df.columns if 'cooler1' in c.lower().replace(" ", "")), None)
            c2_col = next((c for c in df.columns if 'cooler2' in c.lower().replace(" ", "")), None)
            p_col = next((c for c in df.columns if 'perishable' in c.lower()), None)
            
            if not all([time_col, c1_col, c2_col, p_col]):
                continue
                
            sub = df[[time_col, c1_col, c2_col, p_col]].copy()
            sub = sub.rename(columns={
                time_col: 'Time',
                c1_col: 'Dough Cooler1 Temp',
                c2_col: 'Dough Cooler2 Temp',
                p_col: 'Perishable Cooler Temp'
            })
            
            for c in ['Dough Cooler1 Temp', 'Dough Cooler2 Temp', 'Perishable Cooler Temp']:
                sub[c] = sub[c].astype(str).str.strip()
                sub[c] = pd.to_numeric(sub[c], errors='coerce')
                sub[c] = sub[c].ffill().bfill()
                
            sub['Time'] = pd.to_datetime(sub['Time'], dayfirst=True, errors='coerce')
            frames.append(sub)
        except Exception as e:
            st.warning(f"Skipped template anomalies on {name}: {e}")

    if not frames:
        return None

    combined = (
        pd.concat(frames, ignore_index=True)
        .dropna(subset=['Time'])
        .drop_duplicates(subset=['Time'])
        .sort_values('Time')
        .reset_index(drop=True)
    )

    combined['consump. dough1'] = (combined['Dough Cooler1 Temp'] - combined['Dough Cooler1 Temp'].shift(1)).fillna(0)
    combined['consump. dough2'] = (combined['Dough Cooler2 Temp'] - combined['Dough Cooler2 Temp'].shift(1)).fillna(0)
    combined['consump. perishable'] = (combined['Perishable Cooler Temp'] - combined['Perishable Cooler Temp'].shift(1)).fillna(0)

    return combined

# ─────────────────────────────────────────────────────────────
#  EXCEL SHEET LOADER
# ─────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────
#  EXCEL SHEET LOADER - FIXED & ROBUST
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_excel_sheet(sheet_name, fallback_header_row):
    """
    Loads a specific sheet from the Freon Excel workbook found in GitHub.
    Includes dynamic header detection and defensive error handling.
    """
    try:
        # 1. Fetch the files list
        all_files = list_github_files()
        if not all_files:
            return None
        
        # 2. Find the freon file correctly by unpacking both name (n) and url (u)
        match_url = None
        for n, u in all_files:
            if "freon" in n.lower() and n.endswith(".xlsx"):
                match_url = u
                break
        
        if not match_url:
            return None

        # 3. Read a preview to detect the actual header row dynamically
        try:
            preview = read_excel_from_github(match_url, sheet_name=sheet_name, header=None, engine='openpyxl')
        except Exception as e:
            st.warning(f"Could not preview sheet '{sheet_name}' from Freon file: {e}")
            return None

        # Determine header row index
        hdr = fallback_header_row
        if not preview.empty:
            for i in range(min(15, len(preview))):
                # Convert row to string list, handling NaNs
                row_vals = [str(x).lower() for x in preview.iloc[i] if pd.notna(x)]
                if any('date' in x or 'stop time' in x or 'start time' in x or 'sr' in x for x in row_vals):
                    hdr = i
                    break
        
        # 4. Read the actual data with the detected header
        try:
            df = read_excel_from_github(match_url, sheet_name=sheet_name, header=hdr, engine='openpyxl')
        except Exception as e:
            st.warning(f"Failed to read data from sheet '{sheet_name}': {e}")
            return None

        if df.empty:
            return None
            
        # 5. Clean Column Names
        df.columns = [str(c).strip() for c in df.columns]
        df = df.dropna(axis=1, how='all')
        
        # 6. Specific Logic for Sheet3 (Compressor Optimization)
        if sheet_name == 'Sheet3':
            if len(df.columns) >= 12:
                # Ensure the 12th column is named correctly if it exists
                if 'Saving in hrs' not in df.columns:
                     df.columns.values[11] = 'Saving in hrs'
            else:
                # Fallback: check last column for unnamed
                last = df.columns[-1]
                if 'unnamed' in str(last).lower():
                    df = df.rename(columns={last: 'Saving in hrs'})
                
        # 7. Filter out 'Total' rows if they exist in the first column
        if not df.empty:
            fc = df.columns[0]
            # Keep rows where the first column is NOT 'total' (case-insensitive)
            mask = df[fc].astype(str).str.strip().str.lower() != 'total'
            df = df[mask]
            
        return df

    except Exception as e:
        st.warning(f"Unexpected error loading sheet {sheet_name}: {e}")
        import traceback
        st.sidebar.text(traceback.format_exc())
        return None
# ─────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style="padding:16px 0 20px;">
            <div style="font-size:9px; font-weight:700; letter-spacing:1.8px; color:#94A3B8; text-transform:uppercase; margin-bottom:6px;">
                JUBILANT FOODWORKS LIMITED
            </div>
            <div style="font-size:17px; font-weight:800; color:#FFFFFF; line-height:1.25;">
                Plant Operations<br>Dashboard
            </div>
            <div style="margin-top:10px; width:36px; height:3px; background:#E01934; border-radius:2px;"></div>
        </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 Refresh Data Now"):
        st.cache_data.clear()
        st.rerun()

    all_files = list_github_files()
    processed_energy_files = [n for n, _ in all_files if "PROCESSED_DAILY_VARS_Active_Energy_Report" in n]
    csv_files    = [n for n, _ in all_files if n.startswith("DataLog_") and n.endswith(".csv")]
    has_freon    = any("freon" in n.lower() for n, _ in all_files)

    st.markdown("<hr style='border-color:#1E3A8A; margin:14px 0;'>", unsafe_allow_html=True)
    st.markdown("""<div style="font-size:9px; font-weight:700; letter-spacing:1.2px;
                    color:#94A3B8; text-transform:uppercase; margin-bottom:10px;">
                    GitHub Source Status</div>""", unsafe_allow_html=True)

    st.markdown(f"""
        <div style="margin-bottom:8px;">
            <span class="status-pill status-{'ok' if processed_energy_files else 'err'}">
                {'●' if processed_energy_files else '○'}&nbsp; Processed Energy · {'Active' if processed_energy_files else 'Missing'}
            </span>
        </div>
        <div style="margin-bottom:8px;">
            <span class="status-pill status-{'ok' if csv_files else 'err'}">
                {'●' if csv_files else '○'}&nbsp; Temp Logs · {len(csv_files)} file(s)
            </span>
        </div>
        <div>
            <span class="status-pill status-{'ok' if has_freon else 'err'}">
                {'●' if has_freon else '○'}&nbsp; Freon Workbook · {'Found' if has_freon else 'Not Found'}
            </span>
        </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  HEADER SYSTEM
# ─────────────────────────────────────────────────────────────
e_df = load_processed_energy_data()
temp_df = load_temperature_data()

if e_df is not None and not e_df.empty:
    start_date = e_df['Date'].min().strftime('%d %b %Y')
    end_date = e_df['Date'].max().strftime('%d %b %Y')
    date_range_str = f"{start_date} – {end_date}"
else:
    date_range_str = "No Data Loaded"

st.markdown(f"""
<div class="jfl-header-container">
    <div style="display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 16px;">
        <div style="flex: 1; min-width: 280px;">
            <div class="jfl-header-subtitle">Supply Chain & Manufacturing · Noida Plant Group</div>
            <div class="jfl-header-title">Plant Operational Intelligence Hub</div>
        </div>
        <div style="display: flex; gap: 12px; flex-wrap: wrap; min-width: 240px;">
            <div class="jfl-header-meta-box" style="flex: 1;">
                <div class="jfl-meta-label">Reporting Window</div>
                <div class="jfl-meta-value">{date_range_str}</div>
            </div>
            <div class="jfl-header-meta-box" style="flex: 1;">
                <div class="jfl-meta-label">Corporate Entity</div>
                <div class="jfl-meta-value" style="color: #E01934;">Jubilant FoodWorks</div>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  TABS ROUTING
# ─────────────────────────────────────────────────────────────
tab_energy, tab_temp, tab_power, tab_runtime, tab_comp = st.tabs([
    "⚡  Active Energy Meters",
    "🌡️  Cold Storage Temperatures",
    "💡  Energy & Cost Savings",
    "⚙️  Asset Duty Cycles",
    "📉  Compressor Optimisation",
])

# ==============================================================================
#  TAB 1 — ACTIVE ENERGY METERS
# ==============================================================================
with tab_energy:
    if e_df is not None and not e_df.empty:
        st.markdown('<div class="sec-title">📊 Data Quality & Structure Summary</div>', unsafe_allow_html=True)
        
        date_col = 'Date'
        total_records = len(e_df)
        start_date = e_df[date_col].min()
        end_date = e_df[date_col].max()
        total_days = (end_date - start_date).days + 1
        
        col_q1, col_q2, col_q3, col_q4 = st.columns(4)
        with col_q1:
            st.metric("Total Records", f"{total_records} days")
        with col_q2:
            st.metric("Date Range Start", start_date.strftime('%d %b %Y'))
        with col_q3:
            st.metric("Date Range End", end_date.strftime('%d %b %Y'))
        with col_q4:
            st.metric("Coverage", f"{total_days} days")
        
        # Define Zone Columns
        dunkin_col = 'Dunkin Consumption'
        clc_col = 'CLC Consumption'
        bmc_col = 'BMC Consumption'
        deep_col = 'Deep Consumption'
        
        eq_cols = [dunkin_col, clc_col, bmc_col, deep_col]
        
        missing_dates = pd.date_range(start=start_date, end=end_date).difference(e_df[date_col])
        if len(missing_dates) > 0:
            st.markdown(f'<div class="alert-warn">⚠️ <strong>Data Quality Alert:</strong> {len(missing_dates)} missing date(s) detected in the range.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="alert-ok">✓ <strong>Data Integrity:</strong> Complete date coverage with no gaps detected.</div>', unsafe_allow_html=True)
        
        st.markdown("")
        
        st.markdown('<div class="sec-title">📈 Total Energy Consumption Summary (kWh)</div>', unsafe_allow_html=True)
        
        def get_sum(col_name):
            if col_name in e_df.columns:
                return e_df[col_name].sum()
            return 0.0
        
        def get_avg(col_name):
            if col_name in e_df.columns:
                return e_df[col_name].mean()
            return 0.0
        
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: 
            st.metric("Dunkin' Total", f"{get_sum(dunkin_col):,.1f} kWh", 
                     delta=f"Avg: {get_avg(dunkin_col):,.1f} kWh/day")
        with c2: 
            st.metric("CLC Total", f"{get_sum(clc_col):,.1f} kWh",
                     delta=f"Avg: {get_avg(clc_col):,.1f} kWh/day")
        with c3: 
            st.metric("BMC Total", f"{get_sum(bmc_col):,.1f} kWh",
                     delta=f"Avg: {get_avg(bmc_col):,.1f} kWh/day")
        with c4: 
            st.metric("Deep Freezer Total", f"{get_sum(deep_col):,.1f} kWh",
                     delta=f"Avg: {get_avg(deep_col):,.1f} kWh/day")
        with c5:
            total_all = get_sum(dunkin_col) + get_sum(clc_col) + get_sum(bmc_col) + get_sum(deep_col)
            st.metric("Grand Total", f"{total_all:,.1f} kWh",
                     delta=f"{total_days} days")
        
        # Individual V Channels Plot
        v_channels = [f'V{i}_Consumption' for i in range(1, 10)]
        existing_v_channels = [c for c in v_channels if c in e_df.columns]
        
        if existing_v_channels:
            st.markdown('<div class="sec-title">📊 Daily Consumption Profile — V1 to V9 Channels</div>', unsafe_allow_html=True)
            st.markdown(f"*Analyzing {len(existing_v_channels)} meter channels across {total_days} days*")
            
            fig = go.Figure()
            x_dates = e_df[date_col].dt.strftime('%d-%b').tolist()
            
            colors = ['#002D62', '#E01934', '#FF9F1C', '#16A34A', '#0EA5E9', '#8B5CF6', '#EC4899', '#F59E0B', '#10B981']
            meter_names = {
                'V1_Consumption': 'V1 - Dunkin Blast',
                'V2_Consumption': 'V2 - BMC Blast',
                'V3_Consumption': 'V3 - CLC Blast',
                'V4_Consumption': 'V4 - Deep1 Blast',
                'V5_Consumption': 'V5 - Deep2 Blast',
                'V6_Consumption': 'V6 - Dunkin Rack',
                'V7_Consumption': 'V7 - BMC Rack',
                'V8_Consumption': 'V8 - CLC Rack',
                'V9_Consumption': 'V9 - Deep Rack'
            }
            
            for i, col in enumerate(existing_v_channels):
                display_name = meter_names.get(col, col)
                fig.add_trace(go.Scatter(
                    x=x_dates,
                    y=e_df[col].tolist(),
                    mode='lines+markers',
                    name=display_name,
                    line=dict(width=2.5, color=colors[i % len(colors)]),
                    marker=dict(size=6),
                    hovertemplate=f'{display_name}<br>Date: %{{x}}<br>Consumption: %{{y:,.2f}} kWh<extra></extra>'
                ))
                
            fig.update_layout(
                hovermode="x unified",
                margin=dict(l=60, r=20, t=40, b=60),
                height=450,
                xaxis=dict(
                    title='Date',
                    type='category',
                    tickmode='array',
                    tickvals=x_dates,
                    tickangle=45,
                    fixedrange=True
                ),
                yaxis=dict(
                    title='Daily Consumption (kWh)',
                    fixedrange=True,
                    gridcolor='#E2E8F0'
                ),
                legend=dict(
                    orientation="h", 
                    yanchor="bottom", 
                    y=1.02, 
                    xanchor="right", 
                    x=1,
                    bgcolor='rgba(255,255,255,0.8)'
                ),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=True
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Zone Distribution Plot
        st.markdown('<div class="sec-title">🏭 Process Zone Daily Energy Distribution</div>', unsafe_allow_html=True)
        
        fig_zone = go.Figure()
        zone_colors = {
            dunkin_col: '#002D62',
            clc_col: '#FF9F1C',
            bmc_col: '#16A34A',
            deep_col: '#E01934'
        }
        
        for col in eq_cols:
            color = zone_colors.get(col, '#64748B')
            display_name = col.replace(' Consumption', '').title()
            
            fig_zone.add_trace(go.Bar(
                x=x_dates,
                y=e_df[col].tolist(),
                name=display_name,
                marker_color=color,
                hovertemplate=f'{display_name}<br>Date: %{{x}}<br>Energy: %{{y:,.2f}} kWh<extra></extra>'
            ))
        
        fig_zone.update_layout(
            barmode='stack',
            hovermode="x unified",
            margin=dict(l=60, r=20, t=40, b=60),
            height=450,
            xaxis=dict(
                title='Date',
                type='category',
                tickmode='array',
                tickvals=x_dates,
                tickangle=45,
                fixedrange=True
            ),
            yaxis=dict(
                title='Total Energy (kWh)',
                fixedrange=True,
                gridcolor='#E2E8F0'
            ),
            legend=dict(
                orientation="h", 
                yanchor="bottom", 
                y=1.02, 
                xanchor="right", 
                x=1,
                bgcolor='rgba(255,255,255,0.8)'
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_zone, use_container_width=True)
        
        st.markdown('<div class="sec-title">📉 Day-over-Day Consumption Change (Δ vs Previous Day)</div>', unsafe_allow_html=True)
        
        # Filter out rows with zero or invalid consumption data
        valid_data_mask = (e_df[eq_cols].sum(axis=1) > 0)
        e_df_valid = e_df[valid_data_mask].copy()
        
        diff_energy = pd.DataFrame()
        diff_energy['ChartDate'] = e_df_valid[date_col].dt.strftime('%d-%b').tolist()
        diff_energy['DateObj'] = e_df_valid[date_col]
        diff_cols = []
        
        for col in eq_cols:
            col_label = f"{col} Δ"
            diff_series = e_df_valid[col].diff().fillna(0)
            # Ensure no negative values
            diff_series = diff_series.clip(lower=0)
            diff_energy[col_label] = diff_series.values
            diff_cols.append(col_label)
        st.markdown('<div class="sec-title">📉 Day-over-Day Consumption Change (Δ vs Previous Day)</div>', unsafe_allow_html=True)
        
        # Filter out rows with zero consumption (like June 15)
        valid_data_mask = (e_df[eq_cols].sum(axis=1) > 0)
        e_df_valid = e_df[valid_data_mask].copy()
        
        diff_energy = pd.DataFrame()
        diff_energy['ChartDate'] = e_df_valid[date_col].dt.strftime('%d-%b').tolist()
        diff_energy['DateObj'] = e_df_valid[date_col]
        diff_cols = []
        
        for col in eq_cols:
            col_label = f"{col} Δ"
            diff_series = e_df_valid[col].diff().fillna(0)
            diff_series = diff_series.clip(lower=0)
            diff_energy[col_label] = diff_series.values
            diff_cols.append(col_label)
        
        if not diff_energy.empty:
            target_energy_row = diff_energy.iloc[-1]
            last_valid_date = e_df_valid[date_col].iloc[-1].strftime('%d-%b')
            
            ec1, ec2, ec3, ec4 = st.columns(4)
            
            def render_delta_metric(container, col_name, color, label):
                if col_name in e_df_valid.columns:
                    actual_kwh = e_df_valid[col_name].iloc[-1]
                    delta_key = f"{col_name} Δ"
                    if delta_key in diff_energy.columns:
                        delta_val = target_energy_row[delta_key]
                        delta_text = f"Δ {delta_val:+,.1f} kWh vs prev"
                    else:
                        delta_text = "No prior data"
                        
                    container.markdown(f"""
                    <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:16px; border-left:4px solid {color};">
                        <div style="font-size:10px; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.5px;">{label} ({last_valid_date})</div>
                        <div style="font-size:26px; font-weight:800; color:{color}; margin-top:4px;">{actual_kwh:,.1f} kWh</div>
                        <div style="font-size:11px; font-weight:600; color:#64748B; margin-top:6px;">{delta_text}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    container.metric(label, "N/A")
            
            with ec1: render_delta_metric(ec1, dunkin_col, "#002D62", "Dunkin' Daily")
            with ec2: render_delta_metric(ec2, clc_col, "#FF9F1C", "CLC Daily")
            with ec3: render_delta_metric(ec3, bmc_col, "#16A34A", "BMC Daily")
            with ec4: render_delta_metric(ec4, deep_col, "#E01934", "Deep Daily")
            
            st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
            
            fig_delta = go.Figure()
            delta_colors = ['#002D62', '#FF9F1C', '#16A34A', '#E01934']
            
            for i, col in enumerate(diff_cols):
                fig_delta.add_trace(go.Bar(
                    x=diff_energy['ChartDate'].tolist(),
                    y=diff_energy[col].tolist(),
                    name=col.replace(' Δ', ''),
                    marker_color=delta_colors[i % len(delta_colors)],
                    opacity=0.8,
                    hovertemplate=f'{col}<br>Date: %{{x}}<br>Δ: %{{y:+,.2f}} kWh<extra></extra>'
                ))
            
            fig_delta.update_layout(
                barmode='group',
                hovermode="x unified",
                margin=dict(l=60, r=20, t=40, b=60),
                height=400,
                xaxis=dict(
                    title='Date',
                    type='category',
                    tickmode='array',
                    tickvals=diff_energy['ChartDate'].tolist(),
                    tickangle=45,
                    fixedrange=True
                ),
                yaxis=dict(
                    title='Daily Change (kWh)',
                    fixedrange=True,
                    gridcolor='#E2E8F0'
                ),
                legend=dict(
                    orientation="h", 
                    yanchor="bottom", 
                    y=1.02, 
                    xanchor="right", 
                    x=1
                ),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                shapes=[dict(type='line', xref='paper', yref='y', x0=0, y0=0, x1=1, y1=0, line=dict(color='red', width=2, dash='dash'))]
            )
        st.plotly_chart(fig_delta, use_container_width=True)
        
        st.markdown('<div class="sec-title">📋 Statistical Summary by Zone</div>', unsafe_allow_html=True)
        summary_data = []
        zone_labels = {
            dunkin_col: "Dunkin'",
            clc_col: "CLC",
            bmc_col: "BMC",
            deep_col: "Deep Freezer"
        }
        
        for col in eq_cols:
            series = e_df[col]
            summary_data.append({
                "Zone": zone_labels.get(col, col),
                "Total (kWh)": f"{series.sum():,.2f}",
                "Mean (kWh/day)": f"{series.mean():,.2f}",
                "Min (kWh)": f"{series.min():,.2f}",
                "Max (kWh)": f"{series.max():,.2f}",
                "Std Dev": f"{series.std():,.2f}",
                "CV (%)": f"{(series.std()/series.mean()*100) if series.mean() != 0 else 0:.1f}"
            })
        
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
        
        st.markdown('<div class="sec-title">🚨 Anomaly Detection & Alerts</div>', unsafe_allow_html=True)
        
        for col in eq_cols:
            series = e_df[col]
            mean_val = series.mean()
            std_val = series.std()
            if std_val == 0: continue
            
            threshold_upper = mean_val + 2 * std_val
            threshold_lower = mean_val - 2 * std_val
            
            anomalies = e_df[(series > threshold_upper) | (series < threshold_lower)]
            
            if len(anomalies) > 0:
                st.markdown(f'<div class="alert-warn"><strong>{zone_labels.get(col, col)}:</strong> {len(anomalies)} anomaly day(s) detected (outside ±2σ)</div>', unsafe_allow_html=True)
                for idx, row in anomalies.iterrows():
                    date_str = row[date_col].strftime('%d %b %Y')
                    val = row[col]
                    st.markdown(f"  - {date_str}: {val:,.2f} kWh (Mean: {mean_val:,.2f}, Threshold: {threshold_upper:,.2f})")
            else:
                st.markdown(f'<div class="alert-ok"><strong>{zone_labels.get(col, col)}:</strong> No anomalies detected - stable consumption pattern</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sec-title">📥 Raw Data Inspector & Export Portal</div>', unsafe_allow_html=True)
        with st.expander("📂 View Pre-Processed Active Energy File Data Table", expanded=False):
            st.dataframe(e_df.set_index(date_col), use_container_width=True)
            
            csv_data = e_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Active Energy Data as CSV",
                data=csv_data,
                file_name=f"active_energy_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key="btn_download_energy"
            )
    else:
        st.markdown('<div class="alert-info"><strong>⚠️ No active energy data captured matching the current file window constraints.</strong></div>', unsafe_allow_html=True)
        st.markdown("""
        **Troubleshooting Steps:**
        1. Verify that PROCESSED_DAILY_VARS_Active_Energy_Report files exist in the GitHub repository
        2. Check that the date range in the files matches the expected window
        3. Ensure the file format is either .xlsx or .csv
        4. Click '🔄 Refresh Data Now' in the sidebar to reload data
        """)

# ==============================================================================
#  TAB 2 — COLD STORAGE TEMPERATURES
# ==============================================================================
with tab_temp:
    if temp_df is not None and not temp_df.empty:
        latest  = temp_df.iloc[-1]
        sensors = ['Dough Cooler1 Temp', 'Dough Cooler2 Temp', 'Perishable Cooler Temp']
        delta_cols = ['consump. dough1', 'consump. dough2', 'consump. perishable']
        THRESHOLD = 4.0

        c1, c2, c3, c4 = st.columns([1,1,1,1.2])
        with c1: st.metric("Dough Cooler 1",   f"{latest['Dough Cooler1 Temp']:.2f} °C")
        with c2: st.metric("Dough Cooler 2",   f"{latest['Dough Cooler2 Temp']:.2f} °C")
        with c3: st.metric("Perishable Store", f"{latest['Perishable Cooler Temp']:.2f} °C")
        with c4:
            total_logs = len(temp_df)
            total_exc  = sum((temp_df[s] > THRESHOLD).sum() for s in sensors)
            compliance = (1 - total_exc / (total_logs * len(sensors))) * 100
            st.metric("Thermal Compliance Index", f"{compliance:.1f}%",
                      delta=f"{total_exc} critical violations", delta_color="inverse")

        st.markdown('<div class="sec-title">Real-Time Temperature Stream</div>', unsafe_allow_html=True)
        st.line_chart(temp_df.set_index('Time')[sensors], color=["#002D62","#0EA5E9","#E01934"])

        st.markdown('<div class="sec-title">Daily Mean Thermal Signature</div>', unsafe_allow_html=True)
        temp_df['Date'] = temp_df['Time'].dt.date
        daily_avg = temp_df.groupby('Date')[sensors].mean().round(2)
        daily_avg.index = daily_avg.index.astype(str)
        st.bar_chart(daily_avg, color=["#002D62","#0EA5E9","#E01934"])

        st.markdown('<div class="sec-title">Temperature Log Delta Variations</div>', unsafe_allow_html=True)
        
        d1_sum = temp_df['consump. dough1'].sum()
        d2_sum = temp_df['consump. dough2'].sum()
        p_sum  = temp_df['consump. perishable'].sum()
        
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            st.markdown(f"""
            <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:6px; padding:10px 16px; border-left:4px solid #002D62;">
                <div style="font-size:9px; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px;">Dough 1 Delta Variance Sum</div>
                <div style="font-size:16px; font-weight:800; color:#002D62; margin-top:2px;">{d1_sum:,.2f} °C</div>
            </div>
            """, unsafe_allow_html=True)
        with sc2:
            st.markdown(f"""
            <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:6px; padding:10px 16px; border-left:4px solid #0EA5E9;">
                <div style="font-size:9px; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px;">Dough 2 Delta Variance Sum</div>
                <div style="font-size:16px; font-weight:800; color:#002D62; margin-top:2px;">{d2_sum:,.2f} °C</div>
            </div>
            """, unsafe_allow_html=True)
        with sc3:
            st.markdown(f"""
            <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:6px; padding:10px 16px; border-left:4px solid #E01934;">
                <div style="font-size:9px; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px;">Perishable Delta Variance Sum</div>
                <div style="font-size:16px; font-weight:800; color:#002D62; margin-top:2px;">{p_sum:,.2f} °C</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
        st.line_chart(temp_df.set_index('Time')[delta_cols])

        st.markdown('<div class="sec-title">Cold-Chain Thermodynamic Stability Audits</div>', unsafe_allow_html=True)
        labels = {'Dough Cooler1 Temp':'Dough Cooler 1','Dough Cooler2 Temp':'Dough Cooler 2','Perishable Cooler Temp':'Perishable Storage'}
        rows = []
        for col in sensors:
            s   = temp_df[col]
            n   = len(s)
            exc = int((s > THRESHOLD).sum())
            rows.append({"Asset Node": labels[col], "Total Logs": n, "Mean Temp": s.mean(),
                         "Min Temp": s.min(), "Max Temp": s.max(), "Stability (σ)": s.std(),
                         "Excursions": exc, "Compliance Index": (n - exc) / n})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True,
            column_config={
                "Mean Temp": st.column_config.NumberColumn(format="%.2f °C"),
                "Min Temp":  st.column_config.NumberColumn(format="%.2f °C"),
                "Max Temp":  st.column_config.NumberColumn(format="%.2f °C"),
                "Stability (σ)": st.column_config.NumberColumn(format="%.2f σ"),
                "Compliance Index": st.column_config.ProgressColumn(format="%.1f%%", min_value=0.0, max_value=1.0)
            })

        st.markdown('<div class="sec-title">Zone Status Alert Routing</div>', unsafe_allow_html=True)
        for col in sensors:
            exc  = int((temp_df[col] > THRESHOLD).sum())
            comp = ((len(temp_df) - exc) / len(temp_df)) * 100
            lbl  = labels[col]
            if comp >= 95:
                st.markdown(f'<div class="alert-ok">✓ <strong>{lbl}</strong> — Stable at {comp:.1f}% operational compliance.</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="alert-warn">⚠ <strong>{lbl}</strong> — Out-of-bounds drop at {comp:.1f}% compliance level.</div>', unsafe_allow_html=True)

        st.markdown('<div class="sec-title">📥 Raw Data Inspector & Export Portal</div>', unsafe_allow_html=True)
        with st.expander("📂 View & Download Compiled Temperature Log File Data with Delta Metrics", expanded=False):
            st.dataframe(temp_df, use_container_width=True, hide_index=True)
            csv_data = temp_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Compiled Temperature Data as CSV",
                data=csv_data,
                file_name="compiled_temperature_logs.csv",
                mime="text/csv",
                key="btn_download_temp"
            )
    else:
        st.markdown('<div class="alert-info">No environment logs could be successfully loaded.</div>', unsafe_allow_html=True)

# ==============================================================================
#  TAB 3 — ENERGY & COST SAVINGS
# ==============================================================================
with tab_power:
    st.markdown('<div class="sec-title">💡 Energy & Cost Savings Dashboard</div>', unsafe_allow_html=True)

    # Load Sheet1 (header is on the second row, index 1)
    power_df = load_excel_sheet('Sheet1', fallback_header_row=1)

    if power_df is not None and not power_df.empty:
        p = power_df.copy()

        # ── Column constants (matched to actual Sheet1 headers) ─────────────
        COL_DATE       = 'Date'
        COL_DUNKIN     = 'Dunkin Blast'   # cumulative kWh meter
        COL_CLC        = 'CLC Blast'      # cumulative kWh meter
        COL_DEEP       = 'Deep-total'     # cumulative kWh meter
        COL_SAV_DUNKIN = 'Savings'        # daily savings – Dunkin  (₹)
        COL_SAV_CLC    = 'Savings.1'      # daily savings – CLC     (₹)
        COL_SAV_BMC    = 'Savings.2'      # daily savings – BMC     (₹)
        COL_SAV_DEEP   = 'Savings.3'      # daily savings – Deep    (₹)

        REQUIRED = [COL_DATE, COL_DUNKIN, COL_CLC, COL_SAV_DUNKIN, COL_SAV_CLC]
        missing  = [c for c in REQUIRED if c not in p.columns]
        if missing:
            st.error(f"❌ Required columns missing from Sheet1: {missing}")
            st.stop()

        # ── Date parsing ────────────────────────────────────────────────────
        p[COL_DATE] = fast_parse_dates(p[COL_DATE])
        p = p.dropna(subset=[COL_DATE]).copy()

        if p.empty:
            st.warning("No valid date rows found in Sheet1.")
            st.stop()

        # Drop meter-reset rows (negative cumulative readings are artifacts)
        p = p[p[COL_DUNKIN].isna() | (p[COL_DUNKIN] > 0)].copy()

        # ── Duplicate date handling ─────────────────────────────────────────
        n_dupes = len(p) - p[COL_DATE].nunique()
        if n_dupes > 0:
            numeric_cols = p.select_dtypes(include=[np.number]).columns.tolist()
            p = p.groupby(COL_DATE, as_index=False)[numeric_cols].sum(numeric_only=True)
            st.info(f"ℹ️ {n_dupes} duplicate date(s) consolidated by summing.")

        p = p.sort_values(COL_DATE).reset_index(drop=True)

        # ── Reindex to continuous daily range ───────────────────────────────
        date_range = pd.date_range(start=p[COL_DATE].min(), end=p[COL_DATE].max(), freq='D')
        p = p.set_index(COL_DATE).reindex(date_range).rename_axis('Date').reset_index()

        # ── Convert to numeric ──────────────────────────────────────────────
        all_data_cols = [COL_DUNKIN, COL_CLC, COL_DEEP,
                         COL_SAV_DUNKIN, COL_SAV_CLC, COL_SAV_BMC, COL_SAV_DEEP]
        for col in all_data_cols:
            if col in p.columns:
                p[col] = pd.to_numeric(p[col], errors='coerce')

        # ── Daily consumption from cumulative meter diffs ───────────────────
        def daily_diff(series):
            return series.diff().fillna(0).clip(lower=0)

        p['Dunkin Daily']    = daily_diff(p[COL_DUNKIN])
        p['CLC Daily']       = daily_diff(p[COL_CLC])
        p['Deep Daily']      = daily_diff(p[COL_DEEP]) if COL_DEEP in p.columns else 0.0
        p['Combined Load']   = p['Dunkin Daily'] + p['CLC Daily'] + p['Deep Daily']

        # ── Total savings: sum all four section columns row-wise ────────────
        sav_cols_present = [c for c in [COL_SAV_DUNKIN, COL_SAV_CLC, COL_SAV_BMC, COL_SAV_DEEP]
                            if c in p.columns]
        p['Total Savings']   = p[sav_cols_present].fillna(0).sum(axis=1)

        # Clip outlier spikes (meter-reset rows inflate savings unrealistically)
        savings_cap          = p['Total Savings'].quantile(0.98)
        p['Total Savings']   = p['Total Savings'].clip(upper=savings_cap)

        # ── KPI Cards ───────────────────────────────────────────────────────
        st.markdown('<div class="sec-title">⚡ Key Performance Indicators</div>', unsafe_allow_html=True)

        total_load    = p['Combined Load'].sum()
        total_savings = p['Total Savings'].sum()
        savings_per_unit = total_savings / total_load if total_load > 0 else 0

        k1, k2, k3, k4, k5, k6 = st.columns(6)
        with k1: st.metric("Dunkin Blast (kWh)",    f"{p['Dunkin Daily'].sum():,.0f}")
        with k2: st.metric("CLC Blast (kWh)",       f"{p['CLC Daily'].sum():,.0f}")
        with k3: st.metric("Deep Storage (kWh)",    f"{p['Deep Daily'].sum():,.0f}")
        with k4: st.metric("Combined Load (kWh)",   f"{total_load:,.0f}")
        with k5: st.metric("Total Savings (₹)",     f"₹{total_savings:,.2f}")
        with k6: st.metric("Savings / kWh (₹)",     f"₹{savings_per_unit:,.4f}")

        st.markdown("---")

        # ── Chart 1 — Cumulative Meter Readings ─────────────────────────────
        st.markdown('<div class="sec-title">📈 Cumulative Meter Readings (kWh)</div>', unsafe_allow_html=True)
        meter_chart = p.set_index('Date')[[COL_DUNKIN, COL_CLC]].dropna(how='all')
        if not meter_chart.empty:
            st.area_chart(meter_chart, color=["#002D62", "#FF9F1C"])

        # ── Chart 2 — Daily Consumption Breakdown ───────────────────────────
        st.markdown('<div class="sec-title">⚡ Daily Consumption Breakdown (kWh)</div>', unsafe_allow_html=True)
        st.bar_chart(
            p.set_index('Date')[['Dunkin Daily', 'CLC Daily', 'Deep Daily']].fillna(0),
            color=["#002D62", "#FF9F1C", "#10B981"]
        )

        # ── Chart 3 — Daily Savings ─────────────────────────────────────────
        st.markdown('<div class="sec-title">💰 Daily Recovery Realized (₹)</div>', unsafe_allow_html=True)
        st.bar_chart(p.set_index('Date')['Total Savings'].fillna(0), color="#16A34A")

        # ── Daily Summary Table ─────────────────────────────────────────────
        st.markdown('<div class="sec-title">📋 Daily Energy & Savings Data</div>', unsafe_allow_html=True)
        table_df = p[['Date', 'Dunkin Daily', 'CLC Daily', 'Deep Daily', 'Combined Load', 'Total Savings']].copy()
        table_df.columns = ['Date', 'Dunkin Blast (kWh)', 'CLC Blast (kWh)', 'Deep Storage (kWh)', 'Combined Load (kWh)', 'Total Savings (₹)']
        table_df['Date'] = table_df['Date'].dt.strftime('%d-%b-%Y')
        st.dataframe(table_df, use_container_width=True, hide_index=True)

        # ── Savings Breakdown Table ─────────────────────────────────────────
        st.markdown('<div class="sec-title">🔍 Savings Breakdown by Section</div>', unsafe_allow_html=True)
        breakdown_df = p[['Date'] + sav_cols_present].fillna(0).copy()
        rename_map   = {COL_SAV_DUNKIN: 'Dunkin (₹)', COL_SAV_CLC: 'CLC (₹)',
                        COL_SAV_BMC: 'BMC (₹)', COL_SAV_DEEP: 'Deep (₹)'}
        breakdown_df = breakdown_df.rename(columns=rename_map)
        breakdown_df['Date'] = breakdown_df['Date'].dt.strftime('%d-%b-%Y')
        st.dataframe(breakdown_df, use_container_width=True, hide_index=True)

        # ── Raw Data Inspector & Export ─────────────────────────────────────
        st.markdown('<div class="sec-title">📥 Raw Data Inspector & Export Portal</div>', unsafe_allow_html=True)
        with st.expander("📂 View & Download Energy & Cost Savings Raw Sheet Data", expanded=False):
            st.dataframe(p, use_container_width=True, hide_index=True)
            csv_data = p.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Sheet1 Cost Data as CSV",
                data=csv_data,
                file_name="freon_sheet1_energy_savings.csv",
                mime="text/csv",
                key="btn_download_power"
            )
    else:
        st.markdown('<div class="alert-info">Power consumption analytical worksheet missing from repo root.</div>', unsafe_allow_html=True)
        # ==============================================================================
#  TAB 4 — ASSET DUTY CYCLES
# ==============================================================================
with tab_runtime:
    runtime_df = load_excel_sheet('Sheet2', fallback_header_row=2)
    if runtime_df is not None and not runtime_df.empty:
        r  = runtime_df.copy()
        fc = r.columns[0]
        r  = r[~r[fc].astype(str).str.contains('Date|From|Total|Running', case=False, na=False)]
        r[fc] = fast_parse_dates(r[fc])
        r  = r.dropna(subset=[fc]).sort_values(fc)
        
        kwh_cols = [c for c in r.columns if 'KWH' in str(c).upper()]
        for col in kwh_cols:
            r[col] = pd.to_numeric(r[col], errors='coerce').fillna(0)

        if kwh_cols and not r.empty:
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("Consolidated Ingested Draw", f"{r[kwh_cols[0]].sum():,.0f} kWh")
            with c2: st.metric("Peak System Load Vector",    f"{r[kwh_cols[0]].max():,.0f} kWh")
            with c3: st.metric("Mean Constant Load Metric", f"{r[kwh_cols[0]].mean():,.0f} kWh")

            st.markdown('<div class="sec-title">Daily Asset Displacement Matrix (Normal Data Logs)</div>', unsafe_allow_html=True)
            st.bar_chart(r.set_index(fc)[kwh_cols[0]], color="#002D62")

            r['Date_Key'] = r[fc].dt.date
            daily_runtime = r.groupby('Date_Key')[kwh_cols[0]].agg(['sum', 'max', 'mean']).reset_index()
            daily_runtime = daily_runtime.rename(columns={
                'Date_Key': 'Date',
                'sum': 'Energy Drew (kWh)',
                'max': 'Peak System Load Vector (kWh)',
                'mean': 'Mean Load Vector (kWh)'
            })
            daily_runtime['Date'] = pd.to_datetime(daily_runtime['Date'])

            st.markdown('<div class="sec-title">Date-Wise Energy Ingestion Profiles (Differenced Daily Breakdown)</div>', unsafe_allow_html=True)
            target_day = daily_runtime.iloc[-1] if not daily_runtime.empty else None
            
            rc1, rc2, rc3 = st.columns(3)
            with rc1:
                val = target_day['Energy Drew (kWh)'] if target_day is not None else 0
                st.markdown(f"""
                <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:6px; padding:10px 16px; border-left:4px solid #002D62;">
                    <div style="font-size:9px; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px;">Energy Drew</div>
                    <div style="font-size:16px; font-weight:800; color:#002D62; margin-top:2px;">{val:,.1f} kWh</div>
                </div>
                """, unsafe_allow_html=True)
            with rc2:
                val = target_day['Peak System Load Vector (kWh)'] if target_day is not None else 0
                st.markdown(f"""
                <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:6px; padding:10px 16px; border-left:4px solid #FF9F1C;">
                    <div style="font-size:9px; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px;">Peak System Load Vector</div>
                    <div style="font-size:16px; font-weight:800; color:#002D62; margin-top:2px;">{val:,.1f} kWh</div>
                </div>
                """, unsafe_allow_html=True)
            with rc3:
                val = target_day['Mean Load Vector (kWh)'] if target_day is not None else 0
                st.markdown(f"""
                <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:6px; padding:10px 16px; border-left:4px solid #E01934;">
                    <div style="font-size:9px; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px;">Mean Load Vector</div>
                    <div style="font-size:16px; font-weight:800; color:#002D62; margin-top:2px;">{val:,.1f} kWh</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
            st.line_chart(daily_runtime.set_index('Date')[['Energy Drew (kWh)', 'Peak System Load Vector (kWh)', 'Mean Load Vector (kWh)']])

            st.markdown('<div class="sec-title">Date-Wise Asset Duty Performance Log Metrics</div>', unsafe_allow_html=True)
            st.dataframe(daily_runtime, use_container_width=True, hide_index=True)

            st.markdown('<div class="sec-title">📥 Raw Data Inspector & Export Portal</div>', unsafe_allow_html=True)
            with st.expander("📂 View & Download Asset Duty Cycle Raw Sheet Data", expanded=False):
                st.dataframe(r.drop(columns=['Date_Key']), use_container_width=True, hide_index=True)
                csv_data = daily_runtime.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Date-Wise Duty Cycles as CSV",
                    data=csv_data,
                    file_name="datewise_asset_duty_cycles.csv",
                    mime="text/csv",
                    key="btn_download_runtime"
                )
    else:
        st.markdown('<div class="alert-info">Asset duty-cycle log metrics are not active.</div>', unsafe_allow_html=True)

# ==============================================================================
#  TAB 5 — COMPRESSOR OPTIMISATION (REFACTORED — OFF-HOURS / DOWNTIME FOCUS)
# ==============================================================================
with tab_comp:
    try:
        # ------------------------------------------------------------------
        # 1. LOAD & SANITIZE RAW SHEET
        # ------------------------------------------------------------------
        comp_df = load_excel_sheet('Sheet3', fallback_header_row=3)

        if comp_df is None or comp_df.empty:
            st.markdown(
                '<div class="alert-info">Compressor analytical tracking components not parsed.</div>',
                unsafe_allow_html=True
            )
        else:
            c = comp_df.copy()
            c.columns = [str(col).strip() for col in c.columns]   # strip hidden chars
            
            # Drop metadata/header rows that leaked into the data body
            c = c[~c.iloc[:, 0].astype(str).str.strip().str.lower().str.fullmatch(
                r'date|total|from|sr\.?\s*no\.?|stop|start', na=False
            )]
            
            # Parse dates defensively
            c.iloc[:, 0] = fast_parse_dates(c.iloc[:, 0])
            c = c.dropna(subset=[c.columns[0]]).sort_values(c.columns[0]).reset_index(drop=True)
            date_col = c.columns[0]

            # ------------------------------------------------------------------
            # 2. SAVINGS COLUMN DETECTION  (existing logic preserved)
            # ------------------------------------------------------------------
            possible_saving_cols = [col for col in c.columns if "saving" in str(col).lower()]
            if not possible_saving_cols:
                st.warning("Savings column not found in Sheet3. Continuing without savings metrics.")
                sav_col = None
            else:
                sav_col = possible_saving_cols[0]
                st.info(f"Detected Savings Column: `{sav_col}`")

            if sav_col and sav_col in c.columns:
                c[sav_col] = pd.to_numeric(c[sav_col], errors='coerce').fillna(0)
                c['Cumulative Savings'] = c[sav_col].cumsum()
            else:
                c['Cumulative Savings'] = 0
                sav_col = None

            # ------------------------------------------------------------------
            # 3. KPI METRICS  (existing)
            # ------------------------------------------------------------------
            k1, k2, k3, k4 = st.columns(4)
            if sav_col and sav_col in c.columns:
                with k1: st.metric("Relief Window Saved", f"{c[sav_col].sum():,.1f} hrs")
                with k2: st.metric("Mean Daily Dampening", f"{c[sav_col].mean():.1f} hrs")
                with k3: st.metric("Peak Single Window Stop", f"{c[sav_col].max():.1f} hrs")
            else:
                with k1: st.metric("Relief Window Saved", "N/A")
                with k2: st.metric("Mean Daily Dampening", "N/A")
                with k3: st.metric("Peak Single Window Stop", "N/A")
            with k4: st.metric("Audited Shift Blocks", f"{len(c)}")

            # ------------------------------------------------------------------
            # 4. DAILY REST & CUMULATIVE CURVE  (existing)
            # ------------------------------------------------------------------
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="sec-title">Daily Rest Allocations (hrs)</div>', unsafe_allow_html=True)
                if sav_col and sav_col in c.columns:
                    st.line_chart(c.set_index(date_col)[sav_col], color="#002D62")
                else:
                    st.info("No savings data available to plot.")
            with col2:
                st.markdown('<div class="sec-title">Cumulative Rest Curve Metrics</div>', unsafe_allow_html=True)
                if sav_col and sav_col in c.columns:
                    st.area_chart(c.set_index(date_col)['Cumulative Savings'], color="#FF9F1C")
                else:
                    st.info("No cumulative savings data available to plot.")

            # ------------------------------------------------------------------
            # 5. THERMODYNAMIC DRIFT  (existing, guarded)
            # ------------------------------------------------------------------
            try:
                if temp_df is not None and not temp_df.empty:
                    st.markdown(
                        '<div class="sec-title">Thermodynamic Drift vs. System Optimization Rest Cycles</div>',
                        unsafe_allow_html=True
                    )
                    if sav_col and sav_col in c.columns:
                        daily_rest_agg = c.groupby(c[date_col].dt.date)[sav_col].sum().reset_index()
                        daily_rest_agg.columns = ['Date', 'Rest_Hours']
                        daily_rest_agg['Date'] = pd.to_datetime(daily_rest_agg['Date'])
                        
                        t_clean = temp_df.copy()
                        t_clean['Date_Key'] = pd.to_datetime(t_clean['Time']).dt.date
                        
                        dough1_col = next((col for col in t_clean.columns if 'cooler1' in col.lower().replace(" ", "")), None)
                        
                        if dough1_col:
                            daily_thermal_mean = t_clean.groupby('Date_Key')[dough1_col].mean().reset_index()
                            daily_thermal_mean.columns = ['Date', 'Mean_Temp']
                            daily_thermal_mean['Date'] = pd.to_datetime(daily_thermal_mean['Date'])
                            
                            diagnostic_matrix = pd.merge(daily_rest_agg, daily_thermal_mean, on='Date', how='inner')
                            
                            if not diagnostic_matrix.empty:
                                fig_diag = make_subplots(specs=[[{"secondary_y": True}]])
                                x_labels = diagnostic_matrix['Date'].dt.strftime('%d-%b').tolist()
                                
                                fig_diag.add_trace(
                                    go.Bar(x=x_labels, y=diagnostic_matrix['Rest_Hours'].tolist(), name="Rest Window (Hrs)", marker_color='#002D62', opacity=0.75),
                                    secondary_y=False
                                )
                                fig_diag.add_trace(
                                    go.Scatter(x=x_labels, y=diagnostic_matrix['Mean_Temp'].tolist(), mode='lines+markers', name="Dough 1 Mean Temp (°C)", line=dict(color='#E01934', width=2.5)),
                                    secondary_y=True
                                )
                                fig_diag.update_layout(hovermode="x unified", margin=dict(l=20, r=20, t=10, b=10), height=350, legend=dict(orientation="h", y=1.15))
                                fig_diag.update_yaxes(title_text="Rest Profile (Hrs)", secondary_y=False)
                                fig_diag.update_yaxes(title_text="Thermal State (°C)", secondary_y=True)
                                st.plotly_chart(fig_diag, use_container_width=True)
                    else:
                        st.info("No savings data available for thermodynamic drift analysis.")
            except NameError:
                pass   # temp_df not defined in this runtime
            except Exception as e:
                st.warning(f"Thermodynamic drift analysis skipped: {e}")

            # ==================================================================
            # 6. NEW — COMPRESSOR DETECTION & OFF-HOURS / DOWNTIME ANALYTICS
            # ==================================================================
            st.markdown('<div class="sec-title">🔧 Compressor Downtime / OFF-Hours Analysis</div>', unsafe_allow_html=True)

            try:
                compressors = detect_compressors(c.columns)

                # --------------------------------------------------------------
                # 6a. Diagnostics panel
                # --------------------------------------------------------------
                with st.expander("🔍 Diagnostics: Detected Compressor Columns & Processing Method", expanded=False):
                    if not compressors:
                        st.warning("No compressor columns detected.")
                    else:
                        diag_rows = []
                        for comp_id, cols in sorted(compressors.items()):
                            diag_rows.append({
                                'Compressor ID': comp_id,
                                'Stop Column': cols.get('stop', '—'),
                                'Start Column': cols.get('start', '—'),
                                'Run Column': cols.get('run', '—'),
                                'OFF/Downtime Column': cols.get('off', '—'),
                                'Processing Method': (
                                    'Direct OFF Column' if 'off' in cols else
                                    'Stop→Start Duration' if ('stop' in cols and 'start' in cols) else
                                    'Run Column' if 'run' in cols else
                                    'Unknown'
                                )
                            })
                        st.dataframe(pd.DataFrame(diag_rows), use_container_width=True, hide_index=True)

                if not compressors:
                    st.warning("No compressor columns detected. Expected patterns like `Compressor-1 Stop time`.")
                else:
                    st.success(f"Detected **{len(compressors)}** compressor(s): {', '.join(sorted(compressors.keys()))}")

                    # ----------------------------------------------------------
                    # 6b. Build per-row OFF-hours dataframe
                    # ----------------------------------------------------------
                    off_df = pd.DataFrame({date_col: c[date_col].values})

                    for comp_id, cols in compressors.items():
                        comp_name = f"Compressor {comp_id}"

                        # Priority 1: Direct OFF/Downtime column
                        if 'off' in cols:
                            off_df[comp_name] = pd.to_numeric(c[cols['off']], errors='coerce')

                        # Priority 2: Stop → Start calculation
                        elif 'stop' in cols and 'start' in cols:
                            stop_col, start_col = cols['stop'], cols['start']
                            
                            # Optimized: Parse columns independently instead of row-by-row apply
                            stop_times = c[stop_col].apply(parse_time_string)
                            start_times = c[start_col].apply(parse_time_string)
                            
                            off_hours_list = [
                                calculate_off_hours(st_t, st_s) 
                                for st_t, st_s in zip(stop_times, start_times)
                            ]
                            off_df[comp_name] = off_hours_list

                        # Priority 3: Direct Run column (cannot reliably compute OFF hours)
                        elif 'run' in cols:
                            off_df[comp_name] = np.nan

                    # Drop rows where every compressor is NaN
                    comp_cols = [col for col in off_df.columns if col != date_col]
                    if comp_cols:
                        off_df = off_df.dropna(subset=comp_cols, how='all').reset_index(drop=True)

                    if off_df.empty or not comp_cols:
                        st.warning("No valid compressor OFF-hours data could be calculated.")
                    else:
                        # ------------------------------------------------------
                        # 6c. Daily OFF-Hours table (Date | Compressor | OFF Hours)
                        # ------------------------------------------------------
                        melted_off = off_df.melt(id_vars=[date_col], var_name='Compressor', value_name='OFF Hours').dropna(subset=['OFF Hours'])
                        melted_off_events = melted_off[melted_off['OFF Hours'] > 0].copy()

                        st.markdown('<div class="sec-title">📋 Daily Downtime Log (Date | Compressor | OFF Hours)</div>', unsafe_allow_html=True)
                        st.dataframe(
                            melted_off_events.sort_values([date_col, 'Compressor']).reset_index(drop=True),
                            use_container_width=True, hide_index=True
                        )

                        # ------------------------------------------------------
                        # 6d. Summary statistics table
                        # ------------------------------------------------------
                        summary_rows = []
                        for cc in comp_cols:
                            valid = off_df[cc].dropna()
                            if valid.empty: continue
                            events = (valid > 0).sum()
                            summary_rows.append({
                                'Compressor': cc,
                                'Total OFF Hours': round(valid.sum(), 2),
                                'Average OFF Hours': round(valid.mean(), 2),
                                'Maximum OFF Hours': round(valid.max(), 2),
                                'Minimum OFF Hours': round(valid.min(), 2),
                                'Downtime Events': int(events)
                            })

                        if not summary_rows:
                            st.warning("All compressor records were invalid or empty.")
                        else:
                            summary_df = pd.DataFrame(summary_rows)
                            
                            st.markdown('<div class="sec-title">📊 Compressor Downtime Summary</div>', unsafe_allow_html=True)
                            st.dataframe(
                                summary_df.style.format({
                                    'Total OFF Hours': '{:,.2f}',
                                    'Average OFF Hours': '{:,.2f}',
                                    'Maximum OFF Hours': '{:,.2f}',
                                    'Minimum OFF Hours': '{:,.2f}'
                                }),
                                use_container_width=True, hide_index=True
                            )

                            # --------------------------------------------------
                            # 6e. CHART 1 — Bar: Total OFF Hours per Compressor
                            # --------------------------------------------------
                            st.markdown('<div class="sec-title">Total OFF Hours by Compressor</div>', unsafe_allow_html=True)
                            fig_bar = px.bar(summary_df, x='Compressor', y='Total OFF Hours', color='Compressor', text='Total OFF Hours')
                            fig_bar.update_layout(showlegend=False, height=400, margin=dict(l=20, r=20, t=40, b=20))
                            fig_bar.update_traces(texttemplate='%{text:.1f}', textposition='outside')
                            st.plotly_chart(fig_bar, use_container_width=True)

                            # --------------------------------------------------
                            # 6f. CHART 2 — Line: Daily OFF Hours Trend
                            # --------------------------------------------------
                            st.markdown('<div class="sec-title">Daily OFF Hours Trend</div>', unsafe_allow_html=True)
                            fig_line = px.line(melted_off, x=date_col, y='OFF Hours', color='Compressor', markers=True)
                            fig_line.update_layout(height=400, hovermode='x unified', margin=dict(l=20, r=20, t=40, b=20))
                            st.plotly_chart(fig_line, use_container_width=True)

                            # --------------------------------------------------
                            # 6g. CHART 3 — Stacked Area: Daily Contribution
                            # --------------------------------------------------
                            st.markdown('<div class="sec-title">Daily Compressor Downtime Contribution (Stacked Area)</div>', unsafe_allow_html=True)
                            fig_area = px.area(melted_off, x=date_col, y='OFF Hours', color='Compressor')
                            fig_area.update_layout(height=400, hovermode='x unified', margin=dict(l=20, r=20, t=40, b=20))
                            st.plotly_chart(fig_area, use_container_width=True)

                            # --------------------------------------------------
                            # 6h. CHART 4 — Pie: Downtime Share
                            # --------------------------------------------------
                            st.markdown('<div class="sec-title">Downtime Share Distribution</div>', unsafe_allow_html=True)
                            fig_pie = px.pie(summary_df, values='Total OFF Hours', names='Compressor', hole=0.3)
                            fig_pie.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20))
                            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                            st.plotly_chart(fig_pie, use_container_width=True)

                            # --------------------------------------------------
                            # 6i. CHART 5 — Heatmap: Compressor × Date
                            # --------------------------------------------------
                            st.markdown('<div class="sec-title">Downtime Heatmap (Compressor × Date)</div>', unsafe_allow_html=True)
                            try:
                                pivot_df = melted_off.pivot_table(index='Compressor', columns=date_col, values='OFF Hours', aggfunc='sum').fillna(0)
                                date_labels = [d.strftime('%d-%b') for d in pivot_df.columns]
                                
                                fig_heat = go.Figure(data=go.Heatmap(
                                    z=pivot_df.values, x=date_labels, y=pivot_df.index.tolist(),
                                    colorscale='YlOrRd', colorbar=dict(title='OFF Hours'),
                                    hovertemplate='Compressor: %{y}<br>Date: %{x}<br>OFF Hours: %{z:.2f}<extra></extra>'
                                ))
                                fig_heat.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20), xaxis=dict(title='Date', tickangle=45), yaxis=dict(title='Compressor'))
                                st.plotly_chart(fig_heat, use_container_width=True)
                            except Exception as e:
                                st.warning(f"Heatmap generation skipped: {e}")

            except Exception as e:
                st.error(f"Compressor OFF-hours analysis failed: {e}")
                st.info("Verify that compressor columns follow patterns like `Compressor-1 Stop time`.")

            # ==================================================================
            # 7. IMPROVED SAVINGS LOGIC
            # ==================================================================
            st.markdown('<div class="sec-title">💰 Estimated Energy Savings from Compressor Downtime</div>', unsafe_allow_html=True)

            try:
                if sav_col and sav_col in c.columns and 'off_df' in locals() and not off_df.empty and comp_cols:
                    # Calculate total calculated OFF hours across all compressors per day
                    daily_calc_off = off_df.set_index(date_col)[comp_cols].sum(axis=1).reset_index()
                    daily_calc_off.columns = [date_col, 'Calculated OFF Hours']

                    # Merge with actual savings
                    savings_daily = c[[date_col, sav_col]].copy()
                    savings_merged = pd.merge(daily_calc_off, savings_daily, on=date_col, how='inner')

                    if not savings_merged.empty:
                        total_calc_off = savings_merged['Calculated OFF Hours'].sum()
                        total_savings_hrs = savings_merged[sav_col].sum()

                        savings_pct = (total_savings_hrs / total_calc_off * 100) if total_calc_off > 0 else 0

                        sk1, sk2, sk3 = st.columns(3)
                        with sk1: st.metric("Total Calculated OFF Hours", f"{total_calc_off:,.1f} hrs")
                        with sk2: st.metric("Total Savings Hours (Actual)", f"{total_savings_hrs:,.1f} hrs")
                        with sk3: st.metric("Savings Efficiency %", f"{savings_pct:.1f}%")

                        # Savings table
                        savings_table_rows = []
                        for cc in comp_cols:
                            comp_total = off_df[cc].sum()
                            contrib_pct = (comp_total / total_calc_off * 100) if total_calc_off > 0 else 0
                            est_savings = comp_total * (total_savings_hrs / total_calc_off) if total_calc_off > 0 else 0
                            
                            savings_table_rows.append({
                                'Compressor': cc,
                                'Total OFF Hours': round(comp_total, 2),
                                'Contribution %': round(contrib_pct, 2),
                                'Estimated Savings Hours': round(est_savings, 2)
                            })

                        savings_table_df = pd.DataFrame(savings_table_rows)
                        
                        st.markdown('<div class="sec-title">📊 Compressor Savings Contribution</div>', unsafe_allow_html=True)
                        st.dataframe(
                            savings_table_df.style.format({
                                'Total OFF Hours': '{:,.2f}',
                                'Contribution %': '{:,.2f}%',
                                'Estimated Savings Hours': '{:,.2f}'
                            }),
                            use_container_width=True, hide_index=True
                        )
                    else:
                        st.info("No overlapping data between OFF-hours and savings columns.")
                else:
                    st.info("Savings column or OFF-hours data not available for savings estimation.")
            except Exception as e:
                st.warning(f"Savings estimation skipped: {e}")

            # ------------------------------------------------------------------
            # 8. RAW DATA INSPECTOR & CSV EXPORT  (existing)
            # ------------------------------------------------------------------
            st.markdown('<div class="sec-title">📥 Raw Data Inspector & Export Portal</div>', unsafe_allow_html=True)
            with st.expander("📂 View & Download Compressor Optimization Raw Sheet Data", expanded=False):
                st.dataframe(c, use_container_width=True, hide_index=True)
                csv_data = c.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Sheet3 Optimisation Data as CSV",
                    data=csv_data,
                    file_name="freon_sheet3_compressor_optimization.csv",
                    mime="text/csv",
                    key="btn_download_comp"
                )

    except Exception as e:
        # Outer safety net — tab never crashes the whole dashboard
        st.error(f"Compressor Optimisation tab encountered an error: {e}")
        st.info("The rest of the dashboard remains fully functional.")
