# models/multi_binary_model.py
"""
Multi-binary model implementation based on the MultiBinaryClassifier approach.
This version integrates the MultiBinaryClassifier from the notebook with the Flask API structure.
"""

import uuid
import os
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime
import joblib
import pickle
from catboost import CatBoostClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

from models.base_model import BaseModel

logger = logging.getLogger(__name__)

class MultiBinaryClassifier:
    def __init__(self, models, names=None):
        """
        Initialize with multiple binary classifiers.

        Args:
            models: List of binary classifier models (CatBoost models)
            names: Optional list of model/class names
        """
        self.models = models
        if names is None:
            self.names = [f"Class_{i}" for i in range(len(models))]
        else:
            self.names = names

    def predict(self, X, min_confidence=0.5):
        """
        Predict class for input data using ensemble of binary classifiers.
        Includes "Unknown" class when no model meets minimum confidence.

        Args:
            X: Input features
            min_confidence: Threshold for minimum confidence to accept a prediction

        Returns:
            predicted_classes: List of predicted class names (including "Unknown")
            probabilities: Dict of probabilities for each class
        """
        # Get probabilities from each model
        probabilities = {}

        for i, model in enumerate(self.models):
            # CatBoost models support predict_proba
            try:
                # Get probability of positive class (class 1)
                probs = model.predict_proba(X)
                pos_probs = probs[:, 1]  # Second column contains positive class probabilities
            except IndexError:
                # Handle case where predict_proba returns only one column
                pos_probs = model.predict_proba(X)
            except Exception as e:
                # Fallback to raw predictions if predict_proba fails
                logger.warning(f"Warning: predict_proba failed for model {self.names[i]}, using predict: {e}")
                preds = model.predict(X)
                pos_probs = np.array(preds, dtype=float)

            probabilities[self.names[i]] = pos_probs

        # Make predictions based on highest probability
        predicted_classes = []

        # For each sample
        for i in range(len(next(iter(probabilities.values())))):
            max_prob = -1
            predicted_class = "Unknown"  # Default to Unknown

            # Find class with highest probability
            for class_name, probs in probabilities.items():
                if probs[i] > max_prob:
                    max_prob = probs[i]
                    predicted_class = class_name

            # Check if the confidence meets the minimum threshold
            if max_prob < min_confidence:
                predicted_class = "Unknown"

            predicted_classes.append(predicted_class)

        return predicted_classes, probabilities


