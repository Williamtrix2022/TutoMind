"use client";

import { MotionConfig } from "motion/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { retryDelay, shouldRetry } from "@/lib/api/errors";
import { UNAUTHORIZED_EVENT } from "@/lib/api/events";
import type { components } from "@/lib/api/schema";
import { getToken, setToken } from "@/lib/api/token-store";
import type { Role, Theme } from "@/lib/types";
import { MockGate } from "./mock-gate";

type User = components["schemas"]["User"];
type LoginResponse = components["schemas"]["LoginResponse"];

export type AuthStatus = "loading" | "authenticated" | "anonymous";

interface AppState {
  theme: Theme;
  toggleTheme: () => void;
  /** Rol activo de la interfaz. Es de UX: la autorización real la hace el backend. */
  role: Role;
  setRole: (role: Role) => void;
  user: User | null;
  authStatus: AuthStatus;
  signIn: (response: LoginResponse) => void;
  signOut: () => void;
}

const AppContext = createContext<AppState | null>(null);

const THEME_KEY = "tm-theme";
const ROLE_KEY = "tm-role";
const USER_KEY = "tm-user";

function readStorage(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function writeStorage(key: string, value: string): void {
  try {
    window.localStorage.setItem(key, value);
  } catch {
    /* almacenamiento no disponible: se ignora */
  }
}

function removeStorage(key: string): void {
  try {
    window.localStorage.removeItem(key);
  } catch {
    /* almacenamiento no disponible: se ignora */
  }
}

function isUser(value: unknown): value is User {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate.id === "string" &&
    typeof candidate.name === "string" &&
    typeof candidate.email === "string" &&
    (candidate.role === "student" || candidate.role === "teacher")
  );
}

export function AppProviders({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () => new QueryClient({ defaultOptions: { queries: { staleTime: 30_000, retry: shouldRetry, retryDelay } } }),
  );
  const [theme, setTheme] = useState<Theme>("dark");
  const [role, setRoleState] = useState<Role>("student");
  const [user, setUser] = useState<User | null>(null);
  const [authStatus, setAuthStatus] = useState<AuthStatus>("loading");

  // Sincroniza con lo que el script inline ya aplicó al <html> y restaura la sesión.
  useEffect(() => {
    const applied = document.documentElement.dataset.theme;
    if (applied === "light" || applied === "dark") setTheme(applied);

    const storedRole = readStorage(ROLE_KEY);
    if (storedRole === "student" || storedRole === "teacher") setRoleState(storedRole);

    let restored: User | null = null;
    const raw = readStorage(USER_KEY);
    if (raw && getToken()) {
      try {
        const parsed: unknown = JSON.parse(raw);
        if (isUser(parsed)) restored = parsed;
      } catch {
        /* sesión corrupta: se descarta */
      }
    }
    if (restored) {
      setUser(restored);
      setRoleState(restored.role);
      setAuthStatus("authenticated");
    } else {
      setToken(null);
      removeStorage(USER_KEY);
      setAuthStatus("anonymous");
    }
  }, []);

  const toggleTheme = useCallback(() => {
    const next: Theme = theme === "dark" ? "light" : "dark";
    const root = document.documentElement;
    root.classList.add("theme-transition");
    root.dataset.theme = next;
    window.setTimeout(() => root.classList.remove("theme-transition"), 400);
    document
      .querySelector('meta[name="theme-color"]')
      ?.setAttribute("content", next === "dark" ? "#03174C" : "#F6F7FB");
    writeStorage(THEME_KEY, next);
    setTheme(next);
  }, [theme]);

  const setRole = useCallback((next: Role) => {
    writeStorage(ROLE_KEY, next);
    setRoleState(next);
  }, []);

  const signIn = useCallback(
    (response: LoginResponse) => {
      setToken(response.access_token);
      writeStorage(USER_KEY, JSON.stringify(response.user));
      setUser(response.user);
      setRole(response.user.role);
      setAuthStatus("authenticated");
    },
    [setRole],
  );

  const signOut = useCallback(() => {
    setToken(null);
    removeStorage(USER_KEY);
    setUser(null);
    setAuthStatus("anonymous");
    queryClient.clear();
  }, [queryClient]);

  // Un 401 del backend cierra la sesión; AuthGate redirige al login.
  useEffect(() => {
    window.addEventListener(UNAUTHORIZED_EVENT, signOut);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, signOut);
  }, [signOut]);

  const value = useMemo(
    () => ({ theme, toggleTheme, role, setRole, user, authStatus, signIn, signOut }),
    [theme, toggleTheme, role, setRole, user, authStatus, signIn, signOut],
  );

  return (
    <QueryClientProvider client={queryClient}>
      <MotionConfig reducedMotion="user">
        <AppContext.Provider value={value}>
          <MockGate>{children}</MockGate>
        </AppContext.Provider>
      </MotionConfig>
    </QueryClientProvider>
  );
}

export function useApp(): AppState {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp debe usarse dentro de <AppProviders>");
  return ctx;
}
