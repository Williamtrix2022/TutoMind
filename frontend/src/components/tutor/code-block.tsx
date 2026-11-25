"use client";

import { Check, Copy } from "lucide-react";
import { Children, isValidElement, useEffect, useState } from "react";
import type { ReactNode } from "react";

function nodeText(node: ReactNode): string {
  if (typeof node === "string") return node;
  if (Array.isArray(node)) return node.map(nodeText).join("");
  return "";
}

/** Bloque de código con botón de copiar. Recibe el `<code>` que genera react-markdown. */
export function CodeBlock({ children }: { children?: ReactNode }) {
  const [copied, setCopied] = useState(false);

  const child = Children.toArray(children)[0];
  const codeProps = isValidElement<{ className?: string; children?: ReactNode }>(child) ? child.props : {};
  const language = /language-([\w-]+)/.exec(codeProps.className ?? "")?.[1] ?? "texto";
  const code = nodeText(codeProps.children).replace(/\n$/, "");

  useEffect(() => {
    if (!copied) return;
    const timer = window.setTimeout(() => setCopied(false), 1800);
    return () => window.clearTimeout(timer);
  }, [copied]);

  async function copy() {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
    } catch {
      /* el portapapeles puede estar bloqueado: no hacemos nada */
    }
  }

  return (
    <div className="my-4 overflow-hidden rounded-2xl border border-white/10 bg-night-canvas text-slate-100">
      <div className="flex items-center justify-between border-b border-white/10 px-4 py-2">
        <span className="text-xs font-semibold text-slate-300">{language}</span>
        <button
          type="button"
          onClick={copy}
          className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs font-semibold text-slate-200 transition-colors hover:bg-white/10 active:scale-[0.97]"
        >
          {copied ? <Check className="size-3.5 text-success" aria-hidden /> : <Copy className="size-3.5" aria-hidden />}
          <span aria-live="polite">{copied ? "Copiado" : "Copiar"}</span>
        </button>
      </div>
      <pre className="overflow-x-auto p-4 text-sm leading-relaxed">
        <code>{code}</code>
      </pre>
    </div>
  );
}
