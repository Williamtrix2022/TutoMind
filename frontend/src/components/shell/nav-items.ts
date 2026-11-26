import { Activity, FileUp, House, MessagesSquare, Thermometer } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { Role } from "@/lib/types";

export interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
}

export const NAV_BY_ROLE: Record<Role, NavItem[]> = {
  student: [
    { href: "/", label: "Inicio", icon: House },
    { href: "/tutor", label: "Tutor", icon: MessagesSquare },
  ],
  teacher: [
    { href: "/", label: "Inicio", icon: House },
    { href: "/riesgo", label: "Riesgo", icon: Activity },
    { href: "/temas", label: "Temas", icon: Thermometer },
    { href: "/documentos", label: "Documentos", icon: FileUp },
  ],
};
