// routes/dashboard.js
const express = require('express');
const router = express.Router();
const wazuhService = require('../business layer - services/wazuh.service');
const anomalyService = require('../business layer - services/anomaly.service');
const keystrokeService = require('../business layer - services/keystroke.service');

// Main dashboard route
router.get('/', async (req, res, next) => {
  try {
    // Get summary data from all services
    const [wazuhSummary, anomalySummary, keystrokeSummary] = await Promise.all([
      wazuhService.getSummary(),
      anomalyService.getSummary(),
      keystrokeService.getSummary()
    ]);

    // Combine all alerts for the unified view
    const recentAlerts = await Promise.all([
      wazuhService.getRecentAlerts(10),
      anomalyService.getRecentAlerts(10),
      keystrokeService.getRecentAlerts(10)
    ]).then(([wazuhAlerts, anomalyAlerts, keystrokeAlerts]) => {
      return [...wazuhAlerts, ...anomalyAlerts, ...keystrokeAlerts]
        .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
        .slice(0, 10);
    });

    res.render('dashboard/index', {
      wazuhSummary,
      anomalySummary,
      keystrokeSummary,
      recentAlerts
    });
  } catch (error) {
    next(error);
  }
});

// Unified alerts view
router.get('/alerts', async (req, res, next) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 20;
    const filter = req.query.filter || '';
    const source = req.query.source || 'all';

    let alerts = [];
    let totalCount = 0;

    if (source === 'all' || source === 'wazuh') {
      const wazuhAlerts = await wazuhService.getAlerts(page, limit, filter);
      alerts = [...alerts, ...wazuhAlerts.alerts];
      totalCount += wazuhAlerts.totalCount;
    }

    if (source === 'all' || source === 'anomaly') {
      const anomalyAlerts = await anomalyService.getAlerts(page, limit, filter);
      alerts = [...alerts, ...anomalyAlerts.alerts];
      totalCount += anomalyAlerts.totalCount;
    }

    if (source === 'all' || source === 'keystroke') {
      const keystrokeAlerts = await keystrokeService.getAlerts(page, limit, filter);
      alerts = [...alerts, ...keystrokeAlerts.alerts];
      totalCount += keystrokeAlerts.totalCount;
    }

    // Sort alerts by timestamp (newest first)
    alerts.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

    // If combined sources, we need to slice manually
    if (source === 'all') {
      const startIndex = (page - 1) * limit;
      alerts = alerts.slice(startIndex, startIndex + limit);
    }

    res.render('dashboard/alerts', {
      alerts,
      currentPage: page,
      totalPages: Math.ceil(totalCount / limit),
      totalCount,
      filter,
      source
    });
  } catch (error) {
    next(error);
  }
});

// Detailed alert view
router.get('/alerts/:id', async (req, res, next) => {
  try {
    const alertId = req.params.id;
    const source = req.query.source;

    let alert;
    switch (source) {
      case 'wazuh':
        alert = await wazuhService.getAlertById(alertId);
        break;
      case 'anomaly':
        alert = await anomalyService.getAlertById(alertId);
        break;
      case 'keystroke':
        alert = await keystrokeService.getAlertById(alertId);
        break;
      default:
        // Try to find in all sources
        alert = await Promise.any([
          wazuhService.getAlertById(alertId),
          anomalyService.getAlertById(alertId),
          keystrokeService.getAlertById(alertId)
        ]);
    }

    if (!alert) {
      return res.status(404).render('error', {
        message: 'Alert not found',
        error: { status: 404 }
      });
    }

    res.render('dashboard/alert-detail', { alert, source });
  } catch (error) {
    next(error);
  }
});

module.exports = router;