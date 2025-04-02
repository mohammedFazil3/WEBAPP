
# models/free_text_model.py
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
    
    def __init__(self):
        super().__init__('free-text')
        self.data_path = 'storage/data/free_text_data.csv'
        self.collection_path = 'storage/data/keystroke_collection.json'
        
        # Initialize collection status file if it doesn't exist
        if not os.path.exists(self.collection_path):
            self._init_collection_status()
    
    def _init_collection_status(self):
        """Initialize keystroke collection status"""
        try:
            collection_status = {
                'total_collected': 0,
                'target': 10000,
                'last_updated': datetime.now().isoformat(),
                'is_ready': False
            }
            
            with open(self.collection_path, 'w') as f:
                json.dump(collection_status, f)
            
            logger.info("Initialized keystroke collection status")
        except Exception as e:
            logger.error(f"Error initializing collection status: {str(e)}")
    
    def get_collection_status(self):
        """Get keystroke collection status"""
        try:
            if os.path.exists(self.collection_path):
                with open(self.collection_path, 'r') as f:
                    return json.load(f)
            else:
                self._init_collection_status()
                with open(self.collection_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error getting collection status: {str(e)}")
            return {
                'error': str(e),
                'total_collected': 0,
                'target': 10000,
                'is_ready': False
            }
    
    def add_keystrokes(self, keystroke_data):
        """Add keystrokes to collection"""
        try:
            # Get current collection status
            collection_status = self.get_collection_status()
            
            # Update the count
            current_count = collection_status['total_collected']
            new_count = current_count + len(keystroke_data)
            
            # Update the status
            collection_status['total_collected'] = new_count
            collection_status['last_updated'] = datetime.now().isoformat()
            collection_status['is_ready'] = new_count >= collection_status['target']
            
            # Save the updated status
            with open(self.collection_path, 'w') as f:
                json.dump(collection_status, f)
            
            # Append the keystroke data to the data file
            # (In a real implementation, this would process and store the actual keystrokes)
            
            return {
                'success': True,
                'new_count': new_count,
                'is_ready': collection_status['is_ready']
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
            if not collection_status['is_ready']:
                logger.error("Not enough keystroke data collected for free-text model")
                return {
                    'success': False,
                    'error': 'Not enough keystroke data collected',
                    'collected': collection_status['total_collected'],
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
                'iterations': parameters.get('iterations', 100),
                'learning_rate': parameters.get('learning_rate', 0.05),
                'depth': parameters.get('depth', 4),
                'loss_function': 'Logloss',
                'auto_class_weights': 'Balanced',
                'random_seed': 42,
                'verbose': 100
            }
            
            self.model = CatBoostClassifier(**model_params)
            
            # Train the model
            self.model.fit(X_train, y_train)
            
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
