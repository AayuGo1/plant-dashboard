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
GITHUB_FOLDER = ""

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
#  PROCESSED ENERGY FILE LOADER - ENHANCED
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
            df = read_excel_from_github(url)
            
        # Clean column names
        df = df[~df.iloc[:, 0].astype(str).str.contains(r'source|v1|Date|consump', case=False, na=False)]
        df.columns = [str(c).strip() for c in df.columns]
        
        # Identify date column
        date_col = next((c for c in df.columns if c.lower() in ['date', 'timestamp', 'time']), None)
        if not date_col:
            return None
            
        # Parse dates carefully
        df[date_col] = df[date_col].astype(str).str.strip()
        df['DateIndex'] = pd.to_datetime(df[date_col], errors='coerce', format='%Y-%m-%d')
        
        if df['DateIndex'].isna().any():
            df.loc[df['DateIndex'].isna(), 'DateIndex'] = pd.to_datetime(df.loc[df['DateIndex'].isna(), date_col], errors='coerce')
            
        df = df.dropna(subset=['DateIndex'])
        
        # Convert numeric columns
        for col in df.columns:
            if col != 'DateIndex' and col != date_col:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Calculate consumption deltas for V1-V9 if not present
        for i in range(1, 10):
            consump_col = f"consump. v{i}"
            reg_col = f"V{i}"
            
            if consump_col in df.columns and reg_col in df.columns:
                computed_diff = df[reg_col].diff()
                df[consump_col] = df.apply(
                    lambda row: computed_diff.loc[row.name] if (pd.isna(row[consump_col]) or row[consump_col] == 0) and pd.notna(computed_diff.loc[row.name]) and computed_diff.loc[row.name] > 0 else row[consump_col],
                    axis=1
                )
        
        # Calculate aggregated consumption if not present
        dunkin_c = 'dunkin consmp.'
        clc_c = 'clc consump.'
        bmc_c = 'bmc consump.'
        deep_c = 'deep consumption'
        
        if dunkin_c in df.columns:
            df[dunkin_c] = df.apply(lambda r: (r['consump. v1'] if pd.notna(r['consump. v1']) else 0) + (r['consump. v6'] if pd.notna(r['consump. v6']) else 0) if r[dunkin_c] == 0 else r[dunkin_c], axis=1)
        if clc_c in df.columns:
            df[clc_c] = df.apply(lambda r: (r['consump. v3'] if pd.notna(r['consump. v3']) else 0) + (r['consump. v8'] if pd.notna(r['consump. v8']) else 0) if r[clc_c] == 0 else r[clc_c], axis=1)
        if bmc_c in df.columns:
            df[bmc_c] = df.apply(lambda r: (r['consump. v2'] if pd.notna(r['consump. v2']) else 0) + (r['consump. v7'] if pd.notna(r['consump. v7']) else 0) if r[bmc_c] == 0 else r[bmc_c], axis=1)
        if deep_c in df.columns:
            df[deep_c] = df.apply(lambda r: (r['consump. v4'] if pd.notna(r['consump. v4']) else 0) + (r['consump. v5'] if pd.notna(r['consump. v5']) else 0) + (r['consump. v9'] if pd.notna(r['consump. v9']) else 0) if r[deep_c] == 0 else r[deep_c], axis=1)

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
    all_files = list_github_files()
    match = next((u for n, u in all_files if "freon" in n.lower() and n.endswith(".xlsx")), None)
    if not match:
        return None
    try:
        preview = read_excel_from_github(match, sheet_name=sheet_name, header=None, engine='openpyxl')
        hdr = fallback_header_row
        for i in range(min(15, len(preview))):
            row = [str(x).lower() for x in preview.iloc[i].dropna()]
            if any('date' in x or 'stop time' in x or 'start time' in x for x in row):
                hdr = i
                break
        df = read_excel_from_github(match, sheet_name=sheet_name, header=hdr, engine='openpyxl')
        df = df.dropna(axis=1, how='all')
        
        if df.empty:
            return df
            
        df.columns = [str(c).strip() for c in df.columns]
        
        if sheet_name == 'Sheet3' and len(df.columns) >= 12:
            df.columns.values[11] = 'Saving in hrs'
        elif sheet_name == 'Sheet3':
            last = df.columns[-1]
            if 'unnamed' in str(last).lower():
                df = df.rename(columns={last: 'Saving in hrs'})
                
        fc = df.columns[0]
        df = df[df[fc].astype(str).str.strip().str.lower() != 'total']
        return df
    except Exception as e:
        st.warning(f"Could not load sheet {sheet_name}: {e}")
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

