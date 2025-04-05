const wazuhRepo = require('../persistence layer - data/wazuh.repo');
const logger = require('../config/winston');

class WazuhService {
  /**
   * Fetch Wazuh security alerts based on filters
   * @param {string} timeRange - Time range for alerts (e.g., '24h', '7d', '30d')
   * @param {number} limit - Maximum number of alerts to return
   * @param {number} offset - Offset for pagination
   * @returns {Object} - Object containing alerts and pagination metadata
   */
  async fetchWazuhAlerts(timeRange, limit, offset) {
    try {
      return await wazuhRepo.fetchWazuhAlerts(timeRange, limit, offset);
    } catch (error) {
      logger.error(`Error in WazuhService.fetchWazuhAlerts with timeRange ${timeRange}:`, error);
      throw error;
    }
  }

  // /**
  //  * Get Wazuh agent status summary
  //  * @returns {Object} - Summary of agent statuses (active, disconnected, never connected)
  //  */
  // async getAgentStatusSummary() {
  //   try {
  //     return await wazuhRepo.getAgentStatusSummary();
  //   } catch (error) {
  //     logger.error('Error in WazuhService.getAgentStatusSummary:', error);
  //     throw error;
  //   }
  // }

  // /**
  //  * Get alert summary statistics
  //  * @param {string} timeRange - Time range for statistics (e.g., '24h', '7d', '30d')
  //  * @returns {Object} - Summary statistics including counts by severity, rule groups, etc.
  //  */
  // async getAlertSummary(timeRange) {
  //   try {
  //     return await wazuhRepo.getAlertSummary(timeRange);
  //   } catch (error) {
  //     logger.error(`Error in WazuhService.getAlertSummary with timeRange ${timeRange}:`, error);
  //     throw error;
  //   }
  // }

  // /**
  //  * Get details for a specific alert
  //  * @param {string} alertId - ID of the alert to retrieve
  //  * @returns {Object} - Detailed alert information
  //  */
  // async getAlertDetails(alertId) {
  //   try {
  //     return await wazuhRepo.getAlertDetails(alertId);
  //   } catch (error) {
  //     logger.error(`Error in WazuhService.getAlertDetails for alert ${alertId}:`, error);
  //     throw error;
  //   }
  // }
}

module.exports = new WazuhService();