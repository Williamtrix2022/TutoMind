# 🧠 TutoMind — Tutor Inteligente & Analítica Predictiva XAI

Plataforma web educativa (PWA) integrada con **Moodle** que combina tutoría personalizada mediante IA generativa (RAG sobre material docente) con detección temprana y explicable de riesgo académico.

**Entrega: 30 de noviembre de 2026** · [📋 Estado del MVP](docs/TutoMind_Mvp.md) · [Issues](../../issues) · [Milestones (sprints)](../../milestones) · [Contrato de API](docs/openapi.json)

---

## ✨ Características Principales (MVP)

### 🎓 Para Estudiantes
* **Tutor Socrático y Evaluador:** Genera ejercicios prácticos basados en el sílabo y documentos del curso, evalúa respuestas y guía paso a paso sin regalar soluciones completas.
* **Adaptación Cognitiva y Emocional:** Ajusta la profundidad según nivel (Básico, Intermedio, Avanzado), detecta frustración para adaptar el tono y señala lagunas de conocimiento recurrentes.
* **Soporte Técnico Completo:** Renderizado nativo de fórmulas matemáticas (**LaTeX/KaTeX**), bloques de código con resaltado de sintaxis y enlaces directos a recursos de Moodle.
* **Escalamiento Humano:** Opción directa para solicitar apoyo del docente cuando una duda persiste.

### 👩‍🏫 Para Docentes
* **Gestión de Conocimiento por Asignatura:** Carga de archivos PDF, DOCX, PPTX y guías que alimentan la base vectorial del curso.
* **Dashboard Predictivo con Explicabilidad (XAI):** Vista de semáforo (**Verde / Amarillo / Rojo**) actualizada por eventos en Moodle, detallando los factores exactos de cada alerta.
* **Termómetro del Aula:** Reporte automático de los temas más consultados y alertas tempranas de confusión grupal.

---

## 🏗️ Arquitectura del Proyecto

```text
tutomind/
├── frontend/          # Next.js 15 + TypeScript + Tailwind + Motion (PWA)
├── backend/           # FastAPI + Python 3.12 + pgvector + Gemini (gratis)
├── docs/              # Contrato OpenAPI, estado del MVP (TutoMind_Mvp.md) y diagramas
├── .github/           # Plantillas de issues y pull requests
├── CLAUDE.md          # Reglas de arquitectura y diseño para Claude Code
├── CONTRIBUTING.md    # Flujo de trabajo del equipo
└── README.md
```

El contrato [`docs/openapi.json`](docs/openapi.json) es la **fuente única de verdad** entre Frontend y Backend. Cualquier cambio de endpoint se hace ahí primero, en un PR revisado por ambos.

| Endpoint | Descripción |
|---|---|
| `POST /api/v1/auth/login` | Login con rol `student` o `teacher` |
| `POST /api/v1/courses/{course_id}/documents` | Subida de PDF/DOCX/PPTX |
| `POST /api/v1/tutor/chat/stream` | Chat del tutor por SSE (LaTeX, código, frustración, escalamiento) |
| `GET /api/v1/analytics/courses/{course_id}/risk` | Semáforo de riesgo con factores XAI |
| `GET /api/v1/analytics/courses/{course_id}/topics` | Temas más consultados y alertas de confusión |

---

## 🚀 Puesta en marcha

### Frontend
```bash
cd frontend
npm install
npm run dev        # http://localhost:3000
```

### Backend
Ver [`backend/README_BACKEND.md`](backend/README_BACKEND.md).

---

## 👥 Equipo y responsabilidades

| Área | Carpeta | Responsable |
|---|---|---|
| Frontend (UI, PWA, integración) | `/frontend` | @Williamtrix2022 |
| Backend (API, RAG, riesgo XAI, Moodle) | `/backend` | _Compañero de equipo_ |
| Contrato de API | `/docs/openapi.json` | Ambos (revisión cruzada) |

---

## 🗓️ Plan de trabajo: fases y sprints

Cada sprint es un [milestone](../../milestones) de GitHub y cada fase una etiqueta `fase:*`.

| Sprint | Fechas | Fase | Objetivo |
|---|---|---|---|
| **Sprint 0** ✅ | hasta 24 nov | Fase 0 · Fundaciones | Contrato OpenAPI, esqueleto backend, Git y App Shell |
| **Sprint 1** | 25 – 27 nov | Fase 1 · Núcleo | Auth, documentos, RAG y chat del tutor con streaming |
| **Sprint 2** | 28 – 29 nov | Fase 2 · Analítica | Riesgo con XAI, termómetro del aula, integración completa |
| **Entrega** | 30 nov | Fase 3 · Pulido | QA, despliegue, documentación y demo |

Para trabajar en paralelo: el frontend usa **mocks (MSW)** basados en el contrato mientras el backend no está listo, y se integra en el Sprint 2.

### Etiquetas
- **Fase:** `fase:0-fundaciones` · `fase:1-nucleo` · `fase:2-analitica` · `fase:3-entrega`
- **Área:** `area:frontend` · `area:backend` · `area:contrato` · `area:devops`
- **Prioridad:** `prioridad:alta` · `prioridad:media` · `prioridad:baja`
- `bloqueado` cuando una tarea depende de otra.

---

## 🤝 Cómo colaborar

Lee [`CONTRIBUTING.md`](CONTRIBUTING.md). Resumen:

1. Toma una issue de tu área y del sprint actual.
2. Crea una rama desde `develop`: `feat/fe-…`, `feat/be-…`, `fix/…`, `docs/…`.
3. Abre un PR hacia `develop` con `Closes #N`; la otra persona revisa.
4. `main` solo recibe `develop` al cerrar un sprint (y en la entrega).

---

## 🎨 Diseño

Estética Apple HIG + Silent Moon: tarjetas Bento `rounded-3xl`, modo noche (`#03174C`) y día (`#F6F7FB`), acentos `#8E97FD`, `#6CB28E`, `#FA6E5A`, `#FFCF86`, `#D9A5B3`. Detalles en [`CLAUDE.md`](CLAUDE.md).
