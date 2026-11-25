import type { HTMLAttributes } from "react";

/** Tarjeta estilo Bento: rounded-3xl, borde sutil y sombra difusa. */
export function Card({ className = "", ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`rounded-3xl border border-line bg-card p-5 shadow-card ${className}`}
      {...props}
    />
  );
}
