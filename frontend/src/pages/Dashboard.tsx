import { AppShell } from "../components/layout/AppShell";
import { useAuth } from "../auth/AuthContext";

const ROLE_LABELS: Record<string, string> = {
  morador: "Morador",
  sindico: "Sindico",
  zelador: "Zelador",
  administrador: "Administrador",
};

export function Dashboard() {
  const { user } = useAuth();

  return (
    <AppShell>
      <h1 className="text-xl font-bold text-slate-800">Ola, {user?.full_name ?? "usuario"}</h1>
      <p className="mt-1 text-sm text-slate-500">
        Perfil: <span className="font-medium">{user ? ROLE_LABELS[user.role] : ""}</span>
      </p>

      <div className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div className="rounded-2xl bg-white p-4 shadow-sm">
          <p className="text-sm text-slate-500">Unidades e veiculos</p>
          <p className="mt-1 text-sm text-slate-700">
            Use o menu abaixo para navegar entre unidades, veiculos e (se voce for gestor)
            usuarios.
          </p>
        </div>
      </div>
    </AppShell>
  );
}
