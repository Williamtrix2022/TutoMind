"use client";

import { motion } from "motion/react";
import { useId } from "react";
import { spring } from "@/lib/motion";

interface SegmentedOption<T extends string> {
  value: T;
  label: string;
}

interface SegmentedControlProps<T extends string> {
  value: T;
  onChange: (value: T) => void;
  options: SegmentedOption<T>[];
  /** Nombre accesible del grupo. */
  label: string;
  className?: string;
}

/** Control segmentado con píldora animada por resorte. */
export function SegmentedControl<T extends string>({
  value,
  onChange,
  options,
  label,
  className = "",
}: SegmentedControlProps<T>) {
  const pillId = useId();

  return (
    <div
      role="radiogroup"
      aria-label={label}
      className={`relative flex rounded-2xl border border-line bg-canvas p-1 ${className}`}
    >
      {options.map((option) => {
        const active = value === option.value;
        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => onChange(option.value)}
            className={`relative z-10 flex-1 rounded-xl px-2 py-2 text-xs font-semibold transition-colors sm:text-sm ${
              active ? "text-on-primary" : "text-muted hover:text-fg"
            }`}
          >
            {active && (
              <motion.span
                layoutId={pillId}
                transition={spring}
                className="absolute inset-0 -z-10 rounded-xl bg-primary"
              />
            )}
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
