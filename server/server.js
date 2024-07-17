require("log-timestamp");
const express = require("express");
const cors = require("cors"); // Don't forget to install this package using npm
// const path = require('path');
// const fs = require('fs');
const status = require("./routes/status");
const logs = require("./routes/logs");
const start_year = require("./routes/start_year");
const end_year = require("./routes/end_year");
const years_available = require("./routes/years_available");
const geojson = require("./routes/geojson");
const result = require("./routes/result");
const result_base64 = require("./routes/result_base64");
const download = require("./routes/download");
const start_run = require("./routes/start_run/start_run");
const runs = require("./routes/runs");
const prepare_geojson = require("./routes/prepare_geojson/prepare_geojson");
const queue = require("./routes/queue/queue");
const constants = require("./constants");

const { auth } = require("express-oauth2-jwt-bearer");

const working_directory = process.cwd();
const run_directory_base = constants.run_directory_base;
// const html_path = path.join(path.dirname(__dirname), 'page');
const port = constants.port;

// const argv = process.argv.slice(2);
// const demo_mode = argv[0] == "demo";

console.log(`starting server on port ${port}`);
console.log(`run directory: ${run_directory_base}`);
console.log(`working directory: ${working_directory}`);

const app = express();

const verifyAuthToken = auth({
  audience: "https://nmw-dev.jpl.nasa.gov/api",
  issuerBaseURL: "https://water-rights-visualizer.us.auth0.com/",
  tokenSigningAlg: "RS256",
});

app.use(cors()); // Use CORS middleware
app.use(express.json());
// app.use(express.static(html_path));

const basePath = "/api";

// Health check
app.get(`${basePath}/`, (req, res) => {
  res.status(200).send({
    message: "New Mexico Water Rights Visualizer API is running",
  });
});

app.use(`${basePath}/`, verifyAuthToken, status);
app.use(`${basePath}/`, verifyAuthToken, logs);
app.use(`${basePath}/`, verifyAuthToken, start_year);
app.use(`${basePath}/`, verifyAuthToken, end_year);
app.use(`${basePath}/`, verifyAuthToken, years_available);
app.use(`${basePath}/`, verifyAuthToken, geojson);
app.use(`${basePath}/`, verifyAuthToken, result);
app.use(`${basePath}/`, verifyAuthToken, result_base64);
app.use(`${basePath}/`, verifyAuthToken, download);
app.use(`${basePath}/`, verifyAuthToken, start_run);
app.use(`${basePath}/`, verifyAuthToken, runs);
app.use(`${basePath}/queue`, queue);
app.post(`${basePath}/prepare_geojson`, prepare_geojson.upload.single("file"), prepare_geojson.prepareGeojson);

app.use((err, req, res, next) => {
  console.error("Error:", err.message, "Endpoint:", req.originalUrl);
  if (err.status === 401 || err.status === 403) {
    res.status(err.status).json({ error: "Unauthorized access" });
  } else {
    res.status(500).json({ error: "Internal Server Error" });
  }
});

app.listen(port, () => {
  console.log(`API running on http://localhost:${port}${basePath}`);
});
