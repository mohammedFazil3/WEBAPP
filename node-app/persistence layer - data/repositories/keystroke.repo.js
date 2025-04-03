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

//I AM STARTING FROM HERE................

//KEYSTROKE COLLECTION FUNCTIONS:

  //Keylogger Starting Function:
  /**
   * Start keystroke collection for a user
   * @param {string} username - User to collect keystrokes from
   * @param {string} modelType - Model type (fixed-text, free-text, multi-binary)
   */
  async startKeystrokeCollection(username, modelType) {
    try {
      const response = await this.axiosInstance.post(`/api/keystroke/collection/start/${username}/${modelType}`);
      return response.data;
    } catch (error) {
      logger.error(`Error in KeystrokeRepository.startKeystrokeCollection for user ${username} and model ${modelType}:`, error);
      throw error;
    }
  }

  //Keylogger Stopping Function:
  /**
   * Stop keystroke collection
   */
  async stopKeystrokeCollection() {
    try {
      const response = await this.axiosInstance.post('/api/keystroke/collection/stop');
      return response.data;
    } catch (error) {
      logger.error('Error in KeystrokeRepository.stopKeystrokeCollection:', error);
      throw error;
    }
  }

  //Keylogger Status Function:
  /**
   * Get keystroke collection status
   */
  async getKeystrokeCollectionStatus() {
    try {
      const response = await this.axiosInstance.get('/api/keystroke/collection/status');
      return response.data;
    } catch (error) {
      logger.error('Error in KeystrokeRepository.getKeystrokeCollectionStatus:', error);
      throw error;
    }
  }
  
  //Download Keystrokes by Date,Username,Model type Function:
  /**
   * Download keystroke collection data
   * @param {string} username - Username for filtering data (required)
   * @param {string} modelType - Model type to download data for (required)
   * @param {string} date - Optional date parameter (defaults to current date)
   * @returns {Blob} - CSV file as blob data
   */
  async downloadKeystrokeData(username, modelType, date = null) {
    if (!username || !modelType) {
      throw new Error("Both 'name' and 'modelType' parameters are required");
    }

    try {
      let url = '/api/keystroke/collection/download';
      
      // Build query parameters
      const queryParams = [
        `name=${encodeURIComponent(username)}`,
        `modelType=${encodeURIComponent(modelType)}`
      ];
      
      // Add date parameter if provided
      if (date) {
        queryParams.push(`date=${encodeURIComponent(date)}`);
      }
      
      url += `?${queryParams.join('&')}`;
      
      // Use responseType: 'blob' to handle binary data
      const response = await this.axiosInstance.get(url, { responseType: 'blob' });
      return response.data;
    } catch (error) {
      logger.error('Error in KeystrokeRepository.downloadKeystrokeData:', error);
      throw error;
    }
  }

  //Get all available files in "keystroke_collection" directory Function:
  /**
   * Get a list of all available keystroke collection files
   */
  async getKeystrokeFiles() {
    try {
      const response = await this.axiosInstance.get('/api/keystroke/collection/files');
      return response.data;
    } catch (error) {
      logger.error('Error in KeystrokeRepository.getKeystrokeFiles:', error);
      throw error;
    }
  }

  //Get keystroke file by date Function:
  /**
   * Get keystroke data for a specific date
   * @param {string} date - Date in YYYY-MM-DD format
   */
  async getKeystrokeDataByDate(date) {
    try {
      const response = await this.axiosInstance.get(`/api/keystroke/collection/download/${date}`);
      return response.data;
    } catch (error) {
      logger.error(`Error in KeystrokeRepository.getKeystrokeDataByDate for date ${date}:`, error);
      throw error;
    }
  }

//MODEL TRAINING FUNCTIONS:

  //Train a preprocessed keystroke file Function:
  /**
   * Train a keystroke model with the specified parameters
   * @param {string} modelType - Model type (fixed-text, free-text, multi-binary)
   * @param {Object} parameters - Training parameters
   * @param {string} username - Username for model training
   */
  async trainKeystrokeModel(modelType, parameters, username) {
    try {
      const requestData = {
        modelType,
        parameters,
        username
      };
      
      const response = await this.axiosInstance.post('/api/keystroke/train', requestData);
      return response.data;
    } catch (error) {
      logger.error(`Error in KeystrokeRepository.trainKeystrokeModel for ${modelType}:`, error);
      throw error;
    }
  }

  //Checking status of model training Function:
  /**
   * Get training status for a specific job
   * @param {string} jobId - Training job ID
   */
  async getKeystrokeTrainingStatus(jobId) {
    try {
      const response = await this.axiosInstance.get(`/api/keystroke/status/${jobId}`);
      return response.data;
    } catch (error) {
      logger.error(`Error in KeystrokeRepository.getKeystrokeTrainingStatus for job ${jobId}:`, error);
      throw error;
    }
  }

}













module.exports = new KeystrokeRepository();
