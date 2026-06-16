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
# GITHUB SYSTEM CONFIGURATION
# ─────────────────────────────────────────────────────────────
GITHUB_USER   = "AayuGo1"
GITHUB_REPO   = "plant-dashboard"
GITHUB_BRANCH = "main"
GITHUB_FOLDER = ""

RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}"
API_BASE = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents?ref={GITHUB_BRANCH}"

# ─────────────────────────────────────────────────────────────
# RUNTIME UI STRUCTURAL INJECTIONS
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="JFL – Plant Operations Hub",
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
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# COMPONENT FILE FETCH ENGINE
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def list_github_files():
    try:
        r = requests.get(API_BASE, timeout=10)
        r.raise_for_status()
        return [(f["name"], f["download_url"]) for f in r.json() if isinstance(f, dict) and "name" in f and "download_url" in f]
    except Exception as e:
        st.sidebar.error(f"GitHub pipeline disruption: {e}")
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
# INGESTION PIPELINES WITH BUILT-IN DATA CLEANING
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
        df = read_csv_from_github(url) if name.endswith(".csv") else read_excel_from_github(url)
        df = df[~df.iloc[:, 0].astype(str).str.contains(r'source|v1|Date|consump', case=False, na=False)]
        df.columns = [str(c).strip() for c in df.columns]
        
        date_col = next((c for c in df.columns if c.lower() in ['date', 'timestamp', 'time']), None)
        if not date_col: return None
            
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
        
        # Backfill raw delta calculations
        for i in range(1, 10):
            consump_col = f"consump. v{i}"
            reg_col = f"V{i}"
            if consump_col in df.columns and reg_col in df.columns:
                computed_diff = df[reg_col].diff()
                df[consump_col] = df.apply(
                    lambda row: computed_diff.loc[row.name] if (pd.isna(row[consump_col]) or row[consump_col] == 0) and pd.notna(computed_diff.loc[row.name]) and computed_diff.loc[row.name] > 0 else row[consump_col],
                    axis=1
                )
        return df
    except Exception as e:
        st.sidebar.error(f"Inference failure on energy data: {e}")
        return None

@st.cache_data(ttl=300)
def load_temperature_data():
    all_files = list_github_files()
    csv_files = [(n, u) for n, u in all_files if n.startswith("DataLog_") and n.endswith(".csv")]
    if not csv_files: return None

    frames = []
    for name, url in sorted(csv_files):
        try:
            df = read_csv_from_github(url)
            df.columns = [str(c).strip() for c in df.columns]
            
            time_col = next((c for c in df.columns if 'time' in c.lower()), None)
            c1_col = next((c for c in df.columns if 'cooler1' in c.lower().replace(" ", "")), None)
            c2_col = next((c for c in df.columns if 'cooler2' in c.lower().replace(" ", "")), None)
            p_col = next((c for c in df.columns if 'perishable' in c.lower()), None)
            
            if not all([time_col, c1_col, c2_col, p_col]): continue
                
            sub = df[[time_col, c1_col, c2_col, p_col]].copy()
            sub = sub.rename(columns={time_col: 'Time', c1_col: 'Dough Cooler1 Temp', c2_col: 'Dough Cooler2 Temp', p_col: 'Perishable Cooler Temp'})
            
            for c in ['Dough Cooler1 Temp', 'Dough Cooler2 Temp', 'Perishable Cooler Temp']:
                sub[c] = pd.to_numeric(sub[c].astype(str).str.strip(), errors='coerce').ffill().bfill()
                
            sub['Time'] = pd.to_datetime(sub['Time'], dayfirst=True, errors='coerce')
            frames.append(sub)
        except Exception:
            continue

    if not frames: return None
    combined = pd.concat(frames, ignore_index=True).dropna(subset=['Time']).drop_duplicates(subset=['Time']).sort_values('Time').reset_index(drop=True)
    
    for suffix in ['dough1', 'dough2', 'perishable']:
        src = 'Dough Cooler1 Temp' if suffix=='dough1' else 'Dough Cooler2 Temp' if suffix=='dough2' else 'Perishable Cooler Temp'
        combined[f'consump. {suffix}'] = combined[src].diff().fillna(0)
    return combined

@st.cache_data(ttl=300)
def load_excel_sheet(sheet_name, fallback_header_row):
    all_files = list_github_files()
    match = next((u for n, u in all_files if "freon" in n.lower() and n.endswith(".xlsx")), None)
    if not match: return None
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
        df.columns = [str(c).strip() for c in df.columns]
        
        if sheet_name == 'Sheet3':
            if len(df.columns) >= 12: df.columns.values[11] = 'Saving in hrs'
            elif 'unnamed' in str(df.columns[-1]).lower(): df = df.rename(columns={df.columns[-1]: 'Saving in hrs'})
                
        df = df[df[df.columns[0]].astype(str).str.strip().str.lower() != 'total']
        return df
    except Exception:
        return None

