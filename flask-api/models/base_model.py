# models/base_model.py
import os
import json
import logging
from datetime import datetime
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

logger = logging.getLogger(__name__)

class BaseModel:
    """Base class for all keystroke models"""
    
    def __init__(self, model_type):
        self.model_type = model_type
        self.model_path = f'storage/models/{model_type}_model.pkl'
        self.info_path = f'storage/models/{model_type}_info.json'
        self.model = None
        self._load_model()
        
    def _load_model(self):
        """Load model from disk if available"""
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                logger.info(f"Loaded {self.model_type} model from {self.model_path}")
            else:
                logger.info(f"No saved {self.model_type} model found")
        except Exception as e:
            logger.error(f"Error loading {self.model_type} model: {str(e)}")
            self.model = None
    
    def _save_model(self):
        """Save model to disk"""
        try:
            joblib.dump(self.model, self.model_path)
            logger.info(f"Saved {self.model_type} model to {self.model_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving {self.model_type} model: {str(e)}")
            return False
    
    def _save_info(self, info):
        """Save model metadata"""
        try:
            with open(self.info_path, 'w') as f:
                json.dump(info, f)
            logger.info(f"Saved {self.model_type} info to {self.info_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving {self.model_type} info: {str(e)}")
            return False
    
    def get_info(self):
        """Get model metadata"""
        try:
            if os.path.exists(self.info_path):
                with open(self.info_path, 'r') as f:
                    return json.load(f)
            return {
                'is_trained': False,
                'model_type': self.model_type
            }
        except Exception as e:
            logger.error(f"Error getting {self.model_type} info: {str(e)}")
            return {
                'is_trained': False,
                'model_type': self.model_type,
                'error': str(e)
            }
    
    def train(self, parameters):
        """Train the model - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement train()")
    
    def predict(self, data):
        """Make prediction - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement predict()")

