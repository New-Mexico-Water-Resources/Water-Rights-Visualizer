const express = require("express");
const router = express.Router();
const path = require("path");
const fs = require("fs");
const constants = require("../constants");

const run_directory_base = constants.run_directory_base;

function getDirectories(path) {
  return fs.readdirSync(path).filter(function (file) {
    return fs.statSync(path + "/" + file).isDirectory();
  });
}

router.get("/runs", (req, res) => {
  var runs = getDirectories(run_directory_base);
  console.log(`status: ${runs}`);
  res.status(200).send(runs);
});

module.exports = router;
