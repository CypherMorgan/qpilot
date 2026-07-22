/**
 * Auth context — manages JWT token and current user across the app.
 *
 * Stores the JWT in localStorage. On mount, validates the token by
 * calling GET /auth/me and hydrates the user state.
 *
 * Demo mode: when the backend is unreachable (e.g. GitHub Pages static
 * preview), the context enters demo mode so the UI remains browsable.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { User } from "@/services/auth";
import * as authService from "@/services/auth";

const TOKEN_KEY = "cypherpilot-token";

interface AuthContextValue {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  /** True when the backend is unreachable — UI is fully browsable but API calls will fail. */
  isDemoMode: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (
    username: string,
    email: string,
    password: string,
    displayName?: string,
  ) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  /** Manually enter demo mode (e.g. from the login page). */
  enterDemoMode: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

/**
 * Check if an error is a network/unreachable error (not just an invalid
 * response). This is how we detect "no backend" on GitHub Pages.
 */
function isNetworkError(err: unknown): boolean {
  if (!err || typeof err !== "object") return false;
  // Normalized ApiError from api-client
  const code = (err as { code?: string }).code;
  const status = (err as { status?: number }).status;
  if (code === "NETWORK_ERROR" || code === "TIMEOUT") return true;
  if (status === 0) return true;
  // Raw Axios error
  if (code === "ERR_NETWORK" || code === "ECONNABORTED") return true;
  return false;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem(TOKEN_KEY);
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isDemoMode, setIsDemoMode] = useState(false);

  // Validate token on mount
  useEffect(() => {
    if (!token) {
      // No token — try a lightweight probe to detect if backend exists
      authService
        .getMe()
        .then((u) => {
          setUser(u);
          setIsLoading(false);
        })
        .catch((err: unknown) => {
          if (isNetworkError(err)) {
            setIsDemoMode(true);
          }
          // No token + no backend or invalid token — either way, not authenticated
          setIsLoading(false);
        });
      return;
    }

    authService
      .getMe()
      .then((u) => {
        setUser(u);
        setIsLoading(false);
      })
      .catch((err: unknown) => {
        if (isNetworkError(err)) {
          // Backend unreachable — enter demo mode, keep UI browsable
          setIsDemoMode(true);
          setIsLoading(false);
        } else {
          // Token is invalid/expired — clear it
          localStorage.removeItem(TOKEN_KEY);
          setToken(null);
          setUser(null);
          setIsLoading(false);
        }
      });
  }, [token]);

  const login = useCallback(async (username: string, password: string) => {
    const result = await authService.login({ username, password });
    localStorage.setItem(TOKEN_KEY, result.access_token);
    setToken(result.access_token);
    setUser(result.user);
    setIsDemoMode(false);
  }, []);

  const registerFn = useCallback(
    async (
      username: string,
      email: string,
      password: string,
      displayName?: string,
    ) => {
      const result = await authService.register({
        username,
        email,
        password,
        display_name: displayName,
      });
      localStorage.setItem(TOKEN_KEY, result.access_token);
      setToken(result.access_token);
      setUser(result.user);
      setIsDemoMode(false);
    },
    [],
  );

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    if (!token) return;
    try {
      const u = await authService.getMe();
      setUser(u);
    } catch {
      // Token expired
      localStorage.removeItem(TOKEN_KEY);
      setToken(null);
      setUser(null);
    }
  }, [token]);

  const enterDemoMode = useCallback(() => {
    setIsDemoMode(true);
    setIsLoading(false);
  }, []);

  const value = useMemo(
    () => ({
      user,
      token,
      isAuthenticated: !!user,
      isLoading,
      isDemoMode,
      login,
      register: registerFn,
      logout,
      refreshUser,
      enterDemoMode,
    }),
    [user, token, isLoading, isDemoMode, login, registerFn, logout, refreshUser, enterDemoMode],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
