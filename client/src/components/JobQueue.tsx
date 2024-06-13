import { Box, IconButton, Modal, Typography } from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import useStore, { JobStatus } from "../utils/store";
import { useEffect, useMemo, useRef, useState } from "react";
import { LazyLog, ScrollFollow } from "@melloware/react-logviewer";

import "../scss/JobQueue.scss";
import JobQueueItem from "./JobQueueItem";

const JobQueue = () => {
  const queue = useStore((state) => state.queue);
  const backlog = useStore((state) => state.backlog);
  const isBacklogOpen = useStore((state) => state.isBacklogOpen);
  const isQueueOpen = useStore((state) => state.isQueueOpen);

  const fetchJobLogs = useStore((state) => state.fetchJobLogs);

  const [jobLogs, setJobLogs] = useState<Record<string, { timestamp: number; logs: string }>>({});
  const [activeJobLogKey, setActiveJobLogKey] = useState("");
  const [jobLogsOpen, setJobLogsOpen] = useState(false);

  const [jobStatuses, fetchJobStatus] = useStore((state) => [state.jobStatuses, state.fetchJobStatus]);
  const jobStatus = useMemo(() => {
    let jobStatus: JobStatus = jobStatuses[activeJobLogKey];
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
  }, [activeJobLogKey, jobStatuses]);

  let logBottomRef = useRef<HTMLDivElement>(null);
  const viewingJob = useMemo(() => {
    if (!activeJobLogKey) {
      return null;
    }
    let job = queue.find((job) => job.key === activeJobLogKey);
    if (!job) {
      job = backlog.find((job) => job.key === activeJobLogKey);
    }

    return job;
  }, [queue, backlog, activeJobLogKey]);

  useEffect(() => {
    const fetchLogs = async () => {
      if (activeJobLogKey && jobLogsOpen) {
        if (viewingJob?.name) {
          fetchJobStatus(activeJobLogKey, viewingJob.name)
            .then(() => {})
            .catch((error) => {
              console.error("Error fetching job status", error);
            });
        }

        fetchJobLogs(activeJobLogKey).then((logs) => {
          let existingLog = jobLogs[activeJobLogKey];
          if (existingLog && existingLog.logs === logs.logs) {
            return;
          }

          let currentLog = { timestamp: 0, logs: "No Logs Available" };
          if (logs?.logs) {
            currentLog.logs = logs.logs;
          }

          currentLog.timestamp = Date.now();

          setJobLogs({ ...jobLogs, [activeJobLogKey]: currentLog });
          if (logBottomRef.current) {
            logBottomRef.current.scrollIntoView({ behavior: "smooth" });
          }
        });
      }
    };

    fetchLogs();
    const interval = setInterval(() => {
      fetchLogs();
    }, 5000);
    return () => clearInterval(interval);
  }, [activeJobLogKey, jobLogsOpen]);

  return (
    <div className={`queue-container ${isQueueOpen || isBacklogOpen ? "open" : "closed"}`}>
      <Modal
        open={jobLogsOpen}
        onClose={() => {
          setJobLogsOpen(false);
        }}
      >
        <Box
          sx={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            width: "50vw",
            maxWidth: "1000px",
            height: "50vh",
            maxHeight: "500px",
            bgcolor: "var(--st-gray-90)",
            boxShadow: 24,
            padding: "8px 16px",
            borderRadius: "4px",
          }}
        >
          <Typography variant="h6" component="h2" sx={{ display: "flex", alignItems: "center" }}>
            {viewingJob?.name || "Job"} Logs
            <IconButton
              onClick={() => {
                setActiveJobLogKey("");
                setJobLogsOpen(false);
              }}
              sx={{ marginLeft: "auto" }}
            >
              <CloseIcon />
            </IconButton>
          </Typography>
          <div style={{ height: "calc(100% - 64px)" }}>
            <ScrollFollow
              startFollowing={true}
              render={({ follow, onScroll }) => (
                <LazyLog
                  style={{
                    backgroundColor: "var(--st-gray-100)",
                    color: "var(--st-gray-10)",
                  }}
                  text={jobLogs[activeJobLogKey]?.logs || "Loading logs..."}
                  follow={follow}
                  onScroll={onScroll}
                  enableHotKeys={true}
                  enableSearch={true}
                  extraLines={1}
                />
              )}
            />
          </div>
          <div style={{ display: "flex", marginTop: "5px" }}>
            <div style={{ color: "var(--st-gray-50)", fontSize: "14px" }}>Files Generated: {jobStatus.fileCount}</div>
            <div
              style={{
                display: "flex",
                marginLeft: "auto",
                color: "var(--st-gray-50)",
                fontSize: "14px",
              }}
            >
              Last Updated:{" "}
              {jobLogs[activeJobLogKey]?.timestamp
                ? new Date(jobLogs[activeJobLogKey].timestamp).toLocaleTimeString()
                : "Never"}
            </div>
          </div>
        </Box>
      </Modal>
      <Typography variant="h5" style={{ color: "var(--st-gray-30)", padding: "8px 16px" }}>
        {isBacklogOpen ? "Backlog" : "Queue"}
      </Typography>
      <div className="queue-list">
        {(isBacklogOpen ? backlog : queue).map((job, index) => (
          <JobQueueItem
            key={index}
            job={job}
            onOpenLogs={() => {
              setActiveJobLogKey(job.key);
              setJobLogsOpen(true);
            }}
          />
        ))}
      </div>
    </div>
  );
};

export default JobQueue;
