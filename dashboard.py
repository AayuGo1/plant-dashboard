import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Plant Monitoring", layout="wide")
THRESHOLD = 5.0

# --- DATA LOADING ---
@st.cache_data(ttl=60)
def load_data():
    df = pd.read_excel('plant_data.xlsx', engine='openpyxl')
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    return df

# --- LOGGING FUNCTION (New Requirement) ---
def log_alarm(name, temp):
    with open("alarm_log.txt", "a") as f:
        f.write(f"{datetime.now()}: {name} exceeded limit at {temp:.2f}°C\n")

# --- UI & LOGIC ---
st.title("🌡️ Plant Temperature Monitoring")
df = load_data()

if 'alert_sent' not in st.session_state:
    st.session_state.alert_sent = {"Dough Cooler 1": False, "Dough Cooler 2": False}

cols = st.columns(3)
coolers = {"Dough Cooler 1": cols[0], "Dough Cooler 2": cols[1]}

for name, col in coolers.items():
    val = float(df[name].iloc[-1])
    with col:
        st.metric(name, f"{val:.2f}°C")
        
        # Local Alert Logic
        if val > THRESHOLD:
            st.error("⚠️ THRESHOLD EXCEEDED")
            if not st.session_state.alert_sent[name]:
                log_alarm(name, val) # Save to file instead of emailing
                st.session_state.alert_sent[name] = True
        else:
            st.session_state.alert_sent[name] = False

# Visualization
st.subheader("Historical Trends")
df_melted = df.melt(id_vars="Timestamp", var_name="Cooler", value_name="Temperature")
fig = px.line(df_melted, x="Timestamp", y="Temperature", color="Cooler", template="plotly_dark")
fig.update_yaxes(range=[-5, 15])
st.plotly_chart(fig, use_container_width=True)
