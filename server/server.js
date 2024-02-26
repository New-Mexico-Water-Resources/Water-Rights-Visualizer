require('log-timestamp');
const express = require('express');
const cors = require('cors'); // Don't forget to install this package using npm
const path = require('path');
const fs = require('fs');
const status = require('./status');
const start_year = require('./start_year');
const end_year = require('./end_year');
const years_available = require('./years_available');
const geojson = require('./geojson');
const result = require('./result');
const result_base64 = require('./result_base64');
const download = require('./download');
const start_run = require('./start_run');
const runs = require('./runs');
const prepare_geojson = require('./prepare_geojson');
const constants = require('./constants');

const working_directory = process.cwd();
const run_directory_base = constants.run_directory_base;
const html_path = path.join(path.dirname(__dirname), 'page');
const port = constants.port;

// const argv = process.argv.slice(2);
// const demo_mode = argv[0] == "demo";


console.log(`starting server on port ${port}`);
console.log(`run directory: ${run_directory_base}`);
console.log(`working directory: ${working_directory}`);

const app = express();

app.use(cors()); // Use CORS middleware
app.use(express.json());
app.use(express.static(html_path));

app.use('/', status);
app.use('/', start_year);
app.use('/', end_year);
app.use('/', years_available);
app.use('/', geojson);
app.use('/', result);
app.use('/', result_base64);
app.use('/', download);
app.use('/', start_run);
app.use('/', runs);
app.post('/prepare_geojson', prepare_geojson.upload.single('file'), prepare_geojson.prepareGeojson);

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});
