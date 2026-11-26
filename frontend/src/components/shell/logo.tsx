import { LogoMark } from "@/components/brand/logo-mark";

interface LogoProps {
  /** Muestra siempre el nombre (el encabezado móvil lo oculta en pantallas muy angostas). */
  showName?: "always" | "responsive";
  size?: number;
}

export function Logo({ showName = "responsive", size = 40 }: LogoProps) {
  return (
    <div className="flex items-center gap-3">
      <LogoMark size={size} />
      <span className={`${showName === "always" ? "inline" : "hidden sm:inline"} text-xl tracking-tight`}>
        <span className="font-medium">Tuto</span>
        <span className="font-extrabold">Mind</span>
      </span>
    </div>
  );
}
