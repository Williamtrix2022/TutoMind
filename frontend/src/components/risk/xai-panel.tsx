"use client";

import { motion } from "motion/react";
import { TrendingDown, TrendingUp, X } from "lucide-react";
import type { Ref } from "react";
import { AnimatedNumber } from "@/components/ui/animated-number";
import { formatPercent, impactLabel, RISK_STYLE } from "@/lib/risk";
import { spring, tap } from "@/lib/motion";
import type { components } from "@/lib/api/schema";
import { StudentAvatar } from "./student-avatar";

type StudentRisk = components["schemas"]["StudentRisk"];
type XaiFactor = components["schemas"]["XaiFactor"];

/** Medidor semicircular de la nota proyectada. */
function GradeGauge({ student }: { student: StudentRisk }) {
  const max = student.grade_scale_max ?? 5;
  const ratio = Math.min(Math.max(student.projected_grade / max, 0), 1);
  const color = RISK_STYLE[student.risk_level].color;

  return (
    <div className="relative mx-auto w-full max-w-[15rem]">
      <svg viewBox="0 0 200 112" className="w-full" role="img" aria-label={`Nota proyectada ${student.projected_grade.toFixed(1)} de ${max}`}>
        <path d="M20 100A80 80 0 0 1 180 100" fill="none" stroke="currentColor" strokeWidth="14" strokeLinecap="round" className="text-line" />
        <motion.path
          d="M20 100A80 80 0 0 1 180 100"
          fill="none"
          stroke={color}
          strokeWidth="14"
          strokeLinecap="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: ratio }}
          transition={{ type: "spring", stiffness: 60, damping: 18, delay: 0.1 }}
        />
        <text x="14" y="111" fontSize="10" fill="currentColor" className="text-muted">
          0
        </text>
        <text x="186" y="111" fontSize="10" textAnchor="end" fill="currentColor" className="text-muted">
          {max}
        </text>
      </svg>
      <div className="absolute inset-x-0 bottom-1 text-center">
        <p className="text-4xl font-extrabold leading-none tracking-tight">
          <AnimatedNumber value={student.projected_grade} decimals={1} />
        </p>
        <p className="mt-1 text-xs text-muted">nota proyectada</p>
      </div>
    </div>
  );
}

function FactorRow({ factor, index }: { factor: XaiFactor; index: number }) {
  const raises = factor.impact > 0;
  const magnitude = Math.min(Math.abs(factor.impact), 1);
  const Icon = raises ? TrendingUp : TrendingDown;

  return (
    <li className="space-y-2.5 rounded-2xl bg-canvas/70 p-3.5">
      <div className="flex items-start justify-between gap-3">
        <p className="font-semibold leading-snug">{factor.label}</p>
        <span className="shrink-0 rounded-lg bg-card px-2 py-0.5 text-xs font-semibold tabular-nums text-muted">
          {String(factor.value)}
        </span>
      </div>

      {/* Barra divergente: a la derecha aumenta el riesgo, a la izquierda lo reduce. */}
      <div className="relative h-2.5 rounded-full bg-line" aria-hidden>
        <span className="absolute inset-y-[-3px] left-1/2 w-px bg-muted/50" />
        <motion.span
          className={`absolute inset-y-0 rounded-full ${raises ? "left-1/2 origin-left bg-danger" : "right-1/2 origin-right bg-success"}`}
          style={{ width: `${magnitude * 50}%` }}
          initial={{ scaleX: 0 }}
          animate={{ scaleX: 1 }}
          transition={{ ...spring, delay: 0.15 + index * 0.08 }}
        />
      </div>

      <p className={`flex items-center gap-1.5 text-xs font-semibold ${raises ? "text-ink-danger" : "text-ink-success"}`}>
        <Icon className="size-3.5" aria-hidden />
        {impactLabel(factor.impact)} · {raises ? "+" : "−"}
        {formatPercent(Math.abs(factor.impact))}
      </p>
      <p className="text-sm leading-relaxed text-muted">{factor.explanation}</p>
    </li>
  );
}

interface XaiPanelProps {
  student: StudentRisk;
  onClose: () => void;
  closeRef?: Ref<HTMLButtonElement>;
}

/** Por qué el sistema calificó así al estudiante: nota proyectada y factores explícitos. */
export function XaiPanel({ student, onClose, closeRef }: XaiPanelProps) {
  const style = RISK_STYLE[student.risk_level];
  const Icon = style.icon;
  const factors = [...student.factors].sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact));

  return (
    <div className="space-y-5">
      <header className="flex items-center gap-3.5">
        <StudentAvatar name={student.name} level={student.risk_level} score={student.risk_score} size={56} />
        <div className="min-w-0 flex-1 space-y-1.5">
          <h2 className="truncate text-xl">{student.name}</h2>
          <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${style.badge}`}>
            <Icon className="size-3.5" aria-hidden />
            {style.label} · {formatPercent(student.risk_score)}
          </span>
        </div>
        <motion.button
          ref={closeRef}
          type="button"
          whileTap={tap}
          onClick={onClose}
          aria-label="Cerrar detalle"
          className="grid size-9 shrink-0 place-items-center self-start rounded-xl border border-line text-muted transition-colors hover:text-fg"
        >
          <X className="size-4" aria-hidden />
        </motion.button>
      </header>

      <div className="rounded-3xl bg-canvas/70 px-4 pb-4 pt-5">
        <GradeGauge student={student} />
        <p className="mt-3 text-center text-xs text-muted">
          Actualizado el {new Date(student.updated_at).toLocaleDateString("es", { day: "numeric", month: "long" })}
        </p>
      </div>

      <section aria-labelledby={`xai-${student.student_id}`} className="space-y-3">
        <h3 id={`xai-${student.student_id}`} className="text-base">
          Qué explica este resultado
        </h3>
        <ul className="space-y-3">
          {factors.map((factor, index) => (
            <FactorRow key={factor.key} factor={factor} index={index} />
          ))}
        </ul>
      </section>
    </div>
  );
}
