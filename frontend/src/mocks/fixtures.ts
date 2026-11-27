import type { components } from "@/lib/api/schema";

type StudentRisk = components["schemas"]["StudentRisk"];
type CourseTopicsResponse = components["schemas"]["CourseTopicsResponse"];
type XaiFactor = components["schemas"]["XaiFactor"];

const UPDATED_AT = "2026-11-24T12:00:00Z";

const factor = (
  key: string,
  label: string,
  impact: number,
  value: number | string,
  explanation: string,
): XaiFactor => ({ key, label, impact, value, explanation });

export const MOCK_STUDENTS: StudentRisk[] = [
  {
    student_id: "s1",
    name: "Camila Torres",
    risk_level: "red",
    risk_score: 0.86,
    projected_grade: 2.1,
    grade_scale_max: 5,
    updated_at: UPDATED_AT,
    factors: [
      factor("days_since_last_login", "Días sin ingresar a Moodle", 0.42, 12, "No entra a la plataforma desde hace 12 días."),
      factor("missed_assignments", "Tareas sin entregar", 0.31, 3, "Dejó sin entregar las últimas 3 tareas."),
      factor("tutor_confusion", "Dudas sin resolver con el tutor", 0.18, 5, "Repitió 5 veces la misma duda sobre derivadas."),
    ],
  },
  {
    student_id: "s2",
    name: "Andrés Rojas",
    risk_level: "red",
    risk_score: 0.79,
    projected_grade: 2.6,
    grade_scale_max: 5,
    updated_at: UPDATED_AT,
    factors: [
      factor("quiz_average", "Promedio de quices", 0.4, "2.3 / 5", "Su promedio en quices está muy por debajo del curso."),
      factor("late_submissions", "Entregas tardías", 0.25, 4, "4 de las últimas 6 entregas llegaron tarde."),
    ],
  },
  {
    student_id: "s3",
    name: "Valeria Gómez",
    risk_level: "yellow",
    risk_score: 0.54,
    projected_grade: 3.3,
    grade_scale_max: 5,
    updated_at: UPDATED_AT,
    factors: [
      factor("activity_drop", "Caída de actividad", 0.28, "-45 %", "Su actividad semanal bajó 45 % frente al mes anterior."),
      factor("quiz_average", "Promedio de quices", 0.14, "3.1 / 5", "Rinde algo por debajo del promedio del grupo."),
    ],
  },
  {
    student_id: "s4",
    name: "Santiago Mejía",
    risk_level: "yellow",
    risk_score: 0.48,
    projected_grade: 3.5,
    grade_scale_max: 5,
    updated_at: UPDATED_AT,
    factors: [
      factor("tutor_confusion", "Dudas sin resolver con el tutor", 0.22, 3, "Tiene 3 dudas recurrentes sobre integrales."),
      factor("days_since_last_login", "Días sin ingresar a Moodle", 0.1, 5, "Lleva 5 días sin entrar."),
    ],
  },
  {
    student_id: "s5",
    name: "Daniela Pérez",
    risk_level: "yellow",
    risk_score: 0.41,
    projected_grade: 3.6,
    grade_scale_max: 5,
    updated_at: UPDATED_AT,
    factors: [
      factor("late_submissions", "Entregas tardías", 0.2, 2, "2 entregas tardías en el último mes."),
      factor("forum_participation", "Participación en foros", 0.12, 0, "No ha participado en los foros."),
    ],
  },
  {
    student_id: "s6",
    name: "Mateo Ruiz",
    risk_level: "green",
    risk_score: 0.15,
    projected_grade: 4.4,
    grade_scale_max: 5,
    updated_at: UPDATED_AT,
    factors: [
      factor("quiz_average", "Promedio de quices", -0.3, "4.5 / 5", "Su promedio de quices supera al del grupo."),
      factor("activity", "Actividad semanal", -0.2, "Alta", "Entra y practica con el tutor varias veces por semana."),
    ],
  },
  {
    student_id: "s7",
    name: "Isabela Castaño",
    risk_level: "green",
    risk_score: 0.09,
    projected_grade: 4.7,
    grade_scale_max: 5,
    updated_at: UPDATED_AT,
    factors: [
      factor("assignments_on_time", "Entregas a tiempo", -0.35, "100 %", "Entregó todo a tiempo."),
      factor("quiz_average", "Promedio de quices", -0.25, "4.8 / 5", "Resultados sobresalientes."),
    ],
  },
  {
    student_id: "s8",
    name: "Julián Herrera",
    risk_level: "green",
    risk_score: 0.2,
    projected_grade: 4.1,
    grade_scale_max: 5,
    updated_at: UPDATED_AT,
    factors: [factor("activity", "Actividad semanal", -0.18, "Media", "Mantiene un ritmo constante.")],
  },
];

export const MOCK_TOPICS: CourseTopicsResponse = {
  course_id: "demo",
  period_start: "2026-11-17T00:00:00Z",
  period_end: "2026-11-24T00:00:00Z",
  topics: [
    {
      topic: "Derivadas por definición",
      question_count: 42,
      unique_students: 17,
      confusion_score: 0.82,
      confusion_alert: true,
      sample_questions: ["¿Por qué el límite de h tiende a cero?", "No entiendo cómo simplificar el cociente."],
    },
    {
      topic: "Regla de la cadena",
      question_count: 31,
      unique_students: 14,
      confusion_score: 0.71,
      confusion_alert: true,
      sample_questions: ["¿Cuándo uso la regla de la cadena?"],
    },
    {
      topic: "Integrales definidas",
      question_count: 24,
      unique_students: 11,
      confusion_score: 0.38,
      confusion_alert: false,
      sample_questions: ["¿Cómo cambio los límites al sustituir?"],
    },
    {
      topic: "Límites al infinito",
      question_count: 18,
      unique_students: 9,
      confusion_score: 0.3,
      confusion_alert: false,
      sample_questions: [],
    },
    {
      topic: "Continuidad",
      question_count: 12,
      unique_students: 8,
      confusion_score: 0.22,
      confusion_alert: false,
      sample_questions: [],
    },
    {
      topic: "Optimización",
      question_count: 9,
      unique_students: 6,
      confusion_score: 0.18,
      confusion_alert: false,
      sample_questions: [],
    },
  ],
};

/** Respuesta corta cuando el estudiante pide ayuda humana. */
export const MOCK_HELP_REPLY =
  "Listo, le envié tu consulta y nuestra conversación a tu docente para que la revise en su panel. Mientras tanto, si quieres, seguimos con otro ejemplo.";

/** Respuesta del tutor con LaTeX y código, para probar el render. */
export const MOCK_TUTOR_REPLY = `Vamos paso a paso. Piensa en la derivada de $f(x)=x^2$.

La definición es:

$$f'(x)=\\lim_{h\\to 0}\\frac{f(x+h)-f(x)}{h}$$

Puedes comprobarla numéricamente:

\`\`\`python
def derivada(f, x, h=1e-6):
    return (f(x + h) - f(x)) / h

print(derivada(lambda x: x**2, 3))
\`\`\`

¿Qué valor esperas para $x=3$ antes de ejecutarlo?`;
