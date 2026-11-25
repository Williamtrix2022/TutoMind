import createClient from "openapi-fetch";
import type { Middleware } from "openapi-fetch";
import type { paths } from "./schema";
import { getToken } from "./token-store";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

const withAuth: Middleware = {
  onRequest({ request }) {
    const token = getToken();
    if (token) request.headers.set("Authorization", `Bearer ${token}`);
    return request;
  },
};

/** Cliente tipado a partir de `docs/openapi.json`. */
export const api = createClient<paths>({ baseUrl: API_BASE_URL });
api.use(withAuth);
