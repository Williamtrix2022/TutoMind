# 🧠 TutoMind — Tutor Inteligente & Analítica Predictiva XAI

Plataforma web educativa (PWA) que combina **tutoría con IA** (RAG sobre el material del curso) y un **dashboard de riesgo académico explicable (XAI)**, pensada para integrarse con Moodle.

### 👉 Pruébalo ahora
**https://tutomind.vercel.app**

| Rol | Correo | Qué ve |
|---|---|---|
| Docente | `docente@tutomind.demo` | Riesgo por estudiante con factores XAI, termómetro del aula y documentos |
| Estudiante | `ana@tutomind.demo` | Tutor con streaming, ayuda del docente y bloque de estudio |

La contraseña de las cuentas de demo se entrega en privado. Elige el rol en el selector de la pantalla de login.

> **La primera vez puede tardar hasta un minuto:** el servidor gratuito se duerme tras 15 minutos sin uso y la pantalla de login lo despierta al abrirse. Si ves «El servidor está despertando», espera.

📋 [Estado del MVP](docs/TutoMind_Mvp.md) · 🎬 [Guion de la demo](docs/GUION_DEMO.md) · 🚀 [Despliegue](docs/DESPLIEGUE.md) · 📑 [Contrato de API](docs/openapi.json)

---

## ✨ Qué hace

### 🎓 Para estudiantes
* **Tutor explicativo y cercano:** responde con el material que sube el docente (y lo completa con su conocimiento si es breve) y cita sus fuentes. Cada respuesta tiene una validación breve, una explicación paso a paso, **un ejemplo práctico** y una pregunta para comprobar que se entendió.
* **Tres niveles de explicación:** básico, intermedio y avanzado.
* **Detección de frustración:** si el estudiante se frustra, el tutor adapta el tono y baja el ritmo.
* **El docente, como última instancia:** solo si el estudiante dice que sigue sin entender tras dos explicaciones, o su frustración persiste, el tutor le ofrece enviar la duda y la conversación al docente. **La solicitud se registra únicamente si el estudiante acepta**, y se refleja en el riesgo del curso.
* **Formato académico:** Markdown, fórmulas LaTeX (KaTeX) y bloques de código con botón de copiar.

### 👩‍🏫 Para docentes
* **Documentos del curso:** sube PDF, DOCX o PPTX (hasta 20 MB); se indexan en una base vectorial.
* **Semáforo de riesgo con XAI:** verde, amarillo y rojo por estudiante, con **los factores exactos** que explican cada nivel (cuánto aporta cada uno) y la nota proyectada.
* **Termómetro del aula:** temas más consultados y alertas de confusión grupal, con preguntas de ejemplo.

---

## 🏗️ Arquitectura

```text
Navegador (PWA) ──► Vercel: Next.js 15 ──► Render: FastAPI ──► Neon: PostgreSQL + pgvector
                                                │
                                                ├─► Google Gemini (tutor y embeddings, nivel gratuito)
                                                └─► Moodle (Web Services; hoy datos simulados)
```

```text
tutomind/
├── frontend/   Next.js 15 · TypeScript estricto · Tailwind · Motion · TanStack Query · Playwright
├── backend/    FastAPI · Python 3.12 · Pydantic v2 · SQLAlchemy · Alembic · pgvector
├── docs/       Contrato OpenAPI, estado del MVP, guion de demo, despliegue y PDF de ejemplo
└── .github/    Plantillas de issues y pull requests
```

El contrato [`docs/openapi.json`](docs/openapi.json) es la **fuente única de verdad** entre frontend y backend: el frontend genera sus tipos con `npm run gen:api` y el backend valida con modelos Pydantic alineados al mismo archivo (hay un test que los compara).

| Endpoint | Descripción |
|---|---|
| `POST /api/v1/auth/login` | Login con rol `student` o `teacher` (JWT) |
| `GET/POST /api/v1/courses/{course_id}/documents` | Lista y subida de PDF/DOCX/PPTX |
| `POST /api/v1/tutor/chat/stream` | Chat del tutor por SSE (fuentes, frustración, escalamiento) |
| `GET /api/v1/analytics/courses/{course_id}/risk` | Semáforo de riesgo con factores XAI |
| `GET /api/v1/analytics/courses/{course_id}/topics` | Temas más consultados y alertas de confusión |

