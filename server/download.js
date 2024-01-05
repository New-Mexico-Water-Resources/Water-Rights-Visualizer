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

    res.setHeader('Content-Type', 'application/zip');
    res.setHeader('Content-Disposition', `attachment; filename=${name}.zip`);

    archive.pipe(res);

    directory = path.join(run_directory_base, name, "output", "figures");
    let files = glob.sync(path.join(directory, "*.png"));

    files.forEach(file => {
        console.log(`Adding file: ${file}`);
        archive.file(file, { name: path.basename(file) });
    });

    archive.finalize();
});

module.exports = router;
