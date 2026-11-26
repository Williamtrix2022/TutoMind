import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { api } from "../client";
import { toApiError } from "../errors";
import type { RiskLevel } from "@/lib/types";

export function useCourseRisk(courseId: string, level?: RiskLevel) {
  return useQuery({
    queryKey: ["course-risk", courseId, level ?? "all"],
    // Al cambiar de filtro se conserva la lista anterior en vez de parpadear.
    placeholderData: keepPreviousData,
    queryFn: async () => {
      const { data, error, response } = await api.GET("/api/v1/analytics/courses/{course_id}/risk", {
        params: { path: { course_id: courseId }, query: { level } },
      });
      if (!data) throw toApiError(error, response.status);
      return data;
    },
  });
}

export function useCourseTopics(courseId: string) {
  return useQuery({
    queryKey: ["course-topics", courseId],
    queryFn: async () => {
      const { data, error, response } = await api.GET("/api/v1/analytics/courses/{course_id}/topics", {
        params: { path: { course_id: courseId } },
      });
      if (!data) throw toApiError(error, response.status);
      return data;
    },
  });
}
