import { Thermometer } from "lucide-react";
import { PagePlaceholder } from "@/components/shell/page-placeholder";

export const metadata = { title: "Temas consultados" };

export default function TopicsPage() {
  return (
    <PagePlaceholder
      title="Temas consultados"
      icon={Thermometer}
      description="Aquí vivirá el termómetro del aula (GET /api/v1/analytics/courses/{course_id}/topics)."
    />
  );
}
