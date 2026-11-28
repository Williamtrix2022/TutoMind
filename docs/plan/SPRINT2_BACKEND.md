# Sprint 2 — backend: punto de partida

Sprint 1 del backend completo (#12–#18). Orden recomendado: **#22 → #23 → #24**, con el frontend (#19, #20, #21) en paralelo contra los mocks.

## Qué hay disponible para construir encima
| Dato | Dónde | Sirve para |
|---|---|---|
| Usuarios y rol | `users` | Listar estudiantes de un curso (`enrollments` + `role = student`) |
| Matrícula | `enrollments` | Quién pertenece a cada curso |
| Preguntas y respuestas del tutor | `conversations`, `messages` (con fecha) | Actividad por estudiante (#22) y temas más consultados (#23) |
| Escalamientos | `support_tickets` | Señal de riesgo y alertas |
| Autorización por rol | `require_role("teacher")` | Proteger `/analytics/...` (solo docente matriculado, como en documentos) |
| Contrato y tests | `tests/contract.py`, `tests/api/test_contract_paths.py` | Las 2 operaciones de analítica están *skipped*: al implementarlas, el test las compara solo con `openapi.json` |

## #22 Riesgo con XAI
- Cada `StudentRisk` debe llevar ≥ 1 `XaiFactor` (el modelo ya lo exige). `impact` en [−1, 1], positivo = aumenta el riesgo.
- Factores calculables **hoy** sin Moodle: días sin actividad en el tutor, nº de preguntas, nº de tickets abiertos, frustración reciente.
- **Falta persistir el score de frustración** (hoy solo se emite por SSE): añadir `frustration_score` a `messages` (migración 0003) para poder explicarlo.
- Notas e ingresos a Moodle dependen de #24: mientras tanto, datos simulados detrás de una interfaz (`ActivitySource`) para sustituirlos sin tocar el cálculo.
- Decisión a tomar: pesos y umbrales de verde/amarillo/rojo. Propuesta: modelo de reglas ponderadas, transparente y testeable (sin entrenar).

## #23 Temas y confusión
- Hace falta asignar un tema a cada pregunta. Propuesta: columna `topic` en `messages` (migración) rellenada al guardar la pregunta, con un extractor detrás de una interfaz (palabras clave offline; Gemini cuando haya clave).
- `confusion_score` por tema = fracción de preguntas con frustración o repetidas; `confusion_alert` al superar un umbral.

## Huecos del contrato (PR de contrato, requiere aprobación de ambos)
- `POST` y `GET` de documentos: añadir `404` (curso inexistente) y `422`.
- Tutor: añadir `403` (no matriculado), `404` (curso o conversación) y las cabeceras SSE.
- Endpoint para que el docente vea los **tickets** abiertos (hoy se guardan, pero no hay cómo listarlos).

## Límites conocidos del Sprint 1
- ~~Si el servidor se reinicia a mitad de indexar, el documento queda en `processing`.~~ Resuelto: se marca como fallido al arrancar y al listar (ver «Robustez en producción» en `backend/README_BACKEND.md`).
- El 413 se decide tras recibir el cuerpo completo (sin corte temprano).
- El tutor sin API key es un sustituto de reglas; la calidad real exige `GEMINI_API_KEY` (nivel gratuito: usar solo documentos de demo).
- La detección de frustración es léxica: no entiende ironía; `repeated_failure` no se detecta aún.
