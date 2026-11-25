/** El backend respondió 401: la sesión ya no es válida. AppProviders la cierra. */
export const UNAUTHORIZED_EVENT = "tm:unauthorized";

export function notifyUnauthorized(): void {
  if (typeof window !== "undefined") window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
}
