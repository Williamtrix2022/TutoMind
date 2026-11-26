"use client";

import { motion } from "motion/react";
import { X } from "lucide-react";
import type { Ref } from "react";
import { formatGrade, formatPercent, impactLabel, RISK_STYLE } from "@/lib/risk";
import { tap } from "@/lib/motion";
import type { components } from "@/lib/api/schema";

type StudentRisk = components["schemas"]["StudentRisk"];
type XaiFactor = components["schemas"]["XaiFactor"];

function FactorRow({ factor }: { factor: XaiFactor }) {
  const raises = factor.impact > 0;
  const width = `${Math.min(Math.abs(factor.impact), 1) * 50}%`;
  const sign = raises ? "+" : factor.impact < 0 ? "−" : "";

  return (
    <li className="space-y-2">
      <div className="flex items-baseline justify-between gap-3">
        <span className="font-semibold">{factor.label}</span>
        <span className="shrink-0 text-sm text-muted">{String(factor.value)}</span>
      </div>
      {/* Barra divergente: derecha = aumenta el riesgo, izquierda = lo reduce. */}
      <div className="relative h-2 rounded-full bg-line" aria-hidden>
        <span className="absolute inset-y-0 left-1/2 w-px bg-muted/60" />
        <span
          className={`absolute inset-y-0 rounded-full ${raises ? "left-1/2 bg-danger" : "right-1/2 bg-success"}`}
          style={{ width }}
        />
      </div>
      <p className={`text-xs font-semibold ${raises ? "text-danger" : "text-success"}`}>
        {impactLabel(factor.impact)} · {sign}
        {formatPercent(Math.abs(factor.impact))}
      </p>
      <p className="text-sm text-muted">{factor.explanation}</p>
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
      <header className="flex items-start justify-between gap-3">
        <div className="space-y-2">
          <h2 className="text-xl">{student.name}</h2>
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
          className="grid size-9 shrink-0 place-items-center rounded-xl border border-line text-muted hover:text-fg"
        >
          <X className="size-4" aria-hidden />
        </motion.button>
      </header>

      <div className="rounded-2xl bg-canvas p-4">
        <p className="text-xs text-muted">Nota proyectada</p>
        <p className="text-3xl font-semibold">{formatGrade(student.projected_grade, student.grade_scale_max)}</p>
        <p className="mt-1 text-xs text-muted">
          Actualizado el {new Date(student.updated_at).toLocaleDateString("es", { day: "numeric", month: "long" })}
        </p>
      </div>

      <section aria-labelledby={`xai-${student.student_id}`} className="space-y-4">
        <h3 id={`xai-${student.student_id}`} className="text-sm font-semibold text-muted">
          Qué explica este resultado
        </h3>
        <ul className="space-y-5">
          {factors.map((factor) => (
            <FactorRow key={factor.key} factor={factor} />
          ))}
        </ul>
      </section>
    </div>
  );
}
