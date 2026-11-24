# 🧠 TutoMind — Tutor Inteligente & Analítica Predictiva XAI

Plataforma web educativa (PWA) integrada con **Moodle** que combina tutoría personalizada mediante IA generativa (RAG sobre material docente) con detección temprana y explicable de riesgo académico.

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
├── backend/           # FastAPI + Python 3.12 + pgvector + Claude API
├── docs/              # Contrato OpenAPI y diagramas de arquitectura
├── CLAUDE.md          # Reglas de arquitectura y diseño para Claude Code
└── README.md