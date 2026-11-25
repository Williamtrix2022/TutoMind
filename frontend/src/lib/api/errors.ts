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

export function toApiError(error: unknown, status?: number): ApiError {
  if (isErrorBody(error)) return new ApiError(error.code, error.message, status);
  return new ApiError("unknown", "No se pudo completar la solicitud. Inténtalo de nuevo.", status);
}
