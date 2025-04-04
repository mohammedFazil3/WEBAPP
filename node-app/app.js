// app.js
const express = require('express');
const bodyParser = require('body-parser');
const fileupload = require('express-fileupload');
const handlebars = require('express-handlebars');

// Import routes
const htmlPresentation = require('./presentation layer - routes/htmlPresentation');

// Initializing the Express app
let app = express();

// Middleware setup
app.use(fileupload());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use("/static", express.static(__dirname + "/static"));

// Setting up view engine with Handlebars
app.set('views', __dirname + "/presentation layer - routes/templates");
app.set('view engine', 'handlebars');
app.engine('handlebars', handlebars.engine({
  defaultLayout: false // No layout for simplicity
}));

// Set root route to user registration
app.get('/', (req, res) => {
  res.redirect('/user-registration');
});

// Use route modules
app.use('/', htmlPresentation);

// Start the server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});

module.exports = app;