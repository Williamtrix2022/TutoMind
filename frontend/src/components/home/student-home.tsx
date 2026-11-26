"use client";

import { motion } from "motion/react";
import Link from "next/link";
import { ArrowUpRight, LifeBuoy } from "lucide-react";
import { Card } from "@/components/ui/card";
import { useApp } from "@/lib/providers/app-providers";
import { spring, tap } from "@/lib/motion";
import { FocusTimer } from "./focus-timer";
import { GuideSteps } from "./guide-steps";
import { TutorHero } from "./tutor-hero";

function HelpTile() {
  return (
    <motion.div whileTap={tap} whileHover={{ y: -3 }} transition={spring}>
      <Link href="/tutor" className="group block rounded-3xl">
        <Card className="flex items-center gap-4 transition-colors group-hover:border-primary">
          <span className="grid size-12 shrink-0 place-items-center rounded-2xl bg-glow/25 text-glow">
            <LifeBuoy className="size-6" aria-hidden />
          </span>
          <div className="min-w-0 flex-1 space-y-0.5">
            <h2 className="text-lg">¿Te trabaste?</h2>
            <p className="text-sm text-muted">
              Pide ayuda a tu docente desde el chat: recibe tu duda con todo el contexto de la conversación.
            </p>
          </div>
          <ArrowUpRight
            className="size-5 shrink-0 text-muted transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5"
            aria-hidden
          />
        </Card>
      </Link>
    </motion.div>
  );
}

export function StudentHome() {
  const { user } = useApp();

  return (
    <div className="space-y-6">
      <TutorHero name={user?.name} />
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <div className="space-y-6">
          <GuideSteps />
          <HelpTile />
        </div>
        <FocusTimer />
      </div>
    </div>
  );
}
