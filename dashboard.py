import os
import glob
import warnings
import requests
import io
import re
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta, time as dt_time

warnings.filterwarnings("ignore", category=UserWarning)

# ─────────────────────────────────────────────────────────────
#  CONFIGURATION & CONSTANTS
# ─────────────────────────────────────────────────────────────
GITHUB_USER   = "AayuGo1"
GITHUB_REPO   = "plant-dashboard"
GITHUB_BRANCH = "main"

RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}"
API_BASE = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents?ref={GITHUB_BRANCH}"

# Dynamic File Discovery Patterns for Automatic Processing
FILE_PATTERNS = {
    'energy': re.compile(r'PROCESSED_DAILY_VARS_Active_Energy_Report', re.IGNORECASE),
    'temperature': re.compile(r'DataLog_.*\.csv', re.IGNORECASE),
    'freon': re.compile(r'freon.*\.xlsx', re.IGNORECASE)
}

# Standardized Enterprise Plotly Theme
PLOTLY_THEME = dict(
    font_family='Inter, Segoe UI, sans-serif',
    font_size=12,
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    hoverlabel_bgcolor='white',
    hoverlabel_bordercolor='#E2E8F0',
    legend_orientation='h',
    legend_yanchor='bottom',
    legend_y=1.02,
    legend_xanchor='right',
    legend_x=1,
    legend_bgcolor='rgba(255,255,255,0.9)',
    grid_color='#E2E8F0',
    zeroline_color='#E2E8F0'
)

def standardize_chart(fig):
    """Applies the standardized enterprise Plotly theme to a figure safely."""
    fig.update_layout(
        font=dict(family=PLOTLY_THEME['font_family'], size=PLOTLY_THEME['font_size']),
        plot_bgcolor=PLOTLY_THEME['plot_bgcolor'],
        paper_bgcolor=PLOTLY_THEME['paper_bgcolor'],
        hoverlabel=dict(bgcolor=PLOTLY_THEME['hoverlabel_bgcolor'], bordercolor=PLOTLY_THEME['hoverlabel_bordercolor']),
        legend=dict(
            orientation=PLOTLY_THEME['legend_orientation'],
            yanchor=PLOTLY_THEME['legend_yanchor'],
            y=PLOTLY_THEME['legend_y'],
            xanchor=PLOTLY_THEME['legend_xanchor'],
            x=PLOTLY_THEME['legend_x'],
            bgcolor=PLOTLY_THEME['legend_bgcolor']
        )
    )
    if 'xaxis' in fig.layout:
        fig.layout.xaxis.gridcolor = PLOTLY_THEME['grid_color']
        fig.layout.xaxis.zerolinecolor = PLOTLY_THEME['zeroline_color']
    if 'yaxis' in fig.layout:
        fig.layout.yaxis.gridcolor = PLOTLY_THEME['grid_color']
        fig.layout.yaxis.zerolinecolor = PLOTLY_THEME['zeroline_color']
    return fig

# ─────────────────────────────────────────────────────────────
#  PAGE CONFIG & ENTERPRISE CSS
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="JFL – Plant Operations Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="auto"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

html, body, [class*="css"] { 
    font-family: 'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif; 
    color: #0F172A;
}
.block-container { 
    padding: 1.5rem 2.5rem 3rem; 
    background: #F4F6F9; 
    max-width: 1600px;
}

