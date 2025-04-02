// data/repositories/wazuh.repo.js
const axios = require('axios');
const https = require('https');
const config = require('../../config/config');
const logger = require('../../config/winston');

class WazuhRepository {
  constructor() {
    // Create axios instance with SSL verification disabled (similar to your Java implementation)
    this.axiosInstance = axios.create({
      baseURL: `${config.wazuh.protocol}://${config.wazuh.host}:${config.wazuh.port}`,
      auth: {
        username: config.wazuh.user,
        password: config.wazuh.password
      },
      timeout: config.wazuh.timeout,
      httpsAgent: new https.Agent({
        rejectUnauthorized: false // Disable SSL verification
      })
    });

    // For OpenSearch/Elasticsearch direct connections
    this.esAxiosInstance = axios.create({
      baseURL: `${config.openSearch.protocol}://${config.openSearch.host}:${config.openSearch.port}`,
      auth: {
        username: config.openSearch.user,
        password: config.openSearch.password
      },
      timeout: config.openSearch.timeout,
      httpsAgent: new https.Agent({
        rejectUnauthorized: false
      })
    });
  }

  /**
   * Get JWT token for Wazuh API
   * @private
   */
  async _getToken() {
    try {
      const response = await this.axiosInstance.post('/security/user/authenticate');
      return response.data.data.token;
    } catch (error) {
      logger.error('Error in WazuhRepository._getToken:', error);
      throw new Error('Failed to authenticate with Wazuh API');
    }
  }

