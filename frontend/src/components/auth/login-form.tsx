"use client";

import { motion } from "motion/react";
import { Eye, EyeOff, LoaderCircle, TriangleAlert } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useId, useState } from "react";
import type { FormEvent } from "react";
import { LogoMark } from "@/components/brand/logo-mark";
import { SegmentedControl } from "@/components/ui/segmented-control";
import { useLogin } from "@/lib/api/hooks/use-auth";
import { spring, tap } from "@/lib/motion";
import { useApp } from "@/lib/providers/app-providers";
import type { Role } from "@/lib/types";

const ROLES: { value: Role; label: string }[] = [
  { value: "student", label: "Estudiante" },
  { value: "teacher", label: "Docente" },
];

interface FieldErrors {
  email?: string;
  password?: string;
}

function validate(email: string, password: string): FieldErrors {
  const errors: FieldErrors = {};
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
    errors.email = "Escribe un correo válido, por ejemplo nombre@universidad.edu";
  }
  if (password.length < 8) errors.password = "La contraseña tiene al menos 8 caracteres.";
  return errors;
}

/** Solo rutas internas: evita redirecciones abiertas vía ?next=. */
function safeNext(): string {
  const next = new URLSearchParams(window.location.search).get("next");
  return next && next.startsWith("/") && !next.startsWith("//") ? next : "/";
}

const inputClass =
  "w-full rounded-2xl border bg-canvas px-4 py-3 text-base text-fg outline-none transition-colors placeholder:text-muted focus:border-primary";

export function LoginForm() {
  const router = useRouter();
  const { role: demoRole, authStatus, signIn } = useApp();
  const login = useLogin();
  const ids = { email: useId(), password: useId() };

  const [role, setRole] = useState<Role>(demoRole);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  // Si ya hay sesión (o acaba de iniciarse), entra a la app.
  useEffect(() => {
    if (authStatus === "authenticated") router.replace(safeNext());
  }, [authStatus, router]);

  const errors = submitted ? validate(email, password) : {};

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitted(true);
    if (Object.keys(validate(email, password)).length > 0 || login.isPending) return;
    login.mutate({ email: email.trim(), password, role }, { onSuccess: signIn });
  }

  return (
    <main className="grid min-h-dvh place-items-center px-4 py-10">
      <motion.div
        // Solo opacidad: un transform en el contenedor desalinea la píldora (layoutId) del selector.
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
        className="w-full max-w-md space-y-8"
      >
        <div className="flex flex-col items-center gap-5 text-center">
          <LogoMark size={72} />
          <div className="space-y-1">
            <h1 className="text-3xl">Entra a TutoMind</h1>
            <p className="text-sm text-muted">Tu tutor y el seguimiento de tus cursos, en un solo lugar.</p>
          </div>
        </div>

        <form
          onSubmit={onSubmit}
          noValidate
          className="space-y-5 rounded-3xl border border-line bg-card p-6 shadow-card"
        >
          <div className="space-y-2">
            <p className="text-sm font-semibold">Entrar como</p>
            <SegmentedControl label="Rol de la demo" value={role} onChange={setRole} options={ROLES} />
            <p className="text-xs text-muted">Modo demo. En producción tu rol lo define Moodle.</p>
          </div>

          <div className="space-y-2">
            <label htmlFor={ids.email} className="text-sm font-semibold">
              Correo
            </label>
            <input
              id={ids.email}
              type="email"
              inputMode="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              aria-invalid={Boolean(errors.email)}
              aria-describedby={errors.email ? `${ids.email}-error` : undefined}
              placeholder="nombre@universidad.edu"
              className={`${inputClass} ${errors.email ? "border-danger" : "border-line"}`}
            />
            {errors.email && (
              <p id={`${ids.email}-error`} className="text-sm text-danger">
                {errors.email}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <label htmlFor={ids.password} className="text-sm font-semibold">
              Contraseña
            </label>
            <div className="relative">
              <input
                id={ids.password}
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                aria-invalid={Boolean(errors.password)}
                aria-describedby={errors.password ? `${ids.password}-error` : undefined}
                className={`${inputClass} pr-12 ${errors.password ? "border-danger" : "border-line"}`}
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                className="absolute right-1.5 top-1/2 grid size-10 -translate-y-1/2 place-items-center rounded-xl text-muted hover:text-fg"
              >
                {showPassword ? <EyeOff className="size-4" aria-hidden /> : <Eye className="size-4" aria-hidden />}
              </button>
            </div>
            {errors.password && (
              <p id={`${ids.password}-error`} className="text-sm text-danger">
                {errors.password}
              </p>
            )}
          </div>

          {login.isError && (
            <p role="alert" className="flex items-start gap-2 text-sm text-danger">
              <TriangleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
              {login.error.message}
            </p>
          )}

          <motion.button
            type="submit"
            disabled={login.isPending}
            whileTap={tap}
            transition={spring}
            className="flex w-full items-center justify-center gap-2 rounded-2xl bg-primary px-4 py-3.5 text-base font-semibold text-on-primary disabled:opacity-70"
          >
            {login.isPending && <LoaderCircle className="size-4 animate-spin" aria-hidden />}
            {login.isPending ? "Entrando…" : "Entrar"}
          </motion.button>
        </form>
      </motion.div>
    </main>
  );
}
