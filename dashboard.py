import os
import re
import io
import warnings
import requests
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, time as dt_time
from copy import deepcopy

warnings.filterwarnings("ignore", category=UserWarning)

# ─────────────────────────────────────────────────────────────
#  1. CENTRALIZED CONFIGURATION
# ─────────────────────────────────────────────────────────────
class Config:
    GITHUB_USER = "AayuGo1"
    GITHUB_REPO = "plant-dashboard"
    GITHUB_BRANCH = "main"
    API_BASE = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents?ref={GITHUB_BRANCH}"
    
    COLORS = {
        'primary': '#002D62', 'accent': '#E01934', 'success': '#16A34A',
        'warning': '#F59E0B', 'info': '#3B82F6', 'dark': '#0F172A',
        'gray': '#64748B', 'light_gray': '#E2E8F0', 'bg': '#F4F6F9'
    }
    
    # Base Plotly Layout Template
    PLOTLY_LAYOUT = dict(
        font=dict(family='Inter, Segoe UI, sans-serif', color='#0F172A', size=12),
        plot_bgcolor='rgba(0,0,0,0)', 
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=60, r=20, t=50, b=60),
        hoverlabel=dict(font_size=12, bgcolor='white', bordercolor='#E2E8F0'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, bgcolor='rgba(255,255,255,0.9)'),
        xaxis=dict(gridcolor='#E2E8F0', zerolinecolor='#E2E8F0', titlefont=dict(size=13)),
        yaxis=dict(gridcolor='#E2E8F0', zerolinecolor='#E2E8F0', titlefont=dict(size=13))
    )

# ─────────────────────────────────────────────────────────────
#  2. ENTERPRISE CSS INJECTION
# ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="JFL – Plant Operations Dashboard", page_icon="🏭", layout="wide", initial_sidebar_state="auto")

