# TutoMind — Backend

FastAPI (Python 3.12) + Pydantic v2 + PostgreSQL/pgvector + Anthropic SDK.

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
├── app/            # Código de la aplicación (main, core/, api/)
├── tests/          # pytest
├── .env.example
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml  # pytest y ruff
└── README_BACKEND.md
```
