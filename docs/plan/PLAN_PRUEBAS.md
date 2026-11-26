# Plan de pruebas — TutoMind

Punto de partida verificado:
- Frontend: **no tiene test runner** (`package.json` solo define `dev`, `build`, `start`, `lint`, `gen:api`). Los checks existentes son `tsc`, `eslint`, `next build`.
- Backend: sin código ni tests aún.
- El PR #39 afirma "17 comprobaciones" en Edge; son manuales y no quedan en el repo.

## 1. Resultados ya ejecutados sobre el PR #39

Ejecutado en un worktree aislado (Node 24.19, `npm ci`). Ya eliminado.

| Check | Resultado |
|---|---|
| `npx tsc --noEmit` | Sin errores |
| `npm run lint` | Sin errores |
| `next build` | OK; `/documentos` 9.13 kB |
| `npm run gen:api` (deriva contrato ↔ tipos) | Sin deriva real: solo difieren los saltos de línea (LF/CRLF) |

Pendiente (no ejecutado): pruebas en navegador, accesibilidad, backend real.

## 2. Hallazgos de la revisión del PR #39 (por lectura de código)

| ID | Severidad | Hallazgo | Evidencia |
|---|---|---|---|
| A1 | Media | `DEMO_COURSE_ID` fijo: la pantalla no puede usarse con un curso real hasta el #21 | `documents-view.tsx` |
| A2 | Media | Un 413 del backend puede llegar como error de red: si el servidor corta la conexión antes de terminar de recibir, XHR dispara `onerror` y se muestra "No se pudo conectar" en vez de "supera 20 MB". El cliente valida antes, así que solo afecta si el límite del servidor difiere del cliente | `upload.ts` (sin `ontimeout` ni manejo de corte) |
| A3 | Baja | `retry` no impide lanzar dos subidas simultáneas del mismo archivo si se pulsa dos veces seguidas | `use-document-uploads.ts` |
| A4 | Baja | `key={reason}` en la lista de rechazos: dos archivos rechazados con el mismo mensaje duplican la clave de React | `documents-view.tsx` |
| A5 | Baja | El mock genera `doc-${Date.now()}`: dos archivos procesados en el mismo milisegundo colisionan | `documents-store.ts` |
| A6 | Info | `title` existe en el contrato pero la UI nunca lo envía | `use-document-uploads.ts` |
| A7 | Info | El mock no aplica la guarda de rol `teacher` que exige el contrato | `handlers.ts` |

Ninguno bloquea la fusión. A1 se resuelve en #21; A2 se confirma contra el backend real.

## 3. Estrategia

| Nivel | Herramienta propuesta | Dónde |
|---|---|---|
| Unitarias backend | `pytest` | `backend/tests/` |
| Contrato | `schemathesis` o validación contra `docs/openapi.json` | `backend/tests/contract/` |
| Unitarias frontend | `vitest` + Testing Library | `frontend/src/**/*.test.ts(x)` |
| E2E | `playwright` | `e2e/` |
| Manual y accesibilidad | Lista de la sección 7 | — |

Instalar `vitest` y `playwright` es una decisión de dependencias del equipo: confirmar antes de añadirlas.

## 4. Contrato (el que más protege la integración)
1. Cada respuesta real del backend valida contra su esquema de `openapi.json` (todos los endpoints).
2. `npm run gen:api` no produce diff real en CI (ignorando saltos de línea).
3. Normalizar saltos de línea con `.gitattributes` para que el punto 2 sea determinista.

## 5. Backend por endpoint

### Login (#15)
| Caso | Esperado |
|---|---|
| Credenciales válidas | 200 con token y `User.role` |
| Contraseña incorrecta | 401 con `ErrorResponse` |
| Cuerpo inválido | 422 con `ErrorResponse` |
| Ruta de `teacher` con token de `student` | 403 |

