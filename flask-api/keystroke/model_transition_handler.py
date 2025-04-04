# keystroke/model_transition_handler.py
"""
Module for handling the transition from data collection to model activation.
This module implements functionality to:
1. Monitor free-text model training status
2. Switch the active model to free-text once training is complete
3. Stop collection when transition is complete

This version is designed to work cooperatively with the existing training 
logic in freetext_keystroke_collector.py, focusing only on monitoring and
switching the active model after training is complete.
"""

import os
import json
import logging
import threading
import time
from datetime import datetime
import glob

# Setup logging
logger = logging.getLogger(__name__)

# Global variables
transition_active = False
transition_thread = None
active_model_file = 'flask-api/storage/models/active_model.json'

def start_transition_monitoring(free_text_collector, free_text_model):
    """Start monitoring for transition from data collection to model activation."""
    global transition_active, transition_thread
    
    if transition_active:
        logger.warning("Transition monitoring already active")
        return False, "Transition monitoring is already active"
    
    try:
        # Activate monitoring
        transition_active = True
        
        # Start background monitoring thread
        if transition_thread is None or not transition_thread.is_alive():
            transition_thread = threading.Thread(
                target=monitor_transition,
                args=(free_text_collector, free_text_model)
            )
            transition_thread.daemon = True
            transition_thread.start()
        
        logger.info("Started model transition monitoring")
        return True, "Transition monitoring started successfully"
    
    except Exception as e:
        error_msg = f"Error starting transition monitoring: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def stop_transition_monitoring():
    """Stop monitoring for transition."""
    global transition_active
    
    if not transition_active:
        logger.warning("Transition monitoring not active")
        return False, "Transition monitoring is not active"
    
    try:
        # Deactivate monitoring
        transition_active = False
        
        logger.info("Stopped model transition monitoring")
        return True, "Transition monitoring stopped successfully"
    
    except Exception as e:
        error_msg = f"Error stopping transition monitoring: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def is_free_text_model_trained(free_text_model, username):
    """
    Check if the free-text model has been trained by looking for model files.
    This function checks multiple possible locations for the model file.
    """
    try:
        # Check model info from the model object
        model_info = free_text_model.get_info()
        if model_info.get("is_trained", False):
            logger.info("Free-text model info indicates model is trained")
            return True
            
        # Check for model files in user-specific directory
        user_model_dir = os.path.join('storage', 'models', username)
        if os.path.exists(user_model_dir):
            model_files = glob.glob(os.path.join(user_model_dir, 'free-text_model.*'))
            if model_files:
                logger.info(f"Found free-text model files in user directory: {model_files}")
                return True
                
        # Check for model files in general models directory
        models_dir = os.path.join('storage', 'models')
        if os.path.exists(models_dir):
            model_files = glob.glob(os.path.join(models_dir, 'free-text_model.*'))
            if model_files:
                logger.info(f"Found free-text model files in models directory: {model_files}")
                return True
        
        logger.info("No free-text model files found, assuming not trained yet")
        return False
        
    except Exception as e:
        logger.error(f"Error checking if free-text model is trained: {str(e)}")
        return False

