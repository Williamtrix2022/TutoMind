# 🎬 Guion de la demostración (8 a 10 minutos)

**Sitio:** https://tutomind.vercel.app · **Cuentas:** `docente@tutomind.demo` y `ana@tutomind.demo` (la contraseña se entrega en privado).

---

## Antes de empezar (5 minutos antes)

- [ ] **Despierta el servidor:** abre https://tutomind.vercel.app/login y déjalo cargado. El servidor gratuito se duerme tras 15 minutos sin uso y la primera petición puede tardar hasta un minuto.
- [ ] **Dos ventanas:** una normal con el **docente** y una de **incógnito** con el **estudiante**, para no cerrar sesión entre una y otra.
- [ ] Inicia sesión en las dos y deja cada una en su pantalla de inicio. Prueba el modo claro y el oscuro y elige el que se vea mejor en el proyector.
- [ ] Ten el wifi del equipo o un hotspot de respaldo.
- [ ] Un PDF corto cualquiera en el escritorio, para subirlo en vivo.

---

## 1. Apertura (30 s)

> «TutoMind hace dos cosas. A los **estudiantes** les da un tutor que los guía con el material de su curso **sin darles la respuesta hecha**. Y a los **docentes** les muestra **quién está en riesgo y por qué**, no solo un número.»

---

## 2. El docente (4 min)

**Inicio.** «Es el tablero del docente: riesgo, confusión del aula, factores que más pesan y estado de los documentos, con datos reales del curso.»

**Riesgo** (menú *Riesgo*)
1. Señala el **anillo del semáforo**: «5 estudiantes: 2 en rojo, 2 en amarillo, 1 en verde.»
2. Toca **Riesgo alto** (o la tarjeta del anillo): la lista se filtra, pero el semáforo del curso no cambia.
3. Abre al primer estudiante (rojo). Panel de la derecha:
   - **Nota proyectada** en el medidor.
   - **Factores explícitos**: cada barra muestra cuánto *aumenta* (derecha, rojo) o *reduce* (izquierda, verde) el riesgo, con el valor y una explicación en español.
   - **Frase clave:** «Esto es explicabilidad. El docente no recibe una caja negra: ve exactamente por qué el sistema lo marcó. El puntaje es la suma de esos factores.»
4. Menciona de dónde salen: días sin ingresar a Moodle, promedio de notas, tareas sin entregar, frustración con el tutor, uso del tutor y ayudas abiertas.

**Temas** (menú *Temas*)
1. «El **termómetro del aula**: qué tan confundido está el grupo esta semana.»
2. Señala la tarjeta amarilla **Derivadas**: «Hay confusión grupal en este tema; el docente puede reforzarlo en la próxima clase.»
3. Abre **Ver preguntas de ejemplo**: «Son preguntas reales de los estudiantes, **sin nombres**.»

**Documentos** (menú *Documentos*)
1. «El docente sube el material y eso alimenta al tutor.» Arrastra tu PDF corto.
2. Muestra el progreso y el estado pasando a **Indexado**. «Se divide en fragmentos y se guarda como vectores para que el tutor lo consulte.»

---

## 3. El estudiante (3 min), ventana de incógnito

**Inicio.** «Ana entra y ve lo que necesita para estudiar: el tutor, una guía de cómo la acompaña y un bloque de estudio 25/5.»

**Tutor**
1. Toca la pregunta sugerida **«No entiendo la regla de la cadena»**. La conversación abre y el tutor responde en **streaming**.
2. Señala las **fuentes** al final: «Cita el documento del curso y la página. Responde con el material del profesor, no con cualquier cosa de internet.»
3. Resalta el estilo: «Hace preguntas y da pistas; no resuelve el ejercicio por ella.»
4. Cambia el **nivel** a *Avanzado* y repite una pregunta para mostrar que cambia la profundidad (se nota más con Gemini; en modo offline el efecto es menor).
5. **Frustración:** escribe «ya me rendí, no entiendo nada, esto es imposible». Aparece el aviso **«Este tema está costando, y es normal»** y el tutor baja el ritmo.
6. Pulsa **Pedir ayuda al docente**: «Se registra una solicitud para el docente, con el contexto de la conversación.»

---

## 4. Cierre (1 min)

> «Todo corre **gratis** en la nube: pantalla en Vercel, servidor en Render y base de datos con pgvector en Neon. El contrato de API es la fuente de verdad entre frontend y backend, y hay pruebas automáticas end-to-end y de accesibilidad.»

**Di los límites antes de que los pregunten** (suma credibilidad):
- El riesgo es un **modelo de reglas transparente**, no un modelo entrenado: el siguiente paso es calibrarlo con datos reales de un curso.
- **Moodle está simulado**: el cliente está escrito pero no se probó contra un Moodle real.
- Usamos el **nivel gratuito** de Google: solo material de demostración.

---

## Si algo falla (plan B)

| Problema | Qué hacer |
|---|---|
| «El servidor está despertando…» | Espera hasta un minuto y conversa sobre el problema mientras carga. No recargues. |
| El tutor responde con frases genéricas o cortas | Está en modo offline (sin Gemini o sin cuota). Explica: «Sin clave usa un modo de reglas; con Gemini el contenido es más rico.» El flujo, las fuentes y la frustración funcionan igual. |
| No entra / dice credenciales incorrectas | Revisa que el rol del selector coincida con la cuenta (Docente o Estudiante). |
| Sin internet | Lee las capturas de las diapositivas; la arquitectura y los resultados de las pruebas se explican sin la app. |
| Un documento queda en *Procesando* | Espera unos segundos; si pasa a *Falló*, sube otro PDF. |

---

## Preguntas probables del profe

**¿Cómo se calcula el riesgo?** Puntaje = 0,5 + suma de los factores; cada factor es peso × severidad (días sin ingresar 0,30, promedio de notas 0,30, tareas sin entregar 0,15, frustración 0,10, uso del tutor 0,10, ayudas abiertas 0,05). Verde por debajo de 0,40, amarillo por debajo de 0,65 y rojo de ahí en adelante. Es una primera calibración y está documentada en el README del backend.

**¿Por qué no usar machine learning?** Para el MVP no hay datos históricos para entrenar. Un modelo de reglas es explicable por diseño y verificable con pruebas; entrenar uno sin datos sería inventar.

**¿Evita que el estudiante copie?** El tutor está instruido para guiar con preguntas y pistas, no para dar la solución final. Es una barrera pedagógica, no un sistema antiplagio infalible.

**¿Qué pasa con la privacidad?** Las preguntas de ejemplo del docente salen sin nombres. El nivel gratuito de Google puede usar los textos enviados para mejorar sus modelos, así que la demo usa solo material de ejemplo; en producción se usaría un plan que no lo permita.

**¿Funciona con Moodle?** Está implementado el cliente de Web Services (accesos, notas y entregas) y la ingesta; falta probarlo contra una instancia real. Mientras tanto usa datos simulados y avisa.

**¿Escala?** El MVP corre en planes gratuitos pensados para demostración. La arquitectura (API sin estado, PostgreSQL con pgvector) permite escalar subiendo de plan.
