const express = require('express');
const router = express.Router();
const path = require('path');
const fs = require('fs');
const constants = require('./constants');

const project_directory = constants.project_directory;
const run_directory_base = constants.run_directory_base;

router.get('/result', (req, res) => {
  console.log("/result")
  var name = req.query.name;
  console.log(`name: ${name}`);
  var year = req.query.year;
  console.log(`year: ${year}`);
  // var image_filename = path.join(project_directory, "test_images", `${year}_${name}.png`);
  var image_filename = path.join(run_directory_base, name, "output", "figures", `${year}_${name}.png`);
  console.log(`reading image from ${image_filename}`);

  if (fs.existsSync(image_filename)) {
      res.status(200).sendFile(image_filename);
  } else {
      res.status(404).send(`figure for ${name} ${year} is not available`);
  }
});

module.exports = router;
