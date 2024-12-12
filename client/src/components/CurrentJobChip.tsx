import { Button, IconButton, Typography } from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import useStore, { JobStatus } from "../utils/store";
import { useMemo } from "react";

import "../scss/CurrentJobChip.scss";

const CurrentJobChip = () => {
  const [activeJob, setActiveJob] = useStore((state) => [state.activeJob, state.setActiveJob]);
  const [previewMode, setPreviewMode] = useStore((state) => [state.previewMode, state.setPreviewMode]);
  const setShowUploadDialog = useStore((state) => state.setShowUploadDialog);

  const jobStatuses = useStore((state) => state.jobStatuses);
  const jobStatus = useMemo(() => {
    let jobStatus: JobStatus = jobStatuses[activeJob?.key];
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
  }, [activeJob?.key, jobStatuses]);

  const activeJobProperties: { property: string; value: any }[] = useMemo(() => {
    if (!activeJob?.loaded_geo_json) return [];

    let properties = {};
    let features = activeJob.loaded_geo_json?.features;
    if (features.length > 0) {
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
        style={{ color: "var(--st-gray-30)", fontWeight: "bold", display: "flex", alignItems: "center", gap: "4px" }}
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
        <Typography variant="body2" style={{ color: "var(--st-gray-40)" }}>
          Status: <b>{jobStatus?.status || "N/A"}</b>
        </Typography>
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
    </div>
  );
};

export default CurrentJobChip;
