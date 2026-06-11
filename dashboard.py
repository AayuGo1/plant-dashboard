import streamlit as st
import pandas as pd
import glob
import os
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="JFL SCADA Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #0F1923; }
    
    /* Hide default header */
    header[data-testid="stHeader"] { background: transparent; }
    
    /* Metric cards */
    [data-testid="metric-container"] {
        background: #1A2C40;
        border: 1px solid #1E4D7B;
        border-radius: 12px;
        padding: 16px !important;
        border-left: 4px solid #00A6E6;
    }
    [data-testid="metric-container"] label {
        color: #7AADCC !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-size: 28px !important;
        font-weight: 800 !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricDelta"] {
        font-size: 12px !important;
    }
    
    /* Section headers */
    .section-header {
        background: linear-gradient(90deg, #1A4A8A 0%, #0F1923 100%);
        padding: 10px 18px;
        border-radius: 8px;
        border-left: 4px solid #00A6E6;
        margin-bottom: 16px;
        color: white;
        font-weight: 700;
        font-size: 15px;
        letter-spacing: 0.3px;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background: #1A2C40;
        border-radius: 10px;
        padding: 4px;
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #7AADCC;
        font-weight: 600;
        border-radius: 8px;
        padding: 8px 20px;
    }
    .stTabs [aria-selected="true"] {
        background: #1A4A8A !important;
        color: white !important;
    }
    
    /* Dataframe */
    [data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #1A2C40;
        border-right: 1px solid #1E4D7B;
    }
    
    /* Status badge */
    .status-live {
        display: inline-block;
        background: #1A4A2A;
        border: 1px solid #2ECC71;
        color: #2ECC71;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
    }
    .status-nodata {
        display: inline-block;
        background: #4A1A1A;
        border: 1px solid #E74C3C;
        color: #E74C3C;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
    }
    
    /* Warning temp */
    .temp-warning { color: #E74C3C; font-weight: 700; }
    
    /* General text */
    p, span, div { color: #C8D8E8; }
    h1, h2, h3 { color: #FFFFFF !important; }
</style>
""", unsafe_allow_html=True)

# ── Data loading functions ────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def load_temperature_data():
    """Load all CSV/Excel DataLog files"""
    files_csv  = glob.glob("*.csv") + glob.glob("daily_logs/*.csv")
    files_xlsx = glob.glob("DataLog*.xlsx") + glob.glob("daily_logs/DataLog*.xlsx")
    
    all_data = []
    
    for f in files_csv + files_xlsx:
        try:
            df = pd.read_csv(f) if f.endswith(".csv") else pd.read_excel(f)
            df.columns = df.columns.str.strip()
            
            # Map possible column name variants
            col_map = {}
            for c in df.columns:
                if "Cooler1" in c or "Cooler 1" in c:  col_map[c] = "DC1_Temp"
                elif "Cooler2" in c or "Cooler 2" in c: col_map[c] = "DC2_Temp"
                elif "Perishable" in c:                   col_map[c] = "PC_Temp"
                elif c.lower() == "time":                 col_map[c] = "Time"
            df = df.rename(columns=col_map)
            
            needed = [c for c in ["Time","DC1_Temp","DC2_Temp","PC_Temp"] if c in df.columns]
            if "Time" in needed and len(needed) > 1:
                df = df[needed].copy()
                for col in ["DC1_Temp","DC2_Temp","PC_Temp"]:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors="coerce")
                        df[col] = df[col].where(df[col].abs() < 50)  # filter -50 sentinel
                df["Time"] = pd.to_datetime(df["Time"], dayfirst=True, errors="coerce")
                df = df.dropna(subset=["Time"])
                df["Date"] = df["Time"].dt.date
                all_data.append(df)
        except Exception:
            pass
    
    if not all_data:
        return None
    
    combined = pd.concat(all_data, ignore_index=True)
    combined = combined.drop_duplicates(subset=["Time"]).sort_values("Time")
    return combined


@st.cache_data(ttl=60)
def load_power_data():
    """Load Power_consumption_freon.xlsx"""
    candidates = glob.glob("Power_consumption*.xlsx") + glob.glob("*.xlsx")
    for f in candidates:
        if "DataLog" in f:
            continue
        try:
            # Sheet1 = Power
            raw = pd.read_excel(f, sheet_name=0, header=None)
            rows = raw.iloc[1:].copy()
            rows.columns = range(len(rows.columns))
            power = rows[[0,5,6,11,12]].copy()
            power.columns = ["Date","Dunkin_Total","Dunkin_Savings","CLC_Total","CLC_Savings"]
            power["Date"] = pd.to_datetime(power["Date"], errors="coerce").dt.date
            power = power.dropna(subset=["Date"])
            for c in ["Dunkin_Total","Dunkin_Savings","CLC_Total","CLC_Savings"]:
                power[c] = pd.to_numeric(power[c], errors="coerce")
            
            # Sheet2 = Running hours
            raw2 = pd.read_excel(f, sheet_name=1, header=None)
            rows2 = raw2.iloc[3:].copy()
            rows2.columns = range(len(rows2.columns))
            rh = rows2[[0,2,3,4,6,7,8,10,11]].copy()
            rh.columns = ["CLC_From","CLC_RunHrs","CLC_KWH","BMC_From","BMC_RunHrs","BMC_KWH","Dunkin_From","Dunkin_RunHrs","Dunkin_KWH"]
            rh["Date"] = pd.to_datetime(rh["CLC_From"], errors="coerce").dt.date
            rh = rh.dropna(subset=["Date"])
            rh = rh[["Date","CLC_RunHrs","CLC_KWH","BMC_RunHrs","BMC_KWH","Dunkin_RunHrs","Dunkin_KWH"]]
            for c in ["CLC_KWH","BMC_KWH","Dunkin_KWH"]:
                rh[c] = pd.to_numeric(rh[c], errors="coerce")
            
            return power, rh
        except Exception:
            pass
    return None, None


def daily_summary(df):
    return df.groupby("Date").agg(
        DC1_Min=("DC1_Temp","min"), DC1_Max=("DC1_Temp","max"), DC1_Avg=("DC1_Temp","mean"),
        DC2_Min=("DC2_Temp","min"), DC2_Max=("DC2_Temp","max"), DC2_Avg=("DC2_Temp","mean"),
        PC_Min=("PC_Temp","min"),   PC_Max=("PC_Temp","max"),   PC_Avg=("PC_Temp","mean"),
    ).round(2).reset_index()


# ── Header ────────────────────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([3,1])
with col_h1:
    st.markdown("""
    <div style="padding: 8px 0 4px;">
        <div style="font-size:11px; color:#00A6E6; font-weight:700; letter-spacing:2px; text-transform:uppercase;">
            Jubilant FoodWorks Limited · Supply Chain Centre
        </div>
        <div style="font-size:32px; font-weight:900; color:#FFFFFF; line-height:1.1; margin-top:4px;">
            SCADA Monitoring Dashboard
        </div>
        <div style="font-size:12px; color:#7AADCC; margin-top:4px;">
            Maintenance & Operations · Greater Noida
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_h2:
    st.markdown(f"""
    <div style="text-align:right; padding-top:16px;">
        <div style="font-size:11px; color:#7AADCC;">Last refreshed</div>
        <div style="font-size:15px; font-weight:700; color:#fff;">{datetime.now().strftime('%d %b %Y, %H:%M')}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='border:1px solid #1E4D7B; margin:8px 0 20px;'>", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
temp_df  = load_temperature_data()
power_df, rh_df = load_power_data()

has_temp  = temp_df  is not None and len(temp_df)  > 0
has_power = power_df is not None and len(power_df) > 0
has_rh    = rh_df    is not None and len(rh_df)    > 0

# ── Sidebar — Date filter ─────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📅 Filter by Date")
    all_dates = []
    if has_temp:
        all_dates += list(temp_df["Date"].unique())
    if has_power:
        all_dates += list(power_df["Date"].unique())
    all_dates = sorted(set(all_dates))
    
    date_options = ["All Days"] + [str(d) for d in all_dates]
    selected = st.selectbox("Select date", date_options)
    
    st.markdown("---")
    st.markdown("### 📂 Files Found")
    csv_files  = glob.glob("*.csv")  + glob.glob("daily_logs/*.csv")
    xlsx_files = glob.glob("*.xlsx") + glob.glob("daily_logs/*.xlsx")
    st.markdown(f"🌡️ **{len(csv_files + xlsx_files)} DataLog** files")
    pwr_files = glob.glob("Power_consumption*.xlsx")
    st.markdown(f"⚡ **{len(pwr_files)} Power** file(s)")
    
    st.markdown("---")
    st.markdown("### 🔄 Refresh")
    if st.button("Reload Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Apply date filter
def filter_date(df, col="Date"):
    if selected == "All Days" or df is None:
        return df
    return df[df[col].astype(str) == selected]

temp_filtered  = filter_date(temp_df)
power_filtered = filter_date(power_df)
rh_filtered    = filter_date(rh_df)
daily          = daily_summary(temp_filtered) if has_temp and temp_filtered is not None else None

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊  Overview",
    "🌡️  Temperature",
    "⚡  Power Consumption",
    "🕐  Running Hours"
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    if not has_temp and not has_power:
        st.error("⚠️ No data files found. Place DataLog CSV/Excel files in the same folder as this script.")
        st.info("Expected files: `DataLog_DD-MM-YYYY.csv` and `Power_consumption_freon.xlsx`")
    else:
        # ── KPI Row: Temperature ──────────────────────────────────────────────
        st.markdown('<div class="section-header">🌡️ Temperature — Current Status</div>', unsafe_allow_html=True)
        
        if has_temp and temp_filtered is not None:
            latest = temp_df.iloc[-1]
            
            c1, c2, c3, c4 = st.columns(4)
            dc1_val = latest.get("DC1_Temp", None)
            dc2_val = latest.get("DC2_Temp", None)
            pc_val  = latest.get("PC_Temp",  None)
            
            def temp_delta(v):
                if v is None or pd.isna(v): return None
                return "✓ Normal" if 0 <= v <= 8 else "⚠️ Check!"
            
            with c1:
                st.metric("Dough Cooler 1", f"{dc1_val:.2f}°C" if dc1_val is not None else "—", delta=temp_delta(dc1_val))
            with c2:
                st.metric("Dough Cooler 2", f"{dc2_val:.2f}°C" if dc2_val is not None else "—", delta=temp_delta(dc2_val))
            with c3:
                st.metric("Perishable Cooler", f"{pc_val:.2f}°C" if pc_val is not None else "—", delta=temp_delta(pc_val))
            with c4:
                st.metric("Total Readings", f"{len(temp_df):,}", delta=f"{len(temp_df['Date'].unique())} days")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # ── KPI Row: Power ────────────────────────────────────────────────────
        if has_power:
            st.markdown('<div class="section-header">⚡ Power — Month Summary</div>', unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Dunkin Total", f"{power_df['Dunkin_Total'].sum():,.0f} KWH")
            with c2:
                sv = power_df['Dunkin_Savings'].sum()
                st.metric("Dunkin Savings", f"{sv:,.1f}", delta="Under target" if sv >= 0 else "Over target")
            with c3:
                st.metric("CLC Total", f"{power_df['CLC_Total'].sum():,.0f} KWH")
            with c4:
                sv2 = power_df['CLC_Savings'].sum()
                st.metric("CLC Savings", f"{sv2:,.1f}", delta="Under target" if sv2 >= 0 else "Over target")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # ── Overview Chart: Avg Temp ──────────────────────────────────────────
        if has_temp and daily is not None and len(daily) > 0:
            st.markdown('<div class="section-header">📈 Daily Average Temperature Trend</div>', unsafe_allow_html=True)
            
            fig = go.Figure()
            if "DC1_Avg" in daily.columns:
                fig.add_trace(go.Scatter(x=daily["Date"].astype(str), y=daily["DC1_Avg"],
                    name="Dough Cooler 1", line=dict(color="#00A6E6", width=2.5), mode="lines+markers",
                    marker=dict(size=7)))
            if "DC2_Avg" in daily.columns:
                fig.add_trace(go.Scatter(x=daily["Date"].astype(str), y=daily["DC2_Avg"],
                    name="Dough Cooler 2", line=dict(color="#3498DB", width=2.5), mode="lines+markers",
                    marker=dict(size=7)))
            if "PC_Avg" in daily.columns:
                fig.add_trace(go.Scatter(x=daily["Date"].astype(str), y=daily["PC_Avg"],
                    name="Perishable Cooler", line=dict(color="#2ECC71", width=2.5), mode="lines+markers",
                    marker=dict(size=7)))
            
            # Safe range band
            fig.add_hrect(y0=0, y1=8, fillcolor="#2ECC71", opacity=0.07,
                          annotation_text="Safe range (0–8°C)", annotation_position="top left",
                          annotation_font=dict(color="#2ECC71", size=11))
            
            fig.update_layout(
                plot_bgcolor="#1A2C40", paper_bgcolor="#1A2C40",
                font=dict(color="#C8D8E8", family="Segoe UI"),
                legend=dict(bgcolor="#0F1923", bordercolor="#1E4D7B", borderwidth=1),
                xaxis=dict(gridcolor="#1E3A55", title="Date"),
                yaxis=dict(gridcolor="#1E3A55", title="Temperature (°C)"),
                height=320, margin=dict(l=20, r=20, t=20, b=20),
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — TEMPERATURE
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    if not has_temp:
        st.error("No temperature data found.")
    else:
        # Min/Max Chart
        st.markdown('<div class="section-header">🌡️ Daily Min / Max / Average</div>', unsafe_allow_html=True)
        
        if daily is not None and len(daily) > 0:
            fig2 = make_subplots(rows=1, cols=3,
                subplot_titles=("Dough Cooler 1", "Dough Cooler 2", "Perishable Cooler"))
            
            colors = ["#00A6E6", "#3498DB", "#2ECC71"]
            for idx, (prefix, col_name) in enumerate([("DC1","Dough Cooler 1"),("DC2","Dough Cooler 2"),("PC","Perishable Cooler")], 1):
                min_col, max_col, avg_col = f"{prefix}_Min", f"{prefix}_Max", f"{prefix}_Avg"
                if all(c in daily.columns for c in [min_col, max_col, avg_col]):
                    dates = daily["Date"].astype(str)
                    c = colors[idx-1]
                    # Shaded min-max band
                    fig2.add_trace(go.Scatter(x=list(dates)+list(dates[::-1]),
                        y=list(daily[max_col])+list(daily[min_col][::-1]),
                        fill="toself", fillcolor=c, opacity=0.15, line=dict(width=0),
                        showlegend=False, name=f"{col_name} range"), row=1, col=idx)
                    fig2.add_trace(go.Scatter(x=dates, y=daily[avg_col],
                        line=dict(color=c, width=2.5), mode="lines+markers",
                        name=f"{col_name} avg", marker=dict(size=6)), row=1, col=idx)
            
            fig2.update_layout(
                plot_bgcolor="#1A2C40", paper_bgcolor="#1A2C40",
                font=dict(color="#C8D8E8"), height=320,
                margin=dict(l=20, r=20, t=40, b=20),
                showlegend=False
            )
            fig2.update_xaxes(gridcolor="#1E3A55")
            fig2.update_yaxes(gridcolor="#1E3A55", title_text="°C")
            st.plotly_chart(fig2, use_container_width=True)
        
        # Table
        st.markdown('<div class="section-header">📋 Daily Summary Table</div>', unsafe_allow_html=True)
        if daily is not None:
            display_daily = daily.copy()
            display_daily["Date"] = display_daily["Date"].astype(str)
            display_daily.columns = ["Date",
                "DC1 Min","DC1 Max","DC1 Avg",
                "DC2 Min","DC2 Max","DC2 Avg",
                "PC Min","PC Max","PC Avg"]
            st.dataframe(display_daily, use_container_width=True, hide_index=True,
                column_config={c: st.column_config.NumberColumn(c, format="%.2f °C")
                               for c in display_daily.columns if c != "Date"})
        
        # Raw data toggle
        with st.expander("📄 View Raw 5-min Data"):
            if temp_filtered is not None:
                raw_show = temp_filtered[["Time","DC1_Temp","DC2_Temp","PC_Temp"]].copy()
                raw_show["Time"] = raw_show["Time"].astype(str)
                st.dataframe(raw_show, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — POWER CONSUMPTION
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    if not has_power:
        st.error("No power data found. Add `Power_consumption_freon.xlsx` to the folder.")
    else:
        st.markdown('<div class="section-header">⚡ Daily Power Consumption (KWH)</div>', unsafe_allow_html=True)
        
        pf = power_filtered if power_filtered is not None and len(power_filtered) > 0 else power_df
        
        # Bar chart: Total KWH
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(x=pf["Date"].astype(str), y=pf["Dunkin_Total"],
            name="Dunkin Blast", marker_color="#E87820", text=pf["Dunkin_Total"].round(0),
            textposition="outside"))
        fig3.add_trace(go.Bar(x=pf["Date"].astype(str), y=pf["CLC_Total"],
            name="CLC Blast", marker_color="#1A4A8A", text=pf["CLC_Total"].round(0),
            textposition="outside"))
        fig3.update_layout(
            barmode="group", plot_bgcolor="#1A2C40", paper_bgcolor="#1A2C40",
            font=dict(color="#C8D8E8"), height=300,
            xaxis=dict(gridcolor="#1E3A55"), yaxis=dict(gridcolor="#1E3A55", title="KWH"),
            legend=dict(bgcolor="#0F1923"), margin=dict(l=20,r=20,t=20,b=20)
        )
        st.plotly_chart(fig3, use_container_width=True)
        
        # Savings chart
        st.markdown('<div class="section-header">💰 Savings Trend</div>', unsafe_allow_html=True)
        fig4 = go.Figure()
        fig4.add_trace(go.Bar(x=pf["Date"].astype(str), y=pf["Dunkin_Savings"],
            name="Dunkin Savings",
            marker_color=["#2ECC71" if v >= 0 else "#E74C3C" for v in pf["Dunkin_Savings"]]))
        f
