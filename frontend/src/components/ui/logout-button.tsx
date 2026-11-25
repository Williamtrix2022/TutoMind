"use client";

import { motion } from "motion/react";
import { LogOut } from "lucide-react";
import { useApp } from "@/lib/providers/app-providers";
import { spring, tap } from "@/lib/motion";

export function LogoutButton({ className = "size-11" }: { className?: string }) {
  const { signOut } = useApp();

  return (
    <motion.button
      type="button"
      onClick={signOut}
      whileTap={tap}
      transition={spring}
      aria-label="Cerrar sesión"
      title="Cerrar sesión"
      className={`grid shrink-0 place-items-center rounded-2xl border border-line bg-card text-muted shadow-card hover:text-fg ${className}`}
    >
      <LogOut className="size-4" aria-hidden />
    </motion.button>
  );
}
