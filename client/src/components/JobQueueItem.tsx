import { Box, Button, IconButton, LinearProgress, Tooltip, Typography } from "@mui/material";
import MoreHorizIcon from "@mui/icons-material/MoreHoriz";
import CloseIcon from "@mui/icons-material/Close";
import StatusIcon from "./StatusIcon";

import { useConfirm } from "material-ui-confirm";
import useStore, { JobStatus } from "../utils/store";
import { useEffect, useMemo } from "react";
import { formatElapsedTime } from "../utils/helpers";

const JobProgressBar = ({ status }: { status: JobStatus }) => {
  let estimatedPercentComplete = Math.max(Math.min(Math.round(status.estimatedPercentComplete * 1000) / 10, 100), 0);

  let tooltipText = `Status: ${status.status || "N/A"}\nYears Processed: ${status.currentYear}/${
    status.totalYears
  }\nEstimated Percent Complete: ${estimatedPercentComplete}%`;

  if (status.timeRemaining > 0) {
    tooltipText += `\nEstimated Time Remaining: ${formatElapsedTime(status.timeRemaining)}`;
  }

  return (
    <Tooltip title={tooltipText}>
      <Box sx={{ display: "flex", alignItems: "center" }}>
        <Box sx={{ width: "100%", mr: 1 }}>
          <LinearProgress value={estimatedPercentComplete} variant="determinate" />
        </Box>
        <Box sx={{ minWidth: 35 }}>
          <Typography variant="body2" color="text.secondary">{`${estimatedPercentComplete}%`}</Typography>
        </Box>
      </Box>
    </Tooltip>
  );
};

const JobQueueItem = ({ job, onOpenLogs }: { job: any; onOpenLogs: () => void }) => {
  const confirm = useConfirm();

  const setLoadedGeoJSON = useStore((state) => state.setLoadedGeoJSON);
  const setActiveJob = useStore((state) => state.setActiveJob);

  const deleteJob = useStore((state) => state.deleteJob);
  const loadJob = useStore((state) => state.loadJob);
  const downloadJob = useStore((state) => state.downloadJob);
  const [jobStatuses, fetchJobStatus] = useStore((state) => [state.jobStatuses, state.fetchJobStatus]);

  const jobStatus = useMemo(() => {
    let jobStatus: JobStatus = jobStatuses[job.key];
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
  }, [job.key, jobStatuses]);

  useEffect(() => {
    fetchJobStatus(job.key, job.name);
    const interval = setInterval(() => {
      fetchJobStatus(job.key, job.name);
    }, 5000);

    return () => clearInterval(interval);
  }, [job.key]);

  return (
    <div className="queue-item">
      <div className="item-header">
        <Tooltip title={`Status: ${job.status}`}>
          <Typography variant="h6" sx={{ display: "flex", alignItems: "center", gap: "4px" }}>
            <StatusIcon status={job.status} />
            {job.name}
          </Typography>
        </Tooltip>
        <IconButton
          onClick={() => {
            confirm({
              title: "Delete Job",
              description: `Are you sure you want to delete the job "${job.name}"?`,
              confirmationButtonProps: { color: "primary", variant: "contained" },
              cancellationButtonProps: { color: "secondary", variant: "contained" },
              titleProps: { sx: { backgroundColor: "var(--st-gray-90)", color: "var(--st-gray-10)" } },
              contentProps: { sx: { backgroundColor: "var(--st-gray-90)", color: "var(--st-gray-10)" } },
              dialogActionsProps: { sx: { backgroundColor: "var(--st-gray-90)" } },
            }).then(() => {
              deleteJob(job.key);
            });
          }}
        >
          <CloseIcon />
        </IconButton>
      </div>
      <div className="item-body">
        <Typography variant="body2">
          Years:{" "}
          <b>
            {job.start_year} - {job.end_year}
          </b>
        </Typography>
        {!job.started && (
          <Typography variant="body2">
            Submitted: <b>{job.submitted || "Not started yet"}</b>
          </Typography>
        )}
        <Typography variant="body2">
          Started: <b>{job.started || "Not started yet"}</b>
        </Typography>
        {job.started && (
          <Typography variant="body2" sx={{ display: "flex", alignItems: "center" }}>
            Finished: {job.ended ? <b style={{ marginLeft: "4px" }}>{job.ended}</b> : <MoreHorizIcon />}
          </Typography>
        )}
        {job.ended && job.started && (
          <Typography variant="body2">
            Time Elapsed: <b>{job.timeElapsed}</b>
          </Typography>
        )}
        <Typography variant="body2">
          Status: <b>{job.status_msg || job.status}</b>
        </Typography>
        <div>
          <JobProgressBar status={jobStatus} />
        </div>
      </div>
      <div className="action-buttons">
        <Button
          variant="contained"
          color="primary"
          size="small"
          onClick={() => {
            if (job.loaded_geo_json) {
              setLoadedGeoJSON(job.loaded_geo_json);
              setActiveJob(job);
            } else {
              loadJob(job);
            }
          }}
        >
          View
        </Button>
        <Button
          variant="contained"
          color="secondary"
          size="small"
          onClick={() => {
            onOpenLogs();
          }}
        >
          Logs
        </Button>
        <Button
          disabled={job.status !== "Complete"}
          variant="contained"
          color="secondary"
          size="small"
          onClick={() => {
            downloadJob(job.key);
          }}
        >
          Download
        </Button>
      </div>
    </div>
  );
};

export default JobQueueItem;
