"use client";

import type { ReactNode } from "react";
import { RoleSwitcher } from "@/components/ui/role-switcher";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { BottomBar } from "./bottom-bar";
import { Logo } from "./logo";
import { Sidebar } from "./sidebar";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-dvh">
      <Sidebar />

      {/* Cabecera móvil */}
      <header className="flex items-center justify-between gap-3 px-4 pt-[max(1rem,env(safe-area-inset-top))] md:hidden">
        <Logo />
        <div className="flex items-center gap-2">
          <RoleSwitcher className="w-44 sm:w-52" />
          <ThemeToggle />
        </div>
      </header>

      <main className="px-4 pb-32 pt-6 md:py-8 md:pl-[19rem] md:pr-8">
        <div className="mx-auto max-w-5xl">{children}</div>
      </main>

      <BottomBar />
    </div>
  );
}
