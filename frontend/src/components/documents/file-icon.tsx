import { FileText, FileType, Presentation } from "lucide-react";
import { ALLOWED_TYPES, matchType } from "@/lib/documents";

/** Ícono por tipo de archivo (PDF, Word o PowerPoint). */
export function FileIcon({ name, mime }: { name: string; mime?: string }) {
  const kind = matchType({ name, type: mime ?? "" }) ?? ALLOWED_TYPES[0];
  const Icon = kind.label === "PPTX" ? Presentation : kind.label === "DOCX" ? FileType : FileText;
  return (
    <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-glow/25 text-glow">
      <Icon className="size-5" aria-hidden />
    </span>
  );
}
