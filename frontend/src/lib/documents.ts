import { CircleAlert, CircleCheck, Clock, LoaderCircle } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { components } from "@/lib/api/schema";

type DocumentStatus = components["schemas"]["DocumentStatus"];
type DocumentMime = components["schemas"]["CourseDocument"]["mime_type"];

export const MAX_SIZE_BYTES = 20 * 1024 * 1024;
export const MAX_SIZE_LABEL = "20 MB";

export const ALLOWED_TYPES: { mime: DocumentMime; ext: string; label: "PDF" | "DOCX" | "PPTX" }[] = [
  { mime: "application/pdf", ext: ".pdf", label: "PDF" },
  {
    mime: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ext: ".docx",
    label: "DOCX",
  },
  {
    mime: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ext: ".pptx",
    label: "PPTX",
  },
];

/** Valor del atributo `accept` del input de archivos. */
export const ACCEPT = ALLOWED_TYPES.flatMap((t) => [t.ext, t.mime]).join(",");

/** Tipo permitido por MIME o por extensión (algunos navegadores dejan el MIME vacío). */
export function matchType(file: { name: string; type: string }) {
  const name = file.name.toLowerCase();
  return ALLOWED_TYPES.find((t) => file.type === t.mime || name.endsWith(t.ext));
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  const kb = bytes / 1024;
  if (kb < 1024) return `${Math.round(kb)} KB`;
  return `${(kb / 1024).toLocaleString("es", { maximumFractionDigits: 1 })} MB`;
}

/** Devuelve el motivo del rechazo, o `null` si el archivo es válido. */
export function validateFile(file: File): string | null {
  if (!matchType(file)) return `«${file.name}» no es un PDF, DOCX ni PPTX.`;
  if (file.size === 0) return `«${file.name}» está vacío.`;
  if (file.size > MAX_SIZE_BYTES) {
    return `«${file.name}» pesa ${formatBytes(file.size)} y el máximo es ${MAX_SIZE_LABEL}.`;
  }
  return null;
}

export function formatRelative(iso: string, now: number = Date.now()): string {
  const seconds = Math.round((new Date(iso).getTime() - now) / 1000);
  if (Math.abs(seconds) < 45) return "ahora";
  const rtf = new Intl.RelativeTimeFormat("es", { numeric: "auto" });
  const minutes = Math.round(seconds / 60);
  if (Math.abs(minutes) < 60) return rtf.format(minutes, "minute");
  const hours = Math.round(minutes / 60);
  if (Math.abs(hours) < 24) return rtf.format(hours, "hour");
  return rtf.format(Math.round(hours / 24), "day");
}

interface StatusStyle {
  label: string;
  icon: LucideIcon;
  spin: boolean;
  /** Clases completas (Tailwind necesita verlas literales). */
  badge: string;
}

/** El color nunca es la única señal: cada estado lleva etiqueta e ícono. */
export const STATUS_STYLE: Record<DocumentStatus, StatusStyle> = {
  queued: { label: "En cola", icon: Clock, spin: false, badge: "bg-fg/10 text-muted" },
  processing: { label: "Procesando", icon: LoaderCircle, spin: true, badge: "bg-primary/20 text-primary" },
  indexed: { label: "Indexado", icon: CircleCheck, spin: false, badge: "bg-success/20 text-success" },
  failed: { label: "Falló", icon: CircleAlert, spin: false, badge: "bg-danger/20 text-danger" },
};
