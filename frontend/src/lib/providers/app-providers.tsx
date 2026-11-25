"use client";

import { MotionConfig } from "motion/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import type { Role, Theme } from "@/lib/types";
import { MockGate } from "./mock-gate";

interface AppState {
  theme: Theme;
  toggleTheme: () => void;
  role: Role;
  setRole: (role: Role) => void;
}

const AppContext = createContext<AppState | null>(null);

const THEME_KEY = "tm-theme";
const ROLE_KEY = "tm-role";

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

export function AppProviders({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () => new QueryClient({ defaultOptions: { queries: { staleTime: 30_000, retry: 1 } } }),
  );
  const [theme, setTheme] = useState<Theme>("dark");
  const [role, setRoleState] = useState<Role>("student");

  // Sincroniza con lo que el script inline ya aplicó al <html>.
  useEffect(() => {
    const applied = document.documentElement.dataset.theme;
    if (applied === "light" || applied === "dark") setTheme(applied);
    const storedRole = readStorage(ROLE_KEY);
    if (storedRole === "student" || storedRole === "teacher") setRoleState(storedRole);
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

  const value = useMemo(
    () => ({ theme, toggleTheme, role, setRole }),
    [theme, toggleTheme, role, setRole],
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