  /**
   * Get agent status
   */
  async getAgentStatus() {
    try {
      const token = await this._getToken();
      const response = await this.axiosInstance.get('/agents/summary/status', {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      return response.data.data;
    } catch (error) {
      logger.error('Error in WazuhRepository.getAgentStatus:', error);
      throw error;
    }
  }

  /**
   * Get alert counts by category
   */
  async getAlertCounts() {
    try {
      // Query OpenSearch/Elasticsearch directly for alert counts
      const fimQuery = {
        query: {
          bool: {
            must: [
              { term: { 'rule.groups': 'syscheck' } }
            ]
          }
        },
        size: 0
      };
      
      const malwareQuery = {
        query: {
          bool: {
            should: [
              { term: { 'rule.groups': 'rootcheck' } },
              { term: { 'rule.groups': 'virustotal' } }
            ],
            minimum_should_match: 1
          }
        },
        size: 0
      };
      
      const vulnerabilityQuery = {
        query: {
          bool: {
            must: [
              { term: { 'rule.groups': 'vulnerability-detector' } }
            ]
          }
        },
        size: 0
      };
      
      // Execute all queries
      const [fimResult, malwareResult, vulnerabilityResult, totalResult] = await Promise.all([
        this.esAxiosInstance.post('/_count', fimQuery),
        this.esAxiosInstance.post('/_count', malwareQuery),
        this.esAxiosInstance.post('/_count', vulnerabilityQuery),
        this.esAxiosInstance.post('/_count')
      ]);
      
      return {
        fim: fimResult.data.count,
        malware: malwareResult.data.count,
        vulnerability: vulnerabilityResult.data.count,
        total: totalResult.data.count
      };
    } catch (error) {
      logger.error('Error in WazuhRepository.getAlertCounts:', error);
      throw error;
    }
  }

  /**
   * Get recent alerts
   * @param {number} limit - Maximum number of alerts to retrieve
   */
  async getRecentAlerts(limit) {
    try {
      // Query OpenSearch/Elasticsearch directly
      const query = {
        query: {
          match_all: {}
        },
        sort: [
          { '@timestamp': { order: 'desc' } }
        ],
        size: limit
      };
      
      const response = await this.esAxiosInstance.post('/_search', query);
      
      return response.data.hits.hits.map(hit => ({
        ...hit._source,
        id: hit._id
      }));
    } catch (error) {
      logger.error('Error in WazuhRepository.getRecentAlerts:', error);
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
      // Construct query based on filter
      let query = {
        query: {
          match_all: {}
        }
      };
      
      if (filter) {
        query.query = {
          query_string: {
            query: `*${filter}*`,
            default_field: '*'
          }
        };
      }
      
      // Add pagination
      query.from = (page - 1) * limit;
      query.size = limit;
      query.sort = [{ '@timestamp': { order: 'desc' } }];
      
      // Get total count
      const countResponse = await this.esAxiosInstance.post('/_count', {
        query: query.query
      });
      
      // Get paginated results
      const response = await this.esAxiosInstance.post('/_search', query);
      
      return {
        items: response.data.hits.hits.map(hit => ({
          ...hit._source,
          id: hit._id
        })),
        totalItems: countResponse.data.count
      };
    } catch (error) {
      logger.error('Error in WazuhRepository.getAlerts:', error);
      throw error;
    }
  }

  /**
   * Get File Integrity Monitoring alerts
   * @param {number} page - Page number
   * @param {number} limit - Items per page
   * @param {string} filter - Filter text
   */
  async getFIMAlerts(page, limit, filter) {
    try {
      // Query similar to your Java implementation
      let query = {
        query: {
          bool: {
            must: [
              { term: { 'rule.groups': 'syscheck' } }
            ]
          }
        },
        sort: [{ '@timestamp': { order: 'desc' } }],
        from: (page - 1) * limit,
        size: limit
      };
      
      // Add filter if provided
      if (filter) {
        query.query.bool.must.push({
          query_string: {
            query: `*${filter}*`,
            default_field: '*'
          }
        });
      }
      
      // Get total count
      const countResponse = await this.esAxiosInstance.post('/_count', {
        query: query.query
      });
      
      // Get paginated results
      const response = await this.esAxiosInstance.post('/_search', query);
      
      return {
        items: response.data.hits.hits.map(hit => ({
          ...hit._source,
          id: hit._id
        })),
        totalItems: countResponse.data.count
      };
    } catch (error) {
      logger.error('Error in WazuhRepository.getFIMAlerts:', error);
      throw error;
    }
  }

  /**
   * Get Malware/Rootkit alerts
   * @param {number} page - Page number
   * @param {number} limit - Items per page
   * @param {string} filter - Filter text
   */
  async getMalwareAlerts(page, limit, filter) {
    try {
      // Query similar to your Java implementation
      let query = {
        query: {
          bool: {
            must: [
              {
                bool: {
                  should: [
                    { term: { 'rule.groups': 'rootcheck' } },
                    { term: { 'rule.groups': 'virustotal' } }
                  ],
                  minimum_should_match: 1
                }
              }
            ]
          }
        },
        sort: [{ '@timestamp': { order: 'desc' } }],
        from: (page - 1) * limit,
        size: limit
      };
      
      // Add filter if provided
      if (filter) {
        query.query.bool.must.push({
          query_string: {
            query: `*${filter}*`,
            default_field: '*'
          }
        });
      }
      
      // Get total count
      const countResponse = await this.esAxiosInstance.post('/_count', {
        query: query.query
      });
      
      // Get paginated results
      const response = await this.esAxiosInstance.post('/_search', query);
      
      return {
        items: response.data.hits.hits.map(hit => ({
          ...hit._source,
          id: hit._id
        })),
        totalItems: countResponse.data.count
      };
    } catch (error) {
      logger.error('Error in WazuhRepository.getMalwareAlerts:', error);
      throw error;
    }
  }

  /**
   * Get Vulnerability alerts
   * @param {number} page - Page number
   * @param {number} limit - Items per page
   * @param {string} filter - Filter text
   */
  async getVulnerabilityAlerts(page, limit, filter) {
    try {
      // Query similar to your Java implementation
      let query = {
        query: {
          bool: {
            must: [
              { term: { 'rule.groups': 'vulnerability-detector' } }
            ]
          }
        },
        sort: [{ '@timestamp': { order: 'desc' } }],
        from: (page - 1) * limit,
        size: limit
      };
      
      // Add filter if provided
      if (filter) {
        query.query.bool.must.push({
          query_string: {
            query: `*${filter}*`,
            default_field: '*'
          }
        });
      }
      
      // Get total count
      const countResponse = await this.esAxiosInstance.post('/_count', {
        query: query.query
      });
      
      // Get paginated results
      const response = await this.esAxiosInstance.post('/_search', query);
      
      return {
        items: response.data.hits.hits.map(hit => ({
          ...hit._source,
          id: hit._id
        })),
        totalItems: countResponse.data.count
      };
    } catch (error) {
      logger.error('Error in WazuhRepository.getVulnerabilityAlerts:', error);
      throw error;
    }
  }

  /**
   * Get an alert by ID
   * @param {string} id - Alert ID
   */
  async getAlertById(id) {
    try {
      const response = await this.esAxiosInstance.get(`/_doc/${id}`);
      
      if (response.data.found) {
        return {
          ...response.data._source,
          id: response.data._id
        };
      }
      
      return null;
    } catch (error) {
      logger.error('Error in WazuhRepository.getAlertById:', error);
      
      // If 404, return null
      if (error.response && error.response.status === 404) {
        return null;
      }
      
      throw error;
    }
  }

  /**
   * Register a new Wazuh agent (similar to your Java implementation)
   * @param {string} agentName - Name of the agent
   * @param {string} agentIP - IP address of the agent
   */
  async registerAgent(agentName, agentIP) {
    try {
      const token = await this._getToken();
      
      const response = await this.axiosInstance.post(
        '/agents',
        { name: agentName, ip: agentIP },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      if (response.data.error === 0) {
        const agentId = response.data.data.id;
        
        // Get agent key
        const keyResponse = await this.axiosInstance.get(
          `/agents/${agentId}/key`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        
        if (keyResponse.data.error === 0 && 
            keyResponse.data.data.affected_items && 
            keyResponse.data.data.affected_items.length > 0) {
          
          const agentKey = keyResponse.data.data.affected_items[0].key;
          
          // Save agent info to file (or database in production)
          const agentInfo = {
            id: agentId,
            name: agentName,
            ip: agentIP,
            key: agentKey
          };
          
          // In a real app, you'd save to a database
          await this._saveAgentInfo(agentInfo);
          
          return agentInfo;
        }
      }
      
      throw new Error('Failed to register agent');
    } catch (error) {
      logger.error('Error in WazuhRepository.registerAgent:', error);
      throw error;
    }
  }

  /**
   * Save agent info to a file (in production you'd use a database)
   * @param {Object} agentInfo - Agent information
   * @private
   */
  async _saveAgentInfo(agentInfo) {
    // In a real app, you'd save to a database
    // This is just a placeholder for the example
    return agentInfo;
  }

  /**
   * Get OpenSearch anomalies
   * This would normally connect to OpenSearch Anomaly Detection API
   * For this example, we'll just return mock data
   */
  async getOpenSearchAnomalies(page = 1, limit = 20, filter = '') {
    try {
      // In a real implementation, you would query OpenSearch Anomaly Detection
      // For now, return mock data
      const mockAnomalies = [];
      for (let i = 0; i < 50; i++) {
        mockAnomalies.push({
          id: `anomaly-${i}`,
          timestamp: new Date(Date.now() - i * 3600000).toISOString(), // 1 hour intervals
          score: Math.floor(Math.random() * 100),
          details: {
            description: `Unusual behavior detected in system metrics`,
            affected_resource: `Resource-${i % 10}`,
            anomaly_type: i % 3 === 0 ? 'CPU' : (i % 3 === 1 ? 'Memory' : 'Network')
          }
        });
      }
      
      // Apply filter if provided
      let filteredAnomalies = mockAnomalies;
      if (filter) {
        filteredAnomalies = mockAnomalies.filter(a => 
          JSON.stringify(a).toLowerCase().includes(filter.toLowerCase())
        );
      }
      
      // Apply pagination
      const startIndex = (page - 1) * limit;
      const paginatedAnomalies = filteredAnomalies.slice(startIndex, startIndex + limit);
      
      return {
        items: paginatedAnomalies,
        totalItems: filteredAnomalies.length
      };
    } catch (error) {
      logger.error('Error in WazuhRepository.getOpenSearchAnomalies:', error);
      throw error;
    }
  }

  /**
   * Get recent OpenSearch anomalies
   * @param {number} limit - Number of anomalies to retrieve
   */
  async getRecentOpenSearchAnomalies(limit) {
    try {
      const result = await this.getOpenSearchAnomalies(1, limit);
      return result.items;
    } catch (error) {
      logger.error('Error in WazuhRepository.getRecentOpenSearchAnomalies:', error);
      throw error;
    }
  }

  /**
   * Get OpenSearch anomaly by ID
   * @param {string} id - Anomaly ID
   */
  async getOpenSearchAnomalyById(id) {
    try {
      // Mock implementation
      if (id.startsWith('anomaly-')) {
        const index = parseInt(id.split('-')[1]);
        return {
          id,
          timestamp: new Date(Date.now() - index * 3600000).toISOString(),
          score: Math.floor(Math.random() * 100),
          details: {
            description: `Unusual behavior detected in system metrics`,
            affected_resource: `Resource-${index % 10}`,
            anomaly_type: index % 3 === 0 ? 'CPU' : (index % 3 === 1 ? 'Memory' : 'Network')
          }
        };
      }
      
      return null;
    } catch (error) {
      logger.error(`Error in WazuhRepository.getOpenSearchAnomalyById for ${id}:`, error);
      throw error;
    }
  }
}

module.exports = new WazuhRepository();