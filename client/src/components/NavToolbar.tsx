import { AppBar, Badge, Box, Toolbar, Typography } from "@mui/material";
import WaterDropIcon from "@mui/icons-material/WaterDrop";
import ViewStreamIcon from "@mui/icons-material/ViewStream";
import PendingActionsIcon from "@mui/icons-material/PendingActions";
import AddIcon from "@mui/icons-material/Add";
import useStore from "../utils/store";

const NavToolbar = () => {
  const [isQueueOpen, setIsQueueOpen] = useStore((state) => [state.isQueueOpen, state.setIsQueueOpen]);
  const [isBacklogOpen, setIsBacklogOpen] = useStore((state) => [state.isBacklogOpen, state.setIsBacklogOpen]);
  const startNewJob = useStore((state) => state.startNewJob);
  const queue = useStore((state) => state.queue);
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
            ":hover": { color: "var(--st-gray-10)", backgroundColor: "var(--st-gray-80)" },
          }}
          onClick={startNewJob}
        >
          <AddIcon />
          New
        </Typography>

        <Box sx={{ ml: "auto", display: "flex", height: "100%", alignItems: "center" }}>
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
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default NavToolbar;
