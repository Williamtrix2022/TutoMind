import type { components } from "@/lib/api/schema";

/** Tipos derivados del contrato `docs/openapi.json` (ver `npm run gen:api`). */
export type Role = components["schemas"]["Role"];
export type RiskLevel = components["schemas"]["RiskLevel"];
export type StudentLevel = components["schemas"]["StudentLevel"];

/** Solo de UI: no forma parte del contrato. */
export type Theme = "dark" | "light";
