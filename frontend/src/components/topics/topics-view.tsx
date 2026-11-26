"use client";

import { motion } from "motion/react";
import { CircleAlert, MessageSquareDashed } from "lucide-react";
import { Card } from "@/components/ui/card";
import { useCourseTopics } from "@/lib/api/hooks/use-analytics";
import { DEMO_COURSE_ID } from "@/lib/config";
import { tap } from "@/lib/motion";
import { classConfusion, formatPeriod } from "@/lib/topics";
import { ClassThermometer } from "./class-thermometer";
import { AlertTopicCard, TopicRow } from "./topic-card";

function Skeleton() {
  return (
    <div className="space-y-6" aria-busy aria-label="Cargando temas">
      <div className="h-72 animate-pulse rounded-3xl bg-line" />
      <div className="h-44 animate-pulse rounded-3xl bg-line" />
      <div className="h-64 animate-pulse rounded-3xl bg-line" />
    </div>
  );
}

export function TopicsView() {
  const topics = useCourseTopics(DEMO_COURSE_ID);
  const data = topics.data;

  const ranked = data ? [...data.topics].sort((a, b) => b.question_count - a.question_count) : [];
  const alerts = ranked.filter((t) => t.confusion_alert);
  const rest = ranked.filter((t) => !t.confusion_alert);
  const maxQuestions = Math.max(1, ...ranked.map((t) => t.question_count));
  const totalQuestions = ranked.reduce((sum, t) => sum + t.question_count, 0);

  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-3xl md:text-4xl">Temas consultados</h1>
        <p className="max-w-prose text-sm text-muted">
          Lo que tus estudiantes le preguntan al tutor, y dónde el grupo se está confundiendo.
        </p>
      </header>

      {topics.isPending && <Skeleton />}

      {topics.isError && (
        <div role="alert" className="flex flex-wrap items-center gap-3 rounded-3xl border border-danger/40 bg-card p-5 shadow-card">
          <CircleAlert className="size-5 shrink-0 text-ink-danger" aria-hidden />
          <p className="min-w-0 flex-1 text-sm">No pudimos cargar los temas. {topics.error.message}</p>
          <motion.button
            type="button"
            whileTap={tap}
            onClick={() => void topics.refetch()}
            className="rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-on-primary"
          >
            Reintentar
          </motion.button>
        </div>
      )}

      {data && ranked.length === 0 && (
        <Card className="flex flex-col items-center gap-3 px-6 py-14 text-center">
          <span className="grid size-12 place-items-center rounded-2xl bg-primary/15 text-primary">
            <MessageSquareDashed className="size-6" aria-hidden />
          </span>
          <p className="font-semibold">Todavía no hay preguntas en este periodo</p>
          <p className="max-w-sm text-sm text-muted">Cuando tus estudiantes usen el tutor, aquí verás los temas que más consultan.</p>
        </Card>
      )}

      {data && ranked.length > 0 && (
        <>
          <ClassThermometer
            score={classConfusion(ranked)}
            questions={totalQuestions}
            topics={ranked.length}
            alerts={alerts.length}
            period={formatPeriod(data.period_start, data.period_end)}
          />

          {alerts.length > 0 && (
            <section aria-labelledby="alerts-title" className="space-y-3">
              <h2 id="alerts-title" className="text-xl">
                Necesitan atención
              </h2>
              <ul className="grid gap-4 lg:grid-cols-2">
                {alerts.map((topic, index) => (
                  <AlertTopicCard key={topic.topic} topic={topic} maxQuestions={maxQuestions} index={index} />
                ))}
              </ul>
            </section>
          )}

          {rest.length > 0 && (
            <section aria-labelledby="rest-title">
              <Card className="space-y-2">
                <h2 id="rest-title" className="text-xl">
                  {alerts.length > 0 ? "Otros temas" : "Temas más preguntados"}
                </h2>
                <ul className="divide-y divide-line">
                  {rest.map((topic, index) => (
                    <TopicRow key={topic.topic} topic={topic} maxQuestions={maxQuestions} index={index} />
                  ))}
                </ul>
              </Card>
            </section>
          )}
        </>
      )}
    </div>
  );
}