# Get actual date range from loaded data
if e_df is not None and not e_df.empty:
    start_date = e_df['DateIndex'].min().strftime('%d %b %Y')
    end_date = e_df['DateIndex'].max().strftime('%d %b %Y')
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
#  TAB 1 — ACTIVE ENERGY METERS (ENHANCED WITH UPLOADED DATA)
# ==============================================================================
with tab_energy:
    if e_df is not None and not e_df.empty:
        # Data Quality Summary
        st.markdown('<div class="sec-title">📊 Data Quality & Structure Summary</div>', unsafe_allow_html=True)
        
        date_col = 'DateIndex'
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
        
        # Identify all column types
        consump_cols = [c for c in e_df.columns if 'consump. v' in c.lower() and c != 'consumption']
        v_meter_cols = [c for c in e_df.columns if c.startswith('V') and c[1:].isdigit()]
        
        dunkin_col = next((c for c in e_df.columns if 'dunkin consmp.' in c.lower()), None)
        clc_col = next((c for c in e_df.columns if 'clc consump.' in c.lower()), None)
        bmc_col = next((c for c in e_df.columns if 'bmc consump.' in c.lower()), None)
        deep_col = next((c for c in e_df.columns if 'deep consumption' in c.lower()), None)
        
        eq_cols = [c for c in [dunkin_col, clc_col, bmc_col, deep_col] if c is not None]
        
        # Check for data quality issues
        missing_dates = pd.date_range(start=start_date, end=end_date).difference(e_df[date_col])
        if len(missing_dates) > 0:
            st.markdown(f'<div class="alert-warn">⚠️ <strong>Data Quality Alert:</strong> {len(missing_dates)} missing date(s) detected in the range.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="alert-ok">✓ <strong>Data Integrity:</strong> Complete date coverage with no gaps detected.</div>', unsafe_allow_html=True)
        
        st.markdown("")
        
        # KPI Metrics
        st.markdown('<div class="sec-title">📈 Total Energy Consumption Summary (kWh)</div>', unsafe_allow_html=True)
        
        def get_sum(col_name):
            if col_name and col_name in e_df.columns:
                return pd.to_numeric(e_df[col_name], errors='coerce').sum()
            return 0.0
        
        def get_avg(col_name):
            if col_name and col_name in e_df.columns:
                return pd.to_numeric(e_df[col_name], errors='coerce').mean()
            return 0.0
        
        def get_max(col_name):
            if col_name and col_name in e_df.columns:
                return pd.to_numeric(e_df[col_name], errors='coerce').max()
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
        
        # V1-V9 Channel Analysis
        if consump_cols:
            st.markdown('<div class="sec-title">📊 Daily Consumption Profile — V1 to V9 Channels</div>', unsafe_allow_html=True)
            st.markdown(f"*Analyzing {len(consump_cols)} meter channels across {total_days} days*")
            
            fig = go.Figure()
            x_dates = e_df[date_col].dt.strftime('%d-%b').tolist()
            
            colors = ['#002D62', '#E01934', '#FF9F1C', '#16A34A', '#0EA5E9', '#8B5CF6', '#EC4899', '#F59E0B', '#10B981']
            meter_names = {
                'consump. v1': 'V1 - Dunkin Blast',
                'consump. v2': 'V2 - BMC Blast',
                'consump. v3': 'V3 - CLC Blast',
                'consump. v4': 'V4 - Deep1 Blast',
                'consump. v5': 'V5 - Deep2 Blast',
                'consump. v6': 'V6 - Dunkin Rack',
                'consump. v7': 'V7 - BMC Rack',
                'consump. v8': 'V8 - CLC Rack',
                'consump. v9': 'V9 - Deep Rack'
            }
            
            for i, col in enumerate(consump_cols):
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
        
        # Process Zone Loads - Stacked Bar Chart
        if eq_cols:
            st.markdown('<div class="sec-title">🏭 Process Zone Daily Energy Distribution</div>', unsafe_allow_html=True)
            
            fig_zone = go.Figure()
            zone_colors = {
                'dunkin': '#002D62',
                'clc': '#FF9F1C',
                'bmc': '#16A34A',
                'deep': '#E01934'
            }
            
            for col in eq_cols:
                col_lower = col.lower()
                color = '#64748B'
                display_name = col
                for key, hex_color in zone_colors.items():
                    if key in col_lower:
                        color = hex_color
                        display_name = col.replace(' consump.', '').replace(' consmp.', '').replace(' consumption', '').title()
                        break
                
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
        
        # Daily Delta Analysis
        st.markdown('<div class="sec-title">📉 Day-over-Day Consumption Change (Δ vs Previous Day)</div>', unsafe_allow_html=True)
        
        diff_energy = pd.DataFrame()
        diff_energy['ChartDate'] = x_dates
        diff_energy['DateObj'] = e_df[date_col]
        diff_cols = []
        
        for col in eq_cols:
            col_label = f"{col} Δ"
            diff_series = pd.to_numeric(e_df[col], errors='coerce').diff().fillna(0)
            diff_energy[col_label] = diff_series.values
            diff_cols.append(col_label)
        
        if not diff_energy.empty:
            # Latest day metrics
            target_energy_row = diff_energy.iloc[-1]
            
            ec1, ec2, ec3, ec4 = st.columns(4)
            
            def render_delta_metric(container, col_name, color, label):
                if col_name and f"{col_name} Δ" in diff_energy.columns:
                    val = target_energy_row[f"{col_name} Δ"]
                    delta_str = f"{val:+,.1f} kWh"
                    delta_color = "normal" if val >= 0 else "inverse"
                    container.metric(f"{label} Daily Δ", delta_str, delta_color=delta_color)
                else:
                    container.metric(f"{label} Daily Δ", "No Data")
            
            with ec1: render_delta_metric(ec1, dunkin_col, "#002D62", "Dunkin'")
            with ec2: render_delta_metric(ec2, clc_col, "#FF9F1C", "CLC")
            with ec3: render_delta_metric(ec3, bmc_col, "#16A34A", "BMC")
            with ec4: render_delta_metric(ec4, deep_col, "#E01934", "Deep Freezer")
            
            st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
            
            # Delta visualization
            fig_delta = go.Figure()
            delta_colors = ['#002D62', '#FF9F1C', '#16A34A', '#E01934']
            
            for i, col in enumerate(diff_cols):
                fig_delta.add_trace(go.Bar(
                    x=x_dates,
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
                    tickvals=x_dates,
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
        
        # Statistical Summary Table
        st.markdown('<div class="sec-title">📋 Statistical Summary by Zone</div>', unsafe_allow_html=True)
        
        summary_data = []
        zone_labels = {
            dunkin_col: "Dunkin'",
            clc_col: "CLC",
            bmc_col: "BMC",
            deep_col: "Deep Freezer"
        }
        
        for col in eq_cols:
            if col:
                series = pd.to_numeric(e_df[col], errors='coerce')
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
        
        # Anomaly Detection
        st.markdown('<div class="sec-title">🚨 Anomaly Detection & Alerts</div>', unsafe_allow_html=True)
        
        for col in eq_cols:
            if col:
                series = pd.to_numeric(e_df[col], errors='coerce')
                mean_val = series.mean()
                std_val = series.std()
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
        
        # Raw Data Export
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
            
            excel_buffer = io.BytesIO()
with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
    e_df.set_index(date_col).to_excel(writer, sheet_name='Energy Data')
st.download_button(
    label="📥 Download Active Energy Data as Excel",
    data=excel_buffer.getvalue(),
    file_name=f"active_energy_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    key="btn_download_energy_excel"
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
    power_df = load_excel_sheet('Sheet1', fallback_header_row=1)
    if power_df is not None and not power_df.empty:
        p = power_df.copy()
        p['Date'] = fast_parse_dates(p['Date'])
        p = p.dropna(subset=['Date']).sort_values('Date')
        
        dunkin_col = next((c for c in p.columns if 'dunkin' in c.lower()), None)
        clc_col = next((c for c in p.columns if 'clc' in c.lower()), None)
        
        if dunkin_col and clc_col:
            p[dunkin_col] = pd.to_numeric(p[dunkin_col], errors='coerce').fillna(0)
            p[clc_col]    = pd.to_numeric(p[clc_col],    errors='coerce').fillna(0)
            savings_col   = next((c for c in p.columns if 'saving' in str(c).lower()), None)
            if savings_col:
                p[savings_col] = pd.to_numeric(p[savings_col], errors='coerce').fillna(0)
            
            p = p[p[dunkin_col] < 500_000]

            if not p.empty:
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.metric("Dunkin' Blast Sum", f"{p[dunkin_col].sum():,.0f} kWh")
                with c2: st.metric("CLC Blast Sum",     f"{p[clc_col].sum():,.0f} kWh")
                with c3: st.metric("Combined Load Matrix", f"{p[dunkin_col].sum()+p[clc_col].sum():,.0f} kWh")
                with c4:
                    if savings_col:
                        st.metric("Optimized Value Catch", f"₹ {p[savings_col].sum():,.2f}", delta="Valid Integration")

                st.markdown('<div class="sec-title">Daily Power Grid Footprint (kWh)</div>', unsafe_allow_html=True)
                st.area_chart(p.set_index('Date')[[dunkin_col, clc_col]], color=["#002D62","#FF9F1C"])
                
                if savings_col:
                    st.markdown('<div class="sec-title">Daily Recovery Realized (₹)</div>', unsafe_allow_html=True)
                    st.bar_chart(p.set_index('Date')[savings_col], color="#16A34A")

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
#  TAB 5 — COMPRESSOR OPTIMISATION (STABILIZED CROSS-ANALYSIS)
# ==============================================================================
with tab_comp:
    comp_df = load_excel_sheet('Sheet3', fallback_header_row=3)
    if comp_df is not None and not comp_df.empty:
        c  = comp_df.copy()
        c  = c[~c.iloc[:,0].astype(str).str.strip().str.lower().str.fullmatch(r'date|total|from|sr\.?\s*no\.?|stop|start', na=False)]
        c.iloc[:,0] = fast_parse_dates(c.iloc[:,0])
        c  = c.dropna(subset=[c.columns[0]]).sort_values(c.columns[0])
        sav_col = next((col for col in c.columns if 'saving' in str(col).lower()), None)

        if sav_col:
            c[sav_col] = pd.to_numeric(c[sav_col], errors='coerce').fillna(0)
            c['Cumulative Savings'] = c[sav_col].cumsum()
            date_col = c.columns[0]

            k1, k2, k3, k4 = st.columns(4)
            with k1: st.metric("Relief Window Saved", f"{c[sav_col].sum():,.1f} hrs")
            with k2: st.metric("Mean Daily Dampening", f"{c[sav_col].mean():.1f} hrs")
            with k3: st.metric("Peak Single Window Stop", f"{c[sav_col].max():.1f} hrs")
            with k4: st.metric("Audited Shift Blocks",     f"{len(c)}")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="sec-title">Daily Rest Allocations (hrs)</div>', unsafe_allow_html=True)
                st.line_chart(c.set_index(date_col)[sav_col], color="#002D62")
            with col2:
                st.markdown('<div class="sec-title">Cumulative Rest Curve Metrics</div>', unsafe_allow_html=True)
                st.area_chart(c.set_index(date_col)['Cumulative Savings'], color="#FF9F1C")

            # Dynamic Cross-Reference Layer (Safe from KeyErrors)
            if temp_df is not None and not temp_df.empty:
                st.markdown('<div class="sec-title">Thermodynamic Drift vs. System Optimization Rest Cycles</div>', unsafe_allow_html=True)
                
                daily_rest_agg = c.groupby(c[date_col].dt.date)[sav_col].sum().reset_index()
                daily_rest_agg.columns = ['Date', 'Rest_Hours']
                daily_rest_agg['Date'] = pd.to_datetime(daily_rest_agg['Date'])
                
                t_clean = temp_df.copy()
                t_clean['Date_Key'] = pd.to_datetime(t_clean['Time']).dt.date
                
                # Dynamic matching to prevent KeyError on temperature streams
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

            st.markdown('<div class="sec-title">Compressor Structural Load Activation Cycles</div>', unsafe_allow_html=True)
            comp_metrics = {}
            run_cols = [col for col in c.columns if any(phrase in str(col).lower() for phrase in ['stop', 'start', 'run', 'comp'])]
            
            for idx, col_name in enumerate(run_cols[:5], 1):
                active_logs = c[c[col_name].astype(str).str.strip().str.len() > 0]
                comp_metrics[f"Compressor Component {idx}"] = len(active_logs)
                
            if comp_metrics:
                cm_df = pd.DataFrame(list(comp_metrics.items()), columns=["Component", "Cycle Count"]).sort_values("Cycle Count", ascending=False)
                st.bar_chart(cm_df.set_index("Component")["Cycle Count"], color="#E01934")

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
    else:
        st.markdown('<div class="alert-info">Compressor analytical tracking components not parsed.</div>', unsafe_allow_html=True)
