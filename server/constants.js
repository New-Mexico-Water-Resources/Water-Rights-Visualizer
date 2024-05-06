const path = require('path');
const port = 8000;
const server_directory = __dirname;

// Use the first command line argument as the project directory if it exists, otherwise use __dirname
const project_directory = process.argv[2] ? path.resolve(process.argv[2]) : __dirname;

const run_directory_base = path.join(project_directory, 'runs');

module.exports = {
  port,
  server_directory,
  project_directory,
  run_directory_base
};
