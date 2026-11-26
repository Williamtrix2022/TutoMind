import type { components } from "./schema";

type ErrorBody = components["schemas"]["ErrorResponse"];

/** Error de API con el formato `ErrorResponse` del contrato. */
export class ApiError extends Error {
  constructor(
    readonly code: string,
    message: string,
    readonly status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function isErrorBody(value: unknown): value is ErrorBody {
  return (
    typeof value === "object" &&
    value !== null &&
    "code" in value &&
    "message" in value &&
    typeof (value as ErrorBody).code === "string" &&
    typeof (value as ErrorBody).message === "string"
  );
}

/** Mensajes genéricos en inglés que genera el framework del servidor; se muestran en español. */
const FRAMEWORK_MESSAGES: Record<string, string> = {
  "not found": "No encontramos esto en el servidor. Puede que esa función aún no esté disponible.",
  "method not allowed": "El servidor no admite esta acción todavía.",
  "internal server error": "El servidor tuvo un problema. Inténtalo de nuevo en un momento.",
};

export function toApiError(error: unknown, status?: number): ApiError {
  if (isErrorBody(error)) {
    const friendly = FRAMEWORK_MESSAGES[error.message.trim().toLowerCase()];
    return new ApiError(error.code, friendly ?? error.message, status);
  }
  return new ApiError("unknown", "No se pudo completar la solicitud. Inténtalo de nuevo.", status);
}

/** Sin respuesta del servidor: está apagado, sin red o bloqueado por CORS. */
export function networkError(): ApiError {
  return new ApiError("network", "No pudimos conectar con el servidor. Revisa tu conexión e inténtalo de nuevo.");
}

/**
 * Reintenta solo lo que puede arreglarse solo: caídas de red y errores 5xx.
 * Un 4xx (credenciales, permisos, no existe) repetido da el mismo resultado.
 */
export function shouldRetry(failureCount: number, error: unknown): boolean {
  if (error instanceof ApiError && error.status !== undefined && error.status < 500) return false;
  return failureCount < 2;
}

/** 1 s, 2 s, 4 s… con tope de 8 s. */
export function retryDelay(attempt: number): number {
  return Math.min(1000 * 2 ** attempt, 8000);
}
