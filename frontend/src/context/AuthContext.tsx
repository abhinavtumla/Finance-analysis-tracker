import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { fetchCurrentUser, loginUser, registerUser } from "../api/auth";
import type { UserResponse } from "../types/auth";

interface AuthContextValue {
  user: UserResponse | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const TOKEN_STORAGE_KEY = "finance_tracker_token";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_STORAGE_KEY));
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // On first load (or whenever the token changes), ask the backend who this
  // token belongs to. This both hydrates `user` after a page refresh and
  // catches an expired/invalid token early instead of waiting for some
  // other request to fail with a 401.
  useEffect(() => {
    if (!token) {
      setIsLoading(false);
      return;
    }
    fetchCurrentUser(token)
      .then(setUser)
      .catch(() => {
        localStorage.removeItem(TOKEN_STORAGE_KEY);
        setToken(null);
        setUser(null);
      })
      .finally(() => setIsLoading(false));
  }, [token]);

  async function login(email: string, password: string) {
    const { access_token } = await loginUser({ email, password });
    localStorage.setItem(TOKEN_STORAGE_KEY, access_token);
    const me = await fetchCurrentUser(access_token);
    setToken(access_token);
    setUser(me);
  }

  async function register(email: string, password: string, fullName?: string) {
    // /auth/register only creates the account and returns the user, it does
    // not issue a token — so we log in right after to get the same
    // "land the user in the app immediately" experience.
    await registerUser({ email, password, full_name: fullName });
    await login(email, password);
  }

  function logout() {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
