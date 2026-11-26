import { CircleCheck, OctagonAlert, TriangleAlert } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { RiskLevel } from "@/lib/types";

interface RiskStyle {
  label: string;
  icon: LucideIcon;
  /** Clases completas (Tailwind necesita verlas literales). */
  badge: string;
  dot: string;
}

/** El color nunca es la única señal: cada nivel lleva también etiqueta e ícono. */
export const RISK_STYLE: Record<RiskLevel, RiskStyle> = {
  green: { label: "Riesgo bajo", icon: CircleCheck, badge: "bg-success/20 text-success", dot: "bg-success" },
  yellow: { label: "Riesgo medio", icon: TriangleAlert, badge: "bg-warning/20 text-warning", dot: "bg-warning" },
  red: { label: "Riesgo alto", icon: OctagonAlert, badge: "bg-danger/20 text-danger", dot: "bg-danger" },
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
