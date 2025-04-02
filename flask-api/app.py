# app.py - Main Flask application entry point
from flask import Flask, request, jsonify, send_file
import logging
import os
import json
import uuid
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from threading import Thread
import time

# Import custom modules
from keystroke import keystroke_collector
from models import fixed_text_model, free_text_model, multi_binary_model
from preprocessing import keystroke_processor
from utils import scheduler, data_handler

# Set up logging
from log_config import setup_logging
logger = setup_logging()

app = Flask(__name__)

# Create storage directories if they don't exist
os.makedirs('storage/models', exist_ok=True)
os.makedirs('storage/data', exist_ok=True)
os.makedirs('storage/alerts', exist_ok=True)
os.makedirs('storage/jobs', exist_ok=True)

# Load or initialize job status tracking
JOBS_FILE = 'storage/jobs/jobs.json'
if os.path.exists(JOBS_FILE):
    with open(JOBS_FILE, 'r') as f:
        training_jobs = json.load(f)
else:
    training_jobs = {}
    with open(JOBS_FILE, 'w') as f:
        json.dump(training_jobs, f)

# Track active model
ACTIVE_MODEL_FILE = 'storage/models/active_model.json'
if os.path.exists(ACTIVE_MODEL_FILE):
    with open(ACTIVE_MODEL_FILE, 'r') as f:
        active_model = json.load(f)
else:
    # Default to fixed-text model
    active_model = {
        'type': 'fixed-text',
        'last_updated': datetime.now().isoformat()
    }
    with open(ACTIVE_MODEL_FILE, 'w') as f:
        json.dump(active_model, f)

# Schedule registry
SCHEDULES_FILE = 'storage/jobs/schedules.json'
if os.path.exists(SCHEDULES_FILE):
    with open(SCHEDULES_FILE, 'r') as f:
        schedules = json.load(f)
else:
    schedules = []
    with open(SCHEDULES_FILE, 'w') as f:
        json.dump(schedules, f)

# Initialize model instances
fixed_text = fixed_text_model.FixedTextModel()
free_text = free_text_model.FreeTextModel()
multi_binary = multi_binary_model.MultiBinaryModel()

# Map model types to their instances
model_map = {
    'fixed-text': fixed_text,
    'free-text': free_text,
    'multi-binary': multi_binary
}

# Function to run training in background
def run_training(job_id, model_type, parameters):
    try:
        # Update job status to "in progress"
        training_jobs[job_id]['status'] = 'in_progress'
        training_jobs[job_id]['start_time'] = datetime.now().isoformat()
        _save_jobs()
        
        # Get model instance
        model = model_map[model_type]
        
        # Run training
        result = model.train(parameters)
        
        # Update job status to "completed"
        training_jobs[job_id]['status'] = 'completed'
        training_jobs[job_id]['end_time'] = datetime.now().isoformat()
        training_jobs[job_id]['result'] = result
        _save_jobs()
        
        logger.info(f"Training job {job_id} completed successfully")
    except Exception as e:
        # Update job status to "failed"
        training_jobs[job_id]['status'] = 'failed'
        training_jobs[job_id]['error'] = str(e)
        training_jobs[job_id]['end_time'] = datetime.now().isoformat()
        _save_jobs()
        
        logger.error(f"Training job {job_id} failed: {str(e)}")

# Helper function to save jobs to file
def _save_jobs():
    with open(JOBS_FILE, 'w') as f:
        json.dump(training_jobs, f)

# Helper function to save active model configuration
def _save_active_model():
    with open(ACTIVE_MODEL_FILE, 'w') as f:
        json.dump(active_model, f)

# Helper function to save schedules
def _save_schedules():
    with open(SCHEDULES_FILE, 'w') as f:
        json.dump(schedules, f)

# Start the scheduler
scheduler_thread = Thread(target=scheduler.run_scheduler, args=(schedules, model_map))
scheduler_thread.daemon = True
scheduler_thread.start()

#------------ API ROUTES ------------#

