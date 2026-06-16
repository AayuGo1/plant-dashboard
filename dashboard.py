import os
import glob
import warnings
import requests
import io
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
            df = read_excel_from_github(url)
            
        df = df[~df.iloc[:, 0].astype(str).str.contains(r'source|v1|Date|consump', case=False, na=False)]
        df.columns = [str(c).strip() for c in df.columns]
        
        date_col = next((c for c in df.columns if c.lower() in ['date', 'timestamp', 'time']), None)
        if not date_col:
            return None
            
        df[date_col] = df[date_col].astype(str).str.strip()
        df['DateIndex'] = pd.to_datetime(df[date_col], errors='coerce', format='%Y-%m-%d')
        
        if df['DateIndex'].isna().any():
            df.loc[df['DateIndex'].isna(), 'DateIndex'] = pd.to_datetime(df.loc[df['DateIndex'].isna(), date_col], errors='coerce')
            
        df = df.dropna(subset=['DateIndex'])
        df = df[(df['DateIndex'] >= '2026-06-01') & (df['DateIndex'] <= '2026-06-15')]
        df = df.sort_values('DateIndex').reset_index(drop=True)
        
        for col in df.columns:
            if col != 'DateIndex' and col != date_col:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        for i in range(1, 10):
            consump_col = f"consump. v{i}"
            reg_col = f"V{i}"
            
            if consump_col in df.columns and reg_col in df.columns:
                computed_diff = df[reg_col].diff()
                df[consump_col] = df.apply(
                    lambda row: computed_diff.loc[row.name] if (pd.isna(row[consump_col]) or row[consump_col] == 0) and pd.notna(computed_diff.loc[row.name]) and computed_diff.loc[row.name] > 0 else row[consump_col],
                    axis=1
                )
        
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
#  SIDEBAR STATUS INTEGRATION
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
# ==============================================================================
#  TAB 5 — COMPRESSOR DIAGNOSTICS ENGINE
# ==============================================================================
with tab_comp:
    if comp_df is not None and not comp_df.empty and temp_df is not None and not temp_df.empty:
        st.markdown('<div class="sec-title">🛠️ Advanced Production Diagnostic Engine</div>', unsafe_allow_html=True)
        
        # ─────────────────────────────────────────────────────────────
        # DATA PRE-PROCESSING & NORMALIZATION PIPELINE
        # ─────────────────────────────────────────────────────────────
        c_clean = comp_df.copy()
        c_clean = c_clean[~c_clean.iloc[:,0].astype(str).str.strip().str.lower().str.fullmatch(r'date|total|from|sr\.?\s*no\.?|stop|start', na=False)]
        c_clean.iloc[:,0] = pd.to_datetime(c_clean.iloc[:,0], errors='coerce')
        c_clean = c_clean.dropna(subset=[c_clean.columns[0]]).sort_values(c_clean.columns[0])
        
        sav_col = next((col for col in c_clean.columns if 'saving' in str(col).lower()), None)
        date_col = c_clean.columns[0]
        
        if sav_col:
            c_clean[sav_col] = pd.to_numeric(c_clean[sav_col], errors='coerce').fillna(0)
            c_clean['Cumulative Savings'] = c_clean[sav_col].cumsum()
            
            # Aggregate daily rest windows
            daily_compressor_rest = c_clean.groupby(c_clean[date_col].dt.date)[sav_col].sum().reset_index()
            daily_compressor_rest.columns = ['Date', 'Rest_Hours']
            daily_compressor_rest['Date'] = pd.to_datetime(daily_compressor_rest['Date'])
            
            # Dynamic Column Resolver to prevent KeyErrors
            t_clean = temp_df.copy()
            t_clean['Date'] = pd.to_datetime(t_clean['Time']).dt.date
            
            # Locate the exact string name for Dough Cooler 1 dynamically
            dough1_col = next((col for col in t_clean.columns if 'cooler1' in col.lower().replace(" ", "")), None)
            
            if dough1_col:
                daily_thermal = t_clean.groupby('Date').agg(
                    Mean_Dough1=(dough1_col, 'mean'),
                    Max_Dough1=(dough1_col, 'max'),
                    Min_Dough1=(dough1_col, 'min')
                ).reset_index()
                daily_thermal['Date'] = pd.to_datetime(daily_thermal['Date'])
                
                # Merge diagnostic vectors
                diagnostic_matrix = pd.merge(daily_compressor_rest, daily_thermal, on='Date', how='inner')
            else:
                st.warning("⚠️ Could not match 'Dough Cooler 1' column layout within temperature logs. Structural graphs are temporarily uncoupled.")
                diagnostic_matrix = pd.DataFrame() # Fallback safely to prevent crashing downstream
            
            # Metric Summary Strips
            k1, k2, k3, k4 = st.columns(4)
            with k1: st.metric("Relief Window Saved", f"{c_clean[sav_col].sum():,.1f} hrs")
            with k2: st.metric("Mean Daily Dampening", f"{c_clean[sav_col].mean():.1f} hrs")
            with k3: st.metric("Peak Single Window Stop", f"{c_clean[sav_col].max():.1f} hrs")
            with k4: st.metric("Audited Shift Blocks", f"{len(c_clean)}")
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
    "📉  Compressor Diagnostics Engine",
])

