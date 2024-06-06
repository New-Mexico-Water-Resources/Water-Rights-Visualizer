const express = require("express");
const router = express.Router();
const path = require("path");
const fs = require("fs");
const constants = require("../constants");

const project_directory = constants.project_directory;
const run_directory_base = constants.run_directory_base;

router.get("/result_base64", (req, res) => {
  var name = req.query.name;
  console.log(`name: ${name}`);
  var year = req.query.year;
  console.log(`year: ${year}`);
  var image_filename = path.join(project_directory, "test_images", `${year}_${name}.png`);
  console.log(`reading image from ${image_filename}`);

  if (fs.existsSync(image_filename)) {
    fs.readFile(image_filename, (err, data) => {
      if (err) {
        res.status(500).send(`Error reading image file: ${err}`);
      } else {
        var base64Image = new Buffer.from(data).toString("base64");
        var dataURI = "data:image/png;base64," + base64Image;
        res.status(200).send(dataURI);
      }
    });
  } else {
    res.status(404).send(`figure for ${name} ${year} is not available`);
  }
});

module.exports = router;
