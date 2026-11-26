"use client";

import { motion } from "motion/react";
import { RotateCcw, X } from "lucide-react";
import { formatBytes } from "@/lib/documents";
import type { UploadEntry } from "@/lib/hooks/use-document-uploads";
import { spring, tap } from "@/lib/motion";
import { FileIcon } from "./file-icon";

interface UploadItemProps {
  entry: UploadEntry;
  onRemove: (id: string) => void;
  onRetry: (id: string) => void;
}

/** Subida en curso o fallida, con barra de progreso. */
export function UploadItem({ entry, onRemove, onRetry }: UploadItemProps) {
  const percent = entry.progress === null ? null : Math.round(entry.progress * 100);
  const failed = entry.error !== null;

  return (
    <motion.li
      layout="position"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={spring}
      className="flex items-center gap-3 rounded-3xl border border-line bg-card p-4 shadow-card"
    >
      <FileIcon name={entry.name} />
      <div className="min-w-0 flex-1 space-y-2">
        <div className="flex items-baseline justify-between gap-3">
          <p className="truncate text-sm font-semibold">{entry.name}</p>
          <p className="shrink-0 text-xs text-muted">{formatBytes(entry.size)}</p>
        </div>

        {failed ? (
          <p role="alert" className="text-sm text-danger">
            {entry.error}
          </p>
        ) : (
          <div
            role="progressbar"
            aria-label={`Subiendo ${entry.name}`}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={percent ?? undefined}
            className="h-2 overflow-hidden rounded-full bg-fg/10"
          >
            <motion.div
              className="h-full rounded-full bg-primary"
              animate={percent === null ? { x: ["-100%", "250%"], width: "40%" } : { width: `${percent}%` }}
              transition={
                percent === null ? { duration: 1.2, repeat: Infinity, ease: "easeInOut" } : { duration: 0.2 }
              }
            />
          </div>
        )}
      </div>

      <div className="flex shrink-0 items-center gap-1">
        {failed && (
          <motion.button
            type="button"
            onClick={() => onRetry(entry.id)}
            whileTap={tap}
            transition={spring}
            aria-label={`Reintentar ${entry.name}`}
            className="grid size-10 place-items-center rounded-xl text-muted hover:text-fg"
          >
            <RotateCcw className="size-4" aria-hidden />
          </motion.button>
        )}
        <motion.button
          type="button"
          onClick={() => onRemove(entry.id)}
          whileTap={tap}
          transition={spring}
          aria-label={failed ? `Quitar ${entry.name}` : `Cancelar la subida de ${entry.name}`}
          className="grid size-10 place-items-center rounded-xl text-muted hover:text-fg"
        >
          <X className="size-4" aria-hidden />
        </motion.button>
      </div>
    </motion.li>
  );
}
