import { useQuery } from "@tanstack/react-query";
import { api } from "../client";
import { toApiError } from "../errors";

export const documentsKey = (courseId: string) => ["course-documents", courseId] as const;

/** Lista los documentos del curso. Consulta cada 3 s mientras alguno se esté indexando. */
export function useCourseDocuments(courseId: string) {
  return useQuery({
    queryKey: documentsKey(courseId),
    queryFn: async () => {
      const { data, error, response } = await api.GET("/api/v1/courses/{course_id}/documents", {
        params: { path: { course_id: courseId } },
      });
      if (!data) throw toApiError(error, response.status);
      return data;
    },
    refetchInterval: (query) =>
      query.state.data?.documents.some((d) => d.status === "queued" || d.status === "processing") ? 3000 : false,
  });
}
