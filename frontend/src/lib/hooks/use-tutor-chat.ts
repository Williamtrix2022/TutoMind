"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "@/lib/api/errors";
import type { components } from "@/lib/api/schema";
import { streamTutorChat } from "@/lib/api/sse";
import type { StudentLevel } from "@/lib/types";

export type SourceCitation = components["schemas"]["SourceCitation"];
export type FrustrationSignal = components["schemas"]["FrustrationSignal"];
export type EscalationSignal = components["schemas"]["EscalationSignal"];

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources: SourceCitation[];
  streaming: boolean;
  error: string | null;
}

interface UseTutorChatOptions {
  courseId: string;
  level: StudentLevel;
}

let messageCounter = 0;
const nextId = () => `m${++messageCounter}`;

/** Lógica de red del chat; los componentes solo pintan el estado. */
export function useTutorChat({ courseId, level }: UseTutorChatOptions) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [frustration, setFrustration] = useState<FrustrationSignal | null>(null);
  const [escalation, setEscalation] = useState<EscalationSignal | null>(null);

  const messagesRef = useRef<ChatMessage[]>([]);
  const conversationId = useRef<string | null>(null);
  const controller = useRef<AbortController | null>(null);

  const commit = useCallback((updater: (prev: ChatMessage[]) => ChatMessage[]) => {
    setMessages((prev) => {
      const next = updater(prev);
      messagesRef.current = next;
      return next;
    });
  }, []);

  const patchAssistant = useCallback(
    (id: string, patch: (message: ChatMessage) => ChatMessage) => {
      commit((prev) => prev.map((m) => (m.id === id ? patch(m) : m)));
    },
    [commit],
  );

  const send = useCallback(
    async (text: string, options: { requestHumanHelp?: boolean } = {}) => {
      const content = text.trim();
      if (!content || controller.current) return;

      const history = messagesRef.current
        .filter((m) => m.content && !m.error)
        .map((m) => ({ role: m.role, content: m.content }));

      const assistantId = nextId();
      commit((prev) => [
        ...prev,
        { id: nextId(), role: "user", content, sources: [], streaming: false, error: null },
        { id: assistantId, role: "assistant", content: "", sources: [], streaming: true, error: null },
      ]);
      setFrustration(null);

      const abort = new AbortController();
      controller.current = abort;

      try {
        const events = streamTutorChat(
          {
            course_id: courseId,
            conversation_id: conversationId.current,
            student_level: level,
            messages: [...history, { role: "user", content }],
            request_human_help: options.requestHumanHelp ?? false,
          },
          abort.signal,
        );

        for await (const event of events) {
          switch (event.type) {
            case "token":
              patchAssistant(assistantId, (m) => ({ ...m, content: m.content + event.content }));
              break;
            case "sources":
              patchAssistant(assistantId, (m) => ({ ...m, sources: event.sources }));
              break;
            case "frustration":
              setFrustration(event.frustration);
              break;
            case "escalation":
              setEscalation(event.escalation);
              break;
            case "done":
              conversationId.current = event.conversation_id;
              break;
            case "error":
              patchAssistant(assistantId, (m) => ({ ...m, error: event.message }));
              break;
          }
        }
      } catch (error) {
        if (!(error instanceof DOMException && error.name === "AbortError")) {
          const message =
            error instanceof ApiError ? error.message : "Se perdió la conexión con el tutor. Inténtalo de nuevo.";
          patchAssistant(assistantId, (m) => ({ ...m, error: message }));
        }
      } finally {
        controller.current = null;
        patchAssistant(assistantId, (m) => ({ ...m, streaming: false }));
      }
    },
    [commit, courseId, level, patchAssistant],
  );

  const stop = useCallback(() => controller.current?.abort(), []);

  const reset = useCallback(() => {
    controller.current?.abort();
    conversationId.current = null;
    commit(() => []);
    setFrustration(null);
    setEscalation(null);
  }, [commit]);

  // Cancela el stream si el usuario sale de la pantalla.
  useEffect(() => () => controller.current?.abort(), []);

  const isStreaming = messages.some((m) => m.streaming);

  return { messages, isStreaming, frustration, escalation, send, stop, reset };
}
