"use client";

import { motion } from "motion/react";
import { initials, RISK_STYLE } from "@/lib/risk";
import type { RiskLevel } from "@/lib/types";

interface StudentAvatarProps {
  name: string;
  level: RiskLevel;
  /** Riesgo de 0 a 1: es lo que dibuja el anillo. */
  score: number;
  size?: number;
  delay?: number;
}

/** Iniciales dentro de un anillo que se llena según el riesgo del estudiante. */
export function StudentAvatar({ name, level, score, size = 48, delay = 0 }: StudentAvatarProps) {
  const stroke = Math.max(3, size / 14);
  const radius = (size - stroke) / 2;
  const center = size / 2;

  return (
    <span className="relative grid shrink-0 place-items-center" style={{ width: size, height: size }} aria-hidden>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="absolute inset-0 -rotate-90">
        <circle cx={center} cy={center} r={radius} fill="none" stroke="currentColor" strokeWidth={stroke} className="text-line" />
        <motion.circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke={RISK_STYLE[level].color}
          strokeWidth={stroke}
          strokeLinecap="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: score }}
          transition={{ type: "spring", stiffness: 70, damping: 18, delay }}
        />
      </svg>
      <span
        className="grid place-items-center rounded-full bg-canvas font-bold tracking-tight"
        style={{ width: size - stroke * 2 - 4, height: size - stroke * 2 - 4, fontSize: size * 0.3 }}
      >
        {initials(name)}
      </span>
    </span>
  );
}
