const express = require('express');
const router = express.Router();
const path = require('path');
const fs = require('fs');

const spawn_child = require('./spawn_child');

const constants = require('./constants');

const project_directory = constants.project_directory;
const run_directory_base = constants.run_directory_base;

const argv = process.argv.slice(2);
const data_source = argv[0];

router.post('/start_run', (req, res) => {
    var name = req.body.name;
    var start_year = req.body.startYear;
    var end_year = req.body.endYear;
    var geojson = req.body.geojson;
    console.log("receiving start run request");
    console.log(`name: ${name}`);
    console.log(`start year: ${start_year}`);
    console.log(`end year: ${end_year}`);
    console.log("GeoJSON:");
    console.log(geojson);
    var run_directory = path.join(run_directory_base, name);
    console.log(`creating run directory ${run_directory}`);
    fs.mkdirSync(run_directory, { recursive: true });
    geojson_filename = path.join(run_directory, `${name}.geojson`);
    console.log(`writing GeoJSON to ${geojson_filename}`);

    geojson_text = JSON.stringify(geojson);

    if (geojson_text.startsWith('"') && geojson_text.endsWith('"')) {
        geojson_text = geojson_text.slice(1, -1);
    }

    geojson_text = geojson_text.replace(/\\"/g, '"');

    fs.writeFile(geojson_filename, geojson_text, 'utf8', function(err){
        if(err) throw err;
        console.log(`successfully wrote GeoJSON to ${geojson_filename}`);
    });

    var start_year_filename = path.join(run_directory, "start_year.txt");
    console.log(`writing start year to ${start_year_filename}`);

    fs.writeFile(start_year_filename, start_year, 'utf8', function(err){
        if(err) throw err;
        console.log(`successfully wrote start year to ${start_year_filename}`);
    });

    var end_year_filename = path.join(run_directory, "end_year.txt");
    console.log(`writing end year to ${end_year_filename}`);

    fs.writeFile(end_year_filename, end_year, 'utf8', function(err){
        if(err) throw err;
        console.log(`successfully wrote end year to ${end_year_filename}`);
    });

    var status = "run created";
    var status_filename = path.join(run_directory, "status.txt");
    console.log(`writing status to ${status_filename}`);

    fs.writeFile(status_filename, status, 'utf8', function(err){
        if(err) throw err;
        console.log(`successfully wrote status to ${status_filename}`);
    });

    var config_filename = path.join(run_directory, "config.json");
    
    var config = {
        "name": name,
        "start_year": start_year,
        "end_year": end_year,
        "working_directory": run_directory,
        "geojson_filename": geojson_filename,
        "status_filename": status_filename
    };

    fs.writeFile(config_filename, JSON.stringify(config, null, 2), function(err) {
        if(err) {
            console.log(err);
        } else {
            console.log("JSON saved to " + config_filename);
        }
    });

    var pipeline_script;
    
    if (data_source == "demo") {
        pipeline_script = path.join(project_directory, "water-rights-visualizer-backend-demo.py"); 
    } else if (data_source == "S3") {
        pipeline_script = path.join(project_directory, "water-rights-visualizer-backend-S3.py"); 
    } else if (data_source == "google") {
        pipeline_script = path.join(project_directory, "water-rights-visualizer-backend-google.py"); 
    }

    console.log(`pipeline script: ${pipeline_script}`);
    var command = `python ${pipeline_script} ${config_filename}`;
    console.log(command);
    var pid = spawn_child.spawn_child(command);

    var pid_filename = path.join(run_directory, "pid.txt");
    console.log(`writing process ID ${pid} to ${pid_filename}`);

    fs.writeFile(pid_filename, pid.toString(), 'utf8', function(err){
        if(err) throw err;
        console.log(`successfully wrote process ID to ${pid_filename}`);
    });
    
    var report_queue_file = path.join(run_directory_base, "report_queue.json");
    
    fs.readFile(report_queue_file, (err, data) => {
        var report_queue = [];
        
        if (!err && data) {
            report_queue = JSON.parse(data);
            console.log("Loaded report queue with " + data);
        }
        else if(err) {
            console.log("Error loading report queue:");
            console.log(err);
        }
        else {
            console.log("No data in report queue file");
        }
        
        report_queue.push(command);
    
        fs.writeFile(report_queue_file, JSON.stringify(report_queue, null, 2), function(err) {
            if(err) {
                console.log(err);
            } else {
                console.log("report queue saved to " + report_queue_file);
            }
        });
    })
    
    
    
    res.status(200).send(`Queued report for ${name} from ${start_year} to ${end_year}`);
});

module.exports = router;
