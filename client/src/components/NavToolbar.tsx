import {
  AppBar,
  Avatar,
  Badge,
  Box,
  Divider,
  ListItemIcon,
  Menu,
  MenuItem,
  Skeleton,
  Toolbar,
  Tooltip,
  Typography,
} from "@mui/material";
import { useAuth0 } from "@auth0/auth0-react";
import WaterDropIcon from "@mui/icons-material/WaterDrop";
import ViewStreamIcon from "@mui/icons-material/ViewStream";
import PendingActionsIcon from "@mui/icons-material/PendingActions";
import AddIcon from "@mui/icons-material/Add";
import Logout from "@mui/icons-material/Logout";

import useStore from "../utils/store";
import { useEffect, useMemo, useState } from "react";
import LoginButton from "./LoginButton";

const Profile = () => {
  const { user, isAuthenticated, isLoading, logout } = useAuth0();
  const fetchQueue = useStore((state) => state.fetchQueue);
  const fetchUserInfo = useStore((state) => state.fetchUserInfo);

  useEffect(() => {
    if (isAuthenticated) {
      fetchQueue();
      fetchUserInfo();
    }
  }, [user, isAuthenticated]);

  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  if (isLoading) {
    return <Skeleton variant="circular" width={32} height={32} sx={{ marginRight: "8px" }} />;
  }

  return isAuthenticated ? (
    <div>
      <Avatar
        sx={{ width: 32, height: 32, marginRight: "8px", cursor: "pointer" }}
        onClick={(event: React.MouseEvent<HTMLElement>) => {
          setAnchorEl(event.currentTarget);
        }}
      >
        <img style={{ width: "32px", borderRadius: "50%" }} src={user?.picture} alt={user?.name} />
      </Avatar>
      <Menu
        anchorEl={anchorEl}
        id="account-menu"
        open={open}
        onClose={() => setAnchorEl(null)}
        onClick={() => setAnchorEl(null)}
        sx={{
          "& .MuiPaper-root": {
            background: "var(--st-gray-100)",
            overflow: "visible",
            filter: "drop-shadow(0px 2px 8px rgba(0,0,0,0.32))",
            mt: 1.5,
            "&::before": {
              content: '""',
              display: "block",
              position: "absolute",
              top: 0,
              right: 14,
              width: 10,
              height: 10,
              bgcolor: "var(--st-gray-100)",
              transform: "translateY(-50%) rotate(45deg)",
              zIndex: 0,
            },
          },
        }}
        transformOrigin={{ horizontal: "right", vertical: "top" }}
        anchorOrigin={{ horizontal: "right", vertical: "bottom" }}
      >
        <MenuItem onClick={() => setAnchorEl(null)}>
          <Avatar sx={{ width: 32, height: 32, marginRight: "8px", cursor: "pointer" }}>
            <img style={{ width: "32px", borderRadius: "50%" }} src={user?.picture} alt={user?.name} />
          </Avatar>
          <div style={{ display: "flex", flexDirection: "column" }}>
            <span className="name">{user?.name}</span>
            <div
              className="info"
              style={{ display: "flex", flexDirection: "column", fontSize: "12px", color: "var(--st-gray-30)" }}
            >
              <span className="email">{user?.email}</span>
              <span className="role">{user?.profile}</span>
            </div>
          </div>
        </MenuItem>
        <Divider />
        <MenuItem
          onClick={() => {
            setAnchorEl(null);
            logout();
          }}
        >
          <ListItemIcon>
            <Logout fontSize="small" />
          </ListItemIcon>
          Logout
        </MenuItem>
      </Menu>
    </div>
  ) : (
    <LoginButton />
  );
};

