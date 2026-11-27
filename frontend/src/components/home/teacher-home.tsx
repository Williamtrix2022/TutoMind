"use client";

import { motion } from "motion/react";
import Link from "next/link";
import { ArrowUpRight, FileCheck2, FileClock, FileWarning, Flame } from "lucide-react";
import type { ReactNode } from "react";
import { useState } from "react";
import { RiskDonut } from "@/components/risk/risk-donut";
import { StudentAvatar } from "@/components/risk/student-avatar";
import { AnimatedNumber } from "@/components/ui/animated-number";
import { Card } from "@/components/ui/card";
import { useCourseRisk, useCourseTopics } from "@/lib/api/hooks/use-analytics";
import { useCourseDocuments } from "@/lib/api/hooks/use-documents";
import { DEMO_COURSE_ID } from "@/lib/config";
import { spring, tap } from "@/lib/motion";
import { useApp } from "@/lib/providers/app-providers";
import { averageGrade, formatGrade, formatPercent, RISK_ORDER, RISK_STYLE, topRiskFactors } from "@/lib/risk";
import { CONFUSION_STYLE, classConfusion, confusionLevel } from "@/lib/topics";
import type { RiskLevel } from "@/lib/types";
import { firstName, useGreeting } from "./greeting";

/** Tarjeta enlazada con elevación al pasar el cursor y feedback al pulsar. */
function Tile({ href, title, className = "", children }: { href: string; title: string; className?: string; children: ReactNode }) {
  return (
    <motion.div whileTap={tap} whileHover={{ y: -3 }} transition={spring} className={className}>
      <Link href={href} className="group block h-full rounded-3xl">
        <Card className="relative flex h-full flex-col gap-5 transition-colors group-hover:border-primary/60">
          <div className="flex items-start justify-between gap-3">
            <h2 className="text-lg">{title}</h2>
            <ArrowUpRight
              className="size-5 shrink-0 text-muted transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-primary"
              aria-hidden
            />
          </div>
          {children}
        </Card>
      </Link>
    </motion.div>
  );
}

function Pulse({ className }: { className: string }) {
  return <span className={`block animate-pulse rounded-2xl bg-line ${className}`} />;
}

