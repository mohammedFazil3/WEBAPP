# free_text_collector.py - Module for collecting keystrokes for free-text model with real-time anomaly detection

import os
import json
import threading
import time
import logging
from datetime import datetime
import pandas as pd
import numpy as np
import joblib
from keystroke import keystroke_collector
from models import fixed_text_model
from preprocessing import keystroke_processor
import pickle
import glob
from . import transition_integration

logger = logging.getLogger(__name__)

# Global variables
collection_active = False
prediction_active = False
keystroke_count = 0
keystroke_threshold = 30  # Number of keystrokes before prediction
free_text_target = 10000  # Target for free-text model training
monitor_thread = None
last_prediction_time = None

# File paths based on the actual project structure
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
ALERTS_DIR = os.path.join(STORAGE_DIR, "alerts")
COLLECTION_STATUS_PATH = os.path.join(STORAGE_DIR, "free_text_collection_status.json")
PREDICTION_BUFFER_PATH = os.path.join(STORAGE_DIR, "prediction_buffer.csv")
FIXED_TEXT_MODEL_PATH = os.path.join(STORAGE_DIR, "models", "fixed-text_model.pkl")
MODEL_INFO_PATH = os.path.join(STORAGE_DIR, "models", "fixed-text_info.json")

# Ensure directories exist
os.makedirs(ALERTS_DIR, exist_ok=True)

# Initialize fixed text model
# Check if the model file exists
if not os.path.exists(FIXED_TEXT_MODEL_PATH):
    logger.error(f"Fixed-text model file not found at: {FIXED_TEXT_MODEL_PATH}")
    fixed_text = None
    model_trained = False
else:
    try:
        # Load the trained model from .pkl file
        with open(FIXED_TEXT_MODEL_PATH, 'rb') as f:
            fixed_text = pickle.load(f)
        logger.info("Successfully loaded trained fixed-text model from .pkl file")
    except Exception as e:
        logger.error(f"Error loading fixed-text model: {str(e)}")
        fixed_text = None
    
    # Check if model info file exists (this contains training status)
    if os.path.exists(MODEL_INFO_PATH):
        try:
            with open(MODEL_INFO_PATH, 'r') as f:
                model_info = json.load(f)
            model_trained = model_info.get('is_trained', False)
            logger.info(f"Fixed-text model info loaded: trained={model_trained}")
        except Exception as e:
            logger.error(f"Error reading model info file: {str(e)}")
            model_trained = False
    else:
        logger.error(f"Model info file not found at: {MODEL_INFO_PATH}")
        model_trained = False

# Function to check if the model is trained
def is_model_trained():
    return fixed_text is not None and model_trained

def get_status():
    """Get the current status of free-text collection and prediction."""
    global collection_active, prediction_active, keystroke_count, keystroke_threshold, free_text_target, last_prediction_time
    
    # Get the collection status from the existing collector
    collector_status = keystroke_collector.get_collection_status()
    
    # Check fixed-text model status
    fixed_text_model_exists = os.path.exists(FIXED_TEXT_MODEL_PATH)
    fixed_text_info_exists = os.path.exists(MODEL_INFO_PATH)
    
    # Load training status from info file rather than calling get_info()
    fixed_text_model_trained = False
    if fixed_text_info_exists:
        try:
            with open(MODEL_INFO_PATH, 'r') as f:
                model_info = json.load(f)
            fixed_text_model_trained = model_info.get('is_trained', False)
        except Exception as e:
            logger.error(f"Error reading model info file: {str(e)}")
    
    # Build and return the combined status
    status = {
        "collection_active": collection_active,
        "prediction_active": prediction_active,
        "keystroke_count": keystroke_count,
        "keystroke_threshold": keystroke_threshold,
        "prediction_buffer_size": _get_buffer_size(),
        "free_text_progress": {
            "collected": keystroke_count,
            "target": free_text_target,
            "percentage": min(100, round((keystroke_count / free_text_target) * 100, 1)),
            "complete": keystroke_count >= free_text_target
        },
        "last_prediction_time": last_prediction_time,
        "collector_status": collector_status,
        "fixed_text_model": {
            "exists": fixed_text_model_exists,
            "info_exists": fixed_text_info_exists,
            "trained": fixed_text_model_trained,
            "model_path": FIXED_TEXT_MODEL_PATH,
            "info_path": MODEL_INFO_PATH
        },
        "last_updated": datetime.now().isoformat()
    }
    
    return status

