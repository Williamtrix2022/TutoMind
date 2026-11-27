"use client";

import { AnimatePresence, motion } from "motion/react";
import { Check, HeartHandshake } from "lucide-react";
import { useState } from "react";
import type { EscalationSignal } from "@/lib/hooks/use-tutor-chat";
import { spring, tap } from "@/lib/motion";

interface SupportBannerProps {
  escalation: EscalationSignal | null;
  disabled: boolean;
  onRequestHelp: () => void;
}

/**
 * El docente es la última instancia: la oferta aparece solo cuando el servidor la sugiere (el
 * estudiante sigue sin entender tras varias explicaciones, o su frustración persiste). Nada se envía
 * hasta que acepta; entonces el servidor registra la solicitud y devuelve su número.
 */
export function SupportBanner({ escalation, disabled, onRequestHelp }: SupportBannerProps) {
  const [dismissed, setDismissed] = useState<EscalationSignal | null>(null);
  const ticket = escalation?.ticket_id ?? null;
  const showOffer = !ticket && escalation?.suggested === true && escalation !== dismissed;

  return (
    <AnimatePresence initial={false} mode="popLayout">
      {ticket ? (
        <motion.div
          key="confirmed"
          role="status"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 12 }}
          transition={spring}
          className="mb-3 flex items-start gap-3 rounded-3xl border border-success/40 bg-card p-4 shadow-card"
        >
          <span className="grid size-9 shrink-0 place-items-center rounded-2xl bg-success/20 text-ink-success">
            <Check className="size-5" aria-hidden />
          </span>
          <div className="space-y-0.5">
            <p className="font-semibold">Listo, tu docente ya tiene tu consulta</p>
            <p className="text-sm text-muted">
              Solicitud {ticket} registrada: la verá en su panel con nuestra conversación.
            </p>
          </div>
        </motion.div>
      ) : showOffer ? (
        <motion.div
          key="offer"
          role="status"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 12 }}
          transition={spring}
          className="mb-3 flex flex-col gap-3 rounded-3xl border border-glow/50 bg-card p-4 shadow-card sm:flex-row sm:items-center"
        >
          <div className="flex min-w-0 flex-1 items-start gap-3">
            <span className="grid size-9 shrink-0 place-items-center rounded-2xl bg-glow/25 text-glow">
              <HeartHandshake className="size-5" aria-hidden />
            </span>
            <div className="min-w-0 space-y-0.5">
              <p className="font-semibold">Este tema se está complicando, y no pasa nada</p>
              <p className="text-sm text-muted">
                ¿Quieres que le envíe esta consulta y nuestro historial al profesor para que lo revise en su panel?
              </p>
            </div>
          </div>
          <div className="flex w-full gap-2 sm:w-auto">
            <motion.button
              type="button"
              onClick={() => setDismissed(escalation)}
              whileTap={tap}
              transition={spring}
              className="flex-1 rounded-2xl border border-line px-4 py-2.5 text-sm font-semibold text-muted hover:text-fg sm:flex-none"
            >
              Ahora no
            </motion.button>
            <motion.button
              type="button"
              onClick={onRequestHelp}
              disabled={disabled}
              whileTap={tap}
              transition={spring}
              className="flex-1 rounded-2xl bg-primary px-4 py-2.5 text-sm font-semibold text-on-primary disabled:opacity-50 sm:flex-none"
            >
              Sí, enviarla al profesor
            </motion.button>
          </div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
