import os
import glob
import warnings
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

warnings.filterwarnings("ignore", category=UserWarning)

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Plant Ops Hub",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── DESIGN TOKENS ────────────────────────────────────────────────────────────
# Palette: deep navy base, ice-cyan accent, amber alert, emerald gain
C_BG        = "#0D1117"
C_SURFACE   = "#161B22"
C_BORDER    = "#21262D"
C_CYAN      = "#00D2FF"
C_AMBER     = "#F0A500"
C_EMERALD   = "#3DD68C"
C_RED       = "#FF4B4B"
C_MUTED     = "#8B949E"
C_TEXT      = "#E6EDF3"
C_BLUE      = "#58A6FF"

st.markdown(f"""
<style>
  /* ── Reset & base ── */
  html, body, [data-testid="stAppViewContainer"] {{
      background-color: {C_BG};
      color: {C_TEXT};
      font-family: 'Inter', 'Segoe UI', sans-serif;
  }}
  [data-testid="stSidebar"] {{
      background-color: {C_SURFACE};
      border-right: 1px solid {C_BORDER};
  }}
  /* ── Tab strip ── */
  .stTabs [data-baseweb="tab-list"] {{
      gap: 4px;
      background: {C_SURFACE};
      border-radius: 10px;
      padding: 4px;
      border: 1px solid {C_BORDER};
  }}
  .stTabs [data-baseweb="tab"] {{
      background: transparent;
      border: none;
      border-radius: 8px;
      padding: 9px 22px;
      font-weight: 600;
      font-size: 13px;
      color: {C_MUTED};
      transition: all 0.2s;
  }}
  .stTabs [data-baseweb="tab"]:hover {{ color: {C_CYAN}; }}
  .stTabs [data-baseweb="tab"][aria-selected="true"] {{
      background: {C_CYAN}22;
      color: {C_CYAN};
      border-bottom: 2px solid {C_CYAN};
  }}
  /* ── Cards ── */
  .kpi-card {{
      background: {C_SURFACE};
      border: 1px solid {C_BORDER};
      border-radius: 12px;
      padding: 20px 22px 16px;
      position: relative;
      overflow: hidden;
  }}
  .kpi-card::before {{
      content: "";
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 3px;
      background: var(--accent);
  }}
  .kpi-label  {{ font-size: 11px; font-weight: 700; letter-spacing: 1.2px;
                  text-transform: uppercase; color: {C_MUTED}; margin-bottom: 8px; }}
  .kpi-value  {{ font-size: 30px; font-weight: 700; color: {C_TEXT}; line-height: 1; }}
  .kpi-sub    {{ font-size: 12px; color: {C_MUTED}; margin-top: 6px; }}
  .kpi-dot    {{ display: inline-block; width: 7px; height: 7px;
                  border-radius: 50%; margin-right: 5px;
                  animation: pulse 2s infinite; }}
  @keyframes pulse {{ 0%,100%{{opacity:1}} 50%{{opacity:.4}} }}
  /* ── Section headers ── */
  .section-header {{
      font-size: 13px; font-weight: 700; letter-spacing: 1px;
      text-transform: uppercase; color: {C_MUTED};
      border-bottom: 1px solid {C_BORDER}; padding-bottom: 8px;
      margin: 24px 0 16px;
  }}
  /* ── Status chips ── */
  .chip {{
      display: inline-block; border-radius: 20px;
      padding: 3px 12px; font-size: 11px; font-weight: 700;
      letter-spacing: .5px; margin-bottom: 6px;
  }}
  .chip-ok  {{ background: {C_EMERALD}22; color: {C_EMERALD}; border: 1px solid {C_EMERALD}55; }}
  .chip-err {{ background: {C_RED}22;     color: {C_RED};     border: 1px solid {C_RED}55; }}
  /* ── Dataframe ── */
  [data-testid="stDataFrame"] {{ border: 1px solid {C_BORDER}; border-radius: 8px; }}
  /* ── Plotly background override ── */
  .js-plotly-plot .plotly {{ background: transparent !important; }}
</style>
""", unsafe_allow_html=True)


# ── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="padding:16px 0 20px;">
      <div style="font-size:20px; font-weight:800; color:{C_TEXT}; letter-spacing:-0.5px;">🏭 Plant Ops</div>
      <div style="font-size:11px; color:{C_MUTED}; margin-top:2px;">Intelligence Hub · June 2026</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"<div style='font-size:11px;font-weight:700;letter-spacing:1px;color:{C_MUTED};margin-bottom:8px;'>DATA SOURCES</div>", unsafe_allow_html=True)
    user_name    = st.text_input("Windows Username", value="YourName",    label_visibility="visible")
    company_name = st.text_input("OneDrive Company", value="CompanyName", label_visibility="visible")

    ONEDRIVE = f"C:/Users/{user_name}/OneDrive - {company_name}/Plant_Reports/"
    LOCAL    = "./"

    def resolve(filename, glob_mode=False):
        if glob_mode:
            hits = glob.glob(os.path.join(ONEDRIVE, filename)) or \
                   glob.glob(os.path.join(LOCAL,    filename))
            return hits, "OneDrive" if glob.glob(os.path.join(ONEDRIVE, filename)) else ("Local" if hits else "Missing")
        for base in (ONEDRIVE, LOCAL):
            p = os.path.join(base, filename)
            if os.path.exists(p):
                return p, ("OneDrive" if base == ONEDRIVE else "Local")
        return os.path.join(LOCAL, filename), "Missing"

    csv_files, csv_src  = resolve("DataLog_*.csv", glob_mode=True)
    excel_path, xls_src = resolve("Power consumption freon.xlsx")
    excel_ok = os.path.exists(excel_path)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:11px;font-weight:700;letter-spacing:1px;color:{C_MUTED};margin-bottom:8px;'>SYSTEM STATUS</div>", unsafe_allow_html=True)

    def status_chip(label, ok, src=""):
        cls = "chip-ok" if ok else "chip-err"
        icon = "●" if ok else "○"
        detail = f" · {src}" if ok else ""
        return f'<span class="chip {cls}">{icon} {label}{detail}</span>'

    st.markdown(
        status_chip("Thermal CSVs", bool(csv_files), csv_src) + "<br>" +
        status_chip("Freon Excel",  excel_ok,        xls_src),
        unsafe_allow_html=True
    )

    st.markdown(f"""
    <div style="position:absolute;bottom:20px;left:20px;right:20px;
         font-size:10px;color:{C_MUTED};border-top:1px solid {C_BORDER};padding-top:12px;">
      Auto-refreshes on file change · Aayush Automation System
    </div>""", unsafe_allow_html=True)


# ── DATA LOADERS ─────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_thermal(files):
    if not files:
        return None
    dfs = []
    for f in files:
        df = pd.read_csv(f)
        df.columns = df.columns.str.strip()
        want = ['Time', 'Dough Cooler2 Temp', 'Dough Cooler1 Temp', 'Perishable Cooler Temp']
        if not all(c in df.columns for c in want):
            continue
        df = df[want].copy()
        for c in want[1:]:
            df[c] = df[c].astype(str).str.strip()
            df[c] = df[c].replace({'NOP': None, '': None})
            df[c] = pd.to_numeric(df[c], errors='coerce')
        df['Time'] = pd.to_datetime(df['Time'], dayfirst=True, errors='coerce')
        dfs.append(df)
    if not dfs:
        return None
    out = pd.concat(dfs).drop_duplicates('Time').sort_values('Time').reset_index(drop=True)
    # Forward-fill then back-fill NOP gaps
    for c in want[1:]:
        out[c] = out[c].ffill().bfill()
    return out


def _parse_date(val):
    s = str(val).strip()
    if not s or s in ('nan','Date','Total','date','total'):
        return pd.NaT
    s = s.split(' ')[0]
    for fmt in ('%d/%m/%Y','%d-%m-%Y','%Y-%m-%d','%m/%d/%Y'):
        try:
            return pd.to_datetime(s, format=fmt)
        except Exception:
            pass
    return pd.to_datetime(s, errors='coerce')


