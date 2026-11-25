import { API_BASE_URL } from "./client";
import { ApiError, toApiError } from "./errors";
import { notifyUnauthorized } from "./events";
import type { components } from "./schema";
import { getToken } from "./token-store";

export type TutorChatRequest = components["schemas"]["TutorChatRequest"];
export type TutorStreamEvent = components["schemas"]["TutorStreamEvent"];

function isStreamEvent(value: unknown): value is TutorStreamEvent {
  return (
    typeof value === "object" &&
    value !== null &&
    "type" in value &&
    typeof (value as { type: unknown }).type === "string"
  );
}

/**
 * Chat del tutor por SSE. Produce eventos tipados a medida que llegan.
 * Cancela la petición con `signal`.
 */
export async function* streamTutorChat(
  body: TutorChatRequest,
  signal?: AbortSignal,
): AsyncGenerator<TutorStreamEvent, void, void> {
  const token = getToken();
  const response = await fetch(`${API_BASE_URL}/api/v1/tutor/chat/stream`, {
    method: "POST",
    signal,
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  });

  if (!response.ok || !response.body) {
    if (response.status === 401) notifyUnauthorized();
    const payload: unknown = await response.json().catch(() => null);
    throw toApiError(payload, response.status);
  }

  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";

  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += value;

      let boundary = buffer.indexOf("\n\n");
      while (boundary !== -1) {
        const rawEvent = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        boundary = buffer.indexOf("\n\n");

        const data = rawEvent
          .split("\n")
          .filter((line) => line.startsWith("data:"))
          .map((line) => line.slice(5).trimStart())
          .join("\n");
        if (!data) continue;

        const parsed: unknown = JSON.parse(data);
        if (!isStreamEvent(parsed)) throw new ApiError("bad_event", "Evento del tutor no válido.");
        yield parsed;
      }
    }
  } finally {
    reader.releaseLock();
  }
}
