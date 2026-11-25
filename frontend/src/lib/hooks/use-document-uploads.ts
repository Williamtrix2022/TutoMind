"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";
import { documentsKey } from "@/lib/api/hooks/use-documents";
import { uploadDocument } from "@/lib/api/upload";
import { validateFile } from "@/lib/documents";

export interface UploadEntry {
  id: string;
  name: string;
  size: number;
  /** Fracción 0–1, o `null` si es indeterminado. */
  progress: number | null;
  error: string | null;
}

interface Options {
  courseId: string;
  onUploaded?: (filename: string) => void;
}

let uploadCounter = 0;

/** Cola local de subidas en curso. Al terminar, el archivo pasa a la lista del servidor. */
export function useDocumentUploads({ courseId, onUploaded }: Options) {
  const queryClient = useQueryClient();
  const [entries, setEntries] = useState<UploadEntry[]>([]);
  const files = useRef(new Map<string, File>());
  const controllers = useRef(new Map<string, AbortController>());

  const patch = useCallback((id: string, changes: Partial<UploadEntry>) => {
    setEntries((prev) => prev.map((e) => (e.id === id ? { ...e, ...changes } : e)));
  }, []);

  const drop = useCallback((id: string) => {
    files.current.delete(id);
    controllers.current.delete(id);
    setEntries((prev) => prev.filter((e) => e.id !== id));
  }, []);

  const start = useCallback(
    async (id: string) => {
      const file = files.current.get(id);
      if (!file) return;
      const controller = new AbortController();
      controllers.current.set(id, controller);
      // Indeterminada hasta que el navegador informe el primer progreso real.
      patch(id, { progress: null, error: null });

      try {
        await uploadDocument({
          courseId,
          file,
          signal: controller.signal,
          onProgress: (progress) => patch(id, { progress }),
        });
        drop(id);
        await queryClient.invalidateQueries({ queryKey: documentsKey(courseId) });
        onUploaded?.(file.name);
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") return;
        patch(id, {
          progress: null,
          error: error instanceof Error ? error.message : "No se pudo subir el archivo.",
        });
      }
    },
    [courseId, drop, onUploaded, patch, queryClient],
  );

  /** Valida y encola los archivos. Devuelve los motivos de rechazo. */
  const addFiles = useCallback(
    (selected: File[]): string[] => {
      const rejected: string[] = [];
      for (const file of selected) {
        const reason = validateFile(file);
        if (reason) {
          rejected.push(reason);
          continue;
        }
        const id = `u${++uploadCounter}`;
        files.current.set(id, file);
        setEntries((prev) => [...prev, { id, name: file.name, size: file.size, progress: null, error: null }]);
        void start(id);
      }
      return rejected;
    },
    [start],
  );

  const remove = useCallback(
    (id: string) => {
      controllers.current.get(id)?.abort();
      drop(id);
    },
    [drop],
  );

  const retry = useCallback((id: string) => void start(id), [start]);

  // Cancela las subidas si el usuario sale de la pantalla.
  useEffect(() => {
    const active = controllers.current;
    return () => active.forEach((controller) => controller.abort());
  }, []);

  return { entries, addFiles, remove, retry };
}
