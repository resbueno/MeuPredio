import type { ReactNode } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import type { RoleEnum } from "../../api/types";
import logoIcon from "../../assets/logo-icon.png";

interface NavItem {
  to: string;
  label: string;
  roles?: RoleEnum[];
}

const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Inicio" },
  { to: "/predios", label: "Predios", roles: ["administrador"] },
  { to: "/usuarios", label: "Usuarios", roles: ["administrador", "sindico"] },
  { to: "/unidades", label: "Unidades" },
  { to: "/veiculos", label: "Veiculos" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  function handleSignOut(): void {
    signOut();
    navigate("/login", { replace: true });
  }

  const visibleItems = NAV_ITEMS.filter(
    (item) => !item.roles || (user && item.roles.includes(user.role))
  );

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/90 backdrop-blur">
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

      <main className="flex-1 px-4 py-4 pb-24">{children}</main>

      {user && (
        <nav className="fixed inset-x-0 bottom-0 z-10 border-t border-slate-200 bg-white pb-[env(safe-area-inset-bottom)]">
          <ul className="flex justify-around">
            {visibleItems.map((item) => (
              <li key={item.to} className="flex-1">
                <NavLink
                  to={item.to}
                  end={item.to === "/"}
                  className={({ isActive }) =>
                    `flex flex-col items-center gap-0.5 py-2 text-xs font-medium ${
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
  );
}
