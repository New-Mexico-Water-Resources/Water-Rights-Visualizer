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

  const currentUserInfo = useStore((state) => state.userInfo);
  const canApproveJobs = useMemo(
    () => currentUserInfo?.permissions?.includes("submit:jobs") || currentUserInfo?.permissions?.includes("write:jobs"),
    [currentUserInfo]
  );
  const canDeleteJobs = useMemo(() => currentUserInfo?.permissions?.includes("write:jobs"), [currentUserInfo]);

  const approveJob = useStore((state) => state.approveJob);

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
        <Tooltip title={`${job.name}\nStatus: ${job.status}`}>
          <Typography
            variant="h6"
            sx={{
              display: "flex",
              alignItems: "center",
              gap: "4px",
            }}
          >
            <StatusIcon status={job.status} />
            <span style={{ maxWidth: "215px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "pre" }}>
              {job.name}
            </span>
          </Typography>
        </Tooltip>
        {canDeleteJobs && (
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
                deleteJob(job.key, true);
              });
            }}
          >
            <CloseIcon />
          </IconButton>
        )}
      </div>
      <div className="item-body">
        {job.status === "WaitingApproval" && (
          <Button
            disabled={!canApproveJobs}
            variant="contained"
            size="small"
            style={{ marginBottom: "8px" }}
            onClick={() => {
              approveJob(job.key);
            }}
          >
            {canApproveJobs ? "Approve Job" : "Waiting Approval..."}
          </Button>
        )}
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
        {job?.user?.name && (
          <Tooltip title={`Name: ${job.user.name}\nEmail: ${job.user.email}`}>
            <Typography variant="body2" style={{ marginTop: "8px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                <img
                  src={job?.user?.picture}
                  alt="user"
                  style={{ width: "20px", height: "20px", borderRadius: "50%" }}
                />
                <b style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "pre" }}>{job?.user?.name}</b>
              </div>
            </Typography>
          </Tooltip>
        )}
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
          Locate
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
