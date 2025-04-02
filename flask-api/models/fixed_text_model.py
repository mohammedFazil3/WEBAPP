# models/fixed_text_model.py
from models.base_model import BaseModel
import logging
import os
import pandas as pd
import numpy as np
from datetime import datetime
from catboost import CatBoostClassifier, Pool
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

logger = logging.getLogger(__name__)

class FixedTextModel(BaseModel):
    """Fixed text model implementation"""
    
    def __init__(self):
        super().__init__('fixed-text')
        self.data_path = 'storage/data/fixed_text_data_preprocessed.csv'
    
    def train(self, parameters=None):
        """Train the model with the given parameters"""
        try:
            # Check if training data exists
            if not os.path.exists(self.data_path):
                logger.error("No training data found for fixed-text model")
                return {
                    'success': False,
                    'error': 'No training data found'
                }
            
            # Load the data
            df = pd.read_csv(self.data_path)
            
            # Check if label column exists
            if 'User' not in df.columns:
                logger.error("Label column not found in training data")
                return {
                    'success': False,
                    'error': 'Label column not found in training data'
                }
            
            # Prepare features and target
            X = df.drop(columns=['User'])
            y = df['User']

            # Encoding y
            first_user = y.iloc[0]  # Get the first user
            y = (y == first_user).astype(int)  # Convert to binary (1 for first user, 0 for others)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Initialize training pool
            train_pool = Pool(X_train, y_train)
            test_pool = Pool(X_test, y_test)

            # Set default parameters if none provided
            if parameters is None:
                parameters = {
                    'iterations': 100,
                    'depth': 6,
                    'learning_rate': 0.1,
                    'loss_function': 'Logloss',
                    'eval_metric': 'AUC',
                    'random_seed': 42
                }
            
            # Create CatBoost classifier with parameters
            self.model = CatBoostClassifier(**parameters)
            
            # Train the model
            self.model.fit(train_pool)
            
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
                'parameters': parameters,
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
            logger.error(f"Error training fixed-text model: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def predict(self, data):
        """Make prediction with fixed text model"""
        try:
            # Check if model is trained
            if self.model is None:
                logger.error("Fixed-text model is not trained yet")
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
            logger.error(f"Error predicting with fixed-text model: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
