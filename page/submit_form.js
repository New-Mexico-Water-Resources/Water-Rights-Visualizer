document.getElementById('infoForm').addEventListener('submit', function(evt) {
    evt.preventDefault();

    var name = document.getElementById('name').value;
    var startYear = document.getElementById('startYear').value;
    var endYear = document.getElementById('endYear').value;

    var geojson_text = JSON.stringify(geojson).replace(/\\"/g, '"');
    console.log("GeoJSON:");
    console.log(geojson_text);

    var data = {
        name: name,
        startYear: startYear,
        endYear: endYear,
        geojson: geojson_text
    };

    fetch('/start_run', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    }).then(function(response) {
        return response.text();
    }).then(function(data) {
        console.log(data);
        window.location.href = "progress.html?name=" + encodeURIComponent(name);
    });
});