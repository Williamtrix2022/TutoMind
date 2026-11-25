"use client";

import { motion } from "motion/react";
import { CloudUpload } from "lucide-react";
import { useRef, useState } from "react";
import type { DragEvent } from "react";
import { ACCEPT, MAX_SIZE_LABEL } from "@/lib/documents";
import { spring } from "@/lib/motion";

interface DropzoneProps {
  onFiles: (files: File[]) => void;
}

/** Zona para arrastrar y soltar. Es un botón: también se activa con clic, toque o teclado. */
export function Dropzone({ onFiles }: DropzoneProps) {
  const input = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  function onDragOver(event: DragEvent) {
    event.preventDefault();
    setDragging(true);
  }

  function onDragLeave(event: DragEvent) {
    // Ignora los "leave" que solo pasan a un elemento hijo.
    if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setDragging(false);
  }

  function onDrop(event: DragEvent) {
    event.preventDefault();
    setDragging(false);
    const files = Array.from(event.dataTransfer.files);
    if (files.length > 0) onFiles(files);
  }

  return (
    <>
      <input
        ref={input}
        type="file"
        multiple
        accept={ACCEPT}
        className="sr-only"
        tabIndex={-1}
        aria-hidden
        onChange={(event) => {
          const files = Array.from(event.target.files ?? []);
          event.target.value = "";
          if (files.length > 0) onFiles(files);
        }}
      />
      <motion.button
        type="button"
        onClick={() => input.current?.click()}
        onDragEnter={onDragOver}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        animate={{ scale: dragging ? 1.01 : 1 }}
        whileTap={{ scale: 0.99 }}
        transition={spring}
        className={`flex w-full flex-col items-center gap-3 rounded-3xl border-2 border-dashed px-6 py-10 text-center transition-colors ${
          dragging ? "border-primary bg-primary/10" : "border-line bg-card hover:border-primary/60"
        }`}
      >
        <span className="grid size-14 place-items-center rounded-2xl bg-primary/20 text-primary">
          <CloudUpload className="size-7" aria-hidden />
        </span>
        <span className="space-y-1">
          <span className="block text-lg font-bold tracking-tight">
            {dragging ? "Suelta para subir" : "Arrastra tus archivos aquí"}
          </span>
          <span className="block text-sm text-muted">
            o toca para elegirlos · PDF, DOCX o PPTX · hasta {MAX_SIZE_LABEL}
          </span>
        </span>
      </motion.button>
    </>
  );
}
