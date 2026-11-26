"use client";

import { StudentHome } from "@/components/home/student-home";
import { TeacherHome } from "@/components/home/teacher-home";
import { useApp } from "@/lib/providers/app-providers";

export function HomeView() {
  const { role } = useApp();
  return role === "student" ? <StudentHome /> : <TeacherHome />;
}
