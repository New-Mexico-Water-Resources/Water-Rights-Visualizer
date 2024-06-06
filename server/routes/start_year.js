const express = require("express");
const router = express.Router();
const path = require("path");
const fs = require("fs");
const constants = require("../constants");

const run_directory_base = constants.run_directory_base;

router.get("/start_year", (req, res) => {
  let name = req.query.name;
  let key = req.query.key;
  let run_directory = path.join(run_directory_base, key);
  let start_year_filename = path.join(run_directory, "start_year.txt");
  console.log(`reading start year from ${start_year_filename}`);
  let start_year = fs.readFileSync(start_year_filename, "utf8");
  console.log(`start year: ${start_year}`);
  res.status(200).send(start_year);
});

module.exports = router;
