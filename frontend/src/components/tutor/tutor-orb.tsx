"use client";

import { motion } from "motion/react";

interface TutorOrbProps {
  /** Respira mientras el tutor está respondiendo. */
  active?: boolean;
  /** Tono calmado: respiración más lenta y brillo más suave (frustración detectada). */
  calm?: boolean;
  className?: string;
}

/** Orbe del tutor: el brillo de IA (#D9A5B3) sobre el acento primario. */
export function TutorOrb({ active = false, calm = false, className = "size-8" }: TutorOrbProps) {
  return (
    <span className={`relative inline-grid shrink-0 place-items-center ${className}`} aria-hidden>
      <motion.span
        className="absolute inset-0 rounded-full bg-glow blur-md"
        animate={
          active
            ? { opacity: calm ? [0.4, 0.65, 0.4] : [0.35, 0.8, 0.35], scale: calm ? [1, 1.25, 1] : [0.9, 1.35, 0.9] }
            : { opacity: calm ? 0.55 : 0.35, scale: 1 }
        }
        transition={active ? { duration: calm ? 5 : 2.4, repeat: Infinity, ease: "easeInOut" } : { duration: 0.4 }}
      />
      <span className="relative size-full rounded-full bg-gradient-to-br from-glow via-primary to-primary shadow-inner" />
    </span>
  );
}