@st.cache_data(show_spinner=False)
def load_sheet(path, sheet, header_row):
    if not os.path.exists(path):
        return None
    try:
        df = pd.read_excel(path, sheet_name=sheet, header=header_row, engine='openpyxl')
        df = df.dropna(axis=1, how='all').dropna(how='all')
        first = df.columns[0]
        df = df[~df[first].astype(str).str.strip().str.lower().isin(['total',''])]
        return df
    except Exception:
        return None


# ── PLOTLY THEME DEFAULTS ─────────────────────────────────────────────────────
LAYOUT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, Segoe UI, sans-serif", color=C_TEXT, size=12),
    margin=dict(l=10, r=10, t=36, b=10),
    xaxis=dict(gridcolor=C_BORDER, zerolinecolor=C_BORDER, tickfont=dict(size=11)),
    yaxis=dict(gridcolor=C_BORDER, zerolinecolor=C_BORDER, tickfont=dict(size=11)),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    hovermode="x unified",
)

def fig_base(**extra):
    d = dict(**LAYOUT_BASE)
    d.update(extra)
    return go.Layout(**d)


# ── HEADER ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:{C_SURFACE};border:1px solid {C_BORDER};border-radius:14px;
     padding:22px 28px;margin-bottom:24px;border-left:4px solid {C_CYAN};">
  <div style="font-size:26px;font-weight:800;color:{C_TEXT};letter-spacing:-0.5px;">
    🏭 Plant Operations Intelligence Hub
  </div>
  <div style="font-size:13px;color:{C_MUTED};margin-top:4px;">
    Real-Time Thermal Telemetry · Freon Energy Audit · Compressor Analytics · June 2026
  </div>
