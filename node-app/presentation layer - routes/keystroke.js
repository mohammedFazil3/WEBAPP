const express = require('express');
const router = express.Router();
const keystrokeService = require('../business layer - services/keystroke.service');

// Keystroke overview
router.get('/overview', async (req, res, next) => {
  try {
    const summary = await keystrokeService.getSummary();
    const activeModel = await keystrokeService.getActiveModel();
    const recentAlerts = await keystrokeService.getRecentAlerts(5);
    
    res.render('keystroke/overview', {
      summary,
      activeModel,
      recentAlerts
    });
  } catch (error) {
    next(error);
  }
});

// Keystroke models
router.get('/models', async (req, res, next) => {
  try {
    const models = await keystrokeService.getAllModels();
    res.render('keystroke/models', { models });
  } catch (error) {
    next(error);
  }
});

// Fixed-text model management
router.get('/fixed-text', async (req, res, next) => {
  try {
    const model = await keystrokeService.getModelDetails('fixed-text');
    res.render('keystroke/fixed-text', { model });
  } catch (error) {
    next(error);
  }
});

router.get('/fixed-text/train', async (req, res, next) => {
  try {
    res.render('keystroke/fixed-text-train');
  } catch (error) {
    next(error);
  }
});

router.post('/fixed-text/train', async (req, res, next) => {
  try {
    const trainingOptions = {
      intervalType: req.body.intervalType,
      customInterval: req.body.customInterval,
      parameters: {
        iterations: parseInt(req.body.iterations) || 100,
        learning_rate: parseFloat(req.body.learning_rate) || 0.05,
        depth: parseInt(req.body.depth) || 4
      }
    };
    
    const jobId = await keystrokeService.trainModel('fixed-text', trainingOptions);
    res.redirect(`/keystroke/training-status/${jobId}`);
  } catch (error) {
    next(error);
  }
});

// Free-text model management
router.get('/free-text', async (req, res, next) => {
  try {
    const model = await keystrokeService.getModelDetails('free-text');
    const dataCollectionStatus = await keystrokeService.getDataCollectionStatus();
    
    res.render('keystroke/free-text', { 
      model,
      dataCollectionStatus
    });
  } catch (error) {
    next(error);
  }
});

// Multi-binary model management
router.get('/multi-binary', async (req, res, next) => {
  try {
    const model = await keystrokeService.getModelDetails('multi-binary');
    const users = await keystrokeService.getMultiBinaryUsers();
    
    res.render('keystroke/multi-binary', { 
      model,
      users 
    });
  } catch (error) {
    next(error);
  }
});

// Training status page
router.get('/training-status/:jobId', async (req, res, next) => {
  try {
    const jobId = req.params.jobId;
    const initialStatus = await keystrokeService.getTrainingStatus(jobId);
    
    res.render('keystroke/training-status', { 
      jobId,
      initialStatus 
    });
  } catch (error) {
    next(error);
  }
});

// Keystroke schedule management
router.get('/schedule', async (req, res, next) => {
  try {
    const schedules = await keystrokeService.getSchedules();
    res.render('keystroke/schedule', { schedules });
  } catch (error) {
    next(error);
  }
});

router.post('/schedule', async (req, res, next) => {
  try {
    const scheduleData = {
      modelType: req.body.modelType,
      operationType: req.body.operationType,
      intervalType: req.body.intervalType,
      customInterval: req.body.customInterval,
      nextRunTime: new Date(req.body.nextRunTime),
      parameters: req.body.parameters
    };
    
    await keystrokeService.createSchedule(scheduleData);
    res.redirect('/keystroke/schedule');
  } catch (error) {
    next(error);
  }
});

module.exports = router; 