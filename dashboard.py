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
#  PROCESSED ENERGY FILE LOADER
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
        return None

# ==============================================================================
# HELPER FUNCTIONS FOR COMPRESSOR TAB (TAB 5)
# ==============================================================================
def detect_compressors(columns):
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
        comp_id = f"Compressor-{id_match.group(1)}"

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
    return None

def calculate_off_hours(stop_time, start_time):
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
        st.markdown('<div class="alert-info">Active Energy Analytical Data Components Loaded.</div>', unsafe_allow_html=True)
        # Tab 1 details minimized for scannability

# ==============================================================================
#  TAB 2 — COLD STORAGE TEMPERATURES
# ==============================================================================
with tab_temp:
    if temp_df is not None and not temp_df.empty:
        st.markdown('<div class="alert-info">Cold Storage Thermodynamic Logs Matrix Stream Active.</div>', unsafe_allow_html=True)
        # Tab 2 details minimized for scannability

# ==============================================================================
#  TAB 3 — ENERGY & COST SAVINGS
# ==============================================================================
with tab_power:
    st.markdown('<div class="sec-title">💡 Energy & Cost Savings Dashboard</div>', unsafe_allow_html=True)
    power_df = load_excel_sheet('Sheet1', fallback_header_row=1)
    if power_df is not None and not power_df.empty:
        st.markdown('<div class="alert-info">Power Allocation Recovery Matrix Active.</div>', unsafe_allow_html=True)

# ==============================================================================
#  TAB 4 — ASSET DUTY CYCLES
# ==============================================================================
with tab_runtime:
    runtime_df = load_excel_sheet('Sheet2', fallback_header_row=2)
    if runtime_df is not None and not runtime_df.empty:
        st.markdown('<div class="alert-info">Machine Asset Duty Performance Data Enabled.</div>', unsafe_allow_html=True)

