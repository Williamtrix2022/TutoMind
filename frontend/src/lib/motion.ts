import type { Transition } from "motion/react";

/** Resorte estándar de TutoMind (CLAUDE.md). */
export const spring: Transition = { type: "spring", stiffness: 350, damping: 28 };

/** Feedback táctil inmediato en botones. */
export const tap = { scale: 0.97 } as const;
