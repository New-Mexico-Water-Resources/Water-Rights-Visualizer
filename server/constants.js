const path = require('path');
const port = 80;
const server_directory = __dirname;
const project_directory = path.dirname(__dirname);
const run_directory_base = path.join(project_directory, 'runs');

module.exports = {
  port,
  server_directory,
  project_directory,
  run_directory_base
};
