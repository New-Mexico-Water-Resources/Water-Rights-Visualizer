const express = require("express");
const router = express.Router();
const path = require("path");
const fs = require("fs");
const constants = require("../constants");

const run_directory_base = constants.run_directory_base;

const calculateYearsProcessed = (directory, startYear, endYear, startTime) => {
  if (!fs.existsSync(directory) || fs.readdirSync(directory).length === 0) {
    return { years: [], count: 0, estimatedPercentComplete: 0, timeRemaining: 0 };
  }

  const files = fs.readdirSync(directory);
  const yearFiles = files.filter((file) => file.match(/^\d{4}\./)).map((file) => parseInt(file.split(".")[0]));

  let yearCounts = {};
  yearFiles.forEach((year) => {
    yearCounts[year] = yearCounts[year] ? yearCounts[year] + 1 : 1;
  });

  let uniqueYears = new Set(Object.keys(yearCounts));
  let sortedYears = Array.from(uniqueYears).sort((a, b) => a - b);

  // Start with a default of 258 files per year
  let averageFilesPerYear = 258;
  let estimatedTotalFiles = 258 * (endYear - startYear + 1);
  if (sortedYears.length > 1) {
    // Exclude the current year from the average as this may not be complete
    let currentYearProcessing = sortedYears[sortedYears.length - 1];
    let currentYearCount = yearCounts[currentYearProcessing];

    let totalFiles = yearFiles.length - currentYearCount;
    let totalYears = sortedYears.length - 1;

    averageFilesPerYear = totalFiles / totalYears;

    let remainingFilesForCurrentYear = Math.max(averageFilesPerYear - currentYearCount, 0);

    // Estimate the total number of files based on the current files + remaining files for this year + the average files per year for remaining
    estimatedTotalFiles =
      yearFiles.length + remainingFilesForCurrentYear + averageFilesPerYear * (endYear - currentYearProcessing);
  }

  let estimatedPercentComplete =
    estimatedTotalFiles > 0 ? yearFiles.length / Math.max(yearFiles.length, estimatedTotalFiles) : 0;

  let timeRemaining = 0;

  if (startTime && estimatedPercentComplete > 0 && estimatedPercentComplete < 1) {
    let timeElapsed = Date.now() - startTime;

    timeRemaining = timeElapsed / estimatedPercentComplete - timeElapsed;
  } else if (estimatedPercentComplete === 0 || !startTime) {
    // Estimate 3.5 minutes per year
    timeRemaining = (endYear - startYear + 1) * 3.5 * 60 * 1000;
  }

  return { years: sortedYears, count: yearFiles.length, estimatedPercentComplete, timeRemaining };
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
    let processedYears = calculateYearsProcessed(
      path.join(run_directory, "output", "subset", jobName),
      job.start_year,
      job.end_year,
      job.started
    );

    res.status(200).send({
      status: jobStatus,
      currentYear: processedYears.years.length,
      totalYears,
      fileCount: processedYears.count,
      estimatedPercentComplete: job.status === "Complete" ? 1 : processedYears.estimatedPercentComplete,
      timeRemaining: job.status === "Complete" ? 0 : processedYears.timeRemaining,
    });
  });
});

module.exports = router;
