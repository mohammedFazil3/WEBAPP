const express = require('express');
const router = express.Router();
const wazuhService = require('../../business layer - services/wazuh.service');

// Get agent status
router.get('/agent/status', async (req, res, next) => {
  try {
    const status = await wazuhService.getAgentStatus();
    res.json(status);
  } catch (error) {
    next(error);
  }
});

// Get FIM alerts
router.get('/fim', async (req, res, next) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 20;
    const filter = req.query.filter || '';
    
    const alerts = await wazuhService.getFIMAlerts(page, limit, filter);
    res.json(alerts);
  } catch (error) {
    next(error);
  }
});

// Get malware alerts
router.get('/malware', async (req, res, next) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 20;
    const filter = req.query.filter || '';
    
    const alerts = await wazuhService.getMalwareAlerts(page, limit, filter);
    res.json(alerts);
  } catch (error) {
    next(error);
  }
});

// Get vulnerability alerts
router.get('/vulnerabilities', async (req, res, next) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 20;
    const filter = req.query.filter || '';
    
    const alerts = await wazuhService.getVulnerabilityAlerts(page, limit, filter);
    res.json(alerts);
  } catch (error) {
    next(error);
  }
});

module.exports = router; 