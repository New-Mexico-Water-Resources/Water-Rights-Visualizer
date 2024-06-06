import "./App.css";
import "./scss/variables.scss";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { ThemeProvider } from "@emotion/react";
import { CssBaseline } from "@mui/material";
import theme from "./theme";
import Dashboard from "./routes/Dashboard";
import { ConfirmProvider } from "material-ui-confirm";

const router = createBrowserRouter([
  {
    path: "/",
    element: <Dashboard />,
  },
]);

function App() {
  return (
    <ThemeProvider theme={theme}>
      <ConfirmProvider>
        <CssBaseline />
        <RouterProvider router={router} />
      </ConfirmProvider>
    </ThemeProvider>
  );
}

export default App;
