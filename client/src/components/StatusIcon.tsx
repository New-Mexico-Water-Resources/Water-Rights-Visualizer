import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import PendingIcon from "@mui/icons-material/Pending";
import ErrorIcon from "@mui/icons-material/Error";
import NotStartedIcon from "@mui/icons-material/NotStarted";

const StatusIcon = ({ status }: { status: string }) => {
  switch (status) {
    case "Pending":
      return <NotStartedIcon sx={{ color: "#ffeb3b" }} />;
    case "In Progress":
      return <PendingIcon sx={{ color: "#50AC34" }} />;
    case "Complete":
      return <CheckCircleIcon sx={{ color: "var(--st-success-green)" }} />;
    case "Failed":
      return <ErrorIcon sx={{ color: "var(--st-error-red)" }} />;
    default:
      return null;
  }
};

export default StatusIcon;
