import { API_BASE_URL } from "./client";
import { ApiError, toApiError } from "./errors";
import { notifyUnauthorized } from "./events";
import type { components } from "./schema";
import { getToken } from "./token-store";

export type DocumentUploadResponse = components["schemas"]["DocumentUploadResponse"];

interface UploadArgs {
  courseId: string;
  file: File;
  title?: string;
  /** Fracción 0–1, o `null` si el navegador no conoce el total. */
  onProgress?: (fraction: number | null) => void;
  signal?: AbortSignal;
}

function isUploadResponse(value: unknown): value is DocumentUploadResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    typeof (value as { document_id?: unknown }).document_id === "string"
  );
}

/** Sube un documento. Usa XHR porque `fetch` no informa el progreso de subida. */
export function uploadDocument({ courseId, file, title, onProgress, signal }: UploadArgs): Promise<DocumentUploadResponse> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE_URL}/api/v1/courses/${encodeURIComponent(courseId)}/documents`);
    xhr.setRequestHeader("Accept", "application/json");
    const token = getToken();
    if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);

    xhr.upload.onprogress = (event) => onProgress?.(event.lengthComputable ? event.loaded / event.total : null);

    xhr.onload = () => {
      let payload: unknown = null;
      try {
        payload = JSON.parse(xhr.responseText);
      } catch {
        /* respuesta sin JSON */
      }
      if (xhr.status >= 200 && xhr.status < 300 && isUploadResponse(payload)) {
        resolve(payload);
        return;
      }
      if (xhr.status === 401) notifyUnauthorized();
      reject(toApiError(payload, xhr.status));
    };
    xhr.onerror = () =>
      reject(new ApiError("network", "No se pudo conectar. Revisa tu conexión e inténtalo de nuevo."));
    xhr.onabort = () => reject(new DOMException("Subida cancelada", "AbortError"));
    signal?.addEventListener("abort", () => xhr.abort(), { once: true });

    const form = new FormData();
    form.append("file", file);
    if (title) form.append("title", title);
    xhr.send(form);
  });
}
