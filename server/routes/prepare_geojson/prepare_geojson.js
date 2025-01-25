const multer = require("multer");
const shapefile = require("shapefile");
const fs = require("fs");
const unzipper = require("unzipper");
const reprojectGeojson = require("./reproject");
const path = require("path");
const proj4 = require("proj4");

const upload = multer({ dest: "uploads/" });

const extractZip = async (zipPath, extractPath) => {
  return new Promise((resolve, reject) => {
    fs.createReadStream(zipPath)
      .pipe(unzipper.Extract({ path: extractPath }))
      .on("close", resolve)
      .on("error", reject);
  });
};

const getProjection = (prjFilePath) => {
  const projString = fs.readFileSync(prjFilePath, "utf8");
  return proj4(projString);
};

const findFileWithExtensionRecursive = (directory, extension) => {
  const files = fs.readdirSync(directory, { withFileTypes: true });
  for (const file of files) {
    const filePath = path.join(directory, file.name);
    if (file.isDirectory()) {
      const nestedResult = findFileWithExtensionRecursive(filePath, extension);
      if (nestedResult) return nestedResult;
    } else if (file.name.endsWith(extension)) {
      return filePath;
    }
  }
  return null;
};

const convertToGeoJSON = async (extractPath, baseName) => {
  return new Promise((resolve, reject) => {
    const geoJSONPath = path.join(extractPath, "output.geojson");
    const geoJSONStream = fs.createWriteStream(geoJSONPath);

    let basePath = path.join(extractPath, baseName);
    if (!fs.existsSync(basePath)) {
      basePath = extractPath;
    }

    const shapeFilePath = findFileWithExtensionRecursive(extractPath, ".shp");
    if (!fs.existsSync(shapeFilePath)) {
      reject("SHP file not found");
      return;
    }

    const dbfFilePath = findFileWithExtensionRecursive(extractPath, ".dbf");
    if (!fs.existsSync(dbfFilePath)) {
      reject("DBF file not found");
      return;
    }

    const prjFilePath = findFileWithExtensionRecursive(extractPath, ".prj");
    if (!fs.existsSync(prjFilePath)) {
      reject("PRJ file not found");
      return;
    }

    const projection = getProjection(prjFilePath);
    shapefile
      .open(shapeFilePath, dbfFilePath)
      .then((source) =>
        source.read().then(function log(result) {
          if (result.done) {
            geoJSONStream.end();
            fs.readFile(geoJSONPath, "utf8", (err, data) => {
              if (err) {
                console.error("Error reading geojson path", err);
                reject(err);
                return;
              }

              let geojson = { error: "Error reading geojson path" };
              try {
                geojson = JSON.parse(data);

                if (geojson["type"] === "Feature" || !geojson["name"]) {
                  // If this is an individual feature, put in FeatureCollection
                  if (geojson["type"] === "Feature") {
                    geojson = {
                      type: "FeatureCollection",
                      name: baseName || "output",
                      features: [geojson],
                    };
                  } else if (!geojson["name"]) {
                    // Some other type, but missing name field, which the backend needs
                    geojson["name"] = baseName || "output";
                  }

                  // Overwrite existing geojson if we had to reformat it
                  fs.writeFileSync(geoJSONPath, JSON.stringify(geojson));
                }
              } catch (error) {
                try {
                  let multipolygon = data.split("\n");
                  let geojsons = [];
                  multipolygon.forEach((polygon) => {
                    if (polygon) {
                      geojsons.push(JSON.parse(polygon));
                    }
                  });

                  geojson = { multipolygon: true, geojsons };
                } catch (err) {
                  console.error("Error parsing geojson", err);
                  reject(err);
                  return;
                }
              }
              resolve(geojson);
            });
            return;
          }

          let reprojected = {};
          try {
            reprojected = {
              ...result.value,
              geometry: {
                ...result.value.geometry,
                coordinates: result.value.geometry.coordinates.map((coord) => {
                  if (coord.length === 2 && !Array.isArray(coord[0])) {
                    return proj4(projection).inverse(coord);
                  } else {
                    return coord.map((subCoord) => {
                      return proj4(projection).inverse(subCoord);
                    });
                  }
                }),
              },
            };
          } catch (err) {
            console.error("Error reprojecting geojson", err);
            reject(err);
            return;
          }

          geoJSONStream.write(JSON.stringify(reprojected) + "\n");
          return source.read().then(log);
        })
      )
      .catch(reject);
  });
};

