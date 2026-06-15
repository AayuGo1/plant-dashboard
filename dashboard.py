# --- MODERN STYLING INJECTION ---
st.markdown("""
    <style>
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] {
            background-color: #F8F9FA;
            border: 1px solid #E6E8EC;
            border-radius: 6px 6px 0px 0px;
            padding: 10px 20px;
            font-weight: 600;
            color: #4A4A6A;
        }
        .stTabs [data-baseweb="tab"]:hover { color: #00D2FF; }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: #1E1E2F;
            color: white;
            border-color: #1E1E2F;
        }
        
        /* High-Contrast Card Custom Styling for perfect visibility */
        div[data-testid="stMetric"] {
            background-color: #1E1E2F !important;  /* Modern dark theme container */
            border: 1px solid #2D2D44 !important;
            padding: 20px !important;
            border-radius: 10px !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.15) !important;
        }
        
        /* Force color fixes onto native metric label sub-elements */
        div[data-testid="stMetricLabel"] p {
            color: #A3A3C2 !important;              /* High visibility muted label text */
            font-size: 13px !important;
            font-weight: 600 !important;
            letter-spacing: 0.5px !important;
        }
        div[data-testid="stMetricValue"] div {
            color: #FFFFFF !important;              /* Crisp white crisp numbers */
            font-size: 32px !important;
            font-weight: 700 !important;
        }
    </style>
""", unsafe_allow_html=True)
