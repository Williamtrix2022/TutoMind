import { AuthGate } from "@/components/auth/auth-gate";
import { RoleGuard } from "@/components/auth/role-guard";
import { AppShell } from "@/components/shell/app-shell";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGate>
      <AppShell>
        <RoleGuard>{children}</RoleGuard>
      </AppShell>
    </AuthGate>
  );
}
