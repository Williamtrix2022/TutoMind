"use client";

import { motion } from "motion/react";
import { Pause, Play, RotateCcw } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Card } from "@/components/ui/card";
import { SegmentedControl } from "@/components/ui/segmented-control";
import { spring, tap } from "@/lib/motion";

type Mode = "focus" | "break";

const MODES: { value: Mode; label: string }[] = [
  { value: "focus", label: "Enfoque" },
  { value: "break", label: "Pausa" },
];
const SECONDS: Record<Mode, number> = { focus: 25 * 60, break: 5 * 60 };
const RADIUS = 78;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

const clock = (seconds: number) =>
  `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;

/** Temporizador de estudio 25/5: ayuda a repasar por bloques cortos, sin depender de datos del servidor. */
export function FocusTimer() {
  const [mode, setMode] = useState<Mode>("focus");
  const [left, setLeft] = useState(SECONDS.focus);
  const [running, setRunning] = useState(false);
  const [sessions, setSessions] = useState(0);
  const [announcement, setAnnouncement] = useState("");
  // Se mide contra el reloj y no contando ticks: una pestaña en segundo plano no atrasa el tiempo.
  const endAt = useRef(0);

  const choose = useCallback((next: Mode) => {
    setMode(next);
    setLeft(SECONDS[next]);
    setRunning(false);
  }, []);

  useEffect(() => {
    if (!running) return;
    const id = window.setInterval(() => {
      const remaining = Math.max(0, Math.round((endAt.current - Date.now()) / 1000));
      setLeft(remaining);
      if (remaining > 0) return;
      window.clearInterval(id);
      setRunning(false);
      if (mode === "focus") {
        setSessions((count) => count + 1);
        setAnnouncement("Terminaste un bloque de enfoque. Toma una pausa.");
        setMode("break");
        setLeft(SECONDS.break);
      } else {
        setAnnouncement("La pausa terminó. Listo para otro bloque.");
        setMode("focus");
        setLeft(SECONDS.focus);
      }
    }, 250);
    return () => window.clearInterval(id);
  }, [running, mode]);

  function toggle() {
    if (!running) endAt.current = Date.now() + left * 1000;
    setAnnouncement("");
    setRunning((value) => !value);
  }

  const total = SECONDS[mode];
  const color = mode === "focus" ? "var(--color-primary)" : "var(--color-success)";

  return (
    <Card className="flex h-full flex-col items-center gap-5">
      <div className="w-full space-y-1">
        <h2 className="text-xl">Bloque de estudio</h2>
        <p className="text-sm text-muted">25 minutos de enfoque y 5 de pausa rinden más que horas seguidas.</p>
      </div>

      <SegmentedControl label="Tipo de bloque" value={mode} onChange={choose} options={MODES} className="w-full" />

      <div className="relative size-44">
        <svg viewBox="0 0 200 200" className="size-full -rotate-90" aria-hidden>
          <circle cx="100" cy="100" r={RADIUS} fill="none" stroke="currentColor" strokeWidth="12" className="text-line" />
          <motion.circle
            cx="100"
            cy="100"
            r={RADIUS}
            fill="none"
            stroke={color}
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={CIRCUMFERENCE}
            animate={{ strokeDashoffset: CIRCUMFERENCE * (1 - left / total) }}
            transition={{ duration: running ? 0.3 : 0.5, ease: "linear" }}
          />
        </svg>
        <div className="absolute inset-0 grid place-items-center">
          <div className="text-center">
            <p role="timer" className="text-4xl font-extrabold tabular-nums tracking-tight">
              {clock(left)}
            </p>
            <p className="mt-1 text-xs text-muted">{mode === "focus" ? "Enfoque" : "Pausa"}</p>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <motion.button
          type="button"
          whileTap={tap}
          transition={spring}
          onClick={toggle}
          className="inline-flex min-w-36 items-center justify-center gap-2 rounded-2xl bg-primary px-5 py-3 font-semibold text-on-primary"
        >
          {running ? <Pause className="size-4" aria-hidden /> : <Play className="size-4" aria-hidden />}
          {running ? "Pausar" : left < total ? "Seguir" : "Empezar"}
        </motion.button>
        <motion.button
          type="button"
          whileTap={tap}
          transition={spring}
          onClick={() => choose(mode)}
          aria-label="Reiniciar bloque"
          className="grid size-12 place-items-center rounded-2xl border border-line text-muted hover:text-fg"
        >
          <RotateCcw className="size-4" aria-hidden />
        </motion.button>
      </div>

      <div className="mt-auto flex items-center gap-2 text-sm text-muted" aria-label={`${sessions} bloques completados`}>
        <span className="flex gap-1.5" aria-hidden>
          {Array.from({ length: 4 }, (_, i) => (
            <motion.span
              key={i}
              animate={{ scale: i < sessions ? 1 : 0.8 }}
              transition={spring}
              className={`size-2.5 rounded-full ${i < sessions ? "bg-primary" : "bg-line"}`}
            />
          ))}
        </span>
        {sessions === 0 ? "Aún no completas bloques" : `${sessions} ${sessions === 1 ? "bloque completado" : "bloques completados"}`}
      </div>

      <p className="sr-only" role="status" aria-live="polite">
        {announcement}
      </p>
    </Card>
  );
}