class MultiBinaryModel(BaseModel):
    """
    Multi-binary model implementation that uses the MultiBinaryClassifier approach.
    This maintains compatibility with the Flask API structure while using the
    ensemble classifier from the notebook.
    """
    
    def __init__(self, username=None):
        super().__init__('multi-binary', username)
        
        # Set up paths for data and model storage
        self.data_path = 'flask-api/storage/data/multi_binary_data.csv'
        self.users_path = 'flask-api/storage/data/multi_binary_users.json'
        self.classifier_path = 'flask-api/storage/models/multi_binary_classifier.pkl'
        
        # Individual user models
        self.user_models = {}
        
        # Initialize users file if it doesn't exist
        if not os.path.exists(self.users_path):
            self._init_users()
            
        # Load existing user models
        self._load_user_models()
        
        # Load or initialize the MultiBinaryClassifier
        self.classifier = self._load_classifier()
    
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
            if not os.path.exists(self.users_path):
                return
                
            with open(self.users_path, 'r') as f:
                user_data = json.load(f)
            
            # Load each user's model
            for user in user_data.get('users', []):
                user_id = user.get('id')
                user_name = user.get('name')
                model_path = f'flask-api/storage/models/multi_binary_{user_id}.pkl'
                
                if os.path.exists(model_path):
                    try:
                        self.user_models[user_id] = joblib.load(model_path)
                        logger.info(f"Loaded model for user {user_name} (ID: {user_id})")
                    except Exception as e:
                        logger.error(f"Error loading model for user {user_name} (ID: {user_id}): {str(e)}")
        except Exception as e:
            logger.error(f"Error loading user models: {str(e)}")
    
    def _load_classifier(self):
        """Load the MultiBinaryClassifier or create a new one"""
        try:
            if os.path.exists(self.classifier_path):
                # Load existing classifier
                with open(self.classifier_path, 'rb') as f:
                    classifier = pickle.load(f)
                logger.info("Loaded existing MultiBinaryClassifier")
                return classifier
            else:
                # Check if we have user models to create a new classifier
                if not self.user_models:
                    logger.info("No user models available to create MultiBinaryClassifier")
                    return None
                
                # Create new classifier from user models
                models = []
                names = []
                
                for user_id, model in self.user_models.items():
                    models.append(model)
                    
                    # Get user name from users file
                    user_name = None
                    with open(self.users_path, 'r') as f:
                        user_data = json.load(f)
                        for user in user_data.get('users', []):
                            if user.get('id') == user_id:
                                user_name = user.get('name')
                                break
                    
                    names.append(user_name if user_name else f"User_{user_id}")
                
                # Create and save new classifier
                classifier = MultiBinaryClassifier(models=models, names=names)
                with open(self.classifier_path, 'wb') as f:
                    pickle.dump(classifier, f)
                
                logger.info(f"Created new MultiBinaryClassifier with {len(models)} models")
                return classifier
        except Exception as e:
            logger.error(f"Error loading/creating MultiBinaryClassifier: {str(e)}")
            return None
    
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
        """
        Train the multi-binary model for a specific user while including ALL trained free-text models.
        
        Args:
            parameters: Dictionary with training parameters including 'user_id'
            
        Returns:
            Dictionary with training results
        """
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
            
            # Use free-text model for this user if available
            user_name = target_user.get('name')
            logger.info(f"Training multi-binary model for user {user_name} (ID: {user_id})")
            
            # Import free-text model for this user
            from models.free_text_model import FreeTextModel
            free_text_model = FreeTextModel(user_name)
            
            # Check if free-text model is trained
            free_text_info = free_text_model.get_info()
            if not free_text_info.get('is_trained', False):
                logger.error(f"Free-text model for user {user_name} is not trained yet")
                return {
                    'success': False,
                    'error': f'Free-text model for user {user_name} is not trained yet'
                }
            
            # Load the free-text model
            free_text_model._load_model()
            if free_text_model.model is None:
                logger.error(f"Failed to load free-text model for user {user_name}")
                return {
                    'success': False,
                    'error': f'Failed to load free-text model for user {user_name}'
                }
            
            # Save as individual user model
            model_path = f'flask-api/storage/models/multi_binary_{user_id}.pkl'
            joblib.dump(free_text_model.model, model_path)
            
            # Add to user_models dictionary
            self.user_models[user_id] = free_text_model.model
            
            # Update user info
            with open(self.users_path, 'r') as f:
                user_data = json.load(f)
            
            for user in user_data.get('users', []):
                if user.get('id') == user_id:
                    user['is_trained'] = True
                    user['last_trained'] = datetime.now().isoformat()
                    user['model_path'] = model_path
                    break
            
            with open(self.users_path, 'w') as f:
                json.dump(user_data, f)
            
            # CRITICAL: Scan for ALL trained free-text models
            # This ensures we include ALL users with trained models
            
            # 1. Get all users in the system (whether trained or not)
            all_users = user_data.get('users', [])
            user_id_to_name = {user.get('id'): user.get('name') for user in all_users}
            
            # 2. Create a mapping of username to user ID
            username_to_id = {}
            for user in all_users:
                username_to_id[user.get('name')] = user.get('id')
            
            # 3. Scan the free-text directory to find all trained models
            import os
            import glob
            
            free_text_dir = 'flask-api/storage/models/free-text'
            logger.info(f"Scanning for trained free-text models in {free_text_dir}")
            
            # Look for all usernames with trained models
            trained_usernames = []
            
            # Check for user subdirectories
            for item in os.listdir(free_text_dir):
                user_dir = os.path.join(free_text_dir, item)
                if os.path.isdir(user_dir):
                    # Check if this directory has a trained model
                    model_file = os.path.join(user_dir, 'free-text_model.pkl')
                    info_file = os.path.join(user_dir, 'free-text_info.json')
                    
                    if os.path.exists(model_file) and os.path.exists(info_file):
                        # Verify it's actually trained by checking the info file
                        try:
                            with open(info_file, 'r') as f:
                                info = json.load(f)
                                if info.get('is_trained', False):
                                    trained_usernames.append(item)
                                    logger.info(f"Found trained model for user: {item}")
                        except Exception as e:
                            logger.warning(f"Error reading info file for {item}: {str(e)}")
            
            logger.info(f"Found trained models for users: {trained_usernames}")
            
            # 4. Build comprehensive list of models and names
            models = []
            names = []
            included_users = []
            
            # Include all users with trained models
            for username in trained_usernames:
                if username not in username_to_id:
                    print(f"User {username} has a trained model but is not in registry. Adding to registry...")
                    try:
                        # Add user to registry
                        with open(self.users_path, 'r') as f:
                            users_data = json.load(f)
                        
                        # Generate new user ID
                        new_id = str(uuid.uuid4())
                        
                        # Create new user entry with standardized fields
                        new_user = {
                            'id': new_id,
                            'name': username,
                            'is_trained': True,  # Changed from model_trained to is_trained
                            'created_at': datetime.now().isoformat(),  # Changed from added_date to created_at
                            'last_trained': datetime.now().isoformat(),
                            'model_path': f'flask-api/storage/models/multi_binary_{new_id}.pkl'
                        }
                        
                        # Add to users list
                        users_data['users'].append(new_user)
                        users_data['total_users'] = len(users_data['users'])
                        users_data['last_updated'] = datetime.now().isoformat()
                        
                        # Save updated registry
                        with open(self.users_path, 'w') as f:
                            json.dump(users_data, f, indent=4)
                            
                        # Update the username_to_id mapping
                        username_to_id[username] = new_id
                        print(f"Successfully added user {username} to registry with ID: {new_id}")
                        
                    except Exception as e:
                        print(f"Error adding user {username} to registry: {str(e)}")
                        continue
                
                # Load and add the model for this user
                try:
                    # Create FreeTextModel instance for this user
                    from models.free_text_model import FreeTextModel
                    user_free_text_model = FreeTextModel(username)
                    
                    # Load the model
                    user_free_text_model._load_model()
                    if user_free_text_model.model is not None:
                        # Add to our lists
                        models.append(user_free_text_model.model)
                        names.append(username)
                        included_users.append(username)
                        print(f"Successfully loaded and added model for user: {username}")
                        
                        # Save as individual user model in multi-binary format
                        user_id = username_to_id[username]
                        model_path = f'flask-api/storage/models/multi_binary_{user_id}.pkl'
                        joblib.dump(user_free_text_model.model, model_path)
                        self.user_models[user_id] = user_free_text_model.model
                    else:
                        print(f"Failed to load model for user: {username}")
                except Exception as e:
                    print(f"Error loading model for user {username}: {str(e)}")
                    continue
            
            if not models:
                logger.error("No trained models available for multi-binary classifier")
                return {
                    'success': False,
                    'error': 'No trained models available'
                }
            
            # Create and save new classifier with ALL user models
            logger.info(f"Creating MultiBinaryClassifier with {len(models)} models for users: {names}")
            self.classifier = MultiBinaryClassifier(models=models, names=names)
            with open(self.classifier_path, 'wb') as f:
                pickle.dump(self.classifier, f)
            
            # Update model info
            info = self.get_info()
            info['is_trained'] = True
            info['last_updated'] = datetime.now().isoformat()
            info['users'] = names
            info['model_count'] = len(models)
            info['confidence_threshold'] = parameters.get('confidence_threshold', 0.6)
            self._save_info(info)
            
            return {
                'success': True,
                'message': f'Successfully trained multi-binary model with ALL available users',
                'user_id': user_id,
                'user_name': user_name,
                'total_models': len(models),
                'users': names
            }
        except Exception as e:
            logger.error(f"Error training multi-binary model: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def predict(self, data, min_confidence=0.5):
        """
        Make prediction with multi-binary classifier
        
        Args:
            data: Input features
            min_confidence: Minimum confidence threshold
            
        Returns:
            Dictionary with prediction results
        """
        try:
            # Check if classifier is available
            if self.classifier is None:
                logger.error("No MultiBinaryClassifier available for prediction")
                return {
                    'success': False,
                    'error': 'Model is not trained yet'
                }
            
            # Get prediction
            predicted_classes, probabilities = self.classifier.predict(data, min_confidence=min_confidence)
            
            # Get the prediction for the first sample (usually there's only one)
            predicted_class = predicted_classes[0] if predicted_classes else "Unknown"
            
            # Determine if this is an anomaly
            is_anomaly = (predicted_class == "Unknown")
            
            # Get confidence for each class
            confidence_values = {}
            max_confidence = 0
            
            for class_name, probs in probabilities.items():
                confidence = float(probs[0]) if len(probs) > 0 else 0
                confidence_values[class_name] = confidence
                
                if confidence > max_confidence:
                    max_confidence = confidence
            
            # Create response
            return {
                'success': True,
                'predicted_user': predicted_class,
                'is_anomaly': is_anomaly,
                'confidence': max_confidence if not is_anomaly else 0,
                'all_confidences': confidence_values
            }
        except Exception as e:
            logger.error(f"Error predicting with multi-binary model: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }