import { apiClient } from "@/lib/api-client";
import type {
  ListUrlsParams,
  Token,
  Url,
  UrlAnalytics,
  UrlCreateInput,
  UrlListResponse,
  UrlUpdateInput,
  User,
} from "@/types/api";

export const authApi = {
  register: (input: { username: string; email: string; password: string }) =>
    apiClient.post<User>("/register", input).then((res) => res.data),

  login: (input: { email: string; password: string }) =>
    apiClient.post<Token>("/login", input).then((res) => res.data),

  me: () => apiClient.get<User>("/me").then((res) => res.data),
};

export const urlsApi = {
  list: (params: ListUrlsParams) =>
    apiClient.get<UrlListResponse>("/urls", { params }).then((res) => res.data),

  create: (input: UrlCreateInput) =>
    apiClient.post<Url>("/urls", input).then((res) => res.data),

  update: (shortCode: string, input: UrlUpdateInput) =>
    apiClient.patch<Url>(`/urls/${shortCode}`, input).then((res) => res.data),

  remove: (shortCode: string) => apiClient.delete(`/urls/${shortCode}`).then(() => undefined),

  analytics: (shortCode: string, days: number, groupBy: "day" | "week") =>
    apiClient
      .get<UrlAnalytics>(`/urls/${shortCode}/analytics`, { params: { days, group_by: groupBy } })
      .then((res) => res.data),
};
