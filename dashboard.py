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
        
    name, url = sorted(target_files)[-1]
    
    try:
        if name.endswith(".csv"):
            df = read_csv_from_github(url)
        else:
            raw_df = read_excel_from_github(url, header=None)
            header_row_idx = 0
            for i, row in raw_df.iterrows():
                if any('date' in str(x).lower() for x in row if pd.notna(x)):
                    header_row_idx = i
                    break
            df = read_excel_from_github(url, header=header_row_idx)
            
        df.columns = [str(c).strip() for c in df.columns]
        
        date_col = next((c for c in df.columns if 'date' in c.lower()), None)
        if not date_col:
            if pd.api.types.is_datetime64_any_dtype(df.iloc[:,0]) or '2026' in str(df.iloc[0,0]):
                date_col = df.columns[0]
                df.rename(columns={date_col: 'Date'}, inplace=True)
                date_col = 'Date'
            else:
                return None

        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])
        df = df.sort_values(by=date_col).reset_index(drop=True)
        
        if df.empty:
            return None

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
# HELPER FUNCTIONS FOR COMPRESSOR TAB (TAB 5)
# ==============================================================================
def detect_compressors(columns):
    """
    Automatically detect compressor-related columns using flexible pattern matching.
    Returns: dict {compressor_id: {'stop': col_name, 'start': col_name, 'off': col_name, ...}}
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

        if any(k in col_str for k in ['off', 'down', 'downtime', 'rest', 'shutdown']):
            action = 'off'
        elif 'stop' in col_str:
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
    Robustly parse a time string into a datetime.time object.
    Handles: "11.30.00 PM", "23:30:00", "1:30 AM", NaN, empty strings.
    """
    if pd.isna(time_str):
        return None
    s = str(time_str).strip()
    if s == '' or s.lower() in ('nan', 'none', 'nat', '0', '0.0'):
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

