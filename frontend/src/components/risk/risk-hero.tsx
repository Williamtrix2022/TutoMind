"use client";

import { motion } from "motion/react";
import { useState } from "react";
import { Card } from "@/components/ui/card";
import { AnimatedNumber } from "@/components/ui/animated-number";
import { averageGrade, formatPercent, RISK_ORDER, RISK_STYLE, topRiskFactors } from "@/lib/risk";
import { spring, tap } from "@/lib/motion";
import type { components } from "@/lib/api/schema";
import type { RiskLevel } from "@/lib/types";
import { RiskDonut } from "./risk-donut";

type StudentRisk = components["schemas"]["StudentRisk"];

interface RiskHeroProps {
  /** Conteos del curso completo (no cambian con el filtro). */
  summary: Record<RiskLevel, number> | undefined;
  /** Todos los estudiantes del curso, para la media y los factores. */
  students: StudentRisk[] | undefined;
  active: RiskLevel | "all";
  onSelect: (level: RiskLevel | "all") => void;
}

export function RiskHero({ summary, students, active, onSelect }: RiskHeroProps) {
  const [hovered, setHovered] = useState<RiskLevel | null>(null);
  const total = summary ? RISK_ORDER.reduce((sum, level) => sum + summary[level], 0) : 0;
  const grade = students ? averageGrade(students) : null;
  const factors = students ? topRiskFactors(students) : [];

  return (
    <Card className="relative overflow-hidden p-5 sm:p-7">
      <div
        aria-hidden
        className="pointer-events-none absolute -left-24 -top-24 size-80 rounded-full opacity-60 blur-3xl"
        style={{ background: "radial-gradient(closest-side, color-mix(in srgb, var(--color-primary) 35%, transparent), transparent)" }}
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -bottom-32 right-0 size-72 rounded-full opacity-40 blur-3xl"
        style={{ background: "radial-gradient(closest-side, color-mix(in srgb, var(--color-glow) 35%, transparent), transparent)" }}
      />

      <div className="relative grid gap-7 md:grid-cols-[13.5rem_minmax(0,1fr)] md:items-center">
        <RiskDonut summary={summary} active={active} hovered={hovered} onHover={setHovered} onSelect={onSelect} />

        <div className="space-y-5">
          <div className="space-y-1">
            <h2 className="text-xl">Semáforo del curso</h2>
            <p className="text-sm text-muted">Toca un nivel para filtrar la lista de estudiantes.</p>
          </div>

          <ul className="space-y-2" aria-label="Estudiantes por nivel de riesgo">
            {RISK_ORDER.map((level) => {
              const style = RISK_STYLE[level];
              const Icon = style.icon;
              const count = summary?.[level] ?? 0;
              const share = total > 0 ? count / total : 0;
              const selected = active === level;
              return (
                <li key={level}>
                  <motion.button
                    type="button"
                    whileTap={tap}
                    aria-pressed={selected}
                    onClick={() => onSelect(selected ? "all" : level)}
                    onPointerEnter={() => setHovered(level)}
                    onPointerLeave={() => setHovered(null)}
                    onFocus={() => setHovered(level)}
                    onBlur={() => setHovered(null)}
                    className={`group relative flex w-full items-center gap-3 overflow-hidden rounded-2xl border px-3 py-2.5 text-left transition-colors ${
                      selected ? "border-primary bg-primary/10" : "border-line bg-canvas/60 hover:bg-canvas"
                    }`}
                  >
                    <span className={`grid size-9 shrink-0 place-items-center rounded-xl ${style.badge}`}>
                      <Icon className="size-4.5" aria-hidden />
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="flex items-baseline justify-between gap-2">
                        <span className="text-sm font-semibold">{style.label}</span>
                        <span className="text-xs text-muted">{summary ? formatPercent(share) : "—"}</span>
                      </span>
                      <span className="mt-1.5 block h-1.5 overflow-hidden rounded-full bg-line" aria-hidden>
                        <motion.span
                          className={`block h-full origin-left rounded-full ${style.dot}`}
                          initial={{ scaleX: 0 }}
                          animate={{ scaleX: share }}
                          transition={spring}
                          style={{ width: "100%" }}
                        />
                      </span>
                    </span>
                    <span className="w-8 shrink-0 text-right text-2xl font-bold">
                      {summary ? <AnimatedNumber value={count} /> : <span className="text-muted">–</span>}
                    </span>
                  </motion.button>
                </li>
              );
            })}
          </ul>

          {grade && (
            <p className="flex items-baseline gap-2 text-sm text-muted">
              Nota proyectada media
              <span className="text-2xl font-bold text-fg">
                <AnimatedNumber value={grade.value} decimals={1} />
              </span>
              <span>/ {grade.scaleMax}</span>
            </p>
          )}
        </div>
      </div>

      {factors.length > 0 && (
        <section aria-labelledby="group-factors" className="relative mt-7 space-y-4 border-t border-line pt-5">
          <div className="space-y-0.5">
            <h3 id="group-factors" className="text-base">
              Lo que más pesa en el grupo
            </h3>
            <p className="text-xs text-muted">Factores que más aumentan el riesgo, sumando a todos los estudiantes.</p>
          </div>
          <ul className="grid gap-4 sm:grid-cols-3">
            {factors.map((factor, index) => (
              <li key={factor.key} className="space-y-2">
                <p className="text-sm font-semibold leading-snug">{factor.label}</p>
                <span className="block h-2 overflow-hidden rounded-full bg-line" aria-hidden>
                  <motion.span
                    className="block h-full origin-left rounded-full bg-gradient-to-r from-primary to-glow"
                    style={{ width: "100%" }}
                    initial={{ scaleX: 0 }}
                    animate={{ scaleX: factor.share }}
                    transition={{ ...spring, delay: 0.25 + index * 0.08 }}
                  />
                </span>
                <p className="text-xs text-muted">
                  Afecta a {factor.students} {factor.students === 1 ? "estudiante" : "estudiantes"}
                </p>
              </li>
            ))}
          </ul>
        </section>
      )}
    </Card>
  );
}
