import streamlit as st
import pandas as pd
import glob
import os
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

# ─────────────────────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="JFL – Plant Operations Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────
#  GLOBAL STYLES
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
}
.block-container { padding: 1.5rem 2.5rem 3rem; background: #F1F4F8; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #002D62 !important;
    border-right: none !important;
}
section[data-testid="stSidebar"] * { color: #CBD5E0 !important; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #FFFFFF !important; }
section[data-testid="stSidebar"] input {
    background: #001840 !important;
    border: 1px solid #1E3A8A !important;
    color: #FFFFFF !important;
    border-radius: 4px !important;
    font-size: 12px !important;
}
section[data-testid="stSidebar"] label {
    color: #94A3B8 !important;
    font-size: 10px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.8px !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: #FFFFFF;
    border-bottom: 2px solid #E2E8F0;
    padding: 0 8px;
    border-radius: 6px 6px 0 0;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    border: none;
    border-bottom: 3px solid transparent;
    padding: 13px 22px;
    font-size: 12.5px;
    font-weight: 700;
    color: #64748B;
    letter-spacing: 0.2px;
    transition: color 0.15s;
}
.stTabs [data-baseweb="tab"]:hover { color: #002D62; }
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    color: #002D62 !important;
    border-bottom: 3px solid #E01934 !important;
    background: transparent !important;
}

/* KPI Cards */
div[data-testid="stMetric"] {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
    padding: 20px 22px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05) !important;
    border-left: 5px solid #002D62 !important;
}
div[data-testid="stMetricLabel"] p {
    color: #64748B !important;
    font-size: 10.5px !important;
    font-weight: 700 !important;
    letter-spacing: 0.7px !important;
    text-transform: uppercase !important;
}
div[data-testid="stMetricValue"] div {
    color: #0F172A !important;
    font-size: 26px !important;
    font-weight: 800 !important;
    letter-spacing: -0.5px !important;
}
div[data-testid="stMetricDelta"] div {
    font-size: 11.5px !important;
    font-weight: 600 !important;
}

/* Section title rule */
.sec-title {
    font-size: 11px;
    font-weight: 700;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin: 28px 0 12px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid #E2E8F0;
}

/* Alert boxes */
.alert-warn {
    background: #FFFBEB; border: 1px solid #FDE68A; border-left: 4px solid #F59E0B;
    border-radius: 6px; padding: 12px 16px; font-size: 13px; color: #92400E; margin-bottom:12px;
}
.alert-ok {
    background: #F0FDF4; border: 1px solid #BBF7D0; border-left: 4px solid #16A34A;
    border-radius: 6px; padding: 12px 16px; font-size: 13px; color: #14532D; margin-bottom:12px;
}
.alert-info {
    background: #EFF6FF; border: 1px solid #BFDBFE; border-left: 4px solid #3B82F6;
    border-radius: 6px; padding: 12px 16px; font-size: 13px; color: #1E3A8A; margin-bottom:12px;
}

