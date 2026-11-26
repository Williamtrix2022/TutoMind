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
