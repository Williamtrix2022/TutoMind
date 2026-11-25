"use client";

import { AnimatePresence, motion } from "motion/react";
import { Moon, Sun } from "lucide-react";
import { useApp } from "@/lib/providers/app-providers";
import { spring, tap } from "@/lib/motion";

export function ThemeToggle() {
  const { theme, toggleTheme } = useApp();
  const isDark = theme === "dark";

  return (
    <motion.button
      type="button"
      onClick={toggleTheme}
      whileTap={tap}
      transition={spring}
      aria-label={isDark ? "Cambiar a modo día" : "Cambiar a modo noche"}
      className="relative grid size-11 shrink-0 place-items-center overflow-hidden rounded-2xl border border-line bg-card text-fg shadow-card"
    >
      <AnimatePresence mode="popLayout" initial={false}>
        <motion.span
          key={theme}
          initial={{ y: 18, rotate: -70, scale: 0.4, opacity: 0 }}
          animate={{ y: 0, rotate: 0, scale: 1, opacity: 1 }}
          exit={{ y: -18, rotate: 70, scale: 0.4, opacity: 0 }}
          transition={spring}
          className="grid place-items-center"
        >
          {isDark ? (
            <Moon className="size-5 text-primary" aria-hidden />
          ) : (
            <Sun className="size-5 text-warning" aria-hidden />
          )}
        </motion.span>
      </AnimatePresence>
    </motion.button>
  );
}