##Keystroke Collection
@app.route('/api/keystroke/collection/start/<username>/<modelType>', methods=['POST'])
def start_collection(username, modelType):
    """Start keystroke collection"""
    try:
        success = keystroke_collector.start_collection(username, modelType)
        status = keystroke_collector.get_collection_status()
        
        if success:
            return jsonify({
                "success": True,
                "message": "Keystroke collection started",
                "stats": status
            })
        else:
            return jsonify({
                "success": False,
                "message": "Collection is already active or failed to start",
                "error": status.get("last_error"),
                "stats": status
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    
@app.route('/api/keystroke/collection/stop', methods=['POST'])
def stop_collection():
    """Stop keystroke collection"""
    try:
        success = keystroke_collector.stop_collection()
        status = keystroke_collector.get_collection_status()
        
        if success:
            return jsonify({
                "success": True,
                "message": "Keystroke collection stopped",
                "stats": status
            })
        else:
            return jsonify({
                "success": False,
                "message": "Collection is not active or failed to stop",
                "error": status.get("last_error"),
                "stats": status
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    
@app.route('/api/keystroke/collection/status', methods=['GET'])
def get_collection_status():
    """Get keystroke collection status and count"""
    try:
        stats = keystroke_collector.get_collection_status()
        
        # Include additional info
        result = {
            "success": True,
            "stats": stats,
            "today_file": keystroke_collector.get_log_file_path()
        }
        
        # If there's an error, include it in the response
        if stats.get("last_error"):
            result["error"] = stats["last_error"]
        
        # If we're collecting for free-text model, add progress info
        if stats["active"]:
            result["free_text_progress"] = {
                "collected": stats["keystroke_count"],
                "target": stats["target"],
                "percentage": min(100, round((stats["keystroke_count"] / stats["target"]) * 100, 1))
            }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    
@app.route('/api/keystroke/collection/download', methods=['GET'])
def download_keystrokes():
    """Download keystroke CSV file"""
    try:
        # Get the file date from query param, default to today
        file_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        csv_file = os.path.join(keystroke_collector.key_log_dir, f'keystrokes_{file_date}.csv')
        
        if not os.path.exists(csv_file):
            return jsonify({
                "success": False,
                "message": f"No keystroke data available for {file_date}"
            }), 404
        
        return send_file(
            csv_file,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'keystrokes_{file_date}.csv'
        )
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/keystroke/collection/files', methods=['GET'])
def list_keystroke_files():
    """List available keystroke collection files"""
    try:
        file_info = keystroke_collector.get_available_files()
        
        return jsonify({
            "success": True,
            "files": file_info
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/keystroke/collection/data', methods=['GET'])
def get_keystroke_data():
    """Get keystroke data for analysis or training"""
    try:
        # Get parameters
        count = request.args.get('count')
        date = request.args.get('date')
        
        if count:
            count = int(count)
        
        # Get file path if date provided
        file_path = None
        if date:
            file_path = os.path.join(keystroke_collector.key_log_dir, f'keystrokes_{date}.csv')
        
        # Get keystroke data
        data = keystroke_collector.get_keystrokes_for_training(count, file_path)
        
        return jsonify({
            "success": True,
            "count": len(data),
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    

@app.route('/api/keystroke/collection/download/<date>', methods=['GET'])
def download_keystroke_file_by_date(date):
    """Get keystroke data for a specific date in JSON format"""
    try:
        data, exists = keystroke_collector.get_csv_file_by_date(date)
        if not exists:
            return jsonify({
                "success": False,
                "message": f"No keystroke data available for {date}"
            }), 404
        
        return jsonify({
            "success": True,
            "date": date,
            "count": len(data),
            "data": data
        })
    except Exception as e:
        logger.error(f"Error getting keystroke data for {date}: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/keystroke/collection/download-all', methods=['GET'])
def download_all_keystroke_files():
    """Download all keystroke CSV files as a zip archive"""
    try:
        import zipfile
        import io
        
        # Get all CSV files
        files = keystroke_collector.get_all_csv_files()
        if not files:
            return jsonify({
                "success": False,
                "message": "No keystroke data files available"
            }), 404
        
        # Create a zip file in memory
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_info in files:
                zf.write(file_info['path'], f"keystrokes_{file_info['date']}.csv")
        
        memory_file.seek(0)
        
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name='keystroke_data.zip'
        )
    except Exception as e:
        logger.error(f"Error downloading all keystroke files: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Route to upload fixed text data
@app.route('/api/keystroke/upload/fixed-text/<username>', methods=['POST'])
def upload_fixed_text_data(username):
    """Upload a CSV file containing fixed text keystroke data"""
    try:
        # Check if the post request has the file part
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "error": "No file part in the request"
            }), 400
            
        file = request.files['file']
        
        # If user does not select file, browser also submits an empty part without filename
        if file.filename == '':
            return jsonify({
                "success": False,
                "error": "No file selected"
            }), 400
            
        if file and file.filename.endswith('.csv'):
            # Create the directory if it doesn't exist
            os.makedirs('storage/data', exist_ok=True)
            
            # Save the file to the storage directory
            filepath = os.path.join('storage/data', username+'fixed_text_data_raw.csv')
            file.save(filepath)
            
            # Basic validation that the file has the expected format
            try:
                df = pd.read_csv(filepath)
                required_columns = ['Timestamp_Press','Timestamp_Release','Key Stroke','Application','Hold Time']
                
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    return jsonify({
                        "success": False,
                        "error": f"CSV file is missing required columns: {', '.join(missing_columns)}"
                    }), 400
                
                preprocessedDatadf = keystroke_processor.preprocess_keystroke_data(df, username, additional_users={
                    "Aisha": "storage/data/FixedText_Aisha.csv",
                    "Misbah": "storage/data/FixedText_Misbah.csv"
                })
                
                # Save preprocessed data to CSV
                preprocessed_filepath = os.path.join('storage/data', 'fixed_text_data_preprocessed.csv')
                preprocessedDatadf.to_csv(preprocessed_filepath, index=False)
                
                return jsonify({
                    "success": True,
                    "message": "File uploaded and preprocessed successfully",
                    "rows": len(df),
                    "columns": list(df.columns),
                    "preprocessed_file": preprocessed_filepath
                })
            except Exception as e:
                return jsonify({
                    "success": False,
                    "error": f"Error validating CSV file: {str(e)}"
                }), 400
        else:
            return jsonify({
                "success": False,
                "error": "Only CSV files are allowed"
            }), 400
            
    except Exception as e:
        logger.error(f"Error uploading fixed text data: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

##Kinda irrelevant api routes
@app.route('/api/keystroke/models', methods=['GET'])
def get_models():
    """Get all available models"""
    try:
        models = []
        
        # Get fixed-text model info
        fixed_text_info = fixed_text.get_info()
        if fixed_text_info:
            models.append({
                'type': 'fixed-text',
                'info': fixed_text_info
            })
        
        # Get free-text model info
        free_text_info = free_text.get_info()
        if free_text_info:
            models.append({
                'type': 'free-text',
                'info': free_text_info
            })
        
        # Get multi-binary model info
        multi_binary_info = multi_binary.get_info()
        if multi_binary_info:
            models.append({
                'type': 'multi-binary',
                'info': multi_binary_info
            })
        
        return jsonify(models)
    except Exception as e:
        logger.error(f"Error getting models: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/keystroke/models/<model_type>', methods=['GET'])
def get_model_details(model_type):
    """Get details for a specific model type"""
    try:
        if model_type not in model_map:
            return jsonify({'error': 'Invalid model type'}), 400
        
        model = model_map[model_type]
        model_info = model.get_info()
        
        # Include whether this is the active model
        is_active = (active_model['type'] == model_type)
        
        return jsonify({
            'type': model_type,
            'info': model_info,
            'is_active': is_active
        })
    except Exception as e:
        logger.error(f"Error getting model details for {model_type}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/keystroke/models/active', methods=['GET'])
def get_active_model():
    """Get the currently active model"""
    try:
        model_type = active_model['type']
        model = model_map[model_type]
        model_info = model.get_info()
        
        return jsonify({
            'type': model_type,
            'info': model_info,
            'last_updated': active_model['last_updated']
        })
    except Exception as e:
        logger.error(f"Error getting active model: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/keystroke/train', methods=['POST'])
def train_model():
    """Start model training"""
    try:
        data = request.json
        model_type = data.get('modelType')
        parameters = data.get('parameters', {})
        
        if model_type not in model_map:
            return jsonify({'error': 'Invalid model type'}), 400
        
        # Generate a unique job ID
        job_id = str(uuid.uuid4())
        
        # Store job info
        training_jobs[job_id] = {
            'id': job_id,
            'model_type': model_type,
            'parameters': parameters,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        _save_jobs()
        
        # Start training in a separate thread
        training_thread = Thread(target=run_training, args=(job_id, model_type, parameters))
        training_thread.daemon = True
        training_thread.start()
        
        return jsonify({'jobId': job_id})
    
    except Exception as e:
        logger.error(f"Error starting training: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/keystroke/status/<job_id>', methods=['GET'])
def get_training_status(job_id):
    """Get status of a training job"""
    try:
        if job_id not in training_jobs:
            return jsonify({'error': 'Job not found'}), 404
        
        job = training_jobs[job_id]
        
        # Calculate progress if job is in progress
        if job['status'] == 'in_progress':
            # For demo purposes, calculate a fake progress based on time elapsed
            # In a real app, this would be based on actual training progress
            start_time = datetime.fromisoformat(job['start_time'])
            current_time = datetime.now()
            elapsed_seconds = (current_time - start_time).total_seconds()
            
            # Assume training takes around 60 seconds
            progress = min(int(elapsed_seconds / 60 * 100), 99)
            
            job['progress'] = progress
        elif job['status'] == 'completed':
            job['progress'] = 100
        
        return jsonify(job)
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/keystroke/predict', methods=['POST'])
def predict():
    """Make prediction with active model"""
    try:
        data = request.json
        model_type = data.get('modelType', active_model['type'])
        keystroke_data = data.get('data')
        
        if not keystroke_data:
            return jsonify({'error': 'No keystroke data provided'}), 400
        
        if model_type not in model_map:
            return jsonify({'error': 'Invalid model type'}), 400
        
        # Preprocess the data
        processed_data = keystroke_processor.preprocess_keystroke_data(keystroke_data)
        
        # Get predictions
        model = model_map[model_type]
        result = model.predict(processed_data)
        
        # Check if this prediction represents an anomaly/intrusion
        # If it does, save it as an alert
        if result.get('is_anomaly', False):
            alert_id = str(uuid.uuid4())
            alert = {
                'id': alert_id,
                'type': 'keystroke_anomaly',
                'model_type': model_type,
                'confidence': result.get('confidence', 0),
                'timestamp': datetime.now().isoformat(),
                'details': result
            }
            
            # Save alert to file (in a real app, this would go to a database)
            with open(f'storage/alerts/{alert_id}.json', 'w') as f:
                json.dump(alert, f)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error making prediction: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/keystroke/switch/<model_type>', methods=['PUT'])
def switch_active_model(model_type):
    """Switch the active model"""
    try:
        if model_type not in model_map:
            return jsonify({'error': 'Invalid model type'}), 400
        
        # Get model instance
        model = model_map[model_type]
        
        # Check if model is trained/ready
        model_info = model.get_info()
        if not model_info.get('is_trained', False):
            return jsonify({'error': f'Model {model_type} is not trained yet'}), 400
        
        # Update active model
        active_model['type'] = model_type
        active_model['last_updated'] = datetime.now().isoformat()
        _save_active_model()
        
        return jsonify({
            'success': True,
            'message': f'Switched to {model_type} model',
            'active_model': active_model
        })
    except Exception as e:
        logger.error(f"Error switching active model: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/keystroke/collection/status', methods=['GET'])
def get_free_text_collection_status():
    """Get keystroke collection status for free-text model"""
    try:
        status = free_text.get_collection_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting collection status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/keystroke/alerts', methods=['GET'])
def get_alerts():
    """Get keystroke anomaly alerts with pagination"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        filter_text = request.args.get('filter', '')
        
        # Get all alert files
        alert_files = os.listdir('storage/alerts')
        alert_files.sort(key=lambda x: os.path.getmtime(os.path.join('storage/alerts', x)), reverse=True)
        
        alerts = []
        for file_name in alert_files:
            if not file_name.endswith('.json'):
                continue
                
            with open(os.path.join('storage/alerts', file_name), 'r') as f:
                alert = json.load(f)
                
            # Apply filter if provided
            if filter_text and filter_text.lower() not in json.dumps(alert).lower():
                continue
                
            alerts.append(alert)
        
        # Apply pagination
        total_count = len(alerts)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_alerts = alerts[start_idx:end_idx]
        
        return jsonify({
            'alerts': paginated_alerts,
            'totalCount': total_count
        })
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/keystroke/alerts/<alert_id>', methods=['GET'])
def get_alert_by_id(alert_id):
    """Get a specific alert by ID"""
    try:
        alert_path = os.path.join('storage/alerts', f'{alert_id}.json')
        
        if not os.path.exists(alert_path):
            return jsonify({'error': 'Alert not found'}), 404
            
        with open(alert_path, 'r') as f:
            alert = json.load(f)
            
        return jsonify(alert)
    except Exception as e:
        logger.error(f"Error getting alert {alert_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/keystroke/schedule', methods=['GET'])
def get_schedules():
    """Get all schedules"""
    try:
        return jsonify(schedules)
    except Exception as e:
        logger.error(f"Error getting schedules: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/keystroke/schedule/create', methods=['POST'])
def create_schedule():
    """Create a new schedule"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['modelType', 'operationType', 'intervalType']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Generate a unique ID
        schedule_id = str(uuid.uuid4())
        
        # Create schedule object
        schedule = {
            'id': schedule_id,
            'modelType': data['modelType'],
            'operationType': data['operationType'],
            'intervalType': data['intervalType'],
            'customInterval': data.get('customInterval'),
            'nextRunTime': data.get('nextRunTime', (datetime.now() + timedelta(minutes=5)).isoformat()),
            'parameters': data.get('parameters', {}),
            'createdAt': datetime.now().isoformat(),
            'updatedAt': datetime.now().isoformat(),
            'isActive': True
        }
        
        # Add to schedules
        schedules.append(schedule)
        _save_schedules()
        
        return jsonify(schedule)
    except Exception as e:
        logger.error(f"Error creating schedule: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/keystroke/schedule/<schedule_id>', methods=['PUT'])
def update_schedule(schedule_id):
    """Update a schedule"""
    try:
        data = request.json
        
        # Find schedule
        schedule_idx = None
        for idx, schedule in enumerate(schedules):
            if schedule['id'] == schedule_id:
                schedule_idx = idx
                break
        
        if schedule_idx is None:
            return jsonify({'error': 'Schedule not found'}), 404
        
        # Update fields
        for key, value in data.items():
            if key not in ['id', 'createdAt']:  # Don't allow updating these fields
                schedules[schedule_idx][key] = value
        
        # Update updatedAt timestamp
        schedules[schedule_idx]['updatedAt'] = datetime.now().isoformat()
        
        _save_schedules()
        
        return jsonify(schedules[schedule_idx])
    except Exception as e:
        logger.error(f"Error updating schedule {schedule_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/keystroke/schedule/<schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    """Delete a schedule"""
    try:
        # Find schedule
        schedule_idx = None
        for idx, schedule in enumerate(schedules):
            if schedule['id'] == schedule_id:
                schedule_idx = idx
                break
        
        if schedule_idx is None:
            return jsonify({'error': 'Schedule not found'}), 404
        
        # Remove from schedules
        removed_schedule = schedules.pop(schedule_idx)
        _save_schedules()
        
        return jsonify({'success': True, 'deleted': removed_schedule})
    except Exception as e:
        logger.error(f"Error deleting schedule {schedule_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/keystroke/summary', methods=['GET'])
def get_summary():
    """Get summary statistics for keystroke models and alerts"""
    try:
        # Count alerts
        alert_count = len([f for f in os.listdir('storage/alerts') if f.endswith('.json')])
        
        # Get model statuses
        model_statuses = {}
        for model_type, model in model_map.items():
            info = model.get_info()
            model_statuses[model_type] = {
                'trained': info.get('is_trained', False),
                'last_trained': info.get('last_trained', None),
                'accuracy': info.get('accuracy', None)
            }
        
        # Get data collection status for free-text model
        collection_status = free_text.get_collection_status()
        
        return jsonify({
            'alert_count': alert_count,
            'models': model_statuses,
            'active_model': active_model['type'],
            'collection_status': collection_status
        })
    except Exception as e:
        logger.error(f"Error getting summary: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/keystroke/multi-binary/users', methods=['GET'])
def get_multi_binary_users():
    """Get users for multi-binary model"""
    try:
        users = multi_binary.get_users()
        return jsonify(users)
    except Exception as e:
        logger.error(f"Error getting multi-binary users: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Start the Flask application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)