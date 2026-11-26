import { useEffect, useState } from "react";

/** «Buenos días», «Buenas tardes» o «Buenas noches» según la hora local. Empieza neutro para no desajustar el HTML. */
export function useGreeting(): string {
  const [greeting, setGreeting] = useState("Hola");
  useEffect(() => {
    const hour = new Date().getHours();
    setGreeting(hour < 12 ? "Buenos días" : hour < 19 ? "Buenas tardes" : "Buenas noches");
  }, []);
  return greeting;
}

export function firstName(name: string | undefined): string {
  return name?.trim().split(/\s+/)[0] ?? "";
}
