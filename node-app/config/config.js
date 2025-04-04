// config/config.js
require('dotenv').config();

module.exports = {
  env: process.env.NODE_ENV || 'development',
  port: process.env.PORT || 3000,
  sessionSecret: process.env.SESSION_SECRET || 'hids-secret-key',
  
  // Wazuh API configuration
  wazuh: {
    protocol: process.env.WAZUH_PROTOCOL || 'https',
    host: process.env.WAZUH_HOST || 'localhost',
    port: process.env.WAZUH_PORT || 55000,
    user: process.env.WAZUH_USER || 'wazuh',
    password: process.env.WAZUH_PASSWORD || 'wazuh',
    timeout: process.env.WAZUH_TIMEOUT || 30000
  },
  
  // OpenSearch configuration (if separate from Wazuh)
  openSearch: {
    protocol: process.env.OPENSEARCH_PROTOCOL || 'https',
    host: process.env.OPENSEARCH_HOST || 'localhost',
    port: process.env.OPENSEARCH_PORT || 9200,
    user: process.env.OPENSEARCH_USER || 'admin',
    password: process.env.OPENSEARCH_PASSWORD || 'admin',
    timeout: process.env.OPENSEARCH_TIMEOUT || 30000
  },
  
  // Keystroke AI service configuration
  keystrokeAI: {
    url: process.env.KEYSTROKE_API_URL || 'http://127.0.0.1:5000',
    timeout: process.env.KEYSTROKE_TIMEOUT || 60000
  }
};

