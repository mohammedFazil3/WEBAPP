// app.js - Main application entry point
const express = require('express');
const path = require('path');
const cookieParser = require('cookie-parser');
const morgan = require('morgan');
const cors = require('cors');
const session = require('express-session');
const { errorHandler } = require('./middleware/error');
const config = require('./config/config');

// Import routes
const dashboardRoutes = require('./presentation layer - routes/dashboard');
const wazuhApiRoutes = require('./presentation layer - routes/api/wazuh');
const anomalyApiRoutes = require('./presentation layer - routes/api/anomaly');
const keystrokeApiRoutes = require('./presentation layer - routes/api/keystroke');
const keystrokeRoutes = require('./presentation layer - routes/keystroke');
const settingsRoutes = require('./presentation layer - routes/settings');

const wazuhService = require('./business layer - services/wazuh.service');
const keystrokeService = require('./business layer - services/keystroke.service');
const anomalyService = require('./business layer - services/anomaly.service');

const app = express();

// View engine setup
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'ejs');

// Middleware
app.use(cors());
app.use(morgan('dev'));
app.use(express.json());
app.use(express.urlencoded({ extended: false }));
app.use(cookieParser());
app.use(express.static(path.join(__dirname, 'public')));
app.use(session({
  secret: config.sessionSecret,
  resave: false,
  saveUninitialized: true,
  cookie: { secure: config.env === 'production' }
}));

// Routes
app.use('/', dashboardRoutes);
app.use('/api/wazuh', wazuhApiRoutes);
app.use('/api/anomaly', anomalyApiRoutes);
app.use('/api/keystroke', keystrokeApiRoutes);
app.use('/keystroke', keystrokeRoutes);
app.use('/settings', settingsRoutes);

// Error handling
app.use(errorHandler);

// Start the server
const PORT = config.port || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

module.exports = app;