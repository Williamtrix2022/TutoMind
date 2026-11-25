"use client";

import { motion } from "motion/react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useApp } from "@/lib/providers/app-providers";
import { spring, tap } from "@/lib/motion";
import { NAV_BY_ROLE } from "./nav-items";

/** Barra flotante inferior tipo iOS (móvil). Material translúcido sobre el contenido. */
export function BottomBar() {
  const { role } = useApp();
  const pathname = usePathname();

  return (
    <nav
      aria-label="Principal"
      className="material fixed inset-x-4 bottom-[max(1rem,env(safe-area-inset-bottom))] z-40 mx-auto flex max-w-md items-center justify-around rounded-3xl border border-line bg-card/85 p-2 shadow-card backdrop-blur-xl backdrop-saturate-150 md:hidden"
    >
      {NAV_BY_ROLE[role].map(({ href, label, icon: Icon }) => {
        const active = pathname === href;
        return (
          <motion.div key={href} whileTap={tap} transition={spring} className="flex-1">
            <Link
              href={href}
              aria-current={active ? "page" : undefined}
              className={`relative flex flex-col items-center gap-1 rounded-2xl px-2 py-2 text-[11px] font-semibold ${
                active ? "text-fg" : "text-muted"
              }`}
            >
              {active && (
                <motion.span
                  layoutId="bottom-active"
                  transition={spring}
                  className="absolute inset-0 rounded-2xl bg-primary/20"
                />
              )}
              <Icon className={`relative size-6 ${active ? "text-primary" : ""}`} aria-hidden />
              <span className="relative">{label}</span>
            </Link>
          </motion.div>
        );
      })}
    </nav>
  );
}
