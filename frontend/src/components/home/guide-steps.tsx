"use client";

import { motion } from "motion/react";
import { Lightbulb, MessageCircleQuestion, PartyPopper } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Card } from "@/components/ui/card";
import { spring } from "@/lib/motion";

interface Step {
  icon: LucideIcon;
  title: string;
  text: string;
  tint: string;
}

const STEPS: Step[] = [
  {
    icon: MessageCircleQuestion,
    title: "Tú preguntas",
    text: "Cuéntale qué no te cuadra, con tus palabras.",
    tint: "bg-primary/20 text-primary",
  },
  {
    icon: Lightbulb,
    title: "Él te da pistas",
    text: "Te hace preguntas y te muestra el camino con tu material.",
    tint: "bg-highlight/30 text-ink-caution",
  },
  {
    icon: PartyPopper,
    title: "Tú lo resuelves",
    text: "El mérito es tuyo: llegas a la respuesta y la entiendes.",
    tint: "bg-success/20 text-ink-success",
  },
];

/** Cómo te acompaña el tutor: las tres fases de la guía socrática. */
export function GuideSteps() {
  return (
    <Card className="space-y-6">
      <div className="space-y-1">
        <h2 className="text-xl">Así te acompaña tu tutor</h2>
        <p className="text-sm text-muted">No te da la respuesta hecha: aprendes haciéndola.</p>
      </div>

      <ol className="relative grid gap-5 sm:grid-cols-3">
        {/* Hilo que une las fases; se dibuja al entrar en pantalla. */}
        <span className="pointer-events-none absolute left-[16.6%] right-[16.6%] top-6 hidden h-0.5 sm:block" aria-hidden>
          <motion.span
            className="block h-full origin-left rounded-full bg-gradient-to-r from-primary via-highlight to-success"
            initial={{ scaleX: 0 }}
            whileInView={{ scaleX: 1 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 1.1, ease: [0.22, 1, 0.36, 1] }}
          />
        </span>

        {STEPS.map(({ icon: Icon, title, text, tint }, index) => (
          <motion.li
            key={title}
            initial={{ opacity: 0, y: 14 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-40px" }}
            transition={{ ...spring, delay: index * 0.14 }}
            className="relative flex items-start gap-4 sm:flex-col sm:items-center sm:text-center"
          >
            <span className={`relative z-10 grid size-12 shrink-0 place-items-center rounded-2xl border-4 border-card ${tint}`}>
              <Icon className="size-5" aria-hidden />
            </span>
            <div className="space-y-1">
              <h3 className="text-base">{title}</h3>
              <p className="text-sm text-muted">{text}</p>
            </div>
          </motion.li>
        ))}
      </ol>
    </Card>
  );
}