# ==============================================================================
#  TAB 1 — ACTIVE ENERGY METERS
# ==============================================================================
with tab_energy:
    if e_df is not None and not e_df.empty:
        consump_cols = [c for c in e_df.columns if 'consump. v' in c.lower()]
        
        dunkin_col = next((c for c in e_df.columns if 'dunkin consmp.' in c.lower()), None)
        clc_col = next((c for c in e_df.columns if 'clc consump.' in c.lower()), None)
        line_bmc_col = next((c for c in e_df.columns if 'bmc consump.' in c.lower()), None)
        deep_col = next((c for c in e_df.columns if 'deep consumption' in c.lower()), None)
        
        eq_cols = [c for c in [dunkin_col, clc_col, line_bmc_col, deep_col] if c is not None]

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: st.metric("Total Days Recorded", f"{len(e_df)}")
        with c2: st.metric("Dunkin Net Variance", f"{e_df[dunkin_col].sum() if dunkin_col else 0:,.1f}")
        with c3: st.metric("CLC Net Variance",    f"{e_df[clc_col].sum() if clc_col else 0:,.1f}")
        with c4: st.metric("BMC Net Variance",    f"{e_df[line_bmc_col].sum() if line_bmc_col else 0:,.1f}")
        with c5: st.metric("Deep Net Variance",   f"{e_df[deep_col].sum() if deep_col else 0:,.1f}")

        if consump_cols:
            st.markdown('<div class="sec-title">Daily Delta Consumption Profile — V1 to V9 Channels (Strict 01 Jun - 15 Jun Window)</div>', unsafe_allow_html=True)
            
            fig = go.Figure()
            x_dates = e_df['DateIndex'].dt.strftime('%d-%b').tolist()
            
            for col in consump_cols:
                fig.add_trace(go.Scatter(
                    x=x_dates,
                    y=e_df[col].tolist(),
                    mode='lines+markers',
                    name=col,
                    line=dict(width=2.5),
                    marker=dict(size=5)
                ))
                
            fig.update_layout(
                hovermode="x unified",
                margin=dict(l=20, r=20, t=20, b=20),
                height=420,
                xaxis=dict(type='category', tickmode='array', tickvals=x_dates, fixedrange=True),
                yaxis=dict(fixedrange=True),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)

        if eq_cols:
            st.markdown('<div class="sec-title">Calculated Process Zone Loads (Cumulative Distribution)</div>', unsafe_allow_html=True)
            bar_data = e_df[['DateIndex'] + eq_cols].copy()
            bar_data['ChartDate'] = bar_data['DateIndex'].dt.strftime('%d-%b')
            st.bar_chart(bar_data.set_index('ChartDate').drop(columns=['DateIndex']))

        st.markdown('<div class="sec-title">Daily Process Zone Net Energy Consumed (Chronological Progress Delta)</div>', unsafe_allow_html=True)
        
        diff_energy = pd.DataFrame()
        diff_energy['ChartDate'] = e_df['DateIndex'].dt.strftime('%d-%b')
        diff_cols = []
        for col in eq_cols:
            col_label = f"{col} Delta"
            diff_energy[col_label] = (e_df[col] - e_df[col].shift(1)).fillna(0).values
            diff_cols.append(col_label)
        
        target_energy_row = diff_energy.iloc[-1] if not diff_energy.empty else None
        
        ec1, ec2, ec3, ec4 = st.columns(4)
        with ec1:
            val = target_energy_row.get(f"{dunkin_col} Delta", 0) if (target_energy_row is not None and dunkin_col) else 0
            st.markdown(f'<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:6px; padding:10px 16px; border-left:4px solid #002D62;"><div style="font-size:9px; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px;">Dunkin Consumption Delta</div><div style="font-size:16px; font-weight:800; color:#002D62; margin-top:2px;">{val:,.1f} kWh</div></div>', unsafe_allow_html=True)
        with ec2:
            val = target_energy_row.get(f"{clc_col} Delta", 0) if (target_energy_row is not None and clc_col) else 0
            st.markdown(f'<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:6px; padding:10px 16px; border-left:4px solid #FF9F1C;"><div style="font-size:9px; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px;">CLC Consumption Delta</div><div style="font-size:16px; font-weight:800; color:#002D62; margin-top:2px;">{val:,.1f} kWh</div></div>', unsafe_allow_html=True)
        with ec3:
            val = target_energy_row.get(f"{line_bmc_col} Delta", 0) if (target_energy_row is not None and line_bmc_col) else 0
            st.markdown(f'<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:6px; padding:10px 16px; border-left:4px solid #16A34A;"><div style="font-size:9px; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px;">BMC Consumption Delta</div><div style="font-size:16px; font-weight:800; color:#002D62; margin-top:2px;">{val:,.1f} kWh</div></div>', unsafe_allow_html=True)
        with ec4:
            val = target_energy_row.get(f"{deep_col} Delta", 0) if (target_energy_row is not None and deep_col) else 0
            st.markdown(f'<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:6px; padding:10px 16px; border-left:4px solid #E01934;"><div style="font-size:9px; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px;">Deep Consumption Delta</div><div style="font-size:16px; font-weight:800; color:#002D62; margin-top:2px;">{val:,.1f} kWh</div></div>', unsafe_allow_html=True)

        if diff_cols:
            st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
            st.line_chart(diff_energy.set_index('ChartDate')[diff_cols])

        st.markdown('<div class="sec-title">📥 Raw Data Inspector Portal</div>', unsafe_allow_html=True)
        with st.expander("📂 View Pre-Processed Active Energy File Data Table", expanded=False):
            st.dataframe(e_df.set_index('DateIndex'), use_container_width=True)
    else:
        st.markdown('<div class="alert-info"><strong>No active energy data captured matching the current file window constraints.</strong></div>', unsafe_allow_html=True)

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
            st.metric("Thermal Compliance Index", f"{compliance:.1f}%", delta=f"{total_exc} critical violations", delta_color="inverse")

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
            st.markdown(f'<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:6px; padding:10px 16px; border-left:4px solid #002D62;"><div style="font-size:9px; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px;">Dough 1 Delta Variance Sum</div><div style="font-size:16px; font-weight:800; color:#002D62; margin-top:2px;">{d1_sum:,.2f} °C</div></div>', unsafe_allow_html=True)
        with sc2:
            st.markdown(f'<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:6px; padding:10px 16px; border-left:4px solid #0EA5E9;"><div style="font-size:9px; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px;">Dough 2 Delta Variance Sum</div><div style="font-size:16px; font-weight:800; color:#002D62; margin-top:2px;">{d2_sum:,.2f} °C</div></div>', unsafe_allow_html=True)
        with sc3:
            st.markdown(f'<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:6px; padding:10px 16px; border-left:4px solid #E01934;"><div style="font-size:9px; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px;">Perishable Delta Variance Sum</div><div style="font-size:16px; font-weight:800; color:#002D62; margin-top:2px;">{p_sum:,.2f} °C</div></div>', unsafe_allow_html=True)
        
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
            st.download_button(label="Download Compiled Temperature Data as CSV", data=csv_data, file_name="compiled_temperature_logs.csv", mime="text/csv", key="btn_download_temp")
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
                    st.download_button(label="Download Sheet1 Cost Data as CSV", data=csv_data, file_name="freon_sheet1_energy_savings.csv", mime="text/csv", key="btn_download_power")
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
                st.markdown(f'<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:6px; padding:10px 16px; border-left:4px solid #002D62;"><div style="font-size:9px; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px;">Energy Drew</div><div style="font-size:16px; font-weight:800; color:#002D62; margin-top:2px;">{val:,.1f} kWh</div></div>', unsafe_allow_html=True)
            with rc2:
                val = target_day['Peak System Load Vector (kWh)'] if target_day is not None else 0
                st.markdown(f'<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:6px; padding:10px 16px; border-left:4px solid #FF9F1C;"><div style="font-size:9px; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px;">Peak System Load Vector</div><div style="font-size:16px; font-weight:800; color:#002D62; margin-top:2px;">{val:,.1f} kWh</div></div>', unsafe_allow_html=True)
            with rc3:
                val = target_day['Mean Load Vector (kWh)'] if target_day is not None else 0
                st.markdown(f'<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:6px; padding:10px 16px; border-left:4px solid #E01934;"><div style="font-size:9px; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px;">Mean Load Vector</div><div style="font-size:16px; font-weight:800; color:#002D62; margin-top:2px;">{val:,.1f} kWh</div></div>', unsafe_allow_html=True)

            st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
            st.line_chart(daily_runtime.set_index('Date')
