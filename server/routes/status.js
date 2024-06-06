const express = require("express");
const router = express.Router();
const path = require("path");
const fs = require("fs");
const constants = require("../constants");

const run_directory_base = constants.run_directory_base;

const scanForYears = (directory) => {
  if (!fs.existsSync(directory) || fs.readdirSync(directory).length === 0) {
    return { years: [], count: 0 };
  }

  const files = fs.readdirSync(directory);
  const yearFiles = files.filter((file) => file.match(/^\d{4}\./)).map((file) => parseInt(file.split(".")[0]));
  let uniqueYears = new Set(yearFiles);

  return { years: Array.from(uniqueYears).sort((a, b) => a - b), count: yearFiles.length };
};

router.get("/job/status", (req, res) => {
  let key = req.query.key;
  let jobName = req.query.name;

  if (!key) {
    res.status(400).send("key parameter is required");
    return;
  }

  let run_directory = path.join(run_directory_base, key);
  let status_filename = path.join(run_directory, "status.txt");
  let jobStatus = fs.existsSync(status_filename) ? fs.readFileSync(status_filename, "utf8") : "unknown";

  let report_queue_file = path.join(run_directory_base, "report_queue.json");
  fs.readFile(report_queue_file, (err, data) => {
    let report_queue = [];

    if (err) {
      console.error(`Error reading ${report_queue_file}`);
      res.status(500).send("Error reading report queue");
      return;
    }

    try {
      report_queue = JSON.parse(data);
    } catch (e) {
      console.error(`Error parsing JSON from ${report_queue_file}`);
      res.status(500).send("Error parsing report queue");
      return;
    }

    let job = report_queue.find((entry) => entry.key === key);
    if (!job) {
      res.status(404).send("Job not found");
      return;
    }

    let totalYears = job.end_year - job.start_year + 1;
    let processedYears = scanForYears(path.join(run_directory, "output", "subset", jobName));
    let currentYear = processedYears.years.length;

    res.status(200).send({ status: jobStatus, currentYear, totalYears, fileCount: processedYears.count });
  });
});

module.exports = router;
