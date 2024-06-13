import {
  Button,
  FormControl,
  IconButton,
  Input,
  InputLabel,
  MenuItem,
  Select,
  SelectChangeEvent,
  Slider,
  Typography,
} from "@mui/material";
import MapIcon from "@mui/icons-material/Map";
import CloseIcon from "@mui/icons-material/Close";

import { ChangeEvent, useCallback, useMemo } from "react";
import { useDropzone } from "react-dropzone";
import useStore from "../utils/store";

const UploadDialog = () => {
  const [jobName, setJobName] = useStore((state) => [state.jobName, state.setJobName]);
  const [minYear, maxYear] = useStore((state) => [state.minYear, state.maxYear]);
  const [startYear, setStartYear] = useStore((state) => [state.startYear, state.setStartYear]);
  const [endYear, setEndYear] = useStore((state) => [state.endYear, state.setEndYear]);
  const [loadedFile, setLoadedFile] = useStore((state) => [state.loadedFile, state.setLoadedFile]);
  const [loadedGeoJSON, setLoadedGeoJSON] = useStore((state) => [state.loadedGeoJSON, state.setLoadedGeoJSON]);
  const setActiveJob = useStore((state) => state.setActiveJob);
  const submitJob = useStore((state) => state.submitJob);
  const closeNewJob = useStore((state) => state.closeNewJob);
  const prepareGeoJSON = useStore((state) => state.prepareGeoJSON);

  const canSubmitJob = useMemo(() => {
    return jobName && loadedFile && loadedGeoJSON && startYear <= endYear;
  }, [jobName, loadedFile, loadedGeoJSON, startYear, endYear]);

  const validYears = useMemo(() => {
    return Array.from({ length: maxYear - minYear + 1 }, (_, i) => minYear + i);
  }, [startYear, endYear]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    acceptedFiles.forEach((file) => {
      const reader = new FileReader();

      reader.onabort = () => console.log("file reading was aborted");
      reader.onerror = () => console.log("file reading has failed");
      reader.onload = () => {
        const response = reader.result;
        setLoadedFile(file);
        if (!jobName) {
          let fileName = file.name.replace(/\.[^/.]+$/, "");
          setJobName(fileName);
        }

        prepareGeoJSON(file).then((geojson) => {
          if (geojson.data) {
            setLoadedGeoJSON(geojson.data);
            setActiveJob(null);
          }
        });
      };
      reader.readAsText(file);
    });
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    accept: {
      "application/zip": [".zip"],
      "application/json": [".geojson"],
    },
  });

  return (
    <div className="upload-dialog-container" style={{ background: "rgb(0 0 0 / 50%)", zIndex: 1000 }}>
      <div className="upload-zone">
        <div className="upload-options" style={{ width: "100%", color: "white" }}>
          <div className="dialog-header">
            <Typography variant="h5" className="dialog-title">
              Start New Job
            </Typography>
            <IconButton
              className="close-btn"
              onClick={() => {
                closeNewJob();
              }}
            >
              <CloseIcon />
            </IconButton>
          </div>
          <FormControl style={{ width: "100%", padding: "0 8px", marginTop: "16px" }}>
            <InputLabel htmlFor="name-field">Name</InputLabel>
            <Input
              id="name-field"
              style={{ padding: "0 8px", width: "100%" }}
              value={jobName}
              onChange={(event: ChangeEvent<HTMLInputElement>) => {
                setJobName(event.target.value);
              }}
            />
          </FormControl>
          <div style={{ padding: "16px 32px" }}>
            <Slider
              min={minYear}
              max={maxYear}
              getAriaLabel={() => "Year range slider"}
              value={[startYear, endYear]}
              onChange={(_, newValue: number | number[]) => {
                if (!Array.isArray(newValue)) {
                  return;
                }

                setStartYear(newValue[0]);
                setEndYear(newValue[1]);
              }}
              valueLabelDisplay="auto"
              getAriaValueText={(value) => `${value}`}
              marks
            />
            <div className="slider-controls">
              <FormControl size="small">
                <InputLabel id="start-year-label">Start Year</InputLabel>
                <Select
                  labelId="start-year-label"
                  value={startYear}
                  label="Start Year"
                  onChange={(event: SelectChangeEvent<number>) => setStartYear(event.target.value as number)}
                >
                  {validYears.map((year) => (
                    <MenuItem key={year} value={year}>
                      {year}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <FormControl size="small">
                <InputLabel id="end-year-label">End Year</InputLabel>
                <Select
                  labelId="end-year-label"
                  value={endYear}
                  label="End Year"
                  onChange={(event: SelectChangeEvent<number>) => setEndYear(event.target.value as number)}
                >
                  {validYears.map((year) => (
                    <MenuItem key={year} value={year}>
                      {year}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </div>
          </div>
        </div>
        <div className="dropzone-container">
          {loadedFile && (
            <div className="cancel-job">
              <IconButton
                onClick={(evt) => {
                  evt.preventDefault();
                  setLoadedFile(null);
                  setLoadedGeoJSON(null);
                }}
              >
                <CloseIcon sx={{ color: "var(--st-gray-50)", ":hover": { color: "var(--st-gray-10)" } }} />
              </IconButton>
            </div>
          )}
          <div className={`dropzone-area ${isDragActive ? "drag-active" : ""}`} {...getRootProps()}>
            <input {...getInputProps()} />
            {loadedFile ? (
              <div className="loaded-file">
                <MapIcon style={{ color: "var(--st-gray-20)" }} />
                <p style={{ color: "var(--st-gray-20)" }}>{loadedFile.name}</p>
              </div>
            ) : (
              <p style={{ color: "var(--st-gray-40)" }}>Drag and drop a GeoJSON or zipped shapefile</p>
            )}
          </div>
        </div>
        <div
          className="bottom-buttons"
          style={{ width: "100%", display: "flex", alignItems: "center", justifyContent: "flex-end" }}
        >
          <Button
            disabled={!canSubmitJob}
            variant="contained"
            color="primary"
            style={{ margin: "8px", border: canSubmitJob ? "1px solid #1E40AF" : "1px solid transparent" }}
            onClick={() => {
              if (canSubmitJob) {
                submitJob();
              }
            }}
          >
            Submit Job
          </Button>
        </div>
      </div>
    </div>
  );
};

export default UploadDialog;
