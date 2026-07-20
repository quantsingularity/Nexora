import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import api from "../services/api";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState(null);

  // On mount: if a token is already stored, validate it against /auth/me.
  useEffect(() => {
    const bootstrap = async () => {
      const token = api.getAuthToken();
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const me = await api.getCurrentUser();
        setUser(me);
      } catch (e) {
        api.setAuthToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    bootstrap();
  }, []);

  // If any request comes back 401, treat the session as over.
  useEffect(() => {
    api.setUnauthorizedHandler(() => setUser(null));
    return () => api.setUnauthorizedHandler(null);
  }, []);

  const login = useCallback(async ({ email, password }) => {
    setAuthError(null);
    try {
      const { access_token, user: loggedInUser } = await api.login({
        email,
        password,
      });
      api.setAuthToken(access_token);
      setUser(loggedInUser);
      return loggedInUser;
    } catch (e) {
      setAuthError(e.message);
      throw e;
    }
  }, []);

  const register = useCallback(async (payload) => {
    setAuthError(null);
    try {
      const { access_token, user: newUser } = await api.register(payload);
      api.setAuthToken(access_token);
      setUser(newUser);
      return newUser;
    } catch (e) {
      setAuthError(e.message);
      throw e;
    }
  }, []);

  const logout = useCallback(async () => {
    await api.logout();
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    const me = await api.getCurrentUser();
    setUser(me);
    return me;
  }, []);

  const value = {
    user,
    isAuthenticated: !!user,
    loading,
    authError,
    login,
    register,
    logout,
    refreshUser,
    clearAuthError: () => setAuthError(null),
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
};

export default AuthContext;
