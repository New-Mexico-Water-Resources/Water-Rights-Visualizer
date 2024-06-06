const express = require("express");
const router = express.Router();
const path = require("path");
const fs = require("fs");
const constants = require("../constants");

const run_directory_base = constants.run_directory_base;

router.get("/geojson", (req, res) => {
  let name = req.query.name;
  let key = req.query.key;
  let run_directory = path.join(run_directory_base, key);
  let geojson_filename = path.join(run_directory, `${name}.geojson`);
  console.log(`reading GeoJSON from ${geojson_filename}`);
  let geojson = fs.readFileSync(geojson_filename, "utf8");
  console.log("GeoJSON:");
  console.log(geojson);
  res.status(200).send(geojson);
});

module.exports = router;
