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
