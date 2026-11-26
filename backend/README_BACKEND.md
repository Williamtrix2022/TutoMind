# TutoMind — Backend

FastAPI (Python 3.12) + Pydantic v2 + PostgreSQL/pgvector + Google Gemini (nivel gratuito).

## Contrato
La fuente única de verdad es [`../docs/openapi.json`](../docs/openapi.json). Cualquier cambio de endpoint o esquema se hace ahí primero, en un PR revisado por ambos.

## Endpoints base (Sprint 0)
- `POST /api/v1/auth/login`
- `POST /api/v1/courses/{course_id}/documents` (máx. 20 MB; PDF, DOCX, PPTX)
- `GET  /api/v1/courses/{course_id}/documents` (lista + estado `queued → processing → indexed | failed`; **añadido en el Sprint 1**, ver tarea #16)
- `POST /api/v1/tutor/chat/stream` (SSE)
- `GET  /api/v1/analytics/courses/{course_id}/risk`
- `GET  /api/v1/analytics/courses/{course_id}/topics`

## Reglas
- Validar entrada/salida con Pydantic v2.
- Todo nivel de riesgo se devuelve con sus factores XAI estructurados.
- CORS: permitir `http://localhost:3000` en desarrollo.

## Arranque
```bash
cd backend
uv venv --python 3.12 .venv            # o: python -m venv .venv
.venv\Scriptsctivate                 # Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000
```
- `GET http://localhost:8000/health` → `{"status":"ok"}` (no forma parte del contrato).
- Docs interactivas en `http://localhost:8000/docs`.

## Configuración
Variables de entorno o archivo `.env` (ver `.env.example`). Hoy:
| Variable | Por defecto | Uso |
|---|---|---|
| `CORS_ORIGINS` | `http://localhost:3000` | Orígenes permitidos, separados por coma |
| `ENVIRONMENT` | `development` | Nombre del entorno |
| `JWT_SECRET` | secreto de desarrollo | Firma de tokens (obligatorio fuera de `development`) |
| `ACCESS_TOKEN_EXPIRES_SECONDS` | `3600` | Vigencia del token |
| `DATABASE_URL` | `postgresql+psycopg://tutomind:tutomind@localhost:5432/tutomind` | Conexión a PostgreSQL |
| `EMBEDDING_DIMENSIONS` | `1024` | Tamaño de los vectores |
| `GEMINI_API_KEY` | vacío | Clave gratuita de [Google AI Studio](https://aistudio.google.com/apikey). **Sin clave** el backend usa un cliente offline (embeddings léxicos y tutor de prueba) para poder desarrollar y probar |
| `LLM_MODEL` | `gemini-2.5-flash` | Modelo del tutor |
| `EMBEDDING_MODEL` | `gemini-embedding-001` | Modelo de embeddings (se pide a 1024 dimensiones y se normaliza) |

## Base de datos
PostgreSQL 16 + pgvector. Credenciales de desarrollo en `docker-compose.yml`.
```bash
docker compose up -d db            # levanta Postgres con pgvector
alembic upgrade head               # crea el esquema
python -m app.db.seed              # 1 curso (id `demo`), 1 docente y 5 estudiantes
```
- Usuarios demo: `docente@tutomind.demo`, `ana@tutomind.demo`... con la contraseña `demo12345` (solo desarrollo).
- Nueva migración: `alembic revision -m "descripcion"` (escríbela a mano; `0001_initial.py` es el ejemplo).
- Dimensión de los embeddings: `EMBEDDING_DIMENSIONS` (1024). Cambiarla exige una migración nueva.
- Los tests de `tests/db/` usan un Postgres embebido con pgvector (`pgserver`), **sin Docker**. Para usar otro servidor: `TEST_DATABASE_URL=postgresql://...` (se borra el esquema `public`).

## Autenticación
- `POST /api/v1/auth/login` devuelve un JWT (HS256) con `sub`, `role`, `iat` y `exp` (1 h por defecto).
- `401` = sesión inválida o ausente (`code: unauthorized`, cabecera `WWW-Authenticate: Bearer`); `403` = rol sin permiso (`code: forbidden`).
- Credenciales incorrectas: `401` con `code: invalid_credentials`, idéntico para correo inexistente y clave mala (no revela qué correos existen).
- `role` en el login es solo demo: puede **confirmar** el rol de la cuenta, nunca otorgar otro.
- En endpoints: `Depends(get_current_user)` o `Depends(require_role("teacher"))` (`app/api/deps.py`). El rol se lee de la base de datos, no del token.
- `JWT_SECRET` es obligatorio (aleatorio, ≥ 32 caracteres) cuando `ENVIRONMENT` no es `development`; la app no arranca sin él.

## Documentos (RAG)
- `POST /api/v1/courses/{course_id}/documents` (solo docente matriculado en el curso): multipart `file` (+ `title` opcional). Responde `202` y procesa en segundo plano.
- `GET /api/v1/courses/{course_id}/documents`: lista los más recientes primero, con su estado `queued → processing → indexed | failed` (y `error_message` si falló).
- Validaciones: PDF/DOCX/PPTX (por MIME o extensión) y que el contenido coincida con el tipo → `415`; máximo 20 MB → `413`; archivo vacío o sin nombre → `422`; curso inexistente → `404`; no matriculado → `403`.
- Pipeline (`app/services/`): extracción de texto (`pypdf`, `python-docx`, `python-pptx`) → chunks de ~1000 caracteres con solape → embeddings → pgvector. Cualquier fallo deja el documento en `failed` con un motivo legible; los detalles internos solo van al log.
- Los embeddings salen de `LLMClient.embed()` (`app/services/llm.py`): Gemini si hay `GEMINI_API_KEY`; si no, `OfflineLLMClient` (deterministas, **sin API key**, léxicos y no semánticos).

## Frustración y escalamiento (#18)
- `app/services/frustration.py`: puntuación 0–1 por mensaje, basada en reglas (transparente y sin costo). Solo cuentan las palabras del estudiante; el código y las fórmulas se ignoran. Se considera frustración desde `0.5`.
- Escalamiento: `student_requested` (el estudiante pide ayuda) o `persistent_frustration` (frustrado ahora y en ≥ 2 de sus últimos 3 mensajes). `repeated_failure` está en el contrato pero aún no se detecta.
- `app/services/tickets.py`: `open_ticket` crea el ticket para el docente en `support_tickets`, sin duplicar uno abierto de la misma conversación y motivo (índice único parcial, a prueba de peticiones simultáneas).
- Se conecta al chat en #17. Listar los tickets desde la interfaz del docente requiere un endpoint nuevo en el contrato.

## Tutor socrático (#17)
- `POST /api/v1/tutor/chat/stream` (SSE, cualquier usuario matriculado en el curso). Cada evento es `data: {json}` + línea en blanco, con el formato `TutorStreamEvent` del contrato. Orden: `frustration` (si se detecta) → `token`… → `sources` → `escalation` (si aplica) → `done`. Si el modelo falla: un evento `error` (sin detalles internos) y no hay `done`.
- Cada turno guarda la pregunta y la respuesta en `conversations`/`messages`. `conversation_id` ajeno o inexistente → `404`.
- Recuperación (`retrieval.py`): los 4 fragmentos más cercanos **del mismo curso** (distancia coseno) de documentos ya indexados. Si no hay material, el tutor lo dice y no inventa fuentes. Si falla el embedding de la pregunta, responde sin material.
- Prompt (`tutor_prompt.py`): método socrático, **no entrega la solución completa**, negativa a hacer tareas/exámenes (con guardia extra cuando lo detecta), profundidad según `student_level`, tono empático si hay frustración, y el material va delimitado y escapado como *datos*, no instrucciones (defensa contra prompt injection).
- Escalamiento: si el estudiante pide ayuda (`request_human_help`) se responde con un acuse fijo, **sin llamar al modelo**, y se abre el ticket; con frustración persistente se abre el ticket y se avisa. `ticket_id` va en el evento `escalation`.
- Límites: 40 mensajes por petición y 8000 caracteres por mensaje (`422`).
- Sin `GEMINI_API_KEY` responde `OfflineLLMClient` (reglas, no razona); con clave, Gemini.

## Errores
Todo error se devuelve con el formato `ErrorResponse` del contrato: `{ "code", "message", "details"? }`.
Para fallar desde un endpoint: `raise ApiError(status, "codigo", "Mensaje")` (`app/core/errors.py`).

## Pruebas y calidad
```bash
python -m pytest        # tests
python -m ruff check .  # linter
```

## Estructura
```
backend/
├── app/            # Código de la aplicación (main, core/, api/, schemas/, db/)
├── migrations/     # Alembic
├── docker-compose.yml
├── tests/          # pytest
├── .env.example
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml  # pytest y ruff
└── README_BACKEND.md
```
