"use client";

import { AnimatePresence, motion, useDragControls } from "motion/react";
import { MousePointerClick } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { Card } from "@/components/ui/card";
import { SegmentedControl } from "@/components/ui/segmented-control";
import { useCourseRisk } from "@/lib/api/hooks/use-analytics";
import { DEMO_COURSE_ID } from "@/lib/config";
import { spring } from "@/lib/motion";
import type { components } from "@/lib/api/schema";
import type { RiskLevel } from "@/lib/types";
import { RiskHero } from "./risk-hero";
import { StudentRiskList } from "./student-risk-list";
import { XaiPanel } from "./xai-panel";

type StudentRisk = components["schemas"]["StudentRisk"];
type Filter = RiskLevel | "all";

const FILTERS: { value: Filter; label: string }[] = [
  { value: "all", label: "Todos" },
  { value: "red", label: "Alto" },
  { value: "yellow", label: "Medio" },
  { value: "green", label: "Bajo" },
];

const byRisk = (list: StudentRisk[]) => [...list].sort((a, b) => b.risk_score - a.risk_score);

/** Hoja inferior (móvil). Se arrastra desde el asa y se cierra según la velocidad del gesto. */
function MobileSheet({ student, onClose }: { student: StudentRisk; onClose: () => void }) {
  const controls = useDragControls();
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    closeRef.current?.focus({ preventScroll: true });
    const onKey = (event: KeyboardEvent) => event.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="lg:hidden">
      <motion.button
        type="button"
        aria-label="Cerrar detalle"
        tabIndex={-1}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="fixed inset-0 z-40 bg-black/55"
      />
      <motion.div
        role="dialog"
        aria-modal="true"
        aria-label={`Detalle de ${student.name}`}
        initial={{ y: "100%" }}
        animate={{ y: 0 }}
        exit={{ y: "100%" }}
        transition={spring}
        drag="y"
        dragControls={controls}
        dragListener={false}
        dragConstraints={{ top: 0, bottom: 0 }}
        dragElastic={{ top: 0.05, bottom: 0.7 }}
        onDragEnd={(_, info) => {
          // Se proyecta hacia dónde iba el gesto: un empujón corto también la cierra.
          if (info.offset.y + info.velocity.y * 0.25 > 140) onClose();
        }}
        className="fixed inset-x-0 bottom-0 z-50 max-h-[88dvh] overflow-y-auto overscroll-contain rounded-t-3xl border border-line bg-card px-5 pb-8 shadow-card"
      >
        <div onPointerDown={(event) => controls.start(event)} className="-mx-5 grid h-7 cursor-grab touch-none place-items-center active:cursor-grabbing">
          <span className="h-1.5 w-10 rounded-full bg-muted/40" aria-hidden />
        </div>
        <XaiPanel student={student} onClose={onClose} closeRef={closeRef} />
      </motion.div>
    </div>
  );
}

export function RiskView() {
  const [filter, setFilter] = useState<Filter>("all");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // Curso completo (semáforo, media y factores) y lista filtrada. Sin filtro comparten caché.
  const course = useCourseRisk(DEMO_COURSE_ID);
  const risk = useCourseRisk(DEMO_COURSE_ID, filter === "all" ? undefined : filter);

  const students = useMemo(() => (risk.data ? byRisk(risk.data.students) : undefined), [risk.data]);
  const everyone = course.data?.students;
  const selected = everyone?.find((s) => s.student_id === selectedId) ?? null;
  const close = useMemo(() => () => setSelectedId(null), []);

  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-3xl md:text-4xl">Riesgo académico</h1>
        <p className="max-w-prose text-sm text-muted">
          Quién necesita apoyo y por qué. Toca a un estudiante para ver los factores que explican su nivel.
        </p>
      </header>

      <RiskHero summary={course.data?.summary} students={everyone} active={filter} onSelect={setFilter} />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_25rem] lg:items-start">
        <Card className="space-y-4 p-3 sm:p-5">
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

        {/* Escritorio: el detalle queda al lado de la lista. */}
        <aside className="sticky top-6 hidden lg:block" aria-label="Detalle del estudiante">
          <Card className="overflow-hidden">
            <AnimatePresence mode="wait" initial={false}>
              {selected ? (
                <motion.div
                  key={selected.student_id}
                  initial={{ opacity: 0, x: 12 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -12 }}
                  transition={{ duration: 0.16 }}
                >
                  <XaiPanel student={selected} onClose={close} />
                </motion.div>
              ) : (
                <motion.div
                  key="empty"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex flex-col items-center gap-3 px-4 py-14 text-center text-sm text-muted"
                >
                  <span className="grid size-12 place-items-center rounded-2xl bg-primary/15 text-primary">
                    <MousePointerClick className="size-6" aria-hidden />
                  </span>
                  Elige a un estudiante para ver por qué está en ese nivel.
                </motion.div>
              )}
            </AnimatePresence>
          </Card>
        </aside>
      </div>

      <AnimatePresence>{selected && <MobileSheet key="sheet" student={selected} onClose={close} />}</AnimatePresence>

      <p className="sr-only" role="status" aria-live="polite">
        {students ? `${students.length} estudiantes en la lista.` : ""}
      </p>
    </div>
  );
}
