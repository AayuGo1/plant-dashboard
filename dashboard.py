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
    """Returns list of (filename, download_url) from the GitHub folder."""
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
#  METER COLUMNS DEFINITION
# ─────────────────────────────────────────────────────────────
METER_COLS = {
    'V1': 'V1 - DUNKIN BLAST',
    'V2': 'V2 - BMC BLAST',
    'V3': 'V3 - CLC BLAST',
    'V4': 'V4 - DEEP1 BLAST',
    'V5': 'V5 - DEEP2 BLAST',
    'V6': 'V6 - DUNKIN RACK',
    'V7': 'V7 - BMC RACK',
    'V8': 'V8 - CLC RACK',
    'V9': 'V9 - DEEP RACK',
}

# ─────────────────────────────────────────────────────────────
#  ACTIVE ENERGY PROCESSOR
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_and_process_energy_files():
    all_files = list_github_files()
    
    # 1. Look for pre-processed final energy files first
    processed_files = [
        (name, url) for name, url in all_files
        if (name.startswith("PROCESSED_DAILY_VARS_Active_Energy_Report") or "PROCESSED" in name.upper())
        and (name.endswith(".xlsx") or name.endswith(".csv"))
    ]
    
    if processed_files:
        name, url = sorted(processed_files)[-1]
        try:
            if name.endswith(".csv"):
                df = read_csv_from_github(url)
            else:
                df = read_excel_from_github(url)
                
            df.columns = [str(c).strip() for c in df.columns]
            date_col = next((c for c in df.columns if c.lower() in ['date', 'timestamp', 'time']), None)
            
            if date_col:
                df['Date'] = pd.to_datetime(df[date_col], errors='coerce').dt.date
                df = df.dropna(subset=['Date']).sort_values('Date').reset_index(drop=True)
                
                # Coerce data columns to numeric format
                for col in df.columns:
                    if col != 'Date':
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                return df
        except Exception as e:
            st.sidebar.warning(f"Error reading processed file {name}, falling back to raw: {e}")

    # 2. Fallback execution: Load and compute raw individual files if no pre-processed data exists
    energy_files = [
        (name, url) for name, url in all_files
        if name.startswith("Active_Energy_Report") and (name.endswith(".xlsx") or name.endswith(".csv"))
        and not name.startswith("PROCESSED_")
    ]

    frames = []

    if energy_files:
        for name, url in sorted(energy_files):
            try:
                if name.endswith(".csv"):
                    df = read_csv_from_github(url)
                else:
                    df = read_excel_from_github(url)
                    
                df.columns = [str(c).strip() for c in df.columns]

                date_candidate = next((c for c in df.columns if c in ['Timestamp', 'Date', 'time', 'date']), None)
                if not date_candidate:
                    continue

                df['Parsed_Date'] = pd.to_datetime(df[date_candidate], errors='coerce').dt.date
                df = df.dropna(subset=['Parsed_Date'])
                df = df.rename(columns={'Parsed_Date': 'Date'})
                
                rename_dict = {}
                for col in df.columns:
                    col_clean = str(col).upper().replace(" ", "").replace("-", "")
                    for k, v in METER_COLS.items():
                        if col_clean.startswith(k):
                            rename_dict[col] = v
                            break
                df = df.rename(columns=rename_dict)
                frames.append(df)
            except Exception as e:
                st.warning(f"Skipped parsing energy report file {name}: {e}")
    else:
        freon_url = next((u for n, u in all_files if n == "Power consumption freon.xlsx"), None)
        if freon_url:
            try:
                xl = pd.ExcelFile(io.BytesIO(fetch_file_bytes(freon_url)), engine='openpyxl')
                for sheet in xl.sheet_names:
                    df = xl.parse(sheet)
                    df.columns = [str(c).strip() for c in df.columns]
                    
                    has_date = any(c in df.columns for c in ['Timestamp', 'Date', 'time', 'date'])
                    has_meters = any(col in df.columns for col in METER_COLS.values())
                    
                    if has_date or has_meters:
                        date_col = next((c for c in df.columns if c in ['Timestamp', 'Date', 'time', 'date']), df.columns[0])
                        df['Date'] = pd.to_datetime(df[date_col], errors='coerce').dt.date
                        df = df.dropna(subset=['Date'])
                        frames.append(df)
                        break
            except Exception as e:
                st.sidebar.error(f"Failed handling workbook layout mapping logic: {e}")

    if not frames:
        return None

    combined_raw = pd.concat(frames, ignore_index=True)

    for col in METER_COLS.values():
        if col not in combined_raw.columns:
            combined_raw[col] = float('nan')
        else:
            combined_raw[col] = pd.to_numeric(combined_raw[col], errors='coerce')

    combined = (
        combined_raw.groupby('Date')[list(METER_COLS.values())]
        .mean()
        .reset_index()
        .sort_values('Date')
        .reset_index(drop=True)
    )

    if combined.empty:
        return None

    for i in range(1, 10):
        col = METER_COLS[f'V{i}']
        combined[f'consump. v{i}'] = (combined[col] - combined[col].shift(1)).fillna(0)

    v = lambda n: combined[f'consump. v{n}']
    combined['dunkin consmp.']   = 1250 - (v(1) + v(6))
    combined['clc consump.']     = 1450 - (v(3) + v(8))
    combined['bmc consump.']     = 1250 - (v(2) + v(7))
    combined['deep consumption'] = 2200 - (v(4) + v(5) + v(9))

    return combined

