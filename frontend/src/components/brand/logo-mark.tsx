"use client";

import { motion } from "motion/react";
import { useId } from "react";

interface LogoMarkProps {
  size?: number;
  /** Dibuja la T al montar y pulsa el nodo central al pasar el cursor. */
  animated?: boolean;
  className?: string;
}

const INK = "#03174c";

/**
 * Marca de TutoMind: una «T» hecha de red neuronal.
 * El arco es el aula que se abre sobre el estudiante, el tronco es el tutor que lo guía
 * y los nodos son las ideas que se conectan. El nodo central es la chispa de la IA.
 */
export function LogoMark({ size = 40, animated = true, className = "" }: LogoMarkProps) {
  const gradientId = useId();
  const draw = (delay: number) =>
    animated
      ? {
          initial: { pathLength: 0, opacity: 0 },
          animate: { pathLength: 1, opacity: 1 },
          transition: { duration: 0.7, delay, ease: [0.22, 1, 0.36, 1] as const },
        }
      : {};
  const pop = (delay: number) =>
    animated
      ? {
          initial: { scale: 0, opacity: 0 },
          animate: { scale: 1, opacity: 1 },
          transition: { type: "spring" as const, stiffness: 350, damping: 22, delay },
        }
      : {};

  return (
    <motion.svg
      viewBox="0 0 48 48"
      width={size}
      height={size}
      role="img"
      aria-label="TutoMind"
      className={`shrink-0 ${className}`}
      initial="rest"
      whileHover={animated ? "hover" : undefined}
    >
      <defs>
        <linearGradient id={gradientId} x1="4" y1="2" x2="44" y2="46" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#8e97fd" />
          <stop offset="1" stopColor="#d9a5b3" />
        </linearGradient>
      </defs>

      <rect x="1" y="1" width="46" height="46" rx="14" fill={`url(#${gradientId})`} />
      {/* Reflejo superior: la luz que da volumen a la pieza. */}
      <path d="M15 1h18a14 14 0 0 1 14 14v1C36 8 12 8 1 16v-1A14 14 0 0 1 15 1Z" fill="#fff" opacity="0.16" />

      <g fill="none" stroke={INK} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
        <motion.path d="M12 18.5Q24 8 36 18.5" {...draw(0.1)} />
        <motion.path d="M24 13.2V35" {...draw(0.45)} />
      </g>

      <g fill={INK}>
        <motion.circle cx="12" cy="18.5" r="3" style={{ transformOrigin: "12px 18.5px" }} {...pop(0.2)} />
        <motion.circle cx="36" cy="18.5" r="3" style={{ transformOrigin: "36px 18.5px" }} {...pop(0.3)} />
        <motion.circle cx="24" cy="36" r="3.4" style={{ transformOrigin: "24px 36px" }} {...pop(0.75)} />
      </g>

      {/* Chispa: el nodo de la IA, que late al pasar el cursor. */}
      <motion.circle
        cx="24"
        cy="13.2"
        r="6"
        fill="#fff"
        opacity="0.5"
        style={{ transformOrigin: "24px 13.2px" }}
        variants={{ rest: { scale: 0.6, opacity: 0 }, hover: { scale: [0.8, 1.35, 1], opacity: [0.7, 0.2, 0.5] } }}
        transition={{ duration: 0.8 }}
      />
      <motion.circle cx="24" cy="13.2" r="4" fill="#ffcf86" stroke={INK} strokeWidth="2.2" style={{ transformOrigin: "24px 13.2px" }} {...pop(0.55)} />
    </motion.svg>
  );
}
