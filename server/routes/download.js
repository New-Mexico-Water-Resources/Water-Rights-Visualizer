const express = require("express");
const archiver = require("archiver");
const glob = require("glob");
const router = express.Router();
const path = require("path");
const fs = require("fs");
const constants = require("../constants");

const project_directory = constants.project_directory;
const run_directory_base = constants.run_directory_base;

function mm_to_in(mm) {
  if (typeof mm === "string" && !isNaN(parseFloat(mm))) {
    mm = parseFloat(mm);
  }

  if (isNaN(mm)) {
    return "";
  }

  return mm / 25.4;
}

router.get("/download", function (req, res) {
  let key = req.query.key;
  let name = req.query.name;
  let metric_units = req.query.units !== "in";

  let units = metric_units ? "mm" : "in";

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
    if (metric_units && file.endsWith("_in.png")) {
      return;
    } else if (!metric_units && !file.endsWith("_in.png")) {
      return;
    }

    let new_name = path.basename(file).replace("_in.png", ".png");

    console.log(`Adding figure file: ${file} as ${new_name}`);
    archive.file(file, { name: new_name });
  });

  let report_files = glob.sync(path.join(figure_directory, "*.pdf"));
  report_files.forEach((file) => {
    if (metric_units && file.endsWith("_Imperial_Report.pdf")) {
      return;
    } else if (!metric_units && !file.endsWith("_Imperial_Report.pdf")) {
      return;
    }

    let new_name = path.basename(file).replace("_Imperial_Report.pdf", "_Report.pdf");
    console.log(`Adding report file: ${file} as ${new_name}`);
    archive.file(file, { name: new_name });
  });

  let monthly_nan_directory = path.join(run_directory_base, key, "output", "monthly_nan", name);
  let monthly_nan_files = glob.sync(path.join(monthly_nan_directory, "*.csv"));

  nan_values = {};
  monthly_nan_files.forEach((file) => {
    let data = fs.readFileSync(file, "utf8");
    let lines = data.trim().split("\n");
    let header = lines.shift();
    header = header.split(",").map((x) => x.trim());

    lines.forEach((line) => {
      let row = {};
      let columns = line.split(",").map((x) => x.trim());
      columns.forEach((column, i) => {
        row[header[i]] = column;
      });

      let year = row["year"];
      let month = row["month"];

      if (!nan_values[year]) {
        nan_values[year] = {};
      }

      nan_values[year][month] = row;
    });
  });

  let CSV_directory = path.join(run_directory_base, key, "output", "monthly_means", name);
  let CSV_files = glob.sync(path.join(CSV_directory, "*.csv"));

  let header = `Year,Month,ET (${units}/month),PET (${units}/month), Precipitation (${units}/month), Cloud Coverage + Missing Data (%)`;

  CSV_files.forEach((file) => {
    if (path.basename(file).includes("_temp_")) {
      return;
    }

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

    lines.forEach((line, i) => {
      let columns = line.split(",").map((x) => x.trim());
      let year = columns[0];
      let month = columns[1];
      let et = metric_units ? columns[2] : mm_to_in(columns[2]);
      let pet = metric_units ? columns[3] : mm_to_in(columns[3]);

      lines[i] = `${year},${month},${et},${pet}`;

      let yearKey = `${year}`;
      let monthKey = `${Number(month)}`;
      let nan_row = nan_values?.[yearKey]?.[monthKey];
      if (nan_row) {
        let ppt = metric_units ? nan_row["ppt_avg"] : mm_to_in(nan_row["ppt_avg"]);
        lines[i] = lines[i] + `,${ppt},${nan_row["percent_nan"]}`;
      } else {
        lines[i] = lines[i] + ",,";
      }
    });

    let new_data = [header].concat(lines).join("\n");

    let temp_path = file.replace(".csv", `_temp_${metric_units ? "mm" : "in"}.csv`);
    fs.writeFileSync(temp_path, new_data);

    let new_filename = path.basename(file);

    archive.file(temp_path, { name: new_filename });
  });

  // Combine all CSV files into one
  let combined_csv = path.join(CSV_directory, `${name}_combined.csv`);
  let combined_csv_stream = fs.createWriteStream(combined_csv);
  combined_csv_stream.write(`${header}\n`);
  CSV_files.forEach((file) => {
    if (file.endsWith("_combined.csv") || path.basename(file).includes("_temp_")) {
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
