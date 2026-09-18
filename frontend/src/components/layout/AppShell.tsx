import { useState } from "react";
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
  const [menuOpen, setMenuOpen] = useState(false);

  function handleSignOut(): void {
    signOut();
    navigate("/login", { replace: true });
  }

  const visibleItems = NAV_ITEMS.filter(
    (item) => !item.roles || temPapel(user, ...item.roles)
  );

  function renderNavList(onNavigate?: () => void) {
    return (
      <ul className="space-y-0.5 px-2">
        {visibleItems.map((item) => (
          <li key={item.to}>
            <NavLink
              to={item.to}
              end={item.to === "/"}
              onClick={onNavigate}
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
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 lg:flex-row">
      {/* Sidebar fixa - so em telas grandes (desktop). Em celular/tablet o
          menu vira uma gaveta recolhivel acionada pelo botao hamburguer. */}
      {user && (
        <aside className="hidden shrink-0 border-r border-slate-200 bg-white lg:flex lg:w-56 lg:flex-col">
          <div className="flex items-center gap-2 border-b border-slate-200 px-4 py-4">
            <img src={logoIcon} alt="" className="h-8 w-auto" />
            <span className="text-lg font-bold tracking-tight text-ink">
              Meu<span className="text-brand-600">Prédio</span>
            </span>
          </div>
          <nav className="flex-1 overflow-y-auto py-2">{renderNavList()}</nav>
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
        <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur lg:hidden">
          <div className="flex items-center justify-between px-4 py-3">
            <div className="flex items-center gap-2">
              {user && (
                <button
                  type="button"
                  onClick={() => setMenuOpen(true)}
                  aria-label="Abrir menu"
                  className="-ml-1.5 rounded-lg p-1.5 text-slate-600 hover:bg-slate-100"
                >
                  <svg viewBox="0 0 24 24" fill="none" className="h-6 w-6">
                    <path
                      d="M4 6h16M4 12h16M4 18h16"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                    />
                  </svg>
                </button>
              )}
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

        <main className="flex-1 px-4 py-4">
          <div className="mx-auto w-full max-w-3xl">{children}</div>
        </main>
      </div>

      {user && menuOpen && (
        <div className="fixed inset-0 z-30 lg:hidden">
          <div
            className="absolute inset-0 bg-slate-900/40"
            onClick={() => setMenuOpen(false)}
            aria-hidden="true"
          />
          <aside className="absolute inset-y-0 left-0 flex w-64 max-w-[80%] flex-col bg-white pb-[env(safe-area-inset-bottom)] shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-200 px-4 py-4">
              <div className="flex items-center gap-2">
                <img src={logoIcon} alt="" className="h-8 w-auto" />
                <span className="text-lg font-bold tracking-tight text-ink">
                  Meu<span className="text-brand-600">Prédio</span>
                </span>
              </div>
              <button
                type="button"
                onClick={() => setMenuOpen(false)}
                aria-label="Fechar menu"
                className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100"
              >
                <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5">
                  <path
                    d="M6 6l12 12M18 6L6 18"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                  />
                </svg>
              </button>
            </div>
            <nav className="flex-1 overflow-y-auto py-2">
              {renderNavList(() => setMenuOpen(false))}
            </nav>
            <div className="border-t border-slate-200 p-2">
              <button
                type="button"
                onClick={() => {
                  setMenuOpen(false);
                  handleSignOut();
                }}
                className="w-full rounded-lg px-3 py-2 text-left text-sm font-medium text-slate-500 transition hover:bg-slate-100 hover:text-slate-800"
              >
                Sair
              </button>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}
