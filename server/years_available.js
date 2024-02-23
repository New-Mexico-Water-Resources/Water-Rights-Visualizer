const express = require('express');
const router = express.Router();
const path = require('path');
const fs = require('fs');
const constants = require('./constants');

const project_directory = constants.project_directory;
const run_directory_base = constants.run_directory_base;

function years_available(directory) {
  if (!fs.existsSync(directory) || fs.readdirSync(directory).length === 0) {
    return [];
  }

  const files = fs.readdirSync(directory);
  const pngFiles = files.filter(file => file.endsWith('.png'));
  const years = pngFiles.map(file => parseInt(file.split('_')[0]));

  return years.sort((a, b) => a - b);
}

router.get('/years_available', (req, res) => {
  var name = req.query.name;
  console.log(`name: ${name}`);
  var image_directory = path.join(run_directory_base, name, "output", "figures");
  console.log(`scanning image directory: ${image_directory}`);
  var year_list = years_available(image_directory);

  res.status(200).send(year_list);
});

module.exports = router;
