# Plan de ejecución — TutoMind (25 → 30 nov 2026)

Estado de partida (verificado en GitHub y en el repo):
- Frontend del Sprint 1 terminado por el compañero (issues #4–#10 cerrados, PRs #30–#35 fusionados).
- Backend sin implementar: `backend/app/` vacío, `requirements.txt` vacío, no existe `app/main.py`.
- Issues de backend sin asignar: #12–#18 (Sprint 1) y #22–#24 (Sprint 2). Pendiente de despliegue: #27.
- Ramas: los PRs #38 y #39 apuntan a `develop`; el #36 promueve `develop` → `main`.

## Fase 0 — Revisión de PRs (hoy)

Orden obligatorio: **#38 → #39 → #36**. La rama del #39 sale de la del #38 (incluye sus commits).

| PR | Acción | Criterio para aprobar |
|---|---|---|
| #38 contrato | Aceptar o discutir los puntos de la sección "Decisiones de contrato" | Backend acepta 413/415, rol `teacher`, estados y polling de 3 s |
| #39 pantalla de documentos | Revisar hallazgos de `PLAN_PRUEBAS.md` §Hallazgos | `tsc`, `eslint` y `build` en verde (ya verificado) y hallazgos A1–A3 resueltos o anotados |
| #36 release a `main` | Fusionar al final, tras #38 y #39 | `develop` estable; sin issues abiertos que lo bloqueen |

### Decisiones de contrato (PR #38) que te comprometen como dueño del backend
1. El `GET /courses/{id}/documents` pasa a ser parte de la tarea #16. Actualizar el texto del issue.
2. 413 si pesa más de 20 MB y 415 si el tipo no está permitido.
3. El `GET` es solo para rol `teacher`.
4. Estados `queued → processing → indexed | failed`, con `error_message` solo si es `failed`.
5. `mime_type` es un enum cerrado de 3 valores: el backend no puede devolver otro.
6. Falta definir qué responde el `POST` con un archivo vacío (el frontend ya lo rechaza; el contrato no dice nada).

## Fase 1 — Núcleo del backend (26–27 nov)

Dependencias: #12 → #13 → #14 → (#15, #16) → (#17, #18).

| Orden | Issue | Entregable mínimo | Prueba de aceptación |
|---|---|---|---|
| 1 | #12 App FastAPI | `app/main.py`, config, CORS `localhost:3000`, `/health`, manejo de errores con `ErrorResponse` | `GET /health` 200; preflight CORS desde `:3000` |
| 2 | #13 Modelos Pydantic v2 | Modelos alineados con `openapi.json` | Test de contrato (ver Plan de pruebas §Contrato) |
| 3 | #14 PostgreSQL + pgvector | `docker-compose`, migraciones | Migración aplica y revierte limpia |
| 4 | #15 Login JWT y roles | `POST /auth/login`, roles `student`/`teacher` | 401 credenciales malas; token con rol correcto |
| 5 | #16 Ingesta | `POST` y `GET` de documentos, extracción, embeddings, estados | Ver Plan de pruebas §Documentos |
| 6 | #17 Chat SSE | RAG socrático con eventos `TutorStreamEvent` | Stream con citas; no entrega solución completa |
| 7 | #18 Frustración y escalamiento | Señales `FrustrationSignal` / `EscalationSignal` | Frase de frustración dispara la señal |

Regla: cada endpoint se entrega con su test y valida entrada y salida con Pydantic v2 (CLAUDE.md).

## Fase 2 — Analítica (28 nov)

| Issue | Entregable |
|---|---|
| #22 Servicio de riesgo XAI | Cada nivel de riesgo se devuelve con `XaiFactor` estructurados (regla de CLAUDE.md) |
| #23 `GET .../topics` | Agregación de temas y alerta de confusión grupal |
| #24 Moodle (eventos y enlaces) | Recorte aceptable si no hay tiempo: datos simulados con interfaz definida |

Frontend en paralelo (compañero): #19, #20 y #21 (integración real).

## Fase 3 — Entrega (29–30 nov)

| Issue | Entregable | Dueño sugerido |
|---|---|---|
| #21 | Quitar mocks MSW en integración real; `DEMO_COURSE_ID` deja de estar fijo | Frontend |
| #25 | E2E del flujo completo (ver Plan de pruebas §E2E) | Ambos |
| #26 | Auditoría PWA, accesibilidad, rendimiento | Frontend |
| #27 | Despliegue de frontend y backend (sin asignar) | A definir |
| #28 | README final, guion de demo | Frontend |
| #29 | Merge `develop` → `main` y etiqueta `v0.1.0` | Ambos |

## Recorte si falta tiempo (de menos a más sacrificable)
1. #24 Moodle: datos simulados.
2. #18: detección por reglas simples (palabras clave) en vez de modelo.
3. #22: factores XAI con reglas ponderadas simples en vez de modelo entrenado.
No recortar: #12–#17, #19–#21, #25, #29.

## Riesgos conocidos
- El frontend no tiene ningún test automatizado (ver Plan de pruebas): la integración real con el backend es donde más probable es que aparezcan fallos.
- El frontend del Sprint 1 está terminado y el backend no ha empezado; el backend es el camino crítico.
- Las "decisiones de contrato" arriba se deben cerrar antes de escribir #16.
