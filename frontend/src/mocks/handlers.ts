import { delay, http, HttpResponse } from "msw";
import type { components } from "@/lib/api/schema";
import { MAX_SIZE_BYTES, MAX_SIZE_LABEL, matchType } from "@/lib/documents";
import { addDocument, listDocuments } from "./documents-store";
import { MOCK_HELP_REPLY, MOCK_STUDENTS, MOCK_TOPICS, MOCK_TUTOR_REPLY } from "./fixtures";

type LoginRequest = components["schemas"]["LoginRequest"];
type LoginResponse = components["schemas"]["LoginResponse"];
type TutorChatRequest = components["schemas"]["TutorChatRequest"];
type TutorStreamEvent = components["schemas"]["TutorStreamEvent"];
type DocumentListResponse = components["schemas"]["DocumentListResponse"];
type CourseRiskResponse = components["schemas"]["CourseRiskResponse"];
type RiskLevel = components["schemas"]["RiskLevel"];

const FRUSTRATION_PATTERN = /no entiendo|no puedo|me rindo|frustr/i;

function sseStream(request: Request, body: TutorChatRequest): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  const lastUserMessage = [...body.messages].reverse().find((m) => m.role === "user")?.content ?? "";
  const wantsHuman = body.request_human_help === true;
  const frustrated = !wantsHuman && FRUSTRATION_PATTERN.test(lastUserMessage);
  const frustratedMessages = body.messages.filter((m) => m.role === "user" && FRUSTRATION_PATTERN.test(m.content)).length;
  const persistent = frustrated && frustratedMessages >= 2;
  const reply = wantsHuman ? MOCK_HELP_REPLY : MOCK_TUTOR_REPLY;

  return new ReadableStream<Uint8Array>({
    async start(controller) {
      const send = (event: TutorStreamEvent) =>
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(event)}\n\n`));

      if (frustrated) {
        send({ type: "frustration", frustration: { detected: true, score: 0.8, adapted_tone: true } });
      }

      for (const chunk of reply.split(/(\s+)/)) {
        if (request.signal.aborted) {
          controller.close();
          return;
        }
        send({ type: "token", content: chunk });
        await delay(20);
      }

      if (!wantsHuman) {
        send({
          type: "sources",
          sources: [
            {
              document_id: "doc-1",
              title: "Guía de cálculo diferencial",
              page: 12,
              moodle_url: "https://moodle.example.edu/mod/resource/view.php?id=1",
            },
          ],
        });
      }

      if (wantsHuman || persistent) {
        send({
          type: "escalation",
          escalation: {
            suggested: true,
            reason: wantsHuman ? "student_requested" : "persistent_frustration",
            ticket_id: wantsHuman ? "T-1024" : null,
          },
        });
      }

      send({ type: "done", conversation_id: body.conversation_id ?? "conv-demo" });
      controller.close();
    },
  });
}

export const handlers = [
  http.post("*/api/v1/auth/login", async ({ request }) => {
    const body = (await request.json()) as LoginRequest;
    // Contraseña de prueba para ver el estado de error del formulario.
    if (body.password === "incorrecta") {
      return HttpResponse.json(
        { code: "invalid_credentials", message: "Correo o contraseña incorrectos." },
        { status: 401 },
      );
    }
    const role = body.role ?? "student";
    const response: LoginResponse = {
      access_token: `mock-token-${role}`,
      token_type: "bearer",
      expires_in: 3600,
      user: {
        id: role === "teacher" ? "t1" : "s0",
        name: role === "teacher" ? "Profe Demo" : "Estudiante Demo",
        email: body.email,
        role,
      },
    };
    await delay(300);
    return HttpResponse.json(response);
  }),

  http.get("*/api/v1/courses/:courseId/documents", async ({ params }) => {
    await delay(250);
    const response: DocumentListResponse = {
      course_id: String(params.courseId),
      documents: listDocuments(),
    };
    return HttpResponse.json(response);
  }),

  http.post("*/api/v1/courses/:courseId/documents", async ({ params, request }) => {
    const form = await request.formData();
    const file = form.get("file");
    if (!(file instanceof File)) {
      return HttpResponse.json({ code: "invalid_request", message: "Falta el archivo." }, { status: 422 });
    }
    const type = matchType(file);
    if (!type) {
      return HttpResponse.json(
        { code: "unsupported_media_type", message: "Solo se admiten archivos PDF, DOCX y PPTX." },
        { status: 415 },
      );
    }
    if (file.size > MAX_SIZE_BYTES) {
      return HttpResponse.json(
        { code: "file_too_large", message: `El archivo supera el máximo de ${MAX_SIZE_LABEL}.` },
        { status: 413 },
      );
    }
    const title = form.get("title");
    await delay(900);
    const response = addDocument({
      courseId: String(params.courseId),
      file,
      mime: type.mime,
      title: typeof title === "string" && title ? title : null,
    });
    return HttpResponse.json(response, { status: 202 });
  }),

  http.post("*/api/v1/tutor/chat/stream", async ({ request }) => {
    const body = (await request.json()) as TutorChatRequest;
    return new HttpResponse(sseStream(request, body), {
      headers: { "Content-Type": "text/event-stream", "Cache-Control": "no-cache" },
    });
  }),

  http.get("*/api/v1/analytics/courses/:courseId/risk", async ({ params, request }) => {
    const level = new URL(request.url).searchParams.get("level") as RiskLevel | null;
    const students = level ? MOCK_STUDENTS.filter((s) => s.risk_level === level) : MOCK_STUDENTS;
    const response: CourseRiskResponse = {
      course_id: String(params.courseId),
      summary: {
        green: MOCK_STUDENTS.filter((s) => s.risk_level === "green").length,
        yellow: MOCK_STUDENTS.filter((s) => s.risk_level === "yellow").length,
        red: MOCK_STUDENTS.filter((s) => s.risk_level === "red").length,
      },
      students,
    };
    await delay(400);
    return HttpResponse.json(response);
  }),

  http.get("*/api/v1/analytics/courses/:courseId/topics", async ({ params }) => {
    await delay(400);
    return HttpResponse.json({ ...MOCK_TOPICS, course_id: String(params.courseId) });
  }),
];
