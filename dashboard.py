import streamlit as st
import pandas as pd
import plotly.express as px
import smtplib
from email.message import EmailMessage

# --- CONFIGURATION ---
st.set_page_config(page_title="Plant Monitoring", layout="wide")
THRESHOLD = 0.0
SENDER = "kushgoel9998@gmail.com
PASSWORD = "1234567890123456" 
RECIPIENT = "narendra.saraswat@jublfood.com"

# --- ALERT FUNCTION ---
def send_alert(cooler_name, temp):
    msg = EmailMessage()
    msg.set_content(f"CRITICAL: {cooler_name} temperature is {temp:.2f}°C.")
    msg['Subject'] = f"ALERT: {cooler_name} Breach"
    msg['From'] = SENDER
    msg['To'] = RECIPIENT
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER, PASSWORD)
            server.send_message(msg)
        st.sidebar.success(f"Email sent for {cooler_name}")
    except Exception as e:
        st.sidebar.error(f"Email Error: {e}")

# --- DATA LOADING ---
df = pd.read_excel('plant_data.xlsx', engine='openpyxl')

# --- UI & LOGIC ---
st.title("Plant Temperature Monitoring")

if 'alert_sent' not in st.session_state:
    st.session_state.alert_sent = {"Dough Cooler 1": False, "Dough Cooler 2": False}

cols = st.columns(3)
coolers = {"Dough Cooler 1": cols[0], "Dough Cooler 2": cols[1]}

for i, (name, col) in enumerate(coolers.items()):
    # Force convert to float
    val = float(df[name].iloc[-1])
    with col:
        st.metric(name, f"{val:.2f}°C")
        
        # Threshold logic
        if val > THRESHOLD:
            st.error("THRESHOLD EXCEEDED")
            if not st.session_state.alert_sent[name]:
                send_alert(name, val)
                st.session_state.alert_sent[name] = True
        else:
            st.session_state.alert_sent[name] = False
