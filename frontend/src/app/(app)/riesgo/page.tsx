import { Activity } from "lucide-react";
import { PagePlaceholder } from "@/components/shell/page-placeholder";

export const metadata = { title: "Riesgo académico" };

export default function RiskPage() {
  return (
    <PagePlaceholder
      title="Riesgo académico"
      icon={Activity}
      description="Aquí vivirá el semáforo con factores XAI (GET /api/v1/analytics/courses/{course_id}/risk)."
    />
  );
}
