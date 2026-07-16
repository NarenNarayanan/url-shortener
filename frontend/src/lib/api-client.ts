import axios from "axios";
import { clearToken, getToken } from "@/lib/auth-storage";

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
});

apiClient.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// A 401 means the token is missing/expired/invalid — clear it and force a
// fresh login rather than letting the app sit in a half-authenticated state.
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && window.location.pathname !== "/login") {
      clearToken();
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data;
    if (typeof data?.detail === "string") return data.detail;
    if (typeof data?.error === "string") return data.error;
    if (Array.isArray(data?.detail) && data.detail[0]?.msg) return data.detail[0].msg;
    if (error.message) return error.message;
  }
  return "Something went wrong. Please try again.";
}
