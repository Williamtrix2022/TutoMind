"use client";

import { animate, useReducedMotion } from "motion/react";
import { useEffect, useRef } from "react";

interface AnimatedNumberProps {
  value: number;
  decimals?: number;
  className?: string;
}

/** Cuenta hasta `value` con un resorte; si el valor cambia, parte del número que se ve en pantalla. */
export function AnimatedNumber({ value, decimals = 0, className = "" }: AnimatedNumberProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const shown = useRef(0);
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    const write = (n: number) => {
      shown.current = n;
      node.textContent = n.toFixed(decimals);
    };
    if (reduceMotion) {
      write(value);
      return;
    }
    const controls = animate(shown.current, value, {
      type: "spring",
      stiffness: 140,
      damping: 22,
      onUpdate: write,
      onComplete: () => write(value),
    });
    return () => controls.stop();
  }, [value, decimals, reduceMotion]);

  return (
    <span ref={ref} className={`tabular-nums ${className}`}>
      {(0).toFixed(decimals)}
    </span>
  );
}
