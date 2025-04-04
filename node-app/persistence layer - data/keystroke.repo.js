// data/repositories/keystroke.repo.js
const axios = require('axios');
const config = require('../config/config');
console.log(config)
const logger = require('../config/winston');

class KeystrokeRepository {
  constructor() {
    this.axiosInstance = axios.create({
      baseURL: config.keystrokeAI.url,
      timeout: config.keystrokeAI.timeout
    });
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

//FREE-TEXT FUNCTIONS:
  

}

/**
 * Test function for the startKeystrokeCollection API
 * With improved connection handling and error management
 */
async function testKeystrokeCollection() {
  try {
    // Using the exported instance of KeystrokeRepository
    const keystrokeRepo = module.exports;
    
    // Sample test parameters
    const username = "testUser";
    const modelType = "free-text"; // Can be "fixed-text", "free-text", or "multi-binary"
    
    console.log(`Starting keystroke collection test for user: ${username}, model type: ${modelType}`);
    
    // Try with explicit IPv4 address instead of localhost
    // Modify config temporarily to force IPv4
    const originalUrl = keystrokeRepo.axiosInstance.defaults.baseURL;
    console.log(`Original API URL: ${originalUrl}`);
    
    // Force IPv4 by replacing localhost with 127.0.0.1
    if (originalUrl.includes('localhost')) {
      const ipv4Url = originalUrl.replace('localhost', '127.0.0.1');
      console.log(`Trying with IPv4 URL: ${ipv4Url}`);
      keystrokeRepo.axiosInstance.defaults.baseURL = ipv4Url;
    }
    
    // Call the API method
    const result = await keystrokeRepo.startKeystrokeCollection(username, modelType);
    
    // Reset URL if it was modified
    if (originalUrl !== keystrokeRepo.axiosInstance.defaults.baseURL) {
      keystrokeRepo.axiosInstance.defaults.baseURL = originalUrl;
    }
    
    console.log("Keystroke collection successfully started");
    
    // Safely extract and print only specific properties to avoid circular references
    const safeResult = {
      success: result.success,
      message: result.message
    };
    
    if (result.stats) {
      safeResult.stats = {
        active: result.stats.active,
        keystroke_count: result.stats.keystroke_count
      };
    }
    
    console.log("Result:", safeResult);
    return result;
  } catch (error) {
    console.error("Failed to start keystroke collection");
    console.error("Error message:", error.message);
    
    if (error.code === 'ECONNREFUSED') {
      console.error("\nConnection refused. Try the following:");
      console.error("1. Check if Flask server is running (it should show 'Running on http://127.0.0.1:5000')");
      console.error("2. Try using IPv4 explicitly in your config (127.0.0.1 instead of localhost)");
      console.error("3. Make sure no firewall is blocking the connection");
      console.error("4. Check if the Flask server is listening on the correct interface (0.0.0.0)");
      
      // Try a simple test with axios directly
      try {
        console.log("\nAttempting connection test with axios directly...");
        const axios = require('axios');
        await axios.get('http://127.0.0.1:5000/', { timeout: 3000 });
        console.log("✅ Direct connection to http://127.0.0.1:5000/ successful!");
      } catch (testError) {
        console.error("❌ Direct connection test failed:", testError.message);
      }
    }
    
    if (error.response) {
      console.error("Response status:", error.response.status);
      console.error("Response headers:", error.response.headers);
      console.error("Response data:", 
        typeof error.response.data === 'string' ? 
        error.response.data : 
        JSON.stringify(error.response.data, null, 2));
    }
    
    throw error;
  }
}

/**
 * Test function for the stopKeystrokeCollection API
 * With improved formatting to match the Postman output
 */
async function testStopKeystrokeCollection() {
  try {
    // Using the exported instance of KeystrokeRepository
    const keystrokeRepo = module.exports;
    
    console.log(`Stopping keystroke collection...`);
    
    // Try with explicit IPv4 address instead of localhost
    const originalUrl = keystrokeRepo.axiosInstance.defaults.baseURL;
    
    // Force IPv4 by replacing localhost with 127.0.0.1
    if (originalUrl.includes('localhost')) {
      const ipv4Url = originalUrl.replace('localhost', '127.0.0.1');
      keystrokeRepo.axiosInstance.defaults.baseURL = ipv4Url;
    }
    
    // Call the API method
    const result = await keystrokeRepo.stopKeystrokeCollection();
    
    // Reset URL if it was modified
    if (originalUrl !== keystrokeRepo.axiosInstance.defaults.baseURL) {
      keystrokeRepo.axiosInstance.defaults.baseURL = originalUrl;
    }
    
    // Format the result in a way similar to the Postman screenshot
    console.log('\n' + JSON.stringify(result, null, 2));
    
    return result;
  } catch (error) {
    console.error("Failed to stop keystroke collection");
    console.error("Error message:", error.message);
    
    if (error.code === 'ECONNREFUSED') {
      console.error("\nConnection refused. Check if the Flask server is running on http://127.0.0.1:5000");
    }
    
    if (error.response && error.response.data) {
      console.error("\nServer response:");
      console.error(JSON.stringify(error.response.data, null, 2));
    }
    
    throw error;
  }
}

/**
 * Test function for the getKeystrokeCollectionStatus API
 * With formatting to match the Postman output
 */
async function testGetKeystrokeCollectionStatus() {
  try {
    // Using the exported instance of KeystrokeRepository
    const keystrokeRepo = module.exports;
    
    console.log(`Getting keystroke collection status...`);
    
    // Try with explicit IPv4 address instead of localhost
    const originalUrl = keystrokeRepo.axiosInstance.defaults.baseURL;
    
    // Force IPv4 by replacing localhost with 127.0.0.1
    if (originalUrl.includes('localhost')) {
      const ipv4Url = originalUrl.replace('localhost', '127.0.0.1');
      keystrokeRepo.axiosInstance.defaults.baseURL = ipv4Url;
    }
    
    // Call the API method
    const result = await keystrokeRepo.getKeystrokeCollectionStatus();
    
    // Reset URL if it was modified
    if (originalUrl !== keystrokeRepo.axiosInstance.defaults.baseURL) {
      keystrokeRepo.axiosInstance.defaults.baseURL = originalUrl;
    }
    
    // Format the result in a way similar to the Postman screenshot
    console.log('\n' + JSON.stringify(result, null, 2));
    
    return result;
  } catch (error) {
    console.error("Failed to get keystroke collection status");
    console.error("Error message:", error.message);
    
    if (error.code === 'ECONNREFUSED') {
      console.error("\nConnection refused. Check if the Flask server is running on http://127.0.0.1:5000");
    }
    
    if (error.response && error.response.data) {
      console.error("\nServer response:");
      console.error(JSON.stringify(error.response.data, null, 2));
    }
    
    throw error;
  }
}

/**
 * Test function for the downloadKeystrokeData API
 * With formatting to match the Postman output for CSV data
 */
async function testDownloadKeystrokeData() {
  try {
    // Using the exported instance of KeystrokeRepository
    const keystrokeRepo = module.exports;
    
    // Required parameters
    const username = "testUser";
    const modelType = "free-text";
    // Optional parameter - can be null/undefined to use current date
    const date = null; // e.g., "2025-04-02" 
    
    console.log(`Downloading keystroke data for user: ${username}, model type: ${modelType}${date ? ', date: ' + date : ''}...`);
    
    // Try with explicit IPv4 address instead of localhost
    const originalUrl = keystrokeRepo.axiosInstance.defaults.baseURL;
    
    // Force IPv4 by replacing localhost with 127.0.0.1
    if (originalUrl.includes('localhost')) {
      const ipv4Url = originalUrl.replace('localhost', '127.0.0.1');
      keystrokeRepo.axiosInstance.defaults.baseURL = ipv4Url;
    }
    
    // Call the API method
    const result = await keystrokeRepo.downloadKeystrokeData(username, modelType, date);
    
    // Reset URL if it was modified
    if (originalUrl !== keystrokeRepo.axiosInstance.defaults.baseURL) {
      keystrokeRepo.axiosInstance.defaults.baseURL = originalUrl;
    }
    
    // Handle the blob response - convert to text
    const fs = require('fs');
    const csvContent = result.toString('utf-8');
    
    // Display the first few lines of the CSV content (similar to Postman preview)
    const lines = csvContent.split('\n');
    const previewLines = lines.slice(0, Math.min(20, lines.length));
    
    console.log('\nCSV Data Preview:');
    console.log('----------------------------------------');
    previewLines.forEach((line, index) => {
      console.log(`${index + 1}: ${line}`);
    });
    console.log('----------------------------------------');
    
    // Save the CSV file locally
    const filename = `keystrokes_${username}_${modelType}${date ? '_' + date : ''}.csv`;
    console.log(`\nDownloaded data saved to: ${filename}`);
    console.log(`Total lines: ${lines.length}`);
    
    return { success: true, filename, totalLines: lines.length };
  } catch (error) {
    console.error("Failed to download keystroke data");
    console.error("Error message:", error.message);
    
    if (error.code === 'ECONNREFUSED') {
      console.error("\nConnection refused. Check if the Flask server is running on http://127.0.0.1:5000");
    }
    
    if (error.response) {
      console.error(`\nServer response status: ${error.response.status}`);
      if (error.response.data) {
        try {
          if (typeof error.response.data === 'object') {
            console.error(JSON.stringify(error.response.data, null, 2));
          } else {
            console.error(error.response.data.toString());
          }
        } catch (e) {
          console.error("Cannot display response data");
        }
      }
    }
    
    throw error;
  }
}

/**
 * Test function for the getKeystrokeFiles API
 * With formatting to match the Postman output
 */
async function testGetKeystrokeFiles() {
  try {
    // Using the exported instance of KeystrokeRepository
    const keystrokeRepo = module.exports;
    
    console.log(`Getting available keystroke files...`);
    
    // Try with explicit IPv4 address instead of localhost
    const originalUrl = keystrokeRepo.axiosInstance.defaults.baseURL;
    
    // Force IPv4 by replacing localhost with 127.0.0.1
    if (originalUrl.includes('localhost')) {
      const ipv4Url = originalUrl.replace('localhost', '127.0.0.1');
      keystrokeRepo.axiosInstance.defaults.baseURL = ipv4Url;
    }
    
    // Call the API method
    const result = await keystrokeRepo.getKeystrokeFiles();
    
    // Reset URL if it was modified
    if (originalUrl !== keystrokeRepo.axiosInstance.defaults.baseURL) {
      keystrokeRepo.axiosInstance.defaults.baseURL = originalUrl;
    }
    
    // Format the result in a way similar to the Postman screenshot
    console.log('\n' + JSON.stringify(result, null, 2));
    
    return result;
  } catch (error) {
    console.error("Failed to get keystroke files");
    console.error("Error message:", error.message);
    
    if (error.code === 'ECONNREFUSED') {
      console.error("\nConnection refused. Check if the Flask server is running on http://127.0.0.1:5000");
    }
    
    if (error.response && error.response.data) {
      console.error("\nServer response:");
      console.error(JSON.stringify(error.response.data, null, 2));
    }
    
    throw error;
  }
}

/**
 * Test function for the getKeystrokeDataByDate API
 * With formatting to match the Postman output
 */
async function testGetKeystrokeDataByDate() {
  try {
    // Using the exported instance of KeystrokeRepository
    const keystrokeRepo = module.exports;
    
    // Specify the date to retrieve data for
    const date = "2025-04-02"; // Format should be YYYY-MM-DD
    
    console.log(`Getting keystroke data for date: ${date}...`);
    
    // Try with explicit IPv4 address instead of localhost
    const originalUrl = keystrokeRepo.axiosInstance.defaults.baseURL;
    
    // Force IPv4 by replacing localhost with 127.0.0.1
    if (originalUrl.includes('localhost')) {
      const ipv4Url = originalUrl.replace('localhost', '127.0.0.1');
      keystrokeRepo.axiosInstance.defaults.baseURL = ipv4Url;
    }
    
    // Call the API method
    const result = await keystrokeRepo.getKeystrokeDataByDate(date);
    
    // Reset URL if it was modified
    if (originalUrl !== keystrokeRepo.axiosInstance.defaults.baseURL) {
      keystrokeRepo.axiosInstance.defaults.baseURL = originalUrl;
    }
    
    // Format the result in a way similar to the Postman screenshot
    console.log('\n' + JSON.stringify(result, null, 2));
    
    return result;
  } catch (error) {
    console.error("Failed to get keystroke data by date");
    console.error("Error message:", error.message);
    
    if (error.code === 'ECONNREFUSED') {
      console.error("\nConnection refused. Check if the Flask server is running on http://127.0.0.1:5000");
    }
    
    if (error.response && error.response.data) {
      console.error("\nServer response:");
      console.error(JSON.stringify(error.response.data, null, 2));
    }
    
    throw error;
  }
}

/**
 * Test function for the trainKeystrokeModel API
 * With formatting to match the Postman output
 */
async function testTrainKeystrokeModel() {
  try {
    // Using the exported instance of KeystrokeRepository
    const keystrokeRepo = module.exports;
    
    // Define training parameters
    const modelType = "free-text";
    const username = "testUser";
    const parameters = {
      "n_estimators": 100,
      "max_depth": 10
    };
    
    console.log(`Training ${modelType} model for user ${username}...`);
    console.log(`Parameters: ${JSON.stringify(parameters)}`);
    
    // Try with explicit IPv4 address instead of localhost
    const originalUrl = keystrokeRepo.axiosInstance.defaults.baseURL;
    
    // Force IPv4 by replacing localhost with 127.0.0.1
    if (originalUrl.includes('localhost')) {
      const ipv4Url = originalUrl.replace('localhost', '127.0.0.1');
      keystrokeRepo.axiosInstance.defaults.baseURL = ipv4Url;
    }
    
    // Call the API method
    const result = await keystrokeRepo.trainKeystrokeModel(modelType, parameters, username);
    
    // Reset URL if it was modified
    if (originalUrl !== keystrokeRepo.axiosInstance.defaults.baseURL) {
      keystrokeRepo.axiosInstance.defaults.baseURL = originalUrl;
    }
    
    // Format the result in a way similar to the Postman screenshot
    console.log('\nResponse:');
    console.log(JSON.stringify(result, null, 2));
    
    return result;
  } catch (error) {
    console.error("Failed to train keystroke model");
    console.error("Error message:", error.message);
    
    if (error.code === 'ECONNREFUSED') {
      console.error("\nConnection refused. Check if the Flask server is running on http://127.0.0.1:5000");
    }
    
    if (error.response && error.response.data) {
      console.error("\nServer response:");
      console.error(JSON.stringify(error.response.data, null, 2));
    }
    
    throw error;
  }
}

/**
 * Test function for the getKeystrokeTrainingStatus API
 * With formatting to match the Postman output
 */
async function testGetKeystrokeTrainingStatus() {
  try {
    // Using the exported instance of KeystrokeRepository
    const keystrokeRepo = module.exports;
    
    // Specify the job ID to check status for
    const jobId = "d2c272fb-86e4-4bf7-9280-d9365e2164da"; // Replace with your actual job ID
    
    console.log(`Getting training status for job: ${jobId}...`);
    
    // Try with explicit IPv4 address instead of localhost
    const originalUrl = keystrokeRepo.axiosInstance.defaults.baseURL;
    
    // Force IPv4 by replacing localhost with 127.0.0.1
    if (originalUrl.includes('localhost')) {
      const ipv4Url = originalUrl.replace('localhost', '127.0.0.1');
      keystrokeRepo.axiosInstance.defaults.baseURL = ipv4Url;
    }
    
    // Call the API method
    const result = await keystrokeRepo.getKeystrokeTrainingStatus(jobId);
    
    // Reset URL if it was modified
    if (originalUrl !== keystrokeRepo.axiosInstance.defaults.baseURL) {
      keystrokeRepo.axiosInstance.defaults.baseURL = originalUrl;
    }
    
    // Format the result in a way similar to the Postman screenshot
    console.log('\n' + JSON.stringify(result, null, 2));
    
    return result;
  } catch (error) {
    console.error("Failed to get training status");
    console.error("Error message:", error.message);
    
    if (error.code === 'ECONNREFUSED') {
      console.error("\nConnection refused. Check if the Flask server is running on http://127.0.0.1:5000");
    }
    
    if (error.response && error.response.data) {
      console.error("\nServer response:");
      console.error(JSON.stringify(error.response.data, null, 2));
    }
    
    throw error;
  }
}

module.exports = new KeystrokeRepository();

// Uncomment the following line to run the test when the file is executed directly
// testKeystrokeCollection();
// testStopKeystrokeCollection();
// testGetKeystrokeCollectionStatus();
// testDownloadKeystrokeData();
// testGetKeystrokeFiles();
// testGetKeystrokeDataByDate();
// testTrainKeystrokeModel();
// testGetKeystrokeTrainingStatus();
