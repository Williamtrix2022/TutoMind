# 🧠 TutoMind · MVP

> **Documento vivo.** Es la fuente única para saber qué se tiene, qué falta y quién lo hace.
> Se actualiza **en el mismo PR** que cierra una tarea (ver [Cómo mantener este documento](#13-cómo-mantener-este-documento)).

| | |
|---|---|
| **Última actualización** | 2026-11-26 |
| **Sprint en curso** | Entrega · pulido y despliegue (hasta el 30 nov) |
| **Entrega** | 30 de noviembre de 2026 |
| **Tablero** | [Proyecto TutoMind · Roadmap](https://github.com/users/Williamtrix2022/projects/6) |
| **Issues** | [Ver issues](https://github.com/Williamtrix2022/TutoMind/issues) · [Sprints (milestones)](https://github.com/Williamtrix2022/TutoMind/milestones) |

Leyenda de estado: ✅ hecho · 🔄 en curso · ⬜ pendiente · ⛔ bloqueado

---

## 1. Resumen del MVP

TutoMind es una plataforma web educativa (PWA) integrada con **Moodle** que ofrece dos cosas:

1. **Tutor inteligente explicativo** basado en los documentos del curso (RAG): explica con claridad, con un ejemplo práctico y una pregunta de verificación, adapta la profundidad al nivel del alumno (básico, intermedio, avanzado), detecta frustración y permite pedir ayuda al docente.
2. **Dashboard predictivo de riesgo académico con explicabilidad (XAI)**: semáforo verde / amarillo / rojo por estudiante, con los factores exactos que justifican cada nivel, y un «termómetro del aula» con los temas más consultados y alertas de confusión.

**Incluido en el MVP**

| Estudiante | Docente |
|---|---|
| Login | Login |
| Chat con el tutor (streaming, Markdown, LaTeX, código) | Subir documentos del curso (PDF, DOCX, PPTX) |
| Nivel de explicación (básico / intermedio / avanzado) | Semáforo de riesgo con factores XAI y nota proyectada |
| Señales de frustración y botón de ayuda al docente | Termómetro del aula (temas y alertas de confusión) |

**Fuera del MVP** _(propuesta: confirmar entre los dos y ajustar)_: notificaciones push, gestión de múltiples cursos desde la interfaz, resaltado de sintaxis por colores en el código, modo offline avanzado.

---

## 2. Estado actual

**Progreso global: 28 de 29 tareas (97 %)**

`███████████████████░` 97 %

| Área | Estado | Detalle |
|---|---|---|
| **Contrato** (`docs/openapi.json`) | ✅ Listo | Los 5 endpoints definidos, más el `GET` de documentos ([#38](https://github.com/Williamtrix2022/TutoMind/pull/38)). Cambios solo por PR del contrato. |
| **Frontend** | ✅ Sprint 2 completo | Todas las pantallas (login, tutor, documentos, riesgo, temas e inicios por rol) con carga, vacío y error, y reintentos solo ante fallos de red o 5xx. Habla con el backend real por defecto (`NEXT_PUBLIC_USE_MOCKS=false`). Pruebas end-to-end con Playwright contra el backend real y auditoría de accesibilidad (axe) en 7 pantallas, 2 temas y móvil/escritorio, sin violaciones graves. |
| **Despliegue** | ✅ En línea | Frontend en https://tutomind.vercel.app, backend en https://tutomind-api-9o6i.onrender.com y base en Neon, todo en cuentas propias y gratis. Detalle en [`docs/DESPLIEGUE.md`](DESPLIEGUE.md). Las pruebas end-to-end pasan contra la URL pública. |
| **Backend** | ✅ Completo | Sprint 1 y Sprint 2 del backend completos (#12–#24): auth, documentos, tutor con RAG/SSE, frustración y tickets, riesgo con XAI, termómetro del aula y Moodle. Todos los endpoints del contrato están implementados. Funciona sin API key y sin Moodle (clientes offline/simulado); el cliente de Moodle real **no está probado contra un Moodle real** y Gemini real tampoco. |

> Todo el flujo (login, documentos, tutor, riesgo y temas) se probó con la interfaz contra el backend real: `cd frontend && npm run e2e` (ver sección 8). Lighthouse sobre la compilación de producción: accesibilidad, buenas prácticas y SEO en 100; rendimiento 100 en escritorio y 70 en móvil (hidratación de React con la CPU simulada 4× más lenta).

---

## 3. Equipo y responsabilidades

| Área | Carpeta | Responsable |
|---|---|---|
| Frontend (UI, PWA, integración) | `/frontend` | @Williamtrix2022 |
| Backend (API, RAG, riesgo XAI, Moodle) | `/backend` | @Jhon-Quiceno |
| Contrato de API | `/docs/openapi.json` | Ambos (revisión cruzada) |

---

## 4. Cronograma: sprints y fases

| Sprint | Fechas | Fase | Objetivo | Progreso |
|---|---|---|---|---|
| **Sprint 0** | hasta 24 nov | Fase 0 · Fundaciones | Contrato, esqueleto backend, Git y App Shell | ✅ 4 / 4 |
| **Sprint 1** | 25 – 27 nov | Fase 1 · Núcleo | Auth, documentos, RAG y chat del tutor | ✅ 14 / 14 |
| **Sprint 2** | 28 – 29 nov | Fase 2 · Analítica | Riesgo con XAI, temas, integración completa | ✅ 6 / 6 |
| **Entrega** | 30 nov | Fase 3 · Pulido | QA, despliegue, documentación y demo | 🔄 4 / 5 |

---

## 5. Tareas por sprint

### Sprint 0 · Fundaciones ✅

| # | Tarea | Área | Responsable | Estado | PR |
|---|---|---|---|---|---|
| [#1](https://github.com/Williamtrix2022/TutoMind/issues/1) | Contrato OpenAPI 3.1 base | Contrato | @Williamtrix2022 | ✅ | — |
| [#2](https://github.com/Williamtrix2022/TutoMind/issues/2) | Esqueleto de la carpeta `/backend` | Backend | @Williamtrix2022 | ✅ | — |
| [#3](https://github.com/Williamtrix2022/TutoMind/issues/3) | `.gitignore`, ramas y flujo de trabajo | Repo | @Williamtrix2022 | ✅ | [#30](https://github.com/Williamtrix2022/TutoMind/pull/30) |
| [#4](https://github.com/Williamtrix2022/TutoMind/issues/4) | Next.js 15, tokens Silent Moon, PWA y App Shell | Frontend | @Williamtrix2022 | ✅ | [#31](https://github.com/Williamtrix2022/TutoMind/pull/31) |

### Sprint 1 · Núcleo 🔄 (25 – 27 nov)

| # | Tarea | Área | Responsable | Estado | PR | Notas |
|---|---|---|---|---|---|---|
| [#5](https://github.com/Williamtrix2022/TutoMind/issues/5) | Color de riesgo alto (rojo) | Frontend | @Williamtrix2022 | ✅ | [#32](https://github.com/Williamtrix2022/TutoMind/pull/32) | `#E5484D` |
| [#6](https://github.com/Williamtrix2022/TutoMind/issues/6) | Tipos TS desde `openapi.json` y cliente de red | Frontend | @Williamtrix2022 | ✅ | [#32](https://github.com/Williamtrix2022/TutoMind/pull/32) | `npm run gen:api` |
| [#7](https://github.com/Williamtrix2022/TutoMind/issues/7) | Mocks de API (MSW) | Frontend | @Williamtrix2022 | ✅ | [#32](https://github.com/Williamtrix2022/TutoMind/pull/32) | `NEXT_PUBLIC_USE_MOCKS=true` |
| [#8](https://github.com/Williamtrix2022/TutoMind/issues/8) | Login y guardas de rol | Frontend | @Williamtrix2022 | ✅ | [#35](https://github.com/Williamtrix2022/TutoMind/pull/35) | Con mocks |
| [#9](https://github.com/Williamtrix2022/TutoMind/issues/9) | Chat del tutor: streaming, Markdown, KaTeX y código | Frontend | @Williamtrix2022 | ✅ | [#33](https://github.com/Williamtrix2022/TutoMind/pull/33) | Con mocks |
| [#10](https://github.com/Williamtrix2022/TutoMind/issues/10) | Señales de frustración y ayuda humana | Frontend | @Williamtrix2022 | ✅ | [#34](https://github.com/Williamtrix2022/TutoMind/pull/34) | Con mocks |
| [#11](https://github.com/Williamtrix2022/TutoMind/issues/11) | Pantalla de carga de documentos | Frontend | @Williamtrix2022 | ✅ | [#39](https://github.com/Williamtrix2022/TutoMind/pull/39) | Con mocks; usa el nuevo `GET` ([#38](https://github.com/Williamtrix2022/TutoMind/pull/38)) |
| [#12](https://github.com/Williamtrix2022/TutoMind/issues/12) | App FastAPI: config, CORS, health y errores | Backend | @Jhon-Quiceno | ✅ | [#41](https://github.com/Williamtrix2022/TutoMind/pull/41) | **Empezar aquí** |
| [#13](https://github.com/Williamtrix2022/TutoMind/issues/13) | Modelos Pydantic v2 alineados con el contrato | Backend | @Jhon-Quiceno | ✅ | [#42](https://github.com/Williamtrix2022/TutoMind/pull/45) | |
| [#14](https://github.com/Williamtrix2022/TutoMind/issues/14) | PostgreSQL + pgvector (docker-compose y migraciones) | Backend | @Jhon-Quiceno | ✅ | [#43](https://github.com/Williamtrix2022/TutoMind/pull/45) | |
| [#15](https://github.com/Williamtrix2022/TutoMind/issues/15) | `POST /auth/login` con JWT y roles | Backend | @Jhon-Quiceno | ✅ | [#44](https://github.com/Williamtrix2022/TutoMind/pull/45) | |
| [#16](https://github.com/Williamtrix2022/TutoMind/issues/16) | `POST /courses/{id}/documents`: ingesta y embeddings | Backend | @Jhon-Quiceno | ✅ | [#49](https://github.com/Williamtrix2022/TutoMind/pull/49) | Incluye el nuevo `GET` de lista y estados ([#38](https://github.com/Williamtrix2022/TutoMind/pull/38)) |
| [#17](https://github.com/Williamtrix2022/TutoMind/issues/17) | `POST /tutor/chat/stream`: RAG socrático con SSE | Backend | @Jhon-Quiceno | ✅ | [#51](https://github.com/Williamtrix2022/TutoMind/pull/51) | La más pesada |
| [#18](https://github.com/Williamtrix2022/TutoMind/issues/18) | Detección de frustración y escalamiento a humano | Backend | @Jhon-Quiceno | ✅ | [#51](https://github.com/Williamtrix2022/TutoMind/pull/51) | |

### Sprint 2 · Analítica 🔄 (28 – 29 nov)

| # | Tarea | Área | Responsable | Estado | PR |
|---|---|---|---|---|---|
| [#19](https://github.com/Williamtrix2022/TutoMind/issues/19) | Dashboard de riesgo con semáforo y panel XAI | Frontend | @Williamtrix2022 | ✅ | [#53](https://github.com/Williamtrix2022/TutoMind/pull/53) |
| [#20](https://github.com/Williamtrix2022/TutoMind/issues/20) | Termómetro del aula: temas y alertas de confusión | Frontend | @Williamtrix2022 | ✅ | [#54](https://github.com/Williamtrix2022/TutoMind/pull/54) |
| [#21](https://github.com/Williamtrix2022/TutoMind/issues/21) | Integración real con el backend y manejo de errores | Frontend | @Williamtrix2022 | ✅ | [#56](https://github.com/Williamtrix2022/TutoMind/pull/56) |
| [#22](https://github.com/Williamtrix2022/TutoMind/issues/22) | Servicio de riesgo con explicabilidad (XAI) | Backend | @Jhon-Quiceno | ✅ | [#58](https://github.com/Williamtrix2022/TutoMind/pull/58) |
| [#23](https://github.com/Williamtrix2022/TutoMind/issues/23) | `GET /analytics/.../topics`: agregación y confusión | Backend | @Jhon-Quiceno | ✅ | [#59](https://github.com/Williamtrix2022/TutoMind/pull/59) |
| [#24](https://github.com/Williamtrix2022/TutoMind/issues/24) | Integración con Moodle (eventos y enlaces) | Backend | @Jhon-Quiceno | ✅ | [#60](https://github.com/Williamtrix2022/TutoMind/pull/60) |

### Entrega · 30 nov 🔄

| # | Tarea | Área | Responsable | Estado | PR |
|---|---|---|---|---|---|
| [#25](https://github.com/Williamtrix2022/TutoMind/issues/25) | Pruebas end-to-end del flujo completo | Ambos | @Williamtrix2022 | ✅ | [#61](https://github.com/Williamtrix2022/TutoMind/pull/61) |
| [#26](https://github.com/Williamtrix2022/TutoMind/issues/26) | Auditoría PWA, accesibilidad y rendimiento | Frontend | @Williamtrix2022 | ✅ | [#61](https://github.com/Williamtrix2022/TutoMind/pull/61) |
| [#27](https://github.com/Williamtrix2022/TutoMind/issues/27) | Despliegue de frontend y backend | DevOps | @Williamtrix2022 | ✅ | [#64](https://github.com/Williamtrix2022/TutoMind/pull/64) |
| [#28](https://github.com/Williamtrix2022/TutoMind/issues/28) | README final, guion de demo y presentación | Docs | @Williamtrix2022 | ✅ | [#65](https://github.com/Williamtrix2022/TutoMind/pull/65) |
| [#29](https://github.com/Williamtrix2022/TutoMind/issues/29) | Merge `develop` → `main` y etiqueta `v0.1.0` | Release | @Williamtrix2022 | ⬜ | — |

---

## 6. Matriz de integración por endpoint

Esta es la vista clave para coordinar: **qué existe de cada endpoint en cada lado**.
«Frontend» indica si la pantalla o el hook ya consumen el endpoint (hoy contra mocks).
«Integrado» pasa a ✅ solo cuando el frontend funciona contra el backend real.

| Endpoint | Contrato | Frontend | Backend | Integrado |
|---|---|---|---|---|
| `POST /api/v1/auth/login` | ✅ | ✅ pantalla + hook | ✅ #15 | ✅ e2e: login de docente y estudiante, contraseña incorrecta y backend caído |
| `POST /api/v1/courses/{course_id}/documents` | ✅ | ✅ pantalla con subida y progreso | ✅ #16 | ✅ e2e: sube un PDF hasta *Indexado*; rechaza tipos no permitidos |
| `GET /api/v1/courses/{course_id}/documents` _(nuevo)_ | ✅ [#38](https://github.com/Williamtrix2022/TutoMind/pull/38) | ✅ lista y estados | ✅ #16 | ✅ e2e: lista y estados; 403 para estudiantes |
| `POST /api/v1/tutor/chat/stream` | ✅ | ✅ chat + frustración + ayuda | ✅ #17, #18 | ✅ e2e: respuesta en streaming y ayuda ante frustración (cliente offline; Gemini real sin probar) |
| `GET /api/v1/analytics/courses/{course_id}/risk` | ✅ | ✅ dashboard (#19) | ✅ #22 | ✅ e2e: semáforo, lista ordenada, filtro y panel XAI con datos reales |
| `GET /api/v1/analytics/courses/{course_id}/topics` | ✅ | ✅ termómetro (#20) | ✅ #23 | ✅ e2e: alerta de confusión y preguntas de ejemplo |

«✅» = la interfaz funciona contra el backend real, comprobado con las pruebas end-to-end (`npm run e2e`). El tutor corre con el cliente offline hasta que haya una clave de Gemini válida.

---

## 7. Contrato de API

- **Fuente única de verdad:** [`docs/openapi.json`](openapi.json) (OpenAPI 3.1).
- El frontend genera sus tipos con `npm run gen:api`; el backend alinea sus modelos Pydantic v2 con el mismo archivo.
- **Para cambiar un endpoint:** PR **solo con el cambio del contrato** (etiqueta `area:contrato`), aprobado por la otra persona **antes** de implementar.
- Formato de error común: `ErrorResponse { code, message, details? }`.
- El chat responde por **SSE** (`text/event-stream`); cada evento es `data: {json}` + línea en blanco. Tipos de evento: `token`, `sources`, `frustration`, `escalation`, `done`, `error`.
- Valores del nivel del alumno: `basic | intermediate | advanced`. Riesgo: `green | yellow | red`. Estado de documento: `queued | processing | indexed | failed`.
- Documentos: máximo **20 MB** (413) y solo PDF, DOCX o PPTX (415). El estado avanza `queued → processing → indexed | failed`; el frontend consulta el `GET` cada ~3 s mientras haya documentos en proceso.

---

## 8. Cómo ejecutar y probar

### Backend
```bash
cd backend
cp .env.example .env                 # opcional: GEMINI_API_KEY (sin clave usa el cliente offline)
docker compose up -d db              # PostgreSQL + pgvector
alembic upgrade head                 # esquema
python -m app.db.seed                # 1 curso (`demo`), 1 docente y 5 estudiantes
uvicorn app.main:app --reload        # http://localhost:8000/docs
```
- Si el puerto 5432 está ocupado (p. ej. un PostgreSQL de Windows), usa `POSTGRES_PORT=5433` y el mismo puerto en `DATABASE_URL`.
- Usuarios demo: `docente@tutomind.demo` y `ana@tutomind.demo` con la contraseña `demo12345`.
- Tests: `pytest` (los de base de datos usan `TEST_DATABASE_URL` o un Postgres embebido con `pgserver`, que pide Python 3.12).

### Frontend
```bash
cd frontend
cp .env.example .env.local     # NEXT_PUBLIC_API_URL=http://localhost:8000, mocks apagados
npm install
npm run dev                    # http://localhost:3000
```
Con el backend encendido, entra con los usuarios demo de arriba.

**Sin backend (mocks):** pon `NEXT_PUBLIC_USE_MOCKS=true` y reinicia `npm run dev`.
- **Login:** cualquier correo válido con contraseña de 8+ caracteres. La contraseña `incorrecta` simula el error.
- **Frustración:** en el chat escribe «No entiendo nada» para ver el modo calmado y el banner de apoyo.
- **Ayuda humana:** el botón del salvavidas devuelve el ticket `T-1024`.
- **Documentos:** como docente, sube un PDF, DOCX o PPTX (hasta 20 MB) y mira el estado avanzar; un archivo con `fallo` en el nombre termina en *Falló*.
- **Rol docente:** cambia el selector «Rol de la demo» para ver Riesgo, Temas y Documentos.
- Los mocks (`frontend/src/mocks/handlers.ts` y `fixtures.ts`) sirven de referencia de las respuestas que el frontend espera.

**Validar el frontend:** `npx tsc --noEmit`, `npm run lint` y las pruebas end-to-end.
- `npm run e2e`: Playwright contra el backend real (necesita base de datos con seed y `uvicorn` en el puerto 8000; levanta el frontend si no está encendido). Cubre docente, estudiante, errores y la auditoría de accesibilidad (axe, WCAG 2.1 A y AA, en claro y oscuro). `--project=escritorio` o `--project=movil` para uno solo.
- `npm run e2e:capturas`: guarda capturas de cada pantalla en `frontend/e2e/screenshots/` para revisar el diseño.
- La prueba de subida deja un `apuntes-e2e-*.pdf` en el curso de demo; bórralo de la tabla `documents` o recrea la base para limpiar.
- Lighthouse: `NEXT_DIST_DIR=.next-prod npm run build` y `NEXT_DIST_DIR=.next-prod npx next start -p 3100` (no pisa la carpeta de `npm run dev`).
- Iconos de la PWA: `node scripts/generate-icons.mjs` los regenera desde el logo.

---

## 9. Decisiones tomadas

| Fecha | Decisión | Motivo |
|---|---|---|
| 2026-11-24 | Rojo del semáforo: `#E5484D` | `#FA6E5A` ya era «riesgo medio»; este se distingue y mantiene la calma de la paleta. |
| 2026-11-26 | Riesgo medio en amarillo `#F4B63F` (antes `#FA6E5A`) | El semáforo debe leerse verde, amarillo y rojo. `#FFCF86` sigue reservado para alertas de confusión; el texto usa tintas más oscuras en modo día para mantener el contraste. |
| 2026-11-26 | Logo «T neuronal» (`LogoMark`) en lugar del ícono de luna | Marca propia: arco (aula), tronco (tutor) y nodos (ideas conectadas), con la chispa de la IA en el centro. |
| 2026-11-26 | Inicio con contenido propio por rol: estudiante (orbe, preguntas sugeridas, guía del tutor, bloque de estudio 25/5) y docente (mosaico con riesgo, confusión, factores y documentos) | El inicio era una lista de enlaces. El estudiante no tiene endpoint propio de progreso, así que solo muestra lo que no necesita datos inventados; el temporizador es local. Las preguntas sugeridas abren `/tutor?q=…` y se envían solas. |
| 2026-11-24 | Mocks con MSW 2.x (no 3.x) | La 3.x es reciente y su export de navegador falla con webpack. |
| 2026-11-24 | Frontend trabaja con mocks hasta el Sprint 2 | Desbloquea al frontend mientras el backend arranca. |
| 2026-11-25 | Rutas en grupos `(app)` con shell y `(auth)` sin shell | El login no debe mostrar la barra lateral. |
| 2026-11-25 | Guarda de rol en la interfaz es solo de UX | La autorización real la aplica el backend (403). |
| 2026-11-25 | Token de sesión en `localStorage` (por ahora) | Simple para el MVP; ver pendiente de cookie `httpOnly`. |
| 2026-11-25 | Añadir `GET /courses/{id}/documents` al contrato ([#38](https://github.com/Williamtrix2022/TutoMind/pull/38)) | Sin él no hay lista ni estados de indexación. |
| 2026-11-25 | Archivos: máximo 20 MB; tipos PDF, DOCX y PPTX | Cubre el material típico de clase; mismo límite en frontend y backend. |
| 2026-11-25 | Subida con XHR en lugar de `fetch` | `fetch` no informa el progreso de subida. |
| 2026-11-25 | Embeddings con `HashingEmbedder` (offline, sin API key) mientras no haya proveedor | Permite desarrollar y probar todo el RAG; es léxico, no semántico. Cambiarlo es un solo punto (`get_embedder`). Dimensión 1024. |
| 2026-11-25 | Sin `GEMINI_API_KEY` el backend usa un cliente offline (embeddings léxicos y tutor de reglas) | Permite desarrollar y probar todo sin claves ni costo. La calidad real del tutor exige la clave (nivel gratuito: solo documentos de demo). |
| 2026-11-25 | Frustración por reglas, no por modelo | Transparente, gratis y testeable; `repeated_failure` queda sin detectar. Escala por petición explícita o si está frustrado ahora y en ≥ 2 de sus últimos 3 mensajes. |
| 2026-11-25 | Petición de ayuda humana responde con un acuse fijo, sin llamar al modelo | Ahorra costo y es predecible; el evento `escalation` trae `ticket_id`. |
| 2026-11-25 | Errores de la API son JSON (`ErrorResponse`) también en el endpoint SSE | El frontend los trata igual que el resto; el evento SSE `error` no incluye detalles internos. |
| 2026-11-26 | Riesgo con reglas ponderadas y explicables (no un modelo entrenado) | No hay histórico etiquetado y el docente debe poder leer por qué se marca a alguien. `risk_score = 0.5 + Σ impact`; verde < 0.40 ≤ amarillo < 0.65 ≤ rojo. Pesos y umbrales son una primera calibración (ver README del backend). |
| 2026-11-26 | El tema de una pregunta es el documento del curso que la respalda (sin modelo) | Gratis, explicable y funciona sin API key. Es grueso (1 documento = 1 tema); si hace falta más detalle, se sustituye `topic_for` por un extractor con Gemini. Alerta de confusión: ≥ 0.5 con ≥ 3 preguntas. |
| 2026-11-26 | Moodle: ingesta idempotente por correo y datos simulados que se renuevan (no se acumulan) | Permite desarrollar y demostrar sin Moodle, avisando siempre. El cliente real no está probado contra un Moodle real; los eventos simulados llevan `source = 'simulated'` y nunca tocan datos reales. |
| 2026-11-25 | Indexación con tareas en segundo plano de FastAPI | Sin infraestructura extra para el MVP. Límite conocido: si el servidor se reinicia a mitad, el documento queda en `processing`. |
| 2026-11-25 | Login real: el `role` del cuerpo solo confirma el de la cuenta; el rol de las rutas se lee de la base de datos | Evita escalar privilegios con un token o un campo manipulado ([#15](https://github.com/Williamtrix2022/TutoMind/issues/15)). Para el demo, usuarios sembrados: `docente@tutomind.demo`, `ana@tutomind.demo`… con `demo12345`. |
| 2026-11-27 | Tutor explicativo y cercano, no socrático | La demostración mostró que evadir respuestas y repetir plantillas frustra. Ahora cada respuesta valida, explica, da un ejemplo y verifica. Solo ante un trabajo calificado para entregar explica y resuelve un ejemplo análogo. |
| 2026-11-27 | El docente se ofrece como última instancia y el ticket se crea al confirmar | Solo si el estudiante sigue sin entender tras 2 explicaciones o su frustración persiste. Ofrecer no es escalar: el evento llega sin `ticket_id` y el ticket nace cuando el estudiante acepta. |
| 2026-11-27 | Relevancia del material por tipo de embedder | Con Gemini: distancia máxima y margen. El embedder offline casi no separa temas por distancia: ahí se exige vocabulario poco común compartido (tipo IDF). Primera calibración; ajustar con datos reales. |
| 2026-11-26 | Mocks apagados por defecto; la interfaz habla con el backend real | Es la integración (#21). Los mocks siguen disponibles con `NEXT_PUBLIC_USE_MOCKS=true` para trabajar sin backend. |
| 2026-11-26 | Reintentos solo ante caídas de red y errores 5xx (hasta 2, con espera de 1 s y 2 s) | Un 4xx (credenciales, permisos, no existe) da el mismo resultado al repetirlo. Un servidor apagado se muestra como «No pudimos conectar con el servidor» y no como «Failed to fetch». |
| 2026-11-26 | IA gratuita: Google Gemini (`gemini-2.5-flash` + `gemini-embedding-001` a 1024 dims) en lugar de la API de Anthropic | El MVP debe costar cero. El nivel gratuito puede usar los datos para mejorar modelos: **solo documentos de demo**. Detrás de `LLMClient` (`backend/app/services/llm.py`) para poder cambiar de proveedor. |

---

## 10. Pendientes por acordar con el backend

| # | Tema | Qué necesita el frontend |
|---|---|---|
| 1 | **Ayuda humana** | Al enviar `request_human_help: true`, el evento `escalation` debe traer `ticket_id`. El frontend confirma la solicitud solo con ese id. |
| 2 | **401 vs 403** | `401` = sesión inválida (el frontend cierra sesión). `403` = sin permiso por rol. |
| 3 | **Formato SSE** | `data: {json}\n\n` por evento, y `done` al final con `conversation_id`. |
| 4 | **XAI** | Confirmar el significado de `impact` (−1 a 1; positivo = aumenta el riesgo) y que cada estudiante traiga al menos un factor. |
| 5 | **Token de sesión** | Valorar cookie `httpOnly` emitida por el backend en lugar de `localStorage`. |
| 6 | **CORS** | Permitir `http://localhost:3000` en desarrollo y el dominio de despliegue en producción. |
| 7 | **Rol en login** | El campo `role` del login es solo para demo; en producción lo define Moodle. |
| 8 | **Documentos** | Aprobar el `GET /courses/{course_id}/documents` ([#38](https://github.com/Williamtrix2022/TutoMind/pull/38)); avanzar el estado `queued → processing → indexed \| failed` y devolver `error_message` si falla; aplicar 20 MB (413) y tipos permitidos (415). |

---

## 11. Riesgos y bloqueos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Backend sin arrancar con la entrega en 5 días | Alto | Empezar por #12 → #15 hoy; el frontend avanza con mocks. |
| RAG y streaming (#17) es la tarea más pesada | Alto | Entregar primero una versión mínima (recuperación + respuesta) y refinar después. |
| Moodle real puede no estar disponible | Medio | Plan B: datos simulados documentados (#24). |
| Render gratis duerme el servidor tras ~15 min sin uso | Medio | La primera petición tarda hasta un minuto. El login lo despierta al abrirse y avisa; abrir la pantalla un par de minutos antes de la demostración. |
| La clave de Gemini devuelve 403 «free tier not available for this project» | Medio | Crear la clave en https://aistudio.google.com/apikey con un proyecto nuevo creado desde AI Studio, o dejar `GEMINI_API_KEY` vacío para usar el cliente offline. El tutor real queda sin probar hasta entonces. |
| Integración tarde (Sprint 2) | Medio | Contrato estable y matriz de integración revisada a diario. |

---

## 12. Registro de cambios

Más reciente primero.

### 2026-11-27
- Gemini real activo: clave nueva válida y modelo `gemini-3.5-flash-lite` por defecto (el 2.5 ya no está disponible para cuentas nuevas y los flash normales tardan 24 s o más) — PR_GEM.
- Despliegue migrado a cuentas propias: Neon nuevo, Render creado desde `render.yaml` sobre `main` y frontend apuntando al servidor nuevo; pruebas end-to-end 10 de 10 contra el sitio.
- Ajustes del tutor tras verlo desplegado: el offline no busca material en mensajes frustrados y pregunta qué parte se complica, no cuela documentos por una palabra suelta, no repite la misma respuesta empática y el número de solicitud es corto — [#71](https://github.com/Williamtrix2022/TutoMind/pull/71), [#73](https://github.com/Williamtrix2022/TutoMind/pull/73), [#74](https://github.com/Williamtrix2022/TutoMind/pull/74).
- Frontend alineado con el tutor explicativo: la oferta del docente aparece solo cuando el servidor la sugiere y pide confirmación, textos del inicio y del chat, mocks, prueba e2e y diapositivas — [#69](https://github.com/Williamtrix2022/TutoMind/pull/69).
- Tutor explicativo y cercano en lugar de socrático; modo offline que presenta el material con formato limpio; filtro de relevancia del material (no mezcla materias); el docente se ofrece solo como última instancia y el ticket se crea al confirmar — [#67](https://github.com/Williamtrix2022/TutoMind/pull/67).

### 2026-11-26
- README final, [guion de la demostración](GUION_DEMO.md) y diapositivas (10 láminas; el enlace es privado hasta que se comparta desde su menú *Share*) (#28) — [#65](https://github.com/Williamtrix2022/TutoMind/pull/65).
- Despliegue gratuito publicado (#27): Vercel + Render + Neon; las pruebas end-to-end pasan contra la URL pública. Al desplegar se encontró y corrigió que `httpx` faltaba en las dependencias de producción — [#64](https://github.com/Williamtrix2022/TutoMind/pull/64).
- Preparación del despliegue gratuito (#27): `render.yaml`, guía [`docs/DESPLIEGUE.md`](DESPLIEGUE.md), URL de base de datos con cualquier esquema, contraseña de demo por `DEMO_PASSWORD`, aviso de arranque en frío en el login y PDF de ejemplo del curso en `docs/demo/` — [#62](https://github.com/Williamtrix2022/TutoMind/pull/62).
- Pruebas end-to-end con Playwright contra el backend real, auditoría de accesibilidad con axe (contraste y nombres accesibles corregidos), Lighthouse y nuevos iconos de la PWA (#25, #26) — [#61](https://github.com/Williamtrix2022/TutoMind/pull/61).
- Backend: integración con Moodle (cliente de Web Services, ingesta idempotente de eventos, enlaces en las citas y datos simulados documentados) (#24) — [#60](https://github.com/Williamtrix2022/TutoMind/pull/60).
- Backend: temas y termómetro del aula con alertas de confusión; tema por pregunta guardado en cada mensaje (#23) — [#59](https://github.com/Williamtrix2022/TutoMind/pull/59).
- Backend: riesgo académico con explicabilidad XAI, modelo de reglas ponderadas, y guardado de la frustración por mensaje (#22) — [#58](https://github.com/Williamtrix2022/TutoMind/pull/58).
- Integración real: mocks apagados por defecto, error de red legible y reintentos solo ante fallos recuperables (#21) — [#56](https://github.com/Williamtrix2022/TutoMind/pull/56).
- Inicio rediseñado para estudiante (orbe, preguntas sugeridas, guía del tutor, bloque de estudio) y docente (mosaico con datos reales) — [#55](https://github.com/Williamtrix2022/TutoMind/pull/55).
- Termómetro del aula con alertas de confusión (#20) — [#54](https://github.com/Williamtrix2022/TutoMind/pull/54).
- Dashboard de riesgo con semáforo y panel XAI, logo nuevo y riesgo medio en amarillo (#19) — [#53](https://github.com/Williamtrix2022/TutoMind/pull/53).
- Puerto de PostgreSQL configurable con `POSTGRES_PORT` — [#52](https://github.com/Williamtrix2022/TutoMind/pull/52).
- IA gratuita con Google Gemini en lugar de Anthropic — [#46](https://github.com/Williamtrix2022/TutoMind/pull/46).

### 2026-11-25
- Backend: detección de frustración y escalamiento a docente con tickets (#18) — [#51](https://github.com/Williamtrix2022/TutoMind/pull/51).
- Backend: tutor socrático con RAG y SSE (#17) — [#51](https://github.com/Williamtrix2022/TutoMind/pull/51).
- Backend: subida, extracción, chunking e indexación de documentos con embeddings en pgvector (#16) — [#49](https://github.com/Williamtrix2022/TutoMind/pull/49).
- Backend: POST /auth/login con JWT y dependencias de rol (#15) — [#44](https://github.com/Williamtrix2022/TutoMind/pull/44).
- Backend: PostgreSQL + pgvector, migraciones Alembic y seeds de demo (#14) — [#43](https://github.com/Williamtrix2022/TutoMind/pull/43).
- Backend: modelos Pydantic v2 alineados con el contrato, con test de contrato (#13) — [#42](https://github.com/Williamtrix2022/TutoMind/pull/42).
- Backend: app FastAPI con config, CORS, health y errores ErrorResponse (#12) — [#41](https://github.com/Williamtrix2022/TutoMind/pull/41).
- Pantalla de carga de documentos del curso — [#39](https://github.com/Williamtrix2022/TutoMind/pull/39).
- Contrato: `GET /courses/{id}/documents` y límite de 20 MB — [#38](https://github.com/Williamtrix2022/TutoMind/pull/38) _(en revisión)_.
- Se crea este documento (`docs/TutoMind_Mvp.md`) — [#37](https://github.com/Williamtrix2022/TutoMind/pull/37).
- Login, sesión y guardas de rol — [#35](https://github.com/Williamtrix2022/TutoMind/pull/35).

### 2026-11-24
- Señales de frustración y botón de ayuda al docente — [#34](https://github.com/Williamtrix2022/TutoMind/pull/34).
- Chat del tutor con streaming, Markdown, KaTeX y copiar código — [#33](https://github.com/Williamtrix2022/TutoMind/pull/33).
- Cliente de API tipado, mocks MSW y color de riesgo alto — [#32](https://github.com/Williamtrix2022/TutoMind/pull/32).
- Next.js 15, tokens Silent Moon, PWA y App Shell — [#31](https://github.com/Williamtrix2022/TutoMind/pull/31).
- README con plan de sprints, CONTRIBUTING y plantillas — [#30](https://github.com/Williamtrix2022/TutoMind/pull/30).
- Contrato OpenAPI 3.1, esqueleto de `/backend`, `.gitignore` y ramas `main` / `develop`.

---

## 13. Cómo mantener este documento

**Regla de oro:** quien cierra una tarea actualiza este documento **en el mismo PR**. Sea frontend o backend.

Checklist al terminar una tarea:
1. **Sección 5:** cambia el estado de la fila a ✅ y pon el enlace al PR.
2. **Sección 4 y 2:** actualiza el contador del sprint y el progreso global (`X de 29`, porcentaje).
3. **Sección 6:** si la tarea toca un endpoint, actualiza su fila (Frontend / Backend / Integrado).
4. **Sección 12:** añade una línea en el registro de cambios, con fecha y enlace al PR.
5. **Secciones 9 y 10:** anota las decisiones nuevas o resuelve los pendientes.
6. Actualiza la fecha de **Última actualización** y el **Sprint en curso**.

Reglas adicionales:
- Mientras una tarea esté en curso, márcala 🔄; si algo la bloquea, ⛔ y explica en Notas.
- Los PRs van a `develop`, y GitHub **solo cierra las issues automáticamente al llegar a `main`**. Por eso, al fusionar un PR hay que **cerrar la issue a mano** y pasar su tarjeta del [tablero](https://github.com/users/Williamtrix2022/projects/6) a *Done*.
- Si el documento y el tablero se contradicen, gana lo que diga el código fusionado en `develop`; corrige el otro.