function RiskTile() {
  const risk = useCourseRisk(DEMO_COURSE_ID);
  const [hovered, setHovered] = useState<RiskLevel | null>(null);
  const summary = risk.data?.summary;
  const attention = (risk.data?.students ?? [])
    .filter((s) => s.risk_level !== "green")
    .sort((a, b) => b.risk_score - a.risk_score)
    .slice(0, 3);

  return (
    <Tile href="/riesgo" title="Riesgo académico" className="lg:col-span-2">
      {risk.isError ? (
        <p className="text-sm text-muted">No pudimos cargar el riesgo del curso.</p>
      ) : (
        <div className="grid items-center gap-6 sm:grid-cols-[10rem_minmax(0,1fr)]">
          <RiskDonut
            summary={summary}
            active="all"
            hovered={hovered}
            onHover={setHovered}
            onSelect={() => undefined}
            className="w-36 sm:w-40"
          />
          <div className="space-y-4">
            <ul className="flex flex-wrap gap-2" aria-label="Estudiantes por nivel">
              {RISK_ORDER.map((level) => {
                const style = RISK_STYLE[level];
                const Icon = style.icon;
                return (
                  <li key={level} className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-semibold ${style.badge}`}>
                    <Icon className="size-3.5" aria-hidden />
                    {summary ? <AnimatedNumber value={summary[level]} /> : "–"} {style.short.toLowerCase()}
                  </li>
                );
              })}
            </ul>
            <div className="space-y-2">
              <p className="text-sm font-semibold">Requieren atención</p>
              {!risk.data ? (
                <Pulse className="h-24" />
              ) : attention.length === 0 ? (
                <p className="text-sm text-muted">Nadie está en riesgo ahora mismo.</p>
              ) : (
                <ul className="space-y-2">
                  {attention.map((student, index) => (
                    <motion.li
                      key={student.student_id}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ ...spring, delay: 0.2 + index * 0.08 }}
                      className="flex items-center gap-3"
                    >
                      <StudentAvatar name={student.name} level={student.risk_level} score={student.risk_score} size={40} delay={0.3 + index * 0.08} />
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-sm font-semibold">{student.name}</span>
                        <span className="block text-xs text-muted">
                          {RISK_STYLE[student.risk_level].label} · {formatPercent(student.risk_score)}
                        </span>
                      </span>
                      <span className="text-sm font-bold tabular-nums">{formatGrade(student.projected_grade, student.grade_scale_max)}</span>
                    </motion.li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      )}
    </Tile>
  );
}

function TopicsTile() {
  const topics = useCourseTopics(DEMO_COURSE_ID);
  const list = topics.data?.topics ?? [];
  const score = classConfusion(list);
  const style = CONFUSION_STYLE[confusionLevel(score)];
  const Icon = style.icon;
  const hottest = list.filter((t) => t.confusion_alert).sort((a, b) => b.confusion_score - a.confusion_score)[0];

  return (
    <Tile href="/temas" title="Termómetro del aula">
      {topics.isError ? (
        <p className="text-sm text-muted">No pudimos cargar los temas.</p>
      ) : !topics.data ? (
        <Pulse className="h-32" />
      ) : list.length === 0 ? (
        <p className="text-sm text-muted">Aún no hay preguntas en este periodo.</p>
      ) : (
        <>
          <div className="flex items-end justify-between gap-3">
            <p className="flex items-baseline gap-1 text-5xl font-extrabold leading-none tracking-tight">
              <AnimatedNumber value={score * 100} />
              <span className="text-2xl text-muted">%</span>
            </p>
            <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${style.pill}`}>
              <Icon className="size-3.5" aria-hidden />
              {style.label}
            </span>
          </div>
          <div
            className="relative h-2.5 rounded-full"
            aria-hidden
            style={{
              background:
                "linear-gradient(90deg, var(--color-primary), var(--color-glow) 38%, var(--color-highlight) 66%, var(--color-danger))",
            }}
          >
            <motion.span
              className="absolute top-1/2 size-5 -translate-x-1/2 -translate-y-1/2 rounded-full border-4 border-card bg-fg shadow-card"
              initial={{ left: "0%" }}
              animate={{ left: `${score * 100}%` }}
              transition={{ type: "spring", stiffness: 55, damping: 14, delay: 0.2 }}
            />
          </div>
          {hottest ? (
            <p className="flex items-start gap-2 rounded-2xl border border-highlight/60 bg-highlight/12 p-3 text-sm">
              <Flame className="mt-0.5 size-4 shrink-0 text-ink-caution" aria-hidden />
              <span>
                <span className="font-semibold">{hottest.topic}</span> genera confusión grupal.
              </span>
            </p>
          ) : (
            <p className="text-sm text-muted">Ningún tema tiene confusión grupal.</p>
          )}
        </>
      )}
    </Tile>
  );
}

function FactorsTile() {
  const risk = useCourseRisk(DEMO_COURSE_ID);
  const students = risk.data?.students;
  const factors = students ? topRiskFactors(students) : [];
  const grade = students ? averageGrade(students) : null;

  return (
    <Tile href="/riesgo" title="Lo que más pesa en el grupo" className="lg:col-span-2">
      {!students ? (
        <Pulse className="h-28" />
      ) : factors.length === 0 ? (
        <p className="text-sm text-muted">No hay factores que aumenten el riesgo.</p>
      ) : (
        <div className="grid gap-5 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
          <ul className="space-y-3">
            {factors.map((factor, index) => (
              <li key={factor.key} className="space-y-1.5">
                <div className="flex items-baseline justify-between gap-3 text-sm">
                  <span className="font-semibold">{factor.label}</span>
                  <span className="shrink-0 text-xs text-muted">
                    {factor.students} {factor.students === 1 ? "estudiante" : "estudiantes"}
                  </span>
                </div>
                <span className="block h-2 overflow-hidden rounded-full bg-line" aria-hidden>
                  <motion.span
                    className="block h-full origin-left rounded-full bg-gradient-to-r from-primary to-glow"
                    style={{ width: "100%" }}
                    initial={{ scaleX: 0 }}
                    animate={{ scaleX: factor.share }}
                    transition={{ ...spring, delay: 0.25 + index * 0.08 }}
                  />
                </span>
              </li>
            ))}
          </ul>
          {grade && (
            <div className="rounded-2xl bg-canvas/70 px-5 py-4 text-center">
              <p className="text-xs text-muted">Nota proyectada media</p>
              <p className="mt-1 text-4xl font-extrabold leading-none">
                <AnimatedNumber value={grade.value} decimals={1} />
              </p>
              <p className="mt-1 text-xs text-muted">de {grade.scaleMax}</p>
            </div>
          )}
        </div>
      )}
    </Tile>
  );
}

function DocumentsTile() {
  const docs = useCourseDocuments(DEMO_COURSE_ID);
  const list = docs.data?.documents ?? [];
  const indexed = list.filter((d) => d.status === "indexed").length;
  const pending = list.filter((d) => d.status === "queued" || d.status === "processing").length;
  const failed = list.filter((d) => d.status === "failed").length;

  return (
    <Tile href="/documentos" title="Documentos del curso">
      {docs.isError ? (
        <p className="text-sm text-muted">No pudimos cargar los documentos.</p>
      ) : !docs.data ? (
        <Pulse className="h-28" />
      ) : (
        <>
          <p className="flex items-baseline gap-2">
            <span className="text-5xl font-extrabold leading-none tracking-tight">
              <AnimatedNumber value={list.length} />
            </span>
            <span className="text-sm text-muted">{list.length === 1 ? "documento" : "documentos"} para el tutor</span>
          </p>
          <ul className="flex flex-wrap gap-2 text-xs font-semibold">
            <li className="inline-flex items-center gap-1.5 rounded-full bg-success/20 px-2.5 py-1 text-ink-success">
              <FileCheck2 className="size-3.5" aria-hidden />
              {indexed} listos
            </li>
            {pending > 0 && (
              <li className="inline-flex items-center gap-1.5 rounded-full bg-primary/20 px-2.5 py-1 text-ink-primary">
                <FileClock className="size-3.5 motion-safe:animate-pulse" aria-hidden />
                {pending} indexando
              </li>
            )}
            {failed > 0 && (
              <li className="inline-flex items-center gap-1.5 rounded-full bg-danger/20 px-2.5 py-1 text-ink-danger">
                <FileWarning className="size-3.5" aria-hidden />
                {failed} con error
              </li>
            )}
          </ul>
          {list.length === 0 && <p className="text-sm text-muted">Sube el primer material para que el tutor pueda ayudar.</p>}
        </>
      )}
    </Tile>
  );
}

export function TeacherHome() {
  const { user } = useApp();
  const greeting = useGreeting();
  const who = firstName(user?.name);

  return (
    <div className="space-y-6">
      <header className="space-y-3">
        <p className="inline-flex rounded-full bg-primary/15 px-3 py-1 text-sm font-semibold text-ink-primary">
          {greeting}
          {who && `, ${who}`}
        </p>
        <h1 className="text-4xl leading-[1.05] md:text-5xl">Tu aula, de un vistazo</h1>
        <p className="max-w-prose text-muted">Mira el riesgo de cada estudiante, entiende sus causas y actúa a tiempo.</p>
      </header>

      <div className="grid gap-5 lg:grid-cols-3">
        <RiskTile />
        <TopicsTile />
        <FactorsTile />
        <DocumentsTile />
      </div>
    </div>
  );
}
