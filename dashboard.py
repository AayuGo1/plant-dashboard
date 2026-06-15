import streamlit as st
import pandas as pd
import glob
import os
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

# ─────────────────────────────────────────────
#  CORPORATE PAGE CONFIGURATION
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Jubilant FoodWorks - Plant Operational Intelligence Hub",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
#  ENTERPRISE CORE UI STYLE RESETS
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ── Corporate Typography & Canvas ── */
html, body, [class*="css"] { font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif; }
.block-container { padding: 1.5rem 2.5rem 3rem; background: #F8FAFC; }

/* ── Branded Left Navigation Sidebar ── */
section[data-testid="stSidebar"] {
    background: #002D62 !important; /* JFL Corporate Deep Navy Primary */
    border-right: 1px solid #E2E8F0 !important;
}
section[data-testid="stSidebar"] * { color: #E2E8F0 !important; }
section[data-testid="stSidebar"] input {
    background: #001F4D !important;
    border: 1px solid #1E3A8A !important;
    color: #FFFFFF !important;
    border-radius: 4px !important;
}
section[data-testid="stSidebar"] label {
    color: #94A3B8 !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.8px !important;
}

/* ── Professional Executive Tab Strip ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #FFFFFF;
    border-bottom: 2px solid #E2E8F0;
    padding: 6px 6px 0 6px;
    border-radius: 6px 6px 0 0;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    border: none;
    border-bottom: 3px solid transparent;
    padding: 12px 24px;
    font-size: 13px;
    font-weight: 700;
    color: #475569;
    letter-spacing: 0.3px;
    transition: all 0.2s ease;
}
.stTabs [data-baseweb="tab"]:hover { color: #E01934; background: #FFF5F5; }
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    color: #002D62 !important;
    border-bottom: 3px solid #E01934 !important; /* JFL Brand Crimson Accent Line */
    background: transparent !important;
}

/* ── High-Contrast KPI Summary Blocks ── */
div[data-testid="stMetric"] {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 6px !important;
    padding: 22px 24px !important;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02), 0 2px 4px -1px rgba(0,0,0,0.01) !important;
    border-left: 5px solid #002D62 !important;
}
div[data-testid="stMetricLabel"] p {
    color: #475569 !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
}
div[data-testid="stMetricValue"] div {
    color: #0F172A !important;
    font-size: 30px !important;
    font-weight: 800 !important;
    letter-spacing: -0.5px !important;
}

/* ── Section Display Elements ── */
.section-card {
    background: #FFFFFF;
    border-radius: 6px;
    padding: 24px;
    margin-bottom: 18px;
    border: 1px solid #E2E8F0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.02);
}
.section-title {
    font-size: 13px;
    font-weight: 700;
    color: #002D62;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 24px 0 14px 0;
    padding-bottom: 10px;
    border-bottom: 2px solid #EEF2F6;
}

