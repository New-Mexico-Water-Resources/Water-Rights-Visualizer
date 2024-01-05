const express = require('express');
const router = express.Router();
const path = require('path');
const fs = require('fs');
const constants = require('./constants');

const run_directory_base = constants.run_directory_base;

router.get('/end_year', (req, res) => {
  var name = req.query.name;
  var run_directory = path.join(run_directory_base, name);
  var end_year_filename = path.join(run_directory, "end_year.txt");
  console.log(`reading end year from ${end_year_filename}`);
  var end_year = fs.readFileSync(end_year_filename, 'utf8');
  console.log(`end year: ${end_year}`);
  res.status(200).send(end_year);
});

module.exports = router;
