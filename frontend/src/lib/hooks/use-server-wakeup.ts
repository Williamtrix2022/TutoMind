"use client";

import { useEffect, useState } from "react";
import { API_BASE_URL } from "@/lib/api/client";

/**
 * Despierta el servidor mientras la persona escribe: un servidor gratuito se duerme tras unos
 * minutos sin uso y tarda hasta un minuto en responder la primera vez. Es silencioso si falla.
 */
export function useServerWakeUp(): void {
  useEffect(() => {
    if (!API_BASE_URL) return;
    const controller = new AbortController();
    // no-cors: solo nos importa que el servidor despierte, no leer la respuesta.
    void fetch(`${API_BASE_URL}/health`, { mode: "no-cors", signal: controller.signal }).catch(() => undefined);
    return () => controller.abort();
  }, []);
}

/** Pasa a `true` cuando `active` lleva más de `ms` encendido (p. ej. una petición que tarda). */
export function useAfterDelay(active: boolean, ms: number): boolean {
  const [late, setLate] = useState(false);
  useEffect(() => {
    if (!active) return;
    const id = window.setTimeout(() => setLate(true), ms);
    return () => {
      window.clearTimeout(id);
      setLate(false);
    };
  }, [active, ms]);
  return late;
}
