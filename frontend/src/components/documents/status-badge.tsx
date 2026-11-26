import type { components } from "@/lib/api/schema";
import { STATUS_STYLE } from "@/lib/documents";

type DocumentStatus = components["schemas"]["DocumentStatus"];

export function StatusBadge({ status }: { status: DocumentStatus }) {
  const { label, icon: Icon, spin, badge } = STATUS_STYLE[status];
  return (
    <span className={`inline-flex shrink-0 items-center gap-1.5 rounded-xl px-2.5 py-1 text-xs font-semibold ${badge}`}>
      <Icon className={`size-3.5 ${spin ? "animate-spin" : ""}`} aria-hidden />
      {label}
    </span>
  );
}
