import { CircleCheck, OctagonAlert, TriangleAlert } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { components } from "@/lib/api/schema";
import type { RiskLevel } from "@/lib/types";

type StudentRisk = components["schemas"]["StudentRisk"];

interface RiskStyle {
  label: string;
  /** «Alto», «Medio», «Bajo». */
  short: string;
  icon: LucideIcon;
  /** Color sólido para SVG (anillos, barras). Coincide con los tokens de globals.css. */
  color: string;
  /** Clases completas (Tailwind necesita verlas literales). */
  badge: string;
  dot: string;
  /** Texto legible sobre la tarjeta en ambos temas. */
  ink: string;
}

/** El color nunca es la única señal: cada nivel lleva también etiqueta e ícono. */
export const RISK_STYLE: Record<RiskLevel, RiskStyle> = {
  green: {
    label: "Riesgo bajo",
    short: "Bajo",
    icon: CircleCheck,
    color: "#6cb28e",
    badge: "bg-success/20 text-ink-success",
    dot: "bg-success",
    ink: "text-ink-success",
  },
  yellow: {
    label: "Riesgo medio",
    short: "Medio",
    icon: TriangleAlert,
    color: "#f4b63f",
    badge: "bg-caution/25 text-ink-caution",
    dot: "bg-caution",
    ink: "text-ink-caution",
  },
  red: {
    label: "Riesgo alto",
    short: "Alto",
    icon: OctagonAlert,
    color: "#e5484d",
    badge: "bg-danger/20 text-ink-danger",
    dot: "bg-danger",
    ink: "text-ink-danger",
  },
};

/** De mayor a menor urgencia, para mostrar primero lo que necesita atención. */
export const RISK_ORDER: RiskLevel[] = ["red", "yellow", "green"];

/** «2.1 / 5». La escala por defecto del contrato es 5. */
export function formatGrade(grade: number, scaleMax = 5): string {
  return `${grade.toFixed(1)} / ${scaleMax}`;
}

/** Porcentaje entero a partir de un valor de 0 a 1. */
export function formatPercent(value: number): string {
  return `${Math.round(value * 100)} %`;
}

/** En el contrato, impacto positivo = aumenta el riesgo. */
export function impactLabel(impact: number): string {
  return impact > 0 ? "Aumenta el riesgo" : impact < 0 ? "Reduce el riesgo" : "Sin efecto";
}

/** «Camila Torres» → «CT». */
export function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  return ((parts[0]?.[0] ?? "") + (parts.length > 1 ? (parts[parts.length - 1]?.[0] ?? "") : "")).toUpperCase();
}

export interface FactorSummary {
  key: string;
  label: string;
  /** Estudiantes en los que este factor aumenta el riesgo. */
  students: number;
  /** Peso relativo (0 a 1) frente al factor que más pesa. */
  share: number;
}

/** Los factores que más aumentan el riesgo en el grupo, sumando su impacto en cada estudiante. */
export function topRiskFactors(students: StudentRisk[], limit = 3): FactorSummary[] {
  const byKey = new Map<string, { label: string; students: number; total: number }>();
  for (const student of students) {
    for (const factor of student.factors) {
      if (factor.impact <= 0) continue;
      const entry = byKey.get(factor.key) ?? { label: factor.label, students: 0, total: 0 };
      entry.students += 1;
      entry.total += factor.impact;
      byKey.set(factor.key, entry);
    }
  }
  const ranked = [...byKey.entries()].sort((a, b) => b[1].total - a[1].total).slice(0, limit);
  const max = ranked[0]?.[1].total ?? 1;
  return ranked.map(([key, { label, students: count, total }]) => ({ key, label, students: count, share: total / max }));
}

/** Nota proyectada media del grupo y su escala. */
export function averageGrade(students: StudentRisk[]): { value: number; scaleMax: number } | null {
  if (students.length === 0) return null;
  const value = students.reduce((sum, s) => sum + s.projected_grade, 0) / students.length;
  return { value, scaleMax: students[0]?.grade_scale_max ?? 5 };
}
