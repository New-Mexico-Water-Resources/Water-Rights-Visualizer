import { createContext, useContext, useEffect } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import useStore from "./store";

const AuthContext = createContext({ token: "" });

export const AuthProvider = ({ children }: { children: any }) => {
  const { getAccessTokenSilently, isAuthenticated, loginWithRedirect } = useAuth0();
  const [token, setToken] = useStore((state) => [state.authToken, state.setAuthToken]);

  useEffect(() => {
    const fetchToken = async () => {
      if (isAuthenticated) {
        try {
          const accessToken = await getAccessTokenSilently();
          setToken(accessToken);
        } catch (error) {
          if (["invalid_grant", "missing_refresh_token"].includes((error as any)?.error)) {
            loginWithRedirect({
              authorizationParams: { prompt: "login" },
            });
            return;
          }
          console.error("Failed to fetch token", error);
        }
      }
    };

    fetchToken();
  }, [getAccessTokenSilently, isAuthenticated, setToken]);

  return <AuthContext.Provider value={{ token }}>{children}</AuthContext.Provider>;
};

export const useAuth = () => useContext(AuthContext);