def monitor_transition(free_text_collector, free_text_model):
    """
    Background thread to monitor free-text model training status and handle transition.
    This version assumes the training happens in the collector and only monitors for
    completion before switching the active model and restarting anomaly detection.
    """
    global transition_active
    
    logger.info("Started model transition monitoring thread")
    
    # Check current state first time
    username = free_text_collector.get_status().get("collector_status", {}).get("username", "unknown")
    initial_check = is_free_text_model_trained(free_text_model, username)
    if initial_check:
        logger.info("Free-text model already trained on startup, switching active model")
        switch_active_model("free-text")
        start_anomaly_detection(free_text_collector, username)
    
    # Monitoring loop
    while transition_active:
        try:
            # Get the current status from the free-text collector
            status = free_text_collector.get_status()
            
            # Get username from status
            username = status.get("collector_status", {}).get("username", "unknown")
            
            # First check: if collection is complete and active
            if (status.get("free_text_progress", {}).get("complete", False) and 
                status.get("collection_active", False)):
                
                logger.info("Keystroke threshold reached for free-text model, waiting for training to complete")
                
                # Sleep longer to give time for training to complete in the collector
                time.sleep(30)
                
                # Check every 30 seconds if the model is now trained
                if is_free_text_model_trained(free_text_model, username):
                    logger.info("Free-text model is now trained")
                    
                    # Switch the active model to free-text
                    switch_active_model("free-text")
                    
                    # Stop data collection (actual keystroke collection)
                    free_text_collector.stop_free_text_collection()
                    
                    # Start anomaly detection using the free-text model
                    start_anomaly_detection(free_text_collector, username)
                    
                    # Stop transition monitoring
                    transition_active = False
                    logger.info("Model transition complete: Switched to free-text model and started anomaly detection")
                    break
            
            # Second check: if model is trained regardless of collection status
            elif is_free_text_model_trained(free_text_model, username):
                logger.info("Free-text model is trained")
                
                # Switch the active model to free-text
                switch_active_model("free-text")
                
                # Stop collection if it's still active
                if status.get("collection_active", False):
                    free_text_collector.stop_free_text_collection()
                
                # Start anomaly detection using the free-text model
                start_anomaly_detection(free_text_collector, username)
                
                # Stop transition monitoring
                transition_active = False
                logger.info("Model transition complete: Switched to free-text model and started anomaly detection")
                break
            
            # Sleep for a bit before checking again
            time.sleep(10)
        
        except Exception as e:
            logger.error(f"Error in model transition monitoring thread: {str(e)}")
            time.sleep(30)  # Longer sleep on error
    
    logger.info("Model transition monitoring thread stopped")

