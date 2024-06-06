const multer = require("multer");
const shapefile = require("shapefile");
const fs = require("fs");
const unzipper = require("unzipper");
const reprojectGeojson = require("./reproject");

const upload = multer({ dest: "uploads/" });

function prepareGeojson(req, res) {
  const filePath = req.file.path;
  console.log(`converting to GeoJSON lat/lon: ${filePath}`);
  const extension = req.file.originalname.split(".").pop().toLowerCase();

  const removeFile = () => {
    fs.unlink(filePath, (err) => {
      if (err) console.error(err);
    });
  };

  if (extension === "geojson") {
    fs.readFile(filePath, "utf8", (err, data) => {
      if (err) {
        console.error(err);
        return;
      }
      const geojson = JSON.parse(data);
      const reprojectedGeojson = reprojectGeojson(geojson);
      res.send(JSON.stringify(reprojectedGeojson));
      removeFile();
    });
  } else if (extension === "zip") {
    fs.createReadStream(filePath)
      .pipe(unzipper.Parse())
      .on("entry", async function (entry) {
        const fileName = entry.path;
        if (fileName.endsWith(".shp")) {
          const content = await entry.buffer();
          const geojson = await shapefile.read(content);
          const reprojectedGeojson = reprojectGeojson(geojson);
          res.send(JSON.stringify(reprojectedGeojson));
          removeFile();
        } else {
          entry.autodrain();
        }
      });
  } else {
    res.status(400).send("Invalid file type. Please upload a .geojson or .zip file.");
  }
}

module.exports = {
  upload: upload,
  prepareGeojson: prepareGeojson,
};
