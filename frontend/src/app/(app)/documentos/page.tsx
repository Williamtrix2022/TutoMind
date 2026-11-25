import { FileUp } from "lucide-react";
import { PagePlaceholder } from "@/components/shell/page-placeholder";

export const metadata = { title: "Documentos" };

export default function DocumentsPage() {
  return (
    <PagePlaceholder
      title="Documentos del curso"
      icon={FileUp}
      description="Aquí vivirá la carga de PDF, DOCX y PPTX (POST /api/v1/courses/{course_id}/documents)."
    />
  );
}
