import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { login as apiLogin } from "../api/auth";
import { decodeJwtPayload } from "../api/jwt";
import { getStoredToken, setStoredToken } from "../api/client";
import { getUsuario } from "../api/usuarios";
import type { Usuario } from "../api/types";

interface JwtPayload {
  sub: string;
  role: string;
  exp: number;
}

export interface AuthContextValue {
  user: Usuario | null;
  isLoading: boolean;
  signIn: (email: string, password: string, predioId: number | null) => Promise<void>;
  signOut: () => void;
  refreshUser: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Usuario | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      setIsLoading(false);
      return;
    }
    const payload = decodeJwtPayload<JwtPayload>(token);
    if (!payload) {
      setStoredToken(null);
      setIsLoading(false);
      return;
    }
    getUsuario(Number(payload.sub))
      .then(setUser)
      .catch(() => setStoredToken(null))
      .finally(() => setIsLoading(false));
  }, []);

  async function signIn(email: string, password: string, predioId: number | null): Promise<void> {
    const { access_token } = await apiLogin(email, password, predioId);
    setStoredToken(access_token);
    const payload = decodeJwtPayload<JwtPayload>(access_token);
    if (!payload) {
      setStoredToken(null);
      throw new Error("Token inválido recebido do servidor.");
    }
    const profile = await getUsuario(Number(payload.sub));
    setUser(profile);
  }

  function signOut(): void {
    setStoredToken(null);
    setUser(null);
  }

  async function refreshUser(): Promise<void> {
    if (!user) return;
    const profile = await getUsuario(user.id);
    setUser(profile);
  }

  const value = useMemo<AuthContextValue>(
    () => ({ user, isLoading, signIn, signOut, refreshUser }),
    [user, isLoading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth deve ser usado dentro de <AuthProvider>.");
  }
  return ctx;
}
