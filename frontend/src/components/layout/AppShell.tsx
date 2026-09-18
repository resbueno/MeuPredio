import type { ReactNode } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import { temPapel } from "../../auth/roles";
import type { RoleEnum } from "../../api/types";
import logoIcon from "../../assets/logo-icon.png";

interface NavItem {
  to: string;
  label: string;
  roles?: RoleEnum[];
}

const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Início" },
  { to: "/predios", label: "Prédios", roles: ["administrador"] },
  { to: "/usuarios", label: "Usuários", roles: ["administrador", "sindico"] },
  { to: "/unidades", label: "Unidades" },
  { to: "/veiculos", label: "Veículos" },
  { to: "/despesas", label: "Contas", roles: ["administrador", "sindico"] },
  { to: "/transparencia", label: "Transparência" },
  { to: "/avisos", label: "Avisos Gerais" },
  { to: "/avisos-diretos", label: "Avisos Diretos", roles: ["administrador", "sindico", "morador", "proprietario"] },
  { to: "/ocorrencias", label: "Ocorrências" },
  { to: "/tickets", label: "Chamados" },
  { to: "/reunioes", label: "Reuniões" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  function handleSignOut(): void {
    signOut();
    navigate("/login", { replace: true });
  }

  const visibleItems = NAV_ITEMS.filter(
    (item) => !item.roles || temPapel(user, ...item.roles)
  );

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 md:flex-row">
      {user && (
        <aside className="hidden shrink-0 border-r border-slate-200 bg-white md:flex md:w-56 md:flex-col">
          <div className="flex items-center gap-2 border-b border-slate-200 px-4 py-4">
            <img src={logoIcon} alt="" className="h-8 w-auto" />
            <span className="text-lg font-bold tracking-tight text-ink">
              Meu<span className="text-brand-600">Prédio</span>
            </span>
          </div>
          <nav className="flex-1 overflow-y-auto py-2">
            <ul className="space-y-0.5 px-2">
              {visibleItems.map((item) => (
                <li key={item.to}>
                  <NavLink
                    to={item.to}
                    end={item.to === "/"}
                    className={({ isActive }) =>
                      `block rounded-lg px-3 py-2 text-sm font-medium ${
                        isActive
                          ? "bg-brand-50 text-brand-600"
                          : "text-slate-600 hover:bg-slate-100 hover:text-slate-800"
                      }`
                    }
                  >
                    {item.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
          <div className="border-t border-slate-200 p-2">
            <button
              type="button"
              onClick={handleSignOut}
              className="w-full rounded-lg px-3 py-2 text-left text-sm font-medium text-slate-500 transition hover:bg-slate-100 hover:text-slate-800"
            >
              Sair
            </button>
          </div>
        </aside>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/90 backdrop-blur md:hidden">
          <div className="flex items-center justify-between px-4 py-3">
            <div className="flex items-center gap-2">
              <img src={logoIcon} alt="" className="h-8 w-auto" />
              <span className="text-lg font-bold tracking-tight text-ink">
                Meu<span className="text-brand-600">Prédio</span>
              </span>
            </div>
            {user && (
              <button
                type="button"
                onClick={handleSignOut}
                className="rounded-lg px-3 py-1.5 text-sm font-medium text-slate-500 transition hover:bg-slate-100 hover:text-slate-800"
              >
                Sair
              </button>
            )}
          </div>
        </header>

        <main className="flex-1 px-4 py-4 pb-24 md:pb-4">
          <div className="mx-auto w-full max-w-3xl">{children}</div>
        </main>

        {user && (
          <nav className="fixed inset-x-0 bottom-0 z-10 border-t border-slate-200 bg-white pb-[env(safe-area-inset-bottom)] md:hidden">
            {/* Mais itens do que cabem numa tela de celular de uma vez -
                rola horizontalmente em vez de espremer tudo (flex-1 faria
                cada rotulo virar ilegivel com 12 itens). */}
            <ul
              className="flex gap-1 overflow-x-auto px-1 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
            >
              {visibleItems.map((item) => (
                <li key={item.to} className="shrink-0">
                  <NavLink
                    to={item.to}
                    end={item.to === "/"}
                    className={({ isActive }) =>
                      `flex min-w-[64px] flex-col items-center gap-0.5 px-2 py-2 text-center text-[11px] font-medium leading-tight ${
                        isActive ? "text-brand-600" : "text-slate-500"
                      }`
                    }
                  >
                    {item.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
        )}
      </div>
    </div>
  );
}
