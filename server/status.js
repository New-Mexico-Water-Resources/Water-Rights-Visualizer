const express = require('express');
const router = express.Router();
const path = require('path');
const fs = require('fs');
const constants = require('./constants');

const run_directory_base = constants.run_directory_base;

router.get('/status', (req, res) => {
  var name = req.query.name;
  var run_directory = path.join(run_directory_base, name);
  var status_filename = path.join(run_directory, "status.txt");
  console.log(`reading status from ${status_filename}`);
  var status = fs.readFileSync(status_filename, 'utf8');
  console.log(`status: ${status}`);
  res.status(200).send(status);
});

module.exports = router;