st.markdown("""
<style>
:root {
    --jfl-primary: #002D62; --jfl-accent: #E01934; --jfl-success: #16A34A;
    --jfl-warning: #F59E0B; --jfl-info: #3B82F6; --jfl-bg: #F4F6F9;
    --jfl-card-bg: #FFFFFF; --jfl-text-main: #0F172A; --jfl-text-muted: #64748B; --jfl-border: #E2E8F0;
}
html, body, [class*="css"] { font-family: 'Inter', 'Segoe UI', sans-serif; color: var(--jfl-text-main); }
.block-container { padding: 1.5rem 2.5rem 3rem; background: var(--jfl-bg); max-width: 1440px; }

section[data-testid="stSidebar"] { background: linear-gradient(180deg, #001840 0%, #002D62 100%) !important; border-right: none !important; }
section[data-testid="stSidebar"] * { color: #CBD5E0 !important; }
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 { color: #FFFFFF !important; }
section[data-testid="stSidebar"] .stButton>button { background: var(--jfl-accent); color: white; border: none; font-weight: 700; width: 100%; }

.jfl-header-container { background: var(--jfl-card-bg); border-radius: 12px; padding: 28px 32px; margin-bottom: 28px; border: 1px solid var(--jfl-border); border-left: 8px solid var(--jfl-accent); box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px; }
.jfl-header-title { font-size: 26px; font-weight: 800; color: var(--jfl-primary); letter-spacing: -0.5px; }
.jfl-header-subtitle { font-size: 11px; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; color: var(--jfl-text-muted); margin-bottom: 4px; }
.jfl-header-meta-box { background: #F8FAFC; border: 1px solid var(--jfl-border); border-radius: 8px; padding: 12px 18px; min-width: 160px; }
.jfl-meta-label { font-size: 9px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; color: var(--jfl-text-muted); margin-bottom: 4px; }
.jfl-meta-value { font-size: 14px; font-weight: 800; color: var(--jfl-primary); }

.kpi-card { background: var(--jfl-card-bg); border: 1px solid var(--jfl-border); border-radius: 10px; padding: 20px 24px; box-shadow: 0 2px 4px rgba(0,0,0,0.03); border-left: 5px solid var(--jfl-primary); transition: all 0.2s ease; height: 100%; }
.kpi-card:hover { transform: translateY(-3px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.08); }
.kpi-label { font-size: 11px; font-weight: 700; color: var(--jfl-text-muted); text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 8px; }
.kpi-value { font-size: 28px; font-weight: 800; color: var(--jfl-text-main); line-height: 1.2; }
.kpi-delta { font-size: 12px; font-weight: 600; color: var(--jfl-text-muted); margin-top: 8px; }

.sec-title { font-size: 13px; font-weight: 700; color: var(--jfl-text-muted); text-transform: uppercase; letter-spacing: 1.2px; margin: 32px 0 16px 0; padding-bottom: 10px; border-bottom: 2px solid var(--jfl-border); display: flex; align-items: center; gap: 8px; }

.alert-box { border-radius: 8px; padding: 14px 18px; font-size: 13.5px; font-weight: 500; margin-bottom: 16px; border-left: 5px solid; display: flex; align-items: center; gap: 10px; }
.alert-ok { background: #F0FDF4; border-color: var(--jfl-success); color: #14532D; }
.alert-warn { background: #FFFBEB; border-color: var(--jfl-warning); color: #92400E; }
.alert-info { background: #EFF6FF; border-color: var(--jfl-info); color: #1E3A8A; }

.stTabs [data-baseweb="tab-list"] { gap: 0; background: var(--jfl-card-bg); border-bottom: 2px solid var(--jfl-border); padding: 0 12px; border-radius: 10px 10px 0 0; }
.stTabs [data-baseweb="tab"] { background: transparent; border: none; border-bottom: 3px solid transparent; padding: 16px 24px; font-size: 13px; font-weight: 700; color: var(--jfl-text-muted); transition: all 0.2s ease; }
.stTabs [data-baseweb="tab"]:hover { color: var(--jfl-primary); }
.stTabs [data-baseweb="tab"][aria-selected="true"] { color: var(--jfl-primary) !important; border-bottom: 3px solid var(--jfl-accent) !important; background: transparent !important; }

.status-pill { display: inline-block; padding: 5px 12px; border-radius: 20px; font-size: 11px; font-weight: 700; }
.status-ok { background:#D1FAE5; color:#065F46; border:1px solid #A7F3D0; }
.status-err { background:#FEE2E2; color:#991B1B; border:1px solid #FCA5A5; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  3. UI BUILDERS (Reusable Components)
# ─────────────────────────────────────────────────────────────
class UIBuilder:
    @staticmethod
    def section_header(title, icon="📊"):
        return f'<div class="sec-title">{icon} {title}</div>'
        
    @staticmethod
    def alert(message, alert_type="info"):
        classes = {"info": "alert-info", "warn": "alert-warn", "ok": "alert-ok"}
        icons = {"info": "ℹ️", "warn": "⚠️", "ok": "✅"}
        return f'<div class="alert-box {classes.get(alert_type, "alert-info")}">{icons.get(alert_type, "")} <span>{message}</span></div>'
        
    @staticmethod
    def kpi_card(label, value, delta=None, color="#002D62"):
        delta_html = f'<div class="kpi-delta">{delta}</div>' if delta else ''
        return f"""
        <div class="kpi-card" style="border-left-color: {color};">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {delta_html}
        </div>
        """

# ─────────────────────────────────────────────────────────────
#  4. AUTOMATED FILE INGESTION PIPELINE
# ─────────────────────────────────────────────────────────────
class FileIngestionPipeline:
    def __init__(self):
        self.patterns = {
            'energy': re.compile(r'PROCESSED_DAILY_VARS_Active_Energy_Report', re.IGNORECASE),
            'temperature': re.compile(r'DataLog_.*\.csv', re.IGNORECASE),
            'freon': re.compile(r'freon.*\.xlsx', re.IGNORECASE)
        }
        
    @staticmethod
    @st.cache_data(ttl=300)
    def discover_files():
        try:
            r = requests.get(Config.API_BASE, timeout=10)
            r.raise_for_status()
            return [(f["name"], f["download_url"]) for f in r.json() if isinstance(f, dict) and "name" in f and "download_url" in f]
        except Exception as e:
            st.sidebar.error(f"GitHub connection issue: {e}")
            return []
            
    def categorize_files(self, files):
        categorized = {k: [] for k in self.patterns}
        categorized['unknown'] = []
        for name, url in files:
            matched = False
            for category, pattern in self.patterns.items():
                if pattern.search(name):
                    categorized[category].append((name, url))
                    matched = True
                    break
            if not matched:
                categorized['unknown'].append((name, url))
        return categorized

# ─────────────────────────────────────────────────────────────
#  5. DATA PROCESSING & CACHING LAYER
# ─────────────────────────────────────────────────────────────
class DataProcessor:
    @staticmethod
    @st.cache_data(ttl=300)
    def fetch_file_bytes(url: str) -> bytes:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r.content

    @staticmethod
    def read_excel_from_github(url: str, **kwargs):
        return pd.read_excel(io.BytesIO(DataProcessor.fetch_file_bytes(url)), **kwargs)

    @staticmethod
    def read_csv_from_github(url: str, **kwargs):
        return pd.read_csv(io.BytesIO(DataProcessor.fetch_file_bytes(url)), **kwargs)

    @staticmethod
    @st.cache_data(ttl=300)
    def load_processed_energy_data():
        pipeline = FileIngestionPipeline()
        files = pipeline.discover_files()
        categorized = pipeline.categorize_files(files)
        target_files = categorized.get('energy', [])
        
        if not target_files: return None
        name, url = sorted(target_files)[-1]
        
        try:
            if name.endswith(".csv"):
                df = DataProcessor.read_csv_from_github(url)
            else:
                raw_df = DataProcessor.read_excel_from_github(url, header=None)
                header_row_idx = 0
                for i, row in raw_df.iterrows():
                    if any('date' in str(x).lower() for x in row if pd.notna(x)):
                        header_row_idx = i
                        break
                df = DataProcessor.read_excel_from_github(url, header=header_row_idx)
                
            df.columns = [str(c).strip() for c in df.columns]
            date_col = next((c for c in df.columns if 'date' in c.lower()), None)
            if not date_col:
                if pd.api.types.is_datetime64_any_dtype(df.iloc[:,0]) or '2026' in str(df.iloc[0,0]):
                    date_col = df.columns[0]
                    df.rename(columns={date_col: 'Date'}, inplace=True)
                    date_col = 'Date'
                else: return None

            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df = df.dropna(subset=[date_col]).sort_values(by=date_col).reset_index(drop=True)
            if df.empty: return None

            register_cols = []
            for i in range(1, 10):
                v_col = f"V{i}"
                matched_v = next((c for c in df.columns if c.upper() == v_col.upper() or c.startswith(f"V{i} ")), None)
                if matched_v: register_cols.append(matched_v)
                    
            calculated_consumption = {}
            for reg_col in register_cols:
                v_num = next((i for i in range(1, 10) if f"V{i}" in reg_col.upper()), None)
                if v_num:
                    diffs = df[reg_col].diff().where(lambda x: x >= 0, other=np.nan)
                    calculated_consumption[f'calc_consump_v{v_num}'] = diffs.fillna(0)
                    
            for col_name, series in calculated_consumption.items():
                df[col_name] = series
                
            def get_zone_consumption(v_nums):
                total = pd.Series(np.zeros(len(df)), index=df.index)
                for v in v_nums:
                    col = f'calc_consump_v{v}'
                    if col in df.columns: total += df[col]
                return total
                
            df['Dunkin Consumption'] = get_zone_consumption([1, 6])
            df['CLC Consumption'] = get_zone_consumption([3, 8])
            df['BMC Consumption'] = get_zone_consumption([2, 7])
            df['Deep Consumption'] = get_zone_consumption([4, 5, 9])
            
            for i in range(1, 10):
                df[f'V{i}_Consumption'] = df.get(f'calc_consump_v{i}', pd.Series(0, index=df.index))

            return df
        except Exception as e:
            st.sidebar.error(f"Failed parsing processed energy file {name}: {e}")
            return None

    @staticmethod
    @st.cache_data(ttl=300)
    def load_temperature_data():
        pipeline = FileIngestionPipeline()
        files = pipeline.discover_files()
        categorized = pipeline.categorize_files(files)
        csv_files = categorized.get('temperature', [])
        
        if not csv_files: return None
        frames = []
        for name, url in sorted(csv_files):
            try:
                df = DataProcessor.read_csv_from_github(url)
                df.columns = [str(c).strip() for c in df.columns]
                time_col = next((c for c in df.columns if 'time' in c.lower()), None)
                c1_col = next((c for c in df.columns if 'cooler1' in c.lower().replace(" ", "")), None)
                c2_col = next((c for c in df.columns if 'cooler2' in c.lower().replace(" ", "")), None)
                p_col = next((c for c in df.columns if 'perishable' in c.lower()), None)
                
                if not all([time_col, c1_col, c2_col, p_col]): continue
                sub = df[[time_col, c1_col, c2_col, p_col]].copy().rename(columns={
                    time_col: 'Time', c1_col: 'Dough Cooler1 Temp', c2_col: 'Dough Cooler2 Temp', p_col: 'Perishable Cooler Temp'
                })
                for c in ['Dough Cooler1 Temp', 'Dough Cooler2 Temp', 'Perishable Cooler Temp']:
                    sub[c] = pd.to_numeric(sub[c].astype(str).str.strip(), errors='coerce').ffill().bfill()
                sub['Time'] = pd.to_datetime(sub['Time'], dayfirst=True, errors='coerce')
                frames.append(sub)
            except Exception as e:
                st.warning(f"Skipped template anomalies on {name}: {e}")

        if not frames: return None
        combined = pd.concat(frames, ignore_index=True).dropna(subset=['Time']).drop_duplicates(subset=['Time']).sort_values('Time').reset_index(drop=True)
        combined['consump. dough1'] = (combined['Dough Cooler1 Temp'] - combined['Dough Cooler1 Temp'].shift(1)).fillna(0)
        combined['consump. dough2'] = (combined['Dough Cooler2 Temp'] - combined['Dough Cooler2 Temp'].shift(1)).fillna(0)
        combined['consump. perishable'] = (combined['Perishable Cooler Temp'] - combined['Perishable Cooler Temp'].shift(1)).fillna(0)
        return combined

    @staticmethod
    @st.cache_data(ttl=300)
    def load_excel_sheet(sheet_name, fallback_header_row):
        pipeline = FileIngestionPipeline()
        files = pipeline.discover_files()
        categorized = pipeline.categorize_files(files)
        freon_files = categorized.get('freon', [])
        
        if not freon_files: return None
        match_url = freon_files[0][1]

        try:
            preview = DataProcessor.read_excel_from_github(match_url, sheet_name=sheet_name, header=None, engine='openpyxl')
            hdr = fallback_header_row
            if not preview.empty:
                for i in range(min(15, len(preview))):
                    row_vals = [str(x).lower() for x in preview.iloc[i] if pd.notna(x)]
                    if any('date' in x or 'stop time' in x or 'start time' in x or 'sr' in x for x in row_vals):
                        hdr = i
                        break
            
            df = DataProcessor.read_excel_from_github(match_url, sheet_name=sheet_name, header=hdr, engine='openpyxl')
            if df.empty: return None
            df.columns = [str(c).strip() for c in df.columns]
            df = df.dropna(axis=1, how='all')
            
            if sheet_name == 'Sheet3' and len(df.columns) >= 12:
                if 'Saving in hrs' not in df.columns: df.columns.values[11] = 'Saving in hrs'
            elif sheet_name == 'Sheet3':
                last = df.columns[-1]
                if 'unnamed' in str(last).lower(): df = df.rename(columns={last: 'Saving in hrs'})
                
            if not df.empty:
                fc = df.columns[0]
                df = df[df[fc].astype(str).str.strip().str.lower() != 'total']
            return df
        except Exception as e:
            st.warning(f"Unexpected error loading sheet {sheet_name}: {e}")
            return None

# ─────────────────────────────────────────────────────────────
#  6. CHART BUILDERS (Standardized Plotly)
# ─────────────────────────────────────────────────────────────
class ChartBuilder:
    @staticmethod
    def get_layout(**kwargs):
        """
        Deep merges user-provided kwargs into the base Plotly layout.
        Handles nested dictionaries like xaxis/yaxis correctly to avoid TypeErrors.
        """
        layout = deepcopy(Config.PLOTLY_LAYOUT)
        
        for key, value in kwargs.items():
            if key in layout and isinstance(layout[key], dict) and isinstance(value, dict):
                # Merge nested dicts (e.g., xaxis, yaxis)
                layout[key].update(value)
            else:
                # Overwrite or add new keys
                layout[key] = value
                
        return layout

    @staticmethod
    def line_chart(df, x, y_cols, title, colors=None, height=400):
        fig = go.Figure()
        colors = colors or ['#002D62', '#E01934', '#FF9F1C', '#16A34A', '#0EA5E9', '#8B5CF6', '#EC4899', '#F59E0B', '#10B981']
        for i, col in enumerate(y_cols):
            fig.add_trace(go.Scatter(
                x=df[x], y=df[col], mode='lines+markers', name=col,
                line=dict(width=2.5, color=colors[i % len(colors)]),
                marker=dict(size=6),
                hovertemplate=f'{col}<br>%{{x}}<br>%{{y:,.2f}}<extra></extra>'
            ))
        fig.update_layout(title=title, height=height, **ChartBuilder.get_layout())
        return fig

    @staticmethod
    def bar_chart(df, x, y_cols, title, colors=None, barmode='group', orientation='v', height=400):
        fig = go.Figure()
        colors = colors or ['#002D62', '#E01934', '#FF9F1C', '#16A34A', '#0EA5E9']
        for i, col in enumerate(y_cols):
            fig.add_trace(go.Bar(
                x=df[x] if orientation == 'v' else df[col],
                y=df[col] if orientation == 'v' else df[x],
                name=col, marker_color=colors[i % len(colors)], orientation=orientation,
                hovertemplate=f'{col}<br>%{{y:,.2f}}<extra></extra>' if orientation == 'v' else f'{col}<br>%{{x:,.2f}}<extra></extra>'
            ))
        fig.update_layout(title=title, barmode=barmode, height=height, **ChartBuilder.get_layout())
        return fig

# ─────────────────────────────────────────────────────────────
#  7. HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────
def fast_parse_dates(series):
    cleansed = series.astype(str).str.strip().str.split(' ').str[0]
    parsed_df = pd.to_datetime(cleansed, errors='coerce', format='%Y-%m-%d')
    if parsed_df.isna().all(): parsed_df = pd.to_datetime(cleansed, errors='coerce', dayfirst=True)
    return parsed_df

def normalize_to_time(val):
    if val is None or (isinstance(val, float) and pd.isna(val)) or (isinstance(val, pd.Timestamp) and pd.isna(val)): return None
    if isinstance(val, dt_time): return val
    if isinstance(val, (datetime, pd.Timestamp)):
        try: return val.time()
        except: return None
    val_str = str(val).strip()
    if not val_str or val_str.lower() in ['nan', 'nat', 'none', '', '0:00']: return None
    formats_to_try = ['%I.%M.%S %p', '%I:%M:%S %p', '%I:%M %p', '%I.%M %p', '%H:%M:%S', '%H:%M', '%H.%M.%S']
    for fmt in formats_to_try:
        try: return datetime.strptime(val_str, fmt).time()
        except (ValueError, TypeError): continue
    try:
        parsed = pd.to_datetime(val_str, errors='coerce')
        if pd.notna(parsed): return parsed.time()
    except Exception: pass
    return None

# ─────────────────────────────────────────────────────────────
#  8. MAIN APP LAYOUT & EXECUTION
# ─────────────────────────────────────────────────────────────
pipeline = FileIngestionPipeline()
all_files = pipeline.discover_files()
categorized_files = pipeline.categorize_files(all_files)

with st.sidebar:
    st.markdown("""
        <div style="padding:16px 0 20px;">
            <div style="font-size:9px; font-weight:700; letter-spacing:1.8px; color:#94A3B8; text-transform:uppercase; margin-bottom:6px;">JUBILANT FOODWORKS LIMITED</div>
            <div style="font-size:18px; font-weight:800; color:#FFFFFF; line-height:1.25;">Plant Operations<br>Dashboard</div>
            <div style="margin-top:10px; width:36px; height:3px; background:#E01934; border-radius:2px;"></div>
        </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 Refresh Data Now"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("<hr style='border-color:#1E3A8A; margin:14px 0;'>", unsafe_allow_html=True)
    st.markdown("""<div style="font-size:9px; font-weight:700; letter-spacing:1.2px; color:#94A3B8; text-transform:uppercase; margin-bottom:10px;">GitHub Source Status</div>""", unsafe_allow_html=True)

    st.markdown(f"""
        <div style="margin-bottom:8px;"><span class="status-pill status-{'ok' if categorized_files['energy'] else 'err'}">●&nbsp; Processed Energy · {'Active' if categorized_files['energy'] else 'Missing'}</span></div>
        <div style="margin-bottom:8px;"><span class="status-pill status-{'ok' if categorized_files['temperature'] else 'err'}">●&nbsp; Temp Logs · {len(categorized_files['temperature'])} file(s)</span></div>
        <div><span class="status-pill status-{'ok' if categorized_files['freon'] else 'err'}">●&nbsp; Freon Workbook · {'Found' if categorized_files['freon'] else 'Not Found'}</span></div>
    """, unsafe_allow_html=True)

# Load Core Data
e_df = DataProcessor.load_processed_energy_data()
temp_df = DataProcessor.load_temperature_data()

if e_df is not None and not e_df.empty:
    start_date = e_df['Date'].min().strftime('%d %b %Y')
    end_date = e_df['Date'].max().strftime('%d %b %Y')
    date_range_str = f"{start_date} – {end_date}"
else:
    date_range_str = "No Data Loaded"

st.markdown(f"""
<div class="jfl-header-container">
    <div style="flex: 1; min-width: 280px;">
        <div class="jfl-header-subtitle">Supply Chain & Manufacturing · Noida Plant Group</div>
        <div class="jfl-header-title">Plant Operational Intelligence Hub</div>
    </div>
    <div style="display: flex; gap: 12px; flex-wrap: wrap; min-width: 240px;">
        <div class="jfl-header-meta-box" style="flex: 1;"><div class="jfl-meta-label">Reporting Window</div><div class="jfl-meta-value">{date_range_str}</div></div>
        <div class="jfl-header-meta-box" style="flex: 1;"><div class="jfl-meta-label">Corporate Entity</div><div class="jfl-meta-value" style="color: #E01934;">Jubilant FoodWorks</div></div>
    </div>
</div>
""", unsafe_allow_html=True)

tab_energy, tab_temp, tab_power, tab_runtime, tab_comp = st.tabs([
    "⚡  Active Energy Meters", "🌡️  Cold Storage Temperatures", 
    "💡  Energy & Cost Savings", "⚙️  Asset Duty Cycles", "📉  Compressor Optimisation"
])

# ==============================================================================
#  TAB 1 — ACTIVE ENERGY METERS
# ==============================================================================
with tab_energy:
    if e_df is not None and not e_df.empty:
        st.markdown(UIBuilder.section_header("Data Quality & Structure Summary", "📊"), unsafe_allow_html=True)
        date_col = 'Date'
        total_records = len(e_df)
        start_date_dt = e_df[date_col].min()
        end_date_dt = e_df[date_col].max()
        total_days = (end_date_dt - start_date_dt).days + 1
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(UIBuilder.kpi_card("Total Records", f"{total_records} days"), unsafe_allow_html=True)
        with c2: st.markdown(UIBuilder.kpi_card("Date Range Start", start_date_dt.strftime('%d %b %Y')), unsafe_allow_html=True)
        with c3: st.markdown(UIBuilder.kpi_card("Date Range End", end_date_dt.strftime('%d %b %Y')), unsafe_allow_html=True)
        with c4: st.markdown(UIBuilder.kpi_card("Coverage", f"{total_days} days"), unsafe_allow_html=True)
        
        dunkin_col, clc_col, bmc_col, deep_col = 'Dunkin Consumption', 'CLC Consumption', 'BMC Consumption', 'Deep Consumption'
        eq_cols = [dunkin_col, clc_col, bmc_col, deep_col]
        
        missing_dates = pd.date_range(start=start_date_dt, end=end_date_dt).difference(e_df[date_col])
        if len(missing_dates) > 0:
            st.markdown(UIBuilder.alert(f"<strong>Data Quality Alert:</strong> {len(missing_dates)} missing date(s) detected in the range.", "warn"), unsafe_allow_html=True)
        else:
            st.markdown(UIBuilder.alert("<strong>Data Integrity:</strong> Complete date coverage with no gaps detected.", "ok"), unsafe_allow_html=True)
        
        st.markdown(UIBuilder.section_header("Total Energy Consumption Summary (kWh)", "📈"), unsafe_allow_html=True)
        def get_sum(c): return e_df[c].sum() if c in e_df.columns else 0.0
        def get_avg(c): return e_df[c].mean() if c in e_df.columns else 0.0
        
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: st.markdown(UIBuilder.kpi_card("Dunkin' Total", f"{get_sum(dunkin_col):,.1f} kWh", f"Avg: {get_avg(dunkin_col):,.1f} kWh/day", "#002D62"), unsafe_allow_html=True)
        with c2: st.markdown(UIBuilder.kpi_card("CLC Total", f"{get_sum(clc_col):,.1f} kWh", f"Avg: {get_avg(clc_col):,.1f} kWh/day", "#FF9F1C"), unsafe_allow_html=True)
        with c3: st.markdown(UIBuilder.kpi_card("BMC Total", f"{get_sum(bmc_col):,.1f} kWh", f"Avg: {get_avg(bmc_col):,.1f} kWh/day", "#16A34A"), unsafe_allow_html=True)
        with c4: st.markdown(UIBuilder.kpi_card("Deep Freezer Total", f"{get_sum(deep_col):,.1f} kWh", f"Avg: {get_avg(deep_col):,.1f} kWh/day", "#E01934"), unsafe_allow_html=True)
        with c5: 
            total_all = sum(get_sum(c) for c in eq_cols)
            st.markdown(UIBuilder.kpi_card("Grand Total", f"{total_all:,.1f} kWh", f"{total_days} days", "#64748B"), unsafe_allow_html=True)
        
        v_channels = [f'V{i}_Consumption' for i in range(1, 10)]
        existing_v_channels = [c for c in v_channels if c in e_df.columns]
        
        if existing_v_channels:
            st.markdown(UIBuilder.section_header("Daily Consumption Profile — V1 to V9 Channels", "📊"), unsafe_allow_html=True)
            meter_names = {f'V{i}_Consumption': f'V{i} - {n}' for i, n in enumerate(['Dunkin Blast', 'BMC Blast', 'CLC Blast', 'Deep1 Blast', 'Deep2 Blast', 'Dunkin Rack', 'BMC Rack', 'CLC Rack', 'Deep Rack'], 1)}
            fig = go.Figure()
            x_dates = e_df[date_col].dt.strftime('%d-%b').tolist()
            colors = ['#002D62', '#E01934', '#FF9F1C', '#16A34A', '#0EA5E9', '#8B5CF6', '#EC4899', '#F59E0B', '#10B981']
            for i, col in enumerate(existing_v_channels):
                fig.add_trace(go.Scatter(x=x_dates, y=e_df[col], mode='lines+markers', name=meter_names.get(col, col), line=dict(width=2.5, color=colors[i % len(colors)]), marker=dict(size=6)))
            
            # Fixed: Using ChartBuilder.get_layout() with safe merging
            fig.update_layout(
                hovermode="x unified", 
                height=450, 
                xaxis=dict(title='Date', type='category', tickangle=45, fixedrange=True), 
                yaxis=dict(title='Daily Consumption (kWh)', fixedrange=True), 
                **ChartBuilder.get_layout()
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown(UIBuilder.section_header("Process Zone Daily Energy Distribution", "🏭"), unsafe_allow_html=True)
        fig_zone = go.Figure()
        zone_colors = {dunkin_col: '#002D62', clc_col: '#FF9F1C', bmc_col: '#16A34A', deep_col: '#E01934'}
        for col in eq_cols:
            fig_zone.add_trace(go.Bar(x=x_dates, y=e_df[col], name=col.replace(' Consumption', '').title(), marker_color=zone_colors.get(col)))
        
        fig_zone.update_layout(
            barmode='stack', 
            hovermode="x unified", 
            height=450, 
            xaxis=dict(title='Date', type='category', tickangle=45, fixedrange=True), 
            yaxis=dict(title='Total Energy (kWh)', fixedrange=True), 
            **ChartBuilder.get_layout()
        )
        st.plotly_chart(fig_zone, use_container_width=True)
        
        st.markdown(UIBuilder.section_header("Day-over-Day Consumption Change (Δ vs Previous Day)", "📉"), unsafe_allow_html=True)
        valid_data_mask = (e_df[eq_cols].sum(axis=1) > 0)
        e_df_valid = e_df[valid_data_mask].copy()
        
        diff_energy = pd.DataFrame()
        diff_energy['ChartDate'] = e_df_valid[date_col].dt.strftime('%d-%b').tolist()
        diff_cols = []
        for col in eq_cols:
            col_label = f"{col} Δ"
            diff_series = e_df_valid[col].diff().fillna(0).clip(lower=0)
            diff_energy[col_label] = diff_series.values
            diff_cols.append(col_label)
        
        if not diff_energy.empty:
            target_energy_row = diff_energy.iloc[-1]
            last_valid_date = e_df_valid[date_col].iloc[-1].strftime('%d-%b')
            ec1, ec2, ec3, ec4 = st.columns(4)
            def render_delta_metric(container, col_name, color, label):
                actual_kwh = e_df_valid[col_name].iloc[-1]
                delta_val = target_energy_row[f"{col_name} Δ"]
                delta_text = f"Δ {delta_val:+,.1f} kWh vs prev"
                container.markdown(UIBuilder.kpi_card(f"{label} ({last_valid_date})", f"{actual_kwh:,.1f} kWh", delta_text, color), unsafe_allow_html=True)
            
            with ec1: render_delta_metric(ec1, dunkin_col, "#002D62", "Dunkin' Daily")
            with ec2: render_delta_metric(ec2, clc_col, "#FF9F1C", "CLC Daily")
            with ec3: render_delta_metric(ec3, bmc_col, "#16A34A", "BMC Daily")
            with ec4: render_delta_metric(ec4, deep_col, "#E01934", "Deep Daily")
            
            st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
            fig_delta = ChartBuilder.bar_chart(diff_energy, 'ChartDate', diff_cols, "Daily Change (kWh)", colors=['#002D62', '#FF9F1C', '#16A34A', '#E01934'], barmode='group', height=400)
            fig_delta.update_layout(xaxis=dict(type='category', tickangle=45, fixedrange=True), yaxis=dict(title='Daily Change (kWh)', fixedrange=True), shapes=[dict(type='line', xref='paper', yref='y', x0=0, y0=0, x1=1, y1=0, line=dict(color='red', width=2, dash='dash'))])
            st.plotly_chart(fig_delta, use_container_width=True)
            
        st.markdown(UIBuilder.section_header("Statistical Summary by Zone", "📋"), unsafe_allow_html=True)
        summary_data = []
        zone_labels = {dunkin_col: "Dunkin'", clc_col: "CLC", bmc_col: "BMC", deep_col: "Deep Freezer"}
        for col in eq_cols:
            series = e_df[col]
            summary_data.append({
                "Zone": zone_labels.get(col, col), "Total (kWh)": f"{series.sum():,.2f}", "Mean (kWh/day)": f"{series.mean():,.2f}",
                "Min (kWh)": f"{series.min():,.2f}", "Max (kWh)": f"{series.max():,.2f}", "Std Dev": f"{series.std():,.2f}",
                "CV (%)": f"{(series.std()/series.mean()*100) if series.mean() != 0 else 0:.1f}"
            })
        st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)
        
        st.markdown(UIBuilder.section_header("Anomaly Detection & Alerts", "🚨"), unsafe_allow_html=True)
        for col in eq_cols:
            series = e_df[col]
            mean_val, std_val = series.mean(), series.std()
            if std_val == 0: continue
            threshold_upper, threshold_lower = mean_val + 2 * std_val, mean_val - 2 * std_val
            anomalies = e_df[(series > threshold_upper) | (series < threshold_lower)]
            if len(anomalies) > 0:
                st.markdown(UIBuilder.alert(f"<strong>{zone_labels.get(col, col)}:</strong> {len(anomalies)} anomaly day(s) detected (outside ±2σ)", "warn"), unsafe_allow_html=True)
                for idx, row in anomalies.iterrows():
                    st.markdown(f"  - {row[date_col].strftime('%d %b %Y')}: {row[col]:,.2f} kWh (Mean: {mean_val:,.2f}, Threshold: {threshold_upper:,.2f})")
            else:
                st.markdown(UIBuilder.alert(f"<strong>{zone_labels.get(col, col)}:</strong> No anomalies detected - stable consumption pattern", "ok"), unsafe_allow_html=True)
        
        st.markdown(UIBuilder.section_header("Raw Data Inspector & Export Portal", "📥"), unsafe_allow_html=True)
        with st.expander("📂 View Pre-Processed Active Energy File Data Table", expanded=False):
            st.dataframe(e_df.set_index(date_col), use_container_width=True)
            st.download_button("📥 Download Active Energy Data as CSV", e_df.to_csv(index=False).encode('utf-8'), f"active_energy_{start_date_dt.strftime('%Y%m%d')}_to_{end_date_dt.strftime('%Y%m%d')}.csv", "text/csv", key="btn_download_energy")
    else:
        st.markdown(UIBuilder.alert("<strong>⚠️ No active energy data captured matching the current file window constraints.</strong>", "info"), unsafe_allow_html=True)

# ==============================================================================
#  TAB 2 — COLD STORAGE TEMPERATURES
# ==============================================================================
with tab_temp:
    if temp_df is not None and not temp_df.empty:
        latest = temp_df.iloc[-1]
        sensors = ['Dough Cooler1 Temp', 'Dough Cooler2 Temp', 'Perishable Cooler Temp']
        delta_cols = ['consump. dough1', 'consump. dough2', 'consump. perishable']
        THRESHOLD = 4.0

        c1, c2, c3, c4 = st.columns([1,1,1,1.2])
        with c1: st.markdown(UIBuilder.kpi_card("Dough Cooler 1", f"{latest['Dough Cooler1 Temp']:.2f} °C", color="#002D62"), unsafe_allow_html=True)
        with c2: st.markdown(UIBuilder.kpi_card("Dough Cooler 2", f"{latest['Dough Cooler2 Temp']:.2f} °C", color="#0EA5E9"), unsafe_allow_html=True)
        with c3: st.markdown(UIBuilder.kpi_card("Perishable Store", f"{latest['Perishable Cooler Temp']:.2f} °C", color="#E01934"), unsafe_allow_html=True)
        with c4:
            total_logs = len(temp_df)
            total_exc = sum((temp_df[s] > THRESHOLD).sum() for s in sensors)
            compliance = (1 - total_exc / (total_logs * len(sensors))) * 100
            st.markdown(UIBuilder.kpi_card("Thermal Compliance Index", f"{compliance:.1f}%", f"{total_exc} critical violations", "#16A34A"), unsafe_allow_html=True)

        st.markdown(UIBuilder.section_header("Real-Time Temperature Stream", "🌡️"), unsafe_allow_html=True)
        st.line_chart(temp_df.set_index('Time')[sensors], color=["#002D62","#0EA5E9","#E01934"])

        st.markdown(UIBuilder.section_header("Daily Mean Thermal Signature", "📊"), unsafe_allow_html=True)
        temp_df['Date'] = temp_df['Time'].dt.date
        daily_avg = temp_df.groupby('Date')[sensors].mean().round(2)
        daily_avg.index = daily_avg.index.astype(str)
        st.bar_chart(daily_avg, color=["#002D62","#0EA5E9","#E01934"])

        st.markdown(UIBuilder.section_header("Temperature Log Delta Variations", "📉"), unsafe_allow_html=True)
        sc1, sc2, sc3 = st.columns(3)
        with sc1: st.markdown(UIBuilder.kpi_card("Dough 1 Delta Variance Sum", f"{temp_df['consump. dough1'].sum():,.2f} °C", color="#002D62"), unsafe_allow_html=True)
        with sc2: st.markdown(UIBuilder.kpi_card("Dough 2 Delta Variance Sum", f"{temp_df['consump. dough2'].sum():,.2f} °C", color="#0EA5E9"), unsafe_allow_html=True)
        with sc3: st.markdown(UIBuilder.kpi_card("Perishable Delta Variance Sum", f"{temp_df['consump. perishable'].sum():,.2f} °C", color="#E01934"), unsafe_allow_html=True)
        
        st.line_chart(temp_df.set_index('Time')[delta_cols])

        st.markdown(UIBuilder.section_header("Cold-Chain Thermodynamic Stability Audits", "📋"), unsafe_allow_html=True)
        labels = {'Dough Cooler1 Temp':'Dough Cooler 1','Dough Cooler2 Temp':'Dough Cooler 2','Perishable Cooler Temp':'Perishable Storage'}
        rows = []
        for col in sensors:
            s = temp_df[col]
            n, exc = len(s), int((s > THRESHOLD).sum())
            rows.append({"Asset Node": labels[col], "Total Logs": n, "Mean Temp": s.mean(), "Min Temp": s.min(), "Max Temp": s.max(), "Stability (σ)": s.std(), "Excursions": exc, "Compliance Index": (n - exc) / n})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, column_config={
            "Mean Temp": st.column_config.NumberColumn(format="%.2f °C"), "Min Temp": st.column_config.NumberColumn(format="%.2f °C"),
            "Max Temp": st.column_config.NumberColumn(format="%.2f °C"), "Stability (σ)": st.column_config.NumberColumn(format="%.2f σ"),
            "Compliance Index": st.column_config.ProgressColumn(format="%.1f%%", min_value=0.0, max_value=1.0)
        })

        st.markdown(UIBuilder.section_header("Zone Status Alert Routing", "🚨"), unsafe_allow_html=True)
        for col in sensors:
            exc = int((temp_df[col] > THRESHOLD).sum())
            comp = ((len(temp_df) - exc) / len(temp_df)) * 100
            lbl = labels[col]
            if comp >= 95: st.markdown(UIBuilder.alert(f"<strong>{lbl}</strong> — Stable at {comp:.1f}% operational compliance.", "ok"), unsafe_allow_html=True)
            else: st.markdown(UIBuilder.alert(f"<strong>{lbl}</strong> — Out-of-bounds drop at {comp:.1f}% compliance level.", "warn"), unsafe_allow_html=True)

        st.markdown(UIBuilder.section_header("Raw Data Inspector & Export Portal", "📥"), unsafe_allow_html=True)
        with st.expander("📂 View & Download Compiled Temperature Log File Data with Delta Metrics", expanded=False):
            st.dataframe(temp_df, use_container_width=True, hide_index=True)
            st.download_button("Download Compiled Temperature Data as CSV", temp_df.to_csv(index=False).encode('utf-8'), "compiled_temperature_logs.csv", "text/csv", key="btn_download_temp")
    else:
        st.markdown(UIBuilder.alert("No environment logs could be successfully loaded.", "info"), unsafe_allow_html=True)

