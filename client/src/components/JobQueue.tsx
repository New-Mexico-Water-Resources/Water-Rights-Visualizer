import { Box, Button, IconButton, Modal, ToggleButton, ToggleButtonGroup, Typography } from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import useStore, { JobStatus } from "../utils/store";
import { useEffect, useMemo, useState } from "react";
import { LazyLog } from "@melloware/react-logviewer";
import FileDownloadSharpIcon from "@mui/icons-material/FileDownloadSharp";
import FileDownloadOffSharpIcon from "@mui/icons-material/FileDownloadOffSharp";
import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";

import "../scss/JobQueue.scss";
import JobQueueItem from "./JobQueueItem";
import { useConfirm } from "material-ui-confirm";

const JobQueue = () => {
  const queue = useStore((state) => state.queue);
  const backlog = useStore((state) => state.backlog);
  const isBacklogOpen = useStore((state) => state.isBacklogOpen);
  const isQueueOpen = useStore((state) => state.isQueueOpen);
  const clearPendingJobs = useStore((state) => state.clearPendingJobs);
  const fetchJobLogs = useStore((state) => state.fetchJobLogs);

  const [jobLogs, setJobLogs] = useState<Record<string, { timestamp: number; logs: string }>>({});
  const [activeJobLogKey, setActiveJobLogKey] = useState("");
  const [jobLogsOpen, setJobLogsOpen] = useState(false);

  const [pauseLogs, setPauseLogs] = useState(false);

  const [sortAscending, setSortAscending] = useStore((state) => [state.sortAscending, state.setSortAscending]);

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

  const confirm = useConfirm();

  const pendingJobCount = useMemo(() => {
    return queue.reduce((acc, job) => (job.status === "Pending" ? acc + 1 : acc), 0);
  }, [queue]);

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
          let jobStatusRequest = fetchJobStatus(activeJobLogKey, viewingJob.name);
          if (!jobStatusRequest) {
            return;
          }

          jobStatusRequest
            .then(() => {})
            .catch((error) => {
              console.error("Error fetching job status", error);
            });
        }

        let jobLogsRequest = fetchJobLogs(activeJobLogKey);
        if (!jobLogsRequest) {
          return;
        }

        jobLogsRequest.then((logs) => {
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
        });
      }
    };

    fetchLogs();
    const interval = setInterval(() => {
      if (!pauseLogs) {
        fetchLogs();
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [activeJobLogKey, jobLogsOpen]);

  const [searchField, setSearchField] = useState("");

  useEffect(() => {
    setSearchField("");
  }, [isQueueOpen]);

  const filteredItemList = useMemo(() => {
    let items = isBacklogOpen ? backlog : queue;
    let searchTerm = searchField.toLowerCase();
    let filteredItems = items.filter((item) => {
      let fields = [
        item.name.toLowerCase(),
        `${item?.start_year}`,
        `${item?.end_year}`,
        item.user?.name.toLowerCase(),
        item.user?.email.toLowerCase(),
        item?.status.toLowerCase(),
      ].filter((field) => field);

      // Name, Start Year, End Year, Creator Name, Creator Email
      return !searchField || fields.some((field) => field.includes(searchTerm));
    });

    filteredItems.sort((a, b) => {
      // by started "10/3/2024, 11:13:38 AM"
      let aStartedDate = new Date(a.started);
      let bStartedDate = new Date(b.started);
      if (sortAscending) {
        return aStartedDate.getTime() - bStartedDate.getTime();
      } else {
        return bStartedDate.getTime() - aStartedDate.getTime();
      }
    });

    return filteredItems;
  }, [queue, backlog, isBacklogOpen, searchField, sortAscending]);

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
            <LazyLog
              follow={!pauseLogs}
              style={{
                backgroundColor: "var(--st-gray-100)",
                color: "var(--st-gray-10)",
              }}
              text={jobLogs[activeJobLogKey]?.logs || "Loading logs..."}
              enableHotKeys={true}
              enableSearch={true}
              extraLines={1}
            />
          </div>
          <div style={{ display: "flex", alignItems: "center", marginTop: "5px", gap: "8px" }}>
            {!pauseLogs && (
              <FileDownloadSharpIcon
                style={{
                  color: "var(--st-gray-50)",
                  fontSize: "16px",
                  display: "flex",
                  alignItems: "center",
                  cursor: "pointer",
                }}
                onClick={() => {
                  setPauseLogs(!pauseLogs);
                }}
              />
            )}
            {pauseLogs && (
              <FileDownloadOffSharpIcon
                style={{
                  color: "var(--st-gray-50)",
                  fontSize: "16px",
                  display: "flex",
                  alignItems: "center",
                  cursor: "pointer",
                }}
                onClick={() => {
                  setPauseLogs(!pauseLogs);
                }}
              />
            )}

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
      <Typography
        variant="h5"
        style={{ color: "var(--st-gray-30)", padding: "8px 16px", display: "flex", alignItems: "center" }}
      >
        {isBacklogOpen ? "Backlog" : "Queue"}

        {!isBacklogOpen && (
          <Button
            variant="text"
            disabled={!pendingJobCount}
            sx={{ marginLeft: "auto" }}
            onClick={() => {
              confirm({
                title: "Clear Pending Jobs",
                description: `Are you sure you want to clear ${pendingJobCount} jobs from the queue?`,
                confirmationButtonProps: { color: "primary", variant: "contained" },
                cancellationButtonProps: { color: "secondary", variant: "contained" },
                titleProps: { sx: { backgroundColor: "var(--st-gray-90)", color: "var(--st-gray-10)" } },
                contentProps: { sx: { backgroundColor: "var(--st-gray-90)", color: "var(--st-gray-10)" } },
                dialogActionsProps: { sx: { backgroundColor: "var(--st-gray-90)" } },
              }).then(() => {
                clearPendingJobs();
              });
            }}
          >
            Clear Pending
          </Button>
        )}

        {isBacklogOpen && (
          <ToggleButtonGroup
            sx={{ marginLeft: "auto" }}
            value={sortAscending ? "asc" : "desc"}
            exclusive
            onChange={(evt, sortMode) => setSortAscending(sortMode === "asc")}
          >
            <ToggleButton
              size="small"
              value="asc"
              aria-label="Ascending"
              sx={sortAscending ? { backgroundColor: "#334155 !important" } : {}}
            >
              <ArrowUpwardIcon />
            </ToggleButton>
            <ToggleButton
              size="small"
              value="desc"
              aria-label="Descending"
              sx={!sortAscending ? { backgroundColor: "#334155 !important" } : {}}
            >
              <ArrowDownwardIcon />
            </ToggleButton>
          </ToggleButtonGroup>
        )}
      </Typography>
      <div className="search-bar">
        <input
          type="text"
          placeholder="Search..."
          className="search-input"
          value={searchField}
          onChange={(e) => setSearchField(e.target.value)}
        />
      </div>
      <div className="queue-list">
        {filteredItemList.map((job, index) => (
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
