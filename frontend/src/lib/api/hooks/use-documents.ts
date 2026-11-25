import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../client";
import { toApiError } from "../errors";

interface UploadInput {
  file: File;
  title?: string;
}

export function useUploadDocument(courseId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ file, title }: UploadInput) => {
      const { data, error, response } = await api.POST("/api/v1/courses/{course_id}/documents", {
        params: { path: { course_id: courseId } },
        // El contrato tipa `file` como string binario; el cuerpo real se arma como FormData.
        body: { file: file.name, title },
        bodySerializer: () => {
          const form = new FormData();
          form.append("file", file);
          if (title) form.append("title", title);
          return form;
        },
      });
      if (!data) throw toApiError(error, response.status);
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["course-documents", courseId] }),
  });
}
