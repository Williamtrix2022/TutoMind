import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Permite compilar para producción (auditoría con Lighthouse) sin pisar la carpeta del servidor de desarrollo.
  distDir: process.env.NEXT_DIST_DIR ?? ".next",
};

export default nextConfig;
