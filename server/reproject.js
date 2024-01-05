const proj4 = require('proj4');

function reprojectGeojson(geojson) {
  const sourceProj = geojson.crs ? geojson.crs.properties.name : 'EPSG:4326';
  const destProj = 'EPSG:4326';

  if (sourceProj !== destProj) {
    geojson.features.forEach(feature => {
      feature.geometry.coordinates = feature.geometry.coordinates.map(coord => {
        return proj4(sourceProj, destProj, coord);
      });
    });
  }

  return geojson;
}

module.exports = reprojectGeojson;
