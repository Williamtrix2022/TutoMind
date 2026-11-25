import type { components } from "@/lib/api/schema";

type CourseDocument = components["schemas"]["CourseDocument"];
type DocumentStatus = components["schemas"]["DocumentStatus"];
type DocumentUploadResponse = components["schemas"]["DocumentUploadResponse"];

interface StoredDocument {
  doc: CourseDocument;
  uploadedAt: number;
  willFail: boolean;
}

const KEY = "tm-mock-docs";
const QUEUED_MS = 3000;
const PROCESSING_MS = 8000;

const PDF = "application/pdf";
const DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document";

function seed(): StoredDocument[] {
  const day = 24 * 60 * 60 * 1000;
  const now = Date.now();
  const make = (
    id: string,
    filename: string,
    title: string,
    mime: CourseDocument["mime_type"],
    size: number,
    ageMs: number,
  ): StoredDocument => ({
    uploadedAt: now - ageMs,
    willFail: false,
    doc: {
      document_id: id,
      course_id: "demo",
      filename,
      title,
      mime_type: mime,
      size_bytes: size,
      status: "indexed",
      error_message: null,
      created_at: new Date(now - ageMs).toISOString(),
    },
  });
  return [
    make("doc-seed-2", "guia-ejercicios-u2.docx", "Guía de ejercicios · Unidad 2", DOCX, 310_000, day),
    make("doc-seed-1", "silabo-calculo.pdf", "Sílabo de Cálculo Diferencial", PDF, 842_000, 2 * day),
  ];
}

function load(): StoredDocument[] {
  try {
    const raw = window.sessionStorage.getItem(KEY);
    if (raw) {
      const parsed: unknown = JSON.parse(raw);
      if (Array.isArray(parsed)) return parsed as StoredDocument[];
    }
  } catch {
    /* sin almacenamiento: se usa la semilla */
  }
  return seed();
}

function save(items: StoredDocument[]): void {
  try {
    window.sessionStorage.setItem(KEY, JSON.stringify(items));
  } catch {
    /* se ignora */
  }
}

/** El estado avanza con el tiempo: queued → processing → indexed (o failed). */
function statusOf({ uploadedAt, willFail }: StoredDocument): DocumentStatus {
  const elapsed = Date.now() - uploadedAt;
  if (elapsed < QUEUED_MS) return "queued";
  if (elapsed < PROCESSING_MS) return "processing";
  return willFail ? "failed" : "indexed";
}

export function listDocuments(): CourseDocument[] {
  return load()
    .map((item) => {
      const status = statusOf(item);
      return {
        ...item.doc,
        status,
        error_message: status === "failed" ? "No se pudo extraer el texto del archivo. Prueba con otra versión." : null,
      };
    })
    .sort((a, b) => b.created_at.localeCompare(a.created_at));
}

interface NewDocument {
  courseId: string;
  file: File;
  mime: CourseDocument["mime_type"];
  title: string | null;
}

/** Un archivo con «fallo» en el nombre termina en `failed`, para ver ese estado. */
export function addDocument({ courseId, file, mime, title }: NewDocument): DocumentUploadResponse {
  const items = load();
  const id = `doc-${Date.now()}`;
  items.push({
    uploadedAt: Date.now(),
    willFail: file.name.toLowerCase().includes("fallo"),
    doc: {
      document_id: id,
      course_id: courseId,
      filename: file.name,
      title,
      mime_type: mime,
      size_bytes: file.size,
      status: "queued",
      error_message: null,
      created_at: new Date().toISOString(),
    },
  });
  save(items);
  return { document_id: id, course_id: courseId, filename: file.name, mime_type: mime, status: "queued" };
}
