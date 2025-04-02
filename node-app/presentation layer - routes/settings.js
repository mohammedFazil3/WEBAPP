const express = require('express');
const router = express.Router();
const wazuhService = require('../business layer - services/wazuh.service');
const keystrokeService = require('../business layer - services/keystroke.service');

// Settings overview
router.get('/', async (req, res, next) => {
  try {
    res.render('settings/index');
  } catch (error) {
    next(error);
  }
});

// WAZUH configuration settings
router.get('/wazuh', async (req, res, next) => {
  try {
    const wazuhStatus = await wazuhService.getAgentStatus();
    res.render('settings/wazuh', { wazuhStatus });
  } catch (error) {
    next(error);
  }
});

// Keystroke AI settings
router.get('/keystroke', async (req, res, next) => {
  try {
    const activeModel = await keystrokeService.getActiveModel();
    const models = await keystrokeService.getAllModels();
    res.render('settings/keystroke', { activeModel, models });
  } catch (error) {
    next(error);
  }
});

// Threshold settings
router.get('/thresholds', async (req, res, next) => {
  try {
    // Get current thresholds
    const thresholds = {
      wazuh: {
        fim: 75,
        malware: 90,
        vulnerability: 60
      },
      keystroke: {
        confidence: 80
      }
    };
    
    res.render('settings/thresholds', { thresholds });
  } catch (error) {
    next(error);
  }
});

router.post('/thresholds', async (req, res, next) => {
  try {
    // Update thresholds (in a real app, this would save to a database)
    const newThresholds = {
      wazuh: {
        fim: parseInt(req.body.wazuh_fim) || 75,
        malware: parseInt(req.body.wazuh_malware) || 90,
        vulnerability: parseInt(req.body.wazuh_vulnerability) || 60
      },
      keystroke: {
        confidence: parseInt(req.body.keystroke_confidence) || 80
      }
    };
    
    // Save thresholds (mock implementation)
    res.redirect('/settings/thresholds');
  } catch (error) {
    next(error);
  }
});

// Notification settings
router.get('/notifications', async (req, res, next) => {
  try {
    res.render('settings/notifications');
  } catch (error) {
    next(error);
  }
});

module.exports = router; 