"use client";

import { AnimatePresence, motion } from "motion/react";
import { MousePointerClick } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { Card } from "@/components/ui/card";
import { SegmentedControl } from "@/components/ui/segmented-control";
import { useCourseRisk } from "@/lib/api/hooks/use-analytics";
import { DEMO_COURSE_ID } from "@/lib/config";
import { spring } from "@/lib/motion";
import type { RiskLevel } from "@/lib/types";
import { RiskSummary } from "./risk-summary";
import { StudentRiskList } from "./student-risk-list";
import { XaiPanel } from "./xai-panel";

type Filter = RiskLevel | "all";

const FILTERS: { value: Filter; label: string }[] = [
  { value: "all", label: "Todos" },
  { value: "red", label: "Alto" },
  { value: "yellow", label: "Medio" },
  { value: "green", label: "Bajo" },
];

export function RiskView() {
  const [filter, setFilter] = useState<Filter>("all");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const closeRef = useRef<HTMLButtonElement>(null);

  const risk = useCourseRisk(DEMO_COURSE_ID, filter === "all" ? undefined : filter);
  const students = useMemo(
    () => (risk.data ? [...risk.data.students].sort((a, b) => b.risk_score - a.risk_score) : undefined),
    [risk.data],
  );
  const selected = students?.find((s) => s.student_id === selectedId) ?? null;

  // En móvil el detalle es una hoja modal: Escape la cierra y el foco entra en ella.
  useEffect(() => {
    if (!selected) return;
    closeRef.current?.focus({ preventScroll: true });
    const onKey = (event: KeyboardEvent) => event.key === "Escape" && setSelectedId(null);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [selected]);

  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-3xl md:text-4xl">Riesgo académico</h1>
        <p className="max-w-prose text-sm text-muted">
          Quién necesita apoyo y por qué. Toca a un estudiante para ver los factores que explican su nivel.
        </p>
      </header>

      <RiskSummary summary={risk.data?.summary} active={filter} onSelect={setFilter} />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_24rem] lg:items-start">
        <Card className="space-y-3 p-3 sm:p-4">
          <SegmentedControl value={filter} onChange={setFilter} options={FILTERS} label="Filtrar por nivel de riesgo" />
          <StudentRiskList
            students={students}
            isLoading={risk.isPending}
            errorMessage={risk.isError ? risk.error.message : null}
            selectedId={selectedId}
            onSelect={setSelectedId}
            onRetry={() => void risk.refetch()}
          />
        </Card>

        {/* Escritorio: panel fijo al lado de la lista. */}
        <aside className="sticky top-6 hidden lg:block" aria-label="Detalle del estudiante">
          <Card>
            {selected ? (
              <XaiPanel student={selected} onClose={() => setSelectedId(null)} />
            ) : (
              <div className="flex flex-col items-center gap-2 py-10 text-center text-sm text-muted">
                <MousePointerClick className="size-6" aria-hidden />
                Selecciona un estudiante para ver por qué está en ese nivel.
              </div>
            )}
          </Card>
        </aside>
      </div>

      {/* Móvil: hoja inferior. */}
      <AnimatePresence>
        {selected && (
          <div className="lg:hidden">
            <motion.button
              type="button"
              aria-label="Cerrar detalle"
              tabIndex={-1}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSelectedId(null)}
              className="fixed inset-0 z-40 bg-black/50"
            />
            <motion.div
              role="dialog"
              aria-modal="true"
              aria-label={`Detalle de ${selected.name}`}
              initial={{ y: "100%" }}
              animate={{ y: 0 }}
              exit={{ y: "100%" }}
              transition={spring}
              className="fixed inset-x-0 bottom-0 z-50 max-h-[85dvh] overflow-y-auto rounded-t-3xl border border-line bg-card p-5 pb-8 shadow-card"
            >
              <XaiPanel student={selected} onClose={() => setSelectedId(null)} closeRef={closeRef} />
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      <p className="sr-only" role="status" aria-live="polite">
        {students ? `${students.length} estudiantes en la lista.` : ""}
      </p>
    </div>
  );
}
