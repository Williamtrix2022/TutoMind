"use client";

import { useEffect, useState } from "react";
import type { ReactNode } from "react";

const MOCKS_ENABLED = process.env.NEXT_PUBLIC_USE_MOCKS === "true";

/**
 * Con `NEXT_PUBLIC_USE_MOCKS=true` levanta MSW antes de renderizar,
 * para trabajar sin backend. Sin la variable no carga nada.
 */
export function MockGate({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(!MOCKS_ENABLED);

  useEffect(() => {
    if (!MOCKS_ENABLED) return;
    let cancelled = false;
    void import("@/mocks/browser").then(async ({ worker }) => {
      await worker.start({ onUnhandledRequest: "bypass" });
      if (!cancelled) setReady(true);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  return ready ? <>{children}</> : null;
}
