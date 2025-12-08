import pytest
import os
import sys
import numpy as np
import pandas as pd
from unittest.mock import MagicMock, patch
from collections import deque

# Add project root to path so we can import app/ and cloud/
sys.path.append(os.getcwd())

# Import specific functions to test
from app.edge_infer import calculate_rolling_rmse, on_message, PREDICTION_BUFFER_SIZE, N_LAGS
from cloud.train import create_lag_features

# --- TEST 1: Logic Verification (RMSE Calculation) ---
def test_calculate_rolling_rmse_logic():
    """
    Verifies that the Root Mean Square Error math is correct.
    """
    # We patch the global buffer inside edge_infer to control the test data
    with patch("app.edge_infer.prediction_buffer", deque(maxlen=PREDICTION_BUFFER_SIZE)) as mock_buffer:
        
        # Case 1: Perfect predictions (10 vs 10, 20 vs 20). RMSE should be 0.
        mock_buffer.append((10, 10))
        mock_buffer.append((20, 20))
        rmse = calculate_rolling_rmse()
        assert rmse == 0.0

        # Case 2: Known error. 
        # Actual=10, Pred=14 (Diff=4, Sq=16)
        # Actual=10, Pred=6  (Diff=4, Sq=16)
        # Mean Sq = 16. Sqrt(16) = 4.
        mock_buffer.clear()
        mock_buffer.append((10, 14)) 
        mock_buffer.append((10, 6))
        rmse = calculate_rolling_rmse()
        assert rmse == 4.0

# --- TEST 2: Data Processing (Lag Features) ---
def test_lag_creation():
    """
    Verifies that the training script creates the correct number of lag features.
    """
    # Create a dummy DataFrame
    data = {'voc_ppb': [100, 200, 300, 400, 500, 600]}
    df = pd.DataFrame(data)
    
    # Generate lags (e.g., 2 lags)
    n_lags_test = 2
    df_lags = create_lag_features(df, 'voc_ppb', n_lags=n_lags_test)
    
    # Assertions
    # 1. We lose the first N rows (NaNs), so length should be 6 - 2 = 4
    assert len(df_lags) == 4
    
    # 2. Check the last row logic
    # Last row 'voc_ppb' is 600. 'lag_1' should be 500. 'lag_2' should be 400.
    last_row = df_lags.iloc[-1]
    assert last_row['voc_ppb'] == 600
    assert last_row['voc_ppb_lag_1'] == 500
    assert last_row['voc_ppb_lag_2'] == 400

# --- TEST 3: Drift Detection Integration (Mocking) ---
@patch("subprocess.run")
@patch("app.edge_infer.load_latest_model")
@patch("app.edge_infer.save_state") # Prevent writing JSON files during test
def test_drift_trigger_mechanism(mock_save, mock_load, mock_subprocess):
    """
    Simulates a high-error scenario and ensures the code attempts to run 'cloud/train.py'.
    """
    # Import the threshold DYNAMICALLY so if you change the file, the test updates itself
    from app.edge_infer import RETRAIN_THRESHOLD_RMSE
    
    # 1. Setup Mocks
    mock_client = MagicMock()
    mock_msg = MagicMock()
    
    # Mock a loaded model that always predicts "0"
    mock_model = MagicMock()
    mock_model.predict.return_value = [0]
    
    # Mock global variables in edge_infer
    # We create a huge value guaranteed to trigger drift (Threshold + 1000)
    huge_error_value = RETRAIN_THRESHOLD_RMSE + 1000
    
    # Patch the globals
    with patch("app.edge_infer.model", mock_model), \
         patch("app.edge_infer.latest_voc_readings", deque(maxlen=N_LAGS)) as mock_readings, \
         patch("app.edge_infer.prediction_buffer", deque(maxlen=PREDICTION_BUFFER_SIZE)) as mock_buffer:
        
        # 2. Inject Data
        # We need to send enough messages to fill the "N_LAGS" buffer before it predicts
        for _ in range(N_LAGS + 1):
            # Payload simulates a high actual value vs the predicted 0
            payload = f'{{"voc_ppb": {huge_error_value}, "temp_c": 20, "humidity": 50, "timestamp": "2025-01-01"}}'
            mock_msg.payload.decode.return_value = payload
            
            # Run the actual function
            on_message(mock_client, None, mock_msg)
            
        # 3. Assertions
        # Did it call subprocess?
        mock_subprocess.assert_called()
        
        # Did it try to run the specific training script?
        args, _ = mock_subprocess.call_args
        assert "cloud/train.py" in args[0]
        print("\nTest passed: Drift detected and retraining triggered!")