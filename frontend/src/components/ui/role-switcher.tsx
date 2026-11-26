"use client";

import { useApp } from "@/lib/providers/app-providers";
import type { Role } from "@/lib/types";
import { SegmentedControl } from "./segmented-control";

const OPTIONS: { value: Role; label: string }[] = [
  { value: "student", label: "Estudiante" },
  { value: "teacher", label: "Docente" },
];

/** Selector de rol para la demo (no es autenticación real). */
export function RoleSwitcher({ className = "" }: { className?: string }) {
  const { role, setRole } = useApp();

  return (
    <SegmentedControl
      label="Rol de la demo"
      value={role}
      onChange={setRole}
      options={OPTIONS}
      className={className}
    />
  );
}
