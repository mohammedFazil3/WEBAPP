
# models/multi_binary_model.py
from models.base_model import BaseModel
import logging
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
from catboost import CatBoostClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

logger = logging.getLogger(__name__)

class MultiBinaryModel(BaseModel):
    """Multi-binary model implementation"""
    
    def __init__(self):
        super().__init__('multi-binary')
        self.data_path = 'storage/data/multi_binary_data.csv'
        self.users_path = 'storage/data/multi_binary_users.json'
        self.user_models = {}  # Dictionary to store individual user models
        
        # Initialize users file if it doesn't exist
        if not os.path.exists(self.users_path):
            self._init_users()
        else:
            self._load_user_models()
    
    def _init_users(self):
        """Initialize users file"""
        try:
            users = {
                'users': []
            }
            
            with open(self.users_path, 'w') as f:
                json.dump(users, f)
            
            logger.info("Initialized multi-binary users")
        except Exception as e:
            logger.error(f"Error initializing users: {str(e)}")
    
    def _load_user_models(self):
        """Load individual user models"""
        try:
            # Get users
            with open(self.users_path, 'r') as f:
                user_data = json.load(f)
            
            # Load each user's model
            for user in user_data.get('users', []):
                user_id = user.get('id')
                model_path = f'storage/models/multi_binary_{user_id}.pkl'
                
                if os.path.exists(model_path):
                    try:
                        self.user_models[user_id] = joblib.load(model_path)
                        logger.info(f"Loaded model for user {user_id}")
                    except Exception as e:
                        logger.error(f"Error loading model for user {user_id}: {str(e)}")
        except Exception as e:
            logger.error(f"Error loading user models: {str(e)}")
    
    def get_users(self):
        """Get all users for multi-binary model"""
        try:
            if os.path.exists(self.users_path):
                with open(self.users_path, 'r') as f:
                    return json.load(f).get('users', [])
            return []
        except Exception as e:
            logger.error(f"Error getting users: {str(e)}")
            return []
    
    def add_user(self, user_name):
        """Add a new user for multi-binary model"""
        try:
            # Load existing users
            with open(self.users_path, 'r') as f:
                user_data = json.load(f)
            
            # Check if user already exists
            for user in user_data.get('users', []):
                if user.get('name') == user_name:
                    return {
                        'success': False,
                        'error': f'User {user_name} already exists'
                    }
            
            # Add new user
            user_id = str(uuid.uuid4())
            new_user = {
                'id': user_id,
                'name': user_name,
                'is_trained': False,
                'created_at': datetime.now().isoformat()
            }
            
            user_data['users'].append(new_user)
            
            # Save updated users
            with open(self.users_path, 'w') as f:
                json.dump(user_data, f)
            
            logger.info(f"Added new user {user_name} with ID {user_id}")
            
            return {
                'success': True,
                'user': new_user
            }
        except Exception as e:
            logger.error(f"Error adding user: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def train(self, parameters):
        """Train the multi-binary model"""
        try:
            # Get target user ID
            user_id = parameters.get('user_id')
            if not user_id:
                logger.error("No user_id provided for multi-binary model training")
                return {
                    'success': False,
                    'error': 'No user_id provided'
                }
            
            # Check if user exists
            users = self.get_users()
            target_user = None
            for user in users:
                if user.get('id') == user_id:
                    target_user = user
                    break
            
            if not target_user:
                logger.error(f"User {user_id} not found")
                return {
                    'success': False,
                    'error': f'User {user_id} not found'
                }
            
            # Check if training data exists
            if not os.path.exists(self.data_path):
                logger.error("No training data found for multi-binary model")
                return {
                    'success': False,
                    'error': 'No training data found'
                }
            
            # Load the data
            df = pd.read_csv(self.data_path)
            
            # Filter data for this user
            # We'll create a binary classification problem for this user
            # 1 = this user, 0 = any other user
            df['is_user'] = df['user_id'].apply(lambda x: 1 if x == user_id else 0)
            
            # Prepare features and target
            X = df.drop(columns=['user_id', 'is_user'])
            y = df['is_user']
            
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
            
            # Create model for this user
            user_model = CatBoostClassifier(**model_params)
            
            # Train the model
            user_model.fit(X_train, y_train)
            
            # Evaluate the model
            y_pred = user_model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            report = classification_report(y_test, y_pred, output_dict=True)
            
            # Save user model
            user_model_path = f'storage/models/multi_binary_{user_id}.pkl'
            joblib.dump(user_model, user_model_path)
            
            # Store model in memory
            self.user_models[user_id] = user_model
            
            # Update user info
            with open(self.users_path, 'r') as f:
                user_data = json.load(f)
            
            for user in user_data.get('users', []):
                if user.get('id') == user_id:
                    user['is_trained'] = True
                    user['last_trained'] = datetime.now().isoformat()
                    user['accuracy'] = accuracy
                    break
            
            with open(self.users_path, 'w') as f:
                json.dump(user_data, f)
            
            # Update main model info
            info = self.get_info()
            if not info.get('users'):
                info['users'] = {}
            
            info['users'][user_id] = {
                'is_trained': True,
                'accuracy': accuracy,
                'last_trained': datetime.now().isoformat()
            }
            
            info['is_trained'] = any(user.get('is_trained', False) for user in user_data.get('users', []))
            info['last_updated'] = datetime.now().isoformat()
            
            self._save_info(info)
            
            return {
                'success': True,
                'user_id': user_id,
                'accuracy': accuracy,
                'report': report
            }
        except Exception as e:
            logger.error(f"Error training multi-binary model: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def predict(self, data):
        """Make prediction with multi-binary model"""
        try:
            # Get users
            users = self.get_users()
            
            # Check if at least one user model is trained
            if not self.user_models:
                logger.error("No trained user models found")
                return {
                    'success': False,
                    'error': 'No trained user models found'
                }
            
            results = {}
            max_confidence = 0
            identified_user = None
            
            # Test against each user model
            for user_id, model in self.user_models.items():
                try:
                    # Make prediction
                    prediction = model.predict(data)
                    prediction_proba = model.predict_proba(data)
                    
                    # Calculate confidence
                    is_user = bool(prediction[0] == 1)  # 1 = this user
                    confidence = prediction_proba[0][1]  # Confidence for being this user
                    
                    results[user_id] = {
                        'is_user': is_user,
                        'confidence': float(confidence)
                    }
                    
                    # Track the user with highest confidence
                    if is_user and confidence > max_confidence:
                        max_confidence = confidence
                        identified_user = user_id
                except Exception as e:
                    logger.error(f"Error predicting with model for user {user_id}: {str(e)}")
            
            # Check if any user was identified
            is_anomaly = (identified_user is None)
            
            # Map user ID to name if found
            identified_user_name = None
            if identified_user:
                for user in users:
                    if user.get('id') == identified_user:
                        identified_user_name = user.get('name')
                        break
            
            return {
                'success': True,
                'is_anomaly': is_anomaly,
                'identified_user': identified_user,
                'identified_user_name': identified_user_name,
                'confidence': float(max_confidence) if not is_anomaly else 0.0,
                'results': results
            }
        except Exception as e:
            logger.error(f"Error predicting with multi-binary model: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }