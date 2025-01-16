import { Button, IconButton, Tooltip, Typography } from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import useStore, { JobStatus } from "../utils/store";
import { useEffect, useMemo } from "react";

import "../scss/CurrentJobChip.scss";

const CurrentJobChip = () => {
  const [activeJob, setActiveJob] = useStore((state) => [state.activeJob, state.setActiveJob]);
  const [previewMode, setPreviewMode] = useStore((state) => [state.previewMode, state.setPreviewMode]);
  const setShowUploadDialog = useStore((state) => state.setShowUploadDialog);
  const loadJob = useStore((state) => state.loadJob);
  const fetchJobStatus = useStore((state) => state.fetchJobStatus);

  const queue = useStore((state) => state.queue);
  const backlog = useStore((state) => state.backlog);

  const liveJob = useMemo(() => {
    let job = queue.find((job) => job.key === activeJob?.key);
    if (!job) {
      job = backlog.find((job) => job.key === activeJob?.key);
    }

    return job;
  }, [queue, backlog, activeJob?.id]);

  useEffect(() => {
    let interval = setInterval(() => {
      if (activeJob && activeJob?.status !== "Complete") {
        let jobStatusRequest = fetchJobStatus(activeJob.key, activeJob.name);
        if (!jobStatusRequest) {
          return;
        }

        jobStatusRequest
          .then(() => {
            if (liveJob?.status && activeJob.status !== liveJob?.status) {
              setActiveJob(liveJob);
            }
          })
          .catch((error) => {
            console.error("Error fetching job status", error);
          });
      }
    }, 5000);

    return () => {
      clearInterval(interval);
    };
  }, [activeJob, liveJob]);

  const jobStatuses = useStore((state) => state.jobStatuses);
  const jobStatus = useMemo(() => {
    let jobStatus: JobStatus = jobStatuses[activeJob?.key];
    if (activeJob?.status === "Complete") {
      jobStatus.status = "Complete test test long something test";
    }

    if (!jobStatus) {
      jobStatus = {
        status: "",
        currentYear: 0,
        totalYears: 0,
        fileCount: 0,
        estimatedPercentComplete: 0,
        timeRemaining: 0,
      };
    }

    return jobStatus;
  }, [activeJob?.key, activeJob?.status, jobStatuses]);

  const activeJobProperties: { property: string; value: any }[] = useMemo(() => {
    if (!activeJob?.loaded_geo_json) return [];

    let properties = {};
    let features = activeJob.loaded_geo_json?.features;
    if (features && features.length > 0) {
      properties = activeJob.loaded_geo_json.features[0].properties;
    } else if (!features && activeJob.loaded_geo_json?.properties) {
      properties = activeJob.loaded_geo_json.properties;
    }

    return Object.entries(properties).map(([key, value]) => {
      let propertyName = key
        .split(" ")
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");
      return { property: propertyName, value };
    });
  }, [activeJob?.loaded_geo_json]);

  return (
    <div className="current-job">
      <Typography
        variant="body1"
        style={{
          color: "var(--st-gray-30)",
          fontWeight: "bold",
          display: "flex",
          alignItems: "center",
          gap: "4px",
          minWidth: "225px",
        }}
      >
        {activeJob ? activeJob.name : "No active job"}
        {activeJob && (
          <IconButton
            size="small"
            sx={{ color: "var(--st-gray-30)", padding: 0, marginLeft: "auto" }}
            className="close-btn"
            onClick={() => {
              setActiveJob(null);
            }}
          >
            <CloseIcon fontSize="small" />
          </IconButton>
        )}
      </Typography>
      {activeJob && (
        <Typography variant="body2" style={{ color: "var(--st-gray-40)" }}>
          Years:{" "}
          <b>
            {activeJob.start_year} - {activeJob.end_year}
          </b>
        </Typography>
      )}

      {activeJob && (
        <Tooltip title={jobStatus?.status || "N/A"}>
          <Typography
            variant="body2"
            style={{ color: "var(--st-gray-40)", display: "flex", alignItems: "center", gap: "4px" }}
          >
            Status:{" "}
            <b
              style={{
                maxWidth: "178px",
                display: "inline-block",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "pre",
              }}
            >
              {jobStatus?.status || "N/A"}
            </b>
          </Typography>
        </Tooltip>
      )}

      {activeJob && activeJobProperties.length > 0 && (
        <Typography variant="body1" style={{ color: "var(--st-gray-40)", marginTop: "8px" }}>
          Properties:
        </Typography>
      )}
      {activeJob && activeJobProperties.length > 0 && (
        <div
          style={{
            maxHeight: "300px",
            maxWidth: "400px",
            overflow: "auto",
            border: "2px solid #404243",
            borderRadius: "8px",
            padding: "4px",
            textOverflow: "ellipsis",
            whiteSpace: "pre",
            marginBottom: "4px",
          }}
        >
          {activeJobProperties.map((property, index) => (
            <Typography key={index} variant="body2" style={{ color: "var(--st-gray-40)" }}>
              {property.property}: <b>{property.value}</b>
            </Typography>
          ))}
        </div>
      )}

      {previewMode && (
        <Button
          sx={{ margin: "8px 0" }}
          variant="contained"
          onClick={() => {
            setPreviewMode(false);
            setActiveJob(null);
            setShowUploadDialog(true);
          }}
        >
          Continue Editing
        </Button>
      )}
      <div style={{ display: "flex", gap: "8px", margin: "8px 0" }}>
        <Button
          sx={{ fontSize: "12px" }}
          size="small"
          variant="contained"
          color="secondary"
          onClick={() => {
            loadJob(activeJob);
          }}
        >
          Locate
        </Button>
        <Button
          sx={{ fontSize: "12px" }}
          size="small"
          variant="contained"
          color="secondary"
          onClick={() => {
            if (!activeJob?.loaded_geo_json) {
              return;
            }

            let blob = new Blob([JSON.stringify(activeJob.loaded_geo_json)], { type: "application/json" });
            let url = window.URL.createObjectURL(blob);
            let a = document.createElement("a");
            a.href = url;

            let shortName = activeJob.name.replace(/[(),]/g, "");
            let escapedName = encodeURIComponent(shortName);
            a.download = `${escapedName}.geojson`;
            a.click();
          }}
        >
          Download GeoJSON
        </Button>
      </div>
    </div>
  );
};

export default CurrentJobChip;