/* Compliance badge */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
}
.badge-green { background:#D1FAE5; color:#065F46; }
.badge-yellow { background:#FEF3C7; color:#92400E; }
.badge-red { background:#FEE2E2; color:#991B1B; }

/* Status pill sidebar */
.status-pill {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 700;
}
.status-ok  { background:#D1FAE5; color:#065F46; border:1px solid #A7F3D0; }
.status-err { background:#FEE2E2; color:#991B1B; border:1px solid #FCA5A5; }

/* Table clean */
.stDataFrame { border-radius: 6px; overflow: hidden; }
hr { border: none; border-top: 1px solid #E2E8F0; margin: 18px 0; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style="padding:16px 0 20px;">
            <div style="font-size:9px; font-weight:700; letter-spacing:1.8px; color:#64748B;
                        text-transform:uppercase; margin-bottom:6px;">
                JUBILANT FOODWORKS LIMITED
            </div>
            <div style="font-size:17px; font-weight:800; color:#FFFFFF; line-height:1.25;">
                Plant Operations<br>Dashboard
            </div>
            <div style="margin-top:10px; width:36px; height:3px;
                        background:#E01934; border-radius:2px;"></div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#1E3A8A; margin:8px 0 16px;'>", unsafe_allow_html=True)

    st.markdown("""<div style="font-size:9px; font-weight:700; letter-spacing:1.2px;
                    color:#64748B; text-transform:uppercase; margin-bottom:10px;">
                    Data Source</div>""", unsafe_allow_html=True)

    user_name      = st.text_input("Windows Username", value="aayush")
    company_folder = st.text_input("OneDrive Folder", value="OneDrive")

    ONEDRIVE_PATH = f"C:/Users/{user_name}/{company_folder}/PlantData/"
    LOCAL_PATH    = "./"

    st.markdown("<hr style='border-color:#1E3A8A; margin:14px 0;'>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
#  FILE RESOLVER
# ─────────────────────────────────────────────────────────────
def resolve_file(filename, is_pattern=False):
    if is_pattern:
        nodes = glob.glob(os.path.join(ONEDRIVE_PATH, filename))
        if nodes: return nodes, "OneDrive"
        nodes = glob.glob(os.path.join(LOCAL_PATH, filename))
        return nodes, ("Local" if nodes else None)
    cloud = os.path.join(ONEDRIVE_PATH, filename)
    if os.path.exists(cloud): return cloud, "OneDrive"
    return os.path.join(LOCAL_PATH, filename), "Local"


csv_files, csv_src  = resolve_file("DataLog_*.csv", is_pattern=True)
xlsx_path, xlsx_src = resolve_file("Power consumption freon.xlsx")
xlsx_ok             = os.path.exists(xlsx_path)

with st.sidebar:
    st.markdown("""<div style="font-size:9px; font-weight:700; letter-spacing:1.2px;
                    color:#64748B; text-transform:uppercase; margin-bottom:10px;">
                    Connection Status</div>""", unsafe_allow_html=True)

    st.markdown(f"""
        <div style="margin-bottom:8px;">
            <span class="status-pill status-{'ok' if csv_files else 'err'}">
                {'●' if csv_files else '○'}&nbsp; Temp Logs · {csv_src if csv_files else 'Not Found'}
            </span>
        </div>
        <div>
            <span class="status-pill status-{'ok' if xlsx_ok else 'err'}">
                {'●' if xlsx_ok else '○'}&nbsp; Energy Workbook · {xlsx_src if xlsx_ok else 'Not Found'}
            </span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style="position:fixed; bottom:18px; left:0; width:238px;
                    text-align:center; font-size:10px; color:#475569;
                    font-weight:600; letter-spacing:0.3px; padding:0 8px;">
            JFL Internal Operations Tool &nbsp;·&nbsp; v2.1
        </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
#  DATA LOADERS
# ─────────────────────────────────────────────────────────────
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
    for f in sorted(files):
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
              .sort_values('Time')
              .reset_index(drop=True))

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
        if sheet_name == 'Sheet3' and len(df.columns) >= 12:
            df.columns.values[11] = 'Saving in hrs'
        elif sheet_name == 'Sheet3':
            last = df.columns[-1]
            if 'unnamed' in str(last).lower():
                df = df.rename(columns={last: 'Saving in hrs'})
        if not df.empty:
            fc = df.columns[0]
            df = df[df[fc].astype(str).str.strip().str.lower() != 'total']
        return df
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────
#  PAGE HEADER
# ─────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex; align-items:center; justify-content:space-between;
            background:#FFFFFF; border-radius:8px; padding:18px 26px;
            margin-bottom:22px; border:1px solid #E2E8F0;
            border-left:6px solid #E01934;
            box-shadow:0 1px 4px rgba(0,0,0,0.04);">
    <div>
        <div style="font-size:10px; font-weight:700; letter-spacing:1.3px;
                    text-transform:uppercase; color:#94A3B8; margin-bottom:5px;">
            Supply Chain &amp; Manufacturing · Noida Plant
        </div>
        <div style="font-size:22px; font-weight:800; color:#002D62; letter-spacing:-0.4px;">
            Plant Operational Intelligence Hub
        </div>
    </div>
    <div style="display:flex; gap:12px; align-items:center;">
        <div style="text-align:right; background:#F8FAFC; border:1px solid #E2E8F0;
                    border-radius:6px; padding:10px 16px;">
            <div style="font-size:9px; font-weight:700; letter-spacing:1px;
                        text-transform:uppercase; color:#94A3B8;">Reporting Period</div>
            <div style="font-size:13px; font-weight:700; color:#002D62;">
                01 Jun – 06 Jun 2026
            </div>
        </div>
        <div style="text-align:right; background:#002D62; border-radius:6px; padding:10px 16px;">
            <div style="font-size:9px; font-weight:700; letter-spacing:1px;
                        text-transform:uppercase; color:#94A3B8;">Entity</div>
            <div style="font-size:13px; font-weight:700; color:#FFFFFF;">
                Jubilant FoodWorks Ltd.
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
#  TABS
# ─────────────────────────────────────────────────────────────
tab_temp, tab_power, tab_runtime, tab_comp = st.tabs([
    "🌡️  Cold Storage Temperatures",
    "⚡  Energy & Cost Savings",
    "⚙️  Asset Duty Cycles",
    "📉  Compressor Optimisation",
])


# ═══════════════════════════════════════════════════════════════
#  TAB 1 — COLD STORAGE TEMPERATURES
# ═══════════════════════════════════════════════════════════════
with tab_temp:
    temp_df = load_temperature_data()

    if temp_df is not None and not temp_df.empty:
        latest  = temp_df.iloc[-1]
        sensors = ['Dough Cooler1 Temp', 'Dough Cooler2 Temp', 'Perishable Cooler Temp']
        THRESHOLD = 4.0  # °C food-safe limit

        # ── Top KPIs ──────────────────────────────────────────
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Dough Cooler 1  (Latest)", f"{latest['Dough Cooler1 Temp']:.2f} °C")
        with c2:
            st.metric("Dough Cooler 2  (Latest)", f"{latest['Dough Cooler2 Temp']:.2f} °C")
        with c3:
            st.metric("Perishable Store  (Latest)", f"{latest['Perishable Cooler Temp']:.2f} °C")
        with c4:
            total_logs = len(temp_df)
            total_exc  = sum((temp_df[s] > THRESHOLD).sum() for s in sensors)
            fleet_compliance = (1 - total_exc / (total_logs * len(sensors))) * 100
            st.metric("Fleet Compliance Rate", f"{fleet_compliance:.1f}%",
                      delta=f"{total_exc} excursions >4°C", delta_color="inverse")

        # ── Trend Chart ────────────────────────────────────────
        st.markdown('<div class="sec-title">Temperature Trends — 5-Minute Interval Logs (01–06 Jun 2026)</div>',
                    unsafe_allow_html=True)
        st.line_chart(
            temp_df.set_index('Time')[sensors],
            color=["#002D62", "#0EA5E9", "#E01934"]
        )

        # ── Daily Average Chart ────────────────────────────────
        st.markdown('<div class="sec-title">Daily Average Temperature by Zone</div>',
                    unsafe_allow_html=True)
        temp_df['Date'] = temp_df['Time'].dt.date
        daily_avg = temp_df.groupby('Date')[sensors].mean().round(2)
        daily_avg.index = daily_avg.index.astype(str)
        st.bar_chart(daily_avg, color=["#002D62", "#0EA5E9", "#E01934"])

        # ── Compliance Summary Table ───────────────────────────
        st.markdown('<div class="sec-title">Cold-Chain Compliance Audit — 01 to 06 Jun 2026</div>',
                    unsafe_allow_html=True)

        labels = {
            'Dough Cooler1 Temp':    'Dough Cooler 1',
            'Dough Cooler2 Temp':    'Dough Cooler 2',
            'Perishable Cooler Temp':'Perishable Storage',
        }
        rows = []
        for col in sensors:
            s = temp_df[col]
            n = len(s)
            exc = int((s > THRESHOLD).sum())
            comp = (n - exc) / n * 100
            if comp >= 95:
                badge = '<span class="badge badge-green">✓ Compliant</span>'
            elif comp >= 85:
                badge = '<span class="badge badge-yellow">⚠ At Risk</span>'
            else:
                badge = '<span class="badge badge-red">✗ Non-Compliant</span>'
            rows.append({
                "Zone": labels[col],
                "Readings": f"{n:,}",
                "Mean (°C)": f"{s.mean():.2f}",
                "Min (°C)":  f"{s.min():.2f}",
                "Max (°C)":  f"{s.max():.2f}",
                "Std Dev":   f"{s.std():.2f}",
                f"Excursions >4°C": exc,
                "Compliance Rate": f"{comp:.1f}%",
                "Status": badge,
            })

        audit_df = pd.DataFrame(rows)
        st.markdown(
            audit_df.to_html(escape=False, index=False,
                border=0,
                classes="",
                table_id="audit-table"
            ).replace('<table',
                '<table style="width:100%;border-collapse:collapse;font-size:13px;'
                'font-family:Segoe UI,sans-serif;"'
            ).replace('<th>', '<th style="background:#002D62;color:#fff;padding:10px 14px;'
                'text-align:left;font-size:11px;font-weight:700;letter-spacing:0.5px;">',
            ).replace('<td>', '<td style="padding:9px 14px;border-bottom:1px solid #E2E8F0;color:#0F172A;">'),
            unsafe_allow_html=True
        )

        # ── Per-sensor excursion alerts ────────────────────────
        st.markdown('<div class="sec-title">Zone Alerts</div>', unsafe_allow_html=True)
        for col in sensors:
            exc = int((temp_df[col] > THRESHOLD).sum())
            comp = (len(temp_df) - exc) / len(temp_df) * 100
            label = labels[col]
            if comp >= 95:
                st.markdown(f'<div class="alert-ok">✓ <strong>{label}</strong> — {comp:.1f}% compliant. {exc} minor excursion(s) across 1,728 readings.</div>', unsafe_allow_html=True)
            elif comp >= 85:
                st.markdown(f'<div class="alert-warn">⚠ <strong>{label}</strong> — {comp:.1f}% compliant. {exc} excursion(s) above 4°C. Review loading schedule.</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="alert-warn">⚠ <strong>{label}</strong> — {comp:.1f}% compliant. {exc} excursion(s) detected. Immediate review recommended.</div>', unsafe_allow_html=True)

        # ── Raw log expander ───────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("View raw sensor log — all 1,728 readings"):
            st.dataframe(temp_df.drop(columns=['Date']), use_container_width=True, hide_index=True)

    else:
        st.markdown("""
            <div class="alert-info">
                <strong>No data found.</strong> Place <code>DataLog_*.csv</code> files in the
                configured directory to populate this view.
            </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  TAB 2 — ENERGY & COST SAVINGS
# ═══════════════════════════════════════════════════════════════
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
        p = p[p['Dunkin Blast'] < 500_000].copy()

        if not p.empty:
            dunkin_tot = p['Dunkin Blast'].sum()
            clc_tot    = p['CLC Blast'].sum()
            sav_tot    = p[sav_col].sum() if sav_col else 0
            days       = p['Date'].nunique()

            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Dunkin' Blast Total",  f"{dunkin_tot:,.0f} kWh")
            with c2: st.metric("CLC Blast Total",      f"{clc_tot:,.0f} kWh")
            with c3: st.metric("Combined Consumption", f"{dunkin_tot+clc_tot:,.0f} kWh")
            with c4: st.metric("Net Cost Savings",     f"₹ {sav_tot:,.2f}",
                               delta="vs. baseline", delta_color="inverse")

            st.markdown('<div class="sec-title">Daily Power Consumption (kWh)</div>',
                        unsafe_allow_html=True)
            st.area_chart(p.set_index('Date')[['Dunkin Blast', 'CLC Blast']],
                          color=["#002D62", "#FF9F1C"])

            if sav_col:
                st.markdown('<div class="sec-title">Daily Cost Savings (₹)</div>',
                            unsafe_allow_html=True)
                st.bar_chart(p.set_index('Date')[sav_col], color="#16A34A")

            st.markdown('<div class="sec-title">Summary Statistics</div>',
                        unsafe_allow_html=True)
            stat_cols = ['Dunkin Blast', 'CLC Blast'] + ([sav_col] if sav_col else [])
            stats = p[stat_cols].describe().loc[['count','mean','min','max','std']].T.round(2)
            stats.insert(0, 'Total', p[stat_cols].sum().round(2))
            stats.columns = ['Total', 'Days', 'Daily Avg', 'Daily Min', 'Daily Max', 'Std Dev']
            st.dataframe(stats, use_container_width=True)

            if os.path.exists(ONEDRIVE_PATH):
                p.to_csv(os.path.join(ONEDRIVE_PATH, "Clean_Daily_Power_Metrics.csv"), index=False)

            with st.expander("View raw data — Energy Workbook Sheet 1"):
                st.dataframe(p, use_container_width=True, hide_index=True)
    else:
        st.markdown('<div class="alert-info">Energy workbook (Sheet 1) not found at configured path.</div>',
                    unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  TAB 3 — ASSET DUTY CYCLES
# ═══════════════════════════════════════════════════════════════
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
            with c1: st.metric("Total Energy Draw",  f"{r[kwh_cols[0]].sum():,.0f} kWh")
            with c2: st.metric("Peak Daily Draw",    f"{r[kwh_cols[0]].max():,.0f} kWh")
            with c3: st.metric("Average Daily Draw", f"{r[kwh_cols[0]].mean():,.0f} kWh")

            st.markdown(f'<div class="sec-title">Daily Capacity Draw — {kwh_cols[0]}</div>',
                        unsafe_allow_html=True)
            st.bar_chart(r.set_index(fc)[kwh_cols[0]], color="#002D62")

            st.markdown('<div class="sec-title">Summary Statistics</div>',
                        unsafe_allow_html=True)
            stats_r = r[kwh_cols].describe().loc[['count','mean','min','max','std']].T.round(2)
            stats_r.insert(0, 'Total (kWh)', r[kwh_cols].sum().round(2))
            stats_r.columns = ['Total (kWh)', 'Days', 'Avg (kWh)', 'Min (kWh)', 'Max (kWh)', 'Std Dev']
            st.dataframe(stats_r, use_container_width=True)

        with st.expander("View raw data — Asset Duty Cycle Sheet 2"):
            st.dataframe(r, use_container_width=True, hide_index=True)
    else:
        st.markdown('<div class="alert-info">Energy workbook (Sheet 2) not found at configured path.</div>',
                    unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  TAB 4 — COMPRESSOR OPTIMISATION
# ═══════════════════════════════════════════════════════════════
with tab_comp:
    comp_df = load_excel_sheet('Sheet3', fallback_header_row=3)

    if comp_df is not None and not comp_df.empty:
        c = comp_df.copy()
        c = c[~c.iloc[:, 0].astype(str).str.strip().str.lower()
               .str.fullmatch(r'date|total|from|sr\.?\s*no\.?', na=False)]
        c.iloc[:, 0] = fast_parse_dates(c.iloc[:, 0])
        c = c.dropna(subset=[c.columns[0]]).sort_values(c.columns[0])

        sav_col = next(
            (col for col in c.columns
             if 'saving' in str(col).lower() and ('hr' in str(col).lower() or 'hour' in str(col).lower())),
            None
        )
        if not sav_col:
            sav_col = next((col for col in c.columns if 'saving' in str(col).lower()), None)

        if sav_col:
            c[sav_col]              = pd.to_numeric(c[sav_col], errors='coerce').fillna(0)
            c['Cumulative Hours']   = c[sav_col].cumsum()

            tot_hrs  = c[sav_col].sum()
            avg_hrs  = c[sav_col].mean()
            max_hrs  = c[sav_col].max()
            days_rec = len(c)

            k1, k2, k3, k4 = st.columns(4)
            with k1: st.metric("Total Hours Saved",   f"{tot_hrs:,.1f} hrs")
            with k2: st.metric("Average / Day",       f"{avg_hrs:.1f} hrs")
            with k3: st.metric("Best Day (Max)",      f"{max_hrs:.1f} hrs")
            with k4: st.metric("Days on Record",      f"{days_rec}")

            date_col = c.columns[0]

            gc1, gc2 = st.columns(2)
            with gc1:
                st.markdown('<div class="sec-title">Daily Saved Run Hours</div>',
                            unsafe_allow_html=True)
                st.line_chart(c.set_index(date_col)[sav_col], color="#002D62")
                st.caption("Hours of compressor rest achieved each day through optimisation.")
            with gc2:
                st.markdown('<div class="sec-title">Cumulative Hours Saved</div>',
                            unsafe_allow_html=True)
                st.area_chart(c.set_index(date_col)['Cumulative Hours'], color="#FF9F1C")
                st.caption("Running total of compressor hours saved across the reporting period.")

            st.markdown('<div class="sec-title">Optimisation Statistics</div>',
                        unsafe_allow_html=True)
            stats_c = c[[sav_col]].describe().loc[['count','mean','min','max','std']].T.round(2)
            stats_c.insert(0, 'Total Saved (hrs)', round(tot_hrs, 2))
            stats_c.columns = ['Total Saved (hrs)', 'Days', 'Avg/Day', 'Min Day', 'Max Day', 'Std Dev']
            st.dataframe(stats_c, use_container_width=True)

        else:
            st.markdown('<div class="alert-warn">Column "Saving in hrs" not found in Sheet 3.</div>',
                        unsafe_allow_html=True)
            with st.expander("Debug — Sheet 3 column names"):
                st.write(list(comp_df.columns))

        with st.expander("View raw data — Compressor Log Sheet 3"):
            st.dataframe(c, use_container_width=True, hide_index=True)
    else:
        st.markdown('<div class="alert-info">Energy workbook (Sheet 3) not found at configured path.</div>',
                    unsafe_allow_html=True)
