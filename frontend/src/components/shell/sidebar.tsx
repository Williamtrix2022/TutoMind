"use client";

import { motion } from "motion/react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LogoutButton } from "@/components/ui/logout-button";
import { RoleSwitcher } from "@/components/ui/role-switcher";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { useApp } from "@/lib/providers/app-providers";
import { spring } from "@/lib/motion";
import { Logo } from "./logo";
import { NAV_BY_ROLE } from "./nav-items";

/** Navegación de escritorio. */
export function Sidebar() {
  const { role, user } = useApp();
  const pathname = usePathname();

  return (
    <aside className="fixed inset-y-4 left-4 hidden w-64 flex-col justify-between rounded-3xl border border-line bg-card p-5 shadow-card md:flex">
      <div className="space-y-8">
        <Logo />
        <nav aria-label="Principal" className="flex flex-col gap-1">
          {NAV_BY_ROLE[role].map(({ href, label, icon: Icon }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                aria-current={active ? "page" : undefined}
                className={`relative flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-semibold transition-colors ${
                  active ? "text-fg" : "text-muted hover:text-fg"
                }`}
              >
                {active && (
                  <motion.span
                    layoutId="sidebar-active"
                    transition={spring}
                    className="absolute inset-0 rounded-2xl bg-primary/20"
                  />
                )}
                <Icon className={`relative size-5 ${active ? "text-primary" : ""}`} aria-hidden />
                <span className="relative">{label}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="space-y-3">
        <p className="px-1 text-xs font-medium text-muted">Rol de la demo</p>
        <RoleSwitcher />
        <div className="flex items-center justify-between px-1 pt-1">
          <span className="text-sm font-medium text-muted">Apariencia</span>
          <ThemeToggle />
        </div>
        {user && (
          <div className="flex items-center justify-between gap-2 rounded-2xl border border-line bg-canvas p-2 pl-4">
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold">{user.name}</p>
              <p className="truncate text-xs text-muted">{user.email}</p>
            </div>
            <LogoutButton className="size-10" />
          </div>
        )}
      </div>
    </aside>
  );
}