/* Sidebar Styling */
section[data-testid="stSidebar"] { 
    background: linear-gradient(180deg, #001840 0%, #002D62 100%) !important; 
    border-right: none !important; 
}
section[data-testid="stSidebar"] * { color: #CBD5E0 !important; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #FFFFFF !important; }
section[data-testid="stSidebar"] input {
    background: #001840 !important; border: 1px solid #1E3A8A !important;
    color: #FFFFFF !important; border-radius: 6px !important; font-size: 12px !important;
}
section[data-testid="stSidebar"] label {
    color: #94A3B8 !important; font-size: 10px !important; font-weight: 700 !important;
    text-transform: uppercase !important; letter-spacing: 0.8px !important;
}
section[data-testid="stSidebar"] .stButton>button {
    background: #E01934 !important; color: white !important; border: none !important; 
    font-weight: 700 !important; width: 100% !important; border-radius: 6px !important;
    transition: all 0.2s ease !important;
}
section[data-testid="stSidebar"] .stButton>button:hover {
    background: #B91429 !important; transform: translateY(-1px) !important;
}

/* Header System */
.jfl-header-container {
    background: #FFFFFF; border-radius: 12px; padding: 28px 32px; margin-bottom: 28px;
    border: 1px solid #E2E8F0; border-left: 8px solid #E01934;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
    display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 20px;
}
.jfl-header-title { font-size: 26px; font-weight: 800; color: #002D62; letter-spacing: -0.5px; }
.jfl-header-subtitle { font-size: 11px; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; color: #64748B; margin-bottom: 4px; }
.jfl-header-meta-box { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px 18px; min-width: 160px; }
.jfl-meta-label { font-size: 9px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; color: #94A3B8; margin-bottom: 4px; }
.jfl-meta-value { font-size: 14px; font-weight: 800; color: #002D62; }

/* Tabs Styling */
.stTabs [data-baseweb="tab-list"] { 
    gap: 0; background: #FFFFFF; border-bottom: 2px solid #E2E8F0; 
    padding: 0 12px; border-radius: 10px 10px 0 0; 
}
.stTabs [data-baseweb="tab"] { 
    background: transparent; border: none; border-bottom: 3px solid transparent; 
    padding: 16px 24px; font-size: 13px; font-weight: 700; color: #64748B; 
    transition: all 0.2s ease;
}
.stTabs [data-baseweb="tab"]:hover { color: #002D62; }
.stTabs [data-baseweb="tab"][aria-selected="true"] { 
    color: #002D62 !important; border-bottom: 3px solid #E01934 !important; 
    background: transparent !important; 
}

/* Metrics & Cards */
div[data-testid="stMetric"] { 
    background: #FFFFFF !important; border: 1px solid #E2E8F0 !important; 
    border-radius: 10px !important; padding: 20px 24px !important; 
    box-shadow: 0 2px 4px rgba(0,0,0,0.03) !important; 
    border-left: 5px solid #002D62 !important; 
    transition: all 0.2s ease !important;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 15px -3px rgba(0,0,0,0.08) !important;
}
div[data-testid="stMetricLabel"] p { 
    color: #64748B !important; font-size: 11px !important; font-weight: 700 !important; 
    letter-spacing: 0.8px !important; text-transform: uppercase !important; 
}
div[data-testid="stMetricValue"] div { 
    color: #0F172A !important; font-size: 28px !important; font-weight: 800 !important; 
}
div[data-testid="stMetricDelta"] div { 
    font-size: 12px !important; font-weight: 600 !important; 
}

/* Section Titles & Alerts */
.sec-title { 
    font-size: 13px; font-weight: 700; color: #64748B; text-transform: uppercase; 
    letter-spacing: 1.2px; margin: 32px 0 16px 0; padding-bottom: 10px; 
    border-bottom: 2px solid #E2E8F0; display: flex; align-items: center; gap: 8px;
}
.alert-warn { 
    background: #FFFBEB; border: 1px solid #FDE68A; border-left: 5px solid #F59E0B; 
    border-radius: 8px; padding: 14px 18px; font-size: 13.5px; color: #92400E; 
    margin-bottom: 16px; display: flex; align-items: center; gap: 10px;
}
.alert-ok { 
    background: #F0FDF4; border: 1px solid #BBF7D0; border-left: 5px solid #16A34A; 
    border-radius: 8px; padding: 14px 18px; font-size: 13.5px; color: #14532D; 
    margin-bottom: 16px; display: flex; align-items: center; gap: 10px;
}
.alert-info { 
    background: #EFF6FF; border: 1px solid #BFDBFE; border-left: 5px solid #3B82F6; 
    border-radius: 8px; padding: 14px 18px; font-size: 13.5px; color: #1E3A8A; 
    margin-bottom: 16px; display: flex; align-items: center; gap: 10px;
}

/* Status Pills */
.status-pill { 
    display: inline-block; padding: 5px 12px; border-radius: 20px; 
    font-size: 11px; font-weight: 700; 
}
.status-ok { background:#D1FAE5; color:#065F46; border:1px solid #A7F3D0; }
.status-err { background:#FEE2E2; color:#991B1B; border:1px solid #FCA5A5; }

/* Responsive Adjustments */
@media (max-width: 991px) {
    .block-container { padding: 1rem 1.25rem 2rem !important; }
    .jfl-header-title { font-size: 20px !important; }
    div[data-testid="stMetricValue"] div { font-size: 22px !important; }
    .jfl-header-container { flex-direction: column; align-items: flex-start; }
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  AUTOMATIC GITHUB FILE DISCOVERY & PROCESSING FRAMEWORK
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def discover_and_categorize_files():
    """
    Automatically discovers files in the GitHub repository and categorizes them
    based on predefined regex patterns. This enables automatic processing of 
    newly added files without requiring code changes.
    """
    try:
        r = requests.get(API_BASE, timeout=10)
        r.raise_for_status()
        files = [(f["name"], f["download_url"]) for f in r.json() if isinstance(f, dict) and "name" in f and "download_url" in f]
        
        categorized = {k: [] for k in FILE_PATTERNS}
        categorized['unknown'] = []
        
        for name, url in files:
            matched = False
            for category, pattern in FILE_PATTERNS.items():
                if pattern.search(name):
                    categorized[category].append((name, url))
                    matched = True
                    break
            if not matched:
                categorized['unknown'].append((name, url))
                
        return categorized
    except Exception as e:
        st.sidebar.error(f"GitHub connection issue: {e}")
        return {k: [] for k in FILE_PATTERNS}

@st.cache_data(ttl=300)
def fetch_file_bytes(url: str) -> bytes:
    """Fetches raw bytes from a GitHub URL with caching."""
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.content

def read_excel_from_github(url: str, **kwargs):
    """Reads an Excel file directly from GitHub into a pandas DataFrame."""
    return pd.read_excel(io.BytesIO(fetch_file_bytes(url)), **kwargs)

def read_csv_from_github(url: str, **kwargs):
    """Reads a CSV file directly from GitHub into a pandas DataFrame."""
    return pd.read_csv(io.BytesIO(fetch_file_bytes(url)), **kwargs)

# ─────────────────────────────────────────────────────────────
#  DATA PARSING UTILITIES
# ─────────────────────────────────────────────────────────────
def fast_parse_dates(series):
    """Optimized date parsing with fallback formats."""
    cleansed = series.astype(str).str.strip().str.split(' ').str[0]
    parsed_df = pd.to_datetime(cleansed, errors='coerce', format='%Y-%m-%d')
    if parsed_df.isna().all():
        parsed_df = pd.to_datetime(cleansed, errors='coerce', dayfirst=True)
    return parsed_df

def normalize_to_time(val):
    """Converts any time representation to a datetime.time object safely."""
    if val is None: return None
    if isinstance(val, float) and pd.isna(val): return None
    if isinstance(val, pd.Timestamp) and pd.isna(val): return None
    if isinstance(val, dt_time): return val
    if isinstance(val, (datetime, pd.Timestamp)):
        try: return val.time()
        except: return None
    
    val_str = str(val).strip()
    if not val_str or val_str.lower() in ['nan', 'nat', 'none', '', '0:00']: return None
    
    formats_to_try = [
        '%I.%M.%S %p', '%I:%M:%S %p', '%I:%M %p', '%I.%M %p',
        '%H:%M:%S', '%H:%M', '%H.%M.%S'
    ]
    for fmt in formats_to_try:
        try: return datetime.strptime(val_str, fmt).time()
        except (ValueError, TypeError): continue
    
    try:
        parsed = pd.to_datetime(val_str, errors='coerce')
        if pd.notna(parsed): return parsed.time()
    except Exception: pass
    return None

# ─────────────────────────────────────────────────────────────
#  DATA LOADERS (CACHED & ROBUST)
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_processed_energy_data():
    """Loads and processes the latest Active Energy Report automatically."""
    categorized = discover_and_categorize_files()
    target_files = categorized.get('energy', [])
    if not target_files:
        return None
        
    # Automatically select the latest file based on sorted names
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
        
        for i in range(1, 10):
            df[f'V{i}_Consumption'] = df.get(f'calc_consump_v{i}', pd.Series(0, index=df.index))

        return df
        
    except Exception as e:
        st.sidebar.error(f"Failed parsing processed energy file {name}: {e}")
        import traceback
        st.sidebar.text(traceback.format_exc())
        return None

@st.cache_data(ttl=300)
def load_temperature_data():
    """Loads and combines all temperature data logs automatically."""
    categorized = discover_and_categorize_files()
    csv_files = categorized.get('temperature', [])
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

@st.cache_data(ttl=300)
def load_excel_sheet(sheet_name, fallback_header_row):
    """Loads a specific sheet from the Freon Excel workbook automatically."""
    try:
        categorized = discover_and_categorize_files()
        freon_files = categorized.get('freon', [])
        if not freon_files:
            return None
        
        match_url = freon_files[0][1]

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

# ─────────────────────────────────────────────────────────────
#  SIDEBAR & HEADER SYSTEM
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style="padding:16px 0 20px;">
            <div style="font-size:9px; font-weight:700; letter-spacing:1.8px; color:#94A3B8; text-transform:uppercase; margin-bottom:6px;">
                JUBILANT FOODWORKS LIMITED
            </div>
            <div style="font-size:18px; font-weight:800; color:#FFFFFF; line-height:1.25;">
                Plant Operations<br>Dashboard
            </div>
            <div style="margin-top:10px; width:36px; height:3px; background:#E01934; border-radius:2px;"></div>
        </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 Refresh Data Now"):
        st.cache_data.clear()
        st.rerun()

    categorized = discover_and_categorize_files()
    processed_energy_files = categorized.get('energy', [])
    csv_files = categorized.get('temperature', [])
    has_freon = len(categorized.get('freon', [])) > 0

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
                    fixedrange=True
                ),
                showlegend=True
            )
            standardize_chart(fig)
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
                fixedrange=True
            )
        )
        standardize_chart(fig_zone)
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
                    fixedrange=True
                ),
                shapes=[dict(type='line', xref='paper', yref='y', x0=0, y0=0, x1=1, y1=0, line=dict(color='red', width=2, dash='dash'))]
            )
            standardize_chart(fig_delta)
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
            <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:12px 18px; border-left:5px solid #002D62;">
                <div style="font-size:10px; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px;">Dough 1 Delta Variance Sum</div>
                <div style="font-size:18px; font-weight:800; color:#002D62; margin-top:4px;">{d1_sum:,.2f} °C</div>
            </div>
            """, unsafe_allow_html=True)
        with sc2:
            st.markdown(f"""
            <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:12px 18px; border-left:5px solid #0EA5E9;">
                <div style="font-size:10px; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px;">Dough 2 Delta Variance Sum</div>
                <div style="font-size:18px; font-weight:800; color:#002D62; margin-top:4px;">{d2_sum:,.2f} °C</div>
            </div>
            """, unsafe_allow_html=True)
        with sc3:
            st.markdown(f"""
            <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:12px 18px; border-left:5px solid #E01934;">
                <div style="font-size:10px; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px;">Perishable Delta Variance Sum</div>
                <div style="font-size:18px; font-weight:800; color:#002D62; margin-top:4px;">{p_sum:,.2f} °C</div>
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
#  TAB 3 — ENERGY & COST SAVINGS (EXECUTIVE MATRIX ONLY)
# ==============================================================================
with tab_power:
    if e_df is not None and not e_df.empty:
        facilities = {
            'Dunkin': 'dunkin consmp.',
            'CLC': 'clc consump.',
            'BMC': 'bmc consump.',
            'Deep (Blast)': 'deep consumption'
        }
        
        # Robust fallback to calculated columns if specific names are missing
        actual_facilities = {}
        for k, v in facilities.items():
            if v in e_df.columns:
                actual_facilities[k] = v
            else:
                calc_map = {'Dunkin': 'Dunkin Consumption', 'CLC': 'CLC Consumption', 'BMC': 'BMC Consumption', 'Deep (Blast)': 'Deep Consumption'}
                if calc_map[k] in e_df.columns:
                    actual_facilities[k] = calc_map[k]
        
        if not actual_facilities:
            st.markdown('<div class="alert-info">⚠️ Energy data file not found or empty.</div>', unsafe_allow_html=True)
        else:
            df_facilities = e_df[['Date'] + list(actual_facilities.values())].copy()
            df_facilities.columns = ['Date'] + list(actual_facilities.keys())
            
            df_melted = df_facilities.melt(id_vars='Date', var_name='Facility', value_name='Daily Consumption')
            df_melted['Daily Consumption'] = pd.to_numeric(df_melted['Daily Consumption'], errors='coerce').fillna(0).clip(lower=0)
            
            metrics = df_melted.groupby('Facility')['Daily Consumption'].agg([
                ('total_power', 'sum'),
                ('avg_daily', 'mean'),
                ('highest_daily', 'max'),
                ('lowest_daily', 'min'),
                ('days_processed', 'count')
            ]).reset_index()
            
            facility_metrics = dict(zip(metrics['Facility'], metrics.to_dict('records')))
            
            st.markdown('<div class="sec-title">📊 Executive Facility Performance Matrix</div>', unsafe_allow_html=True)
            
            colors = {
                'Dunkin': '#002D62', 
                'CLC': '#FF9F1C', 
                'BMC': '#16A34A', 
                'Deep (Blast)': '#E01934'
            }
            
            st.markdown("""
            <style>
            .fac-card {
                background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 24px;
                box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
                margin-bottom: 20px;
                border-left: 6px solid #002D62;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }
            .fac-card:hover {
                transform: translateY(-3px);
                box-shadow: 0 10px 15px -3px rgba(0,0,0,0.08), 0 4px 6px -2px rgba(0,0,0,0.04);
            }
            .fac-title {
                font-size: 18px;
                font-weight: 800;
                color: #002D62;
                margin-bottom: 15px;
                border-bottom: 2px solid #e2e8f0;
                padding-bottom: 8px;
                letter-spacing: 0.5px;
            }
            .fac-metric {
                display: flex;
                justify-content: space-between;
                margin-bottom: 10px;
                font-size: 13px;
                padding: 4px 0;
            }
            .fac-metric-label {
                color: #64748b;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                font-size: 11px;
            }
            .fac-metric-value {
                color: #0f172a;
                font-weight: 800;
                font-size: 14px;
            }
            </style>
            """, unsafe_allow_html=True)
            
            cols = st.columns(4)
            for idx, fac in enumerate(actual_facilities.keys()):
                with cols[idx]:
                    m = facility_metrics.get(fac, {})
                    total_power = m.get('total_power', 0)
                    avg_daily = m.get('avg_daily', 0)
                    highest = m.get('highest_daily', 0)
                    lowest = m.get('lowest_daily', 0)
                    num_days = int(m.get('days_processed', 0))
                    
                    st.markdown(f"""
                    <div class="fac-card" style="border-left-color: {colors.get(fac, '#002D62')};">
                        <div class="fac-title">{fac}</div>
                        <div class="fac-metric"><span class="fac-metric-label">Total Power</span><span class="fac-metric-value">{total_power:,.0f} kWh</span></div>
                        <div class="fac-metric"><span class="fac-metric-label">Avg Daily</span><span class="fac-metric-value">{avg_daily:,.1f} kWh</span></div>
                        <div class="fac-metric"><span class="fac-metric-label">Highest Daily</span><span class="fac-metric-value">{highest:,.1f} kWh</span></div>
                        <div class="fac-metric"><span class="fac-metric-label">Lowest Daily</span><span class="fac-metric-value">{lowest:,.1f} kWh</span></div>
                        <div class="fac-metric"><span class="fac-metric-label">Total Units</span><span class="fac-metric-value">{total_power:,.0f} kWh</span></div>
                        <div class="fac-metric"><span class="fac-metric-label">Days Processed</span><span class="fac-metric-value">{num_days}</span></div>
                    </div>
                    """, unsafe_allow_html=True)

    else:
        st.markdown('<div class="alert-info">⚠️ Energy data file not found or empty.</div>', unsafe_allow_html=True)

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
                <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:12px 18px; border-left:5px solid #002D62;">
                    <div style="font-size:10px; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px;">Energy Drew</div>
                    <div style="font-size:18px; font-weight:800; color:#002D62; margin-top:4px;">{val:,.1f} kWh</div>
                </div>
                """, unsafe_allow_html=True)
            with rc2:
                val = target_day['Peak System Load Vector (kWh)'] if target_day is not None else 0
                st.markdown(f"""
                <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:12px 18px; border-left:5px solid #FF9F1C;">
                    <div style="font-size:10px; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px;">Peak System Load Vector</div>
                    <div style="font-size:18px; font-weight:800; color:#002D62; margin-top:4px;">{val:,.1f} kWh</div>
                </div>
                """, unsafe_allow_html=True)
            with rc3:
                val = target_day['Mean Load Vector (kWh)'] if target_day is not None else 0
                st.markdown(f"""
                <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:12px 18px; border-left:5px solid #E01934;">
                    <div style="font-size:10px; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px;">Mean Load Vector</div>
                    <div style="font-size:18px; font-weight:800; color:#002D62; margin-top:4px;">{val:,.1f} kWh</div>
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
#  TAB 5 — COMPRESSOR OPTIMISATION (VECTORIZED & OPTIMIZED)
# ==============================================================================
with tab_comp:
    comp_raw = load_excel_sheet('Sheet3', fallback_header_row=1)
    
    if comp_raw is not None and not comp_raw.empty:
        c_df = comp_raw.copy()
        c_df.columns = [str(col).strip() for col in c_df.columns]
        
        if not c_df.empty:
            first_col = c_df.columns[0]
            mask = ~c_df[first_col].astype(str).str.strip().str.lower().str.contains(
                'date|total|from|sr\\.?\\s*no\\.?|running|stop time|start time', 
                case=False, na=False
            )
            c_df = c_df[mask].reset_index(drop=True)
        
        c_df['Parsed_Date'] = pd.to_datetime(c_df.iloc[:, 0], errors='coerce')
        c_df = c_df.dropna(subset=['Parsed_Date'])
        
        TARGET_START = datetime(2026, 4, 26)
        TARGET_END = datetime(2026, 5, 8)
        
        c_df = c_df[
            (c_df['Parsed_Date'] >= TARGET_START) & 
            (c_df['Parsed_Date'] <= TARGET_END)
        ].copy()
        c_df = c_df.sort_values('Parsed_Date').reset_index(drop=True)
        
        if c_df.empty:
            st.markdown('<div class="alert-warn">⚠️ <strong>No Data:</strong> No records found in target range (26-Apr to 08-May 2026).</div>', unsafe_allow_html=True)
        else:
            compressor_config = {}
            for i in range(1, 6):
                comp_name = f"Compressor-{i}"
                stop_col = start_col = None
                for col in c_df.columns:
                    col_lower = col.lower()
                    comp_patterns = [f'compressor-{i}', f'compressor {i}', f'comp-{i}', f'comp {i}']
                    if any(p in col_lower for p in comp_patterns):
                        if 'stop' in col_lower and 'start' not in col_lower: stop_col = col
                        elif 'start' in col_lower and 'stop' not in col_lower: start_col = col
                if stop_col and start_col:
                    compressor_config[comp_name] = {'stop': stop_col, 'start': start_col}
            
            if len(compressor_config) < 5 and len(c_df.columns) >= 11:
                compressor_config = {}
                for i in range(1, 6):
                    comp_name = f"Compressor-{i}"
                    stop_idx = 2 * i - 1
                    start_idx = 2 * i
                    if stop_idx < len(c_df.columns) and start_idx < len(c_df.columns):
                        compressor_config[comp_name] = {
                            'stop': c_df.columns[stop_idx],
                            'start': c_df.columns[start_idx]
                        }
            
            if not compressor_config:
                st.markdown('<div class="alert-warn">⚠️ <strong>Configuration Error:</strong> Could not detect compressor columns.</div>', unsafe_allow_html=True)
            else:
                total_days = (TARGET_END - TARGET_START).days + 1
                all_dates = pd.date_range(start=TARGET_START, end=TARGET_END, freq='D')
                
                # PERFORMANCE OPTIMIZATION: Vectorized grouping instead of nested loop filtering
                c_df['Date_Key'] = c_df['Parsed_Date'].dt.date
                grouped = c_df.groupby('Date_Key').first()
                
                daily_records = []
                summary_records = []
                
                for comp_name, cols in compressor_config.items():
                    stop_col = cols['stop']
                    start_col = cols['start']
                    
                    total_runtime_hrs = 0.0
                    total_downtime_hrs = 0.0
                    
                    for target_date in all_dates:
                        date_key = target_date.date()
                        runtime_hrs = 0.0 
                        
                        if date_key in grouped.index:
                            row = grouped.loc[date_key]
                            t_stop = normalize_to_time(row[stop_col])
                            t_start = normalize_to_time(row[start_col])
                            
                            if t_stop is not None and t_start is not None:
                                stop_mins = t_stop.hour * 60 + t_stop.minute + t_stop.second / 60.0
                                start_mins = t_start.hour * 60 + t_start.minute + t_start.second / 60.0
                                
                                if start_mins < stop_mins:
                                    delta_mins = (1440.0 - stop_mins) + start_mins
                                else:
                                    delta_mins = start_mins - stop_mins
                                    
                                runtime_hrs = max(0.0, delta_mins / 60.0)
                        
                        runtime_hrs = min(24.0, runtime_hrs)
                        downtime_hrs = 24.0 - runtime_hrs
                        
                        total_runtime_hrs += runtime_hrs
                        total_downtime_hrs += downtime_hrs
                        
                        daily_records.append({
                            'Date': target_date,
                            'Compressor': comp_name,
                            'Working Hours': round(runtime_hrs, 2),
                            'Non Working Hours': round(downtime_hrs, 2),
                            'Utilization %': round((runtime_hrs / 24.0) * 100.0, 1)
                        })
                    
                    total_available_hrs = total_days * 24.0
                    summary_records.append({
                        'Compressor': comp_name,
                        'Working Hours': round(total_runtime_hrs, 2),
                        'Non Working Hours': round(total_downtime_hrs, 2),
                        'Utilization %': round((total_runtime_hrs / total_available_hrs) * 100.0, 1),
                        'Downtime %': round((total_downtime_hrs / total_available_hrs) * 100.0, 1)
                    })
                
                df_daily = pd.DataFrame(daily_records, columns=['Date', 'Compressor', 'Working Hours', 'Non Working Hours', 'Utilization %'])
                df_summary = pd.DataFrame(summary_records, columns=['Compressor', 'Working Hours', 'Non Working Hours', 'Utilization %', 'Downtime %'])
                
                for col in ['Working Hours', 'Non Working Hours', 'Utilization %']:
                    df_daily[col] = pd.to_numeric(df_daily[col], errors='coerce')
                for col in ['Working Hours', 'Non Working Hours', 'Utilization %', 'Downtime %']:
                    df_summary[col] = pd.to_numeric(df_summary[col], errors='coerce')
                
                df_daily.dropna(subset=['Working Hours', 'Non Working Hours'], inplace=True)
                
                df_daily['Total Check'] = df_daily['Working Hours'] + df_daily['Non Working Hours']
                validation_failures = df_daily[abs(df_daily['Total Check'] - 24.0) > 0.01]
                
                if len(validation_failures) > 0:
                    st.markdown(f'<div class="alert-warn">⚠️ <strong>Validation Warning:</strong> {len(validation_failures)} record(s) where Working + Non-Working ≠ 24 hours.</div>', unsafe_allow_html=True)
                    with st.expander("View Validation Failures"):
                        st.dataframe(validation_failures, use_container_width=True)
                else:
                    st.markdown('<div class="alert-ok">✓ <strong>Validation Passed:</strong> All daily records sum to exactly 24 hours.</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="sec-title">📊 Compressor Performance Overview</div>', unsafe_allow_html=True)
                avg_util = df_summary['Utilization %'].mean()
                avg_downtime = df_summary['Downtime %'].mean()
                best_comp = df_summary.loc[df_summary['Utilization %'].idxmax(), 'Compressor']
                worst_comp = df_summary.loc[df_summary['Downtime %'].idxmax(), 'Compressor']
                
                k1, k2, k3, k4 = st.columns(4)
                with k1: st.metric("Avg Utilization", f"{avg_util:.1f}%")
                with k2: st.metric("Avg Downtime", f"{avg_downtime:.1f}%")
                with k3: st.metric("Best Performer", best_comp)
                with k4: st.metric("Highest Downtime", worst_comp)
                
                st.markdown('<div class="sec-title">📋 Daily Compressor Performance Table</div>', unsafe_allow_html=True)
                daily_display = df_daily[['Date', 'Compressor', 'Working Hours', 'Non Working Hours', 'Utilization %']].copy()
                daily_display['Date'] = daily_display['Date'].dt.strftime('%d-%b-%Y')
                st.dataframe(daily_display, use_container_width=True, hide_index=True)
                
                st.markdown('<div class="sec-title">📋 Summary Performance Table</div>', unsafe_allow_html=True)
                st.dataframe(df_summary, use_container_width=True, hide_index=True)
                
                st.markdown('<div class="sec-title">📈 Visual Analytics Dashboard</div>', unsafe_allow_html=True)
                chart_colors = ['#002D62', '#E01934', '#FF9F1C', '#16A34A', '#8B5CF6']
                
                # 1. Utilization Comparison
                fig1 = go.Figure()
                fig1.add_trace(go.Bar(
                    y=df_summary['Compressor'], x=df_summary['Utilization %'], orientation='h',
                    marker=dict(color='#002D62', line=dict(color='#001840', width=1)),
                    text=df_summary['Utilization %'].apply(lambda x: f'{x:.1f}%'), textposition='auto'
                ))
                fig1.update_layout(title='Compressor Utilization Comparison', xaxis=dict(title='Utilization (%)', range=[0, 105]), yaxis=dict(title='Compressor', autorange='reversed'), height=350, margin=dict(l=20, r=20, t=50, b=40))
                standardize_chart(fig1)
                
                # 2. Working vs Non Working
                fig2 = go.Figure()
                fig2.add_trace(go.Bar(name='Working Hours', y=df_summary['Compressor'], x=df_summary['Working Hours'], orientation='h', marker_color='#16A34A'))
                fig2.add_trace(go.Bar(name='Non Working Hours', y=df_summary['Compressor'], x=df_summary['Non Working Hours'], orientation='h', marker_color='#E01934'))
                fig2.update_layout(barmode='stack', title='Working vs Non-Working Hours', xaxis=dict(title='Hours'), yaxis=dict(title='Compressor', autorange='reversed'), height=350, margin=dict(l=20, r=20, t=50, b=40))
                standardize_chart(fig2)
                
                col_c1, col_c2 = st.columns(2)
                with col_c1: st.plotly_chart(fig1, use_container_width=True)
                with col_c2: st.plotly_chart(fig2, use_container_width=True)
                
                # 3. Daily Working Trend
                fig3 = go.Figure()
                for idx, comp in enumerate(df_summary['Compressor']):
                    sub = df_daily[df_daily['Compressor'] == comp].sort_values('Date')
                    fig3.add_trace(go.Scatter(x=sub['Date'].dt.strftime('%d-%b'), y=sub['Working Hours'], mode='lines+markers', name=comp, line=dict(color=chart_colors[idx % len(chart_colors)], width=2.5), marker=dict(size=6)))
                fig3.update_layout(title='Daily Working Hours Trend', xaxis=dict(title='Date', tickangle=45), yaxis=dict(title='Working Hours', range=[0, 26]), height=400, margin=dict(l=20, r=20, t=50, b=60))
                standardize_chart(fig3)
                
                # 4. Daily Downtime Trend
                fig4 = go.Figure()
                for idx, comp in enumerate(df_summary['Compressor']):
                    sub = df_daily[df_daily['Compressor'] == comp].sort_values('Date')
                    fig4.add_trace(go.Scatter(x=sub['Date'].dt.strftime('%d-%b'), y=sub['Non Working Hours'], mode='lines+markers', name=comp, line=dict(color=chart_colors[idx % len(chart_colors)], width=2.5), marker=dict(size=6)))
                fig4.update_layout(title='Daily Downtime Trend', xaxis=dict(title='Date', tickangle=45), yaxis=dict(title='Downtime Hours', range=[0, 26]), height=400, margin=dict(l=20, r=20, t=50, b=60))
                standardize_chart(fig4)
                
                col_c3, col_c4 = st.columns(2)
                with col_c3: st.plotly_chart(fig3, use_container_width=True)
                with col_c4: st.plotly_chart(fig4, use_container_width=True)
                
                # 5. Downtime Ranking
                df_sorted_downtime = df_summary.sort_values('Non Working Hours', ascending=True)
                fig5 = go.Figure()
                fig5.add_trace(go.Bar(y=df_sorted_downtime['Compressor'], x=df_sorted_downtime['Non Working Hours'], orientation='h', marker=dict(color='#FF9F1C', line=dict(color='#E8890C', width=1)), text=df_sorted_downtime['Non Working Hours'].apply(lambda x: f'{x:.1f}h'), textposition='auto'))
                fig5.update_layout(title='Downtime Ranking (Lowest to Highest)', xaxis=dict(title='Total Downtime Hours'), yaxis=dict(title='Compressor', autorange='reversed'), height=350, margin=dict(l=20, r=20, t=50, b=40))
                standardize_chart(fig5)
                
                # 6. Utilization Heatmap
                heatmap_pivot = df_daily.pivot_table(index='Compressor', columns='Date', values='Utilization %', aggfunc='mean')
                heatmap_pivot = heatmap_pivot.reindex(sorted(heatmap_pivot.columns), axis=1).fillna(0)
                date_labels = [d.strftime('%d-%b') for d in heatmap_pivot.columns]
                
                fig6 = go.Figure(data=go.Heatmap(
                    z=heatmap_pivot.values, x=date_labels, y=heatmap_pivot.index.tolist(),
                    colorscale=[[0.0, '#E01934'], [0.5, '#FF9F1C'], [1.0, '#16A34A']],
                    zmin=0, zmax=100, text=heatmap_pivot.values.round(1), texttemplate='%{text:.0f}%', textfont=dict(size=10, color='white'),
                    colorbar=dict(title='Utilization %', ticksuffix='%')
                ))
                fig6.update_layout(title='Utilization Heatmap (Date vs Compressor)', xaxis=dict(title='Date', tickangle=45, side='bottom'), yaxis=dict(title='Compressor', autorange='reversed'), height=350, margin=dict(l=20, r=20, t=50, b=60))
                standardize_chart(fig6)
                
                col_c5, col_c6 = st.columns(2)
                with col_c5: st.plotly_chart(fig5, use_container_width=True)
                with col_c6: st.plotly_chart(fig6, use_container_width=True)
                
                st.markdown('<div class="sec-title">📥 Data Export Portal</div>', unsafe_allow_html=True)
                with st.expander("📂 Download Processed Compressor Data", expanded=False):
                    col_dl1, col_dl2 = st.columns(2)
                    with col_dl1:
                        csv_daily = df_daily.to_csv(index=False).encode('utf-8')
                        st.download_button(label="📥 Download Daily Data (CSV)", data=csv_daily, file_name=f"compressor_daily_{TARGET_START.strftime('%Y%m%d')}_to_{TARGET_END.strftime('%Y%m%d')}.csv", mime="text/csv", key="btn_download_comp_daily")
                    with col_dl2:
                        csv_summary = df_summary.to_csv(index=False).encode('utf-8')
                        st.download_button(label="📥 Download Summary Data (CSV)", data=csv_summary, file_name=f"compressor_summary_{TARGET_START.strftime('%Y%m%d')}_to_{TARGET_END.strftime('%Y%m%d')}.csv", mime="text/csv", key="btn_download_comp_summary")
                    st.markdown("**Raw Parsed Data Preview:**")
                    st.dataframe(c_df, use_container_width=True, hide_index=True)
    else:
        st.markdown('<div class="alert-info">⚠️ Compressor optimization data (Sheet3) not available in the repository.</div>', unsafe_allow_html=True)
