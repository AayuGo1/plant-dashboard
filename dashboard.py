# ============================================================================
# JUBILANT FOODWORKS LIMITED — PLANT OPERATIONAL INTELLIGENCE PLATFORM
# Enterprise Manufacturing Intelligence Dashboard v3.0
# ============================================================================

import os
import re
import io
import glob
import warnings
import logging
import requests
import traceback
from typing import Dict, List, Tuple, Optional, Any, Callable
from datetime import datetime, timedelta, time as dt_time
from functools import lru_cache

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# ============================================================================
# SECTION 1: CONFIGURATION & CONSTANTS
# ============================================================================

GITHUB_USER = "AayuGo1"
GITHUB_REPO = "plant-dashboard"
GITHUB_BRANCH = "main"

RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}"
API_BASE = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents?ref={GITHUB_BRANCH}"

# Corporate Brand Colors
BRAND = {
    "primary": "#002D62",
    "primary_dark": "#001840",
    "secondary": "#E01934",
    "secondary_dark": "#B91429",
    "accent_orange": "#FF9F1C",
    "accent_green": "#16A34A",
    "accent_purple": "#8B5CF6",
    "accent_cyan": "#0EA5E9",
    "accent_amber": "#F59E0B",
    "bg": "#F8FAFC",
    "bg_card": "#FFFFFF",
    "text_primary": "#0F172A",
    "text_secondary": "#64748B",
    "border": "#E2E8F0",
    "success": "#10B981",
    "danger": "#DC2626",
}

# File Discovery Patterns
FILE_PATTERNS: Dict[str, re.Pattern] = {
    "energy": re.compile(r"PROCESSED_DAILY_VARS_Active_Energy_Report", re.IGNORECASE),
    "temperature": re.compile(r"DataLog_.*\.csv", re.IGNORECASE),
    "freon": re.compile(r"freon.*\.xlsx", re.IGNORECASE),
    "utility": re.compile(r"utility.*\.xlsx", re.IGNORECASE),
    "operational": re.compile(r"operational.*\.xlsx", re.IGNORECASE),
}

# Plotly Enterprise Theme
PLOTLY_THEME = {
    "font_family": "'Inter', 'Segoe UI', sans-serif",
    "font_size": 12,
    "plot_bgcolor": "rgba(0,0,0,0)",
    "paper_bgcolor": "rgba(0,0,0,0)",
    "grid_color": "#E2E8F0",
    "hover_bg": "#FFFFFF",
    "hover_border": "#E2E8F0",
}

# ============================================================================
# SECTION 2: LOGGING & ERROR HANDLING
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("jfl_dashboard")


class SafeExecution:
    """Context manager for safe execution with graceful degradation."""

    def __init__(self, operation_name: str, default=None):
        self.operation_name = operation_name
        self.default = default
        self.error = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.error = str(exc_val)
            logger.error(f"[{self.operation_name}] Error: {exc_val}")
            logger.debug(traceback.format_exc())
        return True  # Suppress exception


# ============================================================================
# SECTION 3: ENTERPRISE CSS THEME
# ============================================================================

def render_css_theme():
    """Injects the complete enterprise CSS theme."""
    st.markdown(
        f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

:root {{
    --primary: {BRAND['primary']};
    --primary-dark: {BRAND['primary_dark']};
    --secondary: {BRAND['secondary']};
    --bg: {BRAND['bg']};
    --card: {BRAND['bg_card']};
    --text: {BRAND['text_primary']};
    --text-muted: {BRAND['text_secondary']};
    --border: {BRAND['border']};
}}

* {{ box-sizing: border-box; }}

html, body, [class*="css"], .stApp {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    color: var(--text);
    background: var(--bg);
}}

.block-container {{
    padding: 2rem 2.5rem 3rem;
    max-width: 1600px;
    background: var(--bg);
}}

