"use client";

import { Lock } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { Card } from "@/components/ui/card";
import { useApp } from "@/lib/providers/app-providers";

const TEACHER_ROUTES = ["/riesgo", "/temas", "/documentos"];

/**
 * Oculta las vistas docentes a estudiantes. Es una guarda de UX:
 * la autorización real la aplica el backend (403).
 */
export function RoleGuard({ children }: { children: ReactNode }) {
  const { role } = useApp();
  const pathname = usePathname();

  const teacherOnly = TEACHER_ROUTES.some((route) => pathname === route || pathname.startsWith(`${route}/`));
  if (!teacherOnly || role === "teacher") return <>{children}</>;

  return (
    <div className="space-y-6">
      <h1 className="text-3xl md:text-4xl">Solo para docentes</h1>
      <Card className="flex flex-col items-start gap-4 p-8">
        <span className="grid size-12 place-items-center rounded-2xl bg-highlight/25 text-highlight">
          <Lock className="size-6" aria-hidden />
        </span>
        <p className="max-w-prose text-muted">
          Esta sección es para docentes. Cambia el rol de la demo a Docente o vuelve al inicio.
        </p>
        <Link
          href="/"
          className="rounded-2xl bg-primary px-4 py-2.5 text-sm font-semibold text-on-primary active:scale-[0.97]"
        >
          Ir al inicio
        </Link>
      </Card>
    </div>
  );
}
