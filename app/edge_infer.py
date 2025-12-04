# app/edge_infer.py

import paho.mqtt.client as mqtt
import json
import joblib
import numpy as np
import os
import subprocess
from collections import deque
from datetime import datetime
import time

# --- Configuration ---
MQTT_BROKER = "broker"
MQTT_PORT = 1883
MQTT_TOPIC_SENSORS = "roomA/sensors"
MODEL_DIR = "models"
STATE_FILE = "data/state.json" # Kept the fix: saves to 'data/' volume so dashboard sees it
N_LAGS = 5
RETRAIN_THRESHOLD_RMSE = 50.0  # <--- RESTORED TO 50.0
PREDICTION_BUFFER_SIZE = 100

# --- Global State ---
prediction_buffer = deque(maxlen=PREDICTION_BUFFER_SIZE)
latest_voc_readings = deque(maxlen=N_LAGS)
model = None
model_version = "N/A"

def load_latest_model():
    """Loads the most recently created model file from the models directory."""
    global model, model_version
    try:
        model_files = [f for f in os.listdir(MODEL_DIR) if f.endswith(".joblib")]
        if not model_files: return False
        
        # Find the newest file
        latest_model_file = max(model_files, key=lambda f: os.path.getctime(os.path.join(MODEL_DIR, f)))
        model_path = os.path.join(MODEL_DIR, latest_model_file)
        
        model = joblib.load(model_path)
        model_version = latest_model_file
        print(f"Edge: Successfully loaded model: {model_version}")
        return True
    except Exception as e:
        print(f"Edge: Error loading model: {e}")
        return False

def save_state():
    """Saves current pipeline state to a JSON file for the dashboard."""
    rolling_rmse = calculate_rolling_rmse()
    state = {
        "model_version": model_version, 
        "buffer_size": len(prediction_buffer), 
        "rolling_rmse": rolling_rmse, 
        "retrain_threshold": RETRAIN_THRESHOLD_RMSE, 
        "last_updated": datetime.now().isoformat()
    }
    # Ensure directory exists
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f: 
        json.dump(state, f, indent=4)

def calculate_rolling_rmse():
    """Calculates RMSE from the current prediction buffer."""
    if len(prediction_buffer) < 2: return None
    actuals, predictions = zip(*prediction_buffer)
    return np.sqrt(np.mean((np.array(actuals) - np.array(predictions))**2))

def on_connect(client, userdata, flags, reason_code, properties):
    """MQTT V2 Callback for connection."""
    if reason_code == 0:
        print("Edge: Connected to MQTT Broker!")
        client.subscribe(MQTT_TOPIC_SENSORS)
        print(f"Edge: Subscribed to topic: {MQTT_TOPIC_SENSORS}")
    else:
        print(f"Edge: Failed to connect, return code {reason_code}\n")

def on_message(client, userdata, msg):
    """Main logic: Receive data -> Predict -> Check Drift -> Trigger Retrain"""
    try:
        payload = json.loads(msg.payload.decode())
        actual_voc = payload['voc_ppb']
        latest_voc_readings.append(actual_voc)

        # Only predict if we have enough lags and a loaded model
        if len(latest_voc_readings) == N_LAGS and model:
            features = np.array(list(latest_voc_readings)).reshape(1, -1)
            prediction = model.predict(features)[0]
            
            # Store (actual, prediction)
            prediction_buffer.append((actual_voc, prediction))
            
            # Check for Drift
            rolling_rmse = calculate_rolling_rmse()
            if rolling_rmse is not None:
                # print(f"Actual: {actual_voc:<5} | Pred: {prediction:<5.1f} | Rolling RMSE: {rolling_rmse:.2f}")
                
                if rolling_rmse > RETRAIN_THRESHOLD_RMSE:
                    print(f"!!! DRIFT DETECTED (RMSE {rolling_rmse:.2f} > {RETRAIN_THRESHOLD_RMSE}) !!!")
                    print("--- Triggering model retraining ---")
                    
                    # Run the training script via subprocess
                    subprocess.run(["python", "cloud/train.py"], check=True)
                    
                    print("--- Retraining finished. Reloading new model. ---")
                    load_latest_model()
                    prediction_buffer.clear() # Reset buffer to give new model a fresh start
                    latest_voc_readings.clear()
            
            # Save state for Dashboard
            save_state()

    except Exception as e: 
        print(f"An error occurred in on_message: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    print("Edge: Waiting for a model to become available...")
    
    # Bootstrap Logic: Wait until user runs training once manually
    while not load_latest_model():
        time.sleep(5)
    
    print("Edge: Initial model loaded. Proceeding to connect to MQTT.")

    # MQTT Setup (V2 API)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="edge_inference_service")
    client.on_connect = on_connect
    client.on_message = on_message

    # Robust Connection Loop
    connected = False
    while not connected:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            connected = True
        except ConnectionRefusedError:
            print("Edge: Connection refused. Retrying in 5 seconds...")
            time.sleep(5)

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("Edge inference service stopped.")
        client.disconnect()