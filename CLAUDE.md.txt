# TutoMind - Guía de Ingeniería y Diseño para Claude Code

## Contexto del Proyecto
TutoMind es una plataforma web educativa (PWA) integrada con Moodle que ofrece:
1. Un Tutor Inteligente Socrático/Evaluador basado en documentos del curso (RAG) con guardrails pedagógicos y anti-plagio.
2. Un Dashboard Predictivo de Riesgo Académico con Explicabilidad (XAI) en tiempo real.

## Arquitectura del Monorepo
- `/frontend`: Next.js 15 (App Router), TypeScript estricto, Tailwind CSS, shadcn/ui, Motion (Framer), KaTeX, Shiki.
- `/backend`: FastAPI (Python 3.12), Pydantic v2, PostgreSQL + pgvector, Anthropic SDK.
- `/docs/openapi.json`: Fuente única de verdad para los tipos entre Frontend y Backend.

## Estándares de Diseño UI/UX (Apple HIG + Silent Moon Aesthetic)
- **Identidad Visual**: Estética calmada, táctil y de alto contraste. Usa tarjetas estilo Bento con `rounded-3xl` (24px), bordes sutiles (`border-white/10` en dark mode, `border-slate-200/80` en light mode) y sombras difusas.
- **Paleta de Color Obligatoria**:
  - Dark Canvas: `#03174C` | Dark Card: `#0D256C`
  - Light Canvas: `#F6F7FB` | Light Card: `#FFFFFF`
  - Primary Accent (Focus/CTA): `#8E97FD`
  - Success / Riesgo Bajo: `#6CB28E`
  - Warning / Riesgo Medio: `#FA6E5A`
  - Highlight / Alerta Confusión: `#FFCF86`
  - AI Glow / Secundario: `#D9A5B3`
- **Interacción y Movimiento**:
  - Usa `motion` con física de resorte (`type: "spring", stiffness: 350, damping: 28`).
  - Feedback táctil inmediato en botones (`whileTap={{ scale: 0.97 }}`).
  - Nunca apiles dos superficies translúcidas claras una sobre otra.
- **Renderizado Académico**: Toda respuesta del tutor debe soportar Markdown, bloques de código con botón de copiar y ecuaciones LaTeX (`$inline$` y `$$block$$`).

## Reglas de Ingeniería
1. **Frontend**: Nunca uses `any` en TypeScript. Define interfaces basadas en `docs/openapi.json`. Separa la lógica de red (hooks de TanStack Query) de los componentes visuales. Diseña Mobile-First (PWA).
2. **Backend**: Todos los endpoints deben validar entrada/salida con Pydantic v2 y devolver explicaciones XAI estructuradas junto con cada nivel de riesgo.
3. **Flujo de Trabajo**: Antes de crear una nueva vista, revisa los componentes existentes en `frontend/src/components/ui` para mantener consistencia absoluta.