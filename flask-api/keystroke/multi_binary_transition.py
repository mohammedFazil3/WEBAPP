# keystroke/multi_binary_transition.py
"""
Module for handling transition from free-text model training to multi-binary model.
This module monitors the free-text collection and training progress for new users,
then updates the multi-binary model and switches the active model when ready.
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

def init_multi_binary_transition(free_text_collector, username, user_id):
    """Initialize transition monitoring for multi-binary model."""
    global transition_active, transition_thread
    
    if transition_active:
        logger.warning("Multi-binary transition monitoring already active")
        return False, "Multi-binary transition monitoring is already active"
    
    try:
        # Activate monitoring
        transition_active = True
        
        # Start background monitoring thread
        if transition_thread is None or not transition_thread.is_alive():
            transition_thread = threading.Thread(
                target=monitor_multi_binary_transition,
                args=(free_text_collector, username, user_id)
            )
            transition_thread.daemon = True
            transition_thread.start()
        
        logger.info(f"Started multi-binary transition monitoring for user {username}")
        return True, "Multi-binary transition monitoring started successfully"
    
    except Exception as e:
        error_msg = f"Error starting multi-binary transition monitoring: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def stop_multi_binary_transition():
    """Stop monitoring for multi-binary transition."""
    global transition_active
    
    if not transition_active:
        logger.warning("Multi-binary transition monitoring not active")
        return False, "Multi-binary transition monitoring is not active"
    
    try:
        # Deactivate monitoring
        transition_active = False
        
        logger.info("Stopped multi-binary transition monitoring")
        return True, "Multi-binary transition monitoring stopped successfully"
    
    except Exception as e:
        error_msg = f"Error stopping multi-binary transition monitoring: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def is_free_text_model_trained(username):
    """Check if the free-text model for a user has been trained."""
    try:
        # Check for model files in user-specific directory
        user_model_dir = os.path.join('flask-api/storage/models/free-text', username)
        if os.path.exists(user_model_dir):
            model_files = glob.glob(os.path.join(user_model_dir, 'free-text_model.*'))
            if model_files:
                logger.info(f"Found free-text model files for user {username}: {model_files}")
                return True
                
        # Check for model files in general models directory
        models_dir = os.path.join('flask-api/storage/models/free-text')
        if os.path.exists(models_dir):
            model_files = glob.glob(os.path.join(models_dir, f'{username}_free-text_model.*'))
            if model_files:
                logger.info(f"Found free-text model files for user {username}: {model_files}")
                return True
        
        logger.info(f"No free-text model files found for user {username}, assuming not trained yet")
        return False
        
    except Exception as e:
        logger.error(f"Error checking if free-text model is trained for user {username}: {str(e)}")
        return False

def monitor_multi_binary_transition(free_text_collector, username, user_id):
    """
    Background thread to monitor free-text model training status for a new user
    and integrate it into the multi-binary model when ready.
    """
    global transition_active
    
    logger.info(f"Started multi-binary transition monitoring thread for user {username}")
    
    # Progress file path
    progress_file = f'flask-api/storage/models/multi-binary/progress/{username}.json'
    
    # Monitor loop
    while transition_active:
        try:
            # Check if progress file exists
            if not os.path.exists(progress_file):
                logger.error(f"Progress file for user {username} not found")
                time.sleep(30)
                continue
            
            # Load progress
            with open(progress_file, 'r') as f:
                progress = json.load(f)
            
            # Get collection status
            status = free_text_collector.get_status()
            
            # First check: if collection is complete but model not trained
            if (status.get("free_text_progress", {}).get("complete", False) and 
                not progress.get("model_trained", False)):
                
                logger.info(f"Keystroke threshold reached for user {username}, waiting for training to complete")
                
                # Wait for free-text model to be trained
                time.sleep(30)
                
                # Check if free-text model is now trained
                if is_free_text_model_trained(username):
                    logger.info(f"Free-text model for user {username} is now trained")
                    
                    # Update progress
                    progress["model_trained"] = True
                    progress["training_complete"] = datetime.now().isoformat()
                    
                    with open(progress_file, 'w') as f:
                        json.dump(progress, f)
                    
                    # Now train the multi-binary model with this user's data
                    from models import multi_binary_model
                    mb_model = multi_binary_model.MultiBinaryModel()
                    
                    # Set parameters for MultiBinaryClassifier
                    parameters = {
                        "user_id": user_id,
                        "confidence_threshold": 0.6  # Default confidence threshold
                    }
                    
                    # Train model for this user
                    train_result = mb_model.train(parameters)
                    
                    if train_result.get("success", False):
                        logger.info(f"Successfully trained multi-binary model for user {username}")
                        logger.info(f"Model now includes users: {train_result.get('users', [])}")
                        
                        # Update progress
                        progress["multi_binary_trained"] = True
                        progress["multi_binary_training_complete"] = datetime.now().isoformat()
                        progress["users_in_model"] = train_result.get('users', [])
                        
                        with open(progress_file, 'w') as f:
                            json.dump(progress, f)
                        
                        # Switch active model to multi-binary
                        switch_active_model("multi-binary")
                        
                        # Stop collection if it's still active
                        if status.get("collection_active", False):
                            free_text_collector.stop_free_text_collection()
                        
                        # Stop transition monitoring
                        transition_active = False
                        logger.info(f"Multi-binary model transition complete for user {username}")
                        break
                    else:
                        logger.error(f"Error training multi-binary model for user {username}: {train_result.get('error')}")
            
            # Second check: if free-text model is trained but multi-binary not updated
            elif (progress.get("model_trained", False) and 
                  not progress.get("multi_binary_trained", False)):
                
                logger.info(f"Free-text model is trained for user {username}, updating multi-binary model")
                
                # Train the multi-binary model with this user's data
                from models import multi_binary_model
                mb_model = multi_binary_model.MultiBinaryModel()
                
                # Set parameters for MultiBinaryClassifier
                parameters = {
                    "user_id": user_id,
                    "confidence_threshold": 0.6  # Default confidence threshold
                }
                
                train_result = mb_model.train(parameters)
                
                if train_result.get("success", False):
                    logger.info(f"Successfully trained multi-binary model for user {username}")
                    logger.info(f"Model now includes users: {train_result.get('users', [])}")
                    
                    # Update progress
                    progress["multi_binary_trained"] = True
                    progress["multi_binary_training_complete"] = datetime.now().isoformat()
                    progress["users_in_model"] = train_result.get('users', [])
                    
                    with open(progress_file, 'w') as f:
                        json.dump(progress, f)
                    
                    # Switch active model to multi-binary
                    switch_active_model("multi-binary")
                    
                    # Stop collection if it's still active
                    if status.get("collection_active", False):
                        free_text_collector.stop_free_text_collection()
                    
                    # Stop transition monitoring
                    transition_active = False
                    logger.info(f"Multi-binary model transition complete for user {username}")
                    break
                else:
                    logger.error(f"Error training multi-binary model for user {username}: {train_result.get('error')}")
            
            # Sleep for a bit before checking again
            time.sleep(30)
        
        except Exception as e:
            logger.error(f"Error in multi-binary transition monitoring thread: {str(e)}")
            time.sleep(30)  # Longer sleep on error
    
    logger.info(f"Multi-binary transition monitoring thread stopped for user {username}")

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