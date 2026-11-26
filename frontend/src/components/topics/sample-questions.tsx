"use client";

import { AnimatePresence, motion } from "motion/react";
import { ChevronDown, MessageCircleQuestion } from "lucide-react";
import { useId, useState } from "react";
import { spring, tap } from "@/lib/motion";

/** Preguntas reales de los estudiantes sobre el tema, en un desplegable. */
export function SampleQuestions({ questions }: { questions: string[] | undefined }) {
  const [open, setOpen] = useState(false);
  const panelId = useId();

  if (!questions || questions.length === 0) return null;

  return (
    <div>
      <motion.button
        type="button"
        whileTap={tap}
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((value) => !value)}
        className="inline-flex items-center gap-1.5 rounded-xl py-1.5 pr-2 text-sm font-semibold text-primary transition-colors hover:text-fg"
      >
        <MessageCircleQuestion className="size-4" aria-hidden />
        {open ? "Ocultar preguntas" : `Ver ${questions.length === 1 ? "la pregunta" : `${questions.length} preguntas`} de ejemplo`}
        <motion.span animate={{ rotate: open ? 180 : 0 }} transition={spring} className="grid">
          <ChevronDown className="size-4" aria-hidden />
        </motion.span>
      </motion.button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.ul
            id={panelId}
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ ...spring, opacity: { duration: 0.15 } }}
            className="overflow-hidden"
          >
            {questions.map((question) => (
              <li key={question} className="mt-2 rounded-2xl border-l-4 border-glow bg-canvas/70 px-4 py-3 text-sm leading-relaxed">
                «{question}»
              </li>
            ))}
          </motion.ul>
        )}
      </AnimatePresence>
    </div>
  );
}
