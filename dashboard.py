import os
import glob
import warnings
import requests
import io
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

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

.sec-title { font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 1px; margin: 28px 0 12px 0; padding-bottom: 8px; border-bottom: 1px solid #E2E8F0; }
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

def fast_parse_dates(series):
    cleansed = series.astype(str).str.strip().str.split(' ').str[0]
    parsed_df = pd.to_datetime(cleansed, errors='coerce', format='%Y-%m-%d')
    if parsed_df.isna().all():
        parsed_df = pd.to_datetime(cleansed, errors='coerce', dayfirst=True)
    return parsed_df

# ─────────────────────────────────────────────────────────────
#  DATA LOADERS (ENERGY, TEMPERATURE, AND WORKBOOKS)
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
        df['DateIndex'] = pd.to_datetime(df[date_col], errors='coerce')
        
        if df['DateIndex'].isna().any():
            df.loc[df['DateIndex'].isna(), 'DateIndex'] = pd.to_datetime(df.loc[df['DateIndex'].isna(), date_col], errors='coerce', dayfirst=True)
            
        df = df.dropna(subset=['DateIndex'])
        df = df[(df['DateIndex'] >= '2026-06-01') & (df['DateIndex'] <= '2026-06-15')]
        df = df.sort_values('DateIndex').reset_index(drop=True)
        
        for col in df.columns:
            if col != 'DateIndex' and col != date_col:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        
        for i in range(1, 10):
            consump_col = f"consump. v{i}"
            reg_col = f"V{i}"
            if consump_col in df.columns and reg_col in df.columns:
                computed_diff = df[reg_col].diff()
                df[consump_col] = df.apply(
                    lambda row: computed_diff.loc[row.name] if (row[consump_col] == 0) and pd.notna(computed_diff.loc[row.name]) and computed_diff.loc[row.name] > 0 else row[consump_col],
                    axis=1
                )
        
        dunkin_c = 'dunkin consmp.'
        clc_c = 'clc consump.'
        bmc_c = 'bmc consump.'
        deep_c = 'deep consumption'
        
        if dunkin_c in df.columns:
            df[dunkin_c] = df.apply(lambda r: r['consump. v1'] + r['consump. v6'] if r[dunkin_c] == 0 else r[dunkin_c], axis=1)
        if clc_c in df.columns:
            df[clc_c] = df.apply(lambda r: r['consump. v3'] + r['consump. v8'] if r[clc_c] == 0 else r[clc_c], axis=1)
        if bmc_c in df.columns:
            df[bmc_c] = df.apply(lambda r: r['consump. v2'] + r['consump. v7'] if r[bmc_c] == 0 else r[bmc_c], axis=1)
        if deep_c in df.columns:
            df[deep_c] = df.apply(lambda r: r['consump. v4'] + r['consump. v5'] + r['consump. v9'] if r[deep_c] == 0 else r[deep_c], axis=1)

        return df
    except Exception as e:
        st.sidebar.error(f"Failed parsing processed energy file {name}: {e}")
        return None

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
#  GLOBAL ENVIRONMENT LOAD ROUTING
# ─────────────────────────────────────────────────────────────
e_df = load_processed_energy_data()

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
    st.markdown('<div style="font-size:9px; font-weight:700; color:#94A3B8; text-transform:uppercase;">GitHub Source Status</div>', unsafe_allow_html=True)

    st.markdown(f"""
        <div style="margin-top:8px; margin-bottom:8px;"><span class="status-pill status-{'ok' if processed_energy_files else 'err'}">Processed Energy · {'Active' if processed_energy_files else 'Missing'}</span></div>
        <div style="margin-bottom:8px;"><span class="status-pill status-{'ok' if csv_files else 'err'}">Temp Logs · {len(csv_files)} file(s)</span></div>
        <div><span class="status-pill status-{'ok' if has_freon else 'err'}">Freon Workbook · {'Found' if has_freon else 'Not Found'}</span></div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  HEADER SYSTEM
# ─────────────────────────────────────────────────────────────
date_range_str = "01 Jun 2026 – 15 Jun 2026" if e_df is not None and not e_df.empty else "No Data Loaded"

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
        consump_cols = [c for c in e_df.columns if 'consump. v' in c.lower()]
        dunkin_col = next((c for c in e_df.columns if 'dunkin consmp.' in c.lower()), None)
        clc_col = next((c for c in e_df.columns if 'clc consump.' in c.lower()), None)
        bmc_col = next((c for c in e_df.columns if 'bmc consump.' in c.lower()), None)
        deep_col = next((c for c in e_df.columns if 'deep consumption' in c.lower()), None)
        eq_cols = [c for c in [dunkin_col, clc_col, bmc_col, deep_col] if c is not None]

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: st.metric("Total Days Recorded", f"{len(e_df)}")
        with c2: st.metric("Dunkin Net Variance", f"{e_df[dunkin_col].sum() if dunkin_col else 0:,.1f}")
        with c3: st.metric("CLC Net Variance",    f"{e_df[clc_col].sum() if clc_col else 0:,.1f}")
        with c4: st.metric("BMC Net Variance",    f"{e_df[bmc_col].sum() if bmc_col else 0:,.1f}")
        with c5: st.metric("Deep Net Variance",   f"{e_df[deep_col].sum() if deep_col else 0:,.1f}")

        # ─────────────────────────────────────────────────────────────
        #  V1 TO V9 DAILY CHRONOLOGICAL PROFILE GRAPH (STRICT FORMATTING)
        # ─────────────────────────────────────────────────────────────
        if consump_cols:
            st.markdown('<div class="sec-title">Daily Delta Consumption Profile — V1 to V9 Channels (Strict 01 Jun - 15 Jun Window)</div>', unsafe_allow_html=True)
            
            fig_lines = go.Figure()
            x_categories = ["01-Jun", "02-Jun", "03-Jun", "04-Jun", "05-Jun", "06-Jun", "07-Jun", 
                            "08-Jun", "09-Jun", "10-Jun", "11-Jun", "12-Jun", "13-Jun", "14-Jun", "15-Jun"]
            
            temp_plot_df = e_df.copy()
            temp_plot_df['ChartLabel'] = temp_plot_df['DateIndex'].dt.strftime('%d-%b')
            temp_plot_df = temp_plot_df.set_index('ChartLabel').reindex(x_categories).fillna(0.0)
            
            for col in consump_cols:
                fig_lines.add_trace(go.Scatter(
                    x=x_categories,
                    y=temp_plot_df[col].tolist(),
                    mode='lines+markers',
                    name=col,
                    line=dict(width=2.5),
                    marker=dict(size=6)
                ))
                
            fig_lines.update_layout(
                hovermode="x unified",
                margin=dict(l=40, r=20, t=15, b=30),
                height=450,
                xaxis=dict(type='category', categoryarray=x_categories, gridcolor="#E2E8F0", fixedrange=True),
                yaxis=dict(fixedrange=True, gridcolor="#E2E8F0"),
                plot_bgcolor="#FFFFFF",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_lines, use_container_width=True)

        # ─────────────────────────────────────────────────────────────
        #  BAR CHARTS RENDER SECTION
        # ─────────────────────────────────────────────────────────────
        if eq_cols:
            st.markdown('<div class="sec-title">Daily Energy Consumption by Process Area</div>', unsafe_allow_html=True)
            energy_chart = e_df.copy()
            energy_chart["Date"] = energy_chart["DateIndex"].dt.strftime("%d-%b")

            fig_bar = go.Figure()
            if dunkin_col: fig_bar.add_trace(go.Bar(name="Dunkin", x=energy_chart["Date"], y=energy_chart[dunkin_col]))
            if clc_col: fig_bar.add_trace(go.Bar(name="CLC", x=energy_chart["Date"], y=energy_chart[clc_col]))
            if bmc_col: fig_bar.add_trace(go.Bar(name="BMC", x=energy_chart["Date"], y=energy_chart[bmc_col]))
            if deep_col: fig_bar.add_trace(go.Bar(name="Deep Freeze", x=energy_chart["Date"], y=energy_chart[deep_col]))

            fig_bar.update_layout(
                barmode="stack", height=500, xaxis_title="Date", yaxis_title="Energy Consumption (kWh)",
                hovermode="x unified", legend_title="Plant Area", margin=dict(l=40, r=20, t=20, b=40)
            )
            st.plotly_chart(fig_bar, use_container_width=True)

            st.markdown('<div class="sec-title">Calculated Process Zone Loads (Cumulative Distribution)</div>', unsafe_allow_html=True)
            bar_data = e_df.copy()
            bar_data['ChartDate'] = bar_data['DateIndex'].dt.strftime('%d-%b')
            st.bar_chart(bar_data.set_index('ChartDate')[eq_cols])
            
        with st.expander("📂 View Pre-Processed Active Energy File Data Table"):
            st.dataframe(e_df, use_container_width=True)
    else:
        st.markdown('<div class="alert-info">No active energy data captured matching the current file window constraints.</div>', unsafe_allow_html=True)

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
            st.metric("Thermal Compliance Index", f"{compliance:.1f}%")

        st.markdown('<div class="sec-title">Real-Time Temperature Stream</div>', unsafe_allow_html=True)
        st.line_chart(temp_df.set_index('Time')[sensors], color=["#002D62","#0EA5E9","#E01934"])
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
            st.markdown('<div class="sec-title">Daily Power Grid Footprint (kWh)</div>', unsafe_allow_html=True)
            st.area_chart(p.set_index('Date')[[dunkin_col, clc_col]], color=["#002D62","#FF9F1C"])

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
        
        if kwh_cols and not r.empty:
            for col in kwh_cols:
                r[col] = pd.to_numeric(r[col], errors='coerce').fillna(0)
            st.markdown('<div class="sec-title">Daily Asset Displacement Matrix (Normal Data Logs)</div>', unsafe_allow_html=True)
            st.bar_chart(r.set_index(fc)[kwh_cols[0]], color="#002D62")

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
            st.markdown('<div class="sec-title">Daily Rest Allocations (hrs)</div>', unsafe_allow_html=True)
            st.line_chart(c.set_index(c.columns[0])[sav_col], color="#002D62")
