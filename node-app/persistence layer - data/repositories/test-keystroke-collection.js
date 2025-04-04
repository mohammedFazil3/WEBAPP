// test-keystroke-collection.js
const keystrokeRepo = require('./keystroke.repo');

/**
 * Test for startKeystrokeCollection API
 * @param {string} username - User to collect keystrokes from
 * @param {string} modelType - Model type (fixed-text, free-text, multi-binary)
 * @returns {Promise<Object>} - API response
 */
async function testStartKeystrokeCollection(username = 'testUser', modelType = 'free-text') {
  try {
    console.log(`Starting keystroke collection for user: ${username} with model type: ${modelType}`);
    const result = await keystrokeRepo.startKeystrokeCollection(username, modelType);
    console.log('Keystroke collection started successfully:', result);
    return result;
  } catch (error) {
    console.error('Failed to start keystroke collection:', error.message);
    throw error;
  }
}

/**
 * Test for stopKeystrokeCollection API
 * @returns {Promise<Object>} - API response
 */
async function testStopKeystrokeCollection() {
  try {
    console.log('Stopping keystroke collection');
    const result = await keystrokeRepo.stopKeystrokeCollection();
    console.log('Keystroke collection stopped successfully:', result);
    return result;
  } catch (error) {
    console.error('Failed to stop keystroke collection:', error.message);
    throw error;
  }
}

/**
 * Test for getKeystrokeCollectionStatus API
 * @returns {Promise<Object>} - API response
 */
async function testGetKeystrokeCollectionStatus() {
  try {
    console.log('Getting keystroke collection status');
    const result = await keystrokeRepo.getKeystrokeCollectionStatus();
    console.log('Keystroke collection status:', result);
    return result;
  } catch (error) {
    console.error('Failed to get keystroke collection status:', error.message);
    throw error;
  }
}

/**
 * Test for downloadKeystrokeData API
 * @param {string} username - Username for filtering data
 * @param {string} modelType - Model type
 * @param {string} date - Optional date parameter
 * @returns {Promise<Blob>} - CSV file as blob data
 */
async function testDownloadKeystrokeData(username = 'testUser', modelType = 'free-text', date = null) {
  try {
    console.log(`Downloading keystroke data for user: ${username}, model: ${modelType}${date ? `, date: ${date}` : ''}`);
    const result = await keystrokeRepo.downloadKeystrokeData(username, modelType, date);
    console.log('Keystroke data downloaded successfully, blob size:', result.size);
    return result;
  } catch (error) {
    console.error('Failed to download keystroke data:', error.message);
    throw error;
  }
}

/**
 * Test for getKeystrokeFiles API
 * @returns {Promise<Object>} - API response
 */
async function testGetKeystrokeFiles() {
  try {
    console.log('Getting available keystroke files');
    const result = await keystrokeRepo.getKeystrokeFiles();
    console.log('Available keystroke files:', result);
    return result;
  } catch (error) {
    console.error('Failed to get keystroke files:', error.message);
    throw error;
  }
}

/**
 * Test for getKeystrokeDataByDate API
 * @param {string} date - Date in YYYY-MM-DD format
 * @returns {Promise<Object>} - API response
 */
async function testGetKeystrokeDataByDate(date = '2025-04-03') {
  try {
    console.log(`Getting keystroke data for date: ${date}`);
    const result = await keystrokeRepo.getKeystrokeDataByDate(date);
    console.log('Keystroke data for date:', result);
    return result;
  } catch (error) {
    console.error(`Failed to get keystroke data for date ${date}:`, error.message);
    throw error;
  }
}

/**
 * Test for trainKeystrokeModel API
 * @param {string} modelType - Model type
 * @param {Object} parameters - Training parameters
 * @param {string} username - Username for model training
 * @returns {Promise<Object>} - API response
 */
async function testTrainKeystrokeModel(
  modelType = 'free-text',
  parameters = { epochs: 100, batchSize: 32 },
  username = 'testUser'
) {
  try {
    console.log(`Training keystroke model for user: ${username}, model type: ${modelType}`);
    const result = await keystrokeRepo.trainKeystrokeModel(modelType, parameters, username);
    console.log('Keystroke model training started:', result);
    return result;
  } catch (error) {
    console.error('Failed to train keystroke model:', error.message);
    throw error;
  }
}

/**
 * Test for getKeystrokeTrainingStatus API
 * @param {string} jobId - Training job ID
 * @returns {Promise<Object>} - API response
 */
async function testGetKeystrokeTrainingStatus(jobId) {
  try {
    console.log(`Getting training status for job: ${jobId}`);
    const result = await keystrokeRepo.getKeystrokeTrainingStatus(jobId);
    console.log('Training status:', result);
    return result;
  } catch (error) {
    console.error(`Failed to get training status for job ${jobId}:`, error.message);
    throw error;
  }
}

/**
 * Run selected tests sequentially
 */
async function runSelectedTests() {
  try {
    console.log('\n----- Testing Keystroke Collection Functions -----\n');
    
    // Start collection
    const startResult = await testStartKeystrokeCollection('testUser', 'free-text');
    
    // Check status
    await testGetKeystrokeCollectionStatus();
    
    // Get available files
    await testGetKeystrokeFiles();
    
    // Try to download data
    await testDownloadKeystrokeData('testUser', 'free-text');
    
    // Get data by date
    await testGetKeystrokeDataByDate('2025-04-03');
    
    // Stop collection
    await testStopKeystrokeCollection();
    
    // Test training function
    console.log('\n----- Testing Keystroke Training Functions -----\n');
    const trainResult = await testTrainKeystrokeModel();
    
    // If train function returned a job ID, check its status
    if (trainResult && trainResult.jobId) {
      await testGetKeystrokeTrainingStatus(trainResult.jobId);
    } else {
      console.log('No training job ID returned, skipping status check');
    }
    
    console.log('\n----- All tests completed successfully -----\n');
  } catch (error) {
    console.error('Test sequence failed:', error.message);
  }
}

// Export functions for individual usage
module.exports = {
  testStartKeystrokeCollection,
  testStopKeystrokeCollection,
  testGetKeystrokeCollectionStatus,
  testDownloadKeystrokeData,
  testGetKeystrokeFiles,
  testGetKeystrokeDataByDate,
  testTrainKeystrokeModel,
  testGetKeystrokeTrainingStatus,
  runSelectedTests
};

// Uncomment one of these to run a specific test
testStartKeystrokeCollection('testUser', 'free-text').catch(console.error);
// testGetKeystrokeCollectionStatus().catch(console.error);
// runSelectedTests().catch(console.error);