def save_status():
    """Save the current collection status to a file."""
    status = get_status()
    
    try:
        with open(COLLECTION_STATUS_PATH, 'w') as f:
            json.dump(status, f)
    except Exception as e:
        logger.error(f"Error saving collection status: {str(e)}")

def _get_buffer_size():
    """Get the current size of the prediction buffer."""
    if os.path.exists(PREDICTION_BUFFER_PATH):
        try:
            with open(PREDICTION_BUFFER_PATH, 'r') as f:
                return sum(1 for _ in f) - 1  # Subtract 1 for header
        except Exception as e:
            logger.error(f"Error reading prediction buffer: {str(e)}")
    return 0

def _reset_prediction_buffer():
    """Reset the prediction buffer file."""
    try:
        # Create a new empty file with headers
        with open(PREDICTION_BUFFER_PATH, 'w', newline='') as f:
            writer = pd.DataFrame(columns=["Timestamp_Press", "Timestamp_Release", "Key Stroke", "Application", "Hold Time"])
            writer.to_csv(f, index=False)
    except Exception as e:
        logger.error(f"Error resetting prediction buffer: {str(e)}")

def start_free_text_collection(username):
    """Start collecting keystrokes for free-text model with real-time anomaly detection."""
    global collection_active, prediction_active, monitor_thread, keystroke_count
    
    if collection_active:
        logger.warning("Free-text collection already active")
        return False, "Free-text collection is already active"
    
    try:
        # Check if fixed-text model exists and is initialized
        if fixed_text is None:
            logger.error(f"Fixed-text model file not found at: {FIXED_TEXT_MODEL_PATH}")
            return False, f"Fixed-text model file not found at: {FIXED_TEXT_MODEL_PATH}"
            
        # Check if the model file exists in the expected location
        if not os.path.exists(FIXED_TEXT_MODEL_PATH):
            logger.error(f"Fixed-text model file not found at: {FIXED_TEXT_MODEL_PATH}")
            return False, f"Fixed-text model file not found at: {FIXED_TEXT_MODEL_PATH}"
        
        # Check if fixed-text model is trained
        if not is_model_trained():
            logger.error("Fixed-text model is not trained yet")
            return False, "Fixed-text model is not trained yet for anomaly detection"
        
        # First, start the normal keystroke collection for free-text
        if not keystroke_collector.get_collection_status()["active"]:
            model_type = "free-text"  # Specifically for free-text collection
            result = keystroke_collector.start_collection(username, model_type)
            if not result:
                logger.error("Failed to start keystroke collection")
                return False, "Failed to start keystroke collection"
        
        # Reset prediction buffer
        _reset_prediction_buffer()
        
        # Initialize keystroke count
        keystroke_count = 0
        
        # Activate collection and prediction
        collection_active = True
        prediction_active = True
        
        # Start background monitoring thread
        if monitor_thread is None or not monitor_thread.is_alive():
            monitor_thread = threading.Thread(target=monitor_collection)
            monitor_thread.daemon = True
            monitor_thread.start()
        
        # Save status
        save_status()
        
        logger.info(f"Started free-text collection for user {username}")

        # Start transition monitoring
        transition_integration.init_transition_monitoring("keystroke.freetext_keystroke_collector")
        return True, "Free-text collection started successfully"
        
    except Exception as e:
        error_msg = f"Error starting free-text collection: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def stop_free_text_collection():
    """Stop collecting keystrokes for free-text model."""
    global collection_active, prediction_active
    
    if not collection_active:
        logger.warning("Free-text collection not active")
        return False, "Free-text collection is not active"
    
    try:
        # Set flags to stop the background threads
        collection_active = False
        prediction_active = False
        
        # Stop the normal keystroke collection
        keystroke_collector.stop_collection()
        
        # Save status
        save_status()
        
        logger.info("Stopped free-text collection")
        return True, "Free-text collection stopped successfully"
    except Exception as e:
        error_msg = f"Error stopping free-text collection: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def toggle_anomaly_detection(enable):
    """Enable or disable real-time anomaly detection during free-text collection."""
    global prediction_active
    
    if not collection_active:
        logger.warning("Free-text collection not active")
        return False, "Free-text collection is not active"
    
    try:
        prediction_active = enable
        status = "enabled" if enable else "disabled"
        
        # Save status
        save_status()
        
        logger.info(f"Anomaly detection {status}")
        return True, f"Real-time anomaly detection {status} successfully"
    except Exception as e:
        error_msg = f"Error toggling anomaly detection: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def set_keystroke_threshold(threshold):
    """Set the keystroke threshold for anomaly detection."""
    global keystroke_threshold
    
    try:
        keystroke_threshold = max(5, min(100, threshold))  # Limit between 5 and 100
        
        # Save status
        save_status()
        
        logger.info(f"Set keystroke threshold to {keystroke_threshold}")
        return True, f"Keystroke threshold set to {keystroke_threshold}"
    except Exception as e:
        error_msg = f"Error setting keystroke threshold: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def process_for_anomaly_detection():
    """Process the keystroke buffer for anomaly detection."""
    global last_prediction_time
    
    try:
        # Check if prediction buffer exists
        if not os.path.exists(PREDICTION_BUFFER_PATH):
            logger.warning("Prediction buffer does not exist")
            return
        
        # Read the prediction buffer
        try:
            df = pd.read_csv(PREDICTION_BUFFER_PATH)
            if len(df) < keystroke_threshold:
                return  # Not enough keystrokes for prediction
        except Exception as e:
            logger.error(f"Error reading prediction buffer: {str(e)}")
            return
        
        # Preprocess data for prediction
        try:
            processed_data = keystroke_processor.preprocess_keystroke_data(df)
        except Exception as e:
            logger.error(f"Error preprocessing data: {str(e)}")
            return
        
        # Make prediction with fixed-text model for anomaly detection
        try:
            # Use the prediction method
            prediction = fixed_text.predict(processed_data)
            prediction = prediction.flatten() if isinstance(prediction, np.ndarray) else prediction
            
            # Convert prediction to list if it's not already
            if not isinstance(prediction, (list, np.ndarray)):
                predictions = [int(prediction)]
            else:
                predictions = [int(p) for p in prediction]
            
            # Check for consecutive zeros
            consecutive_zeros = 0
            is_anomaly = False
            for pred in predictions:
                if pred == 0:
                    consecutive_zeros += 1
                    if consecutive_zeros >= 2:
                        is_anomaly = True
                        break
                else:
                    consecutive_zeros = 0
            
            # Create result structure
            result = {
                'success': True,
                'predictions': predictions,  # Store all predictions
                'consecutive_zeros': consecutive_zeros,  # Store count of consecutive zeros
                'is_anomaly': is_anomaly  # True if 2 or more consecutive zeros found
            }
            
            # Add confidence if available
            try:
                prediction_proba = fixed_text.predict_proba(processed_data)
                # Calculate average confidence for authorized user class (1)
                if isinstance(prediction_proba, np.ndarray):
                    # Get probabilities for class 1 (authorized user)
                    auth_probas = prediction_proba[:, 1]
                    confidence = float(np.mean(auth_probas))
                else:
                    confidence = float(prediction_proba[1])
                result['confidence'] = confidence
            except Exception as e:
                logger.warning(f"Could not get prediction confidence: {str(e)}")
                result['confidence'] = 0.0
            
        except Exception as e:
            logger.error(f"Error making prediction: {str(e)}")
            return
        
        # Log prediction results
        last_prediction_time = datetime.now().isoformat()
        logger.info(f"Prediction result: {result}")
        
        # Check for anomaly
        if result.get('is_anomaly', False):
            create_alert(result, df)
        
        # Reset prediction buffer
        _reset_prediction_buffer()
        
        # Save status
        save_status()
        
    except Exception as e:
        logger.error(f"Error processing for anomaly detection: {str(e)}")

