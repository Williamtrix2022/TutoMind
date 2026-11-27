"use client";

import { FolderOpen, TriangleAlert } from "lucide-react";
import type { components } from "@/lib/api/schema";
import { formatBytes, formatRelative } from "@/lib/documents";
import { FileIcon } from "./file-icon";
import { StatusBadge } from "./status-badge";

type CourseDocument = components["schemas"]["CourseDocument"];

interface DocumentListProps {
  documents: CourseDocument[] | undefined;
  isLoading: boolean;
  errorMessage: string | null;
  onRetry: () => void;
}

function Skeleton() {
  return (
    <ul className="divide-y divide-line" aria-hidden>
      {[0, 1, 2].map((i) => (
        <li key={i} className="flex items-center gap-3 py-4">
          <span className="size-11 animate-pulse rounded-2xl bg-fg/10" />
          <span className="flex-1 space-y-2">
            <span className="block h-3.5 w-1/2 animate-pulse rounded-full bg-fg/10" />
            <span className="block h-3 w-1/3 animate-pulse rounded-full bg-fg/10" />
          </span>
        </li>
      ))}
    </ul>
  );
}

export function DocumentList({ documents, isLoading, errorMessage, onRetry }: DocumentListProps) {
  if (isLoading) return <Skeleton />;

  if (errorMessage) {
    return (
      <div role="alert" className="flex flex-col items-start gap-3 py-2">
        <p className="flex items-start gap-2 text-sm text-ink-danger">
          <TriangleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
          {errorMessage}
        </p>
        <button
          type="button"
          onClick={onRetry}
          className="rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-on-primary active:scale-[0.97]"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (!documents || documents.length === 0) {
    return (
      <div className="flex flex-col items-center gap-3 py-8 text-center">
        <span className="grid size-12 place-items-center rounded-2xl bg-primary/20 text-primary">
          <FolderOpen className="size-6" aria-hidden />
        </span>
        <div className="space-y-1">
          <p className="font-semibold">Aún no hay documentos</p>
          <p className="max-w-sm text-sm text-muted">
            Sube el sílabo o las guías del curso para que el tutor responda con ese material.
          </p>
        </div>
      </div>
    );
  }

  return (
    <ul className="divide-y divide-line">
      {documents.map((doc) => (
        <li key={doc.document_id} className="flex flex-wrap items-center gap-x-3 gap-y-2 py-4">
          <FileIcon name={doc.filename} mime={doc.mime_type} />
          <div className="min-w-0 flex-1 basis-48 space-y-0.5">
            <p className="truncate text-sm font-semibold">{doc.title ?? doc.filename}</p>
            <p className="truncate text-xs text-muted">
              {doc.title ? `${doc.filename} · ` : ""}
              {formatBytes(doc.size_bytes)} · {formatRelative(doc.created_at)}
            </p>
            {doc.status === "failed" && doc.error_message && (
              <p className="text-xs text-ink-danger">{doc.error_message}</p>
            )}
          </div>
          <StatusBadge status={doc.status} />
        </li>
      ))}
    </ul>
  );
}
