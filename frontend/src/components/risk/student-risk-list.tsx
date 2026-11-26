"use client";

import { AnimatePresence, motion } from "motion/react";
import { ChevronRight, SearchX } from "lucide-react";
import { useEffect, useRef } from "react";
import { formatGrade, formatPercent, RISK_STYLE } from "@/lib/risk";
import { spring, tap } from "@/lib/motion";
import type { components } from "@/lib/api/schema";
import { StudentAvatar } from "./student-avatar";

type StudentRisk = components["schemas"]["StudentRisk"];

interface StudentRiskListProps {
  students: StudentRisk[] | undefined;
  isLoading: boolean;
  errorMessage: string | null;
  selectedId: string | null;
  onSelect: (studentId: string) => void;
  onRetry: () => void;
}

export function StudentRiskList({ students, isLoading, errorMessage, selectedId, onSelect, onRetry }: StudentRiskListProps) {
  // La entrada escalonada ocurre una sola vez; después los cambios de filtro solo reubican filas.
  const settled = useRef(false);
  useEffect(() => {
    if (students && students.length > 0) settled.current = true;
  }, [students]);

  if (errorMessage) {
    return (
      <div role="alert" className="space-y-3 rounded-2xl bg-danger/10 p-4 text-sm">
        <p>No pudimos cargar los estudiantes. {errorMessage}</p>
        <motion.button
          type="button"
          whileTap={tap}
          onClick={onRetry}
          className="rounded-xl bg-primary px-4 py-2 font-semibold text-on-primary"
        >
          Reintentar
        </motion.button>
      </div>
    );
  }

  if (isLoading) {
    return (
      <ul className="space-y-2" aria-label="Cargando estudiantes" aria-busy>
        {Array.from({ length: 5 }, (_, i) => (
          <li key={i} className="flex items-center gap-3 rounded-2xl p-3">
            <span className="size-12 animate-pulse rounded-full bg-line" />
            <span className="flex-1 space-y-2">
              <span className="block h-3.5 w-1/3 animate-pulse rounded-full bg-line" />
              <span className="block h-3 w-2/3 animate-pulse rounded-full bg-line" />
            </span>
          </li>
        ))}
      </ul>
    );
  }

  if (!students || students.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 px-4 py-10 text-center text-sm text-muted">
        <SearchX className="size-6" aria-hidden />
        <p>Nadie está en este nivel ahora mismo.</p>
      </div>
    );
  }

  return (
    <ul className="space-y-1" aria-label="Estudiantes por riesgo">
      <AnimatePresence mode="popLayout" initial>
        {students.map((student, index) => {
          const style = RISK_STYLE[student.risk_level];
          const Icon = style.icon;
          const selected = student.student_id === selectedId;
          const delay = settled.current ? 0 : Math.min(index, 8) * 0.05;
          return (
            <motion.li
              key={student.student_id}
              layout
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.96 }}
              transition={{ ...spring, delay }}
              className="relative"
            >
              {selected && (
                <motion.span
                  layoutId="risk-row-selection"
                  transition={spring}
                  className="absolute inset-0 rounded-2xl border border-primary/50 bg-primary/10"
                  aria-hidden
                />
              )}
              <motion.button
                type="button"
                whileTap={tap}
                aria-pressed={selected}
                onClick={() => onSelect(student.student_id)}
                className="group relative flex w-full items-center gap-3.5 rounded-2xl p-3 text-left transition-colors hover:bg-canvas/70"
              >
                <StudentAvatar name={student.name} level={student.risk_level} score={student.risk_score} delay={delay + 0.1} />
                <span className="min-w-0 flex-1 space-y-1">
                  <span className="flex flex-wrap items-center gap-x-2 gap-y-1">
                    <span className="truncate font-semibold">{student.name}</span>
                    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold ${style.badge}`}>
                      <Icon className="size-3" aria-hidden />
                      {style.label}
                    </span>
                  </span>
                  <span className="block text-xs text-muted">
                    Riesgo {formatPercent(student.risk_score)} · {student.factors.length}{" "}
                    {student.factors.length === 1 ? "factor" : "factores"}
                  </span>
                </span>
                <span className="shrink-0 text-right">
                  <span className="block text-lg font-bold leading-none tabular-nums">
                    {formatGrade(student.projected_grade, student.grade_scale_max)}
                  </span>
                  <span className="mt-1 block text-[0.6875rem] text-muted">nota proyectada</span>
                </span>
                <ChevronRight
                  className="size-4 shrink-0 text-muted transition-transform group-hover:translate-x-0.5"
                  aria-hidden
                />
              </motion.button>
            </motion.li>
          );
        })}
      </AnimatePresence>
    </ul>
  );
}
