"use client";

import { AnimatePresence, motion } from "motion/react";
import { AnimatedNumber } from "@/components/ui/animated-number";
import { RISK_ORDER, RISK_STYLE } from "@/lib/risk";
import type { RiskLevel } from "@/lib/types";

interface RiskDonutProps {
  summary: Record<RiskLevel, number> | undefined;
  /** Nivel que se está filtrando. */
  active: RiskLevel | "all";
  /** Nivel bajo el cursor o el foco (viene de la leyenda o del propio anillo). */
  hovered: RiskLevel | null;
  onHover: (level: RiskLevel | null) => void;
  onSelect: (level: RiskLevel | "all") => void;
}

const RADIUS = 78;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;
const px = (percent: number) => (percent / 100) * CIRCUMFERENCE;
const GAP = 1.6; // separación entre tramos, en % del anillo

/** El semáforo como anillo: cada tramo es un nivel de riesgo y también un filtro. */
export function RiskDonut({ summary, active, hovered, onHover, onSelect }: RiskDonutProps) {
  const total = summary ? RISK_ORDER.reduce((sum, level) => sum + summary[level], 0) : 0;
  const focus = hovered ?? (active === "all" ? null : active);

  let cursor = 0;
  const segments = RISK_ORDER.map((level) => {
    const share = summary && total > 0 ? (summary[level] / total) * 100 : 0;
    const length = Math.max(share - (share > 0 ? GAP : 0), 0);
    const start = cursor + GAP / 2;
    cursor += share;
    return { level, length, start };
  });

  return (
    <div className="relative mx-auto aspect-square w-48 sm:w-52" aria-hidden>
      <svg viewBox="0 0 200 200" className="size-full -rotate-90">
        <circle cx="100" cy="100" r={RADIUS} fill="none" stroke="currentColor" strokeWidth="18" className="text-line" />
        {!summary && (
          <circle
            cx="100"
            cy="100"
            r={RADIUS}
            fill="none"
            stroke="currentColor"
            strokeWidth="18"
            strokeDasharray="60 430"
            strokeLinecap="round"
            className="origin-center animate-spin text-primary/60 [animation-duration:1.4s]"
          />
        )}
        {segments.map(({ level, length, start }) => {
          if (length <= 0) return null;
          const dimmed = focus !== null && focus !== level;
          return (
            <motion.circle
              key={level}
              cx="100"
              cy="100"
              r={RADIUS}
              fill="none"
              stroke={RISK_STYLE[level].color}
              strokeDashoffset={-px(start)}
              initial={{ strokeDasharray: `0 ${CIRCUMFERENCE}`, strokeWidth: 18 }}
              animate={{
                strokeDasharray: `${px(length)} ${CIRCUMFERENCE}`,
                strokeWidth: focus === level ? 24 : 18,
                opacity: dimmed ? 0.28 : 1,
              }}
              transition={{ type: "spring", stiffness: 140, damping: 22 }}
              style={{ cursor: "pointer" }}
              onPointerEnter={() => onHover(level)}
              onPointerLeave={() => onHover(null)}
              onClick={() => onSelect(active === level ? "all" : level)}
            />
          );
        })}
      </svg>

      {/* Centro: el total, o el nivel que se está mirando. */}
      <div className="pointer-events-none absolute inset-0 grid place-items-center">
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={focus ?? "total"}
            initial={{ opacity: 0, scale: 0.92 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.96 }}
            transition={{ duration: 0.16 }}
            className="text-center"
          >
            <p className="text-5xl font-extrabold leading-none tracking-tight">
              <AnimatedNumber value={summary ? (focus ? summary[focus] : total) : 0} />
            </p>
            <p className={`mt-1.5 text-xs font-semibold ${focus ? RISK_STYLE[focus].ink : "text-muted"}`}>
              {focus ? RISK_STYLE[focus].label : "estudiantes"}
            </p>
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
