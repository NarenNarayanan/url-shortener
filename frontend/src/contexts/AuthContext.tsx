import { createContext, useContext, useState, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { authApi } from "@/lib/api";
import { clearToken, getToken, setToken } from "@/lib/auth-storage";
import type { User } from "@/types/api";

interface AuthContextValue {
  user: User | undefined;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [hasToken, setHasToken] = useState(() => Boolean(getToken()));
  const queryClient = useQueryClient();

  // A stale/expired token discovered mid-session (the `me` query below
  // getting a 401) is handled by the axios response interceptor — it clears
  // the token and does a full-page redirect to /login, which remounts this
  // provider and recomputes `hasToken` from scratch. No need to duplicate
  // that logic here by watching for query errors.
  const { data: user, isLoading } = useQuery({
    queryKey: ["me"],
    queryFn: authApi.me,
    enabled: hasToken,
    retry: false,
  });

  async function login(email: string, password: string) {
    const token = await authApi.login({ email, password });
    setToken(token.access_token);
    setHasToken(true);
    await queryClient.invalidateQueries({ queryKey: ["me"] });
  }

  async function register(username: string, email: string, password: string) {
    await authApi.register({ username, email, password });
    await login(email, password);
  }

  function logout() {
    clearToken();
    setHasToken(false);
    queryClient.clear();
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: hasToken && Boolean(user),
        isLoading: hasToken && isLoading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
