// middleware/error.js
const logger = require('../config/winston');

/**
 * Global error handler middleware
 */
exports.errorHandler = (err, req, res, next) => {
  // Log the error
  logger.error('Unhandled exception:', err);

  // Determine status code
  const statusCode = err.statusCode || 500;

  // Send response based on request type
  if (req.accepts('html')) {
    // HTML response
    res.status(statusCode).render('error', {
      message: err.message || 'Something went wrong!',
      error: process.env.NODE_ENV === 'development' ? err : {}
    });
  } else {
    // API/JSON response
    res.status(statusCode).json({
      error: true,
      message: err.message || 'Internal Server Error',
      stack: process.env.NODE_ENV === 'development' ? err.stack : undefined
    });
  }
};

// middleware/auth.js
/**
 * Authentication middleware to secure routes
 */
exports.authenticate = (req, res, next) => {
  if (req.session && req.session.user) {
    // User is authenticated
    return next();
  }

  // User is not authenticated, redirect to login
  if (req.accepts('html')) {
    return res.redirect('/login');
  } else {
    return res.status(401).json({
      error: true,
      message: 'Authentication required'
    });
  }
};