import { Typography } from "@mui/material";

const CurrentJobChip = ({ job }: { job: any }) => {
  return (
    <div className="current-job">
      <Typography variant="body1" style={{ color: "var(--st-gray-30)", fontWeight: "bold" }}>
        {job ? job.name : "No active job"}
      </Typography>
      {job && (
        <Typography variant="body2" style={{ color: "var(--st-gray-40)" }}>
          Years:{" "}
          <b>
            {job.start_year} - {job.end_year}
          </b>
        </Typography>
      )}
      {(job?.status_msg || job?.status) && (
        <Typography variant="body2" style={{ color: "var(--st-gray-40)" }}>
          Status: <b>{job?.status_msg || job?.status}</b>
        </Typography>
      )}
    </div>
  );
};

export default CurrentJobChip;