def start_anomaly_detection(free_text_collector, username):
    """
    Start anomaly detection using the free-text model.
    This function enables prediction mode while keeping collection inactive.
    
    Args:
        free_text_collector: The free-text collector module
        username: The username for the current user
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Since we've stopped collection but want to continue anomaly detection,
        # we need to set up the collector to perform predictions only
        
        # Reset the prediction buffer to start fresh
        free_text_collector._reset_prediction_buffer()
        
        # Enable prediction while keeping collection inactive
        free_text_collector.prediction_active = True
        free_text_collector.collection_active = False
        
        # Set keystroke threshold to 30 for ongoing anomaly detection
        free_text_collector.keystroke_threshold = 30
        
        # Start keystroke monitoring in prediction-only mode
        # We need to modify the keystroke collector to start in a special mode
        # that only collects keystrokes for prediction without storing for training
        monitor_thread = threading.Thread(
            target=monitor_for_anomalies_only,
            args=(free_text_collector, username)
        )
        monitor_thread.daemon = True
        monitor_thread.start()
        
        logger.info(f"Started anomaly detection using free-text model for user {username}")
        return True
    except Exception as e:
        logger.error(f"Error starting anomaly detection: {str(e)}")
        return False

def monitor_for_anomalies_only(free_text_collector, username):
    """
    Background thread to monitor keystrokes for anomaly detection only.
    This is a simplified version of the monitor_collection function that
    only handles prediction without storing keystrokes for training.
    
    Args:
        free_text_collector: The free-text collector module
        username: The username for the current user
    """
    logger.info("Started anomaly-detection-only monitoring thread")
    
    # Access the global prediction_active flag from the collector
    prediction_active = True
    
    # Use a separate keystroke collector instance for anomaly detection only
    try:
        # Import keystroke collector
        from keystroke import keystroke_collector
        
        # Start a special collection mode for prediction only
        keystroke_collector.start_collection(username, "anomaly-detection")
        
        # Buffer for keystroke counting
        buffer_count = 0
        last_known_count = keystroke_collector.get_collection_status().get("keystroke_count", 0)
        
        # Monitor loop
        while prediction_active and free_text_collector.prediction_active:
            try:
                # Get current keystroke count
                collector_status = keystroke_collector.get_collection_status()
                current_count = collector_status.get("keystroke_count", 0)
                
                # If there are new keystrokes
                if current_count > last_known_count:
                    new_keystrokes = current_count - last_known_count
                    buffer_count += new_keystrokes
                    
                    # Get the latest keystrokes for anomaly detection
                    csv_file = keystroke_collector.get_log_file_path()
                    
                    if os.path.exists(csv_file):
                        try:
                            # Read the latest keystrokes with more robust error handling
                            import pandas as pd
                            
                            # Use error_bad_lines=False (renamed to on_bad_lines in newer pandas versions)
                            try:
                                # For newer pandas versions (1.3+)
                                df = pd.read_csv(csv_file, on_bad_lines='skip')
                            except TypeError:
                                # For older pandas versions
                                df = pd.read_csv(csv_file, error_bad_lines=False, warn_bad_lines=True)
                            
                            # Ensure only rows with the expected column count are used
                            expected_columns = ["Timestamp_Press", "Timestamp_Release", "Key Stroke", "Application", "Hold Time"]
                            if df.shape[1] != len(expected_columns):
                                logger.warning(f"CSV has unexpected column count: {df.shape[1]} (expected {len(expected_columns)})")
                                # Only select rows that have complete data for required columns
                                df = df.iloc[:, :len(expected_columns)]
                                df.columns = expected_columns
                            
                            # Validate data
                            if df.empty:
                                logger.warning("No valid keystroke data after filtering")
                                last_known_count = current_count
                                continue
                            
                            # Get only the new ones, being careful about length
                            valid_rows = min(len(df), new_keystrokes)
                            if valid_rows > 0:
                                latest_keystrokes = df.iloc[-valid_rows:]
                                
                                # Append to the prediction buffer
                                buffer_path = free_text_collector.PREDICTION_BUFFER_PATH
                                
                                # Make sure the buffer path directory exists
                                os.makedirs(os.path.dirname(buffer_path), exist_ok=True)
                                
                                if os.path.exists(buffer_path):
                                    # Append to existing buffer, making sure to include proper header
                                    with open(buffer_path, 'a', newline='') as f:
                                        latest_keystrokes.to_csv(f, header=False, index=False)
                                else:
                                    # Create new buffer file with proper header
                                    latest_keystrokes.to_csv(buffer_path, index=False)
                        
                        except Exception as e:
                            logger.error(f"Error processing keystroke CSV file: {str(e)}")
                            # Continue with the loop even if there was an error
                    
                    # Check if we should make an anomaly detection
                    if buffer_count >= free_text_collector.keystroke_threshold:
                        try:
                            # Process for anomaly detection
                            free_text_collector.process_for_anomaly_detection()
                        except Exception as e:
                            logger.error(f"Error in anomaly detection processing: {str(e)}")
                        
                        # Reset buffer count regardless of success/failure
                        buffer_count = 0
                    
                    # Update last known count
                    last_known_count = current_count
                
                # Sleep for a bit
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error in anomaly detection monitoring: {str(e)}")
                time.sleep(5)
    except Exception as e:
        logger.error(f"Error setting up anomaly detection monitoring: {str(e)}")
    
    logger.info("Anomaly detection monitoring thread stopped")

def switch_active_model(model_type):
    """Switch the active model to the specified type."""
    try:
        # Load current active model config
        if os.path.exists(active_model_file):
            with open(active_model_file, 'r') as f:
                active_model = json.load(f)
        else:
            active_model = {
                'type': 'fixed-text',
                'last_updated': datetime.now().isoformat()
            }
        
        # Only switch if needed
        if active_model.get('type') == model_type:
            logger.info(f"Active model is already set to {model_type}")
            return True
        
        # Update model type and timestamp
        active_model['type'] = model_type
        active_model['last_updated'] = datetime.now().isoformat()
        
        # Save updated config
        with open(active_model_file, 'w') as f:
            json.dump(active_model, f)
        
        logger.info(f"Switched active model to {model_type}")
        return True
    
    except Exception as e:
        logger.error(f"Error switching active model: {str(e)}")
        return False