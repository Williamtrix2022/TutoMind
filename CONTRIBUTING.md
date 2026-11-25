# Guía de colaboración

Equipo de dos: **Frontend** (`/frontend`) y **Backend** (`/backend`). Entrega: **30 de noviembre**.

## Ramas
| Rama | Uso |
|---|---|
| `main` | Estable. Solo recibe `develop` al cerrar un sprint y en la entrega. |
| `develop` | Integración. Destino de todos los PRs. |
| `feat/fe-*` · `feat/be-*` | Funcionalidades de cada área. |
| `fix/*` · `docs/*` · `chore/*` | Correcciones, documentación y tareas. |

Nunca hagas push directo a `main` ni a `develop`.

## Flujo diario
1. Elige una issue del sprint actual (milestone) y asígnatela.
2. `git checkout develop && git pull && git checkout -b feat/fe-nombre-corto`
3. Commits pequeños con [Conventional Commits](https://www.conventionalcommits.org/es/): `feat(frontend): …`, `fix(backend): …`, `docs: …`
4. `git push -u origin <rama>` y abre un PR hacia `develop` que incluya `Closes #N`.
5. La otra persona revisa. Se hace squash and merge.
6. Antes de empezar cada día: `git pull` en `develop` y rebase de tu rama.

## Contrato de API
- `docs/openapi.json` es la fuente única de verdad.
- Si necesitas cambiar un endpoint, abre un PR **solo con el cambio del contrato** (etiqueta `area:contrato`) y espera la aprobación de la otra persona antes de implementarlo.
- Frontend: los tipos se generan desde el contrato; nunca se usa `any`.
- Backend: los modelos Pydantic v2 deben coincidir con el contrato.

## Definición de terminado
- [ ] Cumple los criterios de aceptación de la issue.
- [ ] Frontend: `npm run lint` y `npm run build` pasan. Backend: tests y linter pasan.
- [ ] Sin secretos en el código (usa `.env`, que está ignorado).
- [ ] PR revisado por la otra persona.

## Reuniones sugeridas
- **Daily asíncrona** (5 min, por chat): qué hice, qué haré, qué me bloquea.
- **Cierre de sprint:** demo mutua, merge de `develop` a `main` y planificación del siguiente sprint.
