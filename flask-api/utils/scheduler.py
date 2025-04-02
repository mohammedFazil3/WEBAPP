# utils/scheduler.py
import time
import logging
import threading
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def run_scheduler(schedules, model_map):
    """
    Background scheduler thread that executes scheduled tasks.
    
    Args:
        schedules (list): List of schedule configurations
        model_map (dict): Map of model types to model instances
    """
    logger.info("Starting scheduler thread")
    
    while True:
        try:
            # Load current schedules from file to get updates
            try:
                with open('storage/jobs/schedules.json', 'r') as f:
                    current_schedules = json.load(f)
            except Exception as e:
                logger.error(f"Error loading schedules: {str(e)}")
                current_schedules = []
            
            now = datetime.now()
            
            # Check for tasks that need to run
            for schedule in current_schedules:
                if not schedule.get('isActive', True):
                    continue
                    
                try:
                    next_run = datetime.fromisoformat(schedule.get('nextRunTime'))
                    
                    # If it's time to run
                    if now >= next_run:
                        logger.info(f"Running scheduled task: {schedule.get('id')} - {schedule.get('modelType')} {schedule.get('operationType')}")
                        
                        # Run the task based on operation type
                        if schedule.get('operationType') == 'train':
                            model_type = schedule.get('modelType')
                            parameters = schedule.get('parameters', {})
                            
                            if model_type in model_map:
                                # Run training in a separate thread
                                training_thread = threading.Thread(
                                    target=model_map[model_type].train,
                                    args=(parameters,)
                                )
                                training_thread.daemon = True
                                training_thread.start()
                        
                        # Calculate next run time based on interval
                        interval_type = schedule.get('intervalType')
                        
                        if interval_type == 'hourly':
                            next_run = now + timedelta(hours=1)
                        elif interval_type == 'daily':
                            next_run = now + timedelta(days=1)
                        elif interval_type == 'weekly':
                            next_run = now + timedelta(weeks=1)
                        elif interval_type == 'monthly':
                            # Approximate month as 30 days
                            next_run = now + timedelta(days=30)
                        elif interval_type == 'custom':
                            # Custom interval in minutes
                            minutes = schedule.get('customInterval', 60)
                            next_run = now + timedelta(minutes=minutes)
                        else:
                            # Default to daily
                            next_run = now + timedelta(days=1)
                        
                        # Update next run time
                        schedule['nextRunTime'] = next_run.isoformat()
                        schedule['lastRun'] = now.isoformat()
                        
                        # Save updated schedules
                        with open('storage/jobs/schedules.json', 'w') as f:
                            json.dump(current_schedules, f)
                except Exception as e:
                    logger.error(f"Error processing schedule {schedule.get('id')}: {str(e)}")
            
            # Sleep for a minute before checking again
            time.sleep(60)
        except Exception as e:
            logger.error(f"Error in scheduler thread: {str(e)}")
            time.sleep(60)  # Sleep and try again
