"use client";

import { AnimatePresence } from "motion/react";
import { TriangleAlert, X } from "lucide-react";
import { useCallback, useState } from "react";
import { Card } from "@/components/ui/card";
import { useCourseDocuments } from "@/lib/api/hooks/use-documents";
import { DEMO_COURSE_ID } from "@/lib/config";
import { useDocumentUploads } from "@/lib/hooks/use-document-uploads";
import { Dropzone } from "./dropzone";
import { DocumentList } from "./document-list";
import { UploadItem } from "./upload-item";

export function DocumentsView() {
  const [rejections, setRejections] = useState<string[]>([]);
  const [announcement, setAnnouncement] = useState("");

  const onUploaded = useCallback((filename: string) => setAnnouncement(`«${filename}» se subió correctamente.`), []);
  const { entries, addFiles, remove, retry } = useDocumentUploads({ courseId: DEMO_COURSE_ID, onUploaded });
  const documents = useCourseDocuments(DEMO_COURSE_ID);

  function handleFiles(files: File[]) {
    setAnnouncement("");
    setRejections(addFiles(files));
  }

  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-3xl md:text-4xl">Documentos del curso</h1>
        <p className="max-w-prose text-sm text-muted">
          Lo que subas alimenta al tutor. Cada archivo tarda un momento en indexarse antes de poder usarse.
        </p>
      </header>

      <Dropzone onFiles={handleFiles} />

      {rejections.length > 0 && (
        <div role="alert" className="flex items-start gap-3 rounded-3xl border border-danger/40 bg-card p-4 shadow-card">
          <TriangleAlert className="mt-0.5 size-5 shrink-0 text-danger" aria-hidden />
          <ul className="min-w-0 flex-1 space-y-1 text-sm">
            {rejections.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
          <button
            type="button"
            onClick={() => setRejections([])}
            aria-label="Cerrar aviso"
            className="grid size-8 shrink-0 place-items-center rounded-lg text-muted hover:text-fg"
          >
            <X className="size-4" aria-hidden />
          </button>
        </div>
      )}

      {entries.length > 0 && (
        <ul className="space-y-3" aria-label="Subidas en curso">
          <AnimatePresence initial={false}>
            {entries.map((entry) => (
              <UploadItem key={entry.id} entry={entry} onRemove={remove} onRetry={retry} />
            ))}
          </AnimatePresence>
        </ul>
      )}

      <Card className="px-5 py-2">
        <div className="flex items-baseline justify-between gap-3 pb-1 pt-3">
          <h2 className="text-lg">Subidos</h2>
          {documents.data && (
            <span className="text-sm text-muted">
              {documents.data.documents.length}{" "}
              {documents.data.documents.length === 1 ? "documento" : "documentos"}
            </span>
          )}
        </div>
        <DocumentList
          documents={documents.data?.documents}
          isLoading={documents.isPending}
          errorMessage={documents.isError ? documents.error.message : null}
          onRetry={() => void documents.refetch()}
        />
      </Card>

      <p className="sr-only" role="status" aria-live="polite">
        {announcement}
      </p>
    </div>
  );
}
