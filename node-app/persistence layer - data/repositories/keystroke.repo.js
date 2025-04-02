// data/repositories/keystroke.repo.js
const axios = require('axios');
const config = require('../../config/config');
const logger = require('../../config/winston');

class KeystrokeRepository {
  constructor() {
    this.axiosInstance = axios.create({
      baseURL: config.keystrokeAI.url,
      timeout: config.keystrokeAI.timeout
    });
  }

  /**
   * Get all available models
   */
  async getAllModels() {
    try {
      const response = await this.axiosInstance.get('/api/keystroke/models');
      return response.data;
    } catch (error) {
      logger.error('Error in KeystrokeRepository.getAllModels:', error);
      throw error;
    }
  }

  /**
   * Get model details by type
   * @param {string} modelType - Model type (fixed-text, free-text, multi-binary)
   */
  async getModelDetails(modelType) {
    try {
      const response = await this.axiosInstance.get(`/api/keystroke/models/${modelType}`);
      return response.data;
    } catch (error) {
      logger.error(`Error in KeystrokeRepository.getModelDetails for ${modelType}:`, error);
      throw error;
    }
  }

  /**
   * Get active model information
   */
  async getActiveModel() {
    try {
      const response = await this.axiosInstance.get('/api/keystroke/models/active');
      return response.data;
    } catch (error) {
      logger.error('Error in KeystrokeRepository.getActiveModel:', error);
      throw error;
    }
  }

  /**
   * Train a model
   * @param {string} modelType - Model type (fixed-text, free-text, multi-binary)
   * @param {Object} parameters - Training parameters
   */
  async trainModel(modelType, parameters) {
    try {
      const response = await this.axiosInstance.post('/api/keystroke/train', {
        modelType,
        parameters
      });
      return response.data.jobId;
    } catch (error) {
      logger.error(`Error in KeystrokeRepository.trainModel for ${modelType}:`, error);
      throw error;
    }
  }

  /**
   * Get training status
   * @param {string} jobId - Training job ID
   */
  async getTrainingStatus(jobId) {
    try {
      const response = await this.axiosInstance.get(`/api/keystroke/status/${jobId}`);
      return response.data;
    } catch (error) {
      logger.error(`Error in KeystrokeRepository.getTrainingStatus for ${jobId}:`, error);
      throw error;
    }
  }

  /**
   * Make prediction with model
   * @param {string} modelType - Model type (fixed-text, free-text, multi-binary)
   * @param {Object} data - Keystroke data for prediction
   */
  async predict(modelType, data) {
    try {
      const response = await this.axiosInstance.post('/api/keystroke/predict', {
        modelType,
        data
      });
      return response.data;
    } catch (error) {
      logger.error(`Error in KeystrokeRepository.predict for ${modelType}:`, error);
      throw error;
    }
  }

  /**
   * Switch active model
   * @param {string} modelType - Model type (fixed-text, free-text, multi-binary)
   */
  async switchActiveModel(modelType) {
    try {
      const response = await this.axiosInstance.put(`/api/keystroke/switch/${modelType}`);
      return response.data;
    } catch (error) {
      logger.error(`Error in KeystrokeRepository.switchActiveModel to ${modelType}:`, error);
      throw error;
    }
  }

  /**
   * Get data collection status for free-text model
   */
  async getDataCollectionStatus() {
    try {
      const response = await this.axiosInstance.get('/api/keystroke/collection/status');
      return response.data;
    } catch (error) {
      logger.error('Error in KeystrokeRepository.getDataCollectionStatus:', error);
      throw error;
    }
  }

  /**
   * Get recent alerts
   * @param {number} limit - Maximum number of alerts
   */
  async getRecentAlerts(limit) {
    try {
      const response = await this.axiosInstance.get(`/api/keystroke/alerts?limit=${limit}`);
      return response.data;
    } catch (error) {
      logger.error('Error in KeystrokeRepository.getRecentAlerts:', error);
      throw error;
    }
  }

  /**
   * Get alerts with pagination and filtering
   * @param {number} page - Page number
   * @param {number} limit - Items per page
   * @param {string} filter - Filter text
   */
  async getAlerts(page, limit, filter) {
    try {
      let url = `/api/keystroke/alerts?page=${page}&limit=${limit}`;
      if (filter) {
        url += `&filter=${encodeURIComponent(filter)}`;
      }
      
      const response = await this.axiosInstance.get(url);
      return response.data;
    } catch (error) {
      logger.error('Error in KeystrokeRepository.getAlerts:', error);
      throw error;
    }
  }

  /**
   * Get alert by ID
   * @param {string} id - Alert ID
   */
  async getAlertById(id) {
    try {
      const response = await this.axiosInstance.get(`/api/keystroke/alerts/${id}`);
      return response.data;
    } catch (error) {
      logger.error(`Error in KeystrokeRepository.getAlertById for ${id}:`, error);
      
      // If 404, return null
      if (error.response && error.response.status === 404) {
        return null;
      }
      
      throw error;
    }
  }

  /**
   * Get model training schedules
   */
  async getSchedules() {
    try {
      const response = await this.axiosInstance.get('/api/keystroke/schedule');
      return response.data;
    } catch (error) {
      logger.error('Error in KeystrokeRepository.getSchedules:', error);
      throw error;
    }
  }

  /**
   * Create a new schedule
   * @param {Object} scheduleData - Schedule configuration
   */
  async createSchedule(scheduleData) {
    try {
      const response = await this.axiosInstance.post('/api/keystroke/schedule/create', scheduleData);
      return response.data;
    } catch (error) {
      logger.error('Error in KeystrokeRepository.createSchedule:', error);
      throw error;
    }
  }

  /**
   * Update a schedule
   * @param {string} id - Schedule ID
   * @param {Object} scheduleData - Updated schedule configuration
   */
  async updateSchedule(id, scheduleData) {
    try {
      const response = await this.axiosInstance.put(`/api/keystroke/schedule/${id}`, scheduleData);
      return response.data;
    } catch (error) {
      logger.error(`Error in KeystrokeRepository.updateSchedule for ${id}:`, error);
      throw error;
    }
  }

  /**
   * Delete a schedule
   * @param {string} id - Schedule ID
   */
  async deleteSchedule(id) {
    try {
      await this.axiosInstance.delete(`/api/keystroke/schedule/${id}`);
      return { success: true };
    } catch (error) {
      logger.error(`Error in KeystrokeRepository.deleteSchedule for ${id}:`, error);
      throw error;
    }
  }

  /**
   * Get summary statistics
   */
  async getSummary() {
    try {
      const response = await this.axiosInstance.get('/api/keystroke/summary');
      return response.data;
    } catch (error) {
      logger.error('Error in KeystrokeRepository.getSummary:', error);
      throw error;
    }
  }

  /**
   * Get multi-binary model users
   */
  async getMultiBinaryUsers() {
    try {
      const response = await this.axiosInstance.get('/api/keystroke/multi-binary/users');
      return response.data;
    } catch (error) {
      logger.error('Error in KeystrokeRepository.getMultiBinaryUsers:', error);
      throw error;
    }
  }
}

module.exports = new KeystrokeRepository();
