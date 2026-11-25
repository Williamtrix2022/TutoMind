import { useMutation } from "@tanstack/react-query";
import { api } from "../client";
import { toApiError } from "../errors";
import type { components } from "../schema";
import { setToken } from "../token-store";

export type LoginRequest = components["schemas"]["LoginRequest"];

export function useLogin() {
  return useMutation({
    mutationFn: async (body: LoginRequest) => {
      const { data, error, response } = await api.POST("/api/v1/auth/login", { body });
      if (!data) throw toApiError(error, response.status);
      setToken(data.access_token);
      return data;
    },
  });
}
