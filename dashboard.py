import os
import glob
import warnings
import requests
import io
import streamlit as st
import pandas as pd

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

def read_csv_from_github(url: str, **kwargs):
    return pd.read_csv(io.BytesIO(fetch_file_bytes(url)), **kwargs)

def read_excel_from_github(url: str, **kwargs):
    return pd.read_excel(io.BytesIO(fetch_file_bytes(url)), **kwargs)

# ─────────────────────────────────────────────────────────────
#  PROCESSED ENERGY FILE LOADER (TUNED 1-10 JUNE WINDOW)
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
            
        df.columns = [str(c).strip() for c in df.columns]
        date_col = next((c for c in df.columns if c.lower() in ['date', 'timestamp', 'time']), None)
        if not date_col:
            return None
            
        # Standardize strings to absolute timestamp datatypes
        df['DateIndex'] = pd.to_datetime(df[date_col].astype(str).str.strip(), errors='coerce')
        df = df.dropna(subset=['DateIndex'])
        
        # Explicit chronological trim between June 1st and June 10th, 2026
        df = df[(df['DateIndex'] >= '2026-06-01') & (df['DateIndex'] <= '2026-06-10')]
        
        # Enforce sorted DatetimeIndex format required by Streamlit's native charting timeline
        df = df.sort_values('DateIndex').set_index('DateIndex')
        
        # Convert numeric components cleanly
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        return df
    except Exception as e:
        st.sidebar.error(f"Failed parsing processed energy file {name}: {e}")
        return None

# ─────────────────────────────────────────────────────────────
#  ADDITIONAL LOADER STUBS
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_temperature_data():
    return None

@st.cache_data(ttl=300)
def load_excel_sheet(sheet_name, fallback_header_row):
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
        </div>
    """, unsafe_allow_html=True)
    if st.button("🔄 Refresh Data Now"):
        st.cache_data.clear()
        st.rerun()

# ─────────────────────────────────────────────────────────────
#  MAIN PRESENTATION LAYER
# ─────────────────────────────────────────────────────────────
energy_df = load_processed_energy_data()
date_range_str = "01 Jun 2026 – 10 Jun 2026" if energy_df is not None and not energy_df.empty else "No Data Found"

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
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

tab_energy, tab_temp, tab_power, tab_runtime, tab_comp = st.tabs([
    "⚡  Active Energy Meters", "🌡️  Cold Storage Temperatures", "💡  Energy & Cost Savings", "⚙️  Asset Duty Cycles", "📉  Compressor Optimisation"
])

with tab_energy:
    if energy_df is not None and not energy_df.empty:
        # Dynamic case-insensitive extraction based on your raw schema
        consump_cols = [c for c in energy_df.columns if 'consump. v' in c.lower()]
        
        dunkin_col = next((c for c in energy_df.columns if 'dunkin' in c.lower() and 'consum' in c.lower()), None)
        clc_col = next((c for c in energy_df.columns if 'clc' in c.lower() and 'consum' in c.lower()), None)
        bmc_col = next((c for c in energy_df.columns if 'bmc' in c.lower() and 'consum' in c.lower()), None)
        deep_col = next((c for c in energy_df.columns if 'deep' in c.lower() and 'consum' in c.lower()), None)
        
        eq_cols = [c for c in [dunkin_col, clc_col, bmc_col, deep_col] if c is not None]

        # Metric Displays
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: st.metric("Total Days Recorded", f"{len(energy_df)}")
        with c2: st.metric("Dunkin Net Variance", f"{energy_df[dunkin_col].sum() if dunkin_col else 0:,.1f}")
        with c3: st.metric("CLC Net Variance",    f"{energy_df[clc_col].sum() if clc_col else 0:,.1f}")
        with c4: st.metric("BMC Net Variance",    f"{energy_df[bmc_col].sum() if bmc_col else 0:,.1f}")
        with c5: st.metric("Deep Net Variance",   f"{energy_df[deep_col].sum() if deep_col else 0:,.1f}")

        # Charts render directly with index as continuous timeline
        if consump_cols:
            st.markdown('<div class="sec-title">Daily Delta Consumption Profile — V1 to V9 (June 1 - June 10)</div>', unsafe_allow_html=True)
            st.line_chart(energy_df[consump_cols])

        if eq_cols:
            st.markdown('<div class="sec-title">Calculated Process Zone Loads (June 1 - June 10)</div>', unsafe_allow_html=True)
            st.bar_chart(energy_df[eq_cols])

        # Adjacent day difference lookbacks
        st.markdown('<div class="sec-title">Daily Process Zone Net Energy Consumed (Adjacent Day Differences)</div>', unsafe_allow_html=True)
        diff_energy = pd.DataFrame(index=energy_df.index)
        diff_cols = []
        for col in eq_cols:
            lbl = f"{col} Delta"
            diff_energy[lbl] = (energy_df[col] - energy_df[col].shift(-1)).fillna(0)
            diff_cols.append(lbl)
            
        if diff_cols:
            st.line_chart(diff_energy[diff_cols])
            
        st.markdown('<div class="sec-title">📥 Raw Data Inspector Portal</div>', unsafe_allow_html=True)
        st.dataframe(energy_df, use_container_width=True)
    else:
        st.markdown('<div class="alert-info">No matching processed energy dataset found between 1 June and 10 June 2026.</div>', unsafe_allow_html=True)
