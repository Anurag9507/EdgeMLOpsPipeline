import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import time

# --- Configuration ---
STATE_FILE = "data/state.json"
RAW_DATA_FILE = "data/raw.csv"
NUM_ROWS_TO_DISPLAY = 200 # Number of recent data points to show on the chart

# --- Page Setup ---
st.set_page_config(
    page_title="IoT Edge MLOps Dashboard",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Live IoT Edge MLOps Pipeline")

# --- Helper Functions ---
def load_json_state(file_path):
    """Safely loads a JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Return a default structure if file is missing or invalid
        return {
            "model_version": "N/A",
            "rolling_rmse": None, # Explicitly handle None
            "retrain_threshold": 0,
            "buffer_size": 0,
            "last_updated": "Never"
        }

def load_csv_data(file_path, n_rows):
    """Loads the last N rows of a CSV file."""
    if not os.path.exists(file_path):
        return pd.DataFrame(columns=["timestamp", "voc_ppb"]) # Return empty df if no file
    try:
        df = pd.read_csv(file_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df.tail(n_rows)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(columns=["timestamp", "voc_ppb"])

# --- Dashboard Layout ---
placeholder = st.empty()

# --- Main Loop to Auto-Refresh ---
while True:
    state = load_json_state(STATE_FILE)
    df_raw = load_csv_data(RAW_DATA_FILE, NUM_ROWS_TO_DISPLAY)

    with placeholder.container():
        st.header("Pipeline Health & Status")
        # Get state values and handle the possibility of None for RMSE
        rolling_rmse_val = state.get('rolling_rmse')
        retrain_thresh_val = state.get('retrain_threshold', 0)
        
        # Calculate delta only if RMSE is available
        delta_val = None
        if rolling_rmse_val is not None:
            delta_val = rolling_rmse_val - retrain_thresh_val

        col1, col2, col3, col4 = st.columns(4)
        col1.metric(
            label="Current Rolling RMSE",
            # Display a placeholder if RMSE is not yet calculated
            value=f"{rolling_rmse_val:.2f}" if rolling_rmse_val is not None else "Calculating...",
            help="Root Mean Squared Error over the last 100 predictions. Lower is better."
        )
        col2.metric(
            label="Retrain Threshold",
            value=f"{retrain_thresh_val:.2f}",
            # Display delta only if it could be calculated
            delta=f"{delta_val:.2f}" if delta_val is not None else None,
            delta_color="inverse",
            help="If RMSE goes above this value, retraining is triggered. Delta shows how far we are from the threshold."
        )
        
        col3.metric(
            label="Active Model Version",
            value=state.get('model_version', 'N/A').replace('.joblib', ''),
            help="The timestamped version of the model currently used for inference."
        )
        col4.metric(
            label="Prediction Buffer",
            value=f"{state.get('buffer_size', 0)} / 100", # Hardcoded buffer size for display
            help="Number of (actual, prediction) pairs stored for calculating RMSE."
        )

        st.markdown(f"**Last Update:** `{state.get('last_updated', 'N/A')}`")
        st.markdown("---")

        st.header("Live Sensor Data (VOC)")
        if not df_raw.empty:
            st.line_chart(df_raw.rename(columns={'timestamp':'index'}).set_index('index')['voc_ppb'])
        else:
            st.warning("No sensor data found. Is the publisher running?")

    time.sleep(2)