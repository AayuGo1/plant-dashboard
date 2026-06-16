import streamlit as st
import pandas as pd
import requests
import io
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

# ─────────────────────────────────────────────────────────────
#  CORPORATE CROSS-SCREEN PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="JFL – Plant Operations Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="auto"
)

# ─────────────────────────────────────────────────────────────
#  PREMIUM LIGHT THEME & RESPONSIVE CSS INJECTION
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Canvas Background & Typography ── */
html, body, [class*="css"] { font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif; }
.block-container { padding: 1.5rem 2.5rem 3rem; background: #F4F6F9; }

/* ── Branded Left Navigation Sidebar ── */
section[data-testid="stSidebar"] {
    background: #002D62 !important; /* JFL Deep Navy Blue */
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

/* ── Premium Light Theme Header Section ── */
.jfl-header-container {
    background: #FFFFFF;
    border-radius: 8px;
    padding: 24px;
    margin-bottom: 24px;
    border: 1px solid #E2E8F0;
    border-left: 6px solid #E01934; /* JFL Brand Crimson Accent Stripe */
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02), 0 2px 4px -1px rgba(0,0,0,0.01);
}
.jfl-header-title {
    font-size: 24px;
    font-weight: 800;
    color: #002D62;
    letter-spacing: -0.5px;
    line-height: 1.2;
}
.jfl-header-subtitle {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: #64748B;
    margin-top: 4px;
}
.jfl-header-meta-box {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 10px 16px;
    text-align: left;
    height: 100%;
}
.jfl-meta-label {
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #94A3B8;
    margin-bottom: 2px;
}
.jfl-meta-value {
    font-size: 13px;
    font-weight: 700;
    color: #002D62;
}

/* ── Tabs Strip ── */
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
    padding: 14px 22px;
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

/* ── KPI Cards ── */
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

/* ── Section Title ── */
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

/* ── Alert Containers ── */
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

/* ── Status Badges ── */
.badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; }
.badge-green { background:#D1FAE5; color:#065F46; }
.badge-yellow { background:#FEF3C7; color:#92400E; }
.badge-red { background:#FEE2E2; color:#991B1B; }
.status-pill { display: inline-block; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 700; }
.status-ok  { background:#D1FAE5; color:#065F46; border:1px solid #A7F3D0; }
.status-err { background:#FEE2E2; color:#991B1B; border:1px solid #FCA5A5; }

/* ── Clean Dataframe Layouts ── */
.stDataFrame { border-radius: 6px; overflow: hidden; }
hr { border: none; border-top: 1px solid #E2E8F0; margin: 18px 0; }

@media (max-width: 991px) {
    .block-container { padding: 1rem 1.25rem 2rem !important; }
    .jfl-header-container { padding: 16px !important; margin-bottom: 16px !important; }
    .jfl-header-title { font-size: 18px !important; }
    .jfl-header-meta-box { padding: 8px 12px !important; margin-top: 8px; }
    div[data-testid="stMetricValue"] div { font-size: 22px !important; }
    div[data-testid="stMetric"] { padding: 14px 16px !important; }
    .stTabs [data-baseweb="tab"] { padding: 10px 14px !important; font-size: 11.5px !important; }
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  HARDCODED REPOSITORY PATH DETAILS
# ─────────────────────────────────────────────────────────────
GITHUB_USER = "AayuGo1"
GITHUB_REPO = "plant-dashboard"
GITHUB_BRANCH = "main"

RAW_BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}"

# ─────────────────────────────────────────────────────────────
#  SIDEBAR MANAGEMENT CONTROL DECK
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style="padding:16px 0 20px;">
            <div style="font-size:9px; font-weight:700; letter-spacing:1.8px; color:#94A3B8;
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
                    color:#94A3B8; text-transform:uppercase; margin-bottom:10px;">
                    Pipeline Stream</div>""", unsafe_allow_html=True)
    
    st.info(f"📍 Repository:\n`{GITHUB_USER}/{GITHUB_REPO}`\nBranch: `{GITHUB_BRANCH}`")
    st.markdown("<hr style='border-color:#1E3A8A; margin:14px 0;'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  ADAPTIVE PIPELINE DATE RESOLVER
# ─────────────────────────────────────────────────────────────
def fast_parse_dates(series):
    # Returns series directly if already native excel parsed timestamps
    if pd.api.types.is_datetime64_any_dtype(series):
        return series
    
    cleaned = series.astype(str).str.strip().str.split(' ').str[0]
    
    # Adaptive try-catch strategy to prevent empty rows creation across different sheets
    parsed = pd.to_datetime(cleaned, format="%d-%m-%Y", errors='coerce')
    if parsed.isna().all():
        parsed = pd.to_datetime(cleaned, dayfirst=True, errors='coerce')
    return parsed

@st.cache_data(ttl=60)
def load_temperature_data_from_github():
    api_url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents?per_page=100"
    
    try:
        res = requests.get(api_url)
        if res.status_code != 200:
            return None
        
        file_nodes = res.json()
        target_urls = [node["download_url"] for node in file_nodes if "DataLog_" in node["name"] and node["name"].endswith(".csv")]
        
        if not target_urls:
            return None
            
        cols = ['Time', 'Dough Cooler2 Temp', 'Dough Cooler1 Temp', 'Perishable Cooler Temp']
        frames = []
        
        for url in sorted(target_urls):
            csv_res = requests.get(url)
            if csv_res.status_code == 200:
                df = pd.read_csv(io.StringIO(csv_res.text))
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
    except Exception:
        return None

@st.cache_data(ttl=60)
def load_excel_sheet_from_github(sheet_name, fallback_header_row):
    raw_url = f"{RAW_BASE_URL}/Power%20consumption%20freon.xlsx"
    
    try:
        res = requests.get(raw_url)
        if res.status_code != 200:
            return None
            
        excel_bytes = io.BytesIO(res.content)
        preview = pd.read_excel(excel_bytes, sheet_name=sheet_name, header=None, engine='openpyxl')
        
        hdr = fallback_header_row
        for i in range(min(10, len(preview))):
            row = [str(x).lower() for x in preview.iloc[i].dropna()]
            if any('date' in x or 'stop time' in x for x in row):
                hdr = i; break
                
        df = pd.read_excel(excel_bytes, sheet_name=sheet_name, header=hdr, engine='openpyxl')
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

# Trigger Data Retrieval Engines
temp_df = load_temperature_data_from_github()
power_raw = load_excel_sheet_from_github('Sheet1', fallback_header_row=1)
runtime_raw = load_excel_sheet_from_github('Sheet2', fallback_header_row=2)
comp_raw = load_excel_sheet_from_github('Sheet3', fallback_header_row=3)

# Automatically generate dynamic boundaries from file data logs
min_reporting_date = "01 Jun 2026"
max_reporting_date = "10 Jun 2026"

if power_raw is not None and not power_raw.empty and 'Date' in power_raw.columns:
    parsed_dates = fast_parse_dates(power_raw['Date']).dropna()
    if not parsed_dates.empty:
        min_reporting_date = parsed_dates.min().strftime('%d %b %Y')
        max_reporting_date = parsed_dates.max().strftime('%d %b %Y')

with st.sidebar:
    st.markdown("""<div style="font-size:9px; font-weight:700; letter-spacing:1.2px;
                    color:#94A3B8; text-transform:uppercase; margin-bottom:10px;">
                    Connection Status</div>""", unsafe_allow_html=True)

    st.markdown(f"""
        <div style="margin-bottom:8px;">
            <span class="status-pill status-{'ok' if temp_df is not None else 'err'}">
                {'●' if temp_df is not None else '○'}&nbsp; Temp Logs · Live Git
            </span>
        </div>
        <div>
            <span class="status-pill status-{'ok' if power_raw is not None else 'err'}">
                {'●' if power_raw is not None else '○'}&nbsp; Energy Workbook · Live Git
            </span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style="position:fixed; bottom:18px; left:0; width:238px;
                    text-align:center; font-size:10px; color:#94A3B8;
                    font-weight:600; letter-spacing:0.3px; padding:0 8px;">
            JFL Internal Operations Tool &nbsp;·&nbsp; v2.10
        </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  DYNAMIC EXECUTIVE HEADER SECTION
# ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="jfl-header-container">
    <div style="display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 16px;">
        <div style="flex: 1; min-width: 280px;">
            <div class="jfl-header-subtitle">Supply Chain & Manufacturing · Noida Plant Group</div>
            <div class="jfl-header-title">Plant Operational Intelligence Hub</div>
        </div>
        <div style="display: flex; gap: 12px; flex-wrap: wrap; min-width: 240px;">
            <div class="jfl-header-meta-box" style="flex: 1;">
                <div class="jfl-meta-label">Dynamic Reporting Window</div>
                <div class="jfl-meta-value">{min_reporting_date} – {max_reporting_date}</div>
            </div>
            <div class="jfl-header-meta-box" style="flex: 1; border-top: 1px solid #E2E8F0;">
                <div class="jfl-meta-label">Corporate Entity</div>
                <div class="jfl-meta-value" style="color: #E01934;">Jubilant FoodWorks</div>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- NAVIGATION DECK ---
tab_temp, tab_power, tab_runtime, tab_comp = st.tabs([
    "🌡️  Cold Storage Temperatures",
    "⚡  Energy & Cost Savings",
    "⚙️  Asset Duty Cycles",
    "📉  Compressor Optimisation",
])

# ==============================================================================
#  TAB 1 — COLD STORAGE TEMPERATURES
# ==============================================================================
with tab_temp:
    if temp_df is not None and not temp_df.empty:
        latest = temp_df.iloc[-1]
        sensors = ['Dough Cooler1 Temp', 'Dough Cooler2 Temp', 'Perishable Cooler Temp']
        THRESHOLD = 4.0

        c1, c2, c3, c4 = st.columns([1,1,1,1.2])
        with c1: st.metric("Dough Cooler 1", f"{latest['Dough Cooler1 Temp']:.2f} °C")
        with c2: st.metric("Dough Cooler 2", f"{latest['Dough Cooler2 Temp']:.2f} °C")
        with c3: st.metric("Perishable Store", f"{latest['Perishable Cooler Temp']:.2f} °C")
        with c4:
            total_logs = len(temp_df)
            total_exc = sum((temp_df[s] > THRESHOLD).sum() for s in sensors)
            fleet_compliance = (1 - total_exc / (total_logs * len(sensors))) * 100
            st.metric("Fleet Compliance", f"{fleet_compliance:.1f}%",
                      delta=f"{total_exc} spikes >4.0°C", delta_color="inverse")

        st.markdown('<div class="sec-title">Temperature Trends — Ingestion Stream Logs</div>', unsafe_allow_html=True)
        st.line_chart(temp_df.set_index('Time')[sensors], color=["#002D62", "#0EA5E9", "#E01934"])

        st.markdown('<div class="sec-title">Daily Mean Temperature by Zone</div>', unsafe_allow_html=True)
        temp_df['Date'] = temp_df['Time'].dt.date
        daily_avg = temp_df.groupby('Date')[sensors].mean().round(2)
        daily_avg.index = daily_avg.index.astype(str)
        st.bar_chart(daily_avg, color=["#002D62", "#0EA5E9", "#E01934"])

        st.markdown('<div class="sec-title">Cold-Chain Thermodynamic Stability Audits</div>', unsafe_allow_html=True)
        labels = {
            'Dough Cooler1 Temp': 'Dough Cooler 1',
            'Dough Cooler2 Temp': 'Dough Cooler 2',
            'Perishable Cooler Temp': 'Perishable Storage',
        }
        rows = []
        for col in sensors:
            s = temp_df[col]
            n = len(s)
            exc = int((s > THRESHOLD).sum())
            comp = ((n - exc) / n)
            rows.append({
                "Asset Node": labels[col],
                "Total Logs": n,
                "Mean Temp": s.mean(),
                "Minimum Temp": s.min(),
                "Maximum Temp": s.max(),
                "Stability (σ)": s.std(),
                "Excursions": exc,
                "Compliance Index": comp,
            })

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Total Logs": st.column_config.NumberColumn(format="%d entries"),
                "Mean Temp": st.column_config.NumberColumn(format="%.2f °C"),
                "Minimum Temp": st.column_config.NumberColumn(format="%.2f °C"),
                "Maximum Temp": st.column_config.NumberColumn(format="%.2f °C"),
                "Stability (σ)": st.column_config.NumberColumn(format="%.2f σ"),
                "Excursions": st.column_config.NumberColumn(format="%d counts"),
                "Compliance Index": st.column_config.ProgressColumn(format="%.1f%%", min_value=0.0, max_value=1.0)
            }
        )

        st.markdown('<div class="sec-title">Zone Alert Flags</div>', unsafe_allow_html=True)
        for col in sensors:
            exc = int((temp_df[col] > THRESHOLD).sum())
            comp = ((len(temp_df) - exc) / len(temp_df)) * 100
            label = labels[col]
            if comp >= 95:
                st.markdown(f'<div class="alert-ok">✓ <strong>{label}</strong> — Stable baseline at {comp:.1f}% compliance. {exc} minor variations logged.</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="alert-warn">⚠ <strong>{label}</strong> — High load drift at {comp:.1f}% compliance. {exc} critical spikes above 4.0°C.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-info"><strong>No log records detected.</strong> Push data targets directly to your root GitHub tree to populate layouts.</div>', unsafe_allow_html=True)

# ==============================================================================
#  TAB 2 — ENERGY & COST SAVINGS
# ==============================================================================
with tab_power:
    if power_raw is not None and not power_raw.empty:
        p = power_raw.copy()
        p['Date'] = fast_parse_dates(p['Date'])
        p = p.dropna(subset=['Date']).sort_values('Date')
        p['Dunkin Blast'] = pd.to_numeric(p['Dunkin Blast'], errors='coerce').fillna(0)
        p['CLC Blast'] = pd.to_numeric(p['CLC Blast'], errors='coerce').fillna(0)
        
        savings_title = next((c for c in p.columns if 'saving' in str(c).lower()), 'Savings')
        p[savings_title] = pd.to_numeric(p[savings_title], errors='coerce').fillna(0)
        p = p[p['Dunkin Blast'] < 500_000].copy()

        if not p.empty:
            st.markdown('### 🎛️ Dynamic Scope Selector')
            min_d, max_d = p['Date'].min().date(), p['Date'].max().date()
            sel_dates = st.slider("Target Timeline Range Window", min_value=min_d, max_value=max_d, value=(min_d, max_d), key="power_slider")
            
            p_filtered = p[(p['Date'].dt.date >= sel_dates[0]) & (p['Date'].dt.date <= sel_dates[1])]

            dunkin_tot = p_filtered['Dunkin Blast'].sum()
            clc_tot = p_filtered['CLC Blast'].sum()
            sav_tot = p_filtered[savings_title].sum()
            avg_daily_savings = p_filtered[savings_title].mean()

            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Dunkin' Blast Volume", f"{dunkin_tot:,.0f} kWh")
            with c2: st.metric("CLC Blast Volume", f"{clc_tot:,.0f} kWh")
            with c3: st.metric("Combined Grid Demand", f"{dunkin_tot+clc_tot:,.0f} kWh")
            with c4: st.metric("Net Financial Recovery", f"₹ {sav_tot:,.2f}", 
                               delta=f"₹{avg_daily_savings:,.2f}/day Avg", delta_color="normal")

            st.markdown('<div class="sec-title">Operational Load Profiling Trends (kWh Stacked Area)</div>', unsafe_allow_html=True)
            st.area_chart(p_filtered.set_index('Date')[['Dunkin Blast', 'CLC Blast']], color=["#002D62", "#FF9F1C"])

            st.markdown('<div class="sec-title">Daily Scaled Cost Recovery Outlays (₹)</div>', unsafe_allow_html=True)
            st.bar_chart(p_filtered.set_index('Date')[savings_title], color="#16A34A")
    else:
        st.markdown('<div class="alert-info">Excel sheet workbook unmapped or missing from GitHub branch root.</div>', unsafe_allow_html=True)

# ==============================================================================
#  TAB 3 — ASSET DUTY CYCLES
# ==============================================================================
with tab_runtime:
    if runtime_raw is not None and not runtime_raw.empty:
        r = runtime_raw.copy()
        fc = r.columns[0]
        r = r[~r[fc].astype(str).str.contains('Date|From|Total|Running', case=False, na=False)]
        r[fc] = fast_parse_dates(r[fc])
        r = r.dropna(subset=[fc]).sort_values(fc)

        kwh_cols = [c for c in r.columns if 'KWH' in str(c).upper()]
        for col in kwh_cols:
            r[col] = pd.to_numeric(r[col], errors='coerce').fillna(0)

        if kwh_cols and not r.empty:
            st.markdown('### ⚙️ Plant Capacity & Loading Factor Status')
            primary_col = kwh_cols[0]

            c1, c2, c3 = st.columns(3)
            with c1: st.metric("Aggregated Fleet Consumption", f"{r[primary_col].sum():,.0f} kWh")
            with c2: st.metric("Peak Stress Loading Point", f"{r[primary_col].max():,.0f} kWh")
            with c3: st.metric("Mean Continuous Daily Load", f"{r[primary_col].mean():,.0f} kWh")

            st.markdown('<div class="sec-title">Asset Loading Factor Indexes (% of Peak Capacity Recorded)</div>', unsafe_allow_html=True)
            for col in kwh_cols[:5]:
                col_max = r[col].max()
                col_avg = r[col].mean()
                load_factor = (col_avg / col_max) if col_max > 0 else 0.0
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.markdown(f"**{col}** \n`Avg: {col_avg:.1f} kWh / Max: {col_max:.1f} kWh`")
                with col2:
                    st.progress(min(float(load_factor), 1.0), text=f"Calculated Operational Loading: {load_factor*100:.1f}%")

            st.markdown(f'<div class="sec-title">Continuous Capacity Displacement Analytics Profile ({primary_col})</div>', unsafe_allow_html=True)
            st.bar_chart(r.set_index(fc)[primary_col], color="#002D62")
    else:
        st.markdown('<div class="alert-info">Asset loading log entries unmapped or missing from GitHub.</div>', unsafe_allow_html=True)

# ==============================================================================
#  TAB 4 — COMPRESSOR OPTIMISATION
# ==============================================================================
with tab_comp:
    if comp_raw is not None and not comp_raw.empty:
        c = comp_raw.copy()
        
        # Remove description rows safely
        c = c[~c.iloc[:, 0].astype(str).str.strip().str.lower().str.fullmatch(r'date|total|from|sr\.?\s*no\.?|stop|start', na=False)]
        c.iloc[:, 0] = fast_parse_dates(c.iloc[:, 0])
        c = c.dropna(subset=[c.columns[0]]).sort_values(c.columns[0])

        sav_col = next((col for col in c.columns if 'saving' in str(col).lower()), None)

        if sav_col and not c.empty:
            c[sav_col] = pd.to_numeric(c[sav_col], errors='coerce').fillna(0)
            c['Progressive Running Accumulation'] = c[sav_col].cumsum()

            k1, k2, k3, k4 = st.columns(4)
            with k1: st.metric("Optimized Interlock Rest Hours", f"{c[sav_col].sum():,.1f} hrs")
            with k2: st.metric("Mean Relief Window", f"{c[sav_col].mean():,.1f} hrs/day")
            with k3: st.metric("Peak Machine Rest Segment", f"{c[sav_col].max():,.1f} hrs")
            with k4: st.metric("Total Automated Audited Cycles", f"{len(c)}")

            date_col = c.columns[0]

            gc1, gc2 = st.columns(2)
            with gc1:
                st.markdown('<div class="sec-title">Daily Gaps & Cycle Interruptions (Hours)</div>', unsafe_allow_html=True)
                st.line_chart(c.set_index(date_col)[sav_col], color="#002D62")
            with gc2:
                st.markdown('<div class="sec-title">Cumulative Mechanical Fleet Stress Reduction (Rest Hours Sum)</div>', unsafe_allow_html=True)
                st.area_chart(c.set_index(date_col)['Progressive Running Accumulation'], color="#FF9F1C")

            st.markdown('<div class="sec-title">Asset Operational Degradation Risk Ranking (Cycle Counts)</div>', unsafe_allow_html=True)
            comp_metrics = {}
            max_possible_loops = min(5, len(c.columns) // 2)
            
            for idx in range(1, max_possible_loops + 1):
                stop_key = c.columns[2 * idx - 1]
                active_events = c[c[stop_key].notna() & (c[stop_key].astype(str).str.strip() != '')]
                comp_metrics[f"Compressor Unit {idx}"] = len(active_events)
            
            if comp_metrics:
                comp_chart_df = pd.DataFrame(list(comp_metrics.items()), columns=["Asset Component Node", "Trigger Cycle Volume"])
                comp_chart_df = comp_chart_df.sort_values(by="Trigger Cycle Volume", ascending=False)
                st.bar_chart(comp_chart_df.set_index("Asset Component Node")["Trigger Cycle Volume"], color="#E01934")
        else:
            st.markdown('<div class="alert-warn">Optimization layout index column variant or empty lines encountered inside Sheet 3 framework.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-info">Compressor statistics ledger unmapped or missing from GitHub.</div>', unsafe_allow_html=True)
