"use client";

import { motion } from "motion/react";
import { ArrowUp, Square } from "lucide-react";
import { useLayoutEffect, useRef, useState } from "react";
import type { FormEvent, KeyboardEvent } from "react";
import { spring, tap } from "@/lib/motion";

interface ChatComposerProps {
  isStreaming: boolean;
  onSend: (text: string) => void;
  onStop: () => void;
}

export function ChatComposer({ isStreaming, onSend, onStop }: ChatComposerProps) {
  const [text, setText] = useState("");
  const textarea = useRef<HTMLTextAreaElement>(null);

  // Crece con el contenido hasta 8 líneas.
  useLayoutEffect(() => {
    const el = textarea.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 192)}px`;
  }, [text]);

  function submit(event?: FormEvent) {
    event?.preventDefault();
    if (isStreaming || !text.trim()) return;
    onSend(text);
    setText("");
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      submit();
    }
  }

  const canSend = text.trim().length > 0;

  return (
    <form
      onSubmit={submit}
      className="flex items-end gap-2 rounded-3xl border border-line bg-card p-2 shadow-card focus-within:border-primary"
    >
      <label htmlFor="tutor-input" className="sr-only">
        Escribe tu pregunta
      </label>
      <textarea
        ref={textarea}
        id="tutor-input"
        rows={1}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={onKeyDown}
        placeholder="Pregunta lo que no te quedó claro…"
        className="max-h-48 min-h-11 flex-1 resize-none bg-transparent px-3 py-2.5 text-base leading-relaxed text-fg outline-none placeholder:text-muted"
      />

      {isStreaming ? (
        <motion.button
          type="button"
          onClick={onStop}
          whileTap={tap}
          transition={spring}
          aria-label="Detener respuesta"
          className="grid size-11 shrink-0 place-items-center rounded-2xl bg-canvas text-fg"
        >
          <Square className="size-4 fill-current" aria-hidden />
        </motion.button>
      ) : (
        <motion.button
          type="submit"
          disabled={!canSend}
          whileTap={canSend ? tap : undefined}
          transition={spring}
          aria-label="Enviar pregunta"
          className="grid size-11 shrink-0 place-items-center rounded-2xl bg-primary text-on-primary transition-opacity disabled:opacity-40"
        >
          <ArrowUp className="size-5" aria-hidden />
        </motion.button>
      )}
    </form>
  );
}
