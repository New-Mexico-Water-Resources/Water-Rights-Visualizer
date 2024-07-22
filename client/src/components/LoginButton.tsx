import { useAuth0 } from "@auth0/auth0-react";
import { Button } from "@mui/material";
import { FC } from "react";

const LoginButton: FC = () => {
  const { loginWithRedirect, user, isAuthenticated } = useAuth0();
  return (
    <Button
      variant="contained"
      color="primary"
      size="small"
      sx={{ marginRight: "8px" }}
      onClick={() => loginWithRedirect()}
    >
      {user && isAuthenticated ? user.name : "Log In"}
    </Button>
  );
};

export default LoginButton;
