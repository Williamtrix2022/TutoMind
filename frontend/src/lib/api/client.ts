import createClient from "openapi-fetch";
import type { Middleware } from "openapi-fetch";
import { networkError } from "./errors";
import { notifyUnauthorized } from "./events";
import type { paths } from "./schema";
import { getToken } from "./token-store";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

const withAuth: Middleware = {
  onRequest({ request }) {
    const token = getToken();
    if (token) request.headers.set("Authorization", `Bearer ${token}`);
    return request;
  },
  onResponse({ request, response }) {
    // Un 401 en el login es "credenciales incorrectas", no sesión vencida.
    if (response.status === 401 && !request.url.includes("/auth/login")) notifyUnauthorized();
    return response;
  },
};

/** Convierte el fallo crudo de `fetch` («Failed to fetch») en un error que la interfaz sabe explicar. */
async function safeFetch(request: Request): Promise<Response> {
  try {
    return await fetch(request);
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw networkError();
  }
}

/** Cliente tipado a partir de `docs/openapi.json`. */
export const api = createClient<paths>({ baseUrl: API_BASE_URL, fetch: safeFetch });
api.use(withAuth);
