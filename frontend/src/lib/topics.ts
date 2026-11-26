import { Thermometer, ThermometerSnowflake, ThermometerSun } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { components } from "@/lib/api/schema";

type TopicStat = components["schemas"]["TopicStat"];

export type ConfusionLevel = "high" | "medium" | "low";

interface ConfusionStyle {
  label: string;
  icon: LucideIcon;
  /** Clases literales para que Tailwind las vea. */
  pill: string;
}

/** El color nunca va solo: cada nivel lleva también etiqueta e ícono. */
export const CONFUSION_STYLE: Record<ConfusionLevel, ConfusionStyle> = {
  high: { label: "Confusión alta", icon: ThermometerSun, pill: "bg-danger/20 text-ink-danger" },
  medium: { label: "Confusión media", icon: Thermometer, pill: "bg-caution/25 text-ink-caution" },
  low: { label: "Confusión baja", icon: ThermometerSnowflake, pill: "bg-success/20 text-ink-success" },
};

export function confusionLevel(score: number): ConfusionLevel {
  if (score >= 0.6) return "high";
  if (score >= 0.3) return "medium";
  return "low";
}

/** Confusión del aula: la de cada tema, ponderada por cuántas preguntas generó. */
export function classConfusion(topics: TopicStat[]): number {
  const questions = topics.reduce((sum, t) => sum + t.question_count, 0);
  if (questions === 0) return 0;
  return topics.reduce((sum, t) => sum + t.confusion_score * t.question_count, 0) / questions;
}

/** «17 – 24 nov». */
export function formatPeriod(start: string, end: string): string {
  const day = new Intl.DateTimeFormat("es", { day: "numeric", timeZone: "UTC" });
  const dayMonth = new Intl.DateTimeFormat("es", { day: "numeric", month: "short", timeZone: "UTC" });
  const from = new Date(start);
  const to = new Date(end);
  const sameMonth = from.getUTCMonth() === to.getUTCMonth();
  return `${sameMonth ? day.format(from) : dayMonth.format(from)} – ${dayMonth.format(to)}`.replace(/\./g, "");
}
