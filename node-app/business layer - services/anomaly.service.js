// services/wazuh.service.js
const wazuhRepo = require('../data/repositories/wazuh.repo');
const logger = require('../config/winston');

class WazuhService {
  /**
   * Get a summary of Wazuh alerts and status
   */
  async getSummary() {
    try {
      const agentStatus = await wazuhRepo.getAgentStatus();
      const alertCounts = await wazuhRepo.getAlertCounts();
      
      return {
        agentStatus,
        totalAlerts: alertCounts.total,
        fimAlerts: alertCounts.fim,
        malwareAlerts: alertCounts.malware,
        vulnerabilityAlerts: alertCounts.vulnerability
      };
    } catch (error) {
      logger.error('Error in WazuhService.getSummary:', error);
      throw error;
    }
  }

  /**
   * Get recent alerts from Wazuh
   * @param {number} limit - Number of alerts to retrieve
   */
  async getRecentAlerts(limit) {
    try {
      const alerts = await wazuhRepo.getRecentAlerts(limit);
      
      // Transform alerts to a common format
      return alerts.map(alert => ({
        id: alert.id,
        timestamp: alert.timestamp,
        description: alert.rule?.description || 'Unknown alert',
        level: alert.rule?.level || 0,
        source: 'wazuh',
        type: this._determineAlertType(alert),
        details: alert
      }));
    } catch (error) {
      logger.error('Error in WazuhService.getRecentAlerts:', error);
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
      const result = await wazuhRepo.getAlerts(page, limit, filter);
      
      // Transform alerts to a common format
      const alerts = result.items.map(alert => ({
        id: alert.id,
        timestamp: alert.timestamp,
        description: alert.rule?.description || 'Unknown alert',
        level: alert.rule?.level || 0,
        source: 'wazuh',
        type: this._determineAlertType(alert),
        details: alert
      }));
      
      return {
        alerts,
        totalCount: result.totalItems
      };
    } catch (error) {
      logger.error('Error in WazuhService.getAlerts:', error);
      throw error;
    }
  }

  /**
   * Get FIM alerts
   * @param {number} page - Page number
   * @param {number} limit - Items per page
   * @param {string} filter - Filter string
   */
  async getFIMAlerts(page, limit, filter) {
    try {
      return await wazuhRepo.getFIMAlerts(page, limit, filter);
    } catch (error) {
      logger.error('Error in WazuhService.getFIMAlerts:', error);
      throw error;
    }
  }

  /**
   * Get malware alerts
   * @param {number} page - Page number
   * @param {number} limit - Items per page
   * @param {string} filter - Filter string
   */
  async getMalwareAlerts(page, limit, filter) {
    try {
      return await wazuhRepo.getMalwareAlerts(page, limit, filter);
    } catch (error) {
      logger.error('Error in WazuhService.getMalwareAlerts:', error);
      throw error;
    }
  }

  /**
   * Get vulnerability alerts
   * @param {number} page - Page number
   * @param {number} limit - Items per page
   * @param {string} filter - Filter string
   */
  async getVulnerabilityAlerts(page, limit, filter) {
    try {
      return await wazuhRepo.getVulnerabilityAlerts(page, limit, filter);
    } catch (error) {
      logger.error('Error in WazuhService.getVulnerabilityAlerts:', error);
      throw error;
    }
  }

  /**
   * Get agent status
   */
  async getAgentStatus() {
    try {
      return await wazuhRepo.getAgentStatus();
    } catch (error) {
      logger.error('Error in WazuhService.getAgentStatus:', error);
      throw error;
    }
  }

  /**
   * Get alert by ID
   * @param {string} id - Alert ID
   */
  async getAlertById(id) {
    try {
      const alert = await wazuhRepo.getAlertById(id);
      
      if (!alert) {
        return null;
      }
      
      return {
        id: alert.id,
        timestamp: alert.timestamp,
        description: alert.rule?.description || 'Unknown alert',
        level: alert.rule?.level || 0,
        source: 'wazuh',
        type: this._determineAlertType(alert),
        details: alert
      };
    } catch (error) {
      logger.error('Error in WazuhService.getAlertById:', error);
      throw error;
    }
  }

  /**
   * Determine alert type based on alert data
   * @param {Object} alert - Alert data
   * @private
   */
  _determineAlertType(alert) {
    if (alert.rule?.groups?.includes('syscheck')) {
      return 'fim';
    } else if (alert.rule?.groups?.includes('vulnerability-detector')) {
      return 'vulnerability';
    } else if (alert.rule?.groups?.includes('virustotal') || 
               alert.rule?.groups?.includes('rootkit')) {
      return 'malware';
    } else {
      return 'other';
    }
  }
}

module.exports = new WazuhService();