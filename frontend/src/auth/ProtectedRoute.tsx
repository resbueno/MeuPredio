import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "./AuthContext";
import type { RoleEnum } from "../api/types";
import { SplashScreen } from "../components/SplashScreen";

interface ProtectedRouteProps {
  children: ReactNode;
  allowedRoles?: RoleEnum[];
}

export function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <SplashScreen />;
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-2 px-4 text-center">
        <p className="text-lg font-semibold text-slate-800">Acesso restrito</p>
        <p className="text-slate-500">Voce nao tem permissao para acessar esta pagina.</p>
      </div>
    );
  }

  return <>{children}</>;
}
