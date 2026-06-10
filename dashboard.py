import streamlit as st
import pandas as pd
import plotly.express as px
import smtplib
from email.message import EmailMessage

# --- CONFIGURATION ---
st.set_page_config(page_title="Plant Temperature Dashboard", layout="wide")
THRESHOLD = 0.0
SENDER = "kushgoel9998@gmail.com"
PASSWORD = "UJ7iK8oL9pP1aA2s" 
RECIPIENT = "narendra.saraswat@jublfood.com"

# --- ALERT FUNCTION ---
def send_alert(cooler_name, temp):
    msg = EmailMessage()
    msg.set_content(f"CRITICAL: {cooler_name} has reached {temp:.2f}°C, exceeding the safe limit of {THRESHOLD}°C.")
    msg['Subject'] = f"ALERT: {cooler_name} Temperature Breach"
    msg['From'] = SENDER
    msg['To'] = RECIPIENT

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER, PASSWORD)
            server.send_message(msg)
        print(f"SUCCESS: Alert email sent to {RECIPIENT} for {cooler_name}")
    except Exception as e:
        print(f"ERROR: {e}")

# --- DATA LOADING ---
@st.cache_data(ttl=60)
def load_data():
    df = pd.read_excel('plant_data.xlsx', engine='openpyxl')
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    return df

# --- DASHBOARD UI ---
st.title("🌡️ Plant Temperature Monitoring")
df = load_data()

if 'alert_sent' not in st.session_state:
    st.session_state.alert_sent = {"Dough Cooler 1": False, "Dough Cooler 2": False}

cols = st.columns(3)
coolers = {"Dough Cooler 1": cols[0], "Dough Cooler 2": cols[1], "Perishable Cooler": cols[2]}

for name, col in coolers.items():
    # Force data to numeric to ensure comparison works
    current_temp = pd.to_numeric(df[name].iloc[-1], errors='coerce')
    
    with col:
        st.metric(name, f"{current_temp:.2f}°C")
        
        if name in ["Dough Cooler 1", "Dough Cooler 2"]:
            # Check Threshold
            if pd.notnull(current_temp) and current_temp > THRESHOLD:
                st.error(f"ALERT: {name} threshold exceeded!")
                if not st.session_state.alert_sent[name]:
                    send_alert(name, current_temp)
                    st.session_state.alert_sent[name] = True
            else:
                # Reset status if temp is back to safe range
                st.session_state.alert_sent[name] = False
        
        elif current_temp == 0:
            st.warning("Sensor Inactive")

# Visualization
st.subheader("Historical Trends")
df_melted = df.melt(id_vars="Timestamp", var_name="Cooler", value_name="Temperature")
fig = px.line(df_melted, x="Timestamp", y="Temperature", color="Cooler", template="plotly_dark")
fig.update_yaxes(range=[-5, 15])
st.plotly_chart(fig, use_container_width=True)
