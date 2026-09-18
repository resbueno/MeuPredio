import { AppShell } from "../components/layout/AppShell";
import { useAuth } from "../auth/AuthContext";

const ROLE_LABELS: Record<string, string> = {
  morador: "Morador",
  sindico: "Síndico",
  zelador: "Zelador",
  administrador: "Administrador",
};

export function Dashboard() {
  const { user } = useAuth();

  return (
    <AppShell>
      <h1 className="text-xl font-bold text-slate-800">Olá, {user?.full_name ?? "usuário"}</h1>
      <p className="mt-1 text-sm text-slate-500">
        Perfil: <span className="font-medium">{user ? ROLE_LABELS[user.role] : ""}</span>
      </p>

      <div className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div className="rounded-2xl bg-white p-4 shadow-sm">
          <p className="text-sm text-slate-500">Unidades e veículos</p>
          <p className="mt-1 text-sm text-slate-700">
            Use o menu abaixo para navegar entre unidades, veículos e (se você for gestor)
            usuários.
          </p>
        </div>
      </div>
    </AppShell>
  );
}