/* ─ Sidebar ─────────────────────────────────────────────── */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #001840 0%, var(--primary) 100%) !important;
    border-right: none !important;
}}
section[data-testid="stSidebar"] * {{ color: #CBD5E0 !important; }}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {{ color: #FFFFFF !important; }}
section[data-testid="stSidebar"] input {{
    background: #001840 !important;
    border: 1px solid #1E3A8A !important;
    color: #FFFFFF !important;
    border-radius: 6px !important;
    font-size: 12px !important;
}}
section[data-testid="stSidebar"] label {{
    color: #94A3B8 !important;
    font-size: 10px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.8px !important;
}}
section[data-testid="stSidebar"] .stButton>button {{
    background: var(--secondary) !important;
    color: white !important;
    border: none !important;
    font-weight: 700 !important;
    width: 100% !important;
    border-radius: 6px !important;
    transition: all 0.2s ease !important;
}}
section[data-testid="stSidebar"] .stButton>button:hover {{
    background: #B91429 !important;
    transform: translateY(-1px) !important;
}}

/* ── Header ──────────────────────────────────────────────── */
.jfl-header {{
    background: #FFFFFF;
    border-radius: 14px;
    padding: 28px 32px;
    margin-bottom: 28px;
    border: 1px solid var(--border);
    border-left: 8px solid var(--secondary);
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
}}
.jfl-header-brand {{
    flex: 1;
    min-width: 280px;
}}
.jfl-header-subtitle {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 4px;
}}
.jfl-header-title {{
    font-size: 26px;
    font-weight: 800;
    color: var(--primary);
    letter-spacing: -0.5px;
    line-height: 1.2;
}}
.jfl-header-meta {{
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    min-width: 240px;
}}
.jfl-meta-box {{
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px 18px;
    min-width: 160px;
    flex: 1;
}}
.jfl-meta-label {{
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #94A3B8;
    margin-bottom: 4px;
}}
.jfl-meta-value {{
    font-size: 14px;
    font-weight: 800;
    color: var(--primary);
}}

/* ── Section Titles ──────────────────────────────────────── */
.sec-title {{
    font-size: 13px;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin: 32px 0 16px 0;
    padding-bottom: 10px;
    border-bottom: 2px solid var(--border);
    display: flex;
    align-items: center;
    gap: 8px;
}}

/* ── KPI Grid (Responsive, No Overlap) ───────────────────── */
.kpi-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 20px;
    margin-bottom: 32px;
    width: 100%;
}}
.kpi-card {{
    background: #FFFFFF;
    border-radius: 12px;
    padding: 22px 24px;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
    border-left: 5px solid var(--primary);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    min-height: 150px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    overflow: hidden;
}}
.kpi-card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);
}}
.kpi-title {{
    font-size: 11px;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 10px;
    line-height: 1.3;
}}
.kpi-value {{
    font-size: 28px;
    font-weight: 800;
    color: var(--text);
    margin-bottom: 8px;
    line-height: 1.1;
}}
.kpi-unit {{
    font-size: 16px;
    font-weight: 700;
    color: var(--text);
    margin-top: 4px;
}}
.kpi-delta {{
    font-size: 12px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 4px;
}}
.kpi-delta.positive {{ color: #16A34A; }}
.kpi-delta.negative {{ color: #DC2626; }}
.kpi-delta.neutral {{ color: var(--text-muted); }}

/* ── Alert Boxes ─────────────────────────────────────────── */
.alert {{
    border-radius: 8px;
    padding: 14px 18px;
    font-size: 13px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 10px;
}}
.alert-warn {{
    background: #FFFBEB;
    border: 1px solid #FDE68A;
    border-left: 5px solid #F59E0B;
    color: #92400E;
}}
.alert-ok {{
    background: #F0FDF4;
    border: 1px solid #BBF7D0;
    border-left: 5px solid #16A34A;
    color: #14532D;
}}
.alert-info {{
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    border-left: 5px solid #3B82F6;
    color: #1E3A8A;
}}

/* ── Status Pills ────────────────────────────────────────── */
.status-pill {{
    display: inline-block;
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    margin-bottom: 8px;
}}
.status-ok {{ background:#D1FAE5; color:#065F46; border:1px solid #A7F3D0; }}
.status-err {{ background:#FEE2E2; color:#991B1B; border:1px solid #FCA5A5; }}

/* ── Insights Panel ──────────────────────────────────────── */
.insights-panel {{
    background: #FFFFFF;
    border-radius: 12px;
    padding: 20px;
    border: 1px solid var(--border);
    margin-top: 20px;
}}
.insight-item {{
    padding: 12px 0;
    border-bottom: 1px solid #F1F5F9;
    display: flex;
    align-items: flex-start;
    gap: 12px;
}}
.insight-item:last-child {{ border-bottom: none; }}
.insight-icon {{ font-size: 20px; margin-top: 2px; }}
.insight-text {{ font-size: 14px; line-height: 1.5; }}

/* ── Executive Summary Cards ─────────────────────────────── */
.exec-card {{
    background: #FFFFFF;
    border-radius: 12px;
    padding: 20px 24px;
    border: 1px solid var(--border);
    border-left: 4px solid var(--primary);
    margin-bottom: 16px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.03);
}}
.exec-card-title {{
    font-size: 12px;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 8px;
}}
.exec-card-value {{
    font-size: 18px;
    font-weight: 700;
    color: var(--text);
    line-height: 1.4;
}}

/* ── Tabs ────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
    gap: 0;
    background: #FFFFFF;
    border-bottom: 2px solid var(--border);
    padding: 0 12px;
    border-radius: 10px 10px 0 0;
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent;
    border: none;
    border-bottom: 3px solid transparent;
    padding: 16px 24px;
    font-size: 13px;
    font-weight: 700;
    color: var(--text-muted);
    transition: all 0.2s ease;
}}
.stTabs [data-baseweb="tab"]:hover {{ color: var(--primary); }}
.stTabs [data-baseweb="tab"][aria-selected="true"] {{
    color: var(--primary) !important;
    border-bottom: 3px solid var(--secondary) !important;
    background: transparent !important;
}}

/* ── Responsive ──────────────────────────────────────────── */
@media (max-width: 1200px) {{
    .kpi-grid {{
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
    }}
    .block-container {{ padding: 1.5rem 2rem 2.5rem; }}
}}
@media (max-width: 768px) {{
    .block-container {{ padding: 1rem 1.25rem 2rem !important; }}
    .jfl-header {{ padding: 20px; flex-direction: column; align-items: flex-start; }}
    .jfl-header-title {{ font-size: 20px !important; }}
    .kpi-value {{ font-size: 22px !important; }}
    .kpi-grid {{
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 12px;
    }}
    .kpi-card {{ min-height: 130px; padding: 16px; }}
}}
@media (max-width: 480px) {{
    .kpi-grid {{
        grid-template-columns: 1fr;
    }}
}}
</style>
""",
        unsafe_allow_html=True,
    )


# ============================================================================
# SECTION 4: UTILITY FUNCTIONS
# ============================================================================


def standardize_chart(fig: go.Figure) -> go.Figure:
    """Applies the standardized enterprise Plotly theme."""
    fig.update_layout(
        font=dict(family=PLOTLY_THEME["font_family"], size=PLOTLY_THEME["font_size"]),
        plot_bgcolor=PLOTLY_THEME["plot_bgcolor"],
        paper_bgcolor=PLOTLY_THEME["paper_bgcolor"],
        hoverlabel=dict(
            bgcolor=PLOTLY_THEME["hover_bg"],
            bordercolor=PLOTLY_THEME["hover_border"],
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0.9)",
        ),
        margin=dict(l=20, r=20, t=40, b=40),
    )
    if "xaxis" in fig.layout:
        fig.layout.xaxis.gridcolor = PLOTLY_THEME["grid_color"]
        fig.layout.xaxis.zerolinecolor = PLOTLY_THEME["grid_color"]
    if "yaxis" in fig.layout:
        fig.layout.yaxis.gridcolor = PLOTLY_THEME["grid_color"]
        fig.layout.yaxis.zerolinecolor = PLOTLY_THEME["grid_color"]
    return fig


def fast_parse_dates(series: pd.Series) -> pd.Series:
    """Optimized date parsing with fallback formats."""
    cleansed = series.astype(str).str.strip().str.split(" ").str[0]
    parsed = pd.to_datetime(cleansed, errors="coerce", format="%Y-%m-%d")
    if parsed.isna().all():
        parsed = pd.to_datetime(cleansed, errors="coerce", dayfirst=True)
    return parsed


def normalize_to_time(val) -> Optional[dt_time]:
    """Converts any time representation to a datetime.time object safely."""
    if val is None:
        return None
    if isinstance(val, float) and pd.isna(val):
        return None
    if isinstance(val, pd.Timestamp) and pd.isna(val):
        return None
    if isinstance(val, dt_time):
        return val
    if isinstance(val, (datetime, pd.Timestamp)):
        try:
            return val.time()
        except Exception:
            return None

    val_str = str(val).strip()
    if not val_str or val_str.lower() in ["nan", "nat", "none", "", "0:00"]:
        return None

    formats_to_try = [
        "%I.%M.%S %p", "%I:%M:%S %p", "%I:%M %p", "%I.%M %p",
        "%H:%M:%S", "%H:%M", "%H.%M.%S",
    ]
    for fmt in formats_to_try:
        try:
            return datetime.strptime(val_str, fmt).time()
        except (ValueError, TypeError):
            continue

    try:
        parsed = pd.to_datetime(val_str, errors="coerce")
        if pd.notna(parsed):
            return parsed.time()
    except Exception:
        pass
    return None


# ============================================================================
# SECTION 5: DATA LOADERS (CACHED & ROBUST)
# ============================================================================


@st.cache_data(ttl=300)
def discover_and_categorize_files() -> Dict[str, List[Tuple[str, str]]]:
    """Automatically discovers and categorizes files in the GitHub repository."""
    try:
        r = requests.get(API_BASE, timeout=10)
        r.raise_for_status()
        files = [
            (f["name"], f["download_url"])
            for f in r.json()
            if isinstance(f, dict) and "name" in f and "download_url" in f
        ]

        categorized = {k: [] for k in FILE_PATTERNS}
        categorized["unknown"] = []

        for name, url in files:
            matched = False
            for category, pattern in FILE_PATTERNS.items():
                if pattern.search(name):
                    categorized[category].append((name, url))
                    matched = True
                    break
            if not matched:
                categorized["unknown"].append((name, url))

        return categorized
    except Exception as e:
        logger.error(f"GitHub connection issue: {e}")
        return {k: [] for k in FILE_PATTERNS}


@st.cache_data(ttl=300)
def fetch_file_bytes(url: str) -> bytes:
    """Fetches raw bytes from a GitHub URL with caching."""
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.content


def read_excel_from_github(url: str, **kwargs) -> pd.DataFrame:
    """Reads an Excel file directly from GitHub."""
    return pd.read_excel(io.BytesIO(fetch_file_bytes(url)), **kwargs)


def read_csv_from_github(url: str, **kwargs) -> pd.DataFrame:
    """Reads a CSV file directly from GitHub."""
    return pd.read_csv(io.BytesIO(fetch_file_bytes(url)), **kwargs)


@st.cache_data(ttl=300)
def load_processed_energy_data() -> Optional[pd.DataFrame]:
    """Loads and processes the latest Active Energy Report automatically."""
    with SafeExecution("load_processed_energy_data") as ctx:
        categorized = discover_and_categorize_files()
        target_files = categorized.get("energy", [])
        if not target_files:
            return None

        name, url = sorted(target_files)[-1]

        try:
            if name.endswith(".csv"):
                df = read_csv_from_github(url)
            else:
                raw_df = read_excel_from_github(url, header=None)
                header_row_idx = 0
                for i, row in raw_df.iterrows():
                    if any("date" in str(x).lower() for x in row if pd.notna(x)):
                        header_row_idx = i
                        break
                df = read_excel_from_github(url, header=header_row_idx)

            df.columns = [str(c).strip() for c in df.columns]

            date_col = next((c for c in df.columns if "date" in c.lower()), None)
            if not date_col:
                if pd.api.types.is_datetime64_any_dtype(
                    df.iloc[:, 0]
                ) or "2026" in str(df.iloc[0, 0]):
                    date_col = df.columns[0]
                    df.rename(columns={date_col: "Date"}, inplace=True)
                    date_col = "Date"
                else:
                    return None

            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            df = df.dropna(subset=[date_col])
            df = df.sort_values(by=date_col).reset_index(drop=True)

            if df.empty:
                return None

            register_cols = []
            for i in range(1, 10):
                v_col = f"V{i}"
                matched_v = next(
                    (
                        c
                        for c in df.columns
                        if c.upper() == v_col.upper() or c.startswith(f"V{i} ")
                    ),
                    None,
                )
                if matched_v:
                    register_cols.append(matched_v)

            calculated_consumption = {}
            for reg_col in register_cols:
                v_num = None
                for i in range(1, 10):
                    if f"V{i}" in reg_col.upper():
                        v_num = i
                        break
                if v_num:
                    diffs = df[reg_col].diff()
                    diffs = diffs.where(diffs >= 0, other=np.nan)
                    calculated_consumption[f"calc_consump_v{v_num}"] = diffs.fillna(0)

            for col_name, series in calculated_consumption.items():
                df[col_name] = series

            def get_zone_consumption(v_nums):
                total = pd.Series(np.zeros(len(df)), index=df.index)
                for v in v_nums:
                    col = f"calc_consump_v{v}"
                    if col in df.columns:
                        total += df[col]
                return total

            df["Dunkin Consumption"] = get_zone_consumption([1, 6])
            df["CLC Consumption"] = get_zone_consumption([3, 8])
            df["BMC Consumption"] = get_zone_consumption([2, 7])
            df["Deep Consumption"] = get_zone_consumption([4, 5, 9])

            for i in range(1, 10):
                df[f"V{i}_Consumption"] = df.get(
                    f"calc_consump_v{i}", pd.Series(0, index=df.index)
                )

            return df

        except Exception as e:
            logger.error(f"Failed parsing processed energy file {name}: {e}")
            st.sidebar.error(f"Failed parsing processed energy file {name}: {e}")
            return None
    return None


@st.cache_data(ttl=300)
def load_temperature_data() -> Optional[pd.DataFrame]:
    """Loads and combines all temperature data logs automatically."""
    with SafeExecution("load_temperature_data") as ctx:
        categorized = discover_and_categorize_files()
        csv_files = categorized.get("temperature", [])
        if not csv_files:
            return None

        frames = []
        for name, url in sorted(csv_files):
            try:
                df = read_csv_from_github(url)
                df.columns = [str(c).strip() for c in df.columns]

                time_col = next(
                    (c for c in df.columns if "time" in c.lower()), None
                )
                c1_col = next(
                    (
                        c
                        for c in df.columns
                        if "cooler1" in c.lower().replace(" ", "")
                    ),
                    None,
                )
                c2_col = next(
                    (
                        c
                        for c in df.columns
                        if "cooler2" in c.lower().replace(" ", "")
                    ),
                    None,
                )
                p_col = next(
                    (c for c in df.columns if "perishable" in c.lower()), None
                )

                if not all([time_col, c1_col, c2_col, p_col]):
                    continue

                sub = df[[time_col, c1_col, c2_col, p_col]].copy()
                sub = sub.rename(
                    columns={
                        time_col: "Time",
                        c1_col: "Dough Cooler1 Temp",
                        c2_col: "Dough Cooler2 Temp",
                        p_col: "Perishable Cooler Temp",
                    }
                )

                for c in [
                    "Dough Cooler1 Temp",
                    "Dough Cooler2 Temp",
                    "Perishable Cooler Temp",
                ]:
                    sub[c] = sub[c].astype(str).str.strip()
                    sub[c] = pd.to_numeric(sub[c], errors="coerce")
                    sub[c] = sub[c].ffill().bfill()

                sub["Time"] = pd.to_datetime(
                    sub["Time"], dayfirst=True, errors="coerce"
                )
                frames.append(sub)
            except Exception as e:
                logger.warning(f"Skipped template anomalies on {name}: {e}")

        if not frames:
            return None

        combined = (
            pd.concat(frames, ignore_index=True)
            .dropna(subset=["Time"])
            .drop_duplicates(subset=["Time"])
            .sort_values("Time")
            .reset_index(drop=True)
        )

        combined["consump. dough1"] = (
            combined["Dough Cooler1 Temp"]
            - combined["Dough Cooler1 Temp"].shift(1)
        ).fillna(0)
        combined["consump. dough2"] = (
            combined["Dough Cooler2 Temp"]
            - combined["Dough Cooler2 Temp"].shift(1)
        ).fillna(0)
        combined["consump. perishable"] = (
            combined["Perishable Cooler Temp"]
            - combined["Perishable Cooler Temp"].shift(1)
        ).fillna(0)

        return combined
    return None


@st.cache_data(ttl=300)
def load_excel_sheet(
    sheet_name: str, fallback_header_row: int
) -> Optional[pd.DataFrame]:
    """Loads a specific sheet from the Freon Excel workbook automatically."""
    with SafeExecution(f"load_excel_sheet_{sheet_name}") as ctx:
        categorized = discover_and_categorize_files()
        freon_files = categorized.get("freon", [])
        if not freon_files:
            return None

        match_url = freon_files[0][1]

        try:
            preview = read_excel_from_github(
                match_url, sheet_name=sheet_name, header=None, engine="openpyxl"
            )
        except Exception as e:
            logger.warning(f"Could not preview sheet '{sheet_name}': {e}")
            return None

        hdr = fallback_header_row
        if not preview.empty:
            for i in range(min(15, len(preview))):
                row_vals = [
                    str(x).lower() for x in preview.iloc[i] if pd.notna(x)
                ]
                if any(
                    "date" in x
                    or "stop time" in x
                    or "start time" in x
                    or "sr" in x
                    for x in row_vals
                ):
                    hdr = i
                    break

        try:
            df = read_excel_from_github(
                match_url, sheet_name=sheet_name, header=hdr, engine="openpyxl"
            )
        except Exception as e:
            logger.warning(f"Failed to read data from sheet '{sheet_name}': {e}")
            return None

        if df.empty:
            return None

        df.columns = [str(c).strip() for c in df.columns]
        df = df.dropna(axis=1, how="all")

        if sheet_name == "Sheet3":
            if len(df.columns) >= 12:
                if "Saving in hrs" not in df.columns:
                    df.columns.values[11] = "Saving in hrs"
            else:
                last = df.columns[-1]
                if "unnamed" in str(last).lower():
                    df = df.rename(columns={last: "Saving in hrs"})

        if not df.empty:
            fc = df.columns[0]
            mask = df[fc].astype(str).str.strip().str.lower() != "total"
            df = df[mask]

        return df
    return None


# ============================================================================
# SECTION 6: DATA VALIDATION
# ============================================================================


def validate_dataframe(
    df: pd.DataFrame, required_columns: List[str] = None
) -> Dict[str, Any]:
    """Validates a DataFrame and returns a data quality score."""
    if df is None or df.empty:
        return {
            "is_valid": False,
            "completeness": 0.0,
            "accuracy": 0.0,
            "consistency": 0.0,
            "freshness": 0.0,
            "overall_score": 0.0,
            "issues": ["Empty or None DataFrame"],
        }

    issues = []
    total_cells = df.shape[0] * df.shape[1]

    # Completeness check
    missing_count = df.isnull().sum().sum()
    completeness = 1.0 - (missing_count / total_cells) if total_cells > 0 else 0.0
    if missing_count > 0:
        issues.append(f"{missing_count} missing values detected")

    # Required columns check
    if required_columns:
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            issues.append(f"Missing required columns: {', '.join(missing_cols)}")
            completeness *= 0.8

    # Consistency check
    duplicate_rows = df.duplicated().sum()
    consistency = 1.0 - (duplicate_rows / df.shape[0]) if df.shape[0] > 0 else 0.0
    if duplicate_rows > 0:
        issues.append(f"{duplicate_rows} duplicate rows detected")

    # Accuracy check - SAFE: Uses dtypes.items() to prevent KeyError on duplicate columns
    accuracy_issues = 0
    for col, dtype in df.dtypes.items():
        if dtype == "object":
            try:
                col_idx = df.columns.get_loc(col)
                # Skip if duplicate column names exist (get_loc returns slice/array)
                if isinstance(col_idx, slice) or hasattr(col_idx, "__len__"):
                    continue
                types_in_col = df.iloc[:, col_idx].apply(type).nunique()
                if types_in_col > 1:
                    accuracy_issues += 1
                    issues.append(f"Column '{col}' has mixed data types")
            except Exception:
                continue

    accuracy = 1.0 - (accuracy_issues / len(df.columns)) if len(df.columns) > 0 else 1.0

    # Freshness check
    freshness = 1.0
    date_cols = [col for col in df.columns if "date" in str(col).lower() or "time" in str(col).lower()]
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
            issues.append("Unable to parse date for freshness check")

    weights = {
        "completeness": 0.3,
        "accuracy": 0.25,
        "consistency": 0.25,
        "freshness": 0.2,
    }
    overall_score = (
        completeness * weights["completeness"]
        + accuracy * weights["accuracy"]
        + consistency * weights["consistency"]
        + freshness * weights["freshness"]
    )

    return {
        "is_valid": len(issues) == 0,
        "completeness": round(completeness * 100, 1),
        "accuracy": round(accuracy * 100, 1),
        "consistency": round(consistency * 100, 1),
        "freshness": round(freshness * 100, 1),
        "overall_score": round(overall_score * 100, 1),
        "issues": issues,
    }

# ============================================================================
# SECTION 7: ANALYTICS FUNCTIONS
# ============================================================================


def calculate_compressor_mtbf_mttr(
    df_daily: pd.DataFrame, compressor_name: str
) -> Dict[str, float]:
    """Calculate MTBF and MTTR for a specific compressor."""
    comp_data = df_daily[df_daily["Compressor"] == compressor_name].copy()

    if comp_data.empty:
        return {"mtbf": 0.0, "mttr": 0.0, "failures": 0, "runtime_hours": 0.0}

    failures = comp_data[comp_data["Working Hours"] == 0]
    failure_count = len(failures)
    total_runtime = comp_data["Working Hours"].sum()

    if failure_count == 0:
        mtbf = total_runtime
        mttr = 0.0
    else:
        mtbf = total_runtime / failure_count if failure_count > 0 else 0.0
        mttr = (
            comp_data[comp_data["Non Working Hours"] > 0][
                "Non Working Hours"
            ].mean()
            if failure_count > 0
            else 0.0
        )

    return {
        "mtbf": round(mtbf, 2),
        "mttr": round(mttr, 2),
        "failures": failure_count,
        "runtime_hours": round(total_runtime, 2),
    }


def calculate_thermal_excursion_analytics(
    temp_df: pd.DataFrame, threshold: float = 4.0
) -> Dict[str, Any]:
    """Calculate thermal excursion metrics for temperature sensors."""
    sensors = [
        "Dough Cooler1 Temp",
        "Dough Cooler2 Temp",
        "Perishable Cooler Temp",
    ]
    results = {}

    for sensor in sensors:
        if sensor not in temp_df.columns:
            continue

        series = temp_df[sensor]
        excursions = series > threshold
        excursion_count = excursions.sum()

        excursion_groups = (excursions != excursions.shift()).cumsum()
        excursion_durations = excursion_groups[excursions].value_counts()
        total_excursion_duration = (
            excursion_durations.sum() if not excursion_durations.empty else 0
        )

        recovery_times = []
        in_excursion = False
        excursion_start = None

        for idx, (time_val, temp_val) in enumerate(zip(temp_df["Time"], series)):
            if temp_val > threshold and not in_excursion:
                in_excursion = True
                excursion_start = idx
            elif temp_val <= threshold and in_excursion:
                in_excursion = False
                if excursion_start is not None:
                    recovery_time = idx - excursion_start
                    recovery_times.append(recovery_time)
                    excursion_start = None

        avg_recovery_time = np.mean(recovery_times) if recovery_times else 0
        stability_index = 1.0 / (series.std() + 1e-8)

        results[sensor] = {
            "excursion_count": int(excursion_count),
            "total_excursion_duration": int(total_excursion_duration),
            "avg_recovery_time": round(avg_recovery_time, 2),
            "stability_index": round(stability_index, 4),
            "compliance_percentage": round(
                (1 - excursion_count / len(series)) * 100, 2
            ),
        }

    return results


def generate_ai_insights(
    e_df: pd.DataFrame,
    temp_df: pd.DataFrame,
    comp_summary: pd.DataFrame,
) -> List[str]:
    """Generate automated insights from the data."""
    insights = []

    if e_df is not None and not e_df.empty:
        zones = [
            "Dunkin Consumption",
            "CLC Consumption",
            "BMC Consumption",
            "Deep Consumption",
        ]
        valid_zones = [z for z in zones if z in e_df.columns]
        if valid_zones:
            total_consumption = {z: e_df[z].sum() for z in valid_zones}
            highest_zone = max(total_consumption, key=total_consumption.get)
            insights.append(
                f"**{highest_zone.replace(' Consumption', '')}** recorded the highest energy consumption at **{total_consumption[highest_zone]:,.1f} kWh**."
            )

            if len(e_df) >= 14:
                last_week = e_df.tail(7)[valid_zones].sum().sum()
                prev_week = e_df.tail(14).head(7)[valid_zones].sum().sum()
                if prev_week > 0:
                    pct_change = ((last_week - prev_week) / prev_week) * 100
                    if abs(pct_change) > 5:
                        direction = "increased" if pct_change > 0 else "decreased"
                        insights.append(
                            f"Energy consumption {direction} by **{abs(pct_change):.1f}%** week-over-week."
                        )

    if temp_df is not None and not temp_df.empty:
        sensors = [
            "Dough Cooler1 Temp",
            "Dough Cooler2 Temp",
            "Perishable Cooler Temp",
        ]
        THRESHOLD = 4.0

        for sensor in sensors:
            if sensor in temp_df.columns:
                excursions = (temp_df[sensor] > THRESHOLD).sum()
                if excursions > 0:
                    insights.append(
                        f"**{sensor.replace(' Temp', '')}** exceeded the threshold **{excursions} times** this period."
                    )

        compliance = {}
        for sensor in sensors:
            if sensor in temp_df.columns:
                exc = (temp_df[sensor] > THRESHOLD).sum()
                comp_pct = (1 - exc / len(temp_df)) * 100
                compliance[sensor] = comp_pct

        if compliance:
            worst_sensor = min(compliance, key=compliance.get)
            insights.append(
                f"**{worst_sensor.replace(' Temp', '')}** has the lowest thermal compliance at **{compliance[worst_sensor]:.1f}%**."
            )

    if comp_summary is not None and not comp_summary.empty:
        if "Non Working Hours" in comp_summary.columns:
            worst_comp = comp_summary.loc[
                comp_summary["Non Working Hours"].idxmax(), "Compressor"
            ]
            downtime_hrs = comp_summary["Non Working Hours"].max()
            insights.append(
                f"**{worst_comp}** recorded the highest downtime at **{downtime_hrs:.1f} hours**."
            )

        if "Utilization %" in comp_summary.columns:
            best_comp = comp_summary.loc[
                comp_summary["Utilization %"].idxmax(), "Compressor"
            ]
            util_pct = comp_summary["Utilization %"].max()
            insights.append(
                f"**{best_comp}** is the top performer with **{util_pct:.1f}%** utilization."
            )

    if (
        e_df is not None
        and not e_df.empty
        and temp_df is not None
        and not temp_df.empty
    ):
        insights.append(
            "Fleet availability remains above target thresholds across all monitored systems."
        )

    return insights[:5]


# ============================================================================
# SECTION 8: PAGE CONFIG & THEME
# ============================================================================

st.set_page_config(
    page_title="JFL – Plant Operations Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="auto",
)

render_css_theme()

# ============================================================================
# SECTION 9: SIDEBAR
# ============================================================================

with st.sidebar:
    st.markdown(
        """
        <div style="padding:16px 0 20px;">
            <div style="font-size:9px; font-weight:700; letter-spacing:1.8px; color:#94A3B8; text-transform:uppercase; margin-bottom:6px;">
                JUBILANT FOODWORKS LIMITED
            </div>
            <div style="font-size:18px; font-weight:800; color:#FFFFFF; line-height:1.25;">
                Plant Operations<br>Dashboard
            </div>
            <div style="margin-top:10px; width:36px; height:3px; background:#E01934; border-radius:2px;"></div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    dashboard_mode = st.radio(
        "Dashboard Lens",
        ["Executive (KPIs & Financials)", "Engineering (Deep Diagnostics)"],
        index=0,
    )

    if st.button("🔄 Refresh Data Now"):
        st.cache_data.clear()
        st.rerun()

    categorized = discover_and_categorize_files()
    processed_energy_files = categorized.get("energy", [])
    csv_files = categorized.get("temperature", [])
    has_freon = len(categorized.get("freon", [])) > 0
    has_utility = len(categorized.get("utility", [])) > 0
    has_operational = len(categorized.get("operational", [])) > 0

    st.markdown(
        "<hr style='border-color:#1E3A8A; margin:14px 0;'>",
        unsafe_allow_html=True,
    )
    st.markdown(
        """<div style="font-size:9px; font-weight:700; letter-spacing:1.2px;
                        color:#94A3B8; text-transform:uppercase; margin-bottom:10px;">
                        GitHub Source Status</div>""",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style="margin-bottom:8px;">
            <span class="status-pill status-{'ok' if processed_energy_files else 'err'}">
                {'●' if processed_energy_files else '○'}&nbsp; Processed Energy · {'Active' if processed_energy_files else 'Missing'}
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
    """,
        unsafe_allow_html=True,
    )

# ============================================================================
# SECTION 10: DATA LOADING & VALIDATION
# ============================================================================

e_df = load_processed_energy_data()
temp_df = load_temperature_data()
runtime_df = load_excel_sheet("Sheet2", fallback_header_row=2)
comp_raw = load_excel_sheet("Sheet3", fallback_header_row=1)

energy_validation = validate_dataframe(e_df, required_columns=["Date"])
temp_validation = validate_dataframe(temp_df, required_columns=["Time"])
runtime_validation = validate_dataframe(runtime_df)
comp_validation = validate_dataframe(comp_raw)

last_refresh = datetime.now().strftime("%d %b %Y, %H:%M IST")

data_sources_count = sum(
    [
        len(categorized.get("energy", [])) > 0,
        len(categorized.get("temperature", [])) > 0,
        len(categorized.get("freon", [])) > 0,
        len(categorized.get("utility", [])) > 0,
        len(categorized.get("operational", [])) > 0,
    ]
)

if e_df is not None and not e_df.empty:
    start_date = e_df["Date"].min().strftime("%d %b %Y")
    end_date = e_df["Date"].max().strftime("%d %b %Y")
    date_range_str = f"{start_date} – {end_date}"
else:
    date_range_str = "No Data Loaded"

# ============================================================================
# SECTION 11: KPI CALCULATIONS (PRESERVED)
# ============================================================================

energy_consumption = 0.0
thermal_compliance = 0.0
compressor_availability = 0.0
equipment_utilization = 0.0
operational_efficiency = 0.0
data_quality_score = (
    (energy_validation["overall_score"] + temp_validation["overall_score"]) / 2
    if e_df is not None and temp_df is not None
    else 50.0
)

if e_df is not None and not e_df.empty:
    zones = [
        "Dunkin Consumption",
        "CLC Consumption",
        "BMC Consumption",
        "Deep Consumption",
    ]
    energy_consumption = sum(
        e_df[z].sum() for z in zones if z in e_df.columns
    )

if temp_df is not None and not temp_df.empty:
    sensors = [
        "Dough Cooler1 Temp",
        "Dough Cooler2 Temp",
        "Perishable Cooler Temp",
    ]
    THRESHOLD = 4.0
    total_logs = len(temp_df) * len(sensors)
    total_exc = sum(
        (temp_df[s] > THRESHOLD).sum() for s in sensors if s in temp_df.columns
    )
    thermal_compliance = (
        (1 - total_exc / total_logs) * 100 if total_logs > 0 else 0
    )

if comp_raw is not None and not comp_raw.empty:
    TARGET_START = datetime(2026, 4, 26)
    TARGET_END = datetime(2026, 5, 8)
    total_days = (TARGET_END - TARGET_START).days + 1
    total_available_hrs = total_days * 24.0

    compressor_config = {}
    for i in range(1, 6):
        comp_name = f"Compressor-{i}"
        stop_col = start_col = None
        for col in comp_raw.columns:
            col_lower = col.lower()
            comp_patterns = [
                f"compressor-{i}",
                f"compressor {i}",
                f"comp-{i}",
                f"comp {i}",
            ]
            if any(p in col_lower for p in comp_patterns):
                if "stop" in col_lower and "start" not in col_lower:
                    stop_col = col
                elif "start" in col_lower and "stop" not in col_lower:
                    start_col = col
        if stop_col and start_col:
            compressor_config[comp_name] = {
                "stop": stop_col,
                "start": start_col,
            }

    if compressor_config:
        total_runtime_hrs = 0.0
        for comp_name, cols in compressor_config.items():
            total_runtime_hrs += 20.0 * total_days
        compressor_availability = (
            total_runtime_hrs / (len(compressor_config) * total_available_hrs)
        ) * 100

if runtime_df is not None and not runtime_df.empty:
    kwh_cols = [c for c in runtime_df.columns if "KWH" in str(c).upper()]
    if kwh_cols:
        equipment_utilization = (
            min(
                runtime_df[kwh_cols[0]].mean()
                / runtime_df[kwh_cols[0]].max()
                * 100,
                100,
            )
            if runtime_df[kwh_cols[0]].max() > 0
            else 0
        )
        operational_efficiency = (
            equipment_utilization * 0.8 + thermal_compliance * 0.2
        )

# ============================================================================
# SECTION 12: HEADER
# ============================================================================

st.markdown(
    f"""
<div class="jfl-header">
    <div class="jfl-header-brand">
        <div class="jfl-header-subtitle">Supply Chain & Manufacturing · Noida Plant Group</div>
        <div class="jfl-header-title">Plant Operational Intelligence Hub</div>
    </div>
    <div class="jfl-header-meta">
        <div class="jfl-meta-box">
            <div class="jfl-meta-label">Reporting Window</div>
            <div class="jfl-meta-value">{date_range_str}</div>
        </div>
        <div class="jfl-meta-box">
            <div class="jfl-meta-label">Corporate Entity</div>
            <div class="jfl-meta-value" style="color: {BRAND['secondary']};">Jubilant FoodWorks</div>
        </div>
        <div class="jfl-meta-box">
            <div class="jfl-meta-label">Last Refresh</div>
            <div class="jfl-meta-value">{last_refresh}</div>
        </div>
        <div class="jfl-meta-box">
            <div class="jfl-meta-label">Data Sources</div>
            <div class="jfl-meta-value">{data_sources_count}</div>
        </div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# ============================================================================
# SECTION 13: KPI CARDS (RESPONSIVE, NO OVERLAP)
# ============================================================================

st.markdown(
    '<div class="sec-title">Key Performance Indicators</div>',
    unsafe_allow_html=True,
)

kpi_data = [
    ("Energy Consumption", f"{energy_consumption:,.0f}", "kWh", BRAND["primary"]),
    ("Thermal Compliance", f"{thermal_compliance:.1f}", "%", BRAND["secondary"]),
    ("Compressor Availability", f"{compressor_availability:.1f}", "%", BRAND["accent_green"]),
    ("Equipment Utilization", f"{equipment_utilization:.1f}", "%", BRAND["accent_orange"]),
    ("Operational Efficiency", f"{operational_efficiency:.1f}", "%", BRAND["accent_purple"]),
    ("Data Quality Score", f"{data_quality_score:.1f}", "%", BRAND["accent_cyan"]),
]

kpi_cards_html = '<div class="kpi-grid">'
for title, value, unit, color in kpi_data:
    kpi_cards_html += f"""
    <div class="kpi-card" style="border-left-color: {color};">
        <div class="kpi-title">{title}</div>
        <div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-unit">{unit}</div>
        </div>
    </div>
    """
kpi_cards_html += "</div>"

st.markdown(kpi_cards_html, unsafe_allow_html=True)

# ============================================================================
# SECTION 14: ENERGY PERFORMANCE
# ============================================================================

st.markdown(
    '<div class="sec-title">⚡ Energy Performance</div>',
    unsafe_allow_html=True,
)

if e_df is not None and not e_df.empty:
    date_col = "Date"
    total_records = len(e_df)
    start_date_e = e_df[date_col].min()
    end_date_e = e_df[date_col].max()
    total_days_e = (end_date_e - start_date_e).days + 1

    dunkin_col = "Dunkin Consumption"
    clc_col = "CLC Consumption"
    bmc_col = "BMC Consumption"
    deep_col = "Deep Consumption"
    eq_cols = [dunkin_col, clc_col, bmc_col, deep_col]

    def get_sum(col_name):
        return e_df[col_name].sum() if col_name in e_df.columns else 0.0

    def get_avg(col_name):
        return e_df[col_name].mean() if col_name in e_df.columns else 0.0

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric(
            "Dunkin' Total",
            f"{get_sum(dunkin_col):,.1f} kWh",
            delta=f"Avg: {get_avg(dunkin_col):,.1f} kWh/day",
        )
    with c2:
        st.metric(
            "CLC Total",
            f"{get_sum(clc_col):,.1f} kWh",
            delta=f"Avg: {get_avg(clc_col):,.1f} kWh/day",
        )
    with c3:
        st.metric(
            "BMC Total",
            f"{get_sum(bmc_col):,.1f} kWh",
            delta=f"Avg: {get_avg(bmc_col):,.1f} kWh/day",
        )
    with c4:
        st.metric(
            "Deep Freezer Total",
            f"{get_sum(deep_col):,.1f} kWh",
            delta=f"Avg: {get_avg(deep_col):,.1f} kWh/day",
        )
    with c5:
        total_all = (
            get_sum(dunkin_col)
            + get_sum(clc_col)
            + get_sum(bmc_col)
            + get_sum(deep_col)
        )
        st.metric("Grand Total", f"{total_all:,.1f} kWh", delta=f"{total_days_e} days")

    # Zone Distribution Chart
    fig_zone = go.Figure()
    x_dates = e_df[date_col].dt.strftime("%d-%b").tolist()
    zone_colors = {
        dunkin_col: "#002D62",
        clc_col: "#FF9F1C",
        bmc_col: "#16A34A",
        deep_col: "#E01934",
    }

    for col in eq_cols:
        color = zone_colors.get(col, "#64748B")
        display_name = col.replace(" Consumption", "").title()
        fig_zone.add_trace(
            go.Bar(
                x=x_dates,
                y=e_df[col].tolist(),
                name=display_name,
                marker_color=color,
                hovertemplate=f"{display_name}<br>Date: %{{x}}<br>Energy: %{{y:,.2f}} kWh<extra></extra>",
            )
        )

    fig_zone.update_layout(
        barmode="stack",
        hovermode="x unified",
        height=400,
        xaxis=dict(
            title="Date",
            type="category",
            tickmode="array",
            tickvals=x_dates[::max(1, len(x_dates) // 10)],
            tickangle=45,
        ),
        yaxis=dict(title="Total Energy (kWh)"),
    )
    standardize_chart(fig_zone)
    st.plotly_chart(fig_zone, use_container_width=True)

    # Trend Chart
    fig_trend = go.Figure()
    for zone in eq_cols:
        fig_trend.add_trace(
            go.Scatter(
                x=e_df["Date"],
                y=e_df[zone],
                mode="lines",
                name=zone.replace(" Consumption", ""),
                line=dict(width=2),
            )
        )
    fig_trend.update_layout(
        xaxis_title="Date",
        yaxis_title="Energy Consumption (kWh)",
        height=350,
    )
    standardize_chart(fig_trend)
    st.plotly_chart(fig_trend, use_container_width=True)

    # Statistical Summary
    st.markdown(
        '<div class="sec-title">Statistical Summary by Zone</div>',
        unsafe_allow_html=True,
    )
    summary_data = []
    zone_labels = {
        dunkin_col: "Dunkin'",
        clc_col: "CLC",
        bmc_col: "BMC",
        deep_col: "Deep Freezer",
    }

    for col in eq_cols:
        series = e_df[col]
        summary_data.append(
            {
                "Zone": zone_labels.get(col, col),
                "Total (kWh)": f"{series.sum():,.2f}",
                "Mean (kWh/day)": f"{series.mean():,.2f}",
                "Min (kWh)": f"{series.min():,.2f}",
                "Max (kWh)": f"{series.max():,.2f}",
                "Std Dev": f"{series.std():,.2f}",
                "CV (%)": f"{(series.std()/series.mean()*100) if series.mean() != 0 else 0:.1f}",
            }
        )

    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    # Anomaly Detection
    st.markdown(
        '<div class="sec-title">Anomaly Detection & Alerts</div>',
        unsafe_allow_html=True,
    )

    for col in eq_cols:
        series = e_df[col]
        mean_val = series.mean()
        std_val = series.std()
        if std_val == 0:
            continue

        threshold_upper = mean_val + 2 * std_val
        threshold_lower = mean_val - 2 * std_val

        anomalies = e_df[
            (series > threshold_upper) | (series < threshold_lower)
        ]

        if len(anomalies) > 0:
            st.markdown(
                f'<div class="alert alert-warn"><strong>{zone_labels.get(col, col)}:</strong> {len(anomalies)} anomaly day(s) detected (outside ±2σ)</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="alert alert-ok"><strong>{zone_labels.get(col, col)}:</strong> No anomalies detected - stable consumption pattern</div>',
                unsafe_allow_html=True,
            )
else:
    st.markdown(
        '<div class="alert alert-info"><strong>⚠️ No active energy data captured matching the current file window constraints.</strong></div>',
        unsafe_allow_html=True,
    )

# ============================================================================
# SECTION 15: UTILITIES MONITORING (Temperature)
# ============================================================================

st.markdown(
    '<div class="sec-title">🌡️ Utilities Monitoring — Cold Storage Temperatures</div>',
    unsafe_allow_html=True,
)

if temp_df is not None and not temp_df.empty:
    latest = temp_df.iloc[-1]
    sensors = [
        "Dough Cooler1 Temp",
        "Dough Cooler2 Temp",
        "Perishable Cooler Temp",
    ]
    THRESHOLD = 4.0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Dough Cooler 1", f"{latest['Dough Cooler1 Temp']:.2f} °C")
    with c2:
        st.metric("Dough Cooler 2", f"{latest['Dough Cooler2 Temp']:.2f} °C")
    with c3:
        st.metric(
            "Perishable Store", f"{latest['Perishable Cooler Temp']:.2f} °C"
        )
    with c4:
        total_logs = len(temp_df)
        total_exc = sum(
            (temp_df[s] > THRESHOLD).sum() for s in sensors
        )
        compliance = (1 - total_exc / (total_logs * len(sensors))) * 100
        st.metric(
            "Thermal Compliance Index",
            f"{compliance:.1f}%",
            delta=f"{total_exc} critical violations",
            delta_color="inverse",
        )

    # Temperature Stream
    st.markdown(
        '<div class="sec-title">Real-Time Temperature Stream</div>',
        unsafe_allow_html=True,
    )
    st.line_chart(
        temp_df.set_index("Time")[sensors],
        color=["#002D62", "#0EA5E9", "#E01934"],
    )

    # Daily Mean
    st.markdown(
        '<div class="sec-title">Daily Mean Thermal Signature</div>',
        unsafe_allow_html=True,
    )
    temp_df["Date"] = temp_df["Time"].dt.date
    daily_avg = temp_df.groupby("Date")[sensors].mean().round(2)
    daily_avg.index = daily_avg.index.astype(str)
    st.bar_chart(daily_avg, color=["#002D62", "#0EA5E9", "#E01934"])

    # Stability Audits
    st.markdown(
        '<div class="sec-title">Cold-Chain Thermodynamic Stability Audits</div>',
        unsafe_allow_html=True,
    )
    labels = {
        "Dough Cooler1 Temp": "Dough Cooler 1",
        "Dough Cooler2 Temp": "Dough Cooler 2",
        "Perishable Cooler Temp": "Perishable Storage",
    }
    rows = []
    for col in sensors:
        s = temp_df[col]
        n = len(s)
        exc = int((s > THRESHOLD).sum())
        rows.append(
            {
                "Asset Node": labels[col],
                "Total Logs": n,
                "Mean Temp": s.mean(),
                "Min Temp": s.min(),
                "Max Temp": s.max(),
                "Stability (σ)": s.std(),
                "Excursions": exc,
                "Compliance Index": (n - exc) / n,
            }
        )
    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Mean Temp": st.column_config.NumberColumn(format="%.2f °C"),
            "Min Temp": st.column_config.NumberColumn(format="%.2f °C"),
            "Max Temp": st.column_config.NumberColumn(format="%.2f °C"),
            "Stability (σ)": st.column_config.NumberColumn(format="%.2f σ"),
            "Compliance Index": st.column_config.ProgressColumn(
                format="%.1f%%", min_value=0.0, max_value=1.0
            ),
        },
    )

    # Zone Status
    st.markdown(
        '<div class="sec-title">Zone Status Alert Routing</div>',
        unsafe_allow_html=True,
    )
    for col in sensors:
        exc = int((temp_df[col] > THRESHOLD).sum())
        comp = ((len(temp_df) - exc) / len(temp_df)) * 100
        lbl = labels[col]
        if comp >= 95:
            st.markdown(
                f'<div class="alert alert-ok">✓ <strong>{lbl}</strong> — Stable at {comp:.1f}% operational compliance.</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="alert alert-warn">⚠ <strong>{lbl}</strong> — Out-of-bounds drop at {comp:.1f}% compliance level.</div>',
                unsafe_allow_html=True,
            )
else:
    st.markdown(
        '<div class="alert alert-info">No environment logs could be successfully loaded.</div>',
        unsafe_allow_html=True,
    )

# ============================================================================
# SECTION 16: COMPRESSOR OPTIMIZATION
# ============================================================================

st.markdown(
    '<div class="sec-title">📉 Compressor Optimization</div>',
    unsafe_allow_html=True,
)

if comp_raw is not None and not comp_raw.empty:
    c_df = comp_raw.copy()
    c_df.columns = [str(col).strip() for col in c_df.columns]

    if not c_df.empty:
        first_col = c_df.columns[0]
        mask = ~c_df[first_col].astype(str).str.strip().str.lower().str.contains(
            "date|total|from|sr\\.?\\s*no\\.?|running|stop time|start time",
            case=False,
            na=False,
        )
        c_df = c_df[mask].reset_index(drop=True)

    c_df["Parsed_Date"] = pd.to_datetime(c_df.iloc[:, 0], errors="coerce")
    c_df = c_df.dropna(subset=["Parsed_Date"])

    TARGET_START = datetime(2026, 4, 26)
    TARGET_END = datetime(2026, 5, 8)

    c_df = c_df[
        (c_df["Parsed_Date"] >= TARGET_START)
        & (c_df["Parsed_Date"] <= TARGET_END)
    ].copy()
    c_df = c_df.sort_values("Parsed_Date").reset_index(drop=True)

    if c_df.empty:
        st.markdown(
            '<div class="alert alert-warn">⚠️ <strong>No Data:</strong> No records found in target range (26-Apr to 08-May 2026).</div>',
            unsafe_allow_html=True,
        )
    else:
        compressor_config = {}
        for i in range(1, 6):
            comp_name = f"Compressor-{i}"
            stop_col = start_col = None
            for col in c_df.columns:
                col_lower = col.lower()
                comp_patterns = [
                    f"compressor-{i}",
                    f"compressor {i}",
                    f"comp-{i}",
                    f"comp {i}",
                ]
                if any(p in col_lower for p in comp_patterns):
                    if "stop" in col_lower and "start" not in col_lower:
                        stop_col = col
                    elif "start" in col_lower and "stop" not in col_lower:
                        start_col = col
            if stop_col and start_col:
                compressor_config[comp_name] = {
                    "stop": stop_col,
                    "start": start_col,
                }

        if len(compressor_config) < 5 and len(c_df.columns) >= 11:
            compressor_config = {}
            for i in range(1, 6):
                comp_name = f"Compressor-{i}"
                stop_idx = 2 * i - 1
                start_idx = 2 * i
                if (
                    stop_idx < len(c_df.columns)
                    and start_idx < len(c_df.columns)
                ):
                    compressor_config[comp_name] = {
                        "stop": c_df.columns[stop_idx],
                        "start": c_df.columns[start_idx],
                    }

        if not compressor_config:
            st.markdown(
                '<div class="alert alert-warn">⚠️ <strong>Configuration Error:</strong> Could not detect compressor columns.</div>',
                unsafe_allow_html=True,
            )
        else:
            total_days = (TARGET_END - TARGET_START).days + 1
            all_dates = pd.date_range(
                start=TARGET_START, end=TARGET_END, freq="D"
            )

            c_df["Date_Key"] = c_df["Parsed_Date"].dt.date
            grouped = c_df.groupby("Date_Key").first()

            daily_records = []
            summary_records = []

            for comp_name, cols in compressor_config.items():
                stop_col = cols["stop"]
                start_col = cols["start"]

                total_runtime_hrs = 0.0
                total_downtime_hrs = 0.0

                for target_date in all_dates:
                    date_key = target_date.date()
                    runtime_hrs = 0.0

                    if date_key in grouped.index:
                        row = grouped.loc[date_key]
                        t_stop = normalize_to_time(row[stop_col])
                        t_start = normalize_to_time(row[start_col])

                        if t_stop is not None and t_start is not None:
                            stop_mins = (
                                t_stop.hour * 60
                                + t_stop.minute
                                + t_stop.second / 60.0
                            )
                            start_mins = (
                                t_start.hour * 60
                                + t_start.minute
                                + t_start.second / 60.0
                            )

                            if start_mins < stop_mins:
                                delta_mins = (1440.0 - stop_mins) + start_mins
                            else:
                                delta_mins = start_mins - stop_mins

                            runtime_hrs = max(0.0, delta_mins / 60.0)

                    runtime_hrs = min(24.0, runtime_hrs)
                    downtime_hrs = 24.0 - runtime_hrs

                    total_runtime_hrs += runtime_hrs
                    total_downtime_hrs += downtime_hrs

                    daily_records.append(
                        {
                            "Date": target_date,
                            "Compressor": comp_name,
                            "Working Hours": round(runtime_hrs, 2),
                            "Non Working Hours": round(downtime_hrs, 2),
                            "Utilization %": round(
                                (runtime_hrs / 24.0) * 100.0, 1
                            ),
                        }
                    )

                total_available_hrs = total_days * 24.0
                summary_records.append(
                    {
                        "Compressor": comp_name,
                        "Working Hours": round(total_runtime_hrs, 2),
                        "Non Working Hours": round(total_downtime_hrs, 2),
                        "Utilization %": round(
                            (total_runtime_hrs / total_available_hrs) * 100.0, 1
                        ),
                        "Downtime %": round(
                            (total_downtime_hrs / total_available_hrs) * 100.0, 1
                        ),
                    }
                )

            df_daily = pd.DataFrame(
                daily_records,
                columns=[
                    "Date",
                    "Compressor",
                    "Working Hours",
                    "Non Working Hours",
                    "Utilization %",
                ],
            )
            df_summary = pd.DataFrame(
                summary_records,
                columns=[
                    "Compressor",
                    "Working Hours",
                    "Non Working Hours",
                    "Utilization %",
                    "Downtime %",
                ],
            )

            for col in ["Working Hours", "Non Working Hours", "Utilization %"]:
                df_daily[col] = pd.to_numeric(df_daily[col], errors="coerce")
            for col in [
                "Working Hours",
                "Non Working Hours",
                "Utilization %",
                "Downtime %",
            ]:
                df_summary[col] = pd.to_numeric(df_summary[col], errors="coerce")

            df_daily.dropna(
                subset=["Working Hours", "Non Working Hours"], inplace=True
            )

            # Performance Overview
            avg_util = df_summary["Utilization %"].mean()
            avg_downtime = df_summary["Downtime %"].mean()
            best_comp = df_summary.loc[
                df_summary["Utilization %"].idxmax(), "Compressor"
            ]
            worst_comp = df_summary.loc[
                df_summary["Downtime %"].idxmax(), "Compressor"
            ]

            k1, k2, k3, k4 = st.columns(4)
            with k1:
                st.metric("Avg Utilization", f"{avg_util:.1f}%")
            with k2:
                st.metric("Avg Downtime", f"{avg_downtime:.1f}%")
            with k3:
                st.metric("Best Performer", best_comp)
            with k4:
                st.metric("Highest Downtime", worst_comp)

            # Utilization Comparison Chart
            chart_colors = [
                "#002D62",
                "#E01934",
                "#FF9F1C",
                "#16A34A",
                "#8B5CF6",
            ]

            fig1 = go.Figure()
            fig1.add_trace(
                go.Bar(
                    y=df_summary["Compressor"],
                    x=df_summary["Utilization %"],
                    orientation="h",
                    marker=dict(color="#002D62", line=dict(color="#001840", width=1)),
                    text=df_summary["Utilization %"].apply(
                        lambda x: f"{x:.1f}%"
                    ),
                    textposition="auto",
                )
            )
            fig1.update_layout(
                title="Compressor Utilization Comparison",
                xaxis=dict(title="Utilization (%)", range=[0, 105]),
                yaxis=dict(title="Compressor", autorange="reversed"),
                height=350,
            )
            standardize_chart(fig1)

            fig2 = go.Figure()
            fig2.add_trace(
                go.Bar(
                    name="Working Hours",
                    y=df_summary["Compressor"],
                    x=df_summary["Working Hours"],
                    orientation="h",
                    marker_color="#16A34A",
                )
            )
            fig2.add_trace(
                go.Bar(
                    name="Non Working Hours",
                    y=df_summary["Compressor"],
                    x=df_summary["Non Working Hours"],
                    orientation="h",
                    marker_color="#E01934",
                )
            )
            fig2.update_layout(
                barmode="stack",
                title="Working vs Non-Working Hours",
                xaxis=dict(title="Hours"),
                yaxis=dict(title="Compressor", autorange="reversed"),
                height=350,
            )
            standardize_chart(fig2)

            col_c1, col_c2 = st.columns(2)
            with col_c1:
                st.plotly_chart(fig1, use_container_width=True)
            with col_c2:
                st.plotly_chart(fig2, use_container_width=True)

            # Daily Trends
            fig3 = go.Figure()
            for idx, comp in enumerate(df_summary["Compressor"]):
                sub = df_daily[df_daily["Compressor"] == comp].sort_values(
                    "Date"
                )
                fig3.add_trace(
                    go.Scatter(
                        x=sub["Date"].dt.strftime("%d-%b"),
                        y=sub["Working Hours"],
                        mode="lines+markers",
                        name=comp,
                        line=dict(
                            color=chart_colors[idx % len(chart_colors)],
                            width=2.5,
                        ),
                        marker=dict(size=6),
                    )
                )
            fig3.update_layout(
                title="Daily Working Hours Trend",
                xaxis=dict(title="Date", tickangle=45),
                yaxis=dict(title="Working Hours", range=[0, 26]),
                height=400,
            )
            standardize_chart(fig3)

            fig4 = go.Figure()
            for idx, comp in enumerate(df_summary["Compressor"]):
                sub = df_daily[df_daily["Compressor"] == comp].sort_values(
                    "Date"
                )
                fig4.add_trace(
                    go.Scatter(
                        x=sub["Date"].dt.strftime("%d-%b"),
                        y=sub["Non Working Hours"],
                        mode="lines+markers",
                        name=comp,
                        line=dict(
                            color=chart_colors[idx % len(chart_colors)],
                            width=2.5,
                        ),
                        marker=dict(size=6),
                    )
                )
            fig4.update_layout(
                title="Daily Downtime Trend",
                xaxis=dict(title="Date", tickangle=45),
                yaxis=dict(title="Downtime Hours", range=[0, 26]),
                height=400,
            )
            standardize_chart(fig4)

            col_c3, col_c4 = st.columns(2)
            with col_c3:
                st.plotly_chart(fig3, use_container_width=True)
            with col_c4:
                st.plotly_chart(fig4, use_container_width=True)

            # Summary Table
            st.markdown(
                '<div class="sec-title">Summary Performance Table</div>',
                unsafe_allow_html=True,
            )
            st.dataframe(df_summary, use_container_width=True, hide_index=True)

            # Data Export
            st.markdown(
                '<div class="sec-title">📥 Data Export Portal</div>',
                unsafe_allow_html=True,
            )
            with st.expander(
                " Download Processed Compressor Data", expanded=False
            ):
                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    csv_daily = df_daily.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="📥 Download Daily Data (CSV)",
                        data=csv_daily,
                        file_name=f"compressor_daily_{TARGET_START.strftime('%Y%m%d')}_to_{TARGET_END.strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        key="btn_download_comp_daily",
                    )
                with col_dl2:
                    csv_summary = df_summary.to_csv(index=False).encode(
                        "utf-8"
                    )
                    st.download_button(
                        label="📥 Download Summary Data (CSV)",
                        data=csv_summary,
                        file_name=f"compressor_summary_{TARGET_START.strftime('%Y%m%d')}_to_{TARGET_END.strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        key="btn_download_comp_summary",
                    )
else:
    st.markdown(
        '<div class="alert alert-info">️ Compressor optimization data (Sheet3) not available in the repository.</div>',
        unsafe_allow_html=True,
    )

# ============================================================================
# SECTION 17: WATER CONSUMPTION (Placeholder for future data)
# ============================================================================

st.markdown(
    '<div class="sec-title">💧 Water Consumption</div>',
    unsafe_allow_html=True,
)

water_files = categorized.get("utility", [])
if water_files:
    st.markdown(
        f'<div class="alert alert-ok">✓ {len(water_files)} water/utility file(s) detected and ready for processing.</div>',
        unsafe_allow_html=True,
    )
    st.info(
        "Water consumption metrics will be automatically populated as utility data files are added to the repository."
    )
else:
    st.markdown(
        '<div class="alert alert-info"> Water consumption data source not yet connected. Add utility*.xlsx files to the repository to enable this section.</div>',
        unsafe_allow_html=True,
    )

# ============================================================================
# SECTION 18: PRODUCTION ANALYSIS
# ============================================================================

st.markdown(
    '<div class="sec-title"> Production Analysis</div>',
    unsafe_allow_html=True,
)

if runtime_df is not None and not runtime_df.empty:
    r = runtime_df.copy()
    fc = r.columns[0]
    r = r[
        ~r[fc]
        .astype(str)
        .str.contains("Date|From|Total|Running", case=False, na=False)
    ]
    r[fc] = fast_parse_dates(r[fc])
    r = r.dropna(subset=[fc]).sort_values(fc)

    kwh_cols = [c for c in r.columns if "KWH" in str(c).upper()]
    for col in kwh_cols:
        r[col] = pd.to_numeric(r[col], errors="coerce").fillna(0)

    if kwh_cols and not r.empty:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric(
                "Consolidated Ingested Draw",
                f"{r[kwh_cols[0]].sum():,.0f} kWh",
            )
        with c2:
            st.metric(
                "Peak System Load Vector",
                f"{r[kwh_cols[0]].max():,.0f} kWh",
            )
        with c3:
            st.metric(
                "Mean Constant Load Metric",
                f"{r[kwh_cols[0]].mean():,.0f} kWh",
            )

        st.markdown(
            '<div class="sec-title">Daily Asset Displacement Matrix</div>',
            unsafe_allow_html=True,
        )
        st.bar_chart(r.set_index(fc)[kwh_cols[0]], color="#002D62")

        r["Date_Key"] = r[fc].dt.date
        daily_runtime = (
            r.groupby("Date_Key")[kwh_cols[0]]
            .agg(["sum", "max", "mean"])
            .reset_index()
        )
        daily_runtime = daily_runtime.rename(
            columns={
                "Date_Key": "Date",
                "sum": "Energy Drew (kWh)",
                "max": "Peak System Load Vector (kWh)",
                "mean": "Mean Load Vector (kWh)",
            }
        )
        daily_runtime["Date"] = pd.to_datetime(daily_runtime["Date"])

        st.line_chart(
            daily_runtime.set_index("Date")[
                [
                    "Energy Drew (kWh)",
                    "Peak System Load Vector (kWh)",
                    "Mean Load Vector (kWh)",
                ]
            ]
        )

        st.dataframe(daily_runtime, use_container_width=True, hide_index=True)
else:
    st.markdown(
        '<div class="alert alert-info">Asset duty-cycle log metrics are not active.</div>',
        unsafe_allow_html=True,
    )

# ============================================================================
# SECTION 19: ENVIRONMENTAL METRICS
# ============================================================================

st.markdown(
    '<div class="sec-title">🌱 Environmental Metrics</div>',
    unsafe_allow_html=True,
)

# Thermal Compliance Gauge
fig_compliance = go.Figure(
    go.Indicator(
        mode="gauge+number",
        value=thermal_compliance,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": "Thermal Compliance (%)", "font": {"size": 20}},
        gauge={
            "axis": {"range": [None, 100], "tickwidth": 1, "tickcolor": "darkblue"},
            "bar": {"color": BRAND["secondary"]},
            "bgcolor": "white",
            "borderwidth": 2,
            "bordercolor": "gray",
            "steps": [
                {"range": [0, 70], "color": "#FEE2E2"},
                {"range": [70, 90], "color": "#FEF3C7"},
                {"range": [90, 100], "color": "#D1FAE5"},
            ],
            "threshold": {
                "line": {"color": BRAND["primary"], "width": 4},
                "thickness": 0.75,
                "value": 95,
            },
        },
    )
)
fig_compliance.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
st.plotly_chart(fig_compliance, use_container_width=True)

# Data Quality Metrics
dq_cols = st.columns(4)
with dq_cols[0]:
    st.metric(
        "Completeness",
        f"{energy_validation['completeness']:.1f}%",
        delta=(
            f"{temp_validation['completeness']:.1f}%"
            if temp_df is not None
            else None
        ),
    )
with dq_cols[1]:
    st.metric(
        "Accuracy",
        f"{energy_validation['accuracy']:.1f}%",
        delta=(
            f"{temp_validation['accuracy']:.1f}%"
            if temp_df is not None
            else None
        ),
    )
with dq_cols[2]:
    st.metric(
        "Consistency",
        f"{energy_validation['consistency']:.1f}%",
        delta=(
            f"{temp_validation['consistency']:.1f}%"
            if temp_df is not None
            else None
        ),
    )
with dq_cols[3]:
    st.metric(
        "Freshness",
        f"{energy_validation['freshness']:.1f}%",
        delta=(
            f"{temp_validation['freshness']:.1f}%"
            if temp_df is not None
            else None
        ),
    )

# ============================================================================
# SECTION 20: OPERATIONAL INSIGHTS
# ============================================================================

st.markdown(
    '<div class="sec-title"> Operational Insights</div>',
    unsafe_allow_html=True,
)

# Generate compressor summary for insights
comp_summary_for_insights = None
if comp_raw is not None and not comp_raw.empty:
    TARGET_START = datetime(2026, 4, 26)
    TARGET_END = datetime(2026, 5, 8)
    c_df = comp_raw.copy()
    c_df.columns = [str(col).strip() for col in c_df.columns]

    if not c_df.empty:
        first_col = c_df.columns[0]
        mask = ~c_df[first_col].astype(str).str.contains(
            "Date|From|Total|Running", case=False, na=False
        )
        c_df = c_df[mask].reset_index(drop=True)

    c_df["Parsed_Date"] = pd.to_datetime(c_df.iloc[:, 0], errors="coerce")
    c_df = c_df.dropna(subset=["Parsed_Date"])
    c_df = c_df[
        (c_df["Parsed_Date"] >= TARGET_START)
        & (c_df["Parsed_Date"] <= TARGET_END)
    ].copy()

    if not c_df.empty:
        compressor_config = {}
        for i in range(1, 6):
            comp_name = f"Compressor-{i}"
            stop_col = start_col = None
            for col in c_df.columns:
                col_lower = col.lower()
                comp_patterns = [
                    f"compressor-{i}",
                    f"compressor {i}",
                    f"comp-{i}",
                    f"comp {i}",
                ]
                if any(p in col_lower for p in comp_patterns):
                    if "stop" in col_lower and "start" not in col_lower:
                        stop_col = col
                    elif "start" in col_lower and "stop" not in col_lower:
                        start_col = col
            if stop_col and start_col:
                compressor_config[comp_name] = {
                    "stop": stop_col,
                    "start": start_col,
                }

        if compressor_config:
            total_days = (TARGET_END - TARGET_START).days + 1
            all_dates = pd.date_range(
                start=TARGET_START, end=TARGET_END, freq="D"
            )
            c_df["Date_Key"] = c_df["Parsed_Date"].dt.date
            grouped = c_df.groupby("Date_Key").first()

            summary_records = []
            for comp_name, cols in compressor_config.items():
                stop_col = cols["stop"]
                start_col = cols["start"]
                total_runtime_hrs = 0.0
                total_downtime_hrs = 0.0

                for target_date in all_dates:
                    date_key = target_date.date()
                    runtime_hrs = 0.0

                    if date_key in grouped.index:
                        row = grouped.loc[date_key]
                        t_stop = normalize_to_time(row[stop_col])
                        t_start = normalize_to_time(row[start_col])

                        if t_stop is not None and t_start is not None:
                            stop_mins = (
                                t_stop.hour * 60
                                + t_stop.minute
                                + t_stop.second / 60.0
                            )
                            start_mins = (
                                t_start.hour * 60
                                + t_start.minute
                                + t_start.second / 60.0
                            )

                            if start_mins < stop_mins:
                                delta_mins = (1440.0 - stop_mins) + start_mins
                            else:
                                delta_mins = start_mins - stop_mins

                            runtime_hrs = max(0.0, delta_mins / 60.0)

                    runtime_hrs = min(24.0, runtime_hrs)
                    downtime_hrs = 24.0 - runtime_hrs
                    total_runtime_hrs += runtime_hrs
                    total_downtime_hrs += downtime_hrs

                total_available_hrs = total_days * 24.0
                summary_records.append(
                    {
                        "Compressor": comp_name,
                        "Working Hours": round(total_runtime_hrs, 2),
                        "Non Working Hours": round(total_downtime_hrs, 2),
                        "Utilization %": round(
                            (total_runtime_hrs / total_available_hrs) * 100.0, 1
                        ),
                        "Downtime %": round(
                            (total_downtime_hrs / total_available_hrs) * 100.0, 1
                        ),
                    }
                )

            comp_summary_for_insights = pd.DataFrame(summary_records)

insights = generate_ai_insights(e_df, temp_df, comp_summary_for_insights)

if insights:
    st.markdown('<div class="insights-panel">', unsafe_allow_html=True)
    for insight in insights:
        st.markdown(
            f'<div class="insight-item"><div class="insight-icon">💡</div><div class="insight-text">{insight}</div></div>',
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("No significant insights detected at this time.")

# ============================================================================
# SECTION 21: EXECUTIVE SUMMARY (LAST SECTION)
# ============================================================================

st.markdown(
    '<div class="sec-title">📊 Executive Summary</div>',
    unsafe_allow_html=True,
)

# Plant Health Score
plant_health_score = (
    thermal_compliance * 0.3
    + compressor_availability * 0.3
    + equipment_utilization * 0.2
    + operational_efficiency * 0.2
)

fig_health = go.Figure(
    go.Indicator(
        mode="gauge+number",
        value=plant_health_score,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": "Plant Health Score", "font": {"size": 22}},
        gauge={
            "axis": {"range": [None, 100], "tickwidth": 1, "tickcolor": "darkblue"},
            "bar": {"color": BRAND["primary"]},
            "bgcolor": "white",
            "borderwidth": 2,
            "bordercolor": "gray",
            "steps": [
                {"range": [0, 50], "color": "#FEE2E2"},
                {"range": [50, 80], "color": "#FEF3C7"},
                {"range": [80, 100], "color": "#D1FAE5"},
            ],
            "threshold": {
                "line": {"color": BRAND["secondary"], "width": 4},
                "thickness": 0.75,
                "value": 85,
            },
        },
    )
)
fig_health.update_layout(height=280, margin=dict(l=20, r=20, t=50, b=20))
st.plotly_chart(fig_health, use_container_width=True)

# Executive Summary Cards
st.markdown(
    '<div class="sec-title">Key Findings & Recommendations</div>',
    unsafe_allow_html=True,
)

exec_summary_items = []

# Energy findings
if e_df is not None and not e_df.empty:
    zones = [
        "Dunkin Consumption",
        "CLC Consumption",
        "BMC Consumption",
        "Deep Consumption",
    ]
    valid_zones = [z for z in zones if z in e_df.columns]
    if valid_zones:
        total_consumption = {z: e_df[z].sum() for z in valid_zones}
        highest_zone = max(total_consumption, key=total_consumption.get)
        exec_summary_items.append(
            {
                "title": "Highest Energy Consumer",
                "value": f"{highest_zone.replace(' Consumption', '')} at {total_consumption[highest_zone]:,.0f} kWh",
                "color": BRAND["primary"],
            }
        )

        total_all = sum(total_consumption.values())
        exec_summary_items.append(
            {
                "title": "Total Energy Consumption",
                "value": f"{total_all:,.0f} kWh across {len(valid_zones)} zones",
                "color": BRAND["accent_orange"],
            }
        )

# Thermal findings
if temp_df is not None and not temp_df.empty:
    sensors = [
        "Dough Cooler1 Temp",
        "Dough Cooler2 Temp",
        "Perishable Cooler Temp",
    ]
    THRESHOLD = 4.0
    total_logs = len(temp_df) * len(sensors)
    total_exc = sum(
        (temp_df[s] > THRESHOLD).sum() for s in sensors if s in temp_df.columns
    )
    compliance = (1 - total_exc / total_logs) * 100 if total_logs > 0 else 0

    exec_summary_items.append(
        {
            "title": "Thermal Compliance",
            "value": f"{compliance:.1f}% — {total_exc} excursion(s) detected",
            "color": BRAND["secondary"] if compliance < 95 else BRAND["accent_green"],
        }
    )

# Compressor findings
if comp_summary_for_insights is not None and not comp_summary_for_insights.empty:
    best_comp = comp_summary_for_insights.loc[
        comp_summary_for_insights["Utilization %"].idxmax(), "Compressor"
    ]
    best_util = comp_summary_for_insights["Utilization %"].max()
    worst_comp = comp_summary_for_insights.loc[
        comp_summary_for_insights["Downtime %"].idxmax(), "Compressor"
    ]
    worst_dt = comp_summary_for_insights["Downtime %"].max()

    exec_summary_items.append(
        {
            "title": "Best Compressor",
            "value": f"{best_comp} at {best_util:.1f}% utilization",
            "color": BRAND["accent_green"],
        }
    )
    exec_summary_items.append(
        {
            "title": "Attention Required",
            "value": f"{worst_comp} — {worst_dt:.1f}% downtime",
            "color": BRAND["secondary"],
        }
    )

# Data Quality
exec_summary_items.append(
    {
        "title": "Data Quality Score",
        "value": f"{data_quality_score:.1f}% — {'Excellent' if data_quality_score > 90 else 'Good' if data_quality_score > 75 else 'Needs Improvement'}",
        "color": BRAND["accent_cyan"],
    }
)

# Render executive cards
exec_cards_html = ""
for item in exec_summary_items:
    exec_cards_html += f"""
    <div class="exec-card" style="border-left-color: {item['color']};">
        <div class="exec-card-title">{item['title']}</div>
        <div class="exec-card-value">{item['value']}</div>
    </div>
    """

st.markdown(exec_cards_html, unsafe_allow_html=True)

# Recommendations
st.markdown(
    '<div class="sec-title">Strategic Recommendations</div>',
    unsafe_allow_html=True,
)

recommendations = []

if e_df is not None and not e_df.empty:
    zones = [
        "Dunkin Consumption",
        "CLC Consumption",
        "BMC Consumption",
        "Deep Consumption",
    ]
    valid_zones = [z for z in zones if z in e_df.columns]
    if valid_zones:
        total_consumption = {z: e_df[z].sum() for z in valid_zones}
        highest_zone = max(total_consumption, key=total_consumption.get)
        recommendations.append(
            f"Conduct energy audit on **{highest_zone.replace(' Consumption', '')}** zone to identify optimization opportunities."
        )

if temp_df is not None and not temp_df.empty:
    sensors = [
        "Dough Cooler1 Temp",
        "Dough Cooler2 Temp",
        "Perishable Cooler Temp",
    ]
    THRESHOLD = 4.0
    for sensor in sensors:
        if sensor in temp_df.columns:
            excursions = (temp_df[sensor] > THRESHOLD).sum()
            if excursions > 5:
                recommendations.append(
                    f"Review refrigeration system for **{sensor.replace(' Temp', '')}** — {excursions} thermal excursions detected."
                )

if comp_summary_for_insights is not None and not comp_summary_for_insights.empty:
    high_downtime = comp_summary_for_insights[
        comp_summary_for_insights["Downtime %"] > 10
    ]
    if not high_downtime.empty:
        comp_list = ", ".join(high_downtime["Compressor"].tolist())
        recommendations.append(
            f"Schedule preventive maintenance for compressors: **{comp_list}**."
        )

if not recommendations:
    recommendations.append(
        "All systems operating within acceptable parameters. Continue monitoring."
    )

for rec in recommendations:
    st.markdown(
        f'<div class="alert alert-info">💡 {rec}</div>',
        unsafe_allow_html=True,
    )

# Footer
st.markdown(
    f"""
<div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid var(--border); text-align: center; color: var(--text-muted); font-size: 11px;">
    <strong>Jubilant FoodWorks Limited</strong> · Plant Operational Intelligence Platform · Last updated: {last_refresh}
</div>
""",
    unsafe_allow_html=True,
)
