const os = require("os");
const path = require("path");
const port = 5000;
const server_directory = __dirname;
const project_directory = path.dirname(__dirname);
// const run_directory_base = '~/data/water_rights_runs';
const run_directory_base = process.env.RUN_DIRECTORY_BASE || path.join(os.homedir(), "data/water_rights_runs");

module.exports = {
  port,
  server_directory,
  project_directory,
  run_directory_base,
};
