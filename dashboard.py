import streamlit as st
import pandas as pd
import plotly.express as px
import smtplib
from email.message import EmailMessage

# --- CONFIGURATION ---
st.set_page_config(page_title="Plant Temperature Dashboard", layout="wide")
THRESHOLD = 8.0  # Set your safety limit

# --- DATA LOADING ---
@st.cache_data(ttl=60)
def load_data():
    # Replace 'plant_data.xlsx' with your actual filename
    df = pd.read_excel('plant_data.xlsx', engine='openpyxl')
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    return df

# --- ALERT SYSTEM ---
def send_alert(cooler_name, temp):
    msg = EmailMessage()
    msg.set_content(f"CRITICAL: {cooler_name} reached {temp:.2f}°C, exceeding safety limit of {THRESHOLD}°C.")
    msg['Subject'] = f"ALERT: {cooler_name} Temperature"
    msg['From'] = "kushgoel9998email@gmail.com"
    msg['To'] = "recipient@example.com"
    # Use your SMTP server details
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login("kushgoel9998@gmail.com", "your_app_password")
            server.send_message(msg)
    except Exception as e:
        st.error(f"Alert could not be sent: {e}")

# --- DASHBOARD LOGIC ---
st.title("Plant Temperature Monitoring")
df = load_data()

# Initialize Alert Tracking in Session State
if 'alert_sent' not in st.session_state:
    st.session_state.alert_sent = {col: False for col in ["Dough Cooler 1", "Dough Cooler 2"]}

# Metric Cards
cols = st.columns(3)
coolers = {"Dough Cooler 1": cols[0], "Dough Cooler 2": cols[1], "Perishable Cooler": cols[2]}

for name, col in coolers.items():
    current_temp = df[name].iloc[-1]
    with col:
        st.metric(name, f"{current_temp:.2f}°C")
        # Alert logic
        if name != "Perishable Cooler" and current_temp > THRESHOLD:
            st.error("Threshold Exceeded!")
            if not st.session_state.alert_sent[name]:
                send_alert(name, current_temp)
                st.session_state.alert_sent[name] = True
        elif current_temp == 0:
            st.warning("Sensor Inactive")

# Visualization
st.subheader("Historical Trends")
df_melted = df.melt(id_vars="Timestamp", var_name="Cooler", value_name="Temperature")
fig = px.line(df_melted, x="Timestamp", y="Temperature", color="Cooler", template="plotly_dark")
fig.update_yaxes(range=[-5, 15])
st.plotly_chart(fig, use_container_width=True)
