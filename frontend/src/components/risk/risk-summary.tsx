"use client";

import { motion } from "motion/react";
import { RISK_ORDER, RISK_STYLE } from "@/lib/risk";
import { tap } from "@/lib/motion";
import type { RiskLevel } from "@/lib/types";

interface RiskSummaryProps {
  /** Conteos de todo el curso (no cambian con el filtro). */
  summary: Record<RiskLevel, number> | undefined;
  active: RiskLevel | "all";
  onSelect: (level: RiskLevel | "all") => void;
}

/** Semáforo del curso: cada tarjeta filtra la lista por su nivel. */
export function RiskSummary({ summary, active, onSelect }: RiskSummaryProps) {
  return (
    <ul className="grid grid-cols-3 gap-3" aria-label="Resumen de riesgo del curso">
      {RISK_ORDER.map((level) => {
        const style = RISK_STYLE[level];
        const Icon = style.icon;
        const selected = active === level;
        return (
          <li key={level}>
            <motion.button
              type="button"
              whileTap={tap}
              aria-pressed={selected}
              onClick={() => onSelect(selected ? "all" : level)}
              className={`flex h-full w-full flex-col items-start gap-2 rounded-3xl border bg-card p-4 text-left shadow-card transition-colors ${
                selected ? "border-primary" : "border-line"
              }`}
            >
              <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${style.badge}`}>
                <Icon className="size-3.5" aria-hidden />
                {style.label}
              </span>
              <span className="text-3xl font-semibold leading-none md:text-4xl">
                {summary ? summary[level] : <span className="inline-block h-8 w-8 animate-pulse rounded-lg bg-line" />}
              </span>
              <span className="text-xs text-muted">estudiantes</span>
            </motion.button>
          </li>
        );
      })}
    </ul>
  );
}
