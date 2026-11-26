import type { LucideIcon } from "lucide-react";
import { Card } from "@/components/ui/card";

interface PagePlaceholderProps {
  title: string;
  description: string;
  icon: LucideIcon;
}

export function PagePlaceholder({ title, description, icon: Icon }: PagePlaceholderProps) {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl md:text-4xl">{title}</h1>
      <Card className="flex flex-col items-start gap-4 p-8">
        <span className="grid size-12 place-items-center rounded-2xl bg-glow/25 text-glow">
          <Icon className="size-6" aria-hidden />
        </span>
        <p className="max-w-prose text-muted">{description}</p>
      </Card>
    </div>
  );
}
