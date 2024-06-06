import { createTheme } from "@mui/material/styles";

const theme = createTheme({
  palette: {
    mode: "dark",
    primary: {
      main: "#2563EB",
    },
    secondary: {
      main: "#334155",
    },
  },
  typography: {
    fontFamily: "Inter, sans-serif",
  },
  components: {
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: "var(--st-gray-80)",
          color: "var(--st-gray-20)",
          whiteSpace: "pre-line",
        },
        arrow: {
          color: "var(--st-gray-80)",
        },
      },
    },
  },
});

export default theme;
