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
import plotly.express as px
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

# Shared UI Styles
st.markdown("""
<style>
html, body, [class*="css"] { font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif; }
.block-container { padding: 1.5rem 2.5rem 3rem; background: #F4F6F9; }
section[data-testid="stSidebar"] { background: #002D62 !important; border-right: none !important; }
section[data-testid="stSidebar"] * { color: #CBD5E0 !important; }
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 { color: #FFFFFF !important; }
section[data-testid="stSidebar"] input { background: #001840 !important; border: 1px solid #1E3A8A !important; color: #FFFFFF !important; border-radius: 4px !important; font-size: 12px !important; }
section[data-testid="stSidebar"] label { color: #94A3B8 !important; font-size: 10px !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.8px !important; }
.jfl-header-container { background: #FFFFFF; border-radius: 8px; padding: 24px; margin-bottom: 24px; border: 1px solid #E2E8F0; border-left: 6px solid #E01934; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02); }
.jfl-header-title { font-size: 24px; font-weight: 800; color: #002D62; letter-spacing: -0.5px; }
.jfl-header-subtitle { font-size: 11px; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; color: #64748B; margin-top: 4px; }
.jfl-header-meta-box { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 10px 16px; }
.jfl-meta-label { font-size: 9px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; color: #94A3B8; margin-bottom: 2px; }
.jfl-meta-value { font-size: 13px; font-weight: 700; color: #002D62; }
div[data-testid="stMetric"] { background: #FFFFFF !important; border: 1px solid #E2E8F0 !important; border-radius: 8px !important; padding: 20px 22px !important; box-shadow: 0 1px 4px rgba(0,0,0,0.05) !important; border-left: 5px solid #002D62 !important; }
div[data-testid="stMetricLabel"] p { color: #64748B !important; font-size: 10.5px !important; font-weight: 700 !important; letter-spacing: 0.7px !important; text-transform: uppercase !important; }
div[data-testid="stMetricValue"] div { color: #0F172A !important; font-size: 26px !important; font-weight: 800 !important; }
.sec-title { font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 1px; margin: 28px 0 12px 0; padding-bottom: 8px; border-bottom: 1px solid #E2E8F0; }
.alert-warn { background: #FFFBEB; border: 1px solid #FDE68A; border-left: 4px solid #F59E0B; border-radius: 6px; padding: 12px 16px; font-size: 13px; color: #92400E; margin-bottom:12px; }
.alert-ok   { background: #F0FDF4; border: 1px solid #BBF7D0; border-left: 4px solid #16A34A; border-radius: 6px; padding: 12px 16px; font-size: 13px; color: #14532D; margin-bottom:12px; }
.alert-info { background: #EFF6FF; border: 1px solid #BFDBFE; border-left: 4px solid #3B82F6; border-radius: 6px; padding: 12px 16px; font-size: 13px; color: #1E3A8A; margin-bottom:12px; }
.status-pill { display: inline-block; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 700; }
.status-ok  { background:#D1FAE5; color:#065F46; border:1px solid #A7F3D0; }
.status-err { background:#FEE2E2; color:#991B1B; border:1px solid #FCA5A5; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  REUSABLE ENGINE & UTILITIES
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

def read_any_file(name, url, sheet_name=None, header_row=0):
    """Unified file reader handling extensions and sheet selections seamlessly."""
    b_data = fetch_file_bytes(url)
    if name.endswith('.csv'):
        return pd.read_csv(io.BytesIO(b_data))
    else:
        return pd.read_excel(io.BytesIO(b_data), sheet_name=sheet_name, header=header_row, engine='openpyxl')

def fast_parse_dates(series):
    cleansed = series.astype(str).str.strip().str.split(' ').str[0]
    parsed_df = pd.to_datetime(cleansed, errors='coerce', format='%Y-%m-%d')
    if parsed_df.isna().all():
        parsed_df = pd.to_datetime(cleansed, errors='coerce', dayfirst=True)
    return parsed_df

def parse_time_string(t):
    if pd.isna(t) or str(t).strip().lower() in ['nan', 'none', '-']:
        return None
    t_str = str(t).strip()
    for fmt in ['%H:%M:%S', '%H:%M', '%I:%M %p', '%I:%M:%S %p']:
        try:
            return pd.to_datetime(t_str, format=fmt).time()
        except ValueError:
            continue
    return None

def calculate_off_hours(stop, start):
    if not stop or not start:
        return np.nan
    t_stop = pd.to_datetime(str(stop), errors='coerce')
    t_start = pd.to_datetime(str(start), errors='coerce')
    if pd.isna(t_stop) or pd.isna(t_start):
        return np.nan
    diff = (t_start - t_stop).total_seconds() / 3600.0
    return diff if diff >= 0 else diff + 24.0

# ─────────────────────────────────────────────────────────────
#  DYNAMIC SCHEMA MATCHER
# ─────────────────────────────────────────────────────────────
def detect_compressor_columns(columns):
    """Scans and dynamically groups structural compressor metadata."""
    mapping = {}
    for col in columns:
        match = re.search(r'(?:compressor|comp[-_]?)\s*[-_]?\s*(\d+)', col, re.IGNORECASE)
        if match:
            c_id = match.group(1)
            if c_id not in mapping:
                mapping[c_id] = {}
            col_lower = col.lower()
            if 'stop' in col_lower: mapping[c_id]['stop'] = col
            elif 'start' in col_lower: mapping[c_id]['start'] = col
            elif 'run' in col_lower: mapping[c_id]['run'] = col
            elif 'off' in col_lower or 'down' in col_lower: mapping[c_id]['off'] = col
    return mapping

@st.cache_data(ttl=300)
def load_log_workbook(refrigeration_type='freon'):
    """Finds and maps data from workbook types based on selected dynamic engine."""
    all_files = list_github_files()
    match_url, match_name = None, None
    for n, u in all_files:
        if refrigeration_type in n.lower() and n.endswith(".xlsx"):
            match_url, match_name = u, n
            break
            
    if not match_url:
        return None, None, None
        
    # Read Sheets
    try:
        s1 = read_any_file(match_name, match_url, sheet_name=0, header_row=1)
        s2 = read_any_file(match_name, match_url, sheet_name=1, header_row=2)
        s3 = read_any_file(match_name, match_url, sheet_name=2, header_row=3)
        return s1, s2, s3
    except Exception as e:
        st.sidebar.error(f"Error reading {refrigeration_type} sheets: {e}")
        return None, None, None

# ─────────────────────────────────────────────────────────────
#  SIDEBAR MANAGEMENT
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
    
    # SYSTEM SELECTOR SWITCH ENGINE
    plant_engine = st.selectbox(
        "🏭 SELECT REFRIGERATION SYSTEM",
        options=["Freon System", "Ammonia System"],
        index=0
    )
    ref_type = "freon" if "Freon" in plant_engine else "ammonia"

    if st.button("🔄 Refresh Data Now"):
        st.cache_data.clear()
        st.rerun()

    all_files = list_github_files()
    has_target_wb = any(ref_type in n.lower() for n, _ in all_files)
    
    st.markdown("<hr style='border-color:#1E3A8A; margin:14px 0;'>", unsafe_allow_html=True)
    st.markdown(f'<span class="status-pill status-{"ok" if has_target_wb else "err"}">● Engine Active: {ref_type.upper()}</span>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  DATA PIPELINE INTEGRATION
# ─────────────────────────────────────────────────────────────
sheet1, sheet2, sheet3 = load_log_workbook(ref_type)

# Date calculations based on loaded file space
if sheet1 is not None and not sheet1.empty:
    sheet1.columns = [c.strip() for c in sheet1.columns]
    date_col = next((c for c in sheet1.columns if 'date' in c.lower()), sheet1.columns[0])
    sheet1[date_col] = fast_parse_dates(sheet1[date_col])
    sheet1 = sheet1.dropna(subset=[date_col])
    start_str = sheet1[date_col].min().strftime('%d %b %Y') if not sheet1.empty else "N/A"
    end_str = sheet1[date_col].max().strftime('%d %b %Y') if not sheet1.empty else "N/A"
    date_range_str = f"{start_str} – {end_str}"
else:
    date_range_str = "No Data Loaded"

st.markdown(f"""
<div class="jfl-header-container">
    <div style="display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 16px;">
        <div>
            <div class="jfl-header-subtitle">Supply Chain & Manufacturing · Operational Intelligence</div>
            <div class="jfl-header-title">{plant_engine} Performance Hub</div>
        </div>
        <div style="display: flex; gap: 12px;">
            <div class="jfl-header-meta-box">
                <div class="jfl-meta-label">Reporting Window</div>
                <div class="jfl-meta-value">{date_range_str}</div>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Tabs
tab_power, tab_runtime, tab_comp = st.tabs([
    "💡 Energy & Cost Savings",
    "⚙️ Asset Duty Cycles",
    "📉 Compressor Optimisation"
])

# ─────────────────────────────────────────────────────────────
#  TAB 1: ENERGY & COST SAVINGS
# ─────────────────────────────────────────────────────────────
with tab_power:
    if sheet1 is not None and not sheet1.empty:
        df1 = sheet1.copy()
        df1.columns = [c.strip() for c in df1.columns]
        
        # Dynamic Target ID matching
        date_col = next((c for c in df1.columns if 'date' in c.lower()), df1.columns[0])
        consumption_cols = [c for c in df1.columns if 'blast' in c.lower() or 'total' in c.lower() or 'kwh' in c.lower()]
        savings_cols = [c for c in df1.columns if 'savings' in c.lower() or 'recovery' in c.lower()]
        
        # Calculations
        for c in consumption_cols:
            df1[c] = pd.to_numeric(df1[c], errors='coerce')
        for s in savings_cols:
            df1[s] = pd.to_numeric(df1[s], errors='coerce').fillna(0)
            
        df1['Total Savings'] = df1[savings_cols].sum(axis=1)
        
        # Display Metrics
        st.markdown('<div class="sec-title">⚡ KPI Summary Matrix</div>', unsafe_allow_html=True)
        m_cols = st.columns(max(len(consumption_cols) + 1, 4))
        for idx, col_name in enumerate(consumption_cols):
            m_cols[idx].metric(f"{col_name}", f"{df1[col_name].sum():,.0f} kWh")
        m_cols[-1].metric("Total Savings Realized", f"₹{df1['Total Savings'].sum():,.2f}")
        
        # Plots
        st.markdown('<div class="sec-title">📈 Daily Performance Profile Metrics</div>', unsafe_allow_html=True)
        fig_p = px.line(df1, x=date_col, y=consumption_cols, title="Energy Profile Evolution Trends")
        st.plotly_chart(fig_p, use_container_width=True)
        
        fig_s = px.bar(df1, x=date_col, y='Total Savings', color_discrete_sequence=['#16A34A'], title="Realized Savings Breakdown")
        st.plotly_chart(fig_s, use_container_width=True)
    else:
        st.info("Please verify your file naming schema conventions match up correctly.")

# ─────────────────────────────────────────────────────────────
#  TAB 2: ASSET DUTY CYCLES
# ─────────────────────────────────────────────────────────────
with tab_runtime:
    if sheet2 is not None and not sheet2.empty:
        df2 = sheet2.copy()
        df2.columns = [c.strip() for c in df2.columns]
        date_col = next((c for c in df2.columns if 'date' in c.lower()), df2.columns[0])
        df2[date_col] = fast_parse_dates(df2[date_col])
        df2 = df2.dropna(subset=[date_col])
        
        kwh_cols = [c for c in df2.columns if 'kwh' in c.lower() or 'draw' in c.lower() or 'running' in c.lower()]
        for col in kwh_cols:
            df2[col] = pd.to_numeric(df2[col], errors='coerce').fillna(0)
            
        if kwh_cols:
            st.markdown('<div class="sec-title">⚡ Operational Load Metrics</div>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            c1.metric("Consolidated Draw", f"{df2[kwh_cols[0]].sum():,.0f} kWh")
            c2.metric("Peak Load Registered", f"{df2[kwh_cols[0]].max():,.0f} kWh")
            c3.metric("Average System Base Load", f"{df2[kwh_cols[0]].mean():,.0f} kWh")
            
            st.markdown('<div class="sec-title">📈 Loading Profile Curve Plots</div>', unsafe_allow_html=True)
            fig_r = px.bar(df2, x=date_col, y=kwh_cols[0], color_discrete_sequence=['#002D62'])
            st.plotly_chart(fig_r, use_container_width=True)
    else:
        st.info("Asset tracking components not loaded.")

# ─────────────────────────────────────────────────────────────
#  TAB 3: COMPRESSOR OPTIMISATION
# ─────────────────────────────────────────────────────────────
with tab_comp:
    if sheet3 is not None and not sheet3.empty:
        df3 = sheet3.copy()
        df3.columns = [c.strip() for c in df3.columns]
        date_col = next((c for c in df3.columns if 'date' in c.lower()), df3.columns[0])
        df3[date_col] = fast_parse_dates(df3[date_col])
        df3 = df3.dropna(subset=[date_col])
        
        # Automatically map any number of compressors (Comp 1, Comp 2, etc.)
        comps = detect_compressor_columns(df3.columns)
        
        if comps:
            st.success(f"Successfully mapped {len(comps)} structural compressor nodes.")
            off_df = pd.DataFrame({date_col: df3[date_col].values})
            
            for c_id, columns in comps.items():
                c_name = f"Compressor {c_id}"
                if 'off' in columns:
                    off_df[c_name] = pd.to_numeric(df3[columns['off']], errors='coerce')
                elif 'stop' in columns and 'start' in columns:
                    stops = df3[columns['stop']].apply(parse_time_string)
                    starts = df3[columns['start']].apply(parse_time_string)
                    off_df[c_name] = [calculate_off_hours(sp, st) for sp, st in zip(stops, starts)]
            
            comp_cols = [c for c in off_df.columns if c != date_col]
            melted = off_df.melt(id_vars=[date_col], var_name='Compressor', value_name='OFF Hours').dropna()
            
            # Graphs
            fig_comp = px.bar(melted, x=date_col, y='OFF Hours', color='Compressor', barmode='group', title="Downtime Matrix Performance")
            st.plotly_chart(fig_comp, use_container_width=True)
            
            st.markdown('<div class="sec-title">📋 Summary Statistics Table</div>', unsafe_allow_html=True)
            st.dataframe(off_df, use_container_width=True, hide_index=True)
        else:
            st.warning("No structural compressor schemas matched.")
    else:
        st.info("Tracking metrics matching schema parameters not detected.")
