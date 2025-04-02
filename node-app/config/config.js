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
    url: process.env.KEYSTROKE_API_URL || 'http://localhost:5000',
    timeout: process.env.KEYSTROKE_TIMEOUT || 60000
  }
};

// config/winston.js
const winston = require('winston');
const path = require('path');

// Define log format
const logFormat = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
  winston.format.errors({ stack: true }),
  winston.format.splat(),
  winston.format.json()
);

// Define logger
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: logFormat,
  transports: [
    // Console transport
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.printf(({ level, message, timestamp, ...metadata }) => {
          return `${timestamp} ${level}: ${message} ${
            Object.keys(metadata).length ? JSON.stringify(metadata, null, 2) : ''
          }`;
        })
      )
    }),
    // File transport - error logs
    new winston.transports.File({
      filename: path.join(__dirname, '../logs/error.log'),
      level: 'error'
    }),
    // File transport - combined logs
    new winston.transports.File({
      filename: path.join(__dirname, '../logs/combined.log')
    })
  ]
});

module.exports = logger;