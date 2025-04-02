# utils/data_handler.py
import os
import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def save_training_data(data, model_type, user_id=None):
    """
    Save processed training data to appropriate file
    
    Args:
        data (pd.DataFrame): Processed data to save
        model_type (str): Model type (fixed-text, free-text, multi-binary)
        user_id (str, optional): User ID for multi-binary model
        
    Returns:
        bool: Success status
    """
    try:
        if model_type == 'fixed-text':
            file_path = 'storage/data/fixed_text_data.csv'
        elif model_type == 'free-text':
            file_path = 'storage/data/free_text_data.csv'
        elif model_type == 'multi-binary':
            if user_id:
                file_path = f'storage/data/multi_binary_{user_id}_data.csv'
            else:
                file_path = 'storage/data/multi_binary_data.csv'
        else:
            logger.error(f"Invalid model type: {model_type}")
            return False
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save the data
        data.to_csv(file_path, index=False)
        logger.info(f"Saved training data to {file_path}")
        
        return True
    except Exception as e:
        logger.error(f"Error saving training data: {str(e)}")
        return False

def load_training_data(model_type, user_id=None):
    """
    Load training data from file
    
    Args:
        model_type (str): Model type (fixed-text, free-text, multi-binary)
        user_id (str, optional): User ID for multi-binary model
        
    Returns:
        pd.DataFrame: Loaded data or None if file doesn't exist
    """
    try:
        if model_type == 'fixed-text':
            file_path = 'storage/data/fixed_text_data.csv'
        elif model_type == 'free-text':
            file_path = 'storage/data/free_text_data.csv'
        elif model_type == 'multi-binary':
            if user_id:
                file_path = f'storage/data/multi_binary_{user_id}_data.csv'
            else:
                file_path = 'storage/data/multi_binary_data.csv'
        else:
            logger.error(f"Invalid model type: {model_type}")
            return None
        
        if not os.path.exists(file_path):
            logger.info(f"No training data found at {file_path}")
            return None
        
        # Load the data
        data = pd.read_csv(file_path)
        logger.info(f"Loaded training data from {file_path}")
        
        return data
    except Exception as e:
        logger.error(f"Error loading training data: {str(e)}")
        return None

def combine_datasets(datasets, output_path=None):
    """
    Combine multiple datasets into one
    
    Args:
        datasets (list): List of DataFrames to combine
        output_path (str, optional): Path to save combined dataset
        
    Returns:
        pd.DataFrame: Combined dataset
    """
    try:
        if not datasets:
            logger.error("No datasets provided for combining")
            return None
        
        # Combine datasets
        combined = pd.concat(datasets, ignore_index=True)
        
        # Save if output path is provided
        if output_path:
            combined.to_csv(output_path, index=False)
            logger.info(f"Saved combined dataset to {output_path}")
        
        return combined
    except Exception as e:
        logger.error(f"Error combining datasets: {str(e)}")
        return None