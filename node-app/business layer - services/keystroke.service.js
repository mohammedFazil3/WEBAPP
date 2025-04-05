const keystrokeRepo = require('../persistence layer - data/keystroke.repo');
const logger = require('../config/winston');

class KeystrokeService {

  //I AM STARTING FROM HERE..................

  /**
   * Start keystroke collection for a user
   * @param {string} username - User to collect keystrokes from
   * @param {string} modelType - Model type (fixed-text, free-text, multi-binary)
   */
  async startKeystrokeCollection(username, modelType) {
    try {
      return await keystrokeRepo.startKeystrokeCollection(username, modelType);
    } catch (error) {
      logger.error(`Error in KeystrokeService.startKeystrokeCollection for user ${username} and model ${modelType}:`, error);
      throw error;
    }
  }

  /**
   * Stop keystroke collection
   */
  async stopKeystrokeCollection() {
    try {
      return await keystrokeRepo.stopKeystrokeCollection();
    } catch (error) {
      logger.error('Error in KeystrokeService.stopKeystrokeCollection:', error);
      throw error;
    }
  }

  /**
   * Get keystroke collection status
   */
  async getKeystrokeCollectionStatus() {
    try {
      return await keystrokeRepo.getKeystrokeCollectionStatus();
    } catch (error) {
      logger.error('Error in KeystrokeService.getKeystrokeCollectionStatus:', error);
      throw error;
    }
  }
  
  /**
   * Download keystroke collection data
   * @param {string} username - Username for filtering data (required)
   * @param {string} modelType - Model type to download data for (required)
   * @param {string} date - Optional date parameter (defaults to current date)
   * @returns {Blob} - CSV file as blob data
   */
  async downloadKeystrokeData(username, modelType, date = null) {
    try {
      return await keystrokeRepo.downloadKeystrokeData(username, modelType, date);
    } catch (error) {
      logger.error('Error in KeystrokeService.downloadKeystrokeData:', error);
      throw error;
    }
  }

  /**
   * Get a list of all available keystroke collection files
   */
  async getKeystrokeFiles() {
    try {
      return await keystrokeRepo.getKeystrokeFiles();
    } catch (error) {
      logger.error('Error in KeystrokeService.getKeystrokeFiles:', error);
      throw error;
    }
  }

  /**
   * Get keystroke data for a specific date
   * @param {string} date - Date in YYYY-MM-DD format
   */
  async getKeystrokeDataByDate(date) {
    try {
      return await keystrokeRepo.getKeystrokeDataByDate(date);
    } catch (error) {
      logger.error(`Error in KeystrokeService.getKeystrokeDataByDate for date ${date}:`, error);
      throw error;
    }
  }

  /**
   * Train a keystroke model with the specified parameters
   * @param {string} modelType - Model type (fixed-text, free-text, multi-binary)
   * @param {Object} parameters - Training parameters
   * @param {string} username - Username for model training
   */
  async trainKeystrokeModel(modelType, parameters, username) {
    try {
      return await keystrokeRepo.trainKeystrokeModel(modelType, parameters, username);
    } catch (error) {
      logger.error(`Error in KeystrokeService.trainKeystrokeModel for ${modelType}:`, error);
      throw error;
    }
  }

  /**
   * Get training status for a specific job
   * @param {string} jobId - Training job ID
   */
  async getKeystrokeTrainingStatus(jobId) {
    try {
      return await keystrokeRepo.getKeystrokeTrainingStatus(jobId);
    } catch (error) {
      logger.error(`Error in KeystrokeService.getKeystrokeTrainingStatus for job ${jobId}:`, error);
      throw error;
    }
  }

//add the below functions in Keystroke.repo.js in persistence layer................................................................

  /**
   * Fetch keystroke alerts based on filters
   * @param {string} username - Username to filter alerts for
   * @param {string} timeRange - Time range for alerts (e.g., '24h', '7d', '30d')
   * @param {number} confidence - Minimum confidence threshold for alerts
   * @returns {Array} - Array of keystroke alerts
   */
  async fetchKeystrokeAletrs(username, timeRange, confidence) {
    try {
      return await keystrokeRepo.fetchKeystrokeAlerts(username, timeRange, confidence);
    } catch (error) {
      logger.error(`Error in KeystrokeService.fetchKeystrokeAletrs for user ${username}:`, error);
      throw error;
    }
  }
  
  /**
   * Add a new user to the system
   * @param {Object} userData - User data object
   * @param {string} userData.username - Username
   * @param {string} userData.email - Email address
   * @param {string} userData.role - User role (optional)
   * @param {string} userData.department - User department (optional)
   * @param {string} userData.created_at - Creation timestamp
   * @returns {Object} - Created user object
   */
  async addUser(userData) {
    try {
      return await keystrokeRepo.addUser(userData);
    } catch (error) {
      logger.error(`Error in KeystrokeService.addUser for user ${userData.username}:`, error);
      throw error;
    }
  }

}

module.exports = new KeystrokeService(); 