import streamlit as st
import pandas as pd
import glob
import os

# Page configuration
st.set_page_config(page_title="Plant Temperature Monitor", layout="wide")

def get_latest_data():
    # Find all Excel files in the directory
    files = glob.glob("*.xlsx")
    if not files:
        return None
    
    all_data = []
    
    for file in files:
        # Read each file
        df = pd.read_excel(file)
        df.columns = df.columns.str.strip()
        
        # Required columns
        target_cols = ['Time', 'Dough Cooler1 Temp', 'Dough Cooler2 Temp', 'Perishable Cooler Te']
        
        # Only process files that have all these columns
        if all(col in df.columns for col in target_cols):
            df = df[target_cols].copy()
            # Convert to numeric, handle errors
            for col in target_cols[1:]:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            all_data.append(df)
            
    if not all_data:
        return None
        
    # Combine all files into one master dataframe
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Clean: Remove duplicates and sort by Time
    combined_df = combined_df.drop_duplicates(subset=['Time']).sort_values(by='Time')
    
    return combined_df

st.title("Plant Temperature Dashboard")

data = get_latest_data()

if data is not None:
    # Use the most recent entry for the top metrics
    latest = data.iloc[-1]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Dough Cooler 1", f"{latest['Dough Cooler1 Temp']:.2f}°C")
    col2.metric("Dough Cooler 2", f"{latest['Dough Cooler2 Temp']:.2f}°C")
    col3.metric("Perishable Cooler", f"{latest['Perishable Cooler Te']:.2f}°C")

    # Display aggregated Trend Chart
    st.subheader("Historical Temperature Trends (All Files Combined)")
    st.line_chart(data.set_index('Time'))
else:
    st.error("No valid .xlsx files found in the folder!")
