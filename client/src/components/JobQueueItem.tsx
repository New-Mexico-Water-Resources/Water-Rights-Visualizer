import { Box, Button, IconButton, LinearProgress, Tooltip, Typography } from "@mui/material";
import MoreHorizIcon from "@mui/icons-material/MoreHoriz";
import CloseIcon from "@mui/icons-material/Close";
import PauseIcon from "@mui/icons-material/Pause";
import PlayIcon from "@mui/icons-material/PlayArrow";
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
  const restartJob = useStore((state) => state.restartJob);
  const pauseJob = useStore((state) => state.pauseJob);
  const resumeJob = useStore((state) => state.resumeJob);
  const [jobStatuses, fetchJobStatus] = useStore((state) => [state.jobStatuses, state.fetchJobStatus]);

  const currentUserInfo = useStore((state) => state.userInfo);
  const canApproveJobs = useMemo(() => currentUserInfo?.permissions?.includes("write:jobs"), [currentUserInfo]);
  const canDeleteJobs = useMemo(() => currentUserInfo?.permissions?.includes("write:jobs"), [currentUserInfo]);
  const canRestartJobs = useMemo(() => currentUserInfo?.permissions?.includes("write:jobs"), [currentUserInfo]);
  const canPauseJobs = useMemo(() => currentUserInfo?.permissions?.includes("write:jobs"), [currentUserInfo]);

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

  const jobStatusColor = useMemo(() => {
    switch (job.status) {
      case "In Progress":
        return "#50AC34";
      case "Pending":
        return "#ffeb3b";
      default:
        return "var(--st-gray-10)";
    }
  }, [job.status]);

  useEffect(() => {
    fetchJobStatus(job.key, job.name);
    const interval = setInterval(() => {
      fetchJobStatus(job.key, job.name);
    }, 5000);

    return () => clearInterval(interval);
  }, [job.key]);

  return (
    <div className="queue-item" style={{ height: "100%", justifyContent: "space-between" }}>
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
      <div className="item-body" style={{ flex: 1, justifyContent: "space-around" }}>
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
        {job.status === "Failed" && canRestartJobs && (
          <Tooltip title="Restart job from where it failed">
            <Button
              variant="contained"
              size="small"
              style={{ marginBottom: "8px" }}
              onClick={() => {
                restartJob(job.key);
              }}
            >
              Restart Job
            </Button>
          </Tooltip>
        )}
        {["In Progress", "Pending"].includes(job.status) && (
          <Tooltip title="Pause the job after the current year finishes">
            <Button
              disabled={job.status !== "In Progress" || !canPauseJobs}
              variant="contained"
              size="small"
              style={{ marginBottom: "8px" }}
              onClick={() => {
                pauseJob(job.key);
              }}
            >
              <IconButton sx={{ padding: 0 }}>
                <PauseIcon color={job.status !== "In Progress" || !canPauseJobs ? "disabled" : undefined} />
              </IconButton>
              Pause
            </Button>
          </Tooltip>
        )}
        {job.status === "Paused" && canPauseJobs && (
          <Tooltip
            title={
              job.paused_year ? "Resume from " + job?.paused_year : "Job will pause after the current year is processed"
            }
          >
            <Button
              variant="contained"
              size="small"
              style={{ marginBottom: "8px" }}
              onClick={() => {
                resumeJob(job.key);
              }}
            >
              <IconButton sx={{ padding: 0 }}>
                <PlayIcon />
              </IconButton>
              {job.paused_year ? "Resume from " + job?.paused_year : "Resume (Pausing...)"}
            </Button>
          </Tooltip>
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
        {["In Progress", "Paused", "Pending", "WaitingApproval"].includes(job.status) && (
          <Typography variant="body2" sx={{ display: "flex", alignItems: "center" }}>
            Processing Year:{" "}
            <b style={{ display: "flex", marginLeft: "4px" }}>{job?.last_generated_year || <MoreHorizIcon />}</b>
          </Typography>
        )}
        {job.started && job.ended && (
          <Typography variant="body2" sx={{ display: "flex", alignItems: "center" }}>
            Finished:{" "}
            {job.ended ? <b style={{ display: "flex", marginLeft: "4px" }}>{job.ended}</b> : <MoreHorizIcon />}
          </Typography>
        )}
        {job.ended && job.started && (
          <Typography variant="body2">
            Time Elapsed: <b>{job.timeElapsed}</b>
          </Typography>
        )}
        <Typography variant="body2">
          Status: <b style={{ color: jobStatusColor }}>{job.status_msg || job.status}</b>
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
          color="secondary"
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
        <Tooltip title={job.status === "Complete" ? "Download Completed Job" : "Download partial job"}>
          <span>
            <Button
              disabled={["Pending", "In Progress", "WaitingApproval"].includes(job.status)}
              variant="contained"
              color="secondary"
              size="small"
              onClick={() => {
                downloadJob(job.key);
              }}
            >
              Download
            </Button>
          </span>
        </Tooltip>
      </div>
    </div>
  );
};

export default JobQueueItem;
