// Get the 'name' parameter from the URL
var urlParams = new URLSearchParams(window.location.search);
var run_name = urlParams.get('name');
var start_year;
var end_year;
var status;
var geojson;

var map = L.map('map', {zoomControl: false}).setView([0, 0], 2);

L.tileLayer('http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
    maxZoom: 20,
    subdomains: ['mt0','mt1','mt2','mt3'],
    attribution: 'Imagery <a href="https://www.google.com/">Google</a>',
}).addTo(map);

L.control.zoom({
    position: 'topright'
}).addTo(map);

L.control.scale({
    position: 'bottomleft'
}).addTo(map);

// Set the value of the name textarea
document.getElementById('name').value = run_name;

// Run a GET request on /start_year with the name parameter
fetch(`/start_year?name=${run_name}`)
    .then(response => response.text())
    .then(value => {
        // Store the response as start_year
        document.getElementById('startYear').value = value;
        start_year = value;
    });

// Run a GET request on /end_year with the name parameter
fetch(`/end_year?name=${run_name}`)
    .then(response => response.text())
    .then(value => {
        // Store the response as end_year
        document.getElementById('endYear').value = value;
        end_year = value;
    });

function refresh_status() {
// Run a GET request on /status with the name parameter
fetch(`/status?name=${run_name}`)
    .then(response => response.text())
    .then(value => {
        document.getElementById('status').value = value;
        status = value;
    });
};

// Run a GET request on /geojson with the name parameter
fetch(`/geojson?name=${run_name}`)
    .then(response => response.text())
    .then(value => {
        geojson = JSON.parse(value);

        var geojsonLayer = L.geoJSON(geojson, {
            onEachFeature: function (feature, layer) {
                if (feature.properties && feature.properties.name) {
                    layer.bindPopup(feature.properties.name);
                }
            }
        }).addTo(map);

        map.fitBounds(geojsonLayer.getBounds(), {padding: [100, 100]});
    });

function updateGallery(startYear, endYear) {
    // Clear the gallery
    $("#gallery").nanogallery2('destroy');

    // const startYear = parseInt(document.getElementById('startYear').value);
    // const endYear = parseInt(document.getElementById('endYear').value);
    const items = [];
    const promises = [];

    for (let year = startYear; year <= endYear; year++) {
        // FIXME change test_target to run name
        const promise = fetch(`/result?name=${run_name}&year=${year}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('HTTP error ' + response.status);
                }
                return response.blob();
            })
            .then(image => {
                const imageUrl = URL.createObjectURL(image);
                items.push({ src: imageUrl, srct: imageUrl, title: `Year: ${year}` });
            })
            .catch(error => {
                console.log('Fetch failed for year ' + year + ': ' + error.message);
            });

        promises.push(promise);
    }

    Promise.all(promises).then(() => {
        $("#gallery").nanogallery2({
            items: items,
            thumbnailHeight: 150,
            thumbnailWidth: 150,
            viewerToolbar: {
                standard: 'minimizeButton, label, shareButton, fullscreenButton, closeButton'
            }
        });
    });
};

refresh_status();

var gallery_start_year;
var gallery_end_year;

// Define the function that you want to run
function fetchData() {
    fetch(`/years_available?name=${run_name}`)
        .then(response => response.json())
        .then(years_available => {
            if (years_available.length > 0) {
                var available_start_year = years_available[0];
                var available_end_year = years_available[years_available.length - 1];

                if (available_end_year != gallery_end_year) {
                    gallery_start_year = available_start_year;
                    gallery_end_year = available_end_year;
                    updateGallery(gallery_start_year, gallery_end_year);
                }
            }
        });

    fetch(`/status?name=${run_name}`)
        .then(response => response.text())
        .then(status => {
            let currentTime = new Date().toLocaleTimeString();
            document.querySelector('#status').value = currentTime + '\n' + status;

            // Check if status starts with "completed"
            if (status.startsWith("completed")) {
                // Create a new link element
                var link = document.createElement('a');
                link.href = `/download?name=${run_name}`; // Set the destination URL
                link.textContent = `${run_name}.zip`; // Set the display text

                // Append the link to the 'attributes' div
                var attributesDiv = document.getElementById('attributes');
                attributesDiv.appendChild(link);
                clearInterval(intervalId);  // Stop the interval
            }
        });
}

// Call the function immediately
fetchData();

// Then set it to run at intervals
let intervalId = setInterval(fetchData, 10000);



