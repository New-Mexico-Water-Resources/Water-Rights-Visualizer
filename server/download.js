const express = require('express');
const archiver = require('archiver');
const glob = require('glob');
const router = express.Router();
const path = require('path');
const fs = require('fs');
const constants = require('./constants');

const project_directory = constants.project_directory;
const run_directory_base = constants.run_directory_base;

router.get('/download', function(req, res) {
    console.log("/download")
    var name = req.query.name;
    console.log(`name: ${name}`);

    let archive = archiver('zip', {
        zlib: { level: 9 } // Sets the compression level.
    });

    archive.on('end', function() {
        console.log('Archive wrote %d bytes', archive.pointer());
    });

    archive.on('warning', function(err) {
        if (err.code === 'ENOENT') {
            console.log(err);
        } else {
            throw err;
        }
    });

    archive.on('error', function(err) {
        throw err;
    });

    // FIXME the `download` end-point is producing an empty zip-file when tested on AWS

    res.setHeader('Content-Type', 'application/zip');
    res.setHeader('Content-Disposition', `attachment; filename=${name}.zip`);

    archive.pipe(res);

    let figure_directory = path.join(run_directory_base, name, "output", "figures", name);
    let figure_files = glob.sync(path.join(figure_directory, "*.png"));

    figure_files.forEach(file => {
        console.log(`Adding figure file: ${file}`);
        archive.file(file, { name: path.basename(file) });
    });

    // FIXME the zip-file also needs to contain the CSV files produced for each year

    let CSV_directory = path.join(run_directory_base, name, "output", "monthly_means", name);
    let CSV_files = glob.sync(path.join(CSV_directory, "*.csv"));

    CSV_files.forEach(file => {
        console.log(`Adding CSV file: ${file}`);
        archive.file(file, { name: path.basename(file) });
    });

    archive.finalize();
});

module.exports = router;
