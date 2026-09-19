import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter, Navigate, Route, Routes } from "react-router-dom";
import { apiClient } from "../../api/client";
import { AuthContext, type AuthContextValue } from "../../auth/AuthContext";
import { Dashboard } from "../../pages/Dashboard";
import { UnidadesPage } from "../../pages/unidades/UnidadesPage";
import { DespesasPage } from "../../pages/despesas/DespesasPage";
import { TransparenciaPage } from "../../pages/transparencia/TransparenciaPage";
import { AvisosPage } from "../../pages/avisos/AvisosPage";
import { AvisosDiretosPage } from "../../pages/avisos/AvisosDiretosPage";
import { OcorrenciasPage } from "../../pages/ocorrencias/OcorrenciasPage";
import { TicketsPage } from "../../pages/tickets/TicketsPage";
import { ReunioesPage } from "../../pages/reunioes/ReunioesPage";
import { EntregasPage } from "../../pages/entregas/EntregasPage";
import { VisitantesPage } from "../../pages/visitantes/VisitantesPage";
import { ReservasPage } from "../../pages/reservas/ReservasPage";
import { DemoContext } from "./demo/DemoContext";
import { criarAdapterFalso, usuarioDemo } from "./demo/fakeApi";

// Módulos simulados na prévia - exatamente as páginas reais do sistema, só
// com dados fictícios em memória (ver demo/fakeApi.ts). Prédios, Usuários e
// Veículos ficam de fora da prévia (não simulados), não do sistema.
const ROTAS_DISPONIVEIS = [
  "/", "/unidades", "/despesas", "/transparencia", "/avisos", "/avisos-diretos",
  "/ocorrencias", "/tickets", "/reunioes", "/entregas", "/visitantes", "/reservas",
];

// Capturado uma vez, quando o módulo carrega (antes de qualquer prévia abrir):
// é o adapter de rede real, para onde voltar ao fechar.
const ADAPTER_REAL = apiClient.defaults.adapter;

function DemoApp({ onClose }: { onClose: () => void }) {
  const [pronto, setPronto] = useState(false);
  const queryClient = useMemo(
    () => new QueryClient({ defaultOptions: { queries: { retry: 0, refetchOnWindowFocus: false } } }),
    []
  );
  const auth = useMemo<AuthContextValue>(
    () => ({
      user: usuarioDemo(),
      isLoading: false,
      signIn: async () => {},
      signOut: () => {},
      refreshUser: async () => {},
    }),
    []
  );
  const demo = useMemo(() => ({ onClose, rotasDisponiveis: ROTAS_DISPONIVEIS }), [onClose]);

  // Layout effect (não useEffect): precisa rodar ANTES das queries dos
  // filhos dispararem, senão a primeira leva de requisições iria pra rede.
  useLayoutEffect(() => {
    const meuAdapter = criarAdapterFalso();
    apiClient.defaults.adapter = meuAdapter;
    setPronto(true);
    return () => {
      // Só restaura se o adapter ainda é o meu - outra raiz da prévia (ex.:
      // remontagem do StrictMode em dev) pode já ter instalado o dela.
      if (apiClient.defaults.adapter === meuAdapter) {
        apiClient.defaults.adapter = ADAPTER_REAL;
      }
      queryClient.clear();
    };
  }, [queryClient]);

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-white">
      <div className="flex shrink-0 items-center justify-between gap-3 bg-ink px-4 py-2 text-white">
        <p className="text-xs sm:text-sm">
          <span className="font-semibold">Prévia interativa</span> - este é o sistema real, com dados
          fictícios. Nada do que você fizer aqui é salvo.
        </p>
        <button
          type="button"
          onClick={onClose}
          className="shrink-0 rounded-lg border border-white/30 px-3 py-1 text-xs font-medium hover:bg-white/10"
        >
          Fechar prévia
        </button>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        {pronto && (
          <QueryClientProvider client={queryClient}>
            <AuthContext.Provider value={auth}>
              <DemoContext.Provider value={demo}>
                <MemoryRouter initialEntries={["/"]}>
                  <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/unidades" element={<UnidadesPage />} />
                    <Route path="/despesas" element={<DespesasPage />} />
                    <Route path="/transparencia" element={<TransparenciaPage />} />
                    <Route path="/avisos" element={<AvisosPage />} />
                    <Route path="/avisos-diretos" element={<AvisosDiretosPage />} />
                    <Route path="/ocorrencias" element={<OcorrenciasPage />} />
                    <Route path="/tickets" element={<TicketsPage />} />
                    <Route path="/reunioes" element={<ReunioesPage />} />
                    <Route path="/entregas" element={<EntregasPage />} />
                    <Route path="/visitantes" element={<VisitantesPage />} />
                    <Route path="/reservas" element={<ReservasPage />} />
                    <Route path="*" element={<Navigate to="/" replace />} />
                  </Routes>
                </MemoryRouter>
              </DemoContext.Provider>
            </AuthContext.Provider>
          </QueryClientProvider>
        )}
      </div>
    </div>
  );
}

/**
 * A prévia usa o próprio MemoryRouter, e o React Router não permite Router
 * dentro de Router - por isso ela roda em uma raiz React separada, montada
 * em um nó próprio do <body>, em vez de como filha da landing page.
 */
export function DemoTour({ onClose }: { onClose: () => void }) {
  // Ref: o pai passa uma função nova a cada render, e remontar a raiz
  // reiniciaria (apagaria) tudo que a pessoa criou na prévia.
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  useEffect(() => {
    const container = document.createElement("div");
    document.body.appendChild(container);
    const root = createRoot(container);
    root.render(<DemoApp onClose={() => onCloseRef.current()} />);
    return () => {
      setTimeout(() => {
        root.unmount();
        container.remove();
      }, 0);
    };
  }, []);

  return null;
}
