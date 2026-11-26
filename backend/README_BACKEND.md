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

## Arranque (a completar)
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

## Estructura
```
backend/
├── app/            # Código de la aplicación
├── .env.example
├── requirements.txt
└── README_BACKEND.md
```