def calculate_off_hours(stop_time, start_time):
    """
    Duration (hours) between a stop event and the next start event.
    Correctly handles overnight crossovers (e.g. 23:30 → 01:30 = 2 h).
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

# ==============================================================================
#  TAB 3 — ENERGY & COST SAVINGS
# ==============================================================================
with tab_power:
    st.markdown('<div class="sec-title">💡 Energy & Cost Savings Dashboard</div>', unsafe_allow_html=True)
    
    power_df = load_excel_sheet('Sheet1', fallback_header_row=1)
    
    if power_df is not None and not power_df.empty:
        p = power_df.copy()
        
        def detect_col(df, keywords, fallback_idx=0):
            cols = [str(c) for c in df.columns]
            for kw in keywords:
                for c in cols:
                    if kw in c.lower():
                        return c
            return cols[fallback_idx] if fallback_idx < len(cols) else None

        date_col = detect_col(p, ['date'], 0)
        dunkin_meter_col = detect_col(p, ['dunkin blast'], 1) 
        clc_meter_col = detect_col(p, ['clc blast'], 6)       
        deep_meter_col = detect_col(p, ['deep-total'], 21)    
        savings_col = detect_col(p, ['saving'], 5)            

        if date_col and dunkin_meter_col and clc_meter_col and savings_col:
            st.success(f"✅ Auto-detected: **Date**=`{date_col}`, **Dunkin Meter**=`{dunkin_meter_col}`, **CLC Meter**=`{clc_meter_col}`, **Raw Savings**=`{savings_col}`")
            
            p[date_col] = fast_parse_dates(p[date_col])
            p = p.dropna(subset=[date_col])
            
            if not p.empty:
                if 'Date' not in p.columns:
                    st.error("❌ Date column missing after parsing.")
                    st.stop()
                
                total_rows = len(p)
                unique_dates = p['Date'].nunique()
                duplicate_count = total_rows - unique_dates
                
                st.write(f"**Data Quality Check:** {total_rows} total rows, {unique_dates} unique dates")
                
                if duplicate_count > 0:
                    st.warning(f"⚠️ Found **{duplicate_count} duplicate date(s)**. Consolidating...")
                    
                    duplicate_dates = p[p['Date'].duplicated(keep=False)]['Date'].unique()
                    st.write(f"**Duplicate dates found:** {', '.join([d.strftime('%d-%b-%Y') for d in duplicate_dates[:10]])}")
                    if len(duplicate_dates) > 10:
                        st.write(f"... and {len(duplicate_dates) - 10} more")
                    
                    numeric_cols = p.select_dtypes(include=[np.number]).columns.tolist()
                    p = (
                        p.groupby('Date', as_index=False)[numeric_cols]
                        .sum(numeric_only=True)
                    )
                    
                    if p['Date'].duplicated().any():
                        st.error("❌ Duplicate dates still exist after consolidation!")
                    else:
                        st.success(f"✓ Duplicates removed. Now {len(p)} unique date rows.")
                
                assert not p['Date'].duplicated().any(), "Duplicate dates detected after cleaning!"
                
                p = p.sort_values(by='Date').reset_index(drop=True)
                
                date_range = pd.date_range(start=p['Date'].min(), end=p['Date'].max(), freq='D')
                p = p.set_index('Date').reindex(date_range).rename_axis('Date').reset_index()
                
                for col in [dunkin_meter_col, clc_meter_col, deep_meter_col, savings_col]:
                    if col and col in p.columns:
                        p[col] = pd.to_numeric(p[col], errors='coerce')
                
                def calc_daily_consumption(series):
                    diff = series.diff()
                    return diff.fillna(0).clip(lower=0)
                
                p['Dunkin Daily'] = calc_daily_consumption(p[dunkin_meter_col])
                p['CLC Daily'] = calc_daily_consumption(p[clc_meter_col])
                if deep_meter_col and deep_meter_col in p.columns:
                    p['Deep Daily'] = calc_daily_consumption(p[deep_meter_col])
                else:
                    p['Deep Daily'] = 0.0
                    
                p['Combined Load'] = p['Dunkin Daily'] + p['CLC Daily'] + p['Deep Daily']
                
                if savings_col and savings_col in p.columns:
                    p['Total Raw Savings'] = p[savings_col].fillna(0)
                else:
                    p['Total Raw Savings'] = 0.0
                    
                p['Optimized Value'] = p['Total Raw Savings'] * 7

                st.markdown('<div class="sec-title">⚡ Key Performance Indicators</div>', unsafe_allow_html=True)
                k1, k2, k3, k4, k5, k6 = st.columns(6)
                with k1: st.metric("Total Dunkin Blast (kWh)", f"{p['Dunkin Daily'].sum():,.0f}")
                with k2: st.metric("Total CLC Blast (kWh)", f"{p['CLC Daily'].sum():,.0f}")
                with k3: st.metric("Total Deep Consumption (kWh)", f"{p['Deep Daily'].sum():,.0f}")
                with k4: st.metric("Combined Load (kWh)", f"{p['Combined Load'].sum():,.0f}")
                with k5: st.metric("Total Savings (₹)", f"₹ {p['Total Raw Savings'].sum():,.2f}")
                with k6: st.metric("Optimized Value (₹)", f"₹ {(p['Total Raw Savings'].sum() * 7):,.2f}")
                
                st.markdown("---")

                st.markdown('<div class="sec-title">Daily Power Grid Footprint (kWh)</div>', unsafe_allow_html=True)
                p_graph = p[p[dunkin_meter_col] < 500_000].copy()
                if not p_graph.empty:
                    st.area_chart(p_graph.set_index('Date')[[dunkin_meter_col, clc_meter_col]], color=["#002D62","#FF9F1C"])
                
                if savings_col and savings_col in p.columns:
                    st.markdown('<div class="sec-title">Daily Recovery Realized (₹)</div>', unsafe_allow_html=True)
                    st.bar_chart(p.set_index('Date')[savings_col], color="#16A34A")

                st.markdown('<div class="sec-title">📋 Daily Energy & Savings Data</div>', unsafe_allow_html=True)
                table_df = p[['Date', 'Dunkin Daily', 'CLC Daily', 'Deep Daily', 'Combined Load', 'Total Raw Savings', 'Optimized Value']].copy()
                table_df.columns = ['Date', 'Dunkin Blast', 'CLC Blast', 'Deep Consumption', 'Combined Load', 'Savings', 'Optimized Value']
                st.dataframe(table_df, use_container_width=True, hide_index=True)

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
            st.error("Expected Blast column labels could not be parsed from Sheet1.")
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
#  TAB 5 — COMPRESSOR OPTIMISATION (REFACTORED INDUSTRIAL CORE)
# ==============================================================================
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

with tab_comp:
    try:
        # ------------------------------------------------------------------
        # 1. LOAD & SANITIZE RAW DATA (Targeting Sheet3 Structure)
        # ------------------------------------------------------------------
        # Sheet3 has multi-level headers. Fallback parsing reads data row-wise.
        raw_comp_df = load_excel_sheet('Sheet3', fallback_header_row=3)

        if raw_comp_df is None or raw_comp_df.empty:
            st.markdown(
                '<div class="alert-info">Compressor tracking components could not be parsed from source file.</div>',
                unsafe_allow_html=True
            )
        else:
            # Clean and normalize header columns
            c = raw_comp_df.copy()
            c.columns = [str(col).strip() for col in c.columns]
            
            # Filter out metadata blocks or leaking structural row texts
            c = c[~c.iloc[:, 0].astype(str).str.strip().str.lower().str.fullmatch(
                r'date|total|from|sr\.?\s*no\.?|stop|start|compressor.*', na=False
            )]
            
            # Process Core Datetime Index cleanly
            c.iloc[:, 0] = pd.to_datetime(c.iloc[:, 0], errors='coerce')
            c = c.dropna(subset=[c.columns[0]]).sort_values(c.columns[0]).reset_index(drop=True)
            date_col = c.columns[0]
            
            # Extract month identifier for summary layers
            c['Year_Month'] = c[date_col].dt.to_period('M').astype(str)

            # ------------------------------------------------------------------
            # 2. DYNAMIC COMPRESSOR CONFIGURATION PARSING
            # ------------------------------------------------------------------
            # Identify columns associated with each compressor unit
            # Based on layout: Column index pairs or names starting with Compressor-X
            compressor_map = {}
            for idx, col_name in enumerate(c.columns):
                if "compressor" in col_name.lower():
                    # Parse out unit identifiers like 'Compressor-1'
                    parts = col_name.split()
                    comp_id = parts[0]
                    if comp_id not in compressor_map:
                        compressor_map[comp_id] = {}
                    
                    # Map the relative roles of adjacent attributes
                    if "stop" in col_name.lower() or "stop" in str(c.iloc[0, idx]).lower():
                        compressor_map[comp_id]['stop_idx'] = idx
                    elif "start" in col_name.lower() or "start" in str(c.iloc[0, idx]).lower():
                        compressor_map[comp_id]['start_idx'] = idx

            # Clean compressor mappings that lack matching pairs
            compressor_map = {k: v for k, v in compressor_map.items() if 'stop_idx' in v}

            # ------------------------------------------------------------------
            # 3. VECTORIZED ANALYTIC METRIC PROCESSING LOOP
            # ------------------------------------------------------------------
            daily_records = []
            validation_warnings = []

            for comp_name, idx_config in compressor_map.items():
                stop_col = c.columns[idx_config['stop_idx']]
                
                # Extract time entries
                stop_series = c[stop_col].astype(str).str.strip()
                
                # Check for an accompanying Start column or compute fixed shift variations
                if 'start_idx' in idx_config:
                    start_col = c.columns[idx_config['start_idx']]
                    start_series = c[start_col].astype(str).str.strip()
                else:
                    start_series = pd.Series("23:59:59", index=c.index)

                # Process row-by-row deltas dynamically
                for i in range(len(c)):
                    row_date = c.loc[i, date_col]
                    row_month = c.loc[i, 'Year_Month']
                    
                    raw_stop = stop_series.iloc[i]
                    raw_start = start_series.iloc[i]

                    # Condition checking for empty operational blocks
                    if raw_stop in ['nan', '', 'None', 'NAT'] or pd.isna(c.iloc[i, idx_config['stop_idx']]):
                        downtime = 0.0
                        cycles = 0
                    else:
                        try:
                            # Convert delta parsing safely
                            t_stop = pd.to_timedelta(raw_stop if ':' in raw_stop else f"{raw_stop}:00")
                            t_start = pd.to_timedelta(raw_start if ':' in raw_start else f"{raw_start}:00")
                            
                            if t_start >= t_stop:
                                downtime = (t_start - t_stop).total_seconds() / 3600.0
                            else:
                                # Midnight cross logic override boundary adjustment
                                downtime = ((t_start + pd.to_timedelta('1D')) - t_stop).total_seconds() / 3600.0
                            cycles = 1
                        except Exception:
                            downtime = 0.0
                            cycles = 0

                    # Clamp downtime limits to standard mathematical day lengths
                    downtime = min(max(downtime, 0.0), 24.0)
                    working_hours = 24.0 - downtime
                    utilization = (working_hours / 24.0) * 100.0

                    # Industrial Validation Checker
                    total_time_check = working_hours + downtime
                    if abs(total_time_check - 24.0) > 1e-4:
                        validation_warnings.append(
                            f"Validation Alert: {row_date.strftime('%Y-%m-%d')} | {comp_name} sum equals {total_time_check:.2f} hrs instead of 24.0."
                        )

                    daily_records.append({
                        'Date': pd.to_datetime(row_date),
                        'Month': row_month,
                        'Compressor': comp_name,
                        'Working Hours': working_hours,
                        'Non-Working Hours': downtime,
                        'Utilization %': utilization,
                        'Start Count': cycles,
                        'Stop Count': cycles
                    })

            # Form unified structured processing dataframe
            analytics_df = pd.DataFrame(daily_records)

            if analytics_df.empty:
                st.warning("No structured compressor status records found or computed.")
            else:
                # --------------------------------------------------------------
                # 4. AGGREGATIONS & SUMMARY TABLES
                # --------------------------------------------------------------
                # A. Core Asset Table Aggregation
                compressor_summary = analytics_df.groupby('Compressor').agg({
                    'Working Hours': 'sum',
                    'Non-Working Hours': 'sum',
                    'Start Count': 'sum',
                    'Stop Count': 'sum',
                    'Utilization %': 'mean'
                }).reset_index()

                # B. Daily Summary Table
                daily_summary = analytics_df.groupby(['Date', 'Compressor']).agg({
                    'Working Hours': 'sum',
                    'Non-Working Hours': 'sum',
                    'Utilization %': 'mean'
                }).reset_index()

                # C. Monthly Summary Table
                monthly_summary = analytics_df.groupby(['Month', 'Compressor']).agg({
                    'Working Hours': 'sum',
                    'Non-Working Hours': 'sum',
                    'Utilization %': 'mean'
                }).reset_index()

                # --------------------------------------------------------------
                # 5. DASHBOARD DISPLAY PANELS & METRICS
                # --------------------------------------------------------------
                # UI Summary Metrics
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.metric("Monitored Compressors", f"{len(compressor_summary)}")
                with m2:
                    avg_util = compressor_summary['Utilization %'].mean()
                    st.metric("Avg System Utilization", f"{avg_util:.1f}%")
                with m3:
                    total_downtime = compressor_summary['Non-Working Hours'].sum()
                    st.metric("Total Cumulative Downtime", f"{total_downtime:,.1f} hrs")
                with m4:
                    total_cycles = compressor_summary['Start Count'].sum()
                    st.metric("Total System Events", f"{int(total_cycles)}")

                # Validation Warnings Section Container
                if validation_warnings:
                    with st.expander("⚠️ System Calculations Consistency Warnings", expanded=False):
                        for warn in validation_warnings[:10]:  # Limit output loop logs
                            st.write(warn)

                # Core Aggregated Metric Matrix UI Table Output
                st.markdown('### 📊 Asset Summary Metrics')
                st.dataframe(
                    compressor_summary.style.format({
                        'Working Hours': '{:,.2f} hrs',
                        'Non-Working Hours': '{:,.2f} hrs',
                        'Utilization %': '{:.2f}%',
                        'Start Count': '{:,.0f}',
                        'Stop Count': '{:,.0f}'
                    }), use_container_width=True, hide_index=True
                )

                # --------------------------------------------------------------
                # 6. INTERACTIVE DYNAMIC VISUALIZATIONS
                # --------------------------------------------------------------
                st.markdown('### 📈 Optimization Performance & Downtime Charts')
                
                v_col1, v_col2 = st.columns(2)
                
                with v_col1:
                    # 1. Compressor Utilization Comparison (Horizontal Bar Chart)
                    fig1 = px.bar(
                        compressor_summary, 
                        x='Utilization %', 
                        y='Compressor', 
                        orientation='h',
                        title='Compressor Utilization Profile Comparison',
                        color='Compressor',
                        color_discrete_sequence=px.colors.qualitative.Prism
                    )
                    st.plotly_chart(fig1, use_container_width=True)

                    # 3. Daily Trend (Line Chart)
                    fig3 = px.line(
                        daily_summary, 
                        x='Date', 
                        y='Working Hours', 
                        color='Compressor',
                        title='Daily Machine Asset Working Trends'
                    )
                    st.plotly_chart(fig3, use_container_width=True)

                with v_col2:
                    # 2. Working vs Non-Working Hours (Stacked Bar Chart)
                    melted_hours = compressor_summary.melt(
                        id_vars=['Compressor'], 
                        value_vars=['Working Hours', 'Non-Working Hours'],
                        var_name='Operating State', 
                        value_name='Hours'
                    )
                    fig2 = px.bar(
                        melted_hours, 
                        x='Compressor', 
                        y='Hours', 
                        color='Operating State',
                        title='Total Lifecycle Accumulation Matrix (Hours)',
                        barmode='stack',
                        color_discrete_map={'Working Hours': '#1E3A8A', 'Non-Working Hours': '#EF4444'}
                    )
                    st.plotly_chart(fig2, use_container_width=True)

                    # 4. Downtime Analysis
                    downtime_sorted = compressor_summary.sort_values(by='Non-Working Hours', ascending=False)
                    fig4 = px.bar(
                        downtime_sorted, 
                        x='Compressor', 
                        y='Non-Working Hours',
                        title='Critical Asset Downtime Impact Matrix (Sorted Desc)',
                        color='Non-Working Hours',
                        color_continuous_scale='Reds'
                    )
                    st.plotly_chart(fig4, use_container_width=True)

                # 5. Heatmap Component Layer
                st.markdown('#### 📅 Heatmap Profile: System Utilization over Time')
                try:
                    daily_summary['Date_Str'] = daily_summary['Date'].dt.strftime('%d-%b-%Y')
                    pivot_heatmap = daily_summary.pivot(
                        index='Compressor', 
                        columns='Date_Str', 
                        values='Utilization %'
                    ).fillna(0.0)

                    fig5 = go.Figure(data=go.Heatmap(
                        z=pivot_heatmap.values,
                        x=pivot_heatmap.columns.tolist(),
                        y=pivot_heatmap.index.tolist(),
                        colorscale='RdYlGn',
                        zmin=0.0, zmax=100.0,
                        colorbar=dict(title='Utilization %')
                    ))
                    fig5.update_layout(
                        margin=dict(l=20, r=20, t=10, b=10),
                        height=280,
                        xaxis=dict(tickangle=45)
                    )
                    st.plotly_chart(fig5, use_container_width=True)
                except Exception as heatmap_err:
                    st.info(f"Heatmap structural grouping skipped: {heatmap_err}")

                # --------------------------------------------------------------
                # 7. TIME-SERIES CONSOLIDATED DATA TABLES PORTAL
                # --------------------------------------------------------------
                st.markdown('### 📅 Historical Summary Registers')
                t_col1, t_col2 = st.columns(2)
                
                with t_col1:
                    st.markdown('#### 📋 Daily Consolidated Table')
                    st.dataframe(
                        daily_summary.style.format({
                            'Working Hours': '{:.2f}',
                            'Non-Working Hours': '{:.2f}',
                            'Utilization %': '{:.2f}%'
                        }), use_container_width=True, hide_index=True
                    )
                with t_col2:
                    st.markdown('#### 📋 Monthly Operational Summary')
                    st.dataframe(
                        monthly_summary.style.format({
                            'Working Hours': '{:.2f}',
                            'Non-Working Hours': '{:.2f}',
                            'Utilization %': '{:.2f}%'
                        }), use_container_width=True, hide_index=True
                    )

    except Exception as e:
        st.error(f"Compressor Optimisation Module execution context error: {e}")
