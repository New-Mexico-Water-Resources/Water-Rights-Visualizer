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

var geojson;

function handleFileSelect(evt) {
    evt.stopPropagation();
    evt.preventDefault();

    var files = evt.dataTransfer.files;
    var file = evt.dataTransfer.files[0];

    const formData = new FormData();

    formData.append('file', file);

    fetch('/prepare_geojson', {
        method: 'POST',
        body: formData
    })
    .then(response => response.text())
    .then(data => {
        geojson = JSON.parse(data);
        geojson.features = geojson.features.slice(0, 1);
        var geometry = geojson.features[0].geometry;

        var geojsonLayer = L.geoJSON(geojson, {
            onEachFeature: function (feature, layer) {
                if (feature.properties && feature.properties.name) {
                    layer.bindPopup(feature.properties.name);
                }
            }
        }).addTo(map);

        map.fitBounds(geojsonLayer.getBounds(), {padding: [100, 100]});

        // Populate the form with the filename without the extension
        var name_form = document.getElementById('name')

        if (name_form.value === '') {
            var filename = files[0].name;
            var filename_base = filename.split('.').slice(0, -1).join('.');
            var new_name_value = cleanNameValue(filename_base);
            name_form.value = new_name_value;
        }
    })
    .catch((error) => {
    console.error('Error:', error);
    });
}

function handleDragOver(evt) {
    evt.stopPropagation();
    evt.preventDefault();
    evt.dataTransfer.dropEffect = 'copy';
}

var dropZone = map.getContainer();
dropZone.addEventListener('dragover', handleDragOver, false);
dropZone.addEventListener('drop', handleFileSelect, false);
