# keystroke/transition_integration.py
"""
Integration module to connect the transition handler with the existing code.
This file provides the interface for starting/stopping transition monitoring.
It's designed to work cooperatively with the existing training logic in
freetext_keystroke_collector.py.
"""

import logging
import importlib
from . import model_transition_handler
from models import free_text_model

# Set up logging
logger = logging.getLogger(__name__)

def init_transition_monitoring(free_text_collector_module):
    """
    Initialize the transition monitoring with the free-text collector.
    
    Args:
        free_text_collector_module: Either a module object or a string 
                                    representing the module path.
    
    Returns:
        tuple: (success, message)
    """
    try:
        # Handle case where module is passed as string
        if isinstance(free_text_collector_module, str):
            try:
                free_text_collector_module = importlib.import_module(free_text_collector_module)
                logger.info(f"Imported module: {free_text_collector_module}")
            except ImportError as e:
                logger.error(f"Error importing module {free_text_collector_module}: {str(e)}")
                return False, f"Error importing module: {str(e)}"
        
        # Get the username from the collector's status
        try:
            status = free_text_collector_module.get_status()
            username = status.get("collector_status", {}).get("username", "unknown")
            logger.info(f"Getting free-text model for user: {username}")
        except Exception as e:
            logger.error(f"Error getting username from collector status: {str(e)}")
            username = "unknown"
            
        # Create a free-text model instance with the current user
        free_text = free_text_model.FreeTextModel(username)
        
        # Start transition monitoring
        return model_transition_handler.start_transition_monitoring(
            free_text_collector_module,
            free_text
        )
    except Exception as e:
        error_msg = f"Error initializing transition monitoring: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def stop_transition_monitoring():
    """Stop the transition monitoring."""
    return model_transition_handler.stop_transition_monitoring()