# ─────────────────────────────────────────────────────────────
#  TEMPERATURE DATA LOADER (ADAPTIVE HEADER FIX)
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

    return (
        pd.concat(frames, ignore_index=True)
        .dropna(subset=['Time'])
        .drop_duplicates(subset=['Time'])
        .sort_values('Time')
        .reset_index(drop=True)
    )

# ─────────────────────────────────────────────────────────────
#  EXCEL SHEET LOADER
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_excel_sheet(sheet_name, fallback_header_row):
    all_files = list_github_files()
    match = next((u for n, u in all_files if n == "Power consumption freon.xlsx"), None)
    if not match:
        return None
    try:
        preview = read_excel_from_github(match, sheet_name=sheet_name, header=None, engine='openpyxl')
        hdr = fallback_header_row
        for i in range(min(10, len(preview))):
            row = [str(x).lower() for x in preview.iloc[i].dropna()]
            if any('date' in x or 'stop time' in x for x in row):
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

def fast_parse_dates(series):
    return pd.to_datetime(
        series.astype(str).str.strip().str.split(' ').str[0],
        errors='coerce', dayfirst=True
    )

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

    st.markdown("<hr style='border-color:#1E3A8A; margin:8px 0 16px;'>", unsafe_allow_html=True)

    if st.button("🔄 Refresh Data Now"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("""<div style="font-size:9px; font-weight:700; letter-spacing:1.2px; color:#94A3B8;
                    text-transform:uppercase; margin:12px 0 6px;">Auto-refresh every 5 min</div>""", unsafe_allow_html=True)

    all_files = list_github_files()
    energy_files = [n for n, _ in all_files if n.startswith("Active_Energy_Report")]
    processed_energy_files = [n for n, _ in all_files if n.startswith("PROCESSED_DAILY_VARS_Active_Energy_Report") or "PROCESSED" in n.upper()]
    csv_files    = [n for n, _ in all_files if n.startswith("DataLog_") and n.endswith(".csv")]
    has_freon    = any(n == "Power consumption freon.xlsx" for n, _ in all_files)

    st.markdown("<hr style='border-color:#1E3A8A; margin:14px 0;'>", unsafe_allow_html=True)
    st.markdown("""<div style="font-size:9px; font-weight:700; letter-spacing:1.2px;
                    color:#94A3B8; text-transform:uppercase; margin-bottom:10px;">
                    GitHub Source Status</div>""", unsafe_allow_html=True)

    # Dynamic status pill to indicate raw or pre-processed pipeline status
    status_color = "ok" if (energy_files or processed_energy_files) else "err"
    status_label = "Processed File" if processed_energy_files else f"Raw Stream · {len(energy_files)} file(s)"
    st.markdown(f"""
        <div style="margin-bottom:8px;">
            <span class="status-pill status-{status_color}">
                {'●' if (energy_files or processed_energy_files) else '○'}&nbsp; Energy Storage · {status_label}
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

    st.markdown("""
        <div style="position:fixed; bottom:18px; left:0; width:238px; text-align:center;
                    font-size:10px; color:#94A3B8; font-weight:600; padding:0 8px;">
            JFL Internal Operations Tool &nbsp;·&nbsp; v3.1
        </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  HEADER SYSTEM
# ─────────────────────────────────────────────────────────────
energy_df = load_and_process_energy_files()
date_range_str = "No data available"
if energy_df is not None and not energy_df.empty:
    d_min = pd.to_datetime(energy_df['Date'].min()).strftime("%d %b %Y")
    d_max = pd.to_datetime(energy_df['Date'].max()).strftime("%d %b %Y")
    date_range_str = f"{d_min} – {d_max}"

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
    if energy_df is not None and not energy_df.empty:
        e = energy_df.copy()
        e['Date'] = pd.to_datetime(e['Date'])

        consump_cols = [f'consump. v{i}' for i in range(1, 10) if f'consump. v{i}' in e.columns]
        eq_cols = [c for c in ['dunkin consmp.', 'clc consump.', 'bmc consump.', 'deep consumption'] if c in e.columns]

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Total Days Recorded", f"{len(e)}")
        with c2: st.metric("Dunkin Net Variance", f"{e['dunkin consmp.'].sum() if 'dunkin consmp.' in e else 0:,.1f}")
        with c3: st.metric("CLC Net Variance",    f"{e['clc consump.'].sum() if 'clc consump.' in e else 0:,.1f}")
        with c4: st.metric("Deep Net Variance",   f"{e['deep consumption'].sum() if 'deep consumption' in e else 0:,.1f}")

        if consump_cols:
            st.markdown('<div class="sec-title">Daily Delta Consumption Profile — V1 to V9</div>', unsafe_allow_html=True)
            st.line_chart(e.set_index('Date')[consump_cols])
            with st.expander("🔎 View Delta Consumption (V1-V9) Dataset", expanded=False):
                st.dataframe(e[['Date'] + consump_cols], use_container_width=True, hide_index=True)

        if eq_cols:
            st.markdown('<div class="sec-title">Calculated Process Zone Loads (Dunkin / CLC / BMC / Deep)</div>', unsafe_allow_html=True)
            st.bar_chart(e.set_index('Date')[eq_cols])
            with st.expander("🔎 View Calculated Process Zone Loads Dataset", expanded=False):
                st.dataframe(e[['Date'] + eq_cols], use_container_width=True, hide_index=True)

        st.markdown('<div class="sec-title">Full Daily Aggregated Execution Sheet</div>', unsafe_allow_html=True)
        display_cols = ['Date'] + [col for col in METER_COLS.values() if col in e.columns] + consump_cols + eq_cols
        st.dataframe(e[display_cols], use_container_width=True, hide_index=True)

        # ─── SECTION BOTTOM: RAW DATA INSPECTOR & EXPORT ───
        st.markdown('<div class="sec-title">📥 Raw Data Inspector & Export Portal</div>', unsafe_allow_html=True)
        with st.expander("📂 View & Download Compiled Active Energy Raw File Data", expanded=False):
            st.dataframe(e, use_container_width=True)
            csv_data = e.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Compiled Energy Data as CSV",
                data=csv_data,
                file_name="compiled_active_energy_meters.csv",
                mime="text/csv"
            )
    else:
        st.markdown('<div class="alert-info"><strong>No Active Energy data metrics compiled.</strong> Check file stream synchronization properties.</div>', unsafe_allow_html=True)

# ==============================================================================
#  TAB 2 — COLD STORAGE TEMPERATURES
# ==============================================================================
with tab_temp:
    temp_df = load_temperature_data()
    if temp_df is not None and not temp_df.empty:
        latest  = temp_df.iloc[-1]
        sensors = ['Dough Cooler1 Temp', 'Dough Cooler2 Temp', 'Perishable Cooler Temp']
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
        with st.expander("🔎 View Real-Time Temperature Stream Log Sheet", expanded=False):
            st.dataframe(temp_df[['Time'] + sensors], use_container_width=True, hide_index=True)

        st.markdown('<div class="sec-title">Daily Mean Thermal Signature</div>', unsafe_allow_html=True)
        temp_df['Date'] = temp_df['Time'].dt.date
        daily_avg = temp_df.groupby('Date')[sensors].mean().round(2)
        daily_avg.index = daily_avg.index.astype(str)
        st.bar_chart(daily_avg, color=["#002D62","#0EA5E9","#E01934"])
        with st.expander("🔎 View Daily Mean Thermal Metrics Table", expanded=False):
            st.dataframe(daily_avg.reset_index(), use_container_width=True, hide_index=True)

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

        # ─── SECTION BOTTOM: RAW DATA INSPECTOR & EXPORT ───
        st.markdown('<div class="sec-title">📥 Raw Data Inspector & Export Portal</div>', unsafe_allow_html=True)
        with st.expander("📂 View & Download Compiled Temperature Log Raw File Data", expanded=False):
            st.dataframe(temp_df, use_container_width=True)
            csv_data = temp_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Compiled Temperature Data as CSV",
                data=csv_data,
                file_name="compiled_temperature_logs.csv",
                mime="text/csv"
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
                with st.expander("🔎 View Power Grid Footprint Dataset", expanded=False):
                    st.dataframe(p[['Date', dunkin_col, clc_col]], use_container_width=True, hide_index=True)
                
                if savings_col:
                    st.markdown('<div class="sec-title">Daily Recovery Realized (₹)</div>', unsafe_allow_html=True)
                    st.bar_chart(p.set_index('Date')[savings_col], color="#16A34A")
                    with st.expander("🔎 View Daily Cost Recovery Savings Dataset", expanded=False):
                        st.dataframe(p[['Date', savings_col]], use_container_width=True, hide_index=True)

                # ─── SECTION BOTTOM: RAW DATA INSPECTOR & EXPORT ───
                st.markdown('<div class="sec-title">📥 Raw Data Inspector & Export Portal</div>', unsafe_allow_html=True)
                with st.expander("📂 View & Download Energy & Cost Savings Raw Sheet Data", expanded=False):
                    st.dataframe(p, use_container_width=True)
                    csv_data = p.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download Sheet1 Cost Data as CSV",
                        data=csv_data,
                        file_name="freon_sheet1_energy_savings.csv",
                        mime="text/csv"
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

            st.markdown('<div class="sec-title">Daily Asset Displacement Matrix</div>', unsafe_allow_html=True)
            st.bar_chart(r.set_index(fc)[kwh_cols[0]], color="#002D62")
            with st.expander("🔎 View Asset Displacement Log Metrics", expanded=False):
                st.dataframe(r[[fc, kwh_cols[0]]], use_container_width=True, hide_index=True)

            # ─── SECTION BOTTOM: RAW DATA INSPECTOR & EXPORT ───
            st.markdown('<div class="sec-title">📥 Raw Data Inspector & Export Portal</div>', unsafe_allow_html=True)
            with st.expander("📂 View & Download Asset Duty Cycle Raw Sheet Data", expanded=False):
                st.dataframe(r, use_container_width=True)
                csv_data = r.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Sheet2 Duty Cycles as CSV",
                    data=csv_data,
                    file_name="freon_sheet2_asset_duty_cycles.csv",
                    mime="text/csv"
                )
    else:
        st.markdown('<div class="alert-info">Asset duty-cycle log metrics are not active.</div>', unsafe_allow_html=True)

