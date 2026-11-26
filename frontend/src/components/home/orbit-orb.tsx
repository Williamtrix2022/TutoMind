"use client";

import { motion } from "motion/react";
import { TutorOrb } from "@/components/tutor/tutor-orb";

const RINGS = [
  { size: "100%", duration: 22, color: "bg-primary", dot: "size-3", reverse: false },
  { size: "74%", duration: 15, color: "bg-glow", dot: "size-2.5", reverse: true },
  { size: "50%", duration: 10, color: "bg-highlight", dot: "size-2", reverse: false },
];

/** El orbe del tutor con tres órbitas: ideas que giran alrededor de lo que estás aprendiendo. */
export function OrbitOrb({ className = "size-56" }: { className?: string }) {
  return (
    <div className={`relative grid place-items-center ${className}`} aria-hidden>
      {RINGS.map(({ size, duration, color, dot, reverse }) => (
        <div key={size} className="absolute rounded-full border border-dashed border-primary/30" style={{ width: size, height: size }}>
          <motion.div
            className="absolute inset-0"
            animate={{ rotate: reverse ? -360 : 360 }}
            transition={{ duration, repeat: Infinity, ease: "linear" }}
          >
            <span className={`absolute left-1/2 top-0 -translate-x-1/2 -translate-y-1/2 rounded-full shadow-card ${color} ${dot}`} />
          </motion.div>
        </div>
      ))}
      <TutorOrb active className="size-1/4" />
    </div>
  );
}
