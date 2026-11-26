"use client";

import { motion } from "motion/react";
import Link from "next/link";
import { ArrowRight, Sparkles } from "lucide-react";
import { Card } from "@/components/ui/card";
import { spring, tap } from "@/lib/motion";
import { TUTOR_SUGGESTIONS } from "@/lib/tutor-suggestions";
import { firstName, useGreeting } from "./greeting";
import { OrbitOrb } from "./orbit-orb";

export function TutorHero({ name }: { name: string | undefined }) {
  const greeting = useGreeting();
  const who = firstName(name);

  return (
    <Card className="relative overflow-hidden p-6 sm:p-9">
      <div
        aria-hidden
        className="pointer-events-none absolute -right-16 -top-20 size-96 rounded-full opacity-70 blur-3xl"
        style={{ background: "radial-gradient(closest-side, color-mix(in srgb, var(--color-primary) 38%, transparent), transparent)" }}
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -bottom-32 left-10 size-72 rounded-full opacity-40 blur-3xl"
        style={{ background: "radial-gradient(closest-side, color-mix(in srgb, var(--color-glow) 40%, transparent), transparent)" }}
      />

      <div className="relative grid items-center gap-8 md:grid-cols-[minmax(0,1fr)_15rem]">
        <div className="space-y-6">
          <div className="space-y-3">
            <p className="inline-flex items-center gap-2 rounded-full bg-primary/15 px-3 py-1 text-sm font-semibold text-primary">
              <Sparkles className="size-4" aria-hidden />
              {greeting}
              {who && `, ${who}`}
            </p>
            <h1 className="text-4xl leading-[1.05] md:text-6xl">¿Qué repasamos hoy?</h1>
            <p className="max-w-md text-muted">
              Tu tutor conoce el material de tus cursos y te guía paso a paso, sin darte la respuesta hecha.
            </p>
          </div>

          <motion.div whileTap={tap} transition={spring} className="inline-block">
            <Link
              href="/tutor"
              className="group inline-flex items-center gap-2 rounded-2xl bg-primary px-6 py-3.5 font-semibold text-on-primary shadow-card transition-shadow hover:shadow-[0_10px_30px_-8px_var(--color-primary)]"
            >
              Hablar con tu tutor
              <ArrowRight className="size-4 transition-transform group-hover:translate-x-1" aria-hidden />
            </Link>
          </motion.div>

          <div className="space-y-2.5">
            <p className="text-sm font-semibold">O empieza con una de estas</p>
            <ul className="flex flex-wrap gap-2">
              {TUTOR_SUGGESTIONS.map((question, index) => (
                <motion.li
                  key={question}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ ...spring, delay: 0.35 + index * 0.07 }}
                >
                  <motion.div whileTap={tap} whileHover={{ y: -2 }} transition={spring}>
                    <Link
                      href={`/tutor?q=${encodeURIComponent(question)}`}
                      className="block rounded-2xl border border-line bg-canvas/70 px-3.5 py-2 text-sm transition-colors hover:border-primary"
                    >
                      {question}
                    </Link>
                  </motion.div>
                </motion.li>
              ))}
            </ul>
          </div>
        </div>

        <OrbitOrb className="mx-auto size-48 md:size-60" />
      </div>
    </Card>
  );
}