const NavToolbar = () => {
  const [isQueueOpen, setIsQueueOpen] = useStore((state) => [state.isQueueOpen, state.setIsQueueOpen]);
  const [isBacklogOpen, setIsBacklogOpen] = useStore((state) => [state.isBacklogOpen, state.setIsBacklogOpen]);
  const startNewJob = useStore((state) => state.startNewJob);
  const queue = useStore((state) => state.queue);
  const { isAuthenticated } = useAuth0();
  const userInfo = useStore((state) => state.userInfo);
  const canWriteJobs = useMemo(() => userInfo?.permissions.includes("write:jobs"), [userInfo?.permissions]);
  const canReadJobs = useMemo(() => userInfo?.permissions.includes("read:jobs"), [userInfo?.permissions]);

  return (
    <AppBar className="nav-area" position="static">
      <Toolbar
        variant="dense"
        style={{
          display: "flex",
          width: "100%",
          minHeight: "45px",
          gap: "8px",
          paddingLeft: "8px",
          paddingRight: 0,
          borderBottom: "1px solid #1b1d1e",
        }}
      >
        <WaterDropIcon style={{ color: "var(--st-gray-30)" }} />
        <Typography
          variant="h6"
          noWrap
          component="div"
          sx={{
            display: { xs: "none", md: "flex" },
            color: "var(--st-gray-20)",
            textDecoration: "none",
          }}
        >
          New Mexico Water Rights Visualizer
        </Typography>
        <Tooltip
          title={
            isAuthenticated
              ? canWriteJobs
                ? "Configure a new job"
                : "You don't have permission to create jobs"
              : "You must be logged in to start a job"
          }
        >
          <Typography
            color="inherit"
            component="div"
            sx={{
              display: "flex",
              alignItems: "center",
              color: "var(--st-gray-30)",
              cursor: "pointer",
              padding: "0 8px",
              height: "100%",
              userSelect: "none",
              ":hover":
                isAuthenticated && canWriteJobs
                  ? { color: "var(--st-gray-10)", backgroundColor: "var(--st-gray-80)" }
                  : {},
            }}
            onClick={() => {
              if (isAuthenticated && canWriteJobs) {
                startNewJob();
              }
            }}
          >
            <AddIcon />
            New
          </Typography>
        </Tooltip>

        <Box sx={{ ml: "auto", display: "flex", height: "100%", alignItems: "center" }}>
          <Tooltip title={canReadJobs ? "View in progress jobs" : "You don't have permission to view the job queue"}>
            <Box
              className={`nav-item ${isQueueOpen ? "active" : ""}`}
              sx={{
                display: "flex",
                alignItems: "center",
                height: "100%",
                cursor: "pointer",
                ":hover": { backgroundColor: "var(--st-gray-80)", color: "var(--st-gray-10)" },
              }}
              onClick={() => {
                if (isBacklogOpen && !isQueueOpen) {
                  setIsBacklogOpen(false);
                }

                setIsQueueOpen(!isQueueOpen);
              }}
            >
              <Badge badgeContent={queue.length} color="primary">
                <Typography
                  color="inherit"
                  component="div"
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    padding: "0 8px",
                    height: "fit-content",
                    gap: "4px",
                  }}
                >
                  <PendingActionsIcon />
                  Queue
                </Typography>
              </Badge>
            </Box>
          </Tooltip>
          <Tooltip title={canReadJobs ? "View completed jobs" : "You don't have permission to view completed jobs"}>
            <Box
              className={`nav-item ${isBacklogOpen ? "active" : ""}`}
              sx={{
                display: "flex",
                alignItems: "center",
                height: "100%",
                cursor: "pointer",
                ":hover": { backgroundColor: "var(--st-gray-80)", color: "var(--st-gray-10)" },
              }}
              onClick={() => {
                if (isQueueOpen && !isBacklogOpen) {
                  setIsQueueOpen(false);
                }

                setIsBacklogOpen(!isBacklogOpen);
              }}
            >
              <Typography
                color="inherit"
                component="div"
                sx={{
                  display: "flex",
                  alignItems: "center",
                  padding: "0 8px",
                  height: "fit-content",
                  gap: "4px",
                }}
              >
                <ViewStreamIcon />
                Backlog
              </Typography>
            </Box>
          </Tooltip>
        </Box>
        <Profile />
      </Toolbar>
    </AppBar>
  );
};

export default NavToolbar;
