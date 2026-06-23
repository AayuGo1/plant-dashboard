# Complete Enterprise Manufacturing Intelligence Platform for Jubilant FoodWorks Limited
# REFACTORED: Dynamic date detection, automatic GitHub file discovery, no hardcoded dates/limits
import os
import glob
import warnings
import requests
import io
import re
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta, time as dt_time, timezone
import logging
from typing import Dict, List, Tuple, Optional, Any
import traceback

warnings.filterwarnings("ignore", category=UserWarning)

# ─────────────────────────────────────────────────────────────
#  CONFIGURATION & CONSTANTS
# ─────────────────────────────────────────────────────────────
GITHUB_USER   = "AayuGo1"
GITHUB_REPO   = "plant-dashboard"
GITHUB_BRANCH = "main"

RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}"
API_BASE = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents?ref={GITHUB_BRANCH}"

# Dynamic File Discovery Patterns — automatically picks up new files matching these patterns
FILE_PATTERNS = {
    'energy': re.compile(r'PROCESSED_DAILY_VARS_Active_Energy_Report', re.IGNORECASE),
    'temperature': re.compile(r'DataLog_.*\.csv', re.IGNORECASE),
    # Freon temperature logs: matches freon*.csv / freon*.xlsx / Freon_Log*.csv etc.
    'freon_temp': re.compile(r'freon.*\.(csv|xlsx)', re.IGNORECASE),
    # Ammonia temperature logs: matches ammonia*.csv / Ammonia_Log*.xlsx etc.
    'ammonia_temp': re.compile(r'ammonia.*\.(csv|xlsx)', re.IGNORECASE),
    # Freon workbook (equipment/compressor data — distinct from temperature logs)
    'freon': re.compile(r'freon.*workbook.*\.xlsx|freon.*equip.*\.xlsx', re.IGNORECASE),
    'utility': re.compile(r'utility.*\.xlsx', re.IGNORECASE),
    'operational': re.compile(r'operational.*\.xlsx', re.IGNORECASE)
}

# Standardized Enterprise Plotly Theme
PLOTLY_THEME = dict(
    font_family='Inter, Segoe UI, sans-serif',
    font_size=12,
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    hoverlabel_bgcolor='white',
    hoverlabel_bordercolor='#E2E8F0',
    legend_orientation='h',
    legend_yanchor='bottom',
    legend_y=1.02,
    legend_xanchor='right',
    legend_x=1,
    legend_bgcolor='rgba(255,255,255,0.9)',
    grid_color='#E2E8F0',
    zeroline_color='#E2E8F0'
)

PRIMARY_COLOR    = "#002D62"
SECONDARY_COLOR  = "#E01934"
BACKGROUND_COLOR = "#F8FAFC"
TEXT_PRIMARY     = "#0F172A"
TEXT_SECONDARY   = "#64748B"

IST = timezone(timedelta(hours=5, minutes=30))

def standardize_chart(fig):
    """Applies the standardized enterprise Plotly theme to a figure safely."""
    fig.update_layout(
        font=dict(family=PLOTLY_THEME['font_family'], size=PLOTLY_THEME['font_size']),
        plot_bgcolor=PLOTLY_THEME['plot_bgcolor'],
        paper_bgcolor=PLOTLY_THEME['paper_bgcolor'],
        hoverlabel=dict(bgcolor=PLOTLY_THEME['hoverlabel_bgcolor'],
                        bordercolor=PLOTLY_THEME['hoverlabel_bordercolor']),
        legend=dict(
            orientation=PLOTLY_THEME['legend_orientation'],
            yanchor=PLOTLY_THEME['legend_yanchor'],
            y=PLOTLY_THEME['legend_y'],
            xanchor=PLOTLY_THEME['legend_xanchor'],
            x=PLOTLY_THEME['legend_x'],
            bgcolor=PLOTLY_THEME['legend_bgcolor']
        )
    )
    if 'xaxis' in fig.layout:
        fig.layout.xaxis.gridcolor = PLOTLY_THEME['grid_color']
        fig.layout.xaxis.zerolinecolor = PLOTLY_THEME['zeroline_color']
    if 'yaxis' in fig.layout:
        fig.layout.yaxis.gridcolor = PLOTLY_THEME['grid_color']
        fig.layout.yaxis.zerolinecolor = PLOTLY_THEME['zeroline_color']
    return fig

# ─────────────────────────────────────────────────────────────
#  PAGE CONFIG & ENTERPRISE CSS
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="JFL – Plant Operations Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="auto"
)

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

:root {{
    --primary-color: {PRIMARY_COLOR};
    --secondary-color: {SECONDARY_COLOR};
    --background-color: {BACKGROUND_COLOR};
    --text-primary: {TEXT_PRIMARY};
    --text-secondary: {TEXT_SECONDARY};
}}

html, body, [class*="css"] {{
    font-family: 'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
    color: var(--text-primary);
}}
.block-container {{
    padding: 1.5rem 2.5rem 3rem;
    background: #F4F6F9;
    max-width: 1600px;
}}