</div>
""", unsafe_allow_html=True)


# ── TABS ─────────────────────────────────────────────────────────────────────
tab_thermal, tab_power, tab_runtime, tab_compressor = st.tabs([
    "🌡️  Thermal Monitor",
    "⚡  Energy & Savings",
    "⚙️  Duty Cycles",
    "📉  Compressor Analytics",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — THERMAL MONITORING
# ══════════════════════════════════════════════════════════════════════════════
with tab_thermal:
    tdf = load_thermal(csv_files)

    if tdf is not None and not tdf.empty:
        latest = tdf.iloc[-1]

        # ── KPI row ──
        k1, k2, k3 = st.columns(3)
        for col_widget, label, sensor, accent, icon in [
            (k1, "Dough Cooler 1",    "Dough Cooler1 Temp",    C_BLUE,   "❄️"),
            (k2, "Dough Cooler 2",    "Dough Cooler2 Temp",    C_CYAN,   "❄️"),
            (k3, "Perishable Storage","Perishable Cooler Temp", C_AMBER,  "🥩"),
        ]:
            val = latest[sensor]
            with col_widget:
                st.markdown(f"""
                <div class="kpi-card" style="--accent:{accent};">
                  <div class="kpi-label">{icon} {label}</div>
                  <div class="kpi-value">{val:.2f} °C</div>
                  <div class="kpi-sub">
                    <span class="kpi-dot" style="background:{C_EMERALD};"></span>Live
                    &nbsp;·&nbsp; avg {tdf[sensor].mean():.2f} °C
                    &nbsp;·&nbsp; min {tdf[sensor].min():.2f} / max {tdf[sensor].max():.2f}
                  </div>
                </div>""", unsafe_allow_html=True)

        # ── Continuous trend ──
        st.markdown('<div class="section-header">Continuous Temperature Trends</div>', unsafe_allow_html=True)

        fig = go.Figure(layout=fig_base(title=""))
        series = [
            ("Dough Cooler1 Temp",    "Dough Cooler 1", C_BLUE,  True),
            ("Dough Cooler2 Temp",    "Dough Cooler 2", C_CYAN,  True),
            ("Perishable Cooler Temp","Perishable",      C_AMBER, False),
        ]
        for col, name, color, visible in series:
            fig.add_trace(go.Scatter(
                x=tdf['Time'], y=tdf[col], name=name,
                line=dict(color=color, width=1.8),
                visible=True,
                hovertemplate=f"<b>{name}</b>: %{{y:.3f}} °C<extra></extra>",
            ))
        fig.update_layout(fig_base(height=340, yaxis_title="°C"))
        st.plotly_chart(fig, use_container_width=True)

        # ── Daily stats table ──
        st.markdown('<div class="section-header">Daily Statistics</div>', unsafe_allow_html=True)
        tdf['Date'] = tdf['Time'].dt.date
        daily = tdf.groupby('Date').agg(
            DC1_min=('Dough Cooler1 Temp','min'),  DC1_avg=('Dough Cooler1 Temp','mean'), DC1_max=('Dough Cooler1 Temp','max'),
            DC2_min=('Dough Cooler2 Temp','min'),  DC2_avg=('Dough Cooler2 Temp','mean'), DC2_max=('Dough Cooler2 Temp','max'),
            PC_min=('Perishable Cooler Temp','min'),PC_avg=('Perishable Cooler Temp','mean'),PC_max=('Perishable Cooler Temp','max'),
        ).round(3).reset_index()
        daily.columns = ['Date',
            'DC1 Min','DC1 Avg','DC1 Max',
            'DC2 Min','DC2 Avg','DC2 Max',
            'Perishable Min','Perishable Avg','Perishable Max']
        st.dataframe(daily, use_container_width=True, hide_index=True)

        # ── Daily average bar chart ──
        st.markdown('<div class="section-header">Daily Average Comparison</div>', unsafe_allow_html=True)
        fig2 = go.Figure(layout=fig_base(height=280))
        for col_key, name, color in [
            ('DC1 Avg','Dough Cooler 1', C_BLUE),
            ('DC2 Avg','Dough Cooler 2', C_CYAN),
            ('Perishable Avg','Perishable', C_AMBER),
        ]:
            fig2.add_trace(go.Bar(
                x=daily['Date'].astype(str), y=daily[col_key],
                name=name, marker_color=color,
                hovertemplate=f"<b>{name}</b>: %{{y:.3f}} °C<extra></extra>",
            ))
        fig2.update_layout(barmode='group', yaxis_title="Avg °C")
        st.plotly_chart(fig2, use_container_width=True)

    else:
        st.markdown(f"""
        <div style="background:{C_SURFACE};border:1px dashed {C_BORDER};border-radius:12px;
             padding:40px;text-align:center;color:{C_MUTED};">
          <div style="font-size:32px;margin-bottom:12px;">📡</div>
          <div style="font-weight:600;">No telemetry logs found</div>
          <div style="font-size:12px;margin-top:6px;">Add <code>DataLog_*.csv</code> files to your folder</div>
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — ENERGY & SAVINGS
# ══════════════════════════════════════════════════════════════════════════════
with tab_power:
    praw = load_sheet(excel_path, 'Sheet1', 1)

    if praw is not None and not praw.empty:
        pdf = praw.copy()
        pdf['Date'] = pdf['Date'].apply(_parse_date)
        pdf = pdf.dropna(subset=['Date']).sort_values('Date')

        for c in ['Dunkin Blast','CLC Blast','Savings']:
            if c in pdf.columns:
                pdf[c] = pd.to_numeric(pdf[c], errors='coerce').fillna(0)

        pdf = pdf[pdf.get('Dunkin Blast', pd.Series([0])) < 500_000]

        dsum = pdf.get('Dunkin Blast', pd.Series([0])).sum()
        csum = pdf.get('CLC Blast',    pd.Series([0])).sum()
        ssum = pdf.get('Savings',      pd.Series([0])).sum()

        # ── KPIs ──
        m1, m2, m3 = st.columns(3)
        for w, lbl, val, accent, unit in [
            (m1, "Dunkin Blast Total",   dsum, C_BLUE,   "kWh"),
            (m2, "CLC Blast Total",      csum, C_CYAN,   "kWh"),
            (m3, "Net Savings",          ssum, C_EMERALD,"INR"),
        ]:
            with w:
                st.markdown(f"""
                <div class="kpi-card" style="--accent:{accent};">
                  <div class="kpi-label">{lbl}</div>
                  <div class="kpi-value">{val:,.1f}</div>
                  <div class="kpi-sub">{unit} accumulated</div>
                </div>""", unsafe_allow_html=True)

        # ── Area chart ──
        st.markdown('<div class="section-header">Daily Energy Draw — Dunkin vs CLC</div>', unsafe_allow_html=True)
        fig3 = go.Figure(layout=fig_base(height=300))
        for col, name, color in [('Dunkin Blast','Dunkin Blast',C_BLUE),('CLC Blast','CLC Blast',C_CYAN)]:
            if col in pdf.columns:
                fig3.add_trace(go.Scatter(
                    x=pdf['Date'], y=pdf[col], name=name,
                    fill='tozeroy', line=dict(color=color, width=2),
                    fillcolor=color.replace('FF','33') if '#' in color else color,
                    hovertemplate=f"<b>{name}</b>: %{{y:,.1f}} kWh<extra></extra>",
                ))
        fig3.update_layout(yaxis_title="kWh")
        st.plotly_chart(fig3, use_container_width=True)

        # ── Savings bar ──
        st.markdown('<div class="section-header">Daily Savings (INR)</div>', unsafe_allow_html=True)
        if 'Savings' in pdf.columns:
            fig4 = go.Figure(layout=fig_base(height=240))
            fig4.add_trace(go.Bar(
                x=pdf['Date'], y=pdf['Savings'],
                marker_color=[C_EMERALD if v >= 0 else C_RED for v in pdf['Savings']],
                hovertemplate="<b>Savings</b>: ₹%{y:,.2f}<extra></extra>",
            ))
            fig4.update_layout(yaxis_title="INR", showlegend=False)
            st.plotly_chart(fig4, use_container_width=True)

        with st.expander("View Raw Energy Ledger"):
            st.dataframe(pdf, use_container_width=True, hide_index=True)
    else:
        st.info("Add 'Power consumption freon.xlsx' (Sheet1) to your folder.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — DUTY CYCLES
# ══════════════════════════════════════════════════════════════════════════════
with tab_runtime:
    rraw = load_sheet(excel_path, 'Sheet2', 2)

    if rraw is not None and not rraw.empty:
        rdf = rraw.copy()
        first_col = rdf.columns[0]
        rdf = rdf[~rdf[first_col].astype(str).str.strip().str.lower().isin(['date','from','total',''])]
        rdf[first_col] = rdf[first_col].apply(_parse_date)
        rdf = rdf.dropna(subset=[first_col]).sort_values(first_col)

        kwh_cols = [c for c in rdf.columns if 'KWH' in str(c).upper()]
        for c in kwh_cols:
            rdf[c] = pd.to_numeric(rdf[c], errors='coerce').fillna(0)

        if kwh_cols:
            # ── KPI summary row ──
            kcols = st.columns(min(len(kwh_cols), 4))
            for i, kc in enumerate(kwh_cols[:4]):
                with kcols[i]:
                    st.markdown(f"""
                    <div class="kpi-card" style="--accent:{C_AMBER};">
                      <div class="kpi-label">{kc}</div>
                      <div class="kpi-value">{rdf[kc].sum():,.1f}</div>
                      <div class="kpi-sub">kWh total</div>
                    </div>""", unsafe_allow_html=True)

            st.markdown('<div class="section-header">Duty Cycle Draw by Unit</div>', unsafe_allow_html=True)
            colors = [C_AMBER, C_CYAN, C_BLUE, C_EMERALD]
            fig5 = go.Figure(layout=fig_base(height=320))
            for i, kc in enumerate(kwh_cols):
                fig5.add_trace(go.Bar(
                    x=rdf[first_col].astype(str), y=rdf[kc],
                    name=kc, marker_color=colors[i % len(colors)],
                    hovertemplate=f"<b>{kc}</b>: %{{y:,.1f}} kWh<extra></extra>",
                ))
            fig5.update_layout(barmode='group', yaxis_title="kWh")
            st.plotly_chart(fig5, use_container_width=True)

            # ── Stacked area — cumulative load ──
            st.markdown('<div class="section-header">Cumulative Energy Load</div>', unsafe_allow_html=True)
            fig6 = go.Figure(layout=fig_base(height=260))
            for i, kc in enumerate(kwh_cols):
                fig6.add_trace(go.Scatter(
                    x=rdf[first_col].astype(str), y=rdf[kc].cumsum(),
                    name=kc, stackgroup='one',
                    line=dict(color=colors[i % len(colors)], width=1.5),
                    hovertemplate=f"<b>{kc} cumulative</b>: %{{y:,.1f}} kWh<extra></extra>",
                ))
            fig6.update_layout(yaxis_title="Cumulative kWh")
            st.plotly_chart(fig6, use_container_width=True)

        with st.expander("View Duty Cycle Log"):
            st.dataframe(rdf, use_container_width=True, hide_index=True)
    else:
        st.info("Add 'Power consumption freon.xlsx' (Sheet2) to your folder.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — COMPRESSOR ANALYTICS  (fully new graphical representation)
# ══════════════════════════════════════════════════════════════════════════════
with tab_compressor:
    craw = load_sheet(excel_path, 'Sheet3', 3)

    if craw is not None and not craw.empty:
        cdf = craw.copy()
        date_col = cdf.columns[0]
        cdf = cdf[~cdf[date_col].astype(str).str.strip().str.lower().isin(['date','total',''])]
        cdf[date_col] = cdf[date_col].apply(_parse_date)
        cdf = cdf.dropna(subset=[date_col]).sort_values(date_col).reset_index(drop=True)

        # Numeric coerce all non-date columns
        for c in cdf.columns[1:]:
            cdf[c] = pd.to_numeric(cdf[c], errors='coerce').fillna(0)

        sav_col = next((c for c in cdf.columns if 'saving' in str(c).lower() and 'hr' in str(c).lower()), None)
        run_cols = [c for c in cdf.columns if any(k in str(c).lower() for k in ['run','hour','compressor','on time'])]

        # ── KPI strip ──
        kpis = []
        if sav_col:
            kpis.append((sav_col, cdf[sav_col].sum(), "hrs saved", C_EMERALD))
        for rc in run_cols[:3]:
            kpis.append((rc, cdf[rc].sum(), "hrs run", C_CYAN))

        if kpis:
            ks = st.columns(len(kpis))
            for wi, (lbl, val, unit, accent) in zip(ks, kpis):
                with wi:
                    st.markdown(f"""
                    <div class="kpi-card" style="--accent:{accent};">
                      <div class="kpi-label">{lbl}</div>
                      <div class="kpi-value">{val:,.1f}</div>
                      <div class="kpi-sub">{unit} total</div>
                    </div>""", unsafe_allow_html=True)

        # ── CHART 1: Savings line + run hours bar (dual axis) ──
        if sav_col and run_cols:
            st.markdown('<div class="section-header">Savings vs Runtime — Dual Axis View</div>', unsafe_allow_html=True)
            fig7 = make_subplots(specs=[[{"secondary_y": True}]])
            fig7.add_trace(go.Bar(
                x=cdf[date_col].astype(str), y=cdf[run_cols[0]],
                name=run_cols[0], marker_color=C_CYAN + "99",
                hovertemplate=f"<b>{run_cols[0]}</b>: %{{y:.2f}} hrs<extra></extra>",
            ), secondary_y=False)
            fig7.add_trace(go.Scatter(
                x=cdf[date_col].astype(str), y=cdf[sav_col],
                name="Savings (hrs)", line=dict(color=C_EMERALD, width=2.5),
                mode='lines+markers', marker=dict(size=6),
                hovertemplate="<b>Savings</b>: %{y:.2f} hrs<extra></extra>",
            ), secondary_y=True)
            fig7.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color=C_TEXT, size=11), height=320,
                margin=dict(l=10,r=10,t=36,b=10),
                legend=dict(bgcolor="rgba(0,0,0,0)"),
                hovermode="x unified",
                xaxis=dict(gridcolor=C_BORDER, tickfont=dict(size=10)),
                yaxis=dict(gridcolor=C_BORDER, title="Run Hours"),
                yaxis2=dict(gridcolor="rgba(0,0,0,0)", title="Saved Hours", overlaying='y', side='right'),
            )
            st.plotly_chart(fig7, use_container_width=True)

        # ── CHART 2: Cumulative savings trajectory ──
        if sav_col:
            st.markdown('<div class="section-header">Cumulative Compressor Savings Trajectory</div>', unsafe_allow_html=True)
            cdf['_cum_sav'] = cdf[sav_col].cumsum()
            fig8 = go.Figure(layout=fig_base(height=260))
            fig8.add_trace(go.Scatter(
                x=cdf[date_col].astype(str), y=cdf['_cum_sav'],
                fill='tozeroy', fillcolor=C_EMERALD + "22",
                line=dict(color=C_EMERALD, width=2.5),
                mode='lines+markers', marker=dict(size=7, color=C_EMERALD),
                name="Cumulative Savings",
                hovertemplate="<b>Total Saved</b>: %{y:.2f} hrs<extra></extra>",
            ))
            fig8.update_layout(yaxis_title="Cumulative hrs saved")
            st.plotly_chart(fig8, use_container_width=True)

        # ── CHART 3: Efficiency ratio (savings / runtime) ──
        if sav_col and run_cols:
            st.markdown('<div class="section-header">Daily Efficiency Ratio (Savings ÷ Runtime)</div>', unsafe_allow_html=True)
            run_sum = cdf[run_cols].sum(axis=1).replace(0, pd.NA)
            cdf['_eff'] = (cdf[sav_col] / run_sum * 100).fillna(0).round(2)

            fig9 = go.Figure(layout=fig_base(height=240))
            fig9.add_trace(go.Bar(
                x=cdf[date_col].astype(str), y=cdf['_eff'],
                marker_color=[C_EMERALD if v >= cdf['_eff'].mean() else C_AMBER for v in cdf['_eff']],
                name="Efficiency %",
                hovertemplate="<b>Efficiency</b>: %{y:.2f}%<extra></extra>",
            ))
            fig9.add_hline(
                y=cdf['_eff'].mean(), line_dash="dot",
                line_color=C_RED, annotation_text=f"Avg {cdf['_eff'].mean():.1f}%",
                annotation_font_color=C_RED,
            )
            fig9.update_layout(yaxis_title="Efficiency %", showlegend=False)
            st.plotly_chart(fig9, use_container_width=True)

        # ── CHART 4: Multi-compressor runtime heatmap (if multiple run cols) ──
        if len(run_cols) >= 2:
            st.markdown('<div class="section-header">Compressor Runtime Heatmap</div>', unsafe_allow_html=True)
            heat_data = cdf[run_cols].T
            heat_data.columns = cdf[date_col].astype(str)
            fig10 = go.Figure(go.Heatmap(
                z=heat_data.values,
                x=heat_data.columns.tolist(),
                y=run_cols,
                colorscale=[[0,'#0D1117'],[0.5, C_CYAN+'88'],[1, C_CYAN]],
                hovertemplate="<b>%{y}</b> on %{x}: %{z:.2f} hrs<extra></extra>",
                showscale=True,
            ))
            fig10.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color=C_TEXT, size=11), height=240,
                margin=dict(l=10,r=10,t=10,b=10),
                xaxis=dict(tickfont=dict(size=9)),
            )
            st.plotly_chart(fig10, use_container_width=True)

        with st.expander("View Raw Compressor Log"):
            st.dataframe(cdf.drop(columns=['_cum_sav','_eff'], errors='ignore'),
                         use_container_width=True, hide_index=True)
    else:
        st.info("Add 'Power consumption freon.xlsx' (Sheet3) to your folder.")