function prepareGeojson(req, res) {
  let canSubmitJobs =
    req.auth?.payload?.permissions?.includes("submit:jobs") || req.auth?.payload?.permissions?.includes("write:jobs");
  if (!canSubmitJobs) {
    res.status(401).send("Unauthorized: missing submit:jobs permission");
    return;
  }

  const filePath = req.file.path;
  const extension = path.extname(req.file.originalname);
  const baseName = path.basename(req.file.originalname, extension);

  const removeFile = () => {
    fs.unlink(filePath, (err) => {
      if (err) console.error(err);
    });
  };

  if (extension === ".geojson") {
    fs.readFile(filePath, "utf8", (err, data) => {
      if (err) {
        console.error(err);
        return;
      }
      let geojson = JSON.parse(data);

      if (geojson["type"] === "FeatureCollection" && geojson["features"].length === 0) {
        res.status(400).send("Invalid GeoJSON: empty FeatureCollection");
        removeFile();
        return;
      } else if (geojson["type"] === "FeatureCollection" && geojson["features"].length > 1) {
        let polygonMeta = JSON.parse(JSON.stringify(geojson));
        polygonMeta["features"] = [];
        let multipolygon = [];
        try {
          geojson["features"].forEach((feature) => {
            let polygon = JSON.parse(JSON.stringify(polygonMeta));
            polygon["features"] = [feature];

            if (!feature?.["geometry"]?.["coordinates"] || !feature["geometry"]["coordinates"].length) {
              // Invalid, skip this feature
              console.error("Invalid GeoJSON Feature: missing geometry.coordinates");
              return;
            }

            if (feature["geometry"]["type"] !== "Polygon") {
              console.error("Invalid GeoJSON Feature: not a Polygon");
              return;
            }

            let reprojectedGeojson = reprojectGeojson(polygon);
            multipolygon.push(reprojectedGeojson);
          });
        } catch (err) {
          console.error("Error reprojecting GeoJSON Feature", err);
          res.status(500).send(`Error reprojecting GeoJSON Feature (${err})`);
          removeFile();
          return;
        }

        if (multipolygon.length === 0) {
          res.status(400).send("Invalid GeoJSON: no valid features");
          removeFile();
          return;
        } else if (multipolygon.length === 1) {
          let feature = multipolygon[0];
          if (feature["type"] === "Feature") {
            feature = {
              type: "FeatureCollection",
              name: baseName || "output",
              features: [feature],
            };
          }

          res.send(feature);
          removeFile();
        } else {
          res.send({ multipolygon: true, geojsons: multipolygon });
          removeFile();
        }
      } else {
        // If this is an individual feature, put in FeatureCollection
        if (geojson["type"] === "Feature") {
          geojson = {
            type: "FeatureCollection",
            name: baseName || "output",
            features: [geojson],
          };
        }
        const reprojectedGeojson = reprojectGeojson(geojson);
        res.send(reprojectedGeojson);
        removeFile();
      }
    });
  } else if (extension === ".zip") {
    const extractPath = path.join("./uploads", `${baseName}-extracted`);
    if (!fs.existsSync(extractPath)) {
      fs.mkdirSync(extractPath, { recursive: true });
    }

    extractZip(filePath, extractPath)
      .then(() => {
        convertToGeoJSON(extractPath, baseName)
          .then((geojson) => {
            res.send(geojson);
            removeFile();
          })
          .catch((err) => {
            console.error("Error converting shapefile to GeoJSON", err);
            res.status(500).send(`Error converting shapefile to GeoJSON (${err})`);
          });
      })
      .catch((err) => {
        console.error("Error extracting zip file", err);
        res.status(500).send("Error extracting zip file");
      });
  } else {
    res.status(400).send("Invalid file type. Please upload a .geojson or .zip file.");
  }
}

module.exports = {
  upload: upload,
  prepareGeojson: prepareGeojson,
};
