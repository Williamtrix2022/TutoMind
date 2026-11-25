import { Moon } from "lucide-react";

export function Logo() {
  return (
    <div className="flex items-center gap-3">
      <span className="grid size-10 place-items-center rounded-2xl bg-primary text-on-primary">
        <Moon className="size-5" aria-hidden />
      </span>
      <span className="text-xl font-bold tracking-tight">TutoMind</span>
    </div>
  );
}
