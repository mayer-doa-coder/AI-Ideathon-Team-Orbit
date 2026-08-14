import { createContext, useContext, useEffect, useState } from "react";
import { fetchCurrentUser, loginUser, registerUser } from "../services/authApi";

const TOKEN_KEY = "agrisense_token";
const USERNAME_KEY = "agrisense_username";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [username, setUsername] = useState(null);
  const [token, setToken] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const storedToken = localStorage.getItem(TOKEN_KEY);
    const storedUsername = localStorage.getItem(USERNAME_KEY);

    if (!storedToken || !storedUsername) {
      setIsLoading(false);
      return;
    }

    fetchCurrentUser(storedToken)
      .then((user) => {
        setToken(storedToken);
        setUsername(user.username);
      })
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USERNAME_KEY);
      })
      .finally(() => setIsLoading(false));
  }, []);

  function persistSession(data) {
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(USERNAME_KEY, data.username);
    setToken(data.access_token);
    setUsername(data.username);
  }

  async function login(usernameInput, password) {
    const data = await loginUser(usernameInput, password);
    persistSession(data);
  }

  async function register(usernameInput, password) {
    const data = await registerUser(usernameInput, password);
    persistSession(data);
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USERNAME_KEY);
    setToken(null);
    setUsername(null);
  }

  const value = {
    username,
    token,
    isAuthenticated: Boolean(token && username),
    isLoading,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
