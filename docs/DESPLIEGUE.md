# Despliegue gratuito de TutoMind

Tres servicios, todos en plan gratuito:

| Pieza | Servicio | Qué es |
|---|---|---|
| Base de datos | **Neon** | PostgreSQL con la extensión `vector` (pgvector) |
| Backend | **Render** | FastAPI (`backend/`), definido en [`render.yaml`](../render.yaml) |
| Frontend | **Vercel** | Next.js (`frontend/`) |

El orden importa: la base primero, luego el servidor (necesita la URL de la base) y al final la pantalla (necesita la URL del servidor).

## Estado actual (26 nov 2026)

| Pieza | Dónde | Dirección |
|---|---|---|
| Frontend | Vercel (cuenta `williamtrix2022`) | https://tutomind.vercel.app |
| Backend | Render, servicio `tutomind-api`, región Virginia | https://tutomind-api.onrender.com (`/health`, `/docs`) |
| Base de datos | Neon, proyecto `tutomind` (`cool-fire-02965334`), PostgreSQL 17 + pgvector | — |

- **Contraseña de las cuentas de demo:** se fijó con `DEMO_PASSWORD` en Render y **no está en el repositorio**. Se entrega en privado.
- **Backend:** Render sigue la rama `develop` y se redespliega con cada cambio. Al etiquetar `v0.1.0` conviene cambiarlo a `main` (Render → *Settings → Branch*).
- **Frontend:** se publicó desde la carpeta `frontend/` con el CLI de Vercel (el proyecto no está enlazado a GitHub). Para publicar cambios: `cd frontend && npx vercel deploy --prod`. Las variables `NEXT_PUBLIC_API_URL` y `NEXT_PUBLIC_USE_MOCKS` ya están en el proyecto. Si prefieres despliegue automático, conecta el repositorio desde *Settings → Git* del proyecto en Vercel.
- **Tutor:** sin `GEMINI_API_KEY` usa el cliente offline. Al añadir la clave en Render hay que borrar y volver a subir los documentos.
- **Servicio creado a mano:** el servicio de Render se creó con comandos que entran a `backend/` (`cd backend && …`) porque la herramienta no permitía fijar el directorio raíz; `render.yaml` es la versión equivalente con `rootDir`.

## 1. Neon (base de datos)
1. Crea un proyecto y una base (por ejemplo `tutomind`), región cercana al servidor de Render.
2. Copia la **cadena de conexión** (`postgresql://usuario:clave@host/db?sslmode=require`). El backend le agrega el driver solo.
3. Activa pgvector en la base: `CREATE EXTENSION IF NOT EXISTS vector;`
4. **No hace falta sembrar desde tu PC**: el servidor de Render corre las migraciones y la semilla en cada arranque (ver `startCommand` en `render.yaml`). Si prefieres hacerlo a mano, con el entorno del backend activo:
   ```bash
   cd backend
   export DATABASE_URL="<la cadena de Neon>" DEMO_PASSWORD="<contraseña de demo>"
   alembic upgrade head && python -m app.db.seed
   ```
   Algunas redes bloquean el puerto 5432 de PostgreSQL; si pasa, deja que lo haga Render.

## 2. Render (backend)
1. *New → Blueprint* y elige este repositorio: Render lee `render.yaml`.
2. Completa las variables que pide:
   - `DATABASE_URL`: la cadena de Neon.
   - `DEMO_PASSWORD`: la contraseña de las cuentas de demo (`docente@tutomind.demo`, `ana@tutomind.demo`, …). Que no sea `demo12345`; entrégala al profe en privado.
   - `CORS_ORIGINS`: la URL que tendrá Vercel (por ejemplo `https://tutomind.vercel.app`). Puede ir varias, separadas por coma.
   - `GEMINI_API_KEY`: opcional y no se pide al crear. Agrégala después en *Environment*; sin clave el tutor funciona con el cliente offline.
3. `JWT_SECRET` lo genera Render. Con `ENVIRONMENT=production` el servidor **no arranca** sin un secreto de al menos 32 caracteres.
4. Cuando termine, comprueba `https://<tu-servicio>.onrender.com/health` (debe responder 200) y `/docs`.

> **Arranque en frío.** El plan gratuito duerme el servidor tras ~15 min sin uso y tarda hasta un minuto en despertar. El login lo despierta solo al abrirse y avisa si la primera petición tarda. Antes de una demostración, abre la pantalla de login un par de minutos antes.

## 3. Vercel (frontend)
1. *Add New → Project*, mismo repositorio, **Root Directory: `frontend`**.
2. Variables de entorno:
   - `NEXT_PUBLIC_API_URL` = la URL de Render (sin barra final).
   - `NEXT_PUBLIC_USE_MOCKS` = `false`.
3. Despliega. Si la URL final de Vercel es distinta de la que pusiste en `CORS_ORIGINS`, corrígela en Render y redespliega el backend.

## 4. Material del curso
Con la sesión de docente, sube los PDF de [`docs/demo/`](demo/) (o tu material real) desde **Documentos** y espera a que pasen a *Indexado*.

Si activas `GEMINI_API_KEY` **después** de haber subido documentos, hay que borrarlos y volver a subirlos: los vectores del modo offline y los de Gemini no se pueden mezclar.

## Comprobación
Recorre la app en la URL pública: login de docente (riesgo, temas, documentos) y de estudiante (tutor). Las mismas pruebas automáticas sirven contra el sitio publicado:

```bash
cd frontend
E2E_BASE_URL=https://<tu-app>.vercel.app E2E_PASSWORD=<DEMO_PASSWORD> npm run e2e -- --project=escritorio
```

## Problemas frecuentes
| Síntoma | Causa probable |
|---|---|
| El login dice «No pudimos conectar con el servidor» | Render dormido (espera un minuto y reintenta), o `NEXT_PUBLIC_API_URL` mal escrita |
| El navegador bloquea las peticiones (CORS) | La URL de Vercel no está en `CORS_ORIGINS` |
| Render no arranca y el log habla de `JWT_SECRET` | Falta el secreto o tiene menos de 32 caracteres |
| `type "vector" does not exist` al migrar | Falta `CREATE EXTENSION vector` en Neon |
| El tutor cita documentos raros tras poner la clave de Gemini | Hay documentos indexados en modo offline: bórralos y súbelos de nuevo |
