"use client";

import { motion } from "motion/react";
import { FileText, LifeBuoy, TriangleAlert } from "lucide-react";
import type { ChatMessage, SourceCitation } from "@/lib/hooks/use-tutor-chat";
import { spring, tap } from "@/lib/motion";
import { Markdown } from "./markdown";
import { TutorOrb } from "./tutor-orb";

function SourceChip({ source }: { source: SourceCitation }) {
  const label = source.page ? `${source.title} · p. ${source.page}` : source.title;
  const className =
    "inline-flex max-w-full items-center gap-1.5 rounded-full border border-line bg-canvas px-2.5 py-1 text-xs font-medium text-muted";

  const content = (
    <>
      <FileText className="size-3 shrink-0 text-primary" aria-hidden />
      <span className="truncate">{label}</span>
    </>
  );

  return source.moodle_url ? (
    <a
      href={source.moodle_url}
      target="_blank"
      rel="noreferrer noopener"
      className={`${className} transition-colors hover:text-fg`}
    >
      {content}
    </a>
  ) : (
    <span className={className}>{content}</span>
  );
}

function Thinking() {
  return (
    <p className="flex items-center gap-2 text-sm text-muted" role="status">
      <span className="flex gap-1" aria-hidden>
        {[0, 1, 2].map((i) => (
          <motion.span
            key={i}
            className="size-1.5 rounded-full bg-primary"
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{ duration: 1.1, repeat: Infinity, delay: i * 0.18 }}
          />
        ))}
      </span>
      Pensando…
    </p>
  );
}

/** Respuestas muy cortas (saludos, avisos) no necesitan citar el material. */
const MIN_CHARS_FOR_SOURCES = 120;

/** Una pill por documento y página: sin repetidos y solo si la respuesta realmente se apoya en el curso. */
function relevantSources(message: ChatMessage): SourceCitation[] {
  if (message.streaming || message.error || message.content.length < MIN_CHARS_FOR_SOURCES) return [];
  const seen = new Set<string>();
  return message.sources.filter((source) => {
    const key = `${source.document_id}:${source.page ?? ""}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

interface MessageBubbleProps {
  message: ChatMessage;
  calm?: boolean;
  /** Ofrece, de forma sutil, avisar al docente (solo en la última respuesta). */
  onRequestHelp?: () => void;
}

export function MessageBubble({ message, calm = false, onRequestHelp }: MessageBubbleProps) {
  if (message.role === "user") {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={spring}
        className="flex justify-end"
      >
        <p className="max-w-[85%] whitespace-pre-wrap break-words rounded-3xl rounded-br-lg bg-primary px-4 py-3 text-[0.9375rem] font-medium leading-relaxed text-on-primary">
          {message.content}
        </p>
      </motion.div>
    );
  }

  const sources = relevantSources(message);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={spring}
      className="flex items-start gap-3"
    >
      <TutorOrb active={message.streaming} calm={calm} className="mt-1 size-8" />
      <div className="min-w-0 flex-1 space-y-3">
        <div
          className={`rounded-3xl rounded-tl-lg border bg-card px-5 py-4 leading-relaxed shadow-card transition-colors duration-700 ${
            calm ? "border-glow/50" : "border-line"
          }`}
        >
          {message.content ? <Markdown content={message.content} /> : message.streaming ? <Thinking /> : null}

          {message.error && (
            <p role="alert" className="mt-3 flex items-start gap-2 text-sm text-ink-danger">
              <TriangleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
              {message.error}
            </p>
          )}
        </div>

        {sources.length > 0 && (
          <div className="flex flex-wrap gap-1.5 px-1" aria-label="Fuentes del curso">
            {sources.map((source) => (
              <SourceChip key={`${source.document_id}:${source.page ?? ""}`} source={source} />
            ))}
          </div>
        )}

        {onRequestHelp && !message.streaming && !message.error && (
          <motion.button
            type="button"
            onClick={onRequestHelp}
            whileTap={tap}
            transition={spring}
            className="ml-1 inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium text-muted transition-colors hover:bg-card hover:text-fg"
          >
            <LifeBuoy className="size-3.5" aria-hidden />
            ¿Sigue sin quedar claro? Pedir ayuda al profesor
          </motion.button>
        )}
      </div>
    </motion.div>
  );
}
