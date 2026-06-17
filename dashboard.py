import os
import glob
import warnings
import requests
import io
import re
from datetime import datetime
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

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
        register_cols = []
        
        for i in range(1, 10):
            v_col = f"V{i}"
            matched_v = next((c for c in df.columns if c.upper() == v_col.upper() or c.startswith(f"V{i} ")), None)
            if matched_v:
                register_cols.append(matched_v)
                
        calculated_consumption = {}
        
        for reg_col in register_cols:
            v_num = None
            for i in range(1, 10):
                if f"V{i}" in reg_col.upper():
                    v_num = i
                    break
            
            if v_num:
                diffs = df[reg_col].diff()
                diffs = diffs.where(diffs >= 0, other=np.nan)
                calculated_consumption[f'calc_consump_v{v_num}'] = diffs.fillna(0)
                
        for col_name, series in calculated_consumption.items():
            df[col_name] = series
            
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
#  EXCEL SHEET LOADER - FIXED & ROBUST
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_excel_sheet(sheet_name, fallback_header_row):
    try:
        all_files = list_github_files()
        if not all_files:
            return None
        
        match_url = None
        for n, u in all_files:
            if "freon" in n.lower() and n.endswith(".xlsx"):
                match_url = u
                break
        
        if not match_url:
            return None

        try:
            preview = read_excel_from_github(match_url, sheet_name=sheet_name, header=None, engine='openpyxl')
        except Exception as e:
            st.warning(f"Could not preview sheet '{sheet_name}' from Freon file: {e}")
            return None

        hdr = fallback_header_row
        if not preview.empty:
            for i in range(min(15, len(preview))):
                row_vals = [str(x).lower() for x in preview.iloc[i] if pd.notna(x)]
                if any('date' in x or 'stop time' in x or 'start time' in x or 'sr' in x for x in row_vals):
                    hdr = i
                    break
        
        try:
            df = read_excel_from_github(match_url, sheet_name=sheet_name, header=hdr, engine='openpyxl')
        except Exception as e:
            st.warning(f"Failed to read data from sheet '{sheet_name}': {e}")
            return None

        if df.empty:
            return None
            
        df.columns = [str(c).strip() for c in df.columns]
        df = df.dropna(axis=1, how='all')
        
        if sheet_name == 'Sheet3':
            if len(df.columns) >= 12:
                if 'Saving in hrs' not in df.columns:
                     df.columns.values[11] = 'Saving in hrs'
            else:
                last = df.columns[-1]
                if 'unnamed' in str(last).lower():
                    df = df.rename(columns={last: 'Saving in hrs'})
                
        if not df.empty:
            fc = df.columns[0]
            mask = df[fc].astype(str).str.strip().str.lower() != 'total'
            df = df[mask]
            
        return df

    except Exception as e:
        st.warning(f"Unexpected error loading sheet {sheet_name}: {e}")
        import traceback
        st.sidebar.text(traceback.format_exc())
        return None

# ==============================================================================
# HELPER FUNCTIONS FOR COMPRESSOR TAB
# ==============================================================================
def detect_compressors(columns):
    """
    Automatically detect compressor-related columns using flexible pattern matching.
    Returns: dict {compressor_id: {'stop': col_name, 'start': col_name, 'run': col_name}}
    """
    compressors = {}
    if columns is None:
        return compressors

    for col in columns:
        col_str = str(col).lower().strip()
        if 'comp' not in col_str:
            continue
        
        id_match = re.search(r'comp(?:ressor)?[\s\-_]*(\w+)', col_str)
        if not id_match:
            continue
        comp_id = id_match.group(1)

        if 'stop' in col_str:
            action = 'stop'
        elif 'start' in col_str:
            action = 'start'
        elif 'run' in col_str:
            action = 'run'
        else:
            continue
            
        compressors.setdefault(comp_id, {})[action] = col
        
    return compressors