# ==============================================================================
#  TAB 5 — COMPRESSOR OPTIMISATION (TIMELINE-CONSTRAINED RUNTIME ENGINE)
# ==============================================================================
with tab_comp:
    try:
        raw_comp_df = load_excel_sheet('Sheet3', fallback_header_row=3)

        if raw_comp_df is None or raw_comp_df.empty:
            st.markdown('<div class="alert-info">Compressor tracking components could not be parsed.</div>', unsafe_allow_html=True)
        else:
            c = raw_comp_df.copy()
            c.columns = [str(col).strip() for col in c.columns]
            
            c = c[~c.iloc[:, 0].astype(str).str.strip().str.lower().str.fullmatch(
                r'date|total|from|sr\.?\s*no\.?|stop|start|compressor.*', na=False
            )]
            
            c.iloc[:, 0] = pd.to_datetime(c.iloc[:, 0], errors='coerce')
            c = c.dropna(subset=[c.columns[0]]).sort_values(c.columns[0]).reset_index(drop=True)
            date_col = c.columns[0]

            # ──────────────────────────────────────────────────────────
            # CRITICAL TIMELINE BOUNDARY FILTER (2026-04-19 till 2026-05-04)
            # ──────────────────────────────────────────────────────────
            start_window = pd.to_datetime('2026-04-19')
            end_window = pd.to_datetime('2026-05-04')
            c = c[(c[date_col] >= start_window) & (c[date_col] <= end_window)].reset_index(drop=True)

            c['Year_Month'] = c[date_col].dt.to_period('M').astype(str)

            # Map relational structural column indices layout
            compressor_map = {}
            comp_num = 1
            for idx in range(1, len(c.columns) - 1, 2):
                if idx + 1 < len(c.columns):
                    col_left = str(c.columns[idx]).lower()
                    if "saving" in col_left:
                        break
                    comp_id = f"Compressor-{comp_num}"
                    compressor_map[comp_id] = {
                        'stop_idx': idx,
                        'start_idx': idx + 1
                    }
                    comp_num += 1

            daily_records = []
            validation_warnings = []

            for comp_name, idx_config in compressor_map.items():
                stop_col = c.columns[idx_config['stop_idx']]
                start_col = c.columns[idx_config['start_idx']]
                
                stop_series = c[stop_col].astype(str).str.strip()
                start_series = c[start_col].astype(str).str.strip()

                for i in range(len(c)):
                    row_date = c.loc[i, date_col]
                    row_month = c.loc[i, 'Year_Month']
                    raw_stop = stop_series.iloc[i]
                    raw_start = start_series.iloc[i]

                    # Idle conditions verification logic processing (Empty log cell = 0 runtime hours)
                    if raw_stop in ['nan', '', 'None', 'NAT', '0', '0.0'] or pd.isna(c.iloc[i, idx_config['stop_idx']]):
                        working_hours = 0.0
                        downtime = 24.0
                        cycles = 0
                    else:
                        try:
                            t_stop = pd.to_timedelta(raw_stop if ':' in raw_stop else f"{raw_stop}:00")
                            t_start = pd.to_timedelta(raw_start if ':' in raw_start else f"{raw_start}:00")
                            
                            if t_start >= t_stop:
                                working_hours = (t_start - t_stop).total_seconds() / 3600.0
                            else:
                                working_hours = ((t_start + pd.to_timedelta('1D')) - t_stop).total_seconds() / 3600.0
                            
                            working_hours = min(max(working_hours, 0.0), 24.0)
                            downtime = 24.0 - working_hours
                            cycles = 1
                        except Exception:
                            working_hours = 0.0
                            downtime = 24.0
                            cycles = 0

                    utilization = (working_hours / 24.0) * 100.0

                    # Integrity verification checks
                    total_time_check = working_hours + downtime
                    if abs(total_time_check - 24.0) > 1e-4:
                        validation_warnings.append(
                            f"Validation Warning: {row_date.strftime('%Y-%m-%d')} | {comp_name} sum equals {total_time_check:.2f} hrs instead of 24.0."
                        )

                    daily_records.append({
                        'Date': pd.to_datetime(row_date), 'Month': row_month, 'Compressor': comp_name,
                        'Working Hours': working_hours, 'Non-Working Hours': downtime,
                        'Utilization %': utilization, 'Start Count': cycles, 'Stop Count': cycles
                    })

            analytics_df = pd.DataFrame(daily_records)

            if analytics_df.empty:
                st.warning("No structured data inside chosen target timeframe metrics constraints (19-Apr to 04-May).")
            else:
                # Compile aggregation summary pipelines
                compressor_summary = analytics_df.groupby('Compressor').agg({
                    'Working Hours': 'sum', 'Non-Working Hours': 'sum',
                    'Start Count': 'sum', 'Stop Count': 'sum', 'Utilization %': 'mean'
                }).reset_index()

                daily_summary = analytics_df.groupby(['Date', 'Compressor']).agg({
                    'Working Hours': 'sum', 'Non-Working Hours': 'sum', 'Utilization %': 'mean'
                }).reset_index()

                monthly_summary = analytics_df.groupby(['Month', 'Compressor']).agg({
                    'Working Hours': 'sum', 'Non-Working Hours': 'sum', 'Utilization %': 'mean'
                }).reset_index()

                st.markdown(f"### 📅 Constrained Optimization window: `{start_window.strftime('%d-%b-%Y')}` to `{end_window.strftime('%d-%b-%Y')}`")

                # Metrics interface output rows
                m1, m2, m3, m4 = st.columns(4)
                with m1: st.metric("Monitored Compressors", f"{len(compressor_summary)}")
                with m2: st.metric("Avg System Utilization", f"{compressor_summary['Utilization %'].mean():.1f}%")
                with m3: st.metric("Total System Working Hours", f"{compressor_summary['Working Hours'].sum():,.1f} hrs")
                with m4: st.metric("Total Cumulative Downtime", f"{compressor_summary['Non-Working Hours'].sum():,.1f} hrs")

                if validation_warnings:
                    with st.expander("⚠️ Calculations Verification Log"):
                        for warn in validation_warnings[:5]: st.write(warn)

                st.markdown('### 📊 Compressor Asset Summary Metrics')
                st.dataframe(
                    compressor_summary.style.format({
                        'Working Hours': '{:,.2f} hrs', 'Non-Working Hours': '{:,.2f} hrs',
                        'Utilization %': '{:.2f}%', 'Start Count': '{:,.0f}', 'Stop Count': '{:,.0f}'
                    }), use_container_width=True, hide_index=True
                )

                st.markdown('### 📈 Optimization Performance & Downtime Charts')
                v_col1, v_col2 = st.columns(2)
                
                with v_col1:
                    fig1 = px.bar(compressor_summary, x='Utilization %', y='Compressor', orientation='h',
                                  title='Compressor Utilization Profile Comparison', color='Compressor',
                                  color_discrete_sequence=px.colors.qualitative.Prism)
                    st.plotly_chart(fig1, use_container_width=True)

                    fig3 = px.line(daily_summary, x='Date', y='Working Hours', color='Compressor',
                                   title='Daily Compressor Working Hours Trend')
                    st.plotly_chart(fig3, use_container_width=True)

                with v_col2:
                    melted_hours = compressor_summary.melt(id_vars=['Compressor'], value_vars=['Working Hours', 'Non-Working Hours'],
                                                           var_name='Operating State', value_name='Hours')
                    fig2 = px.bar(melted_hours, x='Compressor', y='Hours', color='Operating State',
                                  title='Working vs Non-Working Hours Split Matrix', barmode='stack',
                                  color_discrete_map={'Working Hours': '#1E3A8A', 'Non-Working Hours': '#EF4444'})
                    st.plotly_chart(fig2, use_container_width=True)

                    downtime_sorted = compressor_summary.sort_values(by='Non-Working Hours', ascending=False)
                    fig4 = px.bar(downtime_sorted, x='Compressor', y='Non-Working Hours',
                                  title='Total Cumulative Asset Downtime Impact (Sorted Desc)', color='Non-Working Hours',
                                  color_continuous_scale='Reds')
                    st.plotly_chart(fig4, use_container_width=True)

                st.markdown('#### 📅 Heatmap Profile: Compressor Utilization Matrix over Time')
                try:
                    daily_summary['Date_Str'] = daily_summary['Date'].dt.strftime('%d-%b-%Y')
                    pivot_heatmap = daily_summary.pivot(index='Compressor', columns='Date_Str', values='Utilization %').fillna(0.0)
                    fig5 = go.Figure(data=go.Heatmap(
                        z=pivot_heatmap.values, x=pivot_heatmap.columns.tolist(), y=pivot_heatmap.index.tolist(),
                        colorscale='RdYlGn', zmin=0.0, zmax=100.0, colorbar=dict(title='Utilization %')
                    ))
                    fig5.update_layout(margin=dict(l=20, r=20, t=10, b=10), height=280, xaxis=dict(tickangle=45))
                    st.plotly_chart(fig5, use_container_width=True)
                except Exception as heatmap_err:
                    st.info(f"Heatmap structural tracking layout skipped: {heatmap_err}")

                st.markdown('### 📅 Historical Summary Registers')
                t_col1, t_col2 = st.columns(2)
                with t_col1:
                    st.markdown('#### 📋 Daily Summary Table')
                    st.dataframe(daily_summary.style.format({'Working Hours': '{:.2f}', 'Non-Working Hours': '{:.2f}', 'Utilization %': '{:.2f}%'}), use_container_width=True, hide_index=True)
                with t_col2:
                    st.markdown('#### 📋 Monthly Summary Table')
                    st.dataframe(monthly_summary.style.format({'Working Hours': '{:.2f}', 'Non-Working Hours': '{:.2f}', 'Utilization %': '{:.2f}%'}), use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Compressor Optimisation Module execution context error: {e}")
