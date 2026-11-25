"use client";

import { AnimatePresence, motion } from "motion/react";
import { Check, HeartHandshake } from "lucide-react";
import type { EscalationSignal, FrustrationSignal } from "@/lib/hooks/use-tutor-chat";
import { spring, tap } from "@/lib/motion";

interface SupportBannerProps {
  frustration: FrustrationSignal | null;
  escalation: EscalationSignal | null;
  disabled: boolean;
  onRequestHelp: () => void;
}

/** Aparece cuando el tutor detecta frustración o sugiere apoyo humano; confirma con el ticket. */
export function SupportBanner({ frustration, escalation, disabled, onRequestHelp }: SupportBannerProps) {
  const ticket = escalation?.ticket_id ?? null;
  const showOffer = !ticket && (frustration?.detected === true || escalation?.suggested === true);

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
          <span className="grid size-9 shrink-0 place-items-center rounded-2xl bg-success/20 text-success">
            <Check className="size-5" aria-hidden />
          </span>
          <div className="space-y-0.5">
            <p className="font-semibold">Tu docente ya fue avisado</p>
            <p className="text-sm text-muted">Solicitud {ticket} registrada.</p>
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
          className="mb-3 flex flex-wrap items-center gap-3 rounded-3xl border border-glow/50 bg-card p-4 shadow-card"
        >
          <span className="grid size-9 shrink-0 place-items-center rounded-2xl bg-glow/25 text-glow">
            <HeartHandshake className="size-5" aria-hidden />
          </span>
          <div className="min-w-0 flex-1 space-y-0.5">
            <p className="font-semibold">
              {frustration?.detected ? "Este tema está costando, y es normal" : "¿Quieres apoyo de tu docente?"}
            </p>
            <p className="text-sm text-muted">
              {frustration?.detected
                ? "Vamos más despacio. Si prefieres, tu docente puede ayudarte directamente."
                : "Tu docente puede revisar esta duda contigo."}
            </p>
          </div>
          <motion.button
            type="button"
            onClick={onRequestHelp}
            disabled={disabled}
            whileTap={tap}
            transition={spring}
            className="rounded-2xl bg-primary px-4 py-2.5 text-sm font-semibold text-on-primary disabled:opacity-50"
          >
            Pedir ayuda al docente
          </motion.button>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
