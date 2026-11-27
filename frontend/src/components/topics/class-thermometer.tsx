"use client";

import { motion } from "motion/react";
import { AnimatedNumber } from "@/components/ui/animated-number";
import { Card } from "@/components/ui/card";
import { CONFUSION_STYLE, confusionLevel } from "@/lib/topics";

interface ClassThermometerProps {
  /** Confusión del aula, de 0 a 1. */
  score: number;
  questions: number;
  topics: number;
  alerts: number;
  period: string;
}

/** El termómetro del aula: un bulbo que se desliza por una escala de calma a confusión. */
export function ClassThermometer({ score, questions, topics, alerts, period }: ClassThermometerProps) {
  const style = CONFUSION_STYLE[confusionLevel(score)];
  const Icon = style.icon;
  const percent = score * 100;

  return (
    <Card className="relative overflow-hidden p-5 sm:p-7">
      <div
        aria-hidden
        className="pointer-events-none absolute -right-20 -top-24 size-80 rounded-full opacity-60 blur-3xl"
        style={{ background: "radial-gradient(closest-side, color-mix(in srgb, var(--color-highlight) 40%, transparent), transparent)" }}
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -bottom-28 -left-10 size-72 rounded-full opacity-40 blur-3xl"
        style={{ background: "radial-gradient(closest-side, color-mix(in srgb, var(--color-primary) 40%, transparent), transparent)" }}
      />

      <div className="relative space-y-7">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div className="space-y-2">
            <p className="text-sm text-muted">Confusión del aula · {period}</p>
            <p className="flex items-baseline gap-1 text-6xl font-extrabold leading-none tracking-tight sm:text-7xl">
              <AnimatedNumber value={percent} />
              <span className="text-3xl text-muted sm:text-4xl">%</span>
            </p>
          </div>
          <span className={`inline-flex items-center gap-2 rounded-full px-3.5 py-1.5 text-sm font-semibold ${style.pill}`}>
            <Icon className="size-4" aria-hidden />
            {style.label}
          </span>
        </div>

        {/* Escala: de la calma (periwinkle) a la confusión que necesita atención (rojo). */}
        <div className="px-3.5 pb-1 pt-9">
          <div
            role="img"
            aria-label={`Confusión del aula: ${Math.round(percent)} por ciento, ${style.label.toLowerCase()}`}
            className="relative h-4 rounded-full"
            style={{
              background:
                "linear-gradient(90deg, var(--color-primary) 0%, var(--color-glow) 38%, var(--color-highlight) 66%, var(--color-danger) 100%)",
            }}
          >
            <motion.div
              className="absolute top-1/2 -translate-y-1/2"
              initial={{ left: "0%" }}
              animate={{ left: `${percent}%` }}
              transition={{ type: "spring", stiffness: 55, damping: 14, delay: 0.2 }}
            >
              <div className="-translate-x-1/2">
                <span className="absolute -top-9 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-lg bg-fg px-2 py-1 text-xs font-bold tabular-nums text-canvas">
                  {Math.round(percent)} %
                </span>
                <span className="block size-8 rounded-full border-[5px] border-card bg-fg shadow-card" />
              </div>
            </motion.div>
          </div>
          <div className="mt-3 flex justify-between text-xs text-muted" aria-hidden>
            <span>Tranquilo</span>
            <span>Con dudas</span>
            <span>Confuso</span>
          </div>
        </div>

        <dl className="grid grid-cols-3 gap-3">
          {[
            { label: "Preguntas", value: questions },
            { label: "Temas", value: topics },
            { label: "Con alerta", value: alerts },
          ].map((stat, index) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ type: "spring", stiffness: 350, damping: 28, delay: 0.35 + index * 0.06 }}
              className="rounded-2xl bg-canvas/70 p-3.5"
            >
              <dt className="text-xs text-muted">{stat.label}</dt>
              <dd className="mt-1 text-2xl font-bold leading-none">
                <AnimatedNumber value={stat.value} />
              </dd>
            </motion.div>
          ))}
        </dl>
      </div>
    </Card>
  );
}
