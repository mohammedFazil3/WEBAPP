# multi_binary_keystroke_collector.py - Module for collecting keystrokes 
# and performing anomaly detection using multi-binary classifier

import os
import json
import threading
import time
import logging
from datetime import datetime
import pandas as pd
import numpy as np
import pickle
import uuid

from keystroke import keystroke_collector
from preprocessing import keystroke_processor

logger = logging.getLogger(__name__)

# Global variables
collection_active = False
prediction_active = False
keystroke_count = 0
keystroke_threshold = 30  # Number of keystrokes before prediction
monitor_thread = None
last_prediction_time = None

# File paths based on the project structure
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
ALERTS_DIR = os.path.join(STORAGE_DIR, "alerts")
COLLECTION_STATUS_PATH = os.path.join(STORAGE_DIR, "multi_binary_collection_status.json")
PREDICTION_BUFFER_PATH = os.path.join(STORAGE_DIR, "multi_binary_prediction_buffer.csv")
MULTI_BINARY_MODEL_PATH = os.path.join(STORAGE_DIR, "models", "multi_binary_classifier.pkl")

# Ensure directories exist
os.makedirs(ALERTS_DIR, exist_ok=True)

# Global variable to hold the loaded model
multi_binary_model = None

def load_multi_binary_model():
    """Load the multi-binary classifier model."""
    global multi_binary_model
    try:
        with open(MULTI_BINARY_MODEL_PATH, 'rb') as f:
            multi_binary_model = pickle.load(f)
        logger.info("Successfully loaded multi-binary classifier model")
        return True
    except Exception as e:
        logger.error(f"Error loading multi-binary model: {str(e)}")
        return False

# Ensure model is loaded on import
model_loaded = load_multi_binary_model()

def get_status():
    """Get the current status of multi-binary collection and prediction."""
    global collection_active, prediction_active, keystroke_count, keystroke_threshold, last_prediction_time
    
    # Get the collection status from the keystroke collector
    collector_status = keystroke_collector.get_collection_status()
    
    status = {
        "collection_active": collection_active,
        "prediction_active": prediction_active,
        "keystroke_count": keystroke_count,
        "keystroke_threshold": keystroke_threshold,
        "prediction_buffer_size": _get_buffer_size(),
        "last_prediction_time": last_prediction_time,
        "collector_status": collector_status,
        "model_loaded": model_loaded,
        "model_path": MULTI_BINARY_MODEL_PATH,
        "last_updated": datetime.now().isoformat()
    }
    
    return status

def save_status():
    """Save the current collection status to a file."""
    status = get_status()
    
    try:
        with open(COLLECTION_STATUS_PATH, 'w') as f:
            json.dump(status, f, indent=4)
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

def start_multi_binary_collection(username):
    """Start collecting keystrokes for multi-binary anomaly detection."""
    global collection_active, prediction_active, monitor_thread, keystroke_count
    
    # Check if model is loaded
    if not model_loaded:
        logger.error("Multi-binary model not loaded. Cannot start collection.")
        return False, "Multi-binary model not loaded"
    
    if collection_active:
        logger.warning("Multi-binary collection already active")
        return False, "Multi-binary collection is already active"
    
    try:
        # First, start the normal keystroke collection
        if not keystroke_collector.get_collection_status()["active"]:
            model_type = "multi-binary"
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
        
        logger.info(f"Started multi-binary collection for user {username}")
        
        return True, "Multi-binary collection started successfully"
        
    except Exception as e:
        error_msg = f"Error starting multi-binary collection: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def stop_multi_binary_collection():
    """Stop collecting keystrokes for multi-binary anomaly detection."""
    global collection_active, prediction_active
    
    if not collection_active:
        logger.warning("Multi-binary collection not active")
        return False, "Multi-binary collection is not active"
    
    try:
        # Set flags to stop the background threads
        collection_active = False
        prediction_active = False
        
        # Stop the normal keystroke collection
        keystroke_collector.stop_collection()
        
        # Save status
        save_status()
        
        logger.info("Stopped multi-binary collection")
        return True, "Multi-binary collection stopped successfully"
    except Exception as e:
        error_msg = f"Error stopping multi-binary collection: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def create_alert(result, keystroke_data):
    """Create an alert for anomalous behavior."""
    try:
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        alert_id = f"multi_binary_alert_{timestamp}"
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
            "type": "multi_binary_keystroke_anomaly",
            "confidence": float(result.get('confidence', 0)),
            "prediction_result": result,
            "keystroke_count": int(len(keystroke_data)),
            "keystrokes": all_keystrokes,
            "collection_progress": {
                "collected": int(keystroke_count),
                "threshold": int(keystroke_threshold),
                "percentage": float(min(100, round((keystroke_count / keystroke_threshold) * 100, 1)))
            }
        }
        
        with open(alert_file, 'w') as f:
            json.dump(alert_data, f, indent=4)
        
        # Also log the full keystroke data to a CSV file for easier analysis
        log_file = os.path.join(ALERTS_DIR, f"{alert_id}_keystrokes.csv")
        if isinstance(keystroke_data, pd.DataFrame):
            keystroke_data.to_csv(log_file, index=False)
        
        logger.warning(f"ALERT CREATED: Anomalous keystroke behavior detected during multi-binary collection with confidence {result.get('confidence', 0)}")
        logger.info(f"Full keystroke data saved to {log_file}")
    except Exception as e:
        logger.error(f"Error creating alert: {str(e)}")
        logger.exception("Full traceback:")

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
        
        # Make prediction with multi-binary model
        try:
            # Use the prediction method
            predicted_classes, probabilities = multi_binary_model.predict(processed_data)
            
            # Get the prediction for the first sample (usually there's only one)
            predicted_class = predicted_classes[0] if predicted_classes else "Unknown"
            
            # Determine if this is an anomaly
            is_anomaly = (predicted_class == "Unknown")
            
            # Get confidence for each class
            confidence_values = {}
            max_confidence = 0
            
            for class_name, probs in probabilities.items():
                confidence = float(probs[0]) if len(probs) > 0 else 0
                confidence_values[class_name] = confidence
                
                if confidence > max_confidence:
                    max_confidence = confidence
            
            # Create result structure
            result = {
                'success': True,
                'predicted_user': predicted_class,
                'is_anomaly': is_anomaly,
                'confidence': max_confidence if not is_anomaly else 0,
                'all_confidences': confidence_values
            }
            
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

def monitor_collection():
    """Background thread to monitor multi-binary collection and trigger anomaly detection."""
    global keystroke_count, collection_active, prediction_active
    
    logger.info("Started multi-binary collection monitoring thread")
    
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
            logger.error(f"Error in monitor_collection: {str(e)}")
            time.sleep(1)  # Sleep before retrying