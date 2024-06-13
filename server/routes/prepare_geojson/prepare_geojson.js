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

const convertToGeoJSON = async (extractPath, baseName) => {
  return new Promise((resolve, reject) => {
    const geoJSONPath = path.join(extractPath, "output.geojson");
    const geoJSONStream = fs.createWriteStream(geoJSONPath);

    let basePath = path.join(extractPath, baseName);
    if (!fs.existsSync(basePath)) {
      basePath = extractPath;
    }

    const shapeFilePath = path.join(basePath, `${baseName}.shp`);
    if (!fs.existsSync(shapeFilePath)) {
      reject("SHP file not found");
      return;
    }

    const dbfFilePath = path.join(basePath, `${baseName}.dbf`);
    if (!fs.existsSync(dbfFilePath)) {
      reject("DBF file not found");
      return;
    }

    const prjFilePath = path.join(basePath, `${baseName}.prj`);
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

              const geojson = JSON.parse(data);
              resolve(geojson);
            });
            return;
          }

          const reprojected = {
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

          geoJSONStream.write(JSON.stringify(reprojected) + "\n");
          return source.read().then(log);
        })
      )
      .catch(reject);
  });
};

function prepareGeojson(req, res) {
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
      const geojson = JSON.parse(data);
      const reprojectedGeojson = reprojectGeojson(geojson);
      res.send(reprojectedGeojson);
      removeFile();
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