def create_alert(result, keystroke_data):
    """Create an alert for anomalous behavior."""
    try:
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        alert_id = f"free_text_alert_{timestamp}"
        alert_file = os.path.join(ALERTS_DIR, f"{alert_id}.json")
        
        # Convert DataFrame to dict and handle numpy types
        if isinstance(keystroke_data, pd.DataFrame):
            # Convert DataFrame to records and handle numpy types
            all_keystrokes = []
            for _, row in keystroke_data.iterrows():
                keystroke_dict = {}
                for col in keystroke_data.columns:
                    value = row[col]
                    # Handle numpy types
                    if hasattr(value, 'item'):
                        value = value.item()
                    # Handle datetime objects
                    elif isinstance(value, (pd.Timestamp, datetime)):
                        value = value.isoformat()
                    keystroke_dict[col] = value
                all_keystrokes.append(keystroke_dict)
        else:
            all_keystrokes = []
        
        # Convert any numpy types in result to native Python types
        result = json.loads(json.dumps(result, default=lambda x: x.item() if hasattr(x, 'item') else x))
        
        alert_data = {
            "id": alert_id,
            "timestamp": datetime.now().isoformat(),
            "type": "free_text_keystroke_anomaly",
            "confidence": float(result.get('confidence', 0)),  # Ensure confidence is float
            "prediction_result": result,
            "keystroke_count": int(len(keystroke_data)),  # Ensure count is int
            "keystrokes": all_keystrokes,
            "free_text_collection_progress": {
                "collected": int(keystroke_count),  # Ensure counts are int
                "target": int(free_text_target),
                "percentage": float(min(100, round((keystroke_count / free_text_target) * 100, 1)))  # Ensure percentage is float
            }
        }
        
        with open(alert_file, 'w') as f:
            json.dump(alert_data, f)
        
        # Also log the full keystroke data to a CSV file for easier analysis
        log_file = os.path.join(ALERTS_DIR, f"{alert_id}_keystrokes.csv")
        if isinstance(keystroke_data, pd.DataFrame):
            keystroke_data.to_csv(log_file, index=False)
        
        logger.warning(f"ALERT CREATED: Anomalous keystroke behavior detected during free-text collection with confidence {result.get('confidence', 0)}")
        logger.info(f"Full keystroke data saved to {log_file}")
    except Exception as e:
        logger.error(f"Error creating alert: {str(e)}")
        logger.exception("Full traceback:")