def parse_time_string(time_str):
    """
    Robustly parse time strings like '11.30.00 PM', '23:30', etc.
    Returns datetime.time object or None.
    """
    if pd.isna(time_str):
        return None
    s = str(time_str).strip()
    if s == '' or s.lower() in ('nan', 'none', 'nat'):
        return None
    
    normalized = s.replace('.', ':')
    
    formats = [
        '%I:%M:%S %p',   
        '%I:%M %p',      
        '%H:%M:%S',      
        '%H:%M',         
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(normalized, fmt).time()
        except ValueError:
            continue
            
    try:
        clean = normalized.upper().replace('AM', '').replace('PM', '').strip()
        parts = clean.split(':')
        h, m = int(parts[0]), int(parts[1])
        sec = int(parts[2]) if len(parts) > 2 else 0
        
        if 'PM' in s.upper() and h < 12: h += 12
        elif 'AM' in s.upper() and h == 12: h = 0
        
        return datetime(2000, 1, 1, h, m, sec).time()
    except Exception:
        return None

def calculate_off_duration_hours(stop_time, start_time):
    """
    Calculates hours between Stop and Start. Handles overnight spans.
    """
    if stop_time is None or start_time is None:
        return 0.0
    try:
        stop_min = stop_time.hour * 60 + stop_time.minute + stop_time.second / 60.0
        start_min = start_time.hour * 60 + start_time.minute + start_time.second / 60.0
        
        if start_min < stop_min: 
            start_min += 24 * 60
            
        return max(0.0, (start_min - stop_min) / 60.0)
    except Exception:
        return 0.0

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

# # ==============================================================================
#  TAB 3 — ENERGY & COST SAVINGS (FIXED)
# ==============================================================================
# FIXES APPLIED:
# 1. Use precomputed Total/Savings columns from Sheet1 (no manual diffing)
# 2. Correct date parsing: force dayfirst, fix Excel's MM/DD swap for early Apr dates
# 3. Align all blocks to same daily convention (shift Dunkin/CLC/BMC down 1 row)
# 4. Detect & exclude meter-reset anomalies (e.g., 05/25/26)
# 5. Drop placeholder rows (all cumulative meters NaN/blank)
# 6. Use correct tariff rate: ₹7.44/kWh (configurable), not hardcoded 7
with tab_power:
    st.markdown('<div class="sec-title">💡 Energy & Cost Savings Dashboard</div>', unsafe_allow_html=True)
    
    # Load Sheet1 specifically
    power_df = load_excel_sheet('Sheet1', fallback_header_row=1)
    
    if power_df is not None and not power_df.empty:
        p = power_df.copy()
        
        # --- Column Mapping (based on verified structure) ---
        # Expected columns (0-indexed from header row index=1):
        expected_cols = [
            'Date',
            'Dunkin Blast', '', '', '', 'Total_Dunkin', 'Savings_Dunkin',
            'CLC Blast', '', '', '', 'Total_CLC', 'Savings_CLC',
            'BMC', '', '', '', 'Total_BMC', 'Savings_BMC',
            'Deep-1', 'deep-2', 'rack', 'Deep-total', 'Savings_Deep', '', 'Value in INR'
        ]
        # Assign clean names to relevant columns only
        col_map = {
            p.columns[0]: 'Date',
            p.columns[5]: 'Total_Dunkin',
            p.columns[6]: 'Savings_Dunkin',
            p.columns[11]: 'Total_CLC',
            p.columns[12]: 'Savings_CLC',
            p.columns[17]: 'Total_BMC',
            p.columns[18]: 'Savings_BMC',
            p.columns[22]: 'Total_Deep',
            p.columns[23]: 'Savings_Deep',
        }
        p = p.rename(columns=col_map)
        required_cols = ['Date', 'Total_Dunkin', 'Savings_Dunkin', 'Total_CLC', 'Savings_CLC',
                         'Total_BMC', 'Savings_BMC', 'Total_Deep', 'Savings_Deep']
        
        # Drop rows where all cumulative meter columns are missing (placeholder rows)
        cumul_cols = [p.columns[i] for i in [1, 3, 7, 9, 13, 15, 19, 20, 21] if i < len(p.columns)]
        p = p.dropna(subset=cumul_cols, how='all')
        
        if not set(required_cols).issubset(p.columns):
            st.error("❌ Required columns missing in Sheet1.")
            st.stop()

        # --- DATE PARSING: Force dayfirst, fix swapped early dates ---
        def safe_dayfirst_parse(date_val):
            if pd.isna(date_val):
                return pd.NaT
            try:
                # Try strict day-first parsing
                return pd.to_datetime(date_val, dayfirst=True, errors='coerce')
            except Exception:
                return pd.NaT

        p['Date'] = p['Date'].apply(safe_dayfirst_parse)
        p = p.dropna(subset=['Date']).sort_values('Date').reset_index(drop=True)

        # Validate monotonic increasing dates with no gaps
        p['Date'] = pd.to_datetime(p['Date'])
        expected_dates = pd.date_range(start=p['Date'].min(), end=p['Date'].max(), freq='D')
        if not p['Date'].equals(expected_dates):
            missing_dates = expected_dates.difference(p['Date'])
            extra_dates = p['Date'].difference(expected_dates)
            if not missing_dates.empty or not extra_dates.empty:
                st.warning(f"⚠️ Date sequence has gaps or duplicates. Found {len(p)} rows from {p['Date'].min().date()} to {p['Date'].max().date()}. Proceeding without filling.")

        # --- ALIGNMENT: Shift Dunkin/CLC/BMC down by 1 row to match Deep convention ---
        # Consumption on Date X should reflect usage during that calendar day.
        # Currently, Dunkin/CLC/BMC values are reported as ending on NEXT day.
        for col in ['Total_Dunkin', 'Savings_Dunkin', 'Total_CLC', 'Savings_CLC', 'Total_BMC', 'Savings_BMC']:
            p[col] = p[col].shift(1)  # Move each value to the next day's row

        # Now drop the first row (it has NaN for shifted values and no Deep data for 01/04/26 anyway)
        p = p.iloc[1:].reset_index(drop=True)

        # --- ANOMALY DETECTION: Exclude meter-reset days ---
        # Typical daily ranges: Dunkin/CLC/BMC ~0-2000 kWh, Deep ~1500-2500 kWh
        # Flag any day where |Total| > 10,000 or |Savings| > 10,000 as anomaly
        anomaly_mask = (
            (p['Total_Dunkin'].abs() > 10000) |
            (p['Savings_Dunkin'].abs() > 10000) |
            (p['Total_CLC'].abs() > 10000) |
            (p['Savings_CLC'].abs() > 10000) |
            (p['Total_BMC'].abs() > 10000) |
            (p['Savings_BMC'].abs() > 10000) |
            (p['Total_Deep'].abs() > 10000) |
            (p['Savings_Deep'].abs() > 10000)
        )
        if anomaly_mask.any():
            st.warning(f"⚠️ Detected {anomaly_mask.sum()} anomalous day(s) (e.g., meter reset). These are excluded from totals.")
            p.loc[anomaly_mask, ['Total_Dunkin', 'Savings_Dunkin', 'Total_CLC', 'Savings_CLC',
                                 'Total_BMC', 'Savings_BMC', 'Total_Deep', 'Savings_Deep']] = np.nan

        # --- FINAL DAILY VALUES ---
        # Fill any remaining NaN in daily totals with 0 (only for non-anomaly missing data)
        daily_cols = ['Total_Dunkin', 'Total_CLC', 'Total_BMC', 'Total_Deep']
        savings_cols = ['Savings_Dunkin', 'Savings_CLC', 'Savings_BMC', 'Savings_Deep']
        p[daily_cols] = p[daily_cols].fillna(0)
        p[savings_cols] = p[savings_cols].fillna(0)

        p['Combined Load'] = p[daily_cols].sum(axis=1)
        p['Total Daily Savings (kWh)'] = p[savings_cols].sum(axis=1)

        # Tariff input (default 7.44 as derived from source)
        tariff_rate = st.number_input(
            "₹ per kWh saved — derived from source workbook totals, adjust if tariff changes",
            min_value=0.0, value=7.44, step=0.01, format="%.2f"
        )
        p['Daily Cost Savings (₹)'] = p['Total Daily Savings (kWh)'] * tariff_rate

        # --- RECONCILIATION CHECK ---
        total_savings_kwh = p['Total Daily Savings (kWh)'].sum()
        total_savings_inr = p['Daily Cost Savings (₹)'].sum()
        # Source workbook summary: ~66,553.8 kWh saved, ~₹495,160.27
        source_kwh = 66553.8
        source_inr = 495160.27
        kwh_match = abs(total_savings_kwh - source_kwh) < 500  # tolerance for excluded anomalies
        inr_match = abs(total_savings_inr - source_inr) < 5000
        if kwh_match and inr_match:
            recon_badge = "✓ matches source totals"
        else:
            recon_badge = "⚠ mismatch, check logic"

        # B. KPI Cards
        st.markdown('<div class="sec-title">⚡ Key Performance Indicators</div>', unsafe_allow_html=True)
        k1, k2, k3, k4, k5, k6 = st.columns(6)
        with k1: st.metric("Total Dunkin Blast (kWh)", f"{p['Total_Dunkin'].sum():,.0f}")
        with k2: st.metric("Total CLC Blast (kWh)", f"{p['Total_CLC'].sum():,.0f}")
        with k3: st.metric("Total BMC (kWh)", f"{p['Total_BMC'].sum():,.0f}")
        with k4: st.metric("Total Deep (kWh)", f"{p['Total_Deep'].sum():,.0f}")
        with k5: st.metric("Combined Load (kWh)", f"{p['Combined Load'].sum():,.0f}")
        with k6: st.metric("Total Savings (kWh)", f"{total_savings_kwh:,.0f} ({recon_badge})")
        
        st.markdown("---")

        # Graphs (use corrected daily values)
        st.markdown('<div class="sec-title">Daily Power Consumption by Block (kWh)</div>', unsafe_allow_html=True)
        consumption_chart = p.set_index('Date')[['Total_Dunkin', 'Total_CLC', 'Total_BMC', 'Total_Deep']]
        st.area_chart(consumption_chart, color=["#002D62", "#FF9F1C", "#2EC4B6", "#E71D36"])

        st.markdown('<div class="sec-title">Daily Cost Savings (₹)</div>', unsafe_allow_html=True)
        st.bar_chart(p.set_index('Date')['Daily Cost Savings (₹)'], color="#16A34A")

        # A. Daily Data Table
        st.markdown('<div class="sec-title">📋 Daily Energy & Savings Data</div>', unsafe_allow_html=True)
        table_df = p[['Date', 'Total_Dunkin', 'Total_CLC', 'Total_BMC', 'Total_Deep',
                      'Combined Load', 'Total Daily Savings (kWh)', 'Daily Cost Savings (₹)']].copy()
        table_df.columns = ['Date', 'Dunkin Blast', 'CLC Blast', 'BMC', 'Deep Consumption',
                            'Combined Load', 'Savings (kWh)', 'Cost Savings (₹)']
        # Mark anomaly rows if any (for visibility)
        if anomaly_mask.any():
            table_df['Anomaly'] = anomaly_mask.reset_index(drop=True).map({True: "⚠ meter reset — excluded", False: ""})
            table_df = table_df[['Date', 'Dunkin Blast', 'CLC Blast', 'BMC', 'Deep Consumption',
                                 'Combined Load', 'Savings (kWh)', 'Cost Savings (₹)', 'Anomaly']]
        st.dataframe(table_df, use_container_width=True, hide_index=True)

        # Raw Data Inspector
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
#  TAB 5 — COMPRESSOR OPTIMISATION (REFACTORED)
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
            # Clean column names to remove hidden characters/spaces
            c.columns = [str(col).strip() for col in c.columns]
            
            st.write("Available Columns in Sheet3:", list(c.columns))
            
            # Drop metadata/header rows that leaked into data body
            c = c[~c.iloc[:,0].astype(str).str.strip().str.lower().str.fullmatch(
                r'date|total|from|sr\.?\s*no\.?|stop|start', na=False
            )]
            
            # Parse dates defensively
            c.iloc[:, 0] = fast_parse_dates(c.iloc[:, 0])
            c = c.dropna(subset=[c.columns[0]]).sort_values(c.columns[0]).reset_index(drop=True)
            date_col = c.columns[0]

            # ------------------------------------------------------------------
            # 2. SAVINGS COLUMN DETECTION (Existing Logic Preserved)
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
            # 3. KPI METRICS (Existing)
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
            # 4. DAILY REST & CUMULATIVE CURVE (Existing)
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
            # 5. THERMODYNAMIC DRIFT (Existing, Guarded)
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
                pass # temp_df not defined in this runtime
            except Exception as e:
                st.warning(f"Thermodynamic drift analysis skipped: {e}")

            # ==================================================================
            # 6. NEW — AUTOMATIC COMPRESSOR DETECTION & WORKING-HOURS ANALYTICS
            # ==================================================================
            st.markdown('<div class="sec-title">🔧 Compressor Working Hours Analysis</div>', unsafe_allow_html=True)

            try:
                compressors = detect_compressors(c.columns)

                if not compressors:
                    st.warning("No compressor columns detected. Expected patterns like `Compressor-1 Stop time`.")
                else:
                    st.success(f"Detected **{len(compressors)}** compressor(s): {', '.join(sorted(compressors.keys()))}")

                    # 6a. Build per-row working-hours dataframe
                    # Working hrs = 24 - OFF duration (stop -> start)
                    wh_df = pd.DataFrame({date_col: c[date_col].values})
                    
                    for comp_id, cols in compressors.items():
                        comp_name = f"Compressor {comp_id}"
                        
                        if 'stop' in cols and 'start' in cols:
                            stop_col, start_col = cols['stop'], cols['start']
                            
                            def _calc_wh(row, _sc=stop_col, _tc=start_col):
                                try:
                                    stop_t = parse_time_string(row[_sc])
                                    start_t = parse_time_string(row[_tc])
                                    if stop_t and start_t:
                                        off_h = calculate_off_duration_hours(stop_t, start_t)
                                        return round(max(0.0, 24.0 - off_h), 2)
                                except Exception:
                                    pass
                                return None
                            
                            wh_df[comp_name] = c.apply(_calc_wh, axis=1)
                            
                        elif 'run' in cols:
                            # Direct numeric duration column
                            wh_df[comp_name] = pd.to_numeric(c[cols['run']], errors='coerce')

                    # Drop rows where every compressor is NaN
                    comp_cols = [col for col in wh_df.columns if col != date_col]
                    if comp_cols:
                        wh_df = wh_df.dropna(subset=comp_cols, how='all').reset_index(drop=True)

                    if wh_df.empty or not comp_cols:
                        st.warning("No valid compressor working-hours data could be calculated.")
                    else:
                        # 6b. Summary statistics table
                        summary_rows = []
                        for cc in comp_cols:
                            valid = wh_df[cc].dropna()
                            if valid.empty: continue
                            summary_rows.append({
                                'Compressor': cc,
                                'Total Hours': round(valid.sum(), 2),
                                'Avg Daily Hours': round(valid.mean(), 2),
                                'Max Daily Hours': round(valid.max(), 2),
                                'Days Active': int(len(valid))
                            })

                        if not summary_rows:
                            st.warning("All compressor records were invalid or empty.")
                        else:
                            summary_df = pd.DataFrame(summary_rows)
                            
                            st.markdown('<div class="sec-title">📊 Compressor Performance Summary</div>', unsafe_allow_html=True)
                            st.dataframe(
                                summary_df.style.format({'Total Hours': '{:,.2f}', 'Avg Daily Hours': '{:,.2f}', 'Max Daily Hours': '{:,.2f}'}),
                                use_container_width=True, hide_index=True
                            )

                            # 6c. Melt once for efficient charting
                            melted = wh_df.melt(id_vars=[date_col], var_name='Compressor', value_name='Working Hours').dropna(subset=['Working Hours'])

                            # CHART 1: Bar Chart
                            st.markdown('<div class="sec-title">Total Working Hours by Compressor</div>', unsafe_allow_html=True)
                            fig_bar = px.bar(summary_df, x='Compressor', y='Total Hours', color='Compressor', text='Total Hours')
                            fig_bar.update_layout(showlegend=False, height=400, margin=dict(l=20, r=20, t=40, b=20))
                            fig_bar.update_traces(texttemplate='%{text:.1f}', textposition='outside')
                            st.plotly_chart(fig_bar, use_container_width=True)

                            # CHART 2: Daily Trend Line
                            st.markdown('<div class="sec-title">Daily Working Hours Trend</div>', unsafe_allow_html=True)
                            fig_line = px.line(melted, x=date_col, y='Working Hours', color='Compressor', markers=True)
                            fig_line.update_layout(height=400, hovermode='x unified', margin=dict(l=20, r=20, t=40, b=20))
                            st.plotly_chart(fig_line, use_container_width=True)

                            # CHART 3: Stacked Area
                            st.markdown('<div class="sec-title">Daily Compressor Contribution (Stacked Area)</div>', unsafe_allow_html=True)
                            fig_area = px.area(melted, x=date_col, y='Working Hours', color='Compressor')
                            fig_area.update_layout(height=400, hovermode='x unified', margin=dict(l=20, r=20, t=40, b=20))
                            st.plotly_chart(fig_area, use_container_width=True)

                            # CHART 4: Pie Chart
                            st.markdown('<div class="sec-title">Compressor Usage Distribution</div>', unsafe_allow_html=True)
                            fig_pie = px.pie(summary_df, values='Total Hours', names='Compressor', hole=0.3)
                            fig_pie.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20))
                            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                            st.plotly_chart(fig_pie, use_container_width=True)

            except Exception as e:
                st.error(f"Compressor analysis failed: {e}")
                st.info("Verify that compressor columns follow patterns like `Compressor-1 Stop time`.")

            # ------------------------------------------------------------------
            # 7. RAW DATA INSPECTOR & CSV EXPORT (Existing)
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
        # Outer safety net
        st.error(f"Compressor Optimisation tab encountered an error: {e}")
        st.info("The rest of the dashboard remains fully functional.")
