import type { Metadata, Viewport } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import { AppShell } from "@/components/shell/app-shell";
import { AppProviders } from "@/lib/providers/app-providers";
import "katex/dist/katex.min.css";
import "./globals.css";

const jakarta = Plus_Jakarta_Sans({
  variable: "--font-jakarta",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: { default: "TutoMind", template: "%s · TutoMind" },
  description: "Tutor inteligente y analítica predictiva de riesgo académico.",
  manifest: "/manifest.json",
  applicationName: "TutoMind",
  icons: {
    icon: "/icons/icon-192.png",
    apple: "/icons/apple-touch-icon.png",
  },
  appleWebApp: { capable: true, title: "TutoMind", statusBarStyle: "black-translucent" },
};

export const viewport: Viewport = {
  themeColor: "#03174C",
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

/** Aplica el tema guardado (o el del sistema) antes de pintar, sin parpadeo. */
const themeScript = `(function(){try{var t=localStorage.getItem("tm-theme");if(t!=="light"&&t!=="dark"){t=window.matchMedia("(prefers-color-scheme: light)").matches?"light":"dark"}document.documentElement.dataset.theme=t;var m=document.querySelector('meta[name="theme-color"]');if(m)m.setAttribute("content",t==="dark"?"#03174C":"#F6F7FB")}catch(e){document.documentElement.dataset.theme="dark"}})();`;

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es" data-theme="dark" suppressHydrationWarning className={jakarta.variable}>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body>
        <AppProviders>
          <AppShell>{children}</AppShell>
        </AppProviders>
      </body>
    </html>
  );
}
