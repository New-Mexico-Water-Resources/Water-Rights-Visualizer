const proj4 = require("proj4");
proj4.defs["urn:ogc:def:crs:OGC:1.3:CRS84"] = proj4.defs["EPSG:4326"];

function reprojectGeojson(geojson) {
  const sourceProj = geojson?.crs?.properties?.name || "EPSG:4326";
  const destProj = "EPSG:4326";

  if (sourceProj !== destProj) {
    geojson.features.forEach((feature) => {
      feature.geometry.coordinates = feature.geometry.coordinates.map((coord) => {
        if (coord.length === 2 && !Array.isArray(coord[0])) {
          return proj4(sourceProj, destProj, coord);
        } else {
          return coord.map((subCoord) => {
            return proj4(sourceProj, destProj, subCoord);
          });
        }
      });
    });
  }

  return geojson;
}

module.exports = reprojectGeojson;
