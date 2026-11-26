"use client";

import { motion } from "motion/react";
import { Flame } from "lucide-react";
import { formatPercent } from "@/lib/risk";
import { CONFUSION_STYLE, confusionLevel } from "@/lib/topics";
import { spring } from "@/lib/motion";
import type { components } from "@/lib/api/schema";
import { SampleQuestions } from "./sample-questions";

type TopicStat = components["schemas"]["TopicStat"];

interface TopicCardProps {
  topic: TopicStat;
  /** Mayor número de preguntas entre los temas: la barra se mide contra él. */
  maxQuestions: number;
  index: number;
}

function Stats({ topic }: { topic: TopicStat }) {
  return (
    <p className="text-sm text-muted">
      <span className="font-semibold text-fg tabular-nums">{topic.question_count}</span> preguntas
      {topic.unique_students !== undefined && (
        <>
          {" "}
          de <span className="font-semibold text-fg tabular-nums">{topic.unique_students}</span> estudiantes
        </>
      )}
    </p>
  );
}

function ConfusionPill({ score }: { score: number }) {
  const style = CONFUSION_STYLE[confusionLevel(score)];
  const Icon = style.icon;
  return (
    <span className={`inline-flex shrink-0 items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${style.pill}`}>
      <Icon className="size-3.5" aria-hidden />
      {style.label} · {formatPercent(score)}
    </span>
  );
}

/** Tema con confusión grupal: ocupa el primer plano y se pinta con el amarillo de alerta. */
export function AlertTopicCard({ topic, maxQuestions, index }: TopicCardProps) {
  return (
    <motion.li
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ ...spring, delay: 0.15 + index * 0.08 }}
      className="relative overflow-hidden rounded-3xl border border-highlight/70 bg-highlight/12 p-5 shadow-card"
    >
      <div
        aria-hidden
        className="pointer-events-none absolute -right-10 -top-10 size-40 rounded-full bg-highlight/25 blur-2xl"
      />
      <div className="relative space-y-4">
        <div className="flex items-start gap-3">
          <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-highlight text-night-canvas">
            <Flame className="size-5" aria-hidden />
          </span>
          <div className="min-w-0 flex-1 space-y-1">
            <p className="inline-flex items-center gap-2 text-xs font-bold text-ink-caution">
              <span className="relative flex size-2" aria-hidden>
                <span className="absolute inline-flex size-full rounded-full bg-highlight opacity-75 motion-safe:animate-ping" />
                <span className="relative inline-flex size-2 rounded-full bg-highlight" />
              </span>
              Confusión grupal
            </p>
            <h3 className="text-xl leading-tight">{topic.topic}</h3>
            <Stats topic={topic} />
          </div>
        </div>

        <div className="space-y-1.5">
          <div className="flex items-center justify-between gap-3">
            <ConfusionPill score={topic.confusion_score} />
            <span className="text-xs text-muted">{Math.round((topic.question_count / maxQuestions) * 100)} % del tema más consultado</span>
          </div>
          <div className="h-2.5 overflow-hidden rounded-full bg-highlight/25" aria-hidden>
            <motion.div
              className="h-full origin-left rounded-full bg-highlight"
              style={{ width: "100%" }}
              initial={{ scaleX: 0 }}
              animate={{ scaleX: topic.confusion_score }}
              transition={{ ...spring, delay: 0.3 + index * 0.08 }}
            />
          </div>
        </div>

        <SampleQuestions questions={topic.sample_questions} />
      </div>
    </motion.li>
  );
}

/** Tema sin alerta: una fila con su volumen de preguntas. */
export function TopicRow({ topic, maxQuestions, index }: TopicCardProps) {
  return (
    <motion.li
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ ...spring, delay: 0.2 + index * 0.05 }}
      className="space-y-3 py-4 first:pt-1 last:pb-1"
    >
      <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-2">
        <div className="min-w-0 space-y-0.5">
          <h3 className="text-base leading-snug">{topic.topic}</h3>
          <Stats topic={topic} />
        </div>
        <ConfusionPill score={topic.confusion_score} />
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-line" aria-hidden>
        <motion.div
          className="h-full origin-left rounded-full bg-gradient-to-r from-primary to-glow"
          style={{ width: "100%" }}
          initial={{ scaleX: 0 }}
          animate={{ scaleX: topic.question_count / maxQuestions }}
          transition={{ ...spring, delay: 0.3 + index * 0.05 }}
        />
      </div>
      <SampleQuestions questions={topic.sample_questions} />
    </motion.li>
  );
}