# ==============================================================================
#  TAB 3 — ENERGY & COST SAVINGS
# ==============================================================================
with tab_power:
    if e_df is not None and not e_df.empty:
        facilities = {'Dunkin': 'dunkin consmp.', 'CLC': 'clc consump.', 'BMC': 'bmc consump.', 'Deep (Blast)': 'deep consumption'}
        
        # Fallback to calculated columns if specific names are missing
        actual_facilities = {}
        for k, v in facilities.items():
            if v in e_df.columns: actual_facilities[k] = v
            else:
                calc_map = {'Dunkin': 'Dunkin Consumption', 'CLC': 'CLC Consumption', 'BMC': 'BMC Consumption', 'Deep (Blast)': 'Deep Consumption'}
                if calc_map[k] in e_df.columns: actual_facilities[k] = calc_map[k]
        
        df_facilities = e_df[['Date'] + list(actual_facilities.values())].copy()
        df_facilities.columns = ['Date'] + list(actual_facilities.keys())
        df_melted = df_facilities.melt(id_vars='Date', var_name='Facility', value_name='Daily Consumption')
        df_melted['Daily Consumption'] = pd.to_numeric(df_melted['Daily Consumption'], errors='coerce').fillna(0).clip(lower=0)
        
        metrics = df_melted.groupby('Facility')['Daily Consumption'].agg([('total_power', 'sum'), ('avg_daily', 'mean'), ('highest_daily', 'max'), ('lowest_daily', 'min'), ('days_processed', 'count')]).reset_index()
        facility_metrics = dict(zip(metrics['Facility'], metrics.to_dict('records')))
        
        st.markdown(UIBuilder.section_header("Executive Facility Performance Matrix", "📊"), unsafe_allow_html=True)
        colors = {'Dunkin': '#002D62', 'CLC': '#FF9F1C', 'BMC': '#16A34A', 'Deep (Blast)': '#E01934'}
        cols = st.columns(4)
        for idx, fac in enumerate(actual_facilities.keys()):
            with cols[idx]:
                m = facility_metrics.get(fac, {})
                st.markdown(f"""
                <div class="kpi-card" style="border-left-color: {colors[fac]};">
                    <div class="kpi-label" style="font-size: 16px; color: {colors[fac]}; margin-bottom: 15px; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;">{fac}</div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;"><span class="kpi-label">Total Power</span><span class="kpi-value" style="font-size: 14px;">{m.get('total_power', 0):,.0f} kWh</span></div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;"><span class="kpi-label">Avg Daily</span><span class="kpi-value" style="font-size: 14px;">{m.get('avg_daily', 0):,.1f} kWh</span></div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;"><span class="kpi-label">Highest Daily</span><span class="kpi-value" style="font-size: 14px;">{m.get('highest_daily', 0):,.1f} kWh</span></div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;"><span class="kpi-label">Lowest Daily</span><span class="kpi-value" style="font-size: 14px;">{m.get('lowest_daily', 0):,.1f} kWh</span></div>
                    <div style="display: flex; justify-content: space-between;"><span class="kpi-label">Days Processed</span><span class="kpi-value" style="font-size: 14px;">{int(m.get('days_processed', 0))}</span></div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown(UIBuilder.alert("⚠️ Energy data file not found or empty.", "info"), unsafe_allow_html=True)

# ==============================================================================
#  TAB 4 — ASSET DUTY CYCLES
# ==============================================================================
with tab_runtime:
    runtime_df = DataProcessor.load_excel_sheet('Sheet2', fallback_header_row=2)
    if runtime_df is not None and not runtime_df.empty:
        r = runtime_df.copy()
        fc = r.columns[0]
        r = r[~r[fc].astype(str).str.contains('Date|From|Total|Running', case=False, na=False)]
        r[fc] = fast_parse_dates(r[fc])
        r = r.dropna(subset=[fc]).sort_values(fc)
        kwh_cols = [c for c in r.columns if 'KWH' in str(c).upper()]
        for col in kwh_cols: r[col] = pd.to_numeric(r[col], errors='coerce').fillna(0)

        if kwh_cols and not r.empty:
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(UIBuilder.kpi_card("Consolidated Ingested Draw", f"{r[kwh_cols[0]].sum():,.0f} kWh", color="#002D62"), unsafe_allow_html=True)
            with c2: st.markdown(UIBuilder.kpi_card("Peak System Load Vector", f"{r[kwh_cols[0]].max():,.0f} kWh", color="#FF9F1C"), unsafe_allow_html=True)
            with c3: st.markdown(UIBuilder.kpi_card("Mean Constant Load Metric", f"{r[kwh_cols[0]].mean():,.0f} kWh", color="#E01934"), unsafe_allow_html=True)

            st.markdown(UIBuilder.section_header("Daily Asset Displacement Matrix (Normal Data Logs)", "📊"), unsafe_allow_html=True)
            st.bar_chart(r.set_index(fc)[kwh_cols[0]], color="#002D62")

            r['Date_Key'] = r[fc].dt.date
            daily_runtime = r.groupby('Date_Key')[kwh_cols[0]].agg(['sum', 'max', 'mean']).reset_index().rename(columns={'Date_Key': 'Date', 'sum': 'Energy Drew (kWh)', 'max': 'Peak System Load Vector (kWh)', 'mean': 'Mean Load Vector (kWh)'})
            daily_runtime['Date'] = pd.to_datetime(daily_runtime['Date'])

            st.markdown(UIBuilder.section_header("Date-Wise Energy Ingestion Profiles (Differenced Daily Breakdown)", "📉"), unsafe_allow_html=True)
            target_day = daily_runtime.iloc[-1] if not daily_runtime.empty else None
            rc1, rc2, rc3 = st.columns(3)
            with rc1: st.markdown(UIBuilder.kpi_card("Energy Drew", f"{target_day['Energy Drew (kWh)']:,.1f} kWh" if target_day is not None else "0.0 kWh", color="#002D62"), unsafe_allow_html=True)
            with rc2: st.markdown(UIBuilder.kpi_card("Peak System Load Vector", f"{target_day['Peak System Load Vector (kWh)']:,.1f} kWh" if target_day is not None else "0.0 kWh", color="#FF9F1C"), unsafe_allow_html=True)
            with rc3: st.markdown(UIBuilder.kpi_card("Mean Load Vector", f"{target_day['Mean Load Vector (kWh)']:,.1f} kWh" if target_day is not None else "0.0 kWh", color="#E01934"), unsafe_allow_html=True)

            st.line_chart(daily_runtime.set_index('Date')[['Energy Drew (kWh)', 'Peak System Load Vector (kWh)', 'Mean Load Vector (kWh)']])

            st.markdown(UIBuilder.section_header("Date-Wise Asset Duty Performance Log Metrics", "📋"), unsafe_allow_html=True)
            st.dataframe(daily_runtime, use_container_width=True, hide_index=True)

            st.markdown(UIBuilder.section_header("Raw Data Inspector & Export Portal", "📥"), unsafe_allow_html=True)
            with st.expander("📂 View & Download Asset Duty Cycle Raw Sheet Data", expanded=False):
                st.dataframe(r.drop(columns=['Date_Key']), use_container_width=True, hide_index=True)
                st.download_button("Download Date-Wise Duty Cycles as CSV", daily_runtime.to_csv(index=False).encode('utf-8'), "datewise_asset_duty_cycles.csv", "text/csv", key="btn_download_runtime")
    else:
        st.markdown(UIBuilder.alert("Asset duty-cycle log metrics are not active.", "info"), unsafe_allow_html=True)

# ==============================================================================
#  TAB 5 — COMPRESSOR OPTIMISATION (VECTORIZED & OPTIMIZED)
# ==============================================================================
with tab_comp:
    comp_raw = DataProcessor.load_excel_sheet('Sheet3', fallback_header_row=1)
    
    if comp_raw is not None and not comp_raw.empty:
        c_df = comp_raw.copy()
        c_df.columns = [str(col).strip() for col in c_df.columns]
        if not c_df.empty:
            first_col = c_df.columns[0]
            mask = ~c_df[first_col].astype(str).str.strip().str.lower().str.contains('date|total|from|sr\\.?\\s*no\\.?|running|stop time|start time', case=False, na=False)
            c_df = c_df[mask].reset_index(drop=True)
        
        c_df['Parsed_Date'] = pd.to_datetime(c_df.iloc[:, 0], errors='coerce')
        c_df = c_df.dropna(subset=['Parsed_Date'])
        
        TARGET_START = datetime(2026, 4, 26)
        TARGET_END = datetime(2026, 5, 8)
        c_df = c_df[(c_df['Parsed_Date'] >= TARGET_START) & (c_df['Parsed_Date'] <= TARGET_END)].copy().sort_values('Parsed_Date').reset_index(drop=True)
        
        if c_df.empty:
            st.markdown(UIBuilder.alert("<strong>No Data:</strong> No records found in target range (26-Apr to 08-May 2026).", "warn"), unsafe_allow_html=True)
        else:
            compressor_config = {}
            for i in range(1, 6):
                comp_name = f"Compressor-{i}"
                stop_col = start_col = None
                for col in c_df.columns:
                    col_lower = col.lower()
                    comp_patterns = [f'compressor-{i}', f'compressor {i}', f'comp-{i}', f'comp {i}']
                    if any(p in col_lower for p in comp_patterns):
                        if 'stop' in col_lower and 'start' not in col_lower: stop_col = col
                        elif 'start' in col_lower and 'stop' not in col_lower: start_col = col
                if stop_col and start_col: compressor_config[comp_name] = {'stop': stop_col, 'start': start_col}
            
            if len(compressor_config) < 5 and len(c_df.columns) >= 11:
                compressor_config = {}
                for i in range(1, 6):
                    comp_name = f"Compressor-{i}"
                    stop_idx = 2 * i - 1
                    start_idx = 2 * i
                    if stop_idx < len(c_df.columns) and start_idx < len(c_df.columns):
                        compressor_config[comp_name] = {'stop': c_df.columns[stop_idx], 'start': c_df.columns[start_idx]}
            
            if not compressor_config:
                st.markdown(UIBuilder.alert("<strong>Configuration Error:</strong> Could not detect compressor columns.", "warn"), unsafe_allow_html=True)
            else:
                all_dates = pd.date_range(start=TARGET_START, end=TARGET_END, freq='D')
                daily_records, summary_records = [], []
                
                # Vectorized processing for massive performance gain
                grouped = c_df.groupby(c_df['Parsed_Date'].dt.date).first().reset_index()
                grouped.rename(columns={'Parsed_Date': 'Date_Key'}, inplace=True)
                
                for comp_name, cols in compressor_config.items():
                    stop_col, start_col = cols['stop'], cols['start']
                    
                    def calc_row_runtime(row):
                        t_stop = normalize_to_time(row[stop_col])
                        t_start = normalize_to_time(row[start_col])
                        if t_stop is not None and t_start is not None:
                            stop_mins = t_stop.hour * 60 + t_stop.minute + t_stop.second / 60.0
                            start_mins = t_start.hour * 60 + t_start.minute + t_start.second / 60.0
                            delta_mins = (1440.0 - stop_mins) + start_mins if start_mins < stop_mins else start_mins - stop_mins
                            return max(0.0, min(24.0, delta_mins / 60.0))
                        return 0.0
                        
                    grouped[f'{comp_name}_runtime'] = grouped.apply(calc_row_runtime, axis=1)
                    total_runtime_hrs, total_downtime_hrs = 0.0, 0.0
                    
                    for target_date in all_dates:
                        row_match = grouped[grouped['Date_Key'] == target_date.date()]
                        runtime_hrs = min(24.0, row_match.iloc[0][f'{comp_name}_runtime']) if not row_match.empty else 0.0
                        downtime_hrs = 24.0 - runtime_hrs
                        total_runtime_hrs += runtime_hrs
                        total_downtime_hrs += downtime_hrs
                        daily_records.append({'Date': target_date, 'Compressor': comp_name, 'Working Hours': round(runtime_hrs, 2), 'Non Working Hours': round(downtime_hrs, 2), 'Utilization %': round((runtime_hrs / 24.0) * 100.0, 1)})
                    
                    total_available_hrs = len(all_dates) * 24.0
                    summary_records.append({'Compressor': comp_name, 'Working Hours': round(total_runtime_hrs, 2), 'Non Working Hours': round(total_downtime_hrs, 2), 'Utilization %': round((total_runtime_hrs / total_available_hrs) * 100.0, 1), 'Downtime %': round((total_downtime_hrs / total_available_hrs) * 100.0, 1)})
                
                df_daily = pd.DataFrame(daily_records)
                df_summary = pd.DataFrame(summary_records)
                
                df_daily['Total Check'] = df_daily['Working Hours'] + df_daily['Non Working Hours']
                validation_failures = df_daily[abs(df_daily['Total Check'] - 24.0) > 0.01]
                
                if len(validation_failures) > 0:
                    st.markdown(UIBuilder.alert(f"<strong>Validation Warning:</strong> {len(validation_failures)} record(s) where Working + Non-Working ≠ 24 hours.", "warn"), unsafe_allow_html=True)
                else:
                    st.markdown(UIBuilder.alert("<strong>Validation Passed:</strong> All daily records sum to exactly 24 hours.", "ok"), unsafe_allow_html=True)
                
                st.markdown(UIBuilder.section_header("Compressor Performance Overview", "📊"), unsafe_allow_html=True)
                avg_util = df_summary['Utilization %'].mean()
                avg_downtime = df_summary['Downtime %'].mean()
                best_comp = df_summary.loc[df_summary['Utilization %'].idxmax(), 'Compressor']
                worst_comp = df_summary.loc[df_summary['Downtime %'].idxmax(), 'Compressor']
                
                k1, k2, k3, k4 = st.columns(4)
                with k1: st.markdown(UIBuilder.kpi_card("Avg Utilization", f"{avg_util:.1f}%", color="#16A34A"), unsafe_allow_html=True)
                with k2: st.markdown(UIBuilder.kpi_card("Avg Downtime", f"{avg_downtime:.1f}%", color="#E01934"), unsafe_allow_html=True)
                with k3: st.markdown(UIBuilder.kpi_card("Best Performer", best_comp, color="#002D62"), unsafe_allow_html=True)
                with k4: st.markdown(UIBuilder.kpi_card("Highest Downtime", worst_comp, color="#FF9F1C"), unsafe_allow_html=True)
                
                st.markdown(UIBuilder.section_header("Daily Compressor Performance Table", "📋"), unsafe_allow_html=True)
                daily_display = df_daily[['Date', 'Compressor', 'Working Hours', 'Non Working Hours', 'Utilization %']].copy()
                daily_display['Date'] = daily_display['Date'].dt.strftime('%d-%b-%Y')
                st.dataframe(daily_display, use_container_width=True, hide_index=True)
                
                st.markdown(UIBuilder.section_header("Summary Performance Table", "📋"), unsafe_allow_html=True)
                st.dataframe(df_summary, use_container_width=True, hide_index=True)
                
                st.markdown(UIBuilder.section_header("Visual Analytics Dashboard", "📈"), unsafe_allow_html=True)
                chart_colors = ['#002D62', '#E01934', '#FF9F1C', '#16A34A', '#8B5CF6']
                
                fig1 = go.Figure(go.Bar(y=df_summary['Compressor'], x=df_summary['Utilization %'], orientation='h', marker=dict(color='#002D62'), text=df_summary['Utilization %'].apply(lambda x: f'{x:.1f}%'), textposition='auto'))
                fig1.update_layout(title='Compressor Utilization Comparison', xaxis=dict(title='Utilization (%)', range=[0, 105]), yaxis=dict(autorange='reversed'), height=350, **ChartBuilder.get_layout())
                
                fig2 = go.Figure()
                fig2.add_trace(go.Bar(name='Working Hours', y=df_summary['Compressor'], x=df_summary['Working Hours'], orientation='h', marker_color='#16A34A'))
                fig2.add_trace(go.Bar(name='Non Working Hours', y=df_summary['Compressor'], x=df_summary['Non Working Hours'], orientation='h', marker_color='#E01934'))
                fig2.update_layout(barmode='stack', title='Working vs Non-Working Hours', xaxis=dict(title='Hours'), yaxis=dict(autorange='reversed'), height=350, **ChartBuilder.get_layout())
                
                col_c1, col_c2 = st.columns(2)
                with col_c1: st.plotly_chart(fig1, use_container_width=True)
                with col_c2: st.plotly_chart(fig2, use_container_width=True)
                
                fig3 = ChartBuilder.line_chart(df_daily[df_daily['Compressor']==df_summary['Compressor'].iloc[0]].sort_values('Date'), 'Date', ['Working Hours'], 'Daily Working Hours Trend', height=400)
                for idx, comp in enumerate(df_summary['Compressor']):
                    sub = df_daily[df_daily['Compressor'] == comp].sort_values('Date')
                    fig3.add_trace(go.Scatter(x=sub['Date'].dt.strftime('%d-%b'), y=sub['Working Hours'], mode='lines+markers', name=comp, line=dict(color=chart_colors[idx % len(chart_colors)], width=2.5), marker=dict(size=6)))
                fig3.update_layout(yaxis=dict(title='Working Hours', range=[0, 26]), **ChartBuilder.get_layout())
                
                fig4 = ChartBuilder.line_chart(df_daily[df_daily['Compressor']==df_summary['Compressor'].iloc[0]].sort_values('Date'), 'Date', ['Non Working Hours'], 'Daily Downtime Trend', height=400)
                for idx, comp in enumerate(df_summary['Compressor']):
                    sub = df_daily[df_daily['Compressor'] == comp].sort_values('Date')
                    fig4.add_trace(go.Scatter(x=sub['Date'].dt.strftime('%d-%b'), y=sub['Non Working Hours'], mode='lines+markers', name=comp, line=dict(color=chart_colors[idx % len(chart_colors)], width=2.5), marker=dict(size=6)))
                fig4.update_layout(yaxis=dict(title='Downtime Hours', range=[0, 26]), **ChartBuilder.get_layout())
                
                col_c3, col_c4 = st.columns(2)
                with col_c3: st.plotly_chart(fig3, use_container_width=True)
                with col_c4: st.plotly_chart(fig4, use_container_width=True)
                
                df_sorted_downtime = df_summary.sort_values('Non Working Hours', ascending=True)
                fig5 = go.Figure(go.Bar(y=df_sorted_downtime['Compressor'], x=df_sorted_downtime['Non Working Hours'], orientation='h', marker=dict(color='#FF9F1C'), text=df_sorted_downtime['Non Working Hours'].apply(lambda x: f'{x:.1f}h'), textposition='auto'))
                fig5.update_layout(title='Downtime Ranking (Lowest to Highest)', xaxis=dict(title='Total Downtime Hours'), yaxis=dict(autorange='reversed'), height=350, **ChartBuilder.get_layout())
                
                heatmap_pivot = df_daily.pivot_table(index='Compressor', columns='Date', values='Utilization %', aggfunc='mean').reindex(sorted(df_daily['Date'].unique()), axis=1).fillna(0)
                date_labels = [d.strftime('%d-%b') for d in heatmap_pivot.columns]
                fig6 = go.Figure(data=go.Heatmap(z=heatmap_pivot.values, x=date_labels, y=heatmap_pivot.index.tolist(), colorscale=[[0.0, '#E01934'], [0.5, '#FF9F1C'], [1.0, '#16A34A']], zmin=0, zmax=100, text=heatmap_pivot.values.round(1), texttemplate='%{text:.0f}%', textfont=dict(size=10, color='white'), colorbar=dict(title='Utilization %', ticksuffix='%')))
                fig6.update_layout(title='Utilization Heatmap (Date vs Compressor)', xaxis=dict(title='Date', tickangle=45), yaxis=dict(autorange='reversed'), height=350, **ChartBuilder.get_layout())
                
                col_c5, col_c6 = st.columns(2)
                with col_c5: st.plotly_chart(fig5, use_container_width=True)
                with col_c6: st.plotly_chart(fig6, use_container_width=True)
                
                st.markdown(UIBuilder.section_header("Data Export Portal", "📥"), unsafe_allow_html=True)
                with st.expander("📂 Download Processed Compressor Data", expanded=False):
                    col_dl1, col_dl2 = st.columns(2)
                    with col_dl1: st.download_button("📥 Download Daily Data (CSV)", df_daily.to_csv(index=False).encode('utf-8'), f"compressor_daily_{TARGET_START.strftime('%Y%m%d')}_to_{TARGET_END.strftime('%Y%m%d')}.csv", "text/csv", key="btn_download_comp_daily")
                    with col_dl2: st.download_button("📥 Download Summary Data (CSV)", df_summary.to_csv(index=False).encode('utf-8'), f"compressor_summary_{TARGET_START.strftime('%Y%m%d')}_to_{TARGET_END.strftime('%Y%m%d')}.csv", "text/csv", key="btn_download_comp_summary")
                    st.markdown("**Raw Parsed Data Preview:**")
                    st.dataframe(c_df, use_container_width=True, hide_index=True)
    else:
        st.markdown(UIBuilder.alert("⚠️ Compressor optimization data (Sheet3) not available in the repository.", "info"), unsafe_allow_html=True)