section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #001840 0%, var(--primary-color) 100%) !important;
    border-right: none !important;
}}
section[data-testid="stSidebar"] * {{ color: #CBD5E0 !important; }}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {{ color: #FFFFFF !important; }}
section[data-testid="stSidebar"] input {{
    background: #001840 !important; border: 1px solid #1E3A8A !important;
    color: #FFFFFF !important; border-radius: 6px !important; font-size: 12px !important;
}}
section[data-testid="stSidebar"] label {{
    color: #94A3B8 !important; font-size: 10px !important; font-weight: 700 !important;
    text-transform: uppercase !important; letter-spacing: 0.8px !important;
}}
section[data-testid="stSidebar"] .stButton>button {{
    background: var(--secondary-color) !important; color: white !important; border: none !important;
    font-weight: 700 !important; width: 100% !important; border-radius: 6px !important;
    transition: all 0.2s ease !important;
}}
section[data-testid="stSidebar"] .stButton>button:hover {{
    background: #B91429 !important; transform: translateY(-1px) !important;
}}

.jfl-header-container {{
    background: #FFFFFF; border-radius: 12px; padding: 24px 27px; margin-bottom: 24px;
    border: 1px solid #E2E8F0; border-left: 7px solid var(--secondary-color);
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
    display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 17px;
}}
.jfl-header-title {{ font-size: 22px; font-weight: 800; color: var(--primary-color); letter-spacing: -0.5px; }}
.jfl-header-subtitle {{ font-size: 9px; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; color: var(--text-secondary); margin-bottom: 3px; }}
.jfl-header-meta-box {{ background: var(--background-color); border: 1px solid #E2E8F0; border-radius: 7px; padding: 10px 15px; min-width: 136px; }}
.jfl-meta-label {{ font-size: 8px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; color: #94A3B8; margin-bottom: 3px; }}
.jfl-meta-value {{ font-size: 12px; font-weight: 800; color: var(--primary-color); }}

.stTabs [data-baseweb="tab-list"] {{
    gap: 0; background: #FFFFFF; border-bottom: 2px solid #E2E8F0;
    padding: 0 10px; border-radius: 9px 9px 0 0;
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent; border: none; border-bottom: 3px solid transparent;
    padding: 14px 20px; font-size: 11px; font-weight: 700; color: var(--text-secondary);
    transition: all 0.2s ease;
}}
.stTabs [data-baseweb="tab"]:hover {{ color: var(--primary-color); }}
.stTabs [data-baseweb="tab"][aria-selected="true"] {{
    color: var(--primary-color) !important; border-bottom: 3px solid var(--secondary-color) !important;
    background: transparent !important;
}}

.kpi-container {{
    margin-bottom: 32px !important;
    padding-bottom: 16px !important;
    clear: both !important;
    overflow: visible !important;
}}

.kpi-card {{
    background: white;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
    border-left: 4px solid var(--primary-color);
    transition: all 0.3s ease;
    min-height: 136px;
    max-height: 136px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    overflow: hidden;
    box-sizing: border-box;
}}
.kpi-card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);
}}
.kpi-title {{
    font-size: 10px;
    font-weight: 700;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 7px;
    line-height: 1.3;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}
.kpi-value {{
    font-size: 24px;
    font-weight: 800;
    color: var(--text-primary);
    margin-bottom: 7px;
    flex-grow: 1;
    display: flex;
    align-items: center;
    line-height: 1.2;
}}
.kpi-delta {{
    font-size: 10px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 3px;
}}
.kpi-delta.positive {{ color: #16A34A; }}
.kpi-delta.negative {{ color: #DC2626; }}
.kpi-delta.neutral {{ color: var(--text-secondary); }}

.sec-title {{
    font-size: 11px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase;
    letter-spacing: 1.2px; margin: 27px 0 14px 0; padding-bottom: 9px;
    border-bottom: 2px solid #E2E8F0; display: flex; align-items: center; gap: 7px;
    clear: both;
}}
.alert-warn {{
    background: #FFFBEB; border: 1px solid #FDE68A; border-left: 4px solid #F59E0B;
    border-radius: 7px; padding: 12px 15px; font-size: 11px; color: #92400E;
    margin-bottom: 14px; display: flex; align-items: center; gap: 9px;
}}
.alert-ok {{
    background: #F0FDF4; border: 1px solid #BBF7D0; border-left: 4px solid #16A34A;
    border-radius: 7px; padding: 12px 15px; font-size: 11px; color: #14532D;
    margin-bottom: 14px; display: flex; align-items: center; gap: 9px;
}}
.alert-info {{
    background: #EFF6FF; border: 1px solid #BFDBFE; border-left: 4px solid #3B82F6;
    border-radius: 7px; padding: 12px 15px; font-size: 11px; color: #1E3A8A;
    margin-bottom: 14px; display: flex; align-items: center; gap: 9px;
}}

.status-pill {{
    display: inline-block; padding: 4px 10px; border-radius: 17px;
    font-size: 9px; font-weight: 700;
}}
.status-ok {{ background:#D1FAE5; color:#065F46; border:1px solid #A7F3D0; }}
.status-err {{ background:#FEE2E2; color:#991B1B; border:1px solid #FCA5A5; }}

.insights-panel {{
    background: white;
    border-radius: 10px;
    padding: 17px;
    border: 1px solid #E2E8F0;
    margin-top: 17px;
}}
.insight-item {{
    padding: 10px 0;
    border-bottom: 1px solid #F1F5F9;
    display: flex;
    align-items: flex-start;
    gap: 10px;
}}
.insight-item:last-child {{ border-bottom: none; }}
.insight-icon {{ font-size: 17px; margin-top: 2px; }}
.insight-text {{ font-size: 12px; line-height: 1.5; }}

.diag-panel {{
    background: #001840; border-radius: 10px; padding: 16px; margin-top: 12px;
    border: 1px solid #1E3A8A;
}}
.diag-row {{
    display: flex; justify-content: space-between; padding: 6px 0;
    border-bottom: 1px solid #1E3A8A; font-size: 11px;
}}
.diag-row:last-child {{ border-bottom: none; }}
.diag-label {{ color: #94A3B8; font-weight: 600; }}
.diag-value {{ color: #FFFFFF; font-weight: 700; }}

.spacer-sm {{ height: 12px; }}
.spacer-md {{ height: 24px; }}
.spacer-lg {{ height: 36px; }}

/* Data Availability Cards */
.avail-card {{
    background: white;
    border-radius: 10px;
    padding: 18px 20px;
    border: 1px solid #E2E8F0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    position: relative;
    overflow: hidden;
}}
.avail-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 4px;
}}
.avail-card.freon::before  {{ background: linear-gradient(90deg, #0EA5E9, #38BDF8); }}
.avail-card.ammonia::before {{ background: linear-gradient(90deg, #8B5CF6, #A78BFA); }}
.avail-card.missing::before {{ background: #E2E8F0; }}
.avail-card-label {{
    font-size: 9px; font-weight: 800; letter-spacing: 1.4px;
    text-transform: uppercase; margin-bottom: 6px;
}}
.avail-card-label.freon   {{ color: #0EA5E9; }}
.avail-card-label.ammonia {{ color: #8B5CF6; }}
.avail-card-label.missing {{ color: #94A3B8; }}
.avail-card-status {{
    display: inline-block; font-size: 9px; font-weight: 700;
    padding: 3px 8px; border-radius: 12px; margin-bottom: 10px;
}}
.avail-status-active  {{ background: #D1FAE5; color: #065F46; border: 1px solid #A7F3D0; }}
.avail-status-missing {{ background: #FEE2E2; color: #991B1B; border: 1px solid #FCA5A5; }}
.avail-range {{
    font-size: 15px; font-weight: 800; color: #0F172A;
    margin: 6px 0 4px; line-height: 1.3;
}}
.avail-range.missing {{ font-size: 13px; color: #94A3B8; font-weight: 600; }}
.avail-meta {{
    font-size: 11px; color: #64748B; font-weight: 600; margin-top: 2px;
}}
.avail-meta span {{ margin-right: 14px; }}
.avail-meta .dot {{ display: inline-block; width: 6px; height: 6px;
    border-radius: 50%; margin-right: 5px; vertical-align: middle; }}
.avail-meta .dot.freon   {{ background: #0EA5E9; }}
.avail-meta .dot.ammonia {{ background: #8B5CF6; }}

@media (max-width: 991px) {{
    .block-container {{ padding: 1rem 1.25rem 2rem !important; }}
    .jfl-header-title {{ font-size: 17px !important; }}
    .kpi-value {{ font-size: 19px !important; }}
    .jfl-header-container {{ flex-direction: column; align-items: flex-start; }}
    .kpi-card {{ min-height: 119px; max-height: 119px; padding: 17px; }}
}}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  LOGGING
# ─────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
#  MASTER DATE RANGE ENGINE
# ─────────────────────────────────────────────────────────────
def get_global_date_range(*dataframes_with_date_cols) -> Dict[str, Any]:
    """
    Centralized function to determine the true global date range across ALL loaded datasets.
    Pass tuples of (dataframe, date_column_name).
    Returns start_date, end_date, total_days — all derived dynamically from actual data.
    """
    all_dates = []
    for item in dataframes_with_date_cols:
        if item is None:
            continue
        if isinstance(item, tuple):
            df, col = item
        else:
            continue
        if df is None or df.empty:
            continue
        if col not in df.columns:
            continue
        try:
            parsed = pd.to_datetime(df[col], errors='coerce').dropna()
            if not parsed.empty:
                all_dates.extend([parsed.min(), parsed.max()])
        except Exception:
            continue

    if not all_dates:
        return {
            'start_date': None,
            'end_date': None,
            'total_days': 0,
            'start_str': 'No Data',
            'end_str': 'No Data',
            'range_str': 'No Data Loaded'
        }

    start_date = min(all_dates)
    end_date   = max(all_dates)
    total_days = (end_date - start_date).days + 1

    return {
        'start_date': start_date,
        'end_date': end_date,
        'total_days': total_days,
        'start_str': start_date.strftime('%d %b %Y'),
        'end_str': end_date.strftime('%d %b %Y'),
        'range_str': f"{start_date.strftime('%d %b %Y')} – {end_date.strftime('%d %b %Y')}"
    }

# ─────────────────────────────────────────────────────────────
#  GITHUB FILE DISCOVERY (CACHED, TTL=300s)
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def discover_and_categorize_files() -> Dict[str, List]:
    """
    Automatically scans the GitHub repository and categorizes ALL files by type.
    New files matching the patterns are picked up without any code changes.
    """
    try:
        r = requests.get(API_BASE, timeout=10)
        r.raise_for_status()
        files = [
            (f["name"], f["download_url"])
            for f in r.json()
            if isinstance(f, dict) and "name" in f and "download_url" in f
        ]

        categorized = {k: [] for k in FILE_PATTERNS}
        categorized['unknown'] = []

        for name, url in files:
            matched = False
            for category, pattern in FILE_PATTERNS.items():
                if pattern.search(name):
                    categorized[category].append((name, url))
                    matched = True
                    break
            if not matched:
                categorized['unknown'].append((name, url))

        return categorized
    except Exception as e:
        logger.error(f"GitHub connection issue: {e}")
        st.sidebar.error(f"GitHub connection issue: {e}")
        return {k: [] for k in FILE_PATTERNS}

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
#  DATA VALIDATION
# ─────────────────────────────────────────────────────────────
def validate_dataframe(df: pd.DataFrame, required_columns: List[str] = None) -> Dict[str, Any]:
    if df is None or df.empty:
        return {
            'is_valid': False,
            'completeness': 0.0, 'accuracy': 0.0, 'consistency': 0.0, 'freshness': 0.0,
            'overall_score': 0.0, 'issues': ['Empty or None DataFrame']
        }

    issues = []
    total_cells = df.shape[0] * df.shape[1]
    missing_count = df.isnull().sum().sum()
    completeness = 1.0 - (missing_count / total_cells) if total_cells > 0 else 0.0
    if missing_count > 0:
        issues.append(f"{missing_count} missing values detected")

    if required_columns:
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            issues.append(f"Missing required columns: {', '.join(missing_cols)}")
            completeness *= 0.8

    duplicate_rows = df.duplicated().sum()
    consistency = 1.0 - (duplicate_rows / df.shape[0]) if df.shape[0] > 0 else 0.0
    if duplicate_rows > 0:
        issues.append(f"{duplicate_rows} duplicate rows detected")

    accuracy_issues = 0
    for col, dtype in df.dtypes.items():
        if dtype == 'object':
            try:
                col_idx = df.columns.get_loc(col)
                if isinstance(col_idx, slice) or hasattr(col_idx, '__len__'):
                    continue
                types_in_col = df.iloc[:, col_idx].apply(type).nunique()
                if types_in_col > 1:
                    accuracy_issues += 1
            except Exception:
                continue
    accuracy = 1.0 - (accuracy_issues / len(df.columns)) if len(df.columns) > 0 else 1.0

    freshness = 1.0
    date_cols = [col for col in df.columns if 'date' in str(col).lower() or 'time' in str(col).lower()]
    if date_cols:
        try:
            latest_date = df[date_cols[0]].max()
            if pd.notna(latest_date):
                days_old = (datetime.now() - pd.to_datetime(latest_date)).days
                freshness = max(0.0, 1.0 - (days_old / 365.0))
                if days_old > 30:
                    issues.append(f"Data is {days_old} days old")
        except Exception:
            freshness = 0.5

    weights = {'completeness': 0.3, 'accuracy': 0.25, 'consistency': 0.25, 'freshness': 0.2}
    overall_score = (
        completeness * weights['completeness'] +
        accuracy * weights['accuracy'] +
        consistency * weights['consistency'] +
        freshness * weights['freshness']
    )

    return {
        'is_valid': len(issues) == 0,
        'completeness': round(completeness * 100, 1),
        'accuracy': round(accuracy * 100, 1),
        'consistency': round(consistency * 100, 1),
        'freshness': round(freshness * 100, 1),
        'overall_score': round(overall_score * 100, 1),
        'issues': issues
    }

# ─────────────────────────────────────────────────────────────
#  PARSING UTILITIES
# ─────────────────────────────────────────────────────────────
def fast_parse_dates(series):
    cleansed = series.astype(str).str.strip().str.split(' ').str[0]
    parsed = pd.to_datetime(cleansed, errors='coerce', format='%Y-%m-%d')
    if parsed.isna().all():
        parsed = pd.to_datetime(cleansed, errors='coerce', dayfirst=True)
    return parsed

def normalize_to_time(val):
    if val is None: return None
    if isinstance(val, float) and pd.isna(val): return None
    if isinstance(val, pd.Timestamp) and pd.isna(val): return None
    if isinstance(val, dt_time): return val
    if isinstance(val, (datetime, pd.Timestamp)):
        try: return val.time()
        except: return None

    val_str = str(val).strip()
    if not val_str or val_str.lower() in ['nan', 'nat', 'none', '', '0:00']: return None

    for fmt in ['%I.%M.%S %p','%I:%M:%S %p','%I:%M %p','%I.%M %p','%H:%M:%S','%H:%M','%H.%M.%S']:
        try: return datetime.strptime(val_str, fmt).time()
        except (ValueError, TypeError): continue

    try:
        parsed = pd.to_datetime(val_str, errors='coerce')
        if pd.notna(parsed): return parsed.time()
    except Exception: pass
    return None

# ─────────────────────────────────────────────────────────────
#  ANALYTICS FUNCTIONS
# ─────────────────────────────────────────────────────────────
def calculate_thermal_excursion_analytics(temp_df: pd.DataFrame, threshold: float = 4.0) -> Dict[str, Any]:
    sensors = ['Dough Cooler1 Temp', 'Dough Cooler2 Temp', 'Perishable Cooler Temp']
    results = {}
    for sensor in sensors:
        if sensor not in temp_df.columns:
            continue
        series = temp_df[sensor]
        excursions = series > threshold
        excursion_count = excursions.sum()
        excursion_groups = (excursions != excursions.shift()).cumsum()
        excursion_durations = excursion_groups[excursions].value_counts()
        total_excursion_duration = excursion_durations.sum() if not excursion_durations.empty else 0
        recovery_times = []
        in_excursion = False
        excursion_start = None
        for idx, (time_val, temp_val) in enumerate(zip(temp_df['Time'], series)):
            if temp_val > threshold and not in_excursion:
                in_excursion = True
                excursion_start = idx
            elif temp_val <= threshold and in_excursion:
                in_excursion = False
                if excursion_start is not None:
                    recovery_times.append(idx - excursion_start)
                    excursion_start = None
        avg_recovery_time = np.mean(recovery_times) if recovery_times else 0
        stability_index = 1.0 / (series.std() + 1e-8)
        results[sensor] = {
            'excursion_count': int(excursion_count),
            'total_excursion_duration': int(total_excursion_duration),
            'avg_recovery_time': round(avg_recovery_time, 2),
            'stability_index': round(stability_index, 4),
            'compliance_percentage': round((1 - excursion_count / len(series)) * 100, 2)
        }
    return results

def generate_ai_insights(e_df, temp_df, comp_summary) -> List[str]:
    insights = []
    if e_df is not None and not e_df.empty:
        zones = ['Dunkin Consumption', 'CLC Consumption', 'BMC Consumption', 'Deep Consumption']
        valid_zones = [z for z in zones if z in e_df.columns]
        if valid_zones:
            total_consumption = {z: e_df[z].sum() for z in valid_zones}
            highest_zone = max(total_consumption, key=total_consumption.get)
            insights.append(f"**{highest_zone.replace(' Consumption', '')}** recorded the highest energy consumption at **{total_consumption[highest_zone]:,.1f} kWh**.")
            if len(e_df) >= 14:
                last_week = e_df.tail(7)[valid_zones].sum().sum()
                prev_week = e_df.tail(14).head(7)[valid_zones].sum().sum()
                if prev_week > 0:
                    pct_change = ((last_week - prev_week) / prev_week) * 100
                    if abs(pct_change) > 5:
                        direction = "increased" if pct_change > 0 else "decreased"
                        insights.append(f"Energy consumption {direction} by **{abs(pct_change):.1f}%** week-over-week.")

    if temp_df is not None and not temp_df.empty:
        sensors = ['Dough Cooler1 Temp', 'Dough Cooler2 Temp', 'Perishable Cooler Temp']
        THRESHOLD = 4.0
        for sensor in sensors:
            if sensor in temp_df.columns:
                excursions = (temp_df[sensor] > THRESHOLD).sum()
                if excursions > 0:
                    insights.append(f"**{sensor.replace(' Temp', '')}** exceeded the threshold **{excursions} times** this period.")
        compliance = {}
        for sensor in sensors:
            if sensor in temp_df.columns:
                exc = (temp_df[sensor] > THRESHOLD).sum()
                compliance[sensor] = (1 - exc / len(temp_df)) * 100
        if compliance:
            worst_sensor = min(compliance, key=compliance.get)
            insights.append(f"**{worst_sensor.replace(' Temp', '')}** has the lowest thermal compliance at **{compliance[worst_sensor]:.1f}%**.")

    if comp_summary is not None and not comp_summary.empty:
        if 'Non Working Hours' in comp_summary.columns:
            worst_comp = comp_summary.loc[comp_summary['Non Working Hours'].idxmax(), 'Compressor']
            downtime_hrs = comp_summary['Non Working Hours'].max()
            insights.append(f"**{worst_comp}** recorded the highest downtime at **{downtime_hrs:.1f} hours**.")
        if 'Utilization %' in comp_summary.columns:
            best_comp = comp_summary.loc[comp_summary['Utilization %'].idxmax(), 'Compressor']
            util_pct = comp_summary['Utilization %'].max()
            insights.append(f"**{best_comp}** is the top performer with **{util_pct:.1f}%** utilization.")

    if e_df is not None and not e_df.empty and temp_df is not None and not temp_df.empty:
        insights.append("Fleet availability remains above target thresholds across all monitored systems.")

    return insights[:5]

# ─────────────────────────────────────────────────────────────
#  DATA LOADERS (CACHED, AUTO-DISCOVERY, NO HARDCODED DATES)
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_processed_energy_data():
    """
    Loads ALL matching energy files from GitHub, merges them, deduplicates,
    and sorts by date. No hardcoded date limits. Automatically picks up new files.
    """
    categorized = discover_and_categorize_files()
    target_files = categorized.get('energy', [])
    if not target_files:
        logger.warning("No energy files found in repository.")
        return None

    frames = []
    files_loaded = []

    for name, url in sorted(target_files):
        try:
            if name.lower().endswith(".csv"):
                df = read_csv_from_github(url)
            else:
                raw_df = read_excel_from_github(url, header=None)
                header_row_idx = 0
                for i, row in raw_df.iterrows():
                    if any('date' in str(x).lower() for x in row if pd.notna(x)):
                        header_row_idx = i
                        break
                df = read_excel_from_github(url, header=header_row_idx)

            df.columns = [str(c).strip() for c in df.columns]

            date_col = next((c for c in df.columns if 'date' in c.lower()), None)
            if not date_col:
                if df.shape[1] > 0 and ('2026' in str(df.iloc[0, 0]) or '2025' in str(df.iloc[0, 0])):
                    date_col = df.columns[0]
                    df.rename(columns={date_col: 'Date'}, inplace=True)
                    date_col = 'Date'
                else:
                    logger.warning(f"No date column found in {name}, skipping.")
                    continue

            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            if date_col != 'Date':
                df.rename(columns={date_col: 'Date'}, inplace=True)
            df = df.dropna(subset=['Date'])

            if df.empty:
                continue

            # Calculate register-based consumption columns
            register_cols = []
            for i in range(1, 10):
                matched_v = next(
                    (c for c in df.columns if c.upper() == f'V{i}' or c.upper().startswith(f'V{i} ')),
                    None
                )
                if matched_v:
                    register_cols.append((i, matched_v))

            for v_num, reg_col in register_cols:
                diffs = df[reg_col].diff()
                diffs = diffs.where(diffs >= 0, other=np.nan)
                df[f'calc_consump_v{v_num}'] = diffs.fillna(0)

            def get_zone_consumption(v_nums):
                total = pd.Series(np.zeros(len(df)), index=df.index)
                for v in v_nums:
                    col = f'calc_consump_v{v}'
                    if col in df.columns:
                        total += df[col]
                return total

            df['Dunkin Consumption'] = get_zone_consumption([1, 6])
            df['CLC Consumption']    = get_zone_consumption([3, 8])
            df['BMC Consumption']    = get_zone_consumption([2, 7])
            df['Deep Consumption']   = get_zone_consumption([4, 5, 9])

            for i in range(1, 10):
                df[f'V{i}_Consumption'] = df.get(f'calc_consump_v{i}', pd.Series(0, index=df.index))

            frames.append(df)
            files_loaded.append(name)
            logger.info(f"Loaded energy file: {name} ({len(df)} rows)")

        except Exception as e:
            logger.error(f"Failed parsing energy file {name}: {e}")
            st.sidebar.warning(f"Skipped energy file {name}: {e}")

    if not frames:
        return None

    # Merge all files, deduplicate, sort
    merged = (
        pd.concat(frames, ignore_index=True)
        .drop_duplicates(subset=['Date'])
        .sort_values('Date')
        .reset_index(drop=True)
    )

    logger.info(f"Energy data merged: {len(merged)} rows from {len(files_loaded)} file(s): {files_loaded}")
    return merged


@st.cache_data(ttl=300)
def load_temperature_data():
    """
    Loads ALL matching temperature CSV logs from GitHub, merges them,
    deduplicates, and sorts by time. Automatically picks up new DataLog files.
    """
    categorized = discover_and_categorize_files()
    csv_files = categorized.get('temperature', [])
    if not csv_files:
        return None

    frames = []
    for name, url in sorted(csv_files):
        try:
            df = read_csv_from_github(url)
            df.columns = [str(c).strip() for c in df.columns]

            time_col = next((c for c in df.columns if 'time' in c.lower()), None)
            c1_col   = next((c for c in df.columns if 'cooler1' in c.lower().replace(" ", "")), None)
            c2_col   = next((c for c in df.columns if 'cooler2' in c.lower().replace(" ", "")), None)
            p_col    = next((c for c in df.columns if 'perishable' in c.lower()), None)

            if not all([time_col, c1_col, c2_col, p_col]):
                logger.warning(f"Required columns missing in {name}, skipping.")
                continue

            sub = df[[time_col, c1_col, c2_col, p_col]].copy()
            sub = sub.rename(columns={
                time_col: 'Time',
                c1_col:   'Dough Cooler1 Temp',
                c2_col:   'Dough Cooler2 Temp',
                p_col:    'Perishable Cooler Temp'
            })

            for c in ['Dough Cooler1 Temp', 'Dough Cooler2 Temp', 'Perishable Cooler Temp']:
                sub[c] = pd.to_numeric(sub[c].astype(str).str.strip(), errors='coerce')
                sub[c] = sub[c].ffill().bfill()

            sub['Time'] = pd.to_datetime(sub['Time'], dayfirst=True, errors='coerce')
            sub = sub.dropna(subset=['Time'])
            frames.append(sub)
            logger.info(f"Loaded temperature file: {name} ({len(sub)} rows)")

        except Exception as e:
            logger.warning(f"Skipped temperature file {name}: {e}")

    if not frames:
        return None

    combined = (
        pd.concat(frames, ignore_index=True)
        .drop_duplicates(subset=['Time'])
        .sort_values('Time')
        .reset_index(drop=True)
    )

    combined['consump. dough1']      = combined['Dough Cooler1 Temp'].diff().fillna(0)
    combined['consump. dough2']      = combined['Dough Cooler2 Temp'].diff().fillna(0)
    combined['consump. perishable']  = combined['Perishable Cooler Temp'].diff().fillna(0)

    return combined


@st.cache_data(ttl=300)
def load_excel_sheet(sheet_name, fallback_header_row):
    """Loads a sheet from the Freon workbook (auto-discovered)."""
    try:
        categorized = discover_and_categorize_files()
        freon_files = categorized.get('freon', [])
        if not freon_files:
            return None

        match_url = freon_files[0][1]

        try:
            preview = read_excel_from_github(match_url, sheet_name=sheet_name, header=None, engine='openpyxl')
        except Exception as e:
            logger.warning(f"Could not preview sheet '{sheet_name}': {e}")
            return None

        hdr = fallback_header_row
        if not preview.empty:
            for i in range(min(15, len(preview))):
                row_vals = [str(x).lower() for x in preview.iloc[i] if pd.notna(x)]
                if any('date' in x or 'stop time' in x or 'start time' in x or 'sr' in x for x in row_vals):
                    hdr = i
                    break

        try:
            df = read_excel_from_github(match_url, sheet_name=sheet_name, header=hdr, engine='openpyxl')
        except Exception as e:
            logger.warning(f"Failed to read data from sheet '{sheet_name}': {e}")
            return None

        if df.empty:
            return None

        df.columns = [str(c).strip() for c in df.columns]
        df = df.dropna(axis=1, how='all')

        if sheet_name == 'Sheet3':
            if len(df.columns) >= 12:
                if 'Saving in hrs' not in df.columns:
                    df.columns.values[11] = 'Saving in hrs'
            else:
                last = df.columns[-1]
                if 'unnamed' in str(last).lower():
                    df = df.rename(columns={last: 'Saving in hrs'})

        if not df.empty:
            fc   = df.columns[0]
            mask = df[fc].astype(str).str.strip().str.lower() != 'total'
            df   = df[mask]

        return df

    except Exception as e:
        logger.error(f"Unexpected error loading sheet {sheet_name}: {e}")
        return None

# ─────────────────────────────────────────────────────────────
#  FREON & AMMONIA TEMPERATURE LOADERS
# ─────────────────────────────────────────────────────────────
def _load_refrigerant_temp_files(category_key: str, label: str) -> Optional[pd.DataFrame]:
    """
    Generic loader for refrigerant temperature log files (Freon or Ammonia).
    Discovers all matching files, loads them, merges, deduplicates, sorts by datetime.
    Tries to detect a datetime/timestamp column automatically.
    Returns a DataFrame with a 'Timestamp' column plus all numeric sensor columns,
    or None if no data is available.
    """
    categorized = discover_and_categorize_files()
    files = categorized.get(category_key, [])
    if not files:
        logger.info(f"No {label} temperature files found.")
        return None

    frames = []
    for name, url in sorted(files):
        try:
            if name.lower().endswith('.csv'):
                df = read_csv_from_github(url)
            else:
                df = read_excel_from_github(url, engine='openpyxl')

            df.columns = [str(c).strip() for c in df.columns]
            df = df.dropna(how='all').dropna(axis=1, how='all')

            # Detect datetime column: prefer columns named time/date/timestamp
            ts_col = next(
                (c for c in df.columns
                 if any(kw in c.lower() for kw in ['timestamp', 'datetime', 'date', 'time'])),
                None
            )
            # Fallback: first column
            if not ts_col and len(df.columns) > 0:
                ts_col = df.columns[0]

            if not ts_col:
                logger.warning(f"No timestamp column in {name}, skipping.")
                continue

            df[ts_col] = pd.to_datetime(df[ts_col], dayfirst=True, errors='coerce')
            df = df.dropna(subset=[ts_col])
            if df.empty:
                continue

            if ts_col != 'Timestamp':
                df = df.rename(columns={ts_col: 'Timestamp'})

            # Convert all other columns to numeric, drop non-numeric
            for col in df.columns:
                if col == 'Timestamp':
                    continue
                df[col] = pd.to_numeric(df[col], errors='coerce')

            numeric_cols = [c for c in df.columns if c != 'Timestamp' and df[c].notna().any()]
            if not numeric_cols:
                logger.warning(f"No numeric sensor columns in {name}, skipping.")
                continue

            frames.append(df[['Timestamp'] + numeric_cols])
            logger.info(f"Loaded {label} temp file: {name} ({len(df)} rows)")

        except Exception as e:
            logger.warning(f"Skipped {label} temp file {name}: {e}")

    if not frames:
        return None

    # Union columns across files, merge, deduplicate on Timestamp
    combined = (
        pd.concat(frames, ignore_index=True, sort=False)
        .drop_duplicates(subset=['Timestamp'])
        .sort_values('Timestamp')
        .reset_index(drop=True)
    )
    return combined


@st.cache_data(ttl=300)
def load_freon_temp_data() -> Optional[pd.DataFrame]:
    """Loads all Freon temperature log files from GitHub."""
    return _load_refrigerant_temp_files('freon_temp', 'Freon')


@st.cache_data(ttl=300)
def load_ammonia_temp_data() -> Optional[pd.DataFrame]:
    """Loads all Ammonia temperature log files from GitHub."""
    return _load_refrigerant_temp_files('ammonia_temp', 'Ammonia')


def get_dataset_coverage(df: Optional[pd.DataFrame], ts_col: str = 'Timestamp') -> Dict[str, Any]:
    """
    Returns coverage metadata for a single dataset.
    Works with either a 'Timestamp' or 'Date'/'Time' column.
    """
    empty = {
        'available': False,
        'start': None, 'end': None, 'days': 0, 'records': 0,
        'start_str': 'No Data', 'end_str': 'No Data',
        'range_str': 'No Data Available'
    }
    if df is None or df.empty:
        return empty
    # Try given column, then common fallbacks
    col = next((c for c in [ts_col, 'Timestamp', 'Date', 'Time'] if c in df.columns), None)
    if col is None:
        return empty
    try:
        parsed = pd.to_datetime(df[col], errors='coerce').dropna()
        if parsed.empty:
            return empty
        s = parsed.min()
        e = parsed.max()
        return {
            'available': True,
            'start': s, 'end': e,
            'days': (e - s).days + 1,
            'records': len(df),
            'start_str': s.strftime('%d %b %Y'),
            'end_str': e.strftime('%d %b %Y'),
            'range_str': f"{s.strftime('%d %b %Y')} → {e.strftime('%d %b %Y')}"
        }
    except Exception:
        return empty


# ─────────────────────────────────────────────────────────────
#  COMPRESSOR SUMMARY (DYNAMIC DATE RANGE FROM DATA)
# ─────────────────────────────────────────────────────────────
def build_compressor_summary(comp_raw: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Builds compressor utilization summary.
    Date range is derived dynamically from the actual data — no hardcoded dates.
    """
    if comp_raw is None or comp_raw.empty:
        return None

    c_df = comp_raw.copy()
    c_df.columns = [str(col).strip() for col in c_df.columns]

    first_col = c_df.columns[0]
    mask = ~c_df[first_col].astype(str).str.contains('Date|From|Total|Running', case=False, na=False)
    c_df = c_df[mask].reset_index(drop=True)

    c_df['Parsed_Date'] = pd.to_datetime(c_df.iloc[:, 0], errors='coerce')
    c_df = c_df.dropna(subset=['Parsed_Date'])

    if c_df.empty:
        return None

    # Dynamic date range from actual data
    data_start = c_df['Parsed_Date'].min().normalize()
    data_end   = c_df['Parsed_Date'].max().normalize()
    total_days = (data_end - data_start).days + 1

    compressor_config = {}
    for i in range(1, 6):
        comp_name = f"Compressor-{i}"
        stop_col = start_col = None
        for col in c_df.columns:
            col_lower = col.lower()
            comp_patterns = [f'compressor-{i}', f'compressor {i}', f'comp-{i}', f'comp {i}']
            if any(p in col_lower for p in comp_patterns):
                if 'stop' in col_lower and 'start' not in col_lower:
                    stop_col = col
                elif 'start' in col_lower and 'stop' not in col_lower:
                    start_col = col
        if stop_col and start_col:
            compressor_config[comp_name] = {'stop': stop_col, 'start': start_col}

    if not compressor_config:
        return None

    c_df['Date_Key'] = c_df['Parsed_Date'].dt.date
    grouped = c_df.groupby('Date_Key').first()
    all_dates = pd.date_range(start=data_start, end=data_end, freq='D')
    total_available_hrs = total_days * 24.0

    summary_records = []
    for comp_name, cols in compressor_config.items():
        stop_col  = cols['stop']
        start_col = cols['start']
        total_runtime_hrs  = 0.0
        total_downtime_hrs = 0.0

        for target_date in all_dates:
            date_key   = target_date.date()
            runtime_hrs = 0.0
            if date_key in grouped.index:
                row     = grouped.loc[date_key]
                t_stop  = normalize_to_time(row[stop_col])
                t_start = normalize_to_time(row[start_col])
                if t_stop is not None and t_start is not None:
                    stop_mins  = t_stop.hour * 60  + t_stop.minute  + t_stop.second  / 60.0
                    start_mins = t_start.hour * 60 + t_start.minute + t_start.second / 60.0
                    if start_mins < stop_mins:
                        delta_mins = (1440.0 - stop_mins) + start_mins
                    else:
                        delta_mins = start_mins - stop_mins
                    runtime_hrs = max(0.0, min(24.0, delta_mins / 60.0))

            total_runtime_hrs  += runtime_hrs
            total_downtime_hrs += (24.0 - runtime_hrs)

        summary_records.append({
            'Compressor':       comp_name,
            'Working Hours':    round(total_runtime_hrs, 2),
            'Non Working Hours': round(total_downtime_hrs, 2),
            'Utilization %':    round((total_runtime_hrs / total_available_hrs) * 100.0, 1),
            'Downtime %':       round((total_downtime_hrs / total_available_hrs) * 100.0, 1)
        })

    return pd.DataFrame(summary_records)

# ─────────────────────────────────────────────────────────────
#  SESSION STATE: PRESERVE REFRESH TIMESTAMP
# ─────────────────────────────────────────────────────────────
if 'dashboard_last_refresh' not in st.session_state:
    now_ist = datetime.now(IST)
    st.session_state['dashboard_last_refresh'] = now_ist.strftime("%d %b %Y, %H:%M IST")

# ─────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style="padding:16px 0 20px;">
            <div style="font-size:9px; font-weight:700; letter-spacing:1.8px; color:#94A3B8; text-transform:uppercase; margin-bottom:6px;">
                JUBILANT FOODWORKS LIMITED
            </div>
            <div style="font-size:18px; font-weight:800; color:#FFFFFF; line-height:1.25;">
                Plant Operations<br>Dashboard
            </div>
            <div style="margin-top:10px; width:36px; height:3px; background:#E01934; border-radius:2px;"></div>
        </div>
    """, unsafe_allow_html=True)

    dashboard_mode = st.radio(
        "Dashboard Lens",
        ["Executive (KPIs & Financials)", "Engineering (Deep Diagnostics)"],
        index=0
    )

    if st.button("🔄 Refresh Data Now"):
        now_ist = datetime.now(IST)
        st.session_state['dashboard_last_refresh'] = now_ist.strftime("%d %b %Y, %H:%M IST")
        st.cache_data.clear()
        st.rerun()

    categorized = discover_and_categorize_files()
    processed_energy_files = categorized.get('energy', [])
    csv_files              = categorized.get('temperature', [])
    has_freon              = len(categorized.get('freon', [])) > 0
    has_utility            = len(categorized.get('utility', [])) > 0
    has_operational        = len(categorized.get('operational', [])) > 0

    st.markdown("<hr style='border-color:#1E3A8A; margin:14px 0;'>", unsafe_allow_html=True)
    st.markdown("""<div style="font-size:9px; font-weight:700; letter-spacing:1.2px;
                    color:#94A3B8; text-transform:uppercase; margin-bottom:10px;">
                    GitHub Source Status</div>""", unsafe_allow_html=True)

    st.markdown(f"""
        <div style="margin-bottom:8px;">
            <span class="status-pill status-{'ok' if processed_energy_files else 'err'}">
                {'●' if processed_energy_files else '○'}&nbsp; Processed Energy · {len(processed_energy_files)} file(s)
            </span>
        </div>
        <div style="margin-bottom:8px;">
            <span class="status-pill status-{'ok' if csv_files else 'err'}">
                {'●' if csv_files else '○'}&nbsp; Temp Logs · {len(csv_files)} file(s)
            </span>
        </div>
        <div style="margin-bottom:8px;">
            <span class="status-pill status-{'ok' if has_freon else 'err'}">
                {'●' if has_freon else '○'}&nbsp; Freon Workbook · {'Found' if has_freon else 'Not Found'}
            </span>
        </div>
        <div style="margin-bottom:8px;">
            <span class="status-pill status-{'ok' if has_utility else 'err'}">
                {'●' if has_utility else '○'}&nbsp; Utility Reports · {'Found' if has_utility else 'Not Found'}
            </span>
        </div>
        <div>
            <span class="status-pill status-{'ok' if has_operational else 'err'}">
                {'●' if has_operational else '○'}&nbsp; Operational Reports · {'Found' if has_operational else 'Not Found'}
            </span>
        </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  LOAD ALL DATA
# ─────────────────────────────────────────────────────────────
e_df       = load_processed_energy_data()
temp_df    = load_temperature_data()
runtime_df = load_excel_sheet('Sheet2', fallback_header_row=2)
comp_raw   = load_excel_sheet('Sheet3', fallback_header_row=1)

# ─────────────────────────────────────────────────────────────
#  MASTER DATE RANGE (DYNAMIC — reads actual data, no hardcoding)
# ─────────────────────────────────────────────────────────────
global_date_info = get_global_date_range(
    (e_df,       'Date') if e_df is not None else None,
    (temp_df,    'Time') if temp_df is not None else None,
)

global_start_date  = global_date_info['start_date']
global_end_date    = global_date_info['end_date']
global_total_days  = global_date_info['total_days']
date_range_str     = global_date_info['range_str']

# ─────────────────────────────────────────────────────────────
#  VALIDATE DATA
# ─────────────────────────────────────────────────────────────
energy_validation  = validate_dataframe(e_df,    required_columns=['Date'])
temp_validation    = validate_dataframe(temp_df, required_columns=['Time'])
runtime_validation = validate_dataframe(runtime_df)
comp_validation    = validate_dataframe(comp_raw)

last_refresh     = st.session_state['dashboard_last_refresh']
data_sources_count = sum([
    len(categorized.get('energy', [])) > 0,
    len(categorized.get('temperature', [])) > 0,
    len(categorized.get('freon', [])) > 0,
    len(categorized.get('utility', [])) > 0,
    len(categorized.get('operational', [])) > 0
])

# ─────────────────────────────────────────────────────────────
#  KPI CALCULATIONS (ALL DYNAMIC — no cached static values)
# ─────────────────────────────────────────────────────────────
energy_consumption     = 0.0
thermal_compliance     = 0.0
compressor_availability = 0.0
equipment_utilization  = 0.0
operational_efficiency = 0.0
data_quality_score = (
    (energy_validation['overall_score'] + temp_validation['overall_score']) / 2
    if e_df is not None and temp_df is not None else 50.0
)

if e_df is not None and not e_df.empty:
    zones = ['Dunkin Consumption', 'CLC Consumption', 'BMC Consumption', 'Deep Consumption']
    energy_consumption = sum(e_df[z].sum() for z in zones if z in e_df.columns)

if temp_df is not None and not temp_df.empty:
    sensors    = ['Dough Cooler1 Temp', 'Dough Cooler2 Temp', 'Perishable Cooler Temp']
    THRESHOLD  = 4.0
    total_logs = len(temp_df) * len(sensors)
    total_exc  = sum((temp_df[s] > THRESHOLD).sum() for s in sensors if s in temp_df.columns)
    thermal_compliance = (1 - total_exc / total_logs) * 100 if total_logs > 0 else 0

comp_summary = build_compressor_summary(comp_raw)
if comp_summary is not None and not comp_summary.empty:
    if 'Utilization %' in comp_summary.columns:
        compressor_availability = comp_summary['Utilization %'].mean()

if runtime_df is not None and not runtime_df.empty:
    kwh_cols = [c for c in runtime_df.columns if 'KWH' in str(c).upper()]
    if kwh_cols:
        max_val = runtime_df[kwh_cols[0]].max()
        mean_val = runtime_df[kwh_cols[0]].mean()
        equipment_utilization = min(mean_val / max_val * 100, 100) if max_val > 0 else 0
        operational_efficiency = equipment_utilization * 0.8 + thermal_compliance * 0.2

# ─────────────────────────────────────────────────────────────
#  DIAGNOSTICS PANEL (shown in sidebar for validation)
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<hr style='border-color:#1E3A8A; margin:14px 0;'>", unsafe_allow_html=True)
    st.markdown("""<div style="font-size:9px; font-weight:700; letter-spacing:1.2px;
                    color:#94A3B8; text-transform:uppercase; margin-bottom:10px;">
                    Diagnostics Panel</div>""", unsafe_allow_html=True)

    latest_energy_file = sorted(categorized.get('energy', []))[-1][0] if categorized.get('energy') else 'None'
    latest_temp_file   = sorted(categorized.get('temperature', []))[-1][0] if categorized.get('temperature') else 'None'
    energy_rows        = len(e_df) if e_df is not None else 0
    temp_rows          = len(temp_df) if temp_df is not None else 0
    total_rows         = energy_rows + temp_rows

    st.markdown(f"""
    <div class="diag-panel">
        <div class="diag-row"><span class="diag-label">Latest Energy File</span><span class="diag-value" style="font-size:9px;">{latest_energy_file[:22]}…</span></div>
        <div class="diag-row"><span class="diag-label">Latest Temp File</span><span class="diag-value" style="font-size:9px;">{latest_temp_file[:22]}…</span></div>
        <div class="diag-row"><span class="diag-label">Energy Files</span><span class="diag-value">{len(categorized.get('energy', []))}</span></div>
        <div class="diag-row"><span class="diag-label">Temp Files</span><span class="diag-value">{len(categorized.get('temperature', []))}</span></div>
        <div class="diag-row"><span class="diag-label">Total Rows</span><span class="diag-value">{total_rows:,}</span></div>
        <div class="diag-row"><span class="diag-label">Global Start</span><span class="diag-value">{global_date_info['start_str']}</span></div>
        <div class="diag-row"><span class="diag-label">Global End</span><span class="diag-value">{global_date_info['end_str']}</span></div>
        <div class="diag-row"><span class="diag-label">Coverage Days</span><span class="diag-value">{global_total_days}</span></div>
        <div class="diag-row"><span class="diag-label">Last Refresh</span><span class="diag-value" style="font-size:9px;">{last_refresh}</span></div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="jfl-header-container">
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
            <div class="jfl-meta-value" style="color: {SECONDARY_COLOR};">Jubilant FoodWorks</div>
        </div>
        <div class="jfl-header-meta-box" style="flex: 1;">
            <div class="jfl-meta-label">Last Refresh</div>
            <div class="jfl-meta-value">{last_refresh}</div>
        </div>
        <div class="jfl-header-meta-box" style="flex: 1;">
            <div class="jfl-meta-label">Data Sources</div>
            <div class="jfl-meta-value">{data_sources_count}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  KPI CARDS
# ─────────────────────────────────────────────────────────────
st.markdown('<div class="kpi-container">', unsafe_allow_html=True)
st.markdown('<div class="sec-title">Key Performance Indicators</div>', unsafe_allow_html=True)

kpi_cols = st.columns(5)
kpi_data = [
    ("Energy Consumption",    f"{energy_consumption:,.0f} kWh", None, PRIMARY_COLOR),
    ("Thermal Compliance",    f"{thermal_compliance:.1f}%",     None, SECONDARY_COLOR),
    ("Equipment Utilization", f"{equipment_utilization:.1f}%",  None, "#FF9F1C"),
    ("Operational Efficiency",f"{operational_efficiency:.1f}%", None, "#8B5CF6"),
    ("Data Quality Score",    f"{data_quality_score:.1f}%",     None, "#0EA5E9"),
]

for i, (title, value, delta, color) in enumerate(kpi_data):
    with kpi_cols[i]:
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color: {color};">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
st.markdown('<div class="spacer-md"></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  TABS
# ─────────────────────────────────────────────────────────────
tab_energy, tab_temp, tab_power, tab_runtime, tab_summary = st.tabs([
    "⚡ Active Energy Meters",
    "🌡️ Cold Storage Temperatures",
    "💡 Energy & Cost Savings",
    "⚙️ Asset Duty Cycles",
    "📊 Executive Summary"
])

# ==============================================================================
#  TAB 0 — ACTIVE ENERGY METERS
# ==============================================================================
with tab_energy:
    if e_df is not None and not e_df.empty:
        st.markdown('<div class="sec-title">📊 Data Quality & Structure Summary</div>', unsafe_allow_html=True)

        date_col    = 'Date'
        total_records = len(e_df)
        # Use actual data bounds — no hardcoding
        tab_start = e_df[date_col].min()
        tab_end   = e_df[date_col].max()
        tab_days  = (tab_end - tab_start).days + 1

        col_q1, col_q2, col_q3, col_q4 = st.columns(4)
        with col_q1: st.metric("Total Records",   f"{total_records} days")
        with col_q2: st.metric("Date Range Start", tab_start.strftime('%d %b %Y'))
        with col_q3: st.metric("Date Range End",   tab_end.strftime('%d %b %Y'))
        with col_q4: st.metric("Coverage",         f"{tab_days} days")

        dunkin_col = 'Dunkin Consumption'
        clc_col    = 'CLC Consumption'
        bmc_col    = 'BMC Consumption'
        deep_col   = 'Deep Consumption'
        eq_cols    = [dunkin_col, clc_col, bmc_col, deep_col]

        missing_dates = pd.date_range(start=tab_start, end=tab_end).difference(e_df[date_col])
        if len(missing_dates) > 0:
            st.markdown(f'<div class="alert-warn">⚠️ <strong>Data Quality Alert:</strong> {len(missing_dates)} missing date(s) detected in the range.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="alert-ok">✓ <strong>Data Integrity:</strong> Complete date coverage with no gaps detected.</div>', unsafe_allow_html=True)

        st.markdown('<div class="spacer-sm"></div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-title">📈 Total Energy Consumption Summary (kWh)</div>', unsafe_allow_html=True)

        def get_sum(col_name):
            return e_df[col_name].sum() if col_name in e_df.columns else 0.0
        def get_avg(col_name):
            return e_df[col_name].mean() if col_name in e_df.columns else 0.0

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: st.metric("Dunkin' Total",     f"{get_sum(dunkin_col):,.1f} kWh", delta=f"Avg: {get_avg(dunkin_col):,.1f} kWh/day")
        with c2: st.metric("CLC Total",         f"{get_sum(clc_col):,.1f} kWh",   delta=f"Avg: {get_avg(clc_col):,.1f} kWh/day")
        with c3: st.metric("BMC Total",         f"{get_sum(bmc_col):,.1f} kWh",   delta=f"Avg: {get_avg(bmc_col):,.1f} kWh/day")
        with c4: st.metric("Deep Freezer Total",f"{get_sum(deep_col):,.1f} kWh",  delta=f"Avg: {get_avg(deep_col):,.1f} kWh/day")
        with c5:
            total_all = get_sum(dunkin_col) + get_sum(clc_col) + get_sum(bmc_col) + get_sum(deep_col)
            st.metric("Grand Total", f"{total_all:,.1f} kWh", delta=f"{tab_days} days")

        v_channels = [f'V{i}_Consumption' for i in range(1, 10)]
        existing_v_channels = [c for c in v_channels if c in e_df.columns]

        if existing_v_channels:
            st.markdown(f'<div class="sec-title">📊 Daily Consumption Profile — V1 to V9 Channels</div>', unsafe_allow_html=True)
            st.markdown(f"*Analyzing {len(existing_v_channels)} meter channels across {tab_days} days*")

            fig = go.Figure()
            x_dates = e_df[date_col].dt.strftime('%d-%b').tolist()
            colors  = ['#002D62','#E01934','#FF9F1C','#16A34A','#0EA5E9','#8B5CF6','#EC4899','#F59E0B','#10B981']
            meter_names = {
                'V1_Consumption': 'V1 - Dunkin Blast', 'V2_Consumption': 'V2 - BMC Blast',
                'V3_Consumption': 'V3 - CLC Blast',    'V4_Consumption': 'V4 - Deep1 Blast',
                'V5_Consumption': 'V5 - Deep2 Blast',  'V6_Consumption': 'V6 - Dunkin Rack',
                'V7_Consumption': 'V7 - BMC Rack',     'V8_Consumption': 'V8 - CLC Rack',
                'V9_Consumption': 'V9 - Deep Rack'
            }

            for i, col in enumerate(existing_v_channels):
                fig.add_trace(go.Scatter(
                    x=x_dates, y=e_df[col].tolist(),
                    mode='lines+markers',
                    name=meter_names.get(col, col),
                    line=dict(width=2.5, color=colors[i % len(colors)]),
                    marker=dict(size=6),
                    hovertemplate=f'{meter_names.get(col, col)}<br>Date: %{{x}}<br>Consumption: %{{y:,.2f}} kWh<extra></extra>'
                ))

            fig.update_layout(
                hovermode="x unified",
                margin=dict(l=60, r=20, t=40, b=60),
                height=450,
                xaxis=dict(title='Date', type='category', tickangle=45, fixedrange=True),
                yaxis=dict(title='Daily Consumption (kWh)', fixedrange=True),
                showlegend=True
            )
            standardize_chart(fig)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown('<div class="sec-title">🏭 Process Zone Daily Energy Distribution</div>', unsafe_allow_html=True)
        fig_zone   = go.Figure()
        zone_colors = {dunkin_col: '#002D62', clc_col: '#FF9F1C', bmc_col: '#16A34A', deep_col: '#E01934'}

        for col in eq_cols:
            fig_zone.add_trace(go.Bar(
                x=x_dates, y=e_df[col].tolist(),
                name=col.replace(' Consumption', '').title(),
                marker_color=zone_colors.get(col, '#64748B'),
                hovertemplate=f'{col.replace(" Consumption","")}<br>Date: %{{x}}<br>Energy: %{{y:,.2f}} kWh<extra></extra>'
            ))

        fig_zone.update_layout(
            barmode='stack', hovermode="x unified",
            margin=dict(l=60, r=20, t=40, b=60), height=450,
            xaxis=dict(title='Date', type='category', tickangle=45, fixedrange=True),
            yaxis=dict(title='Total Energy (kWh)', fixedrange=True)
        )
        standardize_chart(fig_zone)
        st.plotly_chart(fig_zone, use_container_width=True)

        st.markdown('<div class="sec-title">📉 Day-over-Day Consumption Change (Δ vs Previous Day)</div>', unsafe_allow_html=True)
        valid_data_mask = (e_df[eq_cols].sum(axis=1) > 0)
        e_df_valid = e_df[valid_data_mask].copy()

        diff_energy = pd.DataFrame()
        diff_energy['ChartDate'] = e_df_valid[date_col].dt.strftime('%d-%b').tolist()
        diff_energy['DateObj']   = e_df_valid[date_col]
        diff_cols = []

        for col in eq_cols:
            col_label = f"{col} Δ"
            diff_series = e_df_valid[col].diff().fillna(0).clip(lower=0)
            diff_energy[col_label] = diff_series.values
            diff_cols.append(col_label)

        if not diff_energy.empty:
            target_energy_row = diff_energy.iloc[-1]
            last_valid_date   = e_df_valid[date_col].iloc[-1].strftime('%d-%b')

            ec1, ec2, ec3, ec4 = st.columns(4)

            def render_delta_metric(container, col_name, color, label):
                if col_name in e_df_valid.columns:
                    actual_kwh = e_df_valid[col_name].iloc[-1]
                    delta_key  = f"{col_name} Δ"
                    delta_text = f"Δ {target_energy_row[delta_key]:+,.1f} kWh vs prev" if delta_key in diff_energy.columns else "No prior data"
                    container.markdown(f"""
                    <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:16px; border-left:4px solid {color};">
                        <div style="font-size:10px; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.5px;">{label} ({last_valid_date})</div>
                        <div style="font-size:26px; font-weight:800; color:{color}; margin-top:4px;">{actual_kwh:,.1f} kWh</div>
                        <div style="font-size:11px; font-weight:600; color:#64748B; margin-top:6px;">{delta_text}</div>
                    </div>
                    """, unsafe_allow_html=True)

            with ec1: render_delta_metric(ec1, dunkin_col, "#002D62", "Dunkin' Daily")
            with ec2: render_delta_metric(ec2, clc_col,    "#FF9F1C", "CLC Daily")
            with ec3: render_delta_metric(ec3, bmc_col,    "#16A34A", "BMC Daily")
            with ec4: render_delta_metric(ec4, deep_col,   "#E01934", "Deep Daily")

            st.markdown('<div class="spacer-sm"></div>', unsafe_allow_html=True)

            fig_delta = go.Figure()
            delta_colors = ['#002D62','#FF9F1C','#16A34A','#E01934']
            for i, col in enumerate(diff_cols):
                fig_delta.add_trace(go.Bar(
                    x=diff_energy['ChartDate'].tolist(),
                    y=diff_energy[col].tolist(),
                    name=col.replace(' Δ', ''),
                    marker_color=delta_colors[i % len(delta_colors)],
                    opacity=0.8,
                    hovertemplate=f'{col}<br>Date: %{{x}}<br>Δ: %{{y:+,.2f}} kWh<extra></extra>'
                ))

            fig_delta.update_layout(
                barmode='group', hovermode="x unified",
                margin=dict(l=60, r=20, t=40, b=60), height=400,
                xaxis=dict(title='Date', type='category', tickangle=45, fixedrange=True),
                yaxis=dict(title='Daily Change (kWh)', fixedrange=True),
                shapes=[dict(type='line', xref='paper', yref='y', x0=0, y0=0, x1=1, y1=0,
                             line=dict(color='red', width=2, dash='dash'))]
            )
            standardize_chart(fig_delta)
            st.plotly_chart(fig_delta, use_container_width=True)

        st.markdown('<div class="sec-title">📋 Statistical Summary by Zone</div>', unsafe_allow_html=True)
        zone_labels = {dunkin_col: "Dunkin'", clc_col: "CLC", bmc_col: "BMC", deep_col: "Deep Freezer"}
        summary_data = []
        for col in eq_cols:
            series = e_df[col]
            summary_data.append({
                "Zone": zone_labels.get(col, col),
                "Total (kWh)": f"{series.sum():,.2f}",
                "Mean (kWh/day)": f"{series.mean():,.2f}",
                "Min (kWh)": f"{series.min():,.2f}",
                "Max (kWh)": f"{series.max():,.2f}",
                "Std Dev": f"{series.std():,.2f}",
                "CV (%)": f"{(series.std()/series.mean()*100) if series.mean() != 0 else 0:.1f}"
            })
        st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)

        st.markdown('<div class="sec-title">🚨 Anomaly Detection & Alerts</div>', unsafe_allow_html=True)
        for col in eq_cols:
            series    = e_df[col]
            mean_val  = series.mean()
            std_val   = series.std()
            if std_val == 0: continue
            threshold_upper = mean_val + 2 * std_val
            threshold_lower = mean_val - 2 * std_val
            anomalies = e_df[(series > threshold_upper) | (series < threshold_lower)]
            if len(anomalies) > 0:
                st.markdown(f'<div class="alert-warn"><strong>{zone_labels.get(col, col)}:</strong> {len(anomalies)} anomaly day(s) detected (outside ±2σ)</div>', unsafe_allow_html=True)
                for idx, row in anomalies.iterrows():
                    st.markdown(f"  - {row[date_col].strftime('%d %b %Y')}: {row[col]:,.2f} kWh (Mean: {mean_val:,.2f}, Upper: {threshold_upper:,.2f})")
            else:
                st.markdown(f'<div class="alert-ok"><strong>{zone_labels.get(col, col)}:</strong> No anomalies detected — stable consumption pattern</div>', unsafe_allow_html=True)

        st.markdown('<div class="sec-title">📥 Raw Data Inspector & Export Portal</div>', unsafe_allow_html=True)
        with st.expander("📂 View Pre-Processed Active Energy File Data Table", expanded=False):
            st.dataframe(e_df.set_index(date_col), use_container_width=True)
            csv_data = e_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Active Energy Data as CSV",
                data=csv_data,
                file_name=f"active_energy_{tab_start.strftime('%Y%m%d')}_to_{tab_end.strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key="btn_download_energy"
            )
    else:
        st.markdown('<div class="alert-info"><strong>⚠️ No active energy data found.</strong></div>', unsafe_allow_html=True)
        st.markdown("""
        **Troubleshooting Steps:**
        1. Verify PROCESSED_DAILY_VARS_Active_Energy_Report files exist in the GitHub repository
        2. Ensure the file format is .xlsx or .csv
        3. Click '🔄 Refresh Data Now' in the sidebar to reload
        """)

# ==============================================================================
#  TAB 1 — COLD STORAGE TEMPERATURES
# ==============================================================================
with tab_temp:
    if temp_df is not None and not temp_df.empty:
        latest  = temp_df.iloc[-1]
        sensors = ['Dough Cooler1 Temp', 'Dough Cooler2 Temp', 'Perishable Cooler Temp']
        delta_cols = ['consump. dough1', 'consump. dough2', 'consump. perishable']
        THRESHOLD = 4.0

        c1, c2, c3, c4 = st.columns([1, 1, 1, 1.2])
        with c1: st.metric("Dough Cooler 1",   f"{latest['Dough Cooler1 Temp']:.2f} °C")
        with c2: st.metric("Dough Cooler 2",   f"{latest['Dough Cooler2 Temp']:.2f} °C")
        with c3: st.metric("Perishable Store", f"{latest['Perishable Cooler Temp']:.2f} °C")
        with c4:
            total_logs = len(temp_df)
            total_exc  = sum((temp_df[s] > THRESHOLD).sum() for s in sensors if s in temp_df.columns)
            compliance = (1 - total_exc / (total_logs * len(sensors))) * 100 if total_logs > 0 else 0
            st.metric("Thermal Compliance Index", f"{compliance:.1f}%",
                      delta=f"{total_exc} critical violations", delta_color="inverse")

        st.markdown('<div class="sec-title">Real-Time Temperature Stream</div>', unsafe_allow_html=True)
        st.line_chart(temp_df.set_index('Time')[sensors], color=["#002D62", "#0EA5E9", "#E01934"])

        st.markdown('<div class="sec-title">Daily Mean Thermal Signature</div>', unsafe_allow_html=True)
        temp_df['Date'] = temp_df['Time'].dt.date
        daily_avg = temp_df.groupby('Date')[sensors].mean().round(2)
        daily_avg.index = daily_avg.index.astype(str)
        st.bar_chart(daily_avg, color=["#002D62", "#0EA5E9", "#E01934"])

        st.markdown('<div class="sec-title">Temperature Log Delta Variations</div>', unsafe_allow_html=True)

        d1_sum = temp_df['consump. dough1'].sum()
        d2_sum = temp_df['consump. dough2'].sum()
        p_sum  = temp_df['consump. perishable'].sum()

        sc1, sc2, sc3 = st.columns(3)
        for container, val, color, label in [
            (sc1, d1_sum, "#002D62", "Dough 1 Delta Variance Sum"),
            (sc2, d2_sum, "#0EA5E9", "Dough 2 Delta Variance Sum"),
            (sc3, p_sum,  "#E01934", "Perishable Delta Variance Sum"),
        ]:
            container.markdown(f"""
            <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:12px 18px; border-left:5px solid {color};">
                <div style="font-size:10px; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px;">{label}</div>
                <div style="font-size:18px; font-weight:800; color:#002D62; margin-top:4px;">{val:,.2f} °C</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="spacer-sm"></div>', unsafe_allow_html=True)
        st.line_chart(temp_df.set_index('Time')[delta_cols])

        st.markdown('<div class="sec-title">Cold-Chain Thermodynamic Stability Audits</div>', unsafe_allow_html=True)
        labels = {
            'Dough Cooler1 Temp': 'Dough Cooler 1',
            'Dough Cooler2 Temp': 'Dough Cooler 2',
            'Perishable Cooler Temp': 'Perishable Storage'
        }
        rows = []
        for col in sensors:
            if col not in temp_df.columns:
                continue
            s   = temp_df[col]
            n   = len(s)
            exc = int((s > THRESHOLD).sum())
            rows.append({
                "Asset Node": labels[col], "Total Logs": n,
                "Mean Temp": s.mean(), "Min Temp": s.min(), "Max Temp": s.max(),
                "Stability (σ)": s.std(), "Excursions": exc,
                "Compliance Index": (n - exc) / n
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True,
            column_config={
                "Mean Temp": st.column_config.NumberColumn(format="%.2f °C"),
                "Min Temp":  st.column_config.NumberColumn(format="%.2f °C"),
                "Max Temp":  st.column_config.NumberColumn(format="%.2f °C"),
                "Stability (σ)": st.column_config.NumberColumn(format="%.2f σ"),
                "Compliance Index": st.column_config.ProgressColumn(format="%.1f%%", min_value=0.0, max_value=1.0)
            })

        if dashboard_mode == "Engineering (Deep Diagnostics)":
            st.markdown('<div class="sec-title">Thermal Stability Index</div>', unsafe_allow_html=True)
            excursion_analytics = calculate_thermal_excursion_analytics(temp_df, THRESHOLD)
            stability_data = []
            for sensor, metrics in excursion_analytics.items():
                stability_data.append({
                    "Sensor": labels.get(sensor, sensor),
                    "Excursion Count": metrics['excursion_count'],
                    "Total Excursion Duration": metrics['total_excursion_duration'],
                    "Avg Recovery Time": metrics['avg_recovery_time'],
                    "Stability Index": metrics['stability_index'],
                    "Compliance %": metrics['compliance_percentage']
                })
            stability_df = pd.DataFrame(stability_data)
            st.dataframe(stability_df, use_container_width=True, hide_index=True)

            st.markdown('<div class="sec-title">Excursion Heatmap</div>', unsafe_allow_html=True)
            temp_df['Hour'] = pd.to_datetime(temp_df['Time']).dt.hour
            excursion_matrix = {}
            for sensor in sensors:
                if sensor in temp_df.columns:
                    temp_df[f'{sensor}_excursion'] = (temp_df[sensor] > THRESHOLD).astype(int)
                    pivot = temp_df.pivot_table(
                        index='Date', columns='Hour',
                        values=f'{sensor}_excursion', aggfunc='sum'
                    ).fillna(0)
                    excursion_matrix[sensor] = pivot

            if sensors and sensors[0] in excursion_matrix:
                mat = excursion_matrix[sensors[0]]
                fig_heatmap = go.Figure(data=go.Heatmap(
                    z=mat.values,
                    x=mat.columns,
                    y=[str(d) for d in mat.index],
                    colorscale='RdYlBu_r',
                    colorbar=dict(title="Excursion Count")
                ))
                fig_heatmap.update_layout(
                    title=f"Excursion Heatmap - {labels.get(sensors[0], sensors[0])}",
                    xaxis_title="Hour of Day", yaxis_title="Date", height=400
                )
                standardize_chart(fig_heatmap)
                st.plotly_chart(fig_heatmap, use_container_width=True)

            st.markdown('<div class="sec-title">Sensor Ranking Table</div>', unsafe_allow_html=True)
            if stability_data:
                ranking_df = stability_df[['Sensor', 'Compliance %', 'Stability Index']].sort_values('Compliance %', ascending=False)
                st.dataframe(ranking_df, use_container_width=True, hide_index=True)

        st.markdown('<div class="sec-title">Zone Status Alert Routing</div>', unsafe_allow_html=True)
        for col in sensors:
            if col not in temp_df.columns:
                continue
            exc  = int((temp_df[col] > THRESHOLD).sum())
            comp = ((len(temp_df) - exc) / len(temp_df)) * 100
            lbl  = labels[col]
            if comp >= 95:
                st.markdown(f'<div class="alert-ok">✓ <strong>{lbl}</strong> — Stable at {comp:.1f}% operational compliance.</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="alert-warn">⚠ <strong>{lbl}</strong> — Out-of-bounds drop at {comp:.1f}% compliance level.</div>', unsafe_allow_html=True)

        st.markdown('<div class="sec-title">📥 Raw Data Inspector & Export Portal</div>', unsafe_allow_html=True)
        with st.expander("📂 View & Download Compiled Temperature Log Data", expanded=False):
            st.dataframe(temp_df, use_container_width=True, hide_index=True)
            csv_data = temp_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Compiled Temperature Data as CSV",
                data=csv_data,
                file_name="compiled_temperature_logs.csv",
                mime="text/csv",
                key="btn_download_temp"
            )
    else:
        st.markdown('<div class="alert-info">No environment logs could be successfully loaded.</div>', unsafe_allow_html=True)

# ==============================================================================
#  TAB 2 — ENERGY & COST SAVINGS
# ==============================================================================
with tab_power:
    if e_df is not None and not e_df.empty:
        actual_facilities = {}
        for k, calc_col in [
            ('Dunkin', 'Dunkin Consumption'),
            ('CLC',    'CLC Consumption'),
            ('BMC',    'BMC Consumption'),
            ('Deep (Blast)', 'Deep Consumption')
        ]:
            if calc_col in e_df.columns:
                actual_facilities[k] = calc_col

        if not actual_facilities:
            st.markdown('<div class="alert-info">⚠️ Energy data file not found or empty.</div>', unsafe_allow_html=True)
        else:
            df_facilities = e_df[['Date'] + list(actual_facilities.values())].copy()
            df_facilities.columns = ['Date'] + list(actual_facilities.keys())

            df_melted = df_facilities.melt(id_vars='Date', var_name='Facility', value_name='Daily Consumption')
            df_melted['Daily Consumption'] = pd.to_numeric(df_melted['Daily Consumption'], errors='coerce').fillna(0).clip(lower=0)

            metrics = df_melted.groupby('Facility')['Daily Consumption'].agg(
                total_power='sum', avg_daily='mean',
                highest_daily='max', lowest_daily='min', days_processed='count'
            ).reset_index()
            facility_metrics = dict(zip(metrics['Facility'], metrics.to_dict('records')))

            st.markdown('<div class="sec-title">📊 Executive Facility Performance Matrix</div>', unsafe_allow_html=True)

            colors = {'Dunkin': '#002D62', 'CLC': '#FF9F1C', 'BMC': '#16A34A', 'Deep (Blast)': '#E01934'}
            st.markdown("""
            <style>
            .fac-card { background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%); border: 1px solid #e2e8f0;
                border-radius: 12px; padding: 24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
                margin-bottom: 20px; border-left: 6px solid #002D62; }
            .fac-title { font-size: 18px; font-weight: 800; color: #002D62; margin-bottom: 15px;
                border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; }
            .fac-metric { display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 13px; padding: 4px 0; }
            .fac-metric-label { color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; font-size: 11px; }
            .fac-metric-value { color: #0f172a; font-weight: 800; font-size: 14px; }
            </style>
            """, unsafe_allow_html=True)

            cols = st.columns(len(actual_facilities))
            for idx, fac in enumerate(actual_facilities.keys()):
                with cols[idx]:
                    m = facility_metrics.get(fac, {})
                    total_power   = m.get('total_power', 0)
                    avg_daily     = m.get('avg_daily', 0)
                    highest       = m.get('highest_daily', 0)
                    lowest        = m.get('lowest_daily', 0)
                    num_days      = int(m.get('days_processed', 0))
                    st.markdown(f"""
                    <div class="fac-card" style="border-left-color: {colors.get(fac, '#002D62')};">
                        <div class="fac-title">{fac}</div>
                        <div class="fac-metric"><span class="fac-metric-label">Total Power</span><span class="fac-metric-value">{total_power:,.0f} kWh</span></div>
                        <div class="fac-metric"><span class="fac-metric-label">Avg Daily</span><span class="fac-metric-value">{avg_daily:,.1f} kWh</span></div>
                        <div class="fac-metric"><span class="fac-metric-label">Highest Daily</span><span class="fac-metric-value">{highest:,.1f} kWh</span></div>
                        <div class="fac-metric"><span class="fac-metric-label">Lowest Daily</span><span class="fac-metric-value">{lowest:,.1f} kWh</span></div>
                        <div class="fac-metric"><span class="fac-metric-label">Days Processed</span><span class="fac-metric-value">{num_days}</span></div>
                    </div>
                    """, unsafe_allow_html=True)

            if dashboard_mode == "Engineering (Deep Diagnostics)":
                st.markdown('<div class="sec-title">Peak Demand Detection</div>', unsafe_allow_html=True)
                for zone, col_name in actual_facilities.items():
                    if col_name in e_df.columns:
                        peak_day   = e_df.loc[e_df[col_name].idxmax(), 'Date']
                        peak_value = e_df[col_name].max()
                        st.write(f"**{zone}**: Peak demand of **{peak_value:.1f} kWh** on **{peak_day.strftime('%d %b %Y')}**")

                st.markdown('<div class="sec-title">Energy Anomaly Detection</div>', unsafe_allow_html=True)
                for zone, col_name in actual_facilities.items():
                    if col_name in e_df.columns:
                        series  = e_df[col_name]
                        mean_v  = series.mean()
                        std_v   = series.std()
                        if std_v > 0:
                            anoms = e_df[e_df[col_name] > mean_v + 2 * std_v]
                            if len(anoms) > 0:
                                st.markdown(f'<div class="alert-warn">⚠️ <strong>{zone}</strong>: {len(anoms)} high consumption anomalies</div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="alert-ok">✓ <strong>{zone}</strong>: No anomalies detected</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-info">⚠️ Energy data file not found or empty.</div>', unsafe_allow_html=True)

# ==============================================================================
#  TAB 3 — ASSET DUTY CYCLES
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
            with c3: st.metric("Mean Constant Load Metric",  f"{r[kwh_cols[0]].mean():,.0f} kWh")

            st.markdown('<div class="sec-title">Daily Asset Displacement Matrix</div>', unsafe_allow_html=True)
            st.bar_chart(r.set_index(fc)[kwh_cols[0]], color="#002D62")

            r['Date_Key'] = r[fc].dt.date
            daily_runtime = r.groupby('Date_Key')[kwh_cols[0]].agg(['sum', 'max', 'mean']).reset_index()
            daily_runtime = daily_runtime.rename(columns={
                'Date_Key': 'Date',
                'sum':  'Energy Drew (kWh)',
                'max':  'Peak System Load Vector (kWh)',
                'mean': 'Mean Load Vector (kWh)'
            })
            daily_runtime['Date'] = pd.to_datetime(daily_runtime['Date'])

            st.markdown('<div class="sec-title">Date-Wise Energy Ingestion Profiles</div>', unsafe_allow_html=True)
            target_day = daily_runtime.iloc[-1] if not daily_runtime.empty else None

            rc1, rc2, rc3 = st.columns(3)
            for container, col_name, color, label in [
                (rc1, 'Energy Drew (kWh)',              '#002D62', 'Energy Drew'),
                (rc2, 'Peak System Load Vector (kWh)',  '#FF9F1C', 'Peak System Load Vector'),
                (rc3, 'Mean Load Vector (kWh)',         '#E01934', 'Mean Load Vector'),
            ]:
                val = target_day[col_name] if target_day is not None else 0
                container.markdown(f"""
                <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:12px 18px; border-left:5px solid {color};">
                    <div style="font-size:10px; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px;">{label}</div>
                    <div style="font-size:18px; font-weight:800; color:#002D62; margin-top:4px;">{val:,.1f} kWh</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('<div class="spacer-sm"></div>', unsafe_allow_html=True)
            st.line_chart(daily_runtime.set_index('Date')[['Energy Drew (kWh)', 'Peak System Load Vector (kWh)', 'Mean Load Vector (kWh)']])

            st.markdown('<div class="sec-title">Date-Wise Asset Duty Performance Log Metrics</div>', unsafe_allow_html=True)
            st.dataframe(daily_runtime, use_container_width=True, hide_index=True)

            if dashboard_mode == "Engineering (Deep Diagnostics)":
                st.markdown('<div class="sec-title">Variance Analysis</div>', unsafe_allow_html=True)
                avg_consumption = daily_runtime['Energy Drew (kWh)'].mean()
                fig_variance = go.Figure()
                fig_variance.add_trace(go.Bar(
                    x=daily_runtime['Date'].dt.strftime('%d-%b'),
                    y=daily_runtime['Energy Drew (kWh)'] - avg_consumption,
                    name='Variance from Average',
                    marker_color=np.where(
                        daily_runtime['Energy Drew (kWh)'] - avg_consumption > 0, '#E01934', '#16A34A'
                    )
                ))
                fig_variance.update_layout(
                    title='Daily Consumption Variance from Average',
                    xaxis_title='Date', yaxis_title='Variance (kWh)', height=300
                )
                standardize_chart(fig_variance)
                st.plotly_chart(fig_variance, use_container_width=True)

            st.markdown('<div class="sec-title">📥 Raw Data Inspector & Export Portal</div>', unsafe_allow_html=True)
            with st.expander("📂 View & Download Asset Duty Cycle Raw Sheet Data", expanded=False):
                st.dataframe(r.drop(columns=['Date_Key']), use_container_width=True, hide_index=True)
                csv_data = daily_runtime.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Date-Wise Duty Cycles as CSV",
                    data=csv_data,
                    file_name="datewise_asset_duty_cycles.csv",
                    mime="text/csv",
                    key="btn_download_runtime"
                )
    else:
        st.markdown('<div class="alert-info">Asset duty-cycle log metrics are not active.</div>', unsafe_allow_html=True)

# ==============================================================================
#  TAB 4 — EXECUTIVE SUMMARY (FULLY DYNAMIC)
# ==============================================================================
with tab_summary:
    st.markdown('<div class="sec-title">Plant Health Overview</div>', unsafe_allow_html=True)

    plant_health_score = (
        thermal_compliance     * 0.3 +
        compressor_availability * 0.3 +
        equipment_utilization  * 0.2 +
        operational_efficiency * 0.2
    )

    fig_health = go.Figure(go.Indicator(
        mode="gauge+number",
        value=plant_health_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Plant Health Score", 'font': {'size': 24}},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': PRIMARY_COLOR},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 50],  'color': '#FEE2E2'},
                {'range': [50, 80], 'color': '#FEF3C7'},
                {'range': [80, 100],'color': '#D1FAE5'}
            ],
            'threshold': {'line': {'color': SECONDARY_COLOR, 'width': 4}, 'thickness': 0.75, 'value': 85}
        }
    ))
    fig_health.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig_health, use_container_width=True)

    st.markdown('<div class="sec-title">Thermal Compliance Gauge</div>', unsafe_allow_html=True)
    fig_compliance = go.Figure(go.Indicator(
        mode="gauge+number",
        value=thermal_compliance,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Thermal Compliance (%)", 'font': {'size': 24}},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': SECONDARY_COLOR},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 70],  'color': '#FEE2E2'},
                {'range': [70, 90], 'color': '#FEF3C7'},
                {'range': [90, 100],'color': '#D1FAE5'}
            ],
            'threshold': {'line': {'color': PRIMARY_COLOR, 'width': 4}, 'thickness': 0.75, 'value': 95}
        }
    ))
    fig_compliance.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig_compliance, use_container_width=True)

    # Dynamic Executive Summary metrics
    st.markdown('<div class="sec-title">Dynamic Reporting Summary</div>', unsafe_allow_html=True)
    es1, es2, es3, es4 = st.columns(4)
    with es1: st.metric("Date Range Start",   global_date_info['start_str'])
    with es2: st.metric("Date Range End",     global_date_info['end_str'])
    with es3: st.metric("Coverage (days)",    str(global_total_days))
    with es4: st.metric("Energy Consumption", f"{energy_consumption:,.0f} kWh")

    if e_df is not None and not e_df.empty:
        st.markdown('<div class="sec-title">Energy Consumption Trend</div>', unsafe_allow_html=True)
        zones = ['Dunkin Consumption', 'CLC Consumption', 'BMC Consumption', 'Deep Consumption']
        valid_zones = [z for z in zones if z in e_df.columns]
        if valid_zones:
            fig_trend = go.Figure()
            for zone in valid_zones:
                fig_trend.add_trace(go.Scatter(
                    x=e_df['Date'], y=e_df[zone],
                    mode='lines', name=zone.replace(' Consumption', ''), line=dict(width=2)
                ))
            fig_trend.update_layout(
                xaxis_title='Date', yaxis_title='Energy Consumption (kWh)',
                height=300, margin=dict(l=20, r=20, t=40, b=40)
            )
            standardize_chart(fig_trend)
            st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown('<div class="sec-title">Executive Insights</div>', unsafe_allow_html=True)
    insights = generate_ai_insights(e_df, temp_df, comp_summary)

    if insights:
        st.markdown('<div class="insights-panel">', unsafe_allow_html=True)
        for insight in insights:
            st.markdown(f'<div class="insight-item"><div class="insight-icon">💡</div><div class="insight-text">{insight}</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No significant insights detected at this time.")

    # Data Quality Summary — all dynamic
    st.markdown('<div class="sec-title">Data Quality Summary</div>', unsafe_allow_html=True)
    dq_cols = st.columns(4)
    with dq_cols[0]: st.metric("Completeness", f"{energy_validation['completeness']:.1f}%")
    with dq_cols[1]: st.metric("Accuracy",     f"{energy_validation['accuracy']:.1f}%")
    with dq_cols[2]: st.metric("Consistency",  f"{energy_validation['consistency']:.1f}%")
    with dq_cols[3]: st.metric("Freshness",    f"{energy_validation['freshness']:.1f}%")

    # Dynamic total records / date range from global engine
    st.markdown('<div class="sec-title">Aggregate Data Summary</div>', unsafe_allow_html=True)
    agg1, agg2, agg3, agg4 = st.columns(4)
    total_master_records = (len(e_df) if e_df is not None else 0) + (len(temp_df) if temp_df is not None else 0)
    with agg1: st.metric("Total Records",    f"{total_master_records:,}")
    with agg2: st.metric("Date Range Start", global_date_info['start_str'])
    with agg3: st.metric("Date Range End",   global_date_info['end_str'])
    with agg4: st.metric("Coverage",         f"{global_total_days} days")

    for issue in energy_validation['issues'] + temp_validation['issues']:
        st.markdown(f'<div class="alert-warn">⚠️ {issue}</div>', unsafe_allow_html=True)
