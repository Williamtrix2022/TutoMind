"use client";

import { motion } from "motion/react";
import { LifeBuoy, RotateCcw } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { SegmentedControl } from "@/components/ui/segmented-control";
import { DEMO_COURSE_ID } from "@/lib/config";
import { useTutorChat } from "@/lib/hooks/use-tutor-chat";
import { TUTOR_SUGGESTIONS } from "@/lib/tutor-suggestions";
import { spring, tap } from "@/lib/motion";
import type { StudentLevel } from "@/lib/types";
import { ChatComposer } from "./chat-composer";
import { MessageBubble } from "./message-bubble";
import { SupportBanner } from "./support-banner";
import { TutorOrb } from "./tutor-orb";

const LEVELS: { value: StudentLevel; label: string }[] = [
  { value: "basic", label: "Básico" },
  { value: "intermediate", label: "Intermedio" },
  { value: "advanced", label: "Avanzado" },
];

export function TutorChat({ initialQuestion }: { initialQuestion?: string }) {
  const [level, setLevel] = useState<StudentLevel>("basic");
  const { messages, isStreaming, frustration, escalation, send, stop, requestHelp, reset } = useTutorChat({
    courseId: DEMO_COURSE_ID,
    level,
  });
  const calm = frustration?.detected === true;
  const helpRequested = Boolean(escalation?.ticket_id);

  // Sigue la respuesta solo si la persona no se ha desplazado hacia arriba.
  const stickToBottom = useRef(true);

  useEffect(() => {
    const onScroll = () => {
      const distance = document.documentElement.scrollHeight - window.scrollY - window.innerHeight;
      stickToBottom.current = distance < 160;
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    // Hasta el final real de la página: así el compositor "pegajoso" no tapa el último mensaje.
    if (stickToBottom.current) window.scrollTo({ top: document.documentElement.scrollHeight });
  }, [messages, frustration, escalation]);

  const isEmpty = messages.length === 0;

  // Pregunta que llega desde el inicio (?q=...): se envía una sola vez y se limpia la URL.
  const sentInitial = useRef(false);
  useEffect(() => {
    if (!initialQuestion || sentInitial.current) return;
    sentInitial.current = true;
    window.history.replaceState(null, "", "/tutor");
    void send(initialQuestion);
  }, [initialQuestion, send]);

  return (
    <div className="flex min-h-[calc(100dvh-9rem)] flex-col md:min-h-[calc(100dvh-4rem)]">
      <header className="flex flex-wrap items-end justify-between gap-4 pb-6">
        <div className="space-y-1">
          <h1 className="text-3xl md:text-4xl">Tutor</h1>
          <p className="max-w-prose text-sm text-muted">
            Te guío paso a paso con el material de tu curso, sin darte la respuesta hecha.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <SegmentedControl
            label="Nivel de explicación"
            value={level}
            onChange={setLevel}
            options={LEVELS}
            className="w-full min-w-64 sm:w-auto"
          />
          {!isEmpty && !helpRequested && (
            <motion.button
              type="button"
              onClick={() => void requestHelp()}
              disabled={isStreaming}
              whileTap={tap}
              transition={spring}
              aria-label="Pedir ayuda al docente"
              title="Pedir ayuda al docente"
              className="grid size-11 shrink-0 place-items-center rounded-2xl border border-line bg-card text-muted shadow-card hover:text-fg disabled:opacity-50"
            >
              <LifeBuoy className="size-4" aria-hidden />
            </motion.button>
          )}
          {!isEmpty && (
            <motion.button
              type="button"
              onClick={reset}
              whileTap={tap}
              transition={spring}
              aria-label="Nueva conversación"
              className="grid size-11 shrink-0 place-items-center rounded-2xl border border-line bg-card text-muted shadow-card hover:text-fg"
            >
              <RotateCcw className="size-4" aria-hidden />
            </motion.button>
          )}
        </div>
      </header>

      <div className="flex-1">
        {isEmpty ? (
          <div className="flex flex-col items-center gap-6 py-10 text-center">
            <TutorOrb active className="size-16" />
            <div className="space-y-1">
              <h2 className="text-xl">¿Qué quieres repasar?</h2>
              <p className="text-sm text-muted">Escribe una duda o empieza con una de estas:</p>
            </div>
            <ul className="flex flex-wrap justify-center gap-2">
              {TUTOR_SUGGESTIONS.map((suggestion) => (
                <li key={suggestion}>
                  <motion.button
                    type="button"
                    onClick={() => void send(suggestion)}
                    whileTap={tap}
                    transition={spring}
                    className="rounded-2xl border border-line bg-card px-4 py-2.5 text-sm font-medium shadow-card transition-colors hover:border-primary"
                  >
                    {suggestion}
                  </motion.button>
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <div role="log" aria-live="polite" aria-label="Conversación con el tutor" className="space-y-5">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} calm={calm} />
            ))}
          </div>
        )}
      </div>

      {/* Borde de scroll: el contenido se desvanece bajo el compositor en lugar de cortarse. */}
      <div className="sticky bottom-[calc(6rem+env(safe-area-inset-bottom))] z-30 mt-6 bg-gradient-to-t from-canvas from-75% to-transparent pt-8 md:bottom-0 md:pb-4">
        <SupportBanner
          frustration={frustration}
          escalation={escalation}
          disabled={isStreaming}
          onRequestHelp={() => void requestHelp()}
        />
        <ChatComposer isStreaming={isStreaming} onSend={(text) => void send(text)} onStop={stop} />
      </div>
    </div>
  );
}
