"use client";

import { motion } from "motion/react";
import { ChevronRight } from "lucide-react";
import { formatGrade, formatPercent, RISK_STYLE } from "@/lib/risk";
import { tap } from "@/lib/motion";
import type { components } from "@/lib/api/schema";

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
  if (errorMessage) {
    return (
      <div role="alert" className="space-y-3 p-4 text-sm">
        <p>No pudimos cargar los estudiantes. {errorMessage}</p>
        <button type="button" onClick={onRetry} className="rounded-xl bg-primary px-4 py-2 font-semibold text-on-primary">
          Reintentar
        </button>
      </div>
    );
  }

  if (isLoading) {
    return (
      <ul className="space-y-2 p-2" aria-label="Cargando estudiantes" aria-busy>
        {Array.from({ length: 5 }, (_, i) => (
          <li key={i} className="h-16 animate-pulse rounded-2xl bg-line" />
        ))}
      </ul>
    );
  }

  if (!students || students.length === 0) {
    return <p className="p-6 text-center text-sm text-muted">No hay estudiantes en este nivel.</p>;
  }

  return (
    <ul className="divide-y divide-line" aria-label="Estudiantes por riesgo">
      {students.map((student) => {
        const style = RISK_STYLE[student.risk_level];
        const Icon = style.icon;
        const selected = student.student_id === selectedId;
        return (
          <li key={student.student_id}>
            <motion.button
              type="button"
              whileTap={tap}
              aria-pressed={selected}
              onClick={() => onSelect(student.student_id)}
              className={`flex w-full items-center gap-3 px-3 py-3 text-left transition-colors ${
                selected ? "bg-primary/10" : "hover:bg-canvas"
              }`}
            >
              <span className="min-w-0 flex-1 space-y-1.5">
                <span className="flex flex-wrap items-center gap-x-2 gap-y-1">
                  <span className="truncate font-semibold">{student.name}</span>
                  <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold ${style.badge}`}>
                    <Icon className="size-3" aria-hidden />
                    {style.label}
                  </span>
                </span>
                <span className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted">
                  <span className="h-1.5 w-24 shrink-0 overflow-hidden rounded-full bg-line" aria-hidden>
                    <span className={`block h-full rounded-full ${style.dot}`} style={{ width: formatPercent(student.risk_score) }} />
                  </span>
                  <span>Riesgo {formatPercent(student.risk_score)}</span>
                  <span>Nota proyectada {formatGrade(student.projected_grade, student.grade_scale_max)}</span>
                </span>
              </span>
              <ChevronRight className="size-4 shrink-0 text-muted" aria-hidden />
            </motion.button>
          </li>
        );
      })}
    </ul>
  );
}