### Documentos (#16)
| Caso | Esperado |
|---|---|
| POST PDF, DOCX, PPTX válidos | 200/202 con `status: queued` |
| POST `.txt` | 415 |
| POST de 20 MB exactos / 20 MB + 1 byte | Aceptado / 413 |
| POST archivo vacío | **Por definir** (decisión de contrato abierta) |
| POST sin archivo | 422 |
| GET con rol `teacher` | 200 con `DocumentListResponse`, más recientes primero |
| GET con rol `student` | 403 |
| GET sin token | 401 |
| GET de curso inexistente | 404 |
| Transición de estados | `queued → processing → indexed`; archivo corrupto → `failed` con `error_message` |
| `mime_type` en la respuesta | Siempre uno de los 3 valores del enum |

### Tutor SSE (#17, #18)
| Caso | Esperado |
|---|---|
| Pregunta cubierta por el material | Eventos de texto + `SourceCitation` |
| Pregunta fuera del material | Responde que no está en el material; sin inventar fuentes |
| Pide la solución directa | No entrega la solución completa (guardrail socrático) |
| Mensaje con "no entiendo, me rindo" | Evento `FrustrationSignal` |
| `request_human_help: true` | Evento `EscalationSignal` |
| Cliente corta la conexión | El servidor libera recursos |
| Mensaje con instrucciones tipo "ignora lo anterior" | No altera las reglas del tutor |

### Riesgo y temas (#22, #23)
| Caso | Esperado |
|---|---|
| Cada `StudentRisk` | Incluye ≥1 `XaiFactor` estructurado (regla obligatoria) |
| Curso sin datos | Respuesta vacía válida, no error 500 |
| Rol `student` | 403 |
| Temas | Orden por frecuencia; alerta de confusión coherente con los datos |

## 6. Frontend: pruebas unitarias a escribir primero (alto valor, bajo costo)

Lógica pura ya aislada en `src/lib/documents.ts`:
| Función | Casos |
|---|---|
| `validateFile` | PDF ok; `.txt`; archivo vacío; 20 MB exactos; 20 MB + 1 |
| `matchType` | MIME correcto; MIME vacío con extensión; extensión en mayúsculas |
| `formatBytes` | 0, 1023, 1024, 1.5 MB |
| `formatRelative` | <45 s, minutos, horas, días |
| `useDocumentUploads` | cancelar aborta; reintentar tras error; sale de pantalla → aborta |
| `uploadDocument` | 2xx válido; 413 → error de API; respuesta sin JSON; `abort` → `AbortError` |

## 7. E2E y manual (#25, #26)

### Flujo completo (backend real)
1. Docente inicia sesión → sube un PDF → ve `En cola → Procesando → Indexado`.
2. Estudiante inicia sesión → pregunta sobre el PDF → recibe respuesta con cita.
3. Estudiante escribe frustración → ve señal y botón de ayuda → solicita docente.
4. Docente abre el dashboard → ve semáforo con panel XAI del estudiante.
5. Docente abre termómetro del aula → ve el tema consultado en el paso 2.

### Negativos del flujo
- Estudiante abre `/documentos` → bloqueado por guarda de rol.
- Token expirado → vuelve al login (`notifyUnauthorized`).
- Backend caído → mensaje de error con reintento, sin pantalla en blanco.
- Subida de 21 MB → rechazo antes de enviar.

### Accesibilidad y PWA (#26)
- Dropzone operable solo con teclado (Enter/Espacio); estados con etiqueta e ícono, no solo color.
- Contraste en modo claro y oscuro con la paleta de CLAUDE.md; sin scroll horizontal en móvil.
- Lighthouse PWA, accesibilidad y rendimiento; instalable; ecuaciones y bloques de código renderizan.

## 8. Criterios de salida para `v0.1.0`
- [ ] `tsc`, `eslint`, `build` en verde en `develop`.
- [ ] Tests de contrato en verde contra el backend real.
- [ ] E2E del flujo completo sin fallos bloqueantes.
- [ ] Negativos de la sección 7 verificados.
- [ ] Cero mocks activos en el build de producción.
- [ ] Hallazgos A1 y A2 resueltos o documentados como límites conocidos.
