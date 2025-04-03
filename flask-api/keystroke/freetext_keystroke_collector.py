# free_text_collector.py - Module for collecting keystrokes for free-text model with real-time anomaly detection

import os
import json
import threading
import time
import logging
from datetime import datetime
import pandas as pd
from . import keystroke_collector
from models import fixed_text_model
from preprocessing import keystroke_processor

logger = logging.getLogger(__name__)

# Global variables
collection_active = False
prediction_active = False
keystroke_count = 0
keystroke_threshold = 30  # Number of keystrokes before prediction
free_text_target = 10000  # Target for free-text model training
monitor_thread = None
last_prediction_time = None

# File paths
STORAGE_DIR = "storage"
ALERTS_DIR = os.path.join(STORAGE_DIR, "alerts")
COLLECTION_STATUS_PATH = os.path.join(STORAGE_DIR, "free_text_collection_status.json")
PREDICTION_BUFFER_PATH = os.path.join(STORAGE_DIR, "prediction_buffer.csv")

# Ensure directories exist
os.makedirs(ALERTS_DIR, exist_ok=True)

# Initialize fixed text model
fixed_text = fixed_text_model.FixedTextModel()

def get_status():
    """Get the current status of free-text collection and prediction."""
    global collection_active, prediction_active, keystroke_count, keystroke_threshold, free_text_target, last_prediction_time
    
    # Get the collection status from the existing collector
    collector_status = keystroke_collector.get_collection_status()
    
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
        "fixed_text_model_trained": fixed_text.get_info().get('is_trained', False),
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
        # Check if fixed-text model is trained (for anomaly detection)
        model_info = fixed_text.get_info()
        is_trained = model_info.get('is_trained', False)
        
        if not is_trained:
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
            result = fixed_text.predict(processed_data)
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
        
        # Include ALL keystroke data in the alert, not just a sample
        all_keystrokes = keystroke_data.to_dict('records') if isinstance(keystroke_data, pd.DataFrame) else []
        
        alert_data = {
            "id": alert_id,
            "timestamp": datetime.now().isoformat(),
            "type": "free_text_keystroke_anomaly",
            "confidence": result.get('confidence', 0),
            "prediction_result": result,
            "keystroke_count": len(keystroke_data),
            "keystrokes": all_keystrokes,  # Full keystroke data
            "free_text_collection_progress": {
                "collected": keystroke_count,
                "target": free_text_target,
                "percentage": min(100, round((keystroke_count / free_text_target) * 100, 1))
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