const keystrokeRepo = require('../persistence layer - data/repositories/keystroke.repo');
const logger = require('../config/winston');

class KeystrokeService {
  /**
   * Get a summary of keystroke models and alerts
   */
  async getSummary() {
    try {
      const summary = await keystrokeRepo.getSummary();
      return summary;
    } catch (error) {
      logger.error('Error in KeystrokeService.getSummary:', error);
      throw error;
    }
  }

  /**
   * Get all available models
   */
  async getAllModels() {
    try {
      return await keystrokeRepo.getAllModels();
    } catch (error) {
      logger.error('Error in KeystrokeService.getAllModels:', error);
      throw error;
    }
  }

  /**
   * Get model details by type
   * @param {string} modelType - Type of model
   */
  async getModelDetails(modelType) {
    try {
      return await keystrokeRepo.getModelDetails(modelType);
    } catch (error) {
      logger.error('Error in KeystrokeService.getModelDetails:', error);
      throw error;
    }
  }

  /**
   * Get active model
   */
  async getActiveModel() {
    try {
      return await keystrokeRepo.getActiveModel();
    } catch (error) {
      logger.error('Error in KeystrokeService.getActiveModel:', error);
      throw error;
    }
  }

  /**
   * Train a model
   * @param {string} modelType - Type of model to train
   * @param {Object} parameters - Training parameters
   */
  async trainModel(modelType, parameters) {
    try {
      return await keystrokeRepo.trainModel(modelType, parameters);
    } catch (error) {
      logger.error('Error in KeystrokeService.trainModel:', error);
      throw error;
    }
  }

  /**
   * Get training status
   * @param {string} jobId - Training job ID
   */
  async getTrainingStatus(jobId) {
    try {
      return await keystrokeRepo.getTrainingStatus(jobId);
    } catch (error) {
      logger.error('Error in KeystrokeService.getTrainingStatus:', error);
      throw error;
    }
  }

  /**
   * Make predictions
   * @param {string} modelType - Type of model to use
   * @param {Object} data - Input data
   */
  async predict(modelType, data) {
    try {
      return await keystrokeRepo.predict(modelType, data);
    } catch (error) {
      logger.error('Error in KeystrokeService.predict:', error);
      throw error;
    }
  }

  /**
   * Switch active model
   * @param {string} modelType - Type of model to activate
   */
  async switchActiveModel(modelType) {
    try {
      return await keystrokeRepo.switchActiveModel(modelType);
    } catch (error) {
      logger.error('Error in KeystrokeService.switchActiveModel:', error);
      throw error;
    }
  }

  /**
   * Get data collection status
   */
  async getDataCollectionStatus() {
    try {
      return await keystrokeRepo.getDataCollectionStatus();
    } catch (error) {
      logger.error('Error in KeystrokeService.getDataCollectionStatus:', error);
      throw error;
    }
  }

  /**
   * Get recent alerts
   * @param {number} limit - Number of alerts to retrieve
   */
  async getRecentAlerts(limit) {
    try {
      const alerts = await keystrokeRepo.getRecentAlerts(limit);
      
      // Transform alerts to a common format
      return alerts.map(alert => ({
        id: alert.id,
        timestamp: alert.timestamp,
        description: alert.description || 'Unknown alert',
        level: alert.level || 0,
        source: 'keystroke',
        type: alert.type || 'unknown',
        details: alert
      }));
    } catch (error) {
      logger.error('Error in KeystrokeService.getRecentAlerts:', error);
      throw error;
    }
  }

  /**
   * Get alerts with pagination
   * @param {number} page - Page number
   * @param {number} limit - Items per page
   * @param {string} filter - Filter string
   */
  async getAlerts(page, limit, filter) {
    try {
      const result = await keystrokeRepo.getAlerts(page, limit, filter);
      
      // Transform alerts to a common format
      const alerts = result.items.map(alert => ({
        id: alert.id,
        timestamp: alert.timestamp,
        description: alert.description || 'Unknown alert',
        level: alert.level || 0,
        source: 'keystroke',
        type: alert.type || 'unknown',
        details: alert
      }));
      
      return {
        alerts,
        totalCount: result.totalItems
      };
    } catch (error) {
      logger.error('Error in KeystrokeService.getAlerts:', error);
      throw error;
    }
  }

  /**
   * Get alert by ID
   * @param {string} id - Alert ID
   */
  async getAlertById(id) {
    try {
      const alert = await keystrokeRepo.getAlertById(id);
      
      if (!alert) {
        return null;
      }
      
      return {
        id: alert.id,
        timestamp: alert.timestamp,
        description: alert.description || 'Unknown alert',
        level: alert.level || 0,
        source: 'keystroke',
        type: alert.type || 'unknown',
        details: alert
      };
    } catch (error) {
      logger.error('Error in KeystrokeService.getAlertById:', error);
      throw error;
    }
  }

  /**
   * Get all schedules
   */
  async getSchedules() {
    try {
      return await keystrokeRepo.getSchedules();
    } catch (error) {
      logger.error('Error in KeystrokeService.getSchedules:', error);
      throw error;
    }
  }

  /**
   * Create a new schedule
   * @param {Object} scheduleData - Schedule data
   */
  async createSchedule(scheduleData) {
    try {
      return await keystrokeRepo.createSchedule(scheduleData);
    } catch (error) {
      logger.error('Error in KeystrokeService.createSchedule:', error);
      throw error;
    }
  }

  /**
   * Update a schedule
   * @param {string} id - Schedule ID
   * @param {Object} scheduleData - Updated schedule data
   */
  async updateSchedule(id, scheduleData) {
    try {
      return await keystrokeRepo.updateSchedule(id, scheduleData);
    } catch (error) {
      logger.error('Error in KeystrokeService.updateSchedule:', error);
      throw error;
    }
  }

  /**
   * Delete a schedule
   * @param {string} id - Schedule ID
   */
  async deleteSchedule(id) {
    try {
      return await keystrokeRepo.deleteSchedule(id);
    } catch (error) {
      logger.error('Error in KeystrokeService.deleteSchedule:', error);
      throw error;
    }
  }

  /**
   * Get users for multi-binary model
   */
  async getMultiBinaryUsers() {
    try {
      return await keystrokeRepo.getMultiBinaryUsers();
    } catch (error) {
      logger.error('Error in KeystrokeService.getMultiBinaryUsers:', error);
      throw error;
    }
  }
}

module.exports = new KeystrokeService(); 