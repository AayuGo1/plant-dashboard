# ==========================================================
# SYSTEM TAB 1: REAL-TIME THERMAL SNAPSHOTS
# ==========================================================
with tab_thermal:
    st.markdown("### 📊 Cryogenic & Cold Storage Thermal Profiles")
    temp_df = load_cached_telemetry()

    if temp_df is not None and not temp_df.empty:
        latest = temp_df.iloc[-1]
        
        # 100% Native premium metric layout blocks
        k1, k2, k3 = st.columns(3)
        with k1:
            st.metric(
                label="❄️ DOUGH COOLER 1", 
                value=f"{latest['Dough Cooler1 Temp']:.2f} °C", 
                delta="Active / Normal Node", 
                delta_color="normal"
            )
        with k2:
            st.metric(
                label="❄️ DOUGH COOLER 2", 
                value=f"{latest['Dough Cooler2 Temp']:.2f} °C", 
                delta="Active / Normal Node", 
                delta_color="normal"
            )
        with k3:
            st.metric(
                label="🥩 PERISHABLE STORAGE", 
                value=f"{latest['Perishable Cooler Temp']:.2f} °C", 
                delta="System Load Alert", 
                delta_color="inverse"
            )
        
        st.markdown("<br><h5 style='color:#1E1E2F;'>📈 Continuous Thermal Profile Stream (5-Min Snapshots)</h5>", unsafe_allow_html=True)
        st.line_chart(temp_df.set_index('Time'), color=["#0068C9", "#29B6F6", "#FF4B4B"])
    else:
        st.warning("⚠️ Telemetry matrix idling. Paste your 'DataLog_*.csv' files into your designated directory path to activate streaming.")
