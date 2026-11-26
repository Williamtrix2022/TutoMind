import { TutorChat } from "@/components/tutor/tutor-chat";

export const metadata = { title: "Tutor" };

export default async function TutorPage({ searchParams }: { searchParams: Promise<{ q?: string | string[] }> }) {
  const { q } = await searchParams;
  const question = (Array.isArray(q) ? q[0] : q)?.trim().slice(0, 500);
  return <TutorChat initialQuestion={question || undefined} />;
}