# ─────────────────────────────────────────────────────────────
# DATA INITIALIZATION ENTRY
# ─────────────────────────────────────────────────────────────
e_df = load_processed_energy_data()
temp_df = load_temperature_data()
comp_df = load_excel_sheet('Sheet3', fallback_header_row=3)

# ==============================================================================
# VIEW SYSTEM METRIC PRESENTATION LAYER
# ==============================================================================
# ACTIVE ENERGY METERS TAB
with tab_energy:
    if e_df is not None and not e_df.empty:
        consump_cols = [c for c in e_df.columns if 'consump. v' in c.lower()]
        eq_cols = [c for c in ['dunkin consmp.', 'clc consmp.', 'bmc consmp.', 'deep consumption'] if c in e_df.columns]

        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Observed Optimization Span", f"{len(e_df)} Days")
        with c2: st.metric("Aggregate Network Ingestion", f"{e_df[consump_cols].sum().sum():,.1f} kWh" if consump_cols else "Insufficient evidence from dataset")
        with c3: st.metric("Active Distribution Channels", f"{len(consump_cols)} Functional V-Nodes")

        if consump_cols:
            st.markdown('<div class="sec-title">Linear Allocation Log — V-Channel Network Profile</div>', unsafe_allow_html=True)
            fig = go.Figure()
            x_dates = e_df['DateIndex'].dt.strftime('%d-%b').tolist()
            for col in consump_cols:
                fig.add_trace(go.Scatter(x=x_dates, y=e_df[col].tolist(), mode='lines+markers', name=col))
            fig.update_layout(hovermode="x unified", height=380, margin=dict(l=20, r=20, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown('<div class="alert-info">Insufficient evidence from dataset to generate Active Energy profiles.</div>', unsafe_allow_html=True)

# COLD STORAGE TEMPERATURES TAB
with tab_temp:
    if temp_df is not None and not temp_df.empty:
        sensors = ['Dough Cooler1 Temp', 'Dough Cooler2 Temp', 'Perishable Cooler Temp']
        latest = temp_df.iloc[-1]
        
        tc1, tc2, tc3 = st.columns(3)
        with tc1: st.metric("Dough Cooler Node 1", f"{latest['Dough Cooler1 Temp']:.2f} °C")
        with tc2: st.metric("Dough Cooler Node 2", f"{latest['Dough Cooler2 Temp']:.2f} °C")
        with tc3: 
            violations = sum((temp_df[s] > 4.0).sum() for s in sensors)
            compliance = (1 - (violations / (len(temp_df) * len(sensors)))) * 100
            st.metric("Thermal Retention Index", f"{compliance:.1f}%", delta=f"{violations} Out-of-Bounds Exceptions", delta_color="inverse")

        st.markdown('<div class="sec-title">High-Density Real-Time Thermal Feedback Loop Stream</div>', unsafe_allow_html=True)
        st.line_chart(temp_df.set_index('Time')[sensors], color=["#002D62","#0EA5E9","#E01934"])
    else:
        st.markdown('<div class="alert-info">Insufficient evidence from dataset to compile real-time environment logs.</div>', unsafe_allow_html=True)

# ENERGY & COST SAVINGS TAB
with tab_power:
    power_df = load_excel_sheet('Sheet1', fallback_header_row=1)
    if power_df is not None and not power_df.empty:
        p = power_df.copy()
        p['Date'] = fast_parse_dates(p['Date'])
        p = p.dropna(subset=['Date']).sort_values('Date')
        
        dunkin_col = next((c for c in p.columns if 'dunkin' in c.lower()), None)
        clc_col = next((c for c in p.columns if 'clc' in c.lower()), None)
        sav_col = next((c for c in p.columns if 'saving' in str(c).lower()), None)
        
        if dunkin_col and clc_col:
            p[dunkin_col] = pd.to_numeric(p[dunkin_col], errors='coerce').fillna(0)
            p[clc_col] = pd.to_numeric(p[clc_col], errors='coerce').fillna(0)
            
            pc1, pc2 = st.columns(2)
            with pc1: st.metric("Substation Area Draw (Combined Blast)", f"{p[dunkin_col].sum() + p[clc_col].sum():,.0f} kWh")
            with pc2: 
                val_str = f"₹ {p[sav_col].sum():,.2f}" if sav_col else "Insufficient evidence from dataset"
                st.metric("Financial Recovery Component Metric", val_str)
                
            st.markdown('<div class="sec-title">Daily Power Footprint Area Analysis (kWh)</div>', unsafe_allow_html=True)
            st.area_chart(p.set_index('Date')[[dunkin_col, clc_col]], color=["#002D62","#FF9F1C"])
    else:
        st.markdown('<div class="alert-info">Insufficient evidence from dataset to process Worksheet 1 Grid Recovery records.</div>', unsafe_allow_html=True)

# ASSET DUTY CYCLES TAB
with tab_runtime:
    runtime_df = load_excel_sheet('Sheet2', fallback_header_row=2)
    if runtime_df is not None and not runtime_df.empty:
        r = runtime_df.copy()
        fc = r.columns[0]
        r = r[~r[fc].astype(str).str.contains('Date|From|Total|Running', case=False, na=False)]
        r[fc] = fast_parse_dates(r[fc])
        r = r.dropna(subset=[fc]).sort_values(fc)
        
        kwh_cols = [c for c in r.columns if 'KWH' in str(c).upper()]
        if kwh_cols:
            r[kwh_cols[0]] = pd.to_numeric(r[kwh_cols[0]], errors='coerce').fillna(0)
            st.markdown('<div class="sec-title">Daily Mechanical Displacement Volume Profile (Gross kWh Intake)</div>', unsafe_allow_html=True)
            st.bar_chart(r.set_index(fc)[kwh_cols[0]], color="#002D62")
    else:
        st.markdown('<div class="alert-info">Insufficient evidence from dataset to extract primary asset indicators.</div>', unsafe_allow_html=True)

# ADVANCED COMPRESSOR DIAGNOSTICS TAB
with tab_comp:
    if comp_df is not None and not comp_df.empty and temp_df is not None and not temp_df.empty:
        st.markdown('<div class="sec-title">🛠️ Advanced Cross-Tab System Diagnostic Engine</div>', unsafe_allow_html=True)
        
        c_clean = comp_df.copy()
        c_clean = c_clean[~c_clean.iloc[:,0].astype(str).str.strip().str.lower().str.fullmatch(r'date|total|from|sr\.?\s*no\.?|stop|start', na=False)]
        c_clean.iloc[:,0] = pd.to_datetime(c_clean.iloc[:,0], errors='coerce')
        c_clean = c_clean.dropna(subset=[c_clean.columns[0]]).sort_values(c_clean.columns[0])
        
        sav_col = next((col for col in c_clean.columns if 'saving' in str(col).lower()), None)
        date_col = c_clean.columns[0]
        
        if sav_col:
            c_clean[sav_col] = pd.to_numeric(c_clean[sav_col], errors='coerce').fillna(0)
            
            # Aggregate structural downtime frames
            daily_compressor_rest = c_clean.groupby(c_clean[date_col].dt.date)[sav_col].sum().reset_index()
            daily_compressor_rest.columns = ['Date', 'Rest_Hours']
            daily_compressor_rest['Date'] = pd.to_datetime(daily_compressor_rest['Date'])
            
            # Extract case-insensitive target thermal column
            t_clean = temp_df.copy()
            t_clean['Date'] = pd.to_datetime(t_clean['Time']).dt.date
            dough1_col = next((col for col in t_clean.columns if 'cooler1' in col.lower().replace(" ", "")), None)
            
            if dough1_col:
                daily_thermal = t_clean.groupby('Date').agg(Mean_Dough1=(dough1_col, 'mean')).reset_index()
                daily_thermal['Date'] = pd.to_datetime(daily_thermal['Date'])
                
                diagnostic_matrix = pd.merge(daily_compressor_rest, daily_thermal, on='Date', how='inner')
                
                if not diagnostic_matrix.empty:
                    st.markdown("""
                        <div class='alert-info'>
                            <strong>Diagnostic Framework Summary:</strong> This advanced visualization correlates mechanical rest sequences 
                            against the baseline thermal drift of your cold storage units. A rising temperature line during extended rest windows 
                            indicates a potential insulation leak or an overloaded structural envelope.
                        </div>
                    """, unsafe_allow_html=True)
                    
                    fig_diagnostic = make_subplots(specs=[[{"secondary_y": True}]])
                    x_labels = diagnostic_matrix['Date'].dt.strftime('%d-%b').tolist()
                    
                    fig_diagnostic.add_trace(
                        go.Bar(x=x_labels, y=diagnostic_matrix['Rest_Hours'].tolist(), name="Isolation Window (Hours)", marker_color='#002D62', opacity=0.8),
                        secondary_y=False
                    )
                    fig_diagnostic.add_trace(
                        go.Scatter(x=x_labels, y=diagnostic_matrix['Mean_Dough1'].tolist(), mode='lines+markers', name="Mean Temperature Vector (°C)", line=dict(color='#E01934', width=3)),
                        secondary_y=True
                    )
                    
                    fig_diagnostic.update_layout(hovermode="x unified", margin=dict(l=40, r=40, t=20, b=20), height=400, legend=dict(orientation="h", y=1.1))
                    fig_diagnostic.update_yaxes(title_text="<b>Rest Allocations</b> (Hours/Day)", secondary_y=False)
                    fig_diagnostic.update_yaxes(title_text="<b>Thermodynamic Drift</b> (°C)", secondary_y=True)
                    st.plotly_chart(fig_diagnostic, use_container_width=True)
            else:
                st.markdown('<div class="alert-warn">Insufficient evidence from dataset: Unable to resolve core tracking columns for Dough Cooler 1.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-info">Insufficient evidence from dataset: Missing required data hooks to unlock advanced diagnostics.</div>', unsafe_allow_html=True)
