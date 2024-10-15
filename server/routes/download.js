const express = require("express");
const archiver = require("archiver");
const glob = require("glob");
const router = express.Router();
const path = require("path");
const fs = require("fs");
const constants = require("../constants");

const project_directory = constants.project_directory;
const run_directory_base = constants.run_directory_base;

router.get("/download", function (req, res) {
  let key = req.query.key;
  let name = req.query.name;

  let archive = archiver("zip", {
    zlib: { level: 9 }, // Sets the compression level.
  });

  archive.on("end", function () {
    console.log("Archive wrote %d bytes", archive.pointer());
  });

  archive.on("warning", function (err) {
    if (err.code === "ENOENT") {
      console.log(err);
    } else {
      throw err;
    }
  });

  archive.on("error", function (err) {
    throw err;
  });

  res.setHeader("Content-Type", "application/zip");
  res.setHeader("Content-Disposition", `attachment; filename=${name}.zip`);

  archive.pipe(res);

  let figure_directory = path.join(run_directory_base, key, "output", "figures", name);

  if (!fs.existsSync(figure_directory)) {
    console.log(`Figure directory ${figure_directory} does not exist`);
    res.status(404).send(`Figure directory ${figure_directory} does not exist`);
    return;
  }

  let figure_files = glob.sync(path.join(figure_directory, "*.png"));
  figure_files.forEach((file) => {
    console.log(`Adding figure file: ${file}`);
    archive.file(file, { name: path.basename(file) });
  });

  let report_files = glob.sync(path.join(figure_directory, "*.pdf"));
  report_files.forEach((file) => {
    console.log(`Adding report file: ${file}`);
    archive.file(file, { name: path.basename(file) });
  });

  let CSV_directory = path.join(run_directory_base, key, "output", "monthly_means", name);
  let CSV_files = glob.sync(path.join(CSV_directory, "*.csv"));

  let header = "Year,Month,ET (mm/month),PET (mm/month)";

  CSV_files.forEach((file) => {
    // If 5 columns, remove the first index column
    // Make sure units are in header
    let data = fs.readFileSync(file, "utf8");
    let lines = data.trim().split("\n");
    let existingHeader = lines.shift();
    if (existingHeader.split(",").length === 5) {
      lines.forEach((line, i) => {
        let columns = line.split(",").map((x) => x.trim());
        if (columns.length === 5) {
          columns.shift(); // remove the first index column
          lines[i] = columns.join(",");
        }
      });
    }
    let new_data = [header].concat(lines).join("\n");
    fs.writeFileSync(file, new_data);

    archive.file(file, { name: path.basename(file) });
  });

  // Combine all CSV files into one
  let combined_csv = path.join(CSV_directory, `${name}_combined.csv`);
  let combined_csv_stream = fs.createWriteStream(combined_csv);
  combined_csv_stream.write(`${header}\n`);
  CSV_files.forEach((file) => {
    if (file.endsWith("_combined.csv")) {
      return;
    }

    let data = fs.readFileSync(file, "utf8");
    let lines = data.trim().split("\n");
    lines.shift(); // remove header
    lines.forEach((line) => {
      let columns = line.split(",").map((x) => x.trim());
      if (columns.length === 5) {
        columns.shift(); // remove the first index column
      }
      combined_csv_stream.write(columns.join(",") + "\n");
    });
  });

  combined_csv_stream.end();
  archive.file(combined_csv, { name: `${name}_combined.csv` });

  // Add geojson file to zip
  let geojson_filename = path.join(run_directory_base, key, `${name}.geojson`);
  archive.file(geojson_filename, { name: `${name}.geojson` });

  archive.finalize();
});

module.exports = router;
