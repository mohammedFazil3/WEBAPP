# free_text_controller.py - Module for managing free text model switching
# This file should be placed in the flask-api/keystroke/ directory

import os
import json
import logging
import time
import threading
from datetime import datetime
import pandas as pd
import pickle

# Setup logging
logger = logging.getLogger(__name__)

# Global variables
STORAGE_DIR = "storage"
MODELS_DIR = os.path.join(STORAGE_DIR, "models")
ACTIVE_MODEL_FILE = os.path.join(MODELS_DIR, "active_model.json")

class FreeTextController:
    """Controller for managing free text model switching"""
    
    def __init__(self):
        self.monitoring_active = False
        self.monitor_thread = None
        self.free_text_target = 10000  # Target for free-text model training
        
    def start_monitoring(self, username="unknown"):
        """Start monitoring for free text model switching"""
        if self.monitoring_active:
            logger.warning("Free text model monitoring already active")
            return False
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_free_text_progress, args=(username,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info(f"Started free text model monitoring for user {username}")
        return True
    
    def stop_monitoring(self):
        """Stop monitoring for free text model switching"""
        if not self.monitoring_active:
            logger.warning("Free text model monitoring not active")
            return False
        
        self.monitoring_active = False
        logger.info("Stopped free text model monitoring")
        return True
    
    def _monitor_free_text_progress(self, username):
        """Background thread to monitor free text collection progress"""
        from keystroke.freetext_keystroke_collector import get_status, stop_free_text_collection
        from models import free_text_model
        
        logger.info(f"Monitoring free text progress for user {username}")
        
        while self.monitoring_active:
            try:
                # Get current status
                status = get_status()
                keystroke_count = status.get("keystroke_count", 0)
                
                # Check if we've reached the target
                if keystroke_count >= self.free_text_target:
                    logger.info(f"Free text collection reached target of {self.free_text_target} keystrokes")
                    
                    # Check if free text model exists and is trained
                    free_text = free_text_model.FreeTextModel()
                    model_info = free_text.get_info()
                    
                    # If model is not trained yet, train it
                    if not model_info.get('is_trained', False):
                        logger.info("Training free text model...")
                        
                        # Prepare parameters for training
                        parameters = {
                            'iterations': 100,
                            'learning_rate': 0.05,
                            'depth': 4,
                            'username': username
                        }
                        
                        # Train the model
                        result = free_text.train(parameters)
                        
                        if result.get('success', False):
                            logger.info(f"Free text model trained successfully with accuracy: {result.get('accuracy', 0)}")
                            
                            # Save a user-specific model
                            self._save_user_model(username, free_text)
                            
                            # Stop collection now that we have a trained model
                            logger.info("Stopping free text collection after successful training")
                            stop_free_text_collection()
                            
                            # Switch active model to free-text
                            self.switch_active_model('free-text', username)
                            logger.info(f"Switched active model to free-text for user {username}")
                            
                            # Stop monitoring as we're done
                            self.monitoring_active = False
                            break
                        else:
                            logger.error(f"Error training free text model: {result.get('error', 'Unknown error')}")
                    else:
                        # Model already trained, just switch active model
                        logger.info("Free text model already trained, switching active model")
                        self.switch_active_model('free-text', username)
                        logger.info(f"Switched active model to free-text for user {username}")
                        
                        # Stop monitoring as we're done
                        self.monitoring_active = False
                        break
            
            except Exception as e:
                logger.error(f"Error in free text model monitoring: {str(e)}")
            
            # Sleep for a bit
            time.sleep(10)
        
        logger.info("Free text model monitoring thread stopped")
    
    def _save_user_model(self, username, free_text_model):
        """Save a user-specific model"""
        try:
            # Check if model is loaded
            if not hasattr(free_text_model, 'model') or free_text_model.model is None:
                logger.error("Model not loaded, cannot save user-specific model")
                return False
            
            # Create user directory if it doesn't exist
            user_dir = os.path.join(MODELS_DIR, "free-text", username)
            os.makedirs(user_dir, exist_ok=True)
            
            # Save the model
            model_path = os.path.join(user_dir, "free-text_model.pkl")
            
            with open(model_path, 'wb') as f:
                pickle.dump(free_text_model.model, f)
            
            # Save info
            info_path = os.path.join(user_dir, "free-text_info.json")
            model_info = free_text_model.get_info()
            
            with open(info_path, 'w') as f:
                json.dump(model_info, f)
            
            logger.info(f"Saved user-specific free text model for {username} at {model_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving user-specific model: {str(e)}")
            return False
    
    def switch_active_model(self, model_type, username):
        """Switch the active model"""
        try:
            # Create active model data
            active_model = {
                'type': model_type,
                'username': username,
                'last_updated': datetime.now().isoformat()
            }
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(ACTIVE_MODEL_FILE), exist_ok=True)
            
            # Save to file
            with open(ACTIVE_MODEL_FILE, 'w') as f:
                json.dump(active_model, f)
            
            logger.info(f"Switched active model to {model_type} for user {username}")
            return True
        except Exception as e:
            logger.error(f"Error switching active model: {str(e)}")
            return False

# Create singleton instance
controller = FreeTextController()

# Helper functions to expose functionality
def start_model_monitoring(username="unknown"):
    """Start monitoring for free text model switching"""
    return controller.start_monitoring(username)

def stop_model_monitoring():
    """Stop monitoring for free text model switching"""
    return controller.stop_monitoring()

def switch_active_model(model_type, username):
    """Switch the active model"""
    return controller.switch_active_model(model_type, username)