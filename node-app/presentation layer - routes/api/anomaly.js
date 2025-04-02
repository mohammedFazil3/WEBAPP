const express = require('express');
const router = express.Router();
const anomalyService = require('../../business layer - services/anomaly.service');
const logger = require('../../config/winston');

// Get anomaly summary
router.get('/summary', async (req, res, next) => {
  try {
    const summary = await anomalyService.getSummary();
    res.json(summary);
  } catch (error) {
    logger.error('Error getting anomaly summary:', error);
    next(error);
  }
});

// Get recent anomaly alerts
router.get('/recent', async (req, res, next) => {
  try {
    const limit = parseInt(req.query.limit) || 10;
    const alerts = await anomalyService.getRecentAlerts(limit);
    res.json(alerts);
  } catch (error) {
    logger.error('Error getting recent anomaly alerts:', error);
    next(error);
  }
});

// Get all anomaly alerts with pagination
router.get('/alerts', async (req, res, next) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 10;
    const filter = req.query.filter;
    
    const result = await anomalyService.getAlerts(page, limit, filter);
    res.json(result);
  } catch (error) {
    logger.error('Error getting anomaly alerts:', error);
    next(error);
  }
});

// Get specific anomaly alert by ID
router.get('/alerts/:id', async (req, res, next) => {
  try {
    const alert = await anomalyService.getAlertById(req.params.id);
    if (!alert) {
      return res.status(404).json({ message: 'Alert not found' });
    }
    res.json(alert);
  } catch (error) {
    logger.error(`Error getting anomaly alert ${req.params.id}:`, error);
    next(error);
  }
});

module.exports = router; 