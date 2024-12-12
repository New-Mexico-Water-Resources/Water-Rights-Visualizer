const express = require("express");
const router = express.Router();
const path = require("path");
const fs = require("fs");
const constants = require("../constants");

const run_directory_base = constants.run_directory_base;
const project_directory = constants.project_directory;

router.get("/geojson", (req, res) => {
  let name = req.query.name;
  let key = req.query.key;
  let run_directory = path.join(run_directory_base, key);
  let geojson_filename = path.join(run_directory, `${name}.geojson`);
  console.log(`reading GeoJSON from ${geojson_filename}`);
  let geojson = fs.readFileSync(geojson_filename, "utf8");
  res.status(200).send(geojson);
});

router.get("/ard_tiles", (req, res) => {
  let waterRightsDir = path.join(project_directory, "water_rights_visualizer");

  let ard_tiles_filename = path.join(waterRightsDir, "ARD_tiles.geojson");
  let ard_tiles = fs.readFileSync(ard_tiles_filename, "utf8");
  res.status(200).send(ard_tiles);
});

module.exports = router;
