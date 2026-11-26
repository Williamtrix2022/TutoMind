"use client";

import { motion } from "motion/react";
import Link from "next/link";
import { Activity, FileUp, MessagesSquare, Thermometer } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Card } from "@/components/ui/card";
import { useApp } from "@/lib/providers/app-providers";
import { spring, tap } from "@/lib/motion";

interface Shortcut {
  href: string;
  title: string;
  text: string;
  icon: LucideIcon;
  tint: string;
}

const STUDENT: Shortcut[] = [
  {
    href: "/tutor",
    title: "Pregunta a tu tutor",
    text: "Resuelve dudas con ayuda paso a paso, basada en el material de tu curso.",
    icon: MessagesSquare,
    tint: "bg-primary/20 text-primary",
  },
];

const TEACHER: Shortcut[] = [
  {
    href: "/riesgo",
    title: "Riesgo académico",
    text: "Revisa quién necesita apoyo y por qué.",
    icon: Activity,
    tint: "bg-warning/20 text-warning",
  },
  {
    href: "/temas",
    title: "Temas consultados",
    text: "Detecta dónde el grupo se está confundiendo.",
    icon: Thermometer,
    tint: "bg-highlight/25 text-highlight",
  },
  {
    href: "/documentos",
    title: "Documentos del curso",
    text: "Sube PDF, DOCX o PPTX para el tutor.",
    icon: FileUp,
    tint: "bg-success/20 text-success",
  },
];

export function HomeView() {
  const { role } = useApp();
  const items = role === "student" ? STUDENT : TEACHER;

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <h1 className="text-4xl md:text-5xl">
          {role === "student" ? "¿Qué repasamos hoy?" : "Tu aula, de un vistazo"}
        </h1>
        <p className="max-w-prose text-muted">
          {role === "student"
            ? "Tu tutor conoce el material de tus cursos y te guía sin darte la respuesta hecha."
            : "Mira el riesgo de cada estudiante, entiende sus causas y actúa a tiempo."}
        </p>
      </header>

      <div className="grid gap-4 md:grid-cols-3">
        {items.map(({ href, title, text, icon: Icon, tint }, index) => (
          <motion.div
            key={href}
            whileTap={tap}
            transition={spring}
            className={items.length === 1 ? "md:col-span-2" : undefined}
          >
            <Link href={href} className="block h-full rounded-3xl">
              <Card className={`flex h-full flex-col gap-4 ${index === 0 && items.length > 1 ? "md:p-6" : ""}`}>
                <span className={`grid size-12 place-items-center rounded-2xl ${tint}`}>
                  <Icon className="size-6" aria-hidden />
                </span>
                <div className="space-y-1">
                  <h2 className="text-lg">{title}</h2>
                  <p className="text-sm text-muted">{text}</p>
                </div>
              </Card>
            </Link>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