# ==============================================================================
#  TAB 5 — COMPRESSOR OPTIMISATION
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
                with st.expander("🔎 View Daily Rest Time Dataset", expanded=False):
                    st.dataframe(c[[date_col, sav_col]], use_container_width=True, hide_index=True)
            with col2:
                st.markdown('<div class="sec-title">Cumulative Rest Curve Metrics</div>', unsafe_allow_html=True)
                st.area_chart(c.set_index(date_col)['Cumulative Savings'], color="#FF9F1C")
                with st.expander("🔎 View Cumulative Savings Dataset", expanded=False):
                    st.dataframe(c[[date_col, 'Cumulative Savings']], use_container_width=True, hide_index=True)

            st.markdown('<div class="sec-title">Compressor Structural Load Activation Cycles</div>', unsafe_allow_html=True)
            comp_metrics = {}
            
            run_cols = [col for col in c.columns if any(phrase in str(col).lower() for phrase in ['stop', 'start', 'run', 'comp'])]
            
            for idx, col_name in enumerate(run_cols[:5], 1):
                active_logs = c[c[col_name].astype(str).str.strip().str.len() > 0]
                comp_metrics[f"Compressor Component {idx}"] = len(active_logs)
                
            if comp_metrics:
                cm_df = pd.DataFrame(list(comp_metrics.items()), columns=["Component", "Cycle Count"]).sort_values("Cycle Count", ascending=False)
                st.bar_chart(cm_df.set_index("Component")["Cycle Count"], color="#E01934")
                with st.expander("🔎 View Component Structural Activation Counts", expanded=False):
                    st.dataframe(cm_df, use_container_width=True, hide_index=True)

            # ─── SECTION BOTTOM: RAW DATA INSPECTOR & EXPORT ───
            st.markdown('<div class="sec-title">📥 Raw Data Inspector & Export Portal</div>', unsafe_allow_html=True)
            with st.expander("📂 View & Download Compressor Optimization Raw Sheet Data", expanded=False):
                st.dataframe(c, use_container_width=True)
                csv_data = c.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Sheet3 Optimisation Data as CSV",
                    data=csv_data,
                    file_name="freon_sheet3_compressor_optimization.csv",
                    mime="text/csv"
                )
    else:
        st.markdown('<div class="alert-info">Compressor analytical tracking components not parsed.</div>', unsafe_allow_html=True)
