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
active_model_file = 'storage/models/active_model.json'

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
    completion before switching the active model.
    """
    global transition_active
    
    logger.info("Started model transition monitoring thread")
    
    # Check current state first time
    username = free_text_collector.get_status().get("collector_status", {}).get("username", "unknown")
    initial_check = is_free_text_model_trained(free_text_model, username)
    if initial_check:
        logger.info("Free-text model already trained on startup, switching active model")
        switch_active_model("free-text")
    
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
                    
                    # Stop collection
                    free_text_collector.stop_free_text_collection()
                    
                    # Stop monitoring
                    transition_active = False
                    logger.info("Model transition complete: Switched to free-text model")
                    break
            
            # Second check: if model is trained regardless of collection status
            elif is_free_text_model_trained(free_text_model, username):
                logger.info("Free-text model is trained")
                
                # Switch the active model to free-text
                switch_active_model("free-text")
                
                # Stop collection if it's still active
                if status.get("collection_active", False):
                    free_text_collector.stop_free_text_collection()
                
                # Stop monitoring
                transition_active = False
                logger.info("Model transition complete: Switched to free-text model")
                break
            
            # Sleep for a bit before checking again
            time.sleep(10)
        
        except Exception as e:
            logger.error(f"Error in model transition monitoring thread: {str(e)}")
            time.sleep(30)  # Longer sleep on error
    
    logger.info("Model transition monitoring thread stopped")

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