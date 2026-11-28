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
| `MOODLE_BASE_URL` / `MOODLE_TOKEN` | vacío | Moodle Web Services; sin ellos, datos simulados (ver Moodle) |
| `GEMINI_API_KEY` | vacío | Clave gratuita de [Google AI Studio](https://aistudio.google.com/apikey). **Sin clave** el backend usa un cliente offline (embeddings léxicos y tutor de prueba) para poder desarrollar y probar |
| `LLM_MODEL` | `gemini-3.5-flash-lite` | Modelo del tutor (responde en ~1 s; los «flash» normales piensan y tardan 24 s o más; `gemini-2.5-flash` ya no se ofrece a cuentas nuevas) |
| `EMBEDDING_MODEL` | `gemini-embedding-001` | Modelo de embeddings (se pide a 1024 dimensiones y se normaliza) |

## Base de datos
PostgreSQL 16 + pgvector. Credenciales de desarrollo en `docker-compose.yml`.
```bash
docker compose up -d db            # levanta Postgres con pgvector
alembic upgrade head               # crea el esquema
python -m app.db.seed              # 1 curso (id `demo`), 1 docente y 5 estudiantes
```
- Si el puerto 5432 ya está ocupado (por ejemplo, un PostgreSQL instalado en Windows), define `POSTGRES_PORT=5433` y apunta `DATABASE_URL` al mismo puerto: `postgresql+psycopg://tutomind:tutomind@localhost:5433/tutomind`.
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

## Tutor explicativo (#17)
- `POST /api/v1/tutor/chat/stream` (SSE, cualquier usuario matriculado en el curso). Cada evento es `data: {json}` + línea en blanco, con el formato `TutorStreamEvent` del contrato. Orden: `frustration` (si se detecta) → `token`… → `sources` → `escalation` (si aplica) → `done`. Si el modelo falla: un evento `error` (sin detalles internos) y no hay `done`.
- Cada turno guarda la pregunta y la respuesta en `conversations`/`messages`. `conversation_id` ajeno o inexistente → `404`.
- Recuperación (`retrieval.py`): se piden hasta 12 candidatos **del mismo curso** (distancia coseno, solo documentos indexados) y se **filtran por relevancia** (`Relevance`) hasta quedarse con 4. Con Gemini cuenta una distancia máxima (`RETRIEVAL_MAX_DISTANCE`, 0,65) y un margen respecto al mejor (`RETRIEVAL_MARGIN`, 0,12). El embedder offline casi no separa temas por distancia, así que ahí se exige vocabulario poco común compartido con la pregunta (peso tipo IDF; las palabras de todas las materias, como «función», no cuentan). Así una duda de Programación no recibe apuntes de Cálculo. Sin material relevante, el tutor lo dice y no inventa fuentes. Si falla el embedding de la pregunta, responde sin material.
- Prompt (`tutor_prompt.py`): tutor académico **amable, paciente y experto** que responde con claridad y completa el material con su conocimiento (diciéndolo). Cada respuesta tiene **validación breve → explicación paso a paso → ejemplo práctico → cierre de verificación**, adapta la profundidad a `student_level` y, si el estudiante sigue sin entender, lo explica de otra forma. Solo ante la petición de hacer un trabajo calificado para entregarlo (guardia extra) explica el concepto y resuelve un ejemplo análogo. El material va delimitado como datos, no como instrucciones.
- Escalamiento (el docente es la **última instancia**): el servidor **ofrece** enviar la duda al docente solo si el estudiante dice que sigue sin entender tras al menos 2 explicaciones (`repeated_failure`) o su frustración persiste (`persistent_frustration`: frustrado ahora y en 2 de sus últimos 3 mensajes). Ofrecer no es escalar: el evento `escalation` llega con `suggested: true` y **sin `ticket_id`**. El ticket se crea cuando el estudiante confirma (`request_human_help: true`): se responde con un acuse fijo, **sin llamar al modelo**, y `ticket_id` va en el evento. Ese ticket cuenta en el factor «ayudas abiertas» del riesgo.
- Límites: 40 mensajes por petición y 8000 caracteres por mensaje (`422`).
- Sin `GEMINI_API_KEY` responde `OfflineLLMClient`: no razona, pero **formatea los fragmentos recuperados** (encabezado, viñetas con las frases que responden la pregunta, el ejemplo del material, la fuente con su página y una pregunta de cierre) y dice con honestidad cuando el curso no cubre el tema. Con clave, Gemini.

## Riesgo académico con XAI (#22)
- `GET /api/v1/analytics/courses/{course_id}/risk[?level=green|yellow|red]` (solo docente matriculado). Estudiantes de mayor a menor riesgo; `level` filtra la lista pero el `summary` siempre cuenta todo el curso.
- Modelo **de reglas ponderadas**, no entrenado: no hay histórico etiquetado y el docente debe poder *leer* por qué se marca a un estudiante. El puntaje es literalmente lo que suman los factores: `risk_score = clamp(0.5 + Σ impact)`, con `impact = peso × severidad` (severidad en [−1, 1]; positivo = más riesgo).
- Factores y pesos (`app/services/risk.py`): días sin ingresar 0.30, promedio de notas 0.30, tareas sin entregar 0.15, frustración con el tutor 0.10, uso del tutor 0.10, ayudas abiertas al docente 0.05. Un factor sin datos no aparece; siempre hay al menos uno.
- Niveles: verde `< 0.40`, amarillo `< 0.65`, rojo `≥ 0.65`. Nota proyectada (escala 5): promedio de notas (3.0 si no hay) menos 0.25 por cada 0.1 de impacto de los demás factores. **Pesos y umbrales son una primera calibración**: ajustarlos con datos reales.
- Los datos salen de `student_events` (accesos, notas, entregas, plazos vencidos; los alimenta Moodle en #24), de las preguntas al tutor (con su `frustration_score`, que ahora se guarda) y de los tickets abiertos. Ventanas: notas 90 días, entregas 30, tutor 14.
- `python -m app.db.seed` incluye actividad de demostración: un estudiante verde, dos amarillos y dos rojos (uno de ellos nunca visto).

## Temas y termómetro del aula (#23)
- `GET /api/v1/analytics/courses/{course_id}/topics` (solo docente matriculado): temas de los **últimos 7 días**, con las alertas primero.
- **Tema de una pregunta** (`app/services/topics.py`): el título del documento del curso cuyo fragmento más cercano comparte vocabulario con la pregunta (se ignoran plurales, tildes y mayúsculas); si ninguno lo hace, `Otros temas`. Se guarda en `messages.topic` al chatear. Pedir ayuda al docente no es un tema. Es un criterio grueso a propósito (1 documento = 1 tema), gratis y sin modelo; `topic_for` es el único punto a sustituir por uno más fino.
- **Confusión de un tema** (0–1): `0.6 × (preguntas con frustración / preguntas) + 0.4 × (estudiantes que preguntaron más de una vez / estudiantes)`.
- **Umbral de alerta:** `confusion_score ≥ 0.5` **y** al menos 3 preguntas (un estudiante molesto no es confusión grupal). Ambos valores son una primera calibración: ajustarlos con clases reales.
- `sample_questions`: hasta 3 textos, primero los frustrados y los más recientes. Los temas no incluyen nombres de estudiantes.
- Límite: se leen como máximo las 5000 preguntas más recientes de la ventana.

## Moodle (#24)
Alimenta el riesgo (#22) con actividad real y enlaza las citas del tutor a Moodle. **Sin Moodle configurado todo funciona con datos simulados**, avisando siempre.

| Variable | Qué hace |
|---|---|
| `MOODLE_BASE_URL` | URL de Moodle (`https://moodle.universidad.edu`). Vacía = sin Moodle (datos simulados) |
| `MOODLE_TOKEN` | Token de Web Services. Obligatorio si hay URL; la app se niega a inventar datos sin él |

- **Ingesta:** `python -m app.services.moodle_sync <course_id>` (a mano o con cron). Es idempotente: un índice único (curso, estudiante, tipo, momento, origen) evita duplicados, así que se puede repetir sin miedo. Los usuarios se emparejan por **correo** (sin distinguir mayúsculas) con los estudiantes matriculados en el curso; el resto se cuenta como `usuarios_desconocidos`. El `course_id` de TutoMind es el id del curso en Moodle.
- **Qué lee** (`app/services/moodle.py`, protocolo REST, un POST por función con el token en el cuerpo, nunca en la URL): `core_enrol_get_enrolled_users` (último acceso y quién es estudiante), `gradereport_user_get_grade_items` (notas), `mod_assign_get_assignments` y `mod_assign_get_submissions` (entregas; vencida sin entrega = plazo incumplido; un borrador no cuenta).
- **Datos simulados:** sin configuración se usa `SimulatedMoodleClient`, solo para el curso `demo` (5 perfiles: verde, amarillo, rojo, y un estudiante nunca visto). Sus eventos llevan `source = 'simulated'` y cada ejecución **reemplaza** la instantánea anterior (están fechados respecto a "ahora"; si no, se acumularían y subirían el riesgo). Nunca toca datos reales de Moodle. `python -m app.db.seed` los usa.
- **Enlaces:** cada cita del tutor lleva `moodle_url`: el enlace propio del documento (`documents.moodle_url`) o, si no lo tiene, la página del curso en Moodle (solo con `MOODLE_BASE_URL` y un id numérico).
- **Límites, dichos con franqueza:** el cliente se escribió a partir de las respuestas documentadas de Moodle y se probó contra un Moodle **simulado**; **no se ha probado contra un Moodle real** (revisar los nombres de campo al primer uso). Moodle solo expone el *último* acceso, así que cada ingesta añade como mucho un acceso por estudiante. No hay planificador integrado (usar cron), ni forma todavía de rellenar `documents.moodle_url` desde la API.

## Robustez en producción (plan gratuito)
- **Reintentos con la IA** (`app/services/llm.py`): ante un fallo transitorio de Gemini (HTTP 429, 500, 502, 503, 504, red o tiempo de espera) se reintenta hasta 2 veces, esperando 1 s y 2 s. Cada lote de embeddings se reintenta por separado. Una vez que el estudiante ya vio el primer fragmento de la respuesta **no se reintenta** (repetiría texto). Un error de petición (4xx) o un bug no se reintenta.
- **Errores con nombre:** el fallo sale como `LLMError` con `kind` (`rate_limit`, `unavailable`, `other`), que nunca incluye el mensaje del proveedor ni la clave. El tutor responde con un evento `error` específico (`llm_rate_limited`: «recibiendo muchas consultas… espera un minuto»; `llm_unavailable`) y la ingesta deja el documento en `failed` con un motivo que dice qué hacer («Vuelve a subir el documento en unos minutos»).
- **Documentos atascados:** el archivo se indexa en memoria, así que si el servidor se reinicia a mitad el trabajo se pierde. Por eso: **al arrancar** se marcan como `failed` los documentos `queued`/`processing` de más de 2 minutos (el margen evita pisar a otra instancia viva), y **al listar** los documentos del curso se marcan los de más de 10 minutos. Si el arranque no puede consultar la base de datos, el servidor igualmente arranca.
- **Límite conocido:** un documento que de verdad tarde más de 10 minutos en indexarse se mostraría como fallido al listar aunque termine después.

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
