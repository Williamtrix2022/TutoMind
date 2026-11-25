"use client";

import { motion } from "motion/react";
import { useId } from "react";
import { useApp } from "@/lib/providers/app-providers";
import { spring } from "@/lib/motion";
import type { Role } from "@/lib/types";

const OPTIONS: { value: Role; label: string }[] = [
  { value: "student", label: "Estudiante" },
  { value: "teacher", label: "Docente" },
];

/** Selector de rol para la demo (no es autenticación real). */
export function RoleSwitcher({ className = "" }: { className?: string }) {
  const { role, setRole } = useApp();
  const pillId = useId();

  return (
    <div
      role="radiogroup"
      aria-label="Rol de la demo"
      className={`relative flex rounded-2xl border border-line bg-canvas p-1 ${className}`}
    >
      {OPTIONS.map((option) => {
        const active = role === option.value;
        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => setRole(option.value)}
            className={`relative z-10 flex-1 rounded-xl px-2 py-2 text-xs font-semibold transition-colors sm:text-sm ${
              active ? "text-on-primary" : "text-muted"
            }`}
          >
            {active && (
              <motion.span
                layoutId={pillId}
                transition={spring}
                className="absolute inset-0 -z-10 rounded-xl bg-primary"
              />
            )}
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
