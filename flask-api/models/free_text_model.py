# models/free_text_model.py
import json
from models.base_model import BaseModel
import logging
import os
import pandas as pd
import numpy as np
from datetime import datetime
from catboost import CatBoostClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

logger = logging.getLogger(__name__)

class FreeTextModel(BaseModel):
    """Free text model implementation"""
    
    def __init__(self, username):
        """Initialize the free-text model."""
        super().__init__('free-text', username)
        self.data_path = 'flask-api/storage/data/free_text_data.csv'
        self.collection_path = 'flask-api/storage/data/keystroke_collection.json'
        self.model = None
        self.is_trained = False
        self.collection_status = {
            "active": False,
            "username": username,
            "keystroke_count": 0,
            "target": 10000,
            "percentage": 0,
            "last_updated": None
        }
        self._initialize_collection_status()
    
    def _initialize_collection_status(self):
        """Initialize the collection status file."""
        try:
            # Ensure the storage directory exists
            os.makedirs(os.path.dirname(self.collection_path), exist_ok=True)
            
            # Check if the file exists
            if not os.path.exists(self.collection_path):
                # Create the file with initial status
                with open(self.collection_path, 'w') as f:
                    json.dump(self.collection_status, f)
            else:
                # Load existing status
                with open(self.collection_path, 'r') as f:
                    self.collection_status = json.load(f)
        except Exception as e:
            logger.error(f"Error initializing collection status: {str(e)}")
            # Create a new file with default status if there was an error
            try:
                with open(self.collection_path, 'w') as f:
                    json.dump(self.collection_status, f)
            except Exception as e2:
                logger.error(f"Error creating collection status file: {str(e2)}")
    
    def get_collection_status(self):
        """Get the current collection status."""
        try:
            if os.path.exists(self.collection_path):
                with open(self.collection_path, 'r') as f:
                    return json.load(f)
            return self.collection_status
        except Exception as e:
            logger.error(f"Error getting collection status: {str(e)}")
            return self.collection_status
    
    def add_keystrokes(self, keystroke_data):
        """Add keystrokes to collection"""
        try:
            # Get current collection status
            collection_status = self.get_collection_status()
            
            # Update the count and percentage
            current_count = collection_status['keystroke_count']
            new_count = current_count + len(keystroke_data)
            percentage = min(100, round((new_count / collection_status['target']) * 100, 1))
            
            # Update the status
            collection_status['keystroke_count'] = new_count
            collection_status['percentage'] = percentage
            collection_status['last_updated'] = datetime.now().isoformat()
            
            # Save the updated status
            with open(self.collection_path, 'w') as f:
                json.dump(collection_status, f)
            
            # Update in-memory status
            self.collection_status = collection_status
            
            return {
                'success': True,
                'new_count': new_count,
                'percentage': percentage,
                'is_ready': new_count >= collection_status['target']
            }
        except Exception as e:
            logger.error(f"Error adding keystrokes: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def train(self, parameters):
        """Train the free text model"""
        try:
            # Check if enough data has been collected
            collection_status = self.get_collection_status()
            if collection_status['keystroke_count'] < collection_status['target']:
                logger.error("Not enough keystroke data collected for free-text model")
                return {
                    'success': False,
                    'error': 'Not enough keystroke data collected',
                    'collected': collection_status['keystroke_count'],
                    'target': collection_status['target']
                }
            
            # Check if training data exists
            if not os.path.exists(self.data_path):
                logger.error("No training data found for free-text model")
                return {
                    'success': False,
                    'error': 'No training data found'
                }
            
            # Load the data
            df = pd.read_csv(self.data_path)
            
            # Check if label column exists
            if 'label' not in df.columns:
                logger.error("Label column not found in training data")
                return {
                    'success': False,
                    'error': 'Label column not found in training data'
                }
            
            # Prepare features and target
            X = df.drop(columns=['label'])
            y = df['label']
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Create CatBoost classifier with parameters
            model_params = {
                'early_stopping_rounds': 150,
                'use_best_model': True,
                'eval_metric': 'Accuracy',
                'custom_metric': ['Recall','F1'],
                'iterations': parameters.get('iterations', 2500),
                'learning_rate': parameters.get('learning_rate', 0.01),
                'depth': parameters.get('depth', 7),
                'l2_leaf_reg': parameters.get('l2_leaf_reg', 4),
                'random_seed': 42
            }
            
            self.model = CatBoostClassifier(**model_params)
            
            # Train the model
            self.model.fit(X_train, y_train,eval_set=[(X_test, y_test)])
            
            # Evaluate the model
            y_pred = self.model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            report = classification_report(y_test, y_pred, output_dict=True)
            
            # Save model and info
            self._save_model()
            
            # Save model metadata
            info = {
                'is_trained': True,
                'model_type': self.model_type,
                'parameters': model_params,
                'accuracy': accuracy,
                'report': report,
                'last_trained': datetime.now().isoformat(),
                'feature_count': X.shape[1],
                'training_samples': X_train.shape[0],
                'test_samples': X_test.shape[0]
            }
            self._save_info(info)
            
            return {
                'success': True,
                'accuracy': accuracy,
                'report': report
            }
        except Exception as e:
            logger.error(f"Error training free-text model: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def predict(self, data):
        """Make prediction with free text model"""
        try:
            # Check if model is trained
            if self.model is None:
                logger.error("Free-text model is not trained yet")
                return {
                    'success': False,
                    'error': 'Model is not trained yet'
                }
            
            # Preprocess the input data to match training data format
            # Assume data is already preprocessed to match the expected format
            
            # Make prediction
            prediction = self.model.predict(data)
            prediction_proba = self.model.predict_proba(data)
            
            # Determine if this is an anomaly (non-authorized user)
            is_anomaly = bool(prediction[0] == 0)  # Assuming 0 = unauthorized
            
            # Calculate confidence
            confidence = prediction_proba[0][prediction[0]]
            
            return {
                'success': True,
                'prediction': int(prediction[0]),
                'confidence': float(confidence),
                'is_anomaly': is_anomaly,
                'prediction_proba': prediction_proba[0].tolist()
            }
        except Exception as e:
            logger.error(f"Error predicting with free-text model: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
