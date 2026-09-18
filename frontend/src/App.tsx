import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { Login } from "./pages/Login";
import { Cadastro } from "./pages/Cadastro";
import { Dashboard } from "./pages/Dashboard";
import { UsuariosPage } from "./pages/usuarios/UsuariosPage";
import { PrediosPage } from "./pages/predios/PrediosPage";
import { UnidadesPage } from "./pages/unidades/UnidadesPage";
import { VeiculosPage } from "./pages/veiculos/VeiculosPage";
import { DespesasPage } from "./pages/despesas/DespesasPage";
import { TransparenciaPage } from "./pages/transparencia/TransparenciaPage";
import { TicketsPage } from "./pages/tickets/TicketsPage";
import { AvisosPage } from "./pages/avisos/AvisosPage";
import { AvisosDiretosPage } from "./pages/avisos/AvisosDiretosPage";
import { OcorrenciasPage } from "./pages/ocorrencias/OcorrenciasPage";
import { ReunioesPage } from "./pages/reunioes/ReunioesPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter basename={import.meta.env.BASE_URL}>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/cadastro/:token" element={<Cadastro />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/predios"
              element={
                <ProtectedRoute allowedRoles={["administrador"]}>
                  <PrediosPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/usuarios"
              element={
                <ProtectedRoute allowedRoles={["administrador", "sindico"]}>
                  <UsuariosPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/unidades"
              element={
                <ProtectedRoute>
                  <UnidadesPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/veiculos"
              element={
                <ProtectedRoute>
                  <VeiculosPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/despesas"
              element={
                <ProtectedRoute allowedRoles={["administrador", "sindico"]}>
                  <DespesasPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/transparencia"
              element={
                <ProtectedRoute>
                  <TransparenciaPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/tickets"
              element={
                <ProtectedRoute>
                  <TicketsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/avisos"
              element={
                <ProtectedRoute>
                  <AvisosPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/avisos-diretos"
              element={
                <ProtectedRoute allowedRoles={["administrador", "sindico", "morador", "proprietario"]}>
                  <AvisosDiretosPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/ocorrencias"
              element={
                <ProtectedRoute>
                  <OcorrenciasPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/reunioes"
              element={
                <ProtectedRoute>
                  <ReunioesPage />
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
