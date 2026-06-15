import streamlit as st
import pandas as pd
import glob
import os
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="JFL – Plant Operations Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
#  GLOBAL STYLES
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ── Reset & Canvas ── */
html, body, [class*="css"] { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; }
.block-container { padding: 1.5rem 2rem 3rem; background: #F0F2F5; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #001F4D !important;
    border-right: none !important;
}
section[data-testid="stSidebar"] * { color: #CBD5E0 !important; }
section[data-testid="stSidebar"] input {
    background: #0A2A5E !important;
    border: 1px solid #2D4A7A !important;
    color: #E2E8F0 !important;
    border-radius: 4px !important;
}
section[data-testid="stSidebar"] label {
    color: #94A3B8 !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.6px !important;
}

/* ── Tab Strip ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: #FFFFFF;
    border-bottom: 2px solid #E2E8F0;
    padding: 0 4px;
    border-radius: 6px 6px 0 0;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    border: none;
    border-bottom: 3px solid transparent;
    padding: 14px 24px;
    font-size: 13px;
    font-weight: 600;
    color: #64748B;
    letter-spacing: 0.2px;
    transition: color 0.15s, border-color 0.15s;
    border-radius: 0;
}
.stTabs [data-baseweb="tab"]:hover { color: #002D62; }
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    color: #002D62 !important;
    border-bottom: 3px solid #E01934 !important;
    background: transparent !important;
}

/* ── KPI Cards ── */
div[data-testid="stMetric"] {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 6px !important;
    padding: 20px 22px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
    border-left: 4px solid #002D62 !important;
}
div[data-testid="stMetricLabel"] p {
    color: #64748B !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    letter-spacing: 0.8px !important;
    text-transform: uppercase !important;
}
div[data-testid="stMetricValue"] div {
    color: #0F172A !important;
    font-size: 28px !important;
    font-weight: 700 !important;
    letter-spacing: -0.5px !important;
}
div[data-testid="stMetricDelta"] div {
    font-size: 12px !important;
    font-weight: 600 !important;
}

/* ── Section Cards ── */
.section-card {
    background: #FFFFFF;
    border-radius: 6px;
    padding: 20px 22px;
    margin-bottom: 16px;
    border: 1px solid #E2E8F0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

/* ── Section Headers ── */
.section-title {
    font-size: 13px;
    font-weight: 700;
    color: #002D62;
    text-transform: uppercase;
    letter-spacing: 0.7px;
    margin: 0 0 16px 0;
    padding-bottom: 10px;
    border-bottom: 1px solid #EEF2F7;
}

/* ── Status Pill ── */
.status-pill {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.4px;
}
.status-ok   { background: #D1FAE5; color: #065F46; }
.status-err  { background: #FEE2E2; color: #991B1B; }
.status-warn { background: #FEF3C7; color: #92400E; }

/* ── Divider ── */
hr { border: none; border-top: 1px solid #E2E8F0; margin: 18px 0; }

/* ── Expander ── */
details summary {
    font-size: 12px !important;
    font-weight: 600 !important;
    color: #475569 !important;
}

/* ── Dataframe ── */
.stDataFrame { border-radius: 6px; overflow: hidden; border: 1px solid #E2E8F0; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style="padding:18px 0 20px;">
            <div style="font-size:10px; font-weight:700; letter-spacing:1.5px;
                        color:#94A3B8; text-transform:uppercase; margin-bottom:4px;">
                JUBILANT FOODWORKS LIMITED
            </div>
            <div style="font-size:17px; font-weight:800; color:#FFFFFF; line-height:1.2;">
                Plant Operations<br>Dashboard
            </div>
            <div style="margin-top:8px; width:32px; height:3px;
                        background:#E01934; border-radius:2px;"></div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""<div style="font-size:10px; font-weight:700; letter-spacing:1px;
                    color:#64748B; text-transform:uppercase; margin-bottom:10px;">
                    Data Source Configuration</div>""", unsafe_allow_html=True)

    user_name      = st.text_input("Windows Username", value="aayush")
    company_folder = st.text_input("OneDrive Folder Name", value="OneDrive")

    ONEDRIVE_PATH = f"C:/Users/{user_name}/{company_folder}/PlantData/"
    LOCAL_PATH    = "./"

    st.markdown("---")


# ─────────────────────────────────────────────
#  FILE RESOLVER
# ─────────────────────────────────────────────
def resolve_file(filename, is_pattern=False):
    if is_pattern:
        nodes = glob.glob(os.path.join(ONEDRIVE_PATH, filename))
        if nodes: return nodes, "OneDrive"
        nodes = glob.glob(os.path.join(LOCAL_PATH, filename))
        return nodes, ("Local" if nodes else None)
    cloud = os.path.join(ONEDRIVE_PATH, filename)
    if os.path.exists(cloud): return cloud, "OneDrive"
    return os.path.join(LOCAL_PATH, filename), "Local"


# Connection status
csv_files, csv_src  = resolve_file("DataLog_*.csv", is_pattern=True)
xlsx_path, xlsx_src = resolve_file("Power consumption freon.xlsx")
xlsx_ok = os.path.exists(xlsx_path)

with st.sidebar:
    st.markdown("""<div style="font-size:10px; font-weight:700; letter-spacing:1px;
                    color:#64748B; text-transform:uppercase; margin-bottom:10px;">
                    Connection Status</div>""", unsafe_allow_html=True)

    csv_status  = ("ok"  if csv_files else "err")
    xlsx_status = ("ok"  if xlsx_ok   else "err")

    csv_label  = f"Temperature Logs · {csv_src}"  if csv_files else "Temperature Logs · Not Found"
    xlsx_label = f"Energy Workbook · {xlsx_src}"  if xlsx_ok   else "Energy Workbook · Not Found"

    st.markdown(f"""
        <div style="margin-bottom:8px;">
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
        <div style="position:fixed; bottom:20px; left:0; width:230px;
                    text-align:center; font-size:10px; color:#334155;
                    font-weight:600; letter-spacing:0.5px;">
            JFL Internal Operations Tool · v2.0
        </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  DATA LOADERS
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
        if not df.empty:
            fc = df.columns[0]
            df = df[df[fc].astype(str).str.strip().str.lower() != 'total']
        return df
    except Exception:
        return None


# ─────────────────────────────────────────────
#  PAGE HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div style="display:flex; align-items:center; justify-content:space-between;
            background:#FFFFFF; border-radius:6px; padding:18px 24px;
            margin-bottom:24px; border:1px solid #E2E8F0;
            border-left:5px solid #E01934;
            box-shadow:0 1px 3px rgba(0,0,0,0.04);">
    <div>
        <div style="font-size:11px; font-weight:700; letter-spacing:1.2px;
                    text-transform:uppercase; color:#94A3B8; margin-bottom:4px;">
            Supply Chain & Manufacturing
        </div>
        <div style="font-size:22px; font-weight:800; color:#0F172A; letter-spacing:-0.3px;">
            Plant Operational Intelligence
        </div>
    </div>
    <div style="text-align:right;">
        <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:4px;
                    padding:8px 14px; display:inline-block;">
            <div style="font-size:10px; font-weight:700; letter-spacing:1px;
                        text-transform:uppercase; color:#94A3B8;">Reporting Unit</div>
            <div style="font-size:13px; font-weight:700; color:#002D62;">
                Jubilant FoodWorks Ltd.
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  TABS
# ─────────────────────────────────────────────
tab_temp, tab_power, tab_runtime, tab_comp = st.tabs([
    "🌡️  Cold Storage Temperatures",
    "⚡  Energy & Cost Savings",
    "⚙️  Asset Duty Cycles",
    "📉  Compressor Optimisation",
])


# ═══════════════════════════════════════════════
#  TAB 1 — COLD STORAGE TEMPERATURES
# ═══════════════════════════════════════════════
with tab_temp:
    temp_df = load_temperature_data()

    if temp_df is not None and not temp_df.empty:
        latest = temp_df.iloc[-1]

        # KPI Row
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Dough Cooler 1", f"{latest['Dough Cooler1 Temp']:.2f} °C")
        with c2:
            st.metric("Dough Cooler 2", f"{latest['Dough Cooler2 Temp']:.2f} °C")
        with c3:
            st.metric("Perishable Storage", f"{latest['Perishable Cooler Temp']:.2f} °C")

        st.markdown("<br>", unsafe_allow_html=True)

        # Chart
        st.markdown("""<div class="section-title">Temperature Trend — 5-Minute Interval Logs</div>""",
                    unsafe_allow_html=True)
        chart_df = temp_df.set_index('Time')[
            ['Dough Cooler1 Temp', 'Dough Cooler2 Temp', 'Perishable Cooler Temp']
        ]
        st.line_chart(chart_df, color=["#002D62", "#0EA5E9", "#E01934"])

        # Stats summary
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""<div class="section-title">Statistical Summary</div>""",
                    unsafe_allow_html=True)
        stats = chart_df.describe().loc[['mean','min','max','std']].T
        stats.columns = ['Mean (°C)', 'Min (°C)', 'Max (°C)', 'Std Dev']
        stats = stats.round(2)
        st.dataframe(stats, use_container_width=True)

    else:
        st.markdown("""
            <div style="background:#FFF8F0; border:1px solid #FCD9A0; border-radius:6px;
                        padding:20px 24px; color:#92400E;">
                <strong>No data found.</strong>&nbsp; Place <code>DataLog_*.csv</code> files in the
                configured directory to populate this view.
            </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════
#  TAB 2 — ENERGY & COST SAVINGS
# ═══════════════════════════════════════════════
with tab_power:
    power_df = load_excel_sheet('Sheet1', fallback_header_row=1)

    if power_df is not None and not power_df.empty:
        p = power_df.copy()
        p['Date']         = fast_parse_dates(p['Date'])
        p                 = p.dropna(subset=['Date']).sort_values('Date')
        p['Dunkin Blast'] = pd.to_numeric(p['Dunkin Blast'], errors='coerce').fillna(0)
        p['CLC Blast']    = pd.to_numeric(p['CLC Blast'],    errors='coerce').fillna(0)

        sav_col = next((c for c in p.columns if 'saving' in str(c).lower()), None)
        if sav_col:
            p[sav_col] = pd.to_numeric(p[sav_col], errors='coerce').fillna(0)

        # Remove outliers
        p = p[p['Dunkin Blast'] < 500_000].copy()

        if not p.empty:
            dunkin_tot = p['Dunkin Blast'].sum()
            clc_tot    = p['CLC Blast'].sum()
            sav_tot    = p[sav_col].sum() if sav_col else 0

            # KPIs
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Dunkin' Blast – Total", f"{dunkin_tot:,.0f} kWh")
            with c2:
                st.metric("CLC Blast – Total",     f"{clc_tot:,.0f} kWh")
            with c3:
                st.metric("Net Cost Savings",      f"₹ {sav_tot:,.2f}",
                          delta="vs. baseline", delta_color="inverse")

            st.markdown("<br>", unsafe_allow_html=True)

            # Charts
            gc1, gc2 = st.columns(2)
            with gc1:
                st.markdown("""<div class="section-title">Daily Power Consumption (kWh)</div>""",
                            unsafe_allow_html=True)
                st.area_chart(p.set_index('Date')[['Dunkin Blast', 'CLC Blast']],
                              color=["#002D62", "#FF9F1C"])
            with gc2:
                if sav_col:
                    st.markdown("""<div class="section-title">Daily Cost Savings (₹)</div>""",
                                unsafe_allow_html=True)
                    st.bar_chart(p.set_index('Date')[sav_col], color="#16A34A")

            # Auto-export
            if os.path.exists(ONEDRIVE_PATH):
                p.to_csv(os.path.join(ONEDRIVE_PATH, "Clean_Daily_Power_Metrics.csv"), index=False)

            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("View raw data — Sheet 1"):
                st.dataframe(p, use_container_width=True, hide_index=True)
    else:
        st.info("'Power consumption freon.xlsx' (Sheet 1) is not available at the configured path.")


# ═══════════════════════════════════════════════
#  TAB 3 — ASSET DUTY CYCLES
# ═══════════════════════════════════════════════
with tab_runtime:
    runtime_df = load_excel_sheet('Sheet2', fallback_header_row=2)

    if runtime_df is not None and not runtime_df.empty:
        r = runtime_df.copy()
        fc = r.columns[0]
        r  = r[~r[fc].astype(str).str.contains('Date|From|Total|Running', case=False, na=False)]
        r[fc] = fast_parse_dates(r[fc])
        r  = r.dropna(subset=[fc]).sort_values(fc)

        kwh_cols = [c for c in r.columns if 'KWH' in str(c).upper()]
        for col in kwh_cols:
            r[col] = pd.to_numeric(r[col], errors='coerce').fillna(0)

        if kwh_cols and not r.empty:
            # KPIs
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Total Energy Draw", f"{r[kwh_cols[0]].sum():,.0f} kWh")
            with c2:
                st.metric("Peak Daily Draw", f"{r[kwh_cols[0]].max():,.0f} kWh")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"""<div class="section-title">Daily Capacity Draw — {kwh_cols[0]}</div>""",
                        unsafe_allow_html=True)
            st.bar_chart(r.set_index(fc)[kwh_cols[0]], color="#002D62")

        with st.expander("View raw data — Sheet 2"):
            st.dataframe(r, use_container_width=True, hide_index=True)
    else:
        st.info("'Power consumption freon.xlsx' (Sheet 2) is not available at the configured path.")


# ═══════════════════════════════════════════════
#  TAB 4 — COMPRESSOR OPTIMISATION
# ═══════════════════════════════════════════════
with tab_comp:
    comp_df = load_excel_sheet('Sheet3', fallback_header_row=3)

    if comp_df is not None and not comp_df.empty:
        c = comp_df.copy()

        # Only drop summary/header rows — NOT data rows that mention start/stop times
        c = c[~c.iloc[:, 0].astype(str).str.strip().str.lower()
               .str.fullmatch(r'date|total|from|sr\.?\s*no\.?', na=False)]
        c.iloc[:, 0] = fast_parse_dates(c.iloc[:, 0])
        c = c.dropna(subset=[c.columns[0]]).sort_values(c.columns[0])

        # Match 'saving in hrs' or 'savings hrs' but not plain 'hrs' columns
        sav_col = next(
            (col for col in c.columns
             if 'saving' in str(col).lower() and ('hr' in str(col).lower() or 'hour' in str(col).lower())),
            None
        )
        # Fallback: any column with 'saving'
        if not sav_col:
            sav_col = next(
                (col for col in c.columns if 'saving' in str(col).lower()),
                None
            )

        if sav_col:
            c[sav_col] = pd.to_numeric(c[sav_col], errors='coerce').fillna(0)
            c['Cumulative Hours'] = c[sav_col].cumsum()

            tot_hrs = c[sav_col].sum()
            avg_hrs = c[sav_col].mean()

            # KPIs
            k1, k2, k3 = st.columns(3)
            with k1:
                st.metric("Total Hours Saved", f"{tot_hrs:,.1f} hrs")
            with k2:
                st.metric("Average / Day",     f"{avg_hrs:.1f} hrs")
            with k3:
                st.metric("Days Recorded",     f"{len(c)}")

            st.markdown("<br>", unsafe_allow_html=True)

            # Charts
            gc1, gc2 = st.columns(2)
            date_col = c.columns[0]

            with gc1:
                st.markdown("""<div class="section-title">Daily Saved Run Hours</div>""",
                            unsafe_allow_html=True)
                st.line_chart(c.set_index(date_col)[sav_col], color="#002D62")

            with gc2:
                st.markdown("""<div class="section-title">Cumulative Hours Saved</div>""",
                            unsafe_allow_html=True)
                st.area_chart(c.set_index(date_col)['Cumulative Hours'], color="#FF9F1C")

        else:
            st.warning("Column 'Saving in hrs' not found in Sheet 3. Check the file headers.")
            with st.expander("🔍 Debug — detected column names in Sheet 3"):
                st.write(list(comp_df.columns))

        with st.expander("View raw data — Sheet 3"):
            st.dataframe(c, use_container_width=True, hide_index=True)
    else:
        st.info("'Power consumption freon.xlsx' (Sheet 3) is not available at the configured path.")
