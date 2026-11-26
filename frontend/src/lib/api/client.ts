import createClient from "openapi-fetch";
import type { Middleware } from "openapi-fetch";
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

/** Cliente tipado a partir de `docs/openapi.json`. */
export const api = createClient<paths>({ baseUrl: API_BASE_URL });
api.use(withAuth);