/* ── Pipeline Connection Badges ── */
.status-pill {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
}
.status-ok   { background: #D1FAE5; color: #065F46; border: 1px solid #A7F3D0; }
.status-err  { background: #FEE2E2; color: #991B1B; border: 1px solid #FCA5A5; }

/* ── Clean Data Tables ── */
.stDataFrame { border-radius: 6px; overflow: hidden; border: 1px solid #E2E8F0; }
hr { border: none; border-top: 1px solid #E2E8F0; margin: 20px 0; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  SIDEBAR MANAGEMENT CONTROLS
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style="padding:15px 0 20px;">
            <div style="font-size:10px; font-weight:700; letter-spacing:1.5px; color:#94A3B8; text-transform:uppercase; margin-bottom:4px;">
                JUBILANT FOODWORKS LIMITED
            </div>
            <div style="font-size:18px; font-weight:800; color:#FFFFFF; line-height:1.2; letter-spacing:-0.3px;">
                Cold Chain Network<br>Control Center
            </div>
            <div style="margin-top:10px; width:40px; height:4px; background:#E01934; border-radius:2px;"></div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""<div style="font-size:10px; font-weight:700; letter-spacing:1px; color:#94A3B8; text-transform:uppercase; margin-bottom:12px;">
                    Local Node Configuration</div>""", unsafe_allow_html=True)

    user_name = st.text_input("Windows User Profile", value="aayush")
    company_folder = st.text_input("OneDrive Root Name", value="OneDrive")

    ONEDRIVE_PATH = f"C:/Users/{user_name}/{company_folder}/PlantData/"
    LOCAL_PATH = "./"

    st.markdown("---")

# ─────────────────────────────────────────────
#  AUTOMATED PIPELINE PATH RESOLVER
# ─────────────────────────────────────────────
def resolve_file(filename, is_pattern=False):
    if is_pattern:
        nodes = glob.glob(os.path.join(ONEDRIVE_PATH, filename))
        if nodes: return nodes, "OneDrive"
        nodes = glob.glob(os.path.join(LOCAL_PATH, filename))
        return nodes, ("Local Node" if nodes else None)
    cloud = os.path.join(ONEDRIVE_PATH, filename)
    if os.path.exists(cloud): return cloud, "OneDrive"
    return os.path.join(LOCAL_PATH, filename), "Local Node"

# Evaluate Live Connection Infrastructure
csv_files, csv_src = resolve_file("DataLog_*.csv", is_pattern=True)
xlsx_path, xlsx_src = resolve_file("Power consumption freon.xlsx")
xlsx_ok = os.path.exists(xlsx_path)

with st.sidebar:
    st.markdown("""<div style="font-size:10px; font-weight:700; letter-spacing:1px; color:#94A3B8; text-transform:uppercase; margin-bottom:12px;">
                    Data Pipeline Integrity Monitor</div>""", unsafe_allow_html=True)

    csv_status = ("ok" if csv_files else "err")
    xlsx_status = ("ok" if xlsx_ok else "err")

    csv_label = f"Thermal Telemetry Logs · {csv_src}" if csv_files else "Thermal Telemetry Logs · Offline"
    xlsx_label = f"Infrastructure Energy Workbook · {xlsx_src}" if xlsx_ok else "Infrastructure Energy Workbook · Missing"

    st.markdown(f"""
        <div style="margin-bottom:10px;">
            <span class="status-pill status-{csv_status}">
                {'● ' if csv_files else '○ '}{csv_label}
            </span>
        </div>
        <div>
            <span class="status-pill status-{xlsx_status}">
                {'● ' if xlsx_ok else '○ '}{xlsx_label}
            </span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style="position:fixed; bottom:20px; left:0; width:244px; text-align:center; font-size:10px; color:#64748B; font-weight:600; letter-spacing:0.5px;">
            JFL Supply Chain Operations Matrix · v2.2
        </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  HIGH-SPEED DATA INGESTION ENGINE
# ─────────────────────────────────────────────
def fast_parse_dates(series):
    return pd.to_datetime(
        series.astype(str).str.strip().str.split(' ').str[0],
        errors='coerce', dayfirst=True
    )

@st.cache_data
def load_temperature_data():
    files, _ = resolve_file("DataLog_*.csv", is_pattern=True)
    if not files: return None
    cols = ['Time', 'Dough Cooler2 Temp', 'Dough Cooler1 Temp', 'Perishable Cooler Temp']
    frames = []
    for f in files:
        df = pd.read_csv(f)
        df.columns = df.columns.str.strip()
        if all(c in df.columns for c in cols):
            sub = df[cols].copy()
            for c in cols[1:]:
                if sub[c].dtype == object:
                    sub[c] = sub[c].astype(str).str.replace(r'.*NOP.*', '0', regex=True)
                sub[c] = pd.to_numeric(sub[c], errors='coerce').ffill().bfill()
            sub['Time'] = pd.to_datetime(sub['Time'], dayfirst=True, errors='coerce')
            frames.append(sub)
    if not frames: return None
    return (pd.concat(frames, ignore_index=True)
              .drop_duplicates(subset=['Time'])
              .sort_values('Time'))

@st.cache_data
def load_excel_sheet(sheet_name, fallback_header_row):
    path, _ = resolve_file('Power consumption freon.xlsx')
    if not os.path.exists(path): return None
    try:
        preview = pd.read_excel(path, sheet_name=sheet_name, header=None, engine='openpyxl')
        hdr = fallback_header_row
        for i in range(min(10, len(preview))):
            row = [str(x).lower() for x in preview.iloc[i].dropna()]
            if any('date' in x or 'stop time' in x for x in row):
                hdr = i; break
        df = pd.read_excel(path, sheet_name=sheet_name, header=hdr, engine='openpyxl')
        df = df.dropna(axis=1, how='all')
        
        # Self-Repairing Header Mapping for Compressor Logs
        if sheet_name == 'Sheet3' or str(sheet_name).lower() == 'sheet3':
            if len(df.columns) >= 12:
                df.columns.values[11] = 'Saving in hrs'
            else:
                last_col = df.columns[-1]
                if 'unnamed' in str(last_col).lower():
                    df = df.rename(columns={last_col: 'Saving in hrs'})
                    
        if not df.empty:
            fc = df.columns[0]
            df = df[df[fc].astype(str).str.strip().str.lower() != 'total']
        return df
    except Exception:
        return None


# ─────────────────────────────────────────────
#  CORPORATE BANNER COHORT
# ─────────────────────────────────────────────
st.markdown("""
<div style="display:flex; align-items:center; justify-content:space-between;
            background:#FFFFFF; border-radius:6px; padding:20px 24px;
            margin-bottom:24px; border:1px solid #E2E8F0;
            border-left:6px solid #E01934;
            box-shadow:0 1px 3px rgba(0,0,0,0.02);">
    <div>
        <div style="font-size:10px; font-weight:700; letter-spacing:1.2px; text-transform:uppercase; color:#94A3B8; margin-bottom:4px;">
            Supply Chain & Infrastructure Performance Analytics
        </div>
        <div style="font-size:24px; font-weight:800; color:#002D62; letter-spacing:-0.5px;">
            Plant Operational Intelligence Hub
        </div>
    </div>
    <div style="text-align:right;">
        <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:4px; padding:8px 16px; display:inline-block;">
            <div style="font-size:9px; font-weight:700; letter-spacing:1px; text-transform:uppercase; color:#94A3B8;">Reporting Domain</div>
            <div style="font-size:13px; font-weight:700; color:#002D62;">
                Jubilant FoodWorks Ltd.
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- NAVIGATION DECK ---
tab_temp, tab_power, tab_runtime, tab_comp = st.tabs([
    "🌡️  Thermodynamic Profiles",
    "⚡  Energy Management & Recovery",
    "⚙️  Component Duty Cycles",
    "📉  Compressor Optimization Suite",
])


# ==========================================================
# TAB 1 — THERMODYNAMIC PROFILES
# ==========================================================
with tab_temp:
    temp_df = load_temperature_data()

    if temp_df is not None and not temp_df.empty:
        latest = temp_df.iloc[-1]

        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Dough Cooler 1 Target", f"{latest['Dough Cooler1 Temp']:.2f} °C")
        with c2: st.metric("Dough Cooler 2 Target", f"{latest['Dough Cooler2 Temp']:.2f} °C")
        with c3: st.metric("Perishable Storage Core", f"{latest['Perishable Cooler Temp']:.2f} °C")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""<div class="section-title">Continuous Thermodynamic Streams (5-Minute Ingestion)</div>""", unsafe_allow_html=True)
        chart_df = temp_df.set_index('Time')[['Dough Cooler1 Temp', 'Dough Cooler2 Temp', 'Perishable Cooler Temp']]
        st.line_chart(chart_df, color=["#002D62", "#0EA5E9", "#E01934"])

        # STATS SUMMARY OVERHAUL
        st.markdown("""<div class="section-title">Thermodynamic Statistical Variance Summary</div>""", unsafe_allow_html=True)
        stats_temp = chart_df.describe().loc[['mean','min','max','std']].T
        stats_temp.columns = ['Mean Operating Temp (°C)', 'Minimum Recorded (°C)', 'Maximum Recorded (°C)', 'Standard Deviation']
        st.dataframe(stats_temp.round(2), use_container_width=True)
    else:
        st.info("System idling. Drop telemetry tracking DataLog files into path directory to activate streaming.")


# ==========================================================
# TAB 2 — ENERGY MANAGEMENT & RECOVERY
# ==========================================================
with tab_power:
    power_df = load_excel_sheet('Sheet1', fallback_header_row=1)

    if power_df is not None and not power_df.empty:
        p = power_df.copy()
        p['Date'] = fast_parse_dates(p['Date'])
        p = p.dropna(subset=['Date']).sort_values('Date')
        p['Dunkin Blast'] = pd.to_numeric(p['Dunkin Blast'], errors='coerce').fillna(0)
        p['CLC Blast'] = pd.to_numeric(p['CLC Blast'], errors='coerce').fillna(0)

        savings_col = next((c for c in p.columns if 'savings' in str(c).lower()), None)
        if savings_col: p[savings_col] = pd.to_numeric(p[savings_col], errors='coerce').fillna(0)

        p = p[p['Dunkin Blast'] < 500_000].copy()

        if not p.empty:
            dunkin_tot = p['Dunkin Blast'].sum()
            clc_tot = p['CLC Blast'].sum()
            sav_tot = p[savings_col].sum() if savings_col else 0

            c1, c2, c3 = st.columns(3)
            with c1: st.metric("Dunkin' Blast Total Consumption", f"{dunkin_tot:,.0f} kWh")
            with c2: st.metric("CLC Blast Total Consumption", f"{clc_tot:,.0f} kWh")
            with c3: st.metric("Net Cost Optimization Balance", f"₹ {sav_tot:,.2f}", delta="Audit Positive", delta_color="inverse")

            st.markdown("<br>", unsafe_allow_html=True)
            gc1, gc2 = st.columns(2)
            with gc1:
                st.markdown("""<div class="section-title">Grid Demand Load Performance Breakdown (kWh)</div>""", unsafe_allow_html=True)
                st.area_chart(p.set_index('Date')[['Dunkin Blast', 'CLC Blast']], color=["#002D62", "#FF9F1C"])
            with gc2:
                if savings_col:
                    st.markdown("""<div class="section-title">Daily Financial Optimization Yield Trails (₹)</div>""", unsafe_allow_html=True)
                    st.bar_chart(p.set_index('Date')[savings_col], color="#16A34A")

            # NEW TAB 2 STATISTICAL OVERHAUL
            st.markdown("""<div class="section-title">Energy Consumption & Cost Optimization Summary Statistics</div>""", unsafe_allow_html=True)
            stats_cols = ['Dunkin Blast', 'CLC Blast']
            if savings_col in p.columns: stats_cols.append(savings_col)
            stats_power = p[stats_cols].describe().loc[['count', 'mean', 'min', 'max', 'std']].T
            stats_power.insert(1, 'Total Accumulated', p[stats_cols].sum())
            stats_power.columns = ['Data Points (Days)', 'Total Accumulated', 'Daily Average', 'Daily Minimum', 'Daily Maximum', 'Standard Deviation']
            st.dataframe(stats_power.round(2), use_container_width=True)

            if os.path.exists(ONEDRIVE_PATH):
                p.to_csv(os.path.join(ONEDRIVE_PATH, "Clean_Daily_Power_Metrics.csv"), index=False)

            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("Open Infrastructure Energy Distribution Ledger"):
                st.dataframe(p, use_container_width=True, hide_index=True)
    else:
        st.info("Energy infrastructure database source path currently unmapped.")


# ==========================================================
# TAB 3 — COMPONENT DUTY CYCLES
# ==========================================================
with tab_runtime:
    runtime_df = load_excel_sheet('Sheet2', fallback_header_row=2)

    if runtime_df is not None and not runtime_df.empty:
        r = runtime_df.copy()
        fc = r.columns[0]
        r = r[~r[fc].astype(str).str.contains('Date|From|Total|Running', case=False, na=False)]
        r[fc] = fast_parse_dates(r[fc])
        r = r.dropna(subset=[f_col]).sort_values(f_col)

        kwh_cols = [c for c in r.columns if 'KWH' in str(c).upper()]
        for col in kwh_cols:
            r[col] = pd.to_numeric(r[col], errors='coerce').fillna(0)

        if kwh_cols and not r.empty:
            c1, c2 = st.columns(2)
            with c1: st.metric("Consolidated Infrastructure Draw", f"{r[kwh_cols[0]].sum():,.0f} kWh")
            with c2: st.metric("Peak System Demand Capacity", f"{r[kwh_cols[0]].max():,.0f} kWh")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"""<div class="section-title">Measured Daily Core Load Displacement Tracker — {kwh_cols[0]}</div>""", unsafe_allow_html=True)
            st.bar_chart(r.set_index(fc)[kwh_cols[0]], color="#002D62")

            # NEW TAB 3 STATISTICAL OVERHAUL
            st.markdown("""<div class="section-title">Component Duty Cycle Load Distribution Statistics</div>""", unsafe_allow_html=True)
            stats_runtime = r[kwh_cols].describe().loc[['count', 'mean', 'min', 'max', 'std']].T
            stats_runtime.insert(1, 'Total Consumption', r[kwh_cols].sum())
            stats_runtime.columns = ['Log Counts (Days)', 'Total Ingested (kWh)', 'Average Load (kWh)', 'Minimum Load (kWh)', 'Maximum Load (kWh)', 'Standard Deviation']
            st.dataframe(stats_runtime.round(2), use_container_width=True)

        with st.expander("Open Active Component Duty Cycle Ledger"):
            st.dataframe(r, use_container_width=True, hide_index=True)
    else:
        st.info("Active asset run-hour capacity workbook logs currently unmapped.")


# ==========================================================
# TAB 4 — COMPRESSOR OPTIMIZATION SUITE
# ==========================================================
with tab_comp:
    comp_df = load_excel_sheet('Sheet3', fallback_header_row=3)

    if comp_df is not None and not comp_df.empty:
        c = comp_df.copy()

        c = c[~c.iloc[:, 0].astype(str).str.strip().str.lower().str.fullmatch(r'date|total|from|sr\.?\s*no\.?|stop|start', na=False)]
        c.iloc[:, 0] = fast_parse_dates(c.iloc[:, 0])
        c = c.dropna(subset=[c.columns[0]]).sort_values(c.columns[0])

        target_hr_col = next((col for col in c.columns if 'saving' in str(col).lower()), None)

        if target_hr_col:
            c[target_hr_col] = pd.to_numeric(c[target_hr_col], errors='coerce').fillna(0)
            c['Progressive Cumulative Savings'] = c[target_hr_col].cumsum()

            tot_hrs = c[target_hr_col].sum()
            avg_hrs = c[target_hr_col].mean()

            k1, k2, k3 = st.columns(3)
            with k1: st.metric("Total Rest Window Allocation", f"{tot_hrs:,.1f} Hours")
            with k2: st.metric("Mean Daily Relief Window", f"{avg_hrs:.1f} Hours / Day")
            with k3: st.metric("Audited Observation Blocks", f"{len(c)} Days")

            st.markdown("<br>", unsafe_allow_html=True)
            gc1, gc2 = st.columns(2)
            date_col = c.columns[0]

            with gc1:
                st.markdown("""<div class="section-title">Daily Component Maintenance Rest Windows (Hours)</div>""", unsafe_allow_html=True)
                st.line_chart(c.set_index(date_col)[target_hr_col], color="#002D62")
            with gc2:
                st.markdown("""<div class="section-title">Progressive Asset Optimization Curve (Cumulative Hours)</div>""", unsafe_allow_html=True)
                st.area_chart(c.set_index(date_col)['Progressive Cumulative Savings'], color="#FF9F1C")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""<div class="section-title">Refrigeration Cluster Operations Frequency Breakdown</div>""", unsafe_allow_html=True)
            
            comp_metrics = {}
            for idx in range(1, 6):
                stop_key = c.columns[2 * idx - 1]
                active_events = c[c[stop_key].notna() & (c[stop_key].astype(str).str.strip() != '')]
                comp_metrics[f"Compressor Unit {idx}"] = len(active_events)
            
            comp_chart_df = pd.DataFrame(list(comp_metrics.items()), columns=["Asset Node", "Maintenance Cycle Triggers"])
            st.bar_chart(comp_chart_df.set_index("Asset Node")["Maintenance Cycle Triggers"], color="#E01934")

            # NEW TAB 4 STATISTICAL OVERHAUL
            st.markdown("""<div class="section-title">Compressor Fleet Resting & Optimization Efficiency Statistics</div>""", unsafe_allow_html=True)
            stats_comp = c[[target_hr_col]].describe().loc[['count', 'mean', 'min', 'max', 'std']].T
            stats_comp.insert(1, 'Total Rest Hours', c[[target_hr_col]].sum())
            stats_comp.columns = ['Audited Days', 'Total Saved Hours', 'Daily Average Rest', 'Minimum Rest Window', 'Maximum Rest Window', 'Standard Deviation']
            st.dataframe(stats_comp.round(2), use_container_width=True)

        else:
            st.warning("Data Validation Warning: Optimization indicator 'Saving in hrs' not discovered in header layer row.")

        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("🔍 Open Full Compressor Machinery Operational Logs (Sheet 3 Raw Data)"):
            st.dataframe(c, use_container_width=True, hide_index=True)
    else:
        st.info("Compressor optimization telemetry source workbook currently unmapped.")