def monitor_collection():
    """Background thread to monitor free-text collection and trigger anomaly detection."""
    global keystroke_count, collection_active, prediction_active
    
    logger.info("Started free-text collection monitoring thread")
    
    # Keep track of last known keystroke count
    last_known_count = 0
    buffer_count = 0
    
    while collection_active:
        try:
            # Get the current status from the keystroke collector
            collector_status = keystroke_collector.get_collection_status()
            current_count = collector_status.get("keystroke_count", 0)
            
            # If there are new keystrokes
            if current_count > last_known_count:
                new_keystrokes = current_count - last_known_count
                keystroke_count += new_keystrokes
                logger.debug(f"Detected {new_keystrokes} new keystrokes, total: {keystroke_count}")
                
                # Check if we've reached the free-text target
                if keystroke_count >= free_text_target:
                    logger.info(f"Reached target of {free_text_target} keystrokes for free-text model training")
                    # Train free-text model once target is reached
                    try:
                        logger.info("Starting free-text model training process")
                        
                        # Get the username from the current collection status
                        username = keystroke_collector.get_collection_status().get("username", "unknown")
                        
                        # 1. Load authorized user data from the most recent collection file
                        user_keystroke_dir = os.path.join(STORAGE_DIR, "keystroke_collection")
                        current_date = datetime.now().strftime('%Y-%m-%d')
                        user_file = os.path.join(user_keystroke_dir, f"keystrokes_{username}_free-text_{current_date}.csv")
                        
                        # If today's file doesn't exist, try to find any matching file
                        if not os.path.exists(user_file):
                            all_files = os.listdir(user_keystroke_dir)
                            matching_files = [f for f in all_files if f.startswith(f"keystrokes_{username}_free-text_") and f.endswith(".csv")]
                            
                            if not matching_files:
                                logger.error(f"No free-text keystroke files found for user {username}")
                                return
                            
                            # Sort files by modification time (newest first)
                            matching_files.sort(key=lambda f: os.path.getmtime(os.path.join(user_keystroke_dir, f)), reverse=True)
                            user_file = os.path.join(user_keystroke_dir, matching_files[0])
                        
                        logger.info(f"Loading authorized user data from {user_file}")
                        
                        # 2. Load anomaly user data
                        anomaly_dir = os.path.join(STORAGE_DIR, "data")
                        all_files = os.listdir(anomaly_dir)
                        anomaly_files = [os.path.join(anomaly_dir, f) for f in all_files 
                                    if f.startswith("Freetext_") and f.endswith(".csv")]
                        
                        if not anomaly_files:
                            logger.error("No anomaly data files found")
                            return
                        
                        logger.info(f"Found {len(anomaly_files)} anomaly data files")
                        
                        # 3. Create a dictionary of additional users (anomaly users)
                        additional_users = {}
                        for idx, file_path in enumerate(anomaly_files):
                            # Use a numbered ID for each anomaly user
                            additional_users[f"anomaly_user_{idx}"] = file_path
                        
                        # 4. Preprocess the data using the keystroke_processor
                        logger.info("Preprocessing keystroke data with user information")
                        processed_df = keystroke_processor.preprocess_keystroke_data(
                            user_file,
                            user_name=username,
                            additional_users=additional_users
                        )
                        
                        logger.info(f"Processed data shape: {processed_df.shape}")
                        
                        # 5. Separate features and labels
                        if 'User' in processed_df.columns:
                            # Create binary labels: 1 for authorized user, 0 for anomaly users
                            y = (processed_df['User'] == username).astype(int)
                            # Remove User column from features
                            X = processed_df.drop('User', axis=1)
                        else:
                            logger.error("User column not found in processed data")
                            return
                        
                        logger.info(f"Features shape: {X.shape}, Labels shape: {y.shape}")
                        logger.info(f"Positive samples (authorized user): {sum(y)}, Negative samples (anomaly): {len(y) - sum(y)}")
                        
                        # 6. Import the model
                        from models import free_text_model
                        model = free_text_model.FreeTextModel(username)
                        
                        # Get the absolute file path that the model is expecting
                        # Convert the relative path in model.data_path to an absolute path
                        model_data_dir = os.path.dirname(os.path.abspath(model.data_path))
                        model_data_path = os.path.abspath(model.data_path)
                        
                        # Ensure the directory exists
                        os.makedirs(model_data_dir, exist_ok=True)
                        
                        # Add the label column to the processed data
                        data_for_model = X.copy()
                        data_for_model['label'] = y
                        
                        # Save directly to the exact path that the model is looking for
                        data_for_model.to_csv(model_data_path, index=False)
                        logger.info(f"Saved processed data to {model_data_path}")
                        
                        # 7. Update collection status to indicate enough data has been collected
                        collection_status = model.get_collection_status()
                        collection_status['keystroke_count'] = free_text_target
                        collection_status['percentage'] = 100
                        collection_status['last_updated'] = datetime.now().isoformat()
                        collection_status['username'] = username
                        
                        # Save the updated status
                        with open(model.collection_path, 'w') as f:
                            json.dump(collection_status, f)
                        logger.info(f"Updated collection status at {model.collection_path}")
                        
                        # 8. Train the model with parameters
                        logger.info("Training free-text model")
                        model_params = {
                            
                        }
                        
                        # Verify the file exists before training
                        if os.path.exists(model_data_path):
                            logger.info(f"Confirmed training data file exists at {model_data_path}")
                        else:
                            logger.error(f"Training data file NOT found at {model_data_path}")
                        
                        result = model.train(model_params)
                        
                        if result.get('success', False):
                            logger.info(f"Free-text model trained successfully with accuracy: {result.get('accuracy', 0)}")
                        else:
                            logger.error(f"Error in model training: {result.get('error', 'Unknown error')}")
                        
                    except Exception as e:
                        logger.error(f"Error in free-text model training process: {str(e)}")
                        logger.exception("Full traceback for training process:")

                # Get the latest keystrokes for anomaly detection
                try:
                    # Get the csv file path
                    csv_file = keystroke_collector.get_log_file_path()
                    
                    if os.path.exists(csv_file):
                        # Read the latest keystrokes
                        df = pd.read_csv(csv_file)
                        
                        # Get only the new ones
                        if len(df) >= new_keystrokes:
                            latest_keystrokes = df.iloc[-new_keystrokes:]
                            
                            # Append to the prediction buffer
                            if os.path.exists(PREDICTION_BUFFER_PATH):
                                # Append to existing buffer
                                with open(PREDICTION_BUFFER_PATH, 'a', newline='') as f:
                                    latest_keystrokes.to_csv(f, header=False, index=False)
                            else:
                                # Create new buffer file
                                latest_keystrokes.to_csv(PREDICTION_BUFFER_PATH, index=False)
                            
                            buffer_count += new_keystrokes
                except Exception as e:
                    logger.error(f"Error updating prediction buffer: {str(e)}")
                
                # Check if we should make an anomaly detection
                if buffer_count >= keystroke_threshold and prediction_active:
                    # Process for anomaly detection
                    process_for_anomaly_detection()
                    buffer_count = 0
                
                # Update last known count
                last_known_count = current_count
            
            # Save status
            save_status()
            
            # Sleep for a bit
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error in free-text collection monitoring thread: {str(e)}")
            time.sleep(5)
    
    logger.info("Free-text collection monitoring thread stopped")