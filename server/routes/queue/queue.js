const express = require("express");
const router = express.Router();
const path = require("path");
const fs = require("fs");
const constants = require("../../constants");

router.get("/list", async (req, res) => {
  let canReadJobs = req.auth?.payload?.permissions?.includes("read:jobs") || false;
  if (!canReadJobs) {
    res.status(401).send("Unauthorized: missing read:jobs permission");
    return;
  }

  let db = await constants.connectToDatabase();
  let collection = db.collection(constants.report_queue_collection);
  let result = await collection.find({}).toArray();
  res.status(200).send(result);
});

router.delete("/delete_job", async (req, res) => {
  let canWriteJobs = req.auth?.payload?.permissions?.includes("write:jobs") || false;
  if (!canWriteJobs) {
    res.status(401).send("Unauthorized: missing write:jobs permission");
    return;
  }

  let key = req.query.key;
  let deleteFiles = req.query.deleteFiles;

  if (!key) {
    res.status(400).send("Missing key");
    return;
  }

  let db = await constants.connectToDatabase();
  let collection = db.collection(constants.report_queue_collection);
  let job = await collection.findOne({ key });

  if (!job) {
    res.status(404).send("Job not found");
    return;
  }

  if (!["Complete", "Failed"].includes(job.status) && job.pid) {
    try {
      process.kill(job.pid, "SIGKILL");
    } catch (e) {
      console.error(`Error killing process ${job.pid}`, e);
    }
  }

  let result = await collection.deleteOne({ key });

  if (deleteFiles && job.base_dir) {
    fs.rmdir(job.base_dir, { recursive: true }, (err) => {
      if (err) {
        console.error(`Error deleting ${job.base_dir}`, err);
      }
    });
  }

  res.status(200).send(result);
});

router.delete("/bulk_delete_jobs", async (req, res) => {
  let canWriteJobs = req.auth?.payload?.permissions?.includes("write:jobs") || false;
  if (!canWriteJobs) {
    res.status(401).send("Unauthorized: missing write:jobs permission");
    return;
  }

  let keys = req.body.keys;
  let deleteFiles = req.query.deleteFiles;

  if (!keys) {
    res.status(400).send("Missing keys");
  }

  let db = await constants.connectToDatabase();
  let collection = db.collection(constants.report_queue_collection);
  let deleted = await collection.deleteMany({ key: { $in: keys } });

  let jobs = await collection.find({ key: { $in: keys } }).toArray();
  jobs.forEach((job) => {
    if (!["Complete", "Failed"].includes(job.status) && job.pid) {
      try {
        process.kill(job.pid, "SIGKILL");
      } catch (e) {
        console.error(`Error killing process ${job.pid}`, e);
      }
    }

    if (deleteFiles && job.base_dir) {
      fs.rmdir(job.base_dir, { recursive: true }, (err) => {
        if (err) {
          console.error(`Error deleting ${job.base_dir}`, err);
        }
      });
    }
  });

  res.status(200).send(deleted);
});

module.exports = router;
