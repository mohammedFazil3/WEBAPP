"""
Keystroke collector module for HIDS solution.
This module handles collecting keystroke data for AI model training.
"""

import time
import platform
import csv
import os
import signal
import sys
from pynput import keyboard
import threading
from datetime import datetime
import ctypes
import subprocess
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('keystroke_collector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global variables
key_log_dir = os.path.join("flask-api", "storage", "keystroke_collection")
lock = threading.Lock()
partial_data = {}
collection_active = False
listener = None
collection_stats = {
    "start_time": None,
    "keystroke_count": 0,
    "active": False,
    "target": 10000,  # Target for free-text model
    "last_error": None,
    "username": None,
    "model_type": None
}

# Create log directory
os.makedirs(key_log_dir, exist_ok=True)
logger.info(f"Created keystroke collection directory: {key_log_dir}")

# Helper functions
def get_active_window_title():
    """Get the title of the currently active window."""
    if platform.system() == "Windows":
        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            length = user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            return buff.value
        except Exception as e:
            return f"Error: {e}"
    elif platform.system() == "Darwin":
        try:
            # Check if the frontmost app is Safari or Chrome
            script = """
            tell application "System Events"
                set frontApp to name of first application process whose frontmost is true
            end tell
            if frontApp is "Safari" then
                tell application "Safari"
                    return URL of current tab of window 1
                end tell
            else if frontApp is "Google Chrome" then
                tell application "Google Chrome"
                    return URL of active tab of front window
                end tell
            else
                return "No supported browser is active"
            end if
            """
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            return result.stdout.strip()
        except Exception as e:
            return f"Error: {e}"
    return "Unknown"

def get_active_process():
    """Get the name of the currently active process."""
    return get_active_window_title()

def is_sensitive_field():
    """Determine if the current window is a sensitive field."""
    window_title = get_active_window_title().lower()
    # Keywords for sensitive fields
    sensitive_keywords = [
    ]
    return any(keyword in window_title for keyword in sensitive_keywords)

def get_log_file_path(log_dir=None):
    """Get the path to the log file for today."""
    if log_dir is None:
        log_dir = key_log_dir
    today = datetime.now().strftime('%Y-%m-%d')
    username = collection_stats.get("username", "unknown")
    model_type = collection_stats.get("model_type", "unknown")
    return os.path.join(log_dir, f'keystrokes_{username}_{model_type}_{today}.csv')

def get_previous_log_file_path(log_dir=None):
    """Get the path to the most recent log file."""
    if log_dir is None:
        log_dir = key_log_dir
    username = collection_stats.get("username", "unknown")
    model_type = collection_stats.get("model_type", "unknown")
    pattern = f'keystrokes_{username}_{model_type}_*.csv'
    files = [f for f in os.listdir(log_dir) if f.startswith(f'keystrokes_{username}_{model_type}_') and f.endswith('.csv')]
    if not files:
        return None
    files.sort(reverse=True)
    return os.path.join(log_dir, files[0]) if files else None

# Keyboard event handlers
def on_press(key):
    """Handle key press events."""
    global partial_data, collection_active
    
    if not collection_active or is_sensitive_field():
        return  # Skip if collection is inactive or in a sensitive field
    
    try:
        active_process = get_active_process()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        
        # Convert key to string representation
        key_str = str(key)
        
        if key_str not in partial_data:    
            partial_data[key_str] = {
                "timestamp_press": timestamp,
                "key": key_str,
                "active_process": active_process
            }
    except Exception as e:
        print(f"Error in on_press: {e}")

def on_release(key):
    """Handle key release events."""
    global partial_data, collection_stats, collection_active
    
    if not collection_active:
        return  # Skip if collection is inactive
    
    try:
        key_str = str(key)
        
        if key_str in partial_data:
            press_data = partial_data.pop(key_str)
            csv_file = get_log_file_path()
            headers = ["Timestamp_Press", "Timestamp_Release", "Key Stroke", "Application", "Hold Time"]
            
            timestamp_release = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            timestamp_release_dt = datetime.strptime(timestamp_release, '%Y-%m-%d %H:%M:%S.%f')
            timestamp_press = press_data["timestamp_press"]
            timestamp_press_dt = datetime.strptime(timestamp_press, '%Y-%m-%d %H:%M:%S.%f')
            
            hold_time = timestamp_release_dt - timestamp_press_dt
            
            with lock:
                file_exists = os.path.isfile(csv_file)
                with open(csv_file, mode='a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    if not file_exists:
                        writer.writerow(headers)
                    writer.writerow([
                        press_data["timestamp_press"],
                        timestamp_release,
                        press_data["key"],
                        press_data["active_process"],
                        hold_time
                    ])
                    f.flush()
                
                # Update keystroke count from file
                try:
                    with open(csv_file, 'r', encoding='utf-8') as f:
                        # Count lines and subtract 1 for header
                        line_count = sum(1 for _ in f) - 1
                        collection_stats["keystroke_count"] = max(0, line_count)
                except Exception as e:
                    logger.error(f"Error updating keystroke count: {str(e)}")
    except Exception as e:
        error_msg = f"Error in on_release: {str(e)}"
        logger.error(error_msg)
        collection_stats["last_error"] = error_msg

# Collection control functions
def start_collection(username, modelType):
    """Start collecting keystrokes."""
    global listener, collection_active, collection_stats
    
    if collection_active:
        logger.warning("Collection is already active")
        return False
    
    try:
        # Reset stats and store username and modelType
        collection_stats = {
            "start_time": datetime.now().isoformat(),
            "keystroke_count": 0,
            "active": True,
            "target": 10000,
            "last_error": None,
            "username": username,
            "model_type": modelType
        }
        
        # Set up keyboard listener
        listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        listener.start()
        collection_active = True
        logger.info(f"Keystroke collection started successfully for user {username} with model type {modelType}")
        return True
    except Exception as e:
        error_msg = f"Error starting keystroke collection: {str(e)}"
        logger.error(error_msg)
        collection_active = False
        collection_stats["last_error"] = error_msg
        return False

def stop_collection():
    """Stop collecting keystrokes."""
    global listener, collection_active, collection_stats
    
    if not collection_active:
        logger.warning("Collection is not active")
        return False
    
    try:
        if listener:
            listener.stop()
            listener = None
        collection_active = False
        collection_stats["active"] = False
        collection_stats["end_time"] = datetime.now().isoformat()
        
        # Update keystroke count from file
        csv_file = get_log_file_path()
        if os.path.exists(csv_file):
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    # Count lines and subtract 1 for header
                    line_count = sum(1 for _ in f) - 1
                    collection_stats["keystroke_count"] = max(0, line_count)
                    logger.info(f"Final keystroke count: {line_count}")
            except Exception as e:
                error_msg = f"Error reading final keystroke count: {str(e)}"
                logger.error(error_msg)
                collection_stats["last_error"] = error_msg
        
        logger.info("Keystroke collection stopped successfully")
        return True
    except Exception as e:
        error_msg = f"Error stopping keystroke collection: {str(e)}"
        logger.error(error_msg)
        collection_stats["last_error"] = error_msg
        return False

def get_collection_status():
    """Get the current status of keystroke collection."""
    global collection_stats
    
    # Update keystroke count from file if active
    if collection_active:
        csv_file = get_log_file_path()
        if os.path.exists(csv_file):
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    # Count lines and subtract 1 for header
                    line_count = sum(1 for _ in f) - 1
                    if line_count > 0:
                        collection_stats["keystroke_count"] = line_count
                        logger.debug(f"Updated keystroke count: {line_count}")
            except Exception as e:
                error_msg = f"Error reading keystroke count: {str(e)}"
                logger.error(error_msg)
                collection_stats["last_error"] = error_msg
    
    return collection_stats

def get_available_files():
    """Get a list of available keystroke collection files."""
    files = [f for f in os.listdir(key_log_dir) if f.startswith('keystrokes_') and f.endswith('.csv')]
    files.sort(reverse=True)
    
    file_info = []
    for file in files:
        path = os.path.join(key_log_dir, file)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                # Count lines and subtract 1 for header
                line_count = sum(1 for _ in f) - 1
            
            date = file.replace('keystrokes_', '').replace('.csv', '')
            file_info.append({
                "date": date,
                "filename": file,
                "keystroke_count": line_count,
                "size_bytes": os.path.getsize(path)
            })
        except Exception as e:
            print(f"Error reading file {file}: {e}")
    
    return file_info

def get_keystrokes_for_training(count=None, file_path=None):
    """Get keystroke data for model training.
    
    Args:
        count: Number of keystrokes to return (None for all)
        file_path: Specific file path to use (None for today's file)
    
    Returns:
        List of keystroke data dictionaries
    """
    if file_path is None:
        file_path = get_log_file_path()
    
    if not os.path.exists(file_path):
        return []
    
    keystrokes = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                keystrokes.append(row)
                if count is not None and len(keystrokes) >= count:
                    break
    except Exception as e:
        print(f"Error reading keystrokes: {e}")
    
    return keystrokes

def get_csv_file_by_date(date_str):
    """Get keystroke data for a specific date in JSON format.
    
    Args:
        date_str: Date string in YYYY-MM-DD format
    
    Returns:
        tuple: (data_list, exists_bool) - List of keystroke data dictionaries and whether data exists
    """
    try:
        # Validate date format
        datetime.strptime(date_str, '%Y-%m-%d')
        file_path = os.path.join(key_log_dir, f'keystrokes_{date_str}.csv')
        
        if not os.path.exists(file_path):
            return [], False
            
        # Read CSV file into list of dictionaries
        data = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        
        return data, True
    except ValueError:
        return [], False
    except Exception as e:
        logger.error(f"Error reading keystroke data for {date_str}: {str(e)}")
        return [], False

def get_all_csv_files():
    """Get all CSV files in the keystroke collection directory.
    
    Returns:
        list: List of dictionaries containing file information
    """
    try:
        files = []
        for filename in os.listdir(key_log_dir):
            if filename.startswith('keystrokes_') and filename.endswith('.csv'):
                file_path = os.path.join(key_log_dir, filename)
                date_str = filename.replace('keystrokes_', '').replace('.csv', '')
                files.append({
                    'date': date_str,
                    'path': file_path,
                    'size': os.path.getsize(file_path)
                })
        return files
    except Exception as e:
        logger.error(f"Error getting CSV files: {str(e)}")
        return []

# Run collection as standalone script
if __name__ == "__main__":
    import argparse
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Keystroke collection for HIDS")
    parser.add_argument("--output", help="Custom output directory")
    parser.add_argument("--duration", type=int, default=0, help="Collection duration in seconds (0 for indefinite)")
    args = parser.parse_args()
    
    # Set custom output directory if provided
    if args.output:
        key_log_dir = args.output
        os.makedirs(key_log_dir, exist_ok=True)
    
    # Start collection
    print(f"Starting keystroke collection. Output directory: {key_log_dir}")
    start_collection()
    
    try:
        if args.duration > 0:
            print(f"Collection will run for {args.duration} seconds")
            time.sleep(args.duration)
            stop_collection()
            print("Collection completed")
        else:
            print("Press Ctrl+C to stop collection")
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        stop_collection()
        print("Collection stopped by user")
    except Exception as e:
        stop_collection()
        print(f"Collection stopped due to error: {e}")