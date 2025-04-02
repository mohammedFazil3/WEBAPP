const express = require('express');
const router = express.Router();
const keystrokeService = require('../../business layer - services/keystroke.service');

// Get training status
router.get('/status/:jobId', async (req, res, next) => {
  try {
    const jobId = req.params.jobId;
    const status = await keystrokeService.getTrainingStatus(jobId);
    res.json(status);
  } catch (error) {
    next(error);
  }
});

// Train model
router.post('/train', async (req, res, next) => {
  try {
    const { modelType, parameters } = req.body;
    const jobId = await keystrokeService.trainModel(modelType, parameters);
    res.json({ jobId });
  } catch (error) {
    next(error);
  }
});

// Make prediction
router.post('/predict', async (req, res, next) => {
  try {
    const { modelType, data } = req.body;
    const result = await keystrokeService.predict(modelType, data);
    res.json(result);
  } catch (error) {
    next(error);
  }
});

// Switch active model
router.put('/switch/:modelType', async (req, res, next) => {
  try {
    const modelType = req.params.modelType;
    await keystrokeService.switchActiveModel(modelType);
    res.json({ success: true, message: `Switched to ${modelType} model` });
  } catch (error) {
    next(error);
  }
});

// Schedule management
router.get('/schedule', async (req, res, next) => {
  try {
    const schedules = await keystrokeService.getSchedules();
    res.json(schedules);
  } catch (error) {
    next(error);
  }
});

router.post('/schedule/create', async (req, res, next) => {
  try {
    const scheduleData = req.body;
    const schedule = await keystrokeService.createSchedule(scheduleData);
    res.json(schedule);
  } catch (error) {
    next(error);
  }
});

router.put('/schedule/:id', async (req, res, next) => {
  try {
    const id = req.params.id;
    const scheduleData = req.body;
    const schedule = await keystrokeService.updateSchedule(id, scheduleData);
    res.json(schedule);
  } catch (error) {
    next(error);
  }
});

router.delete('/schedule/:id', async (req, res, next) => {
  try {
    const id = req.params.id;
    await keystrokeService.deleteSchedule(id);
    res.json({ success: true });
  } catch (error) {
    next(error);
  }
});

module.exports = router; 