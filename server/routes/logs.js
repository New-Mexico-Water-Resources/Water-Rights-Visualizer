const express = require("express");
const router = express.Router();
const path = require("path");
const fs = require("fs");
const constants = require("../constants");

const run_directory_base = constants.run_directory_base;

router.get("/job/logs", (req, res) => {
  let key = req.query.key;
  if (!key) {
    res.status(400).send("key parameter is required");
    return;
  }

  let run_directory = path.join(run_directory_base, key);
  let log_file = path.join(run_directory, "exec_report_log.txt");
  if (!fs.existsSync(log_file)) {
    res.status(200).send({ logs: "" });
    return;
  }

  console.log(`reading logs from ${log_file}`);
  let logs = fs.readFileSync(log_file, "utf8");
  res.status(200).send({ logs });
});

module.exports = router;
