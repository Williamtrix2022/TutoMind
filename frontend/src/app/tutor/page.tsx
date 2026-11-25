import { MessagesSquare } from "lucide-react";
import { PagePlaceholder } from "@/components/shell/page-placeholder";

export const metadata = { title: "Tutor" };

export default function TutorPage() {
  return (
    <PagePlaceholder
      title="Tutor"
      icon={MessagesSquare}
      description="Aquí vivirá el chat con el tutor (POST /api/v1/tutor/chat/stream)."
    />
  );
}