---

## ⚖️ Qué es y qué no es (límites honestos)

* **El riesgo es un modelo de reglas ponderadas, no un modelo predictivo entrenado.** Es transparente y verificable (el puntaje es exactamente la suma de los factores), pero los pesos y umbrales son una primera calibración que debe ajustarse con datos reales.
* **Moodle es simulado.** El cliente de Web Services está escrito y probado contra un Moodle simulado; **no se ha ejecutado contra un Moodle real**. Sin `MOODLE_BASE_URL` se usan datos de demostración y la aplicación lo avisa.
* **El tutor depende de la clave de Gemini.** Sin clave funciona con un cliente offline: no razona, pero presenta con formato limpio los fragmentos relevantes de tu material (con su fuente) y avisa cuando el curso no cubre la pregunta. Sirve para probar y demostrar el flujo, pero es menos capaz. El nivel gratuito de Google puede usar lo que se envíe para mejorar sus modelos: **usa solo material de demostración**.
* **El tema de cada pregunta es el documento más cercano**, no el concepto. La alerta de confusión exige al menos 3 preguntas de varios estudiantes.
* **Servidor gratuito:** se duerme sin uso (primera respuesta lenta) y no es para cargas reales.

---

## 🚀 Ejecutarlo en tu máquina

Necesitas Node 20+, Python 3.12 y Docker.

```bash
# 1. Base de datos (PostgreSQL + pgvector)
cd backend
cp .env.example .env            # opcional: GEMINI_API_KEY (sin clave usa el cliente offline)
docker compose up -d db         # si el 5432 está ocupado: POSTGRES_PORT=5433 y el mismo puerto en DATABASE_URL
pip install -r requirements.txt
alembic upgrade head && python -m app.db.seed

# 2. Backend  →  http://localhost:8000/docs
uvicorn app.main:app --reload

# 3. Frontend  →  http://localhost:3000   (en otra terminal)
cd frontend
cp .env.example .env.local      # NEXT_PUBLIC_API_URL=http://localhost:8000
npm install && npm run dev
```

Usuarios de desarrollo (los crea el seed): `docente@tutomind.demo` y `ana@tutomind.demo`, contraseña `demo12345`. Sin backend, `NEXT_PUBLIC_USE_MOCKS=true` usa respuestas simuladas.

### Pruebas
```bash
cd backend && pytest             # ~420 tests (los de base de datos usan TEST_DATABASE_URL)
cd frontend && npm run e2e       # Playwright contra el backend real + accesibilidad (axe)
```
Detalles, Lighthouse y cómo recrear los iconos en [`docs/TutoMind_Mvp.md`](docs/TutoMind_Mvp.md#8-cómo-ejecutar-y-probar).

**Calidad medida:** Lighthouse (producción) en accesibilidad, buenas prácticas y SEO: 100; rendimiento: 100 en escritorio y 70 en móvil. Auditoría axe WCAG 2.1 AA sin violaciones graves en 7 pantallas, 2 temas y móvil/escritorio.

---

## 👥 Equipo

| Área | Carpeta | Responsable |
|---|---|---|
| Frontend, QA, despliegue y documentación | `/frontend`, `/docs` | @Williamtrix2022 |
| Backend (API, RAG, riesgo XAI, Moodle) | `/backend` | @Jhon-Quiceno |
| Contrato de API | `/docs/openapi.json` | Ambos (revisión cruzada) |

Flujo de trabajo en [`CONTRIBUTING.md`](CONTRIBUTING.md): ramas `feat/…` desde `develop`, PR con `Closes #N` y revisión cruzada; `main` solo recibe `develop` al cerrar un sprint.

---

## 🎨 Diseño

Estética Apple HIG + Silent Moon: tarjetas Bento `rounded-3xl`, modo noche (`#03174C`) y día (`#F6F7FB`), acento `#8E97FD`, semáforo verde `#6CB28E`, amarillo `#F4B63F` y rojo `#E5484D`, alerta de confusión `#FFCF86` y brillo de IA `#D9A5B3`. Movimiento con resortes, feedback táctil en cada botón y respeto por `prefers-reduced-motion`. Reglas completas en [`CLAUDE.md`](CLAUDE.md).
