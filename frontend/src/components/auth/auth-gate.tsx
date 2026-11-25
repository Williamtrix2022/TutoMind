"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import type { ReactNode } from "react";
import { TutorOrb } from "@/components/tutor/tutor-orb";
import { useApp } from "@/lib/providers/app-providers";

/** Exige sesión: sin ella redirige a /login y recuerda a dónde volver. */
export function AuthGate({ children }: { children: ReactNode }) {
  const { authStatus } = useApp();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (authStatus === "anonymous") router.replace(`/login?next=${encodeURIComponent(pathname)}`);
  }, [authStatus, pathname, router]);

  if (authStatus !== "authenticated") {
    return (
      <div className="grid min-h-dvh place-items-center" role="status" aria-label="Cargando sesión">
        <TutorOrb active className="size-12" />
      </div>
    );
  }

  return <>{children}</>;
}
