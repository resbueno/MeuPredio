import { useMutation, useQueries, useQuery } from "@tanstack/react-query";
import { AppShell } from "../components/layout/AppShell";
import { useAuth } from "../auth/AuthContext";
import { temPapel } from "../auth/roles";
import { listAvisosMural } from "../api/avisosMural";
import { listAvisosDiretos } from "../api/avisosDiretos";
import { aceitarConsentimentoLgpd, revogarConsentimentoLgpd } from "../api/usuarios";
import { listUnidades } from "../api/unidades";
import { getPreviaUnidade } from "../api/transparencia";

const ROLE_LABELS: Record<string, string> = {
  morador: "Morador",
  sindico: "Síndico",
  zelador: "Zelador",
  administrador: "Administrador",
};

const TIPO_AVISO_DIRETO_LABEL: Record<string, string> = {
  aviso: "Aviso",
  advertencia: "Advertência",
  multa: "Multa",
};

const MESES_ABREV = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];

function formatarData(data: string): string {
  return new Date(data).toLocaleDateString("pt-BR");
}

function formatarValor(valor: string): string {
  const numero = Number(valor);
  return Number.isFinite(numero)
    ? numero.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
    : valor;
}

export function Dashboard() {
  const { user, refreshUser } = useAuth();
  const souAdministrador = user?.role === "administrador";
  const recebeAvisoDireto = temPapel(user, "morador", "proprietario");

  const aceitarConsentimentoMutation = useMutation({
    mutationFn: () => aceitarConsentimentoLgpd(user!.id),
    onSuccess: refreshUser,
  });
  const revogarConsentimentoMutation = useMutation({
    mutationFn: () => revogarConsentimentoLgpd(user!.id),
    onSuccess: refreshUser,
  });

  const { data: avisosCondominio, isLoading } = useQuery({
    queryKey: ["avisos-mural", "proprio", "condominio"],
    queryFn: () => listAvisosMural({ tipo: "condominio" }),
    enabled: !souAdministrador,
  });

  const { data: avisosDiretos, isLoading: carregandoDiretos } = useQuery({
    queryKey: ["avisos-diretos", "proprio"],
    queryFn: () => listAvisosDiretos(),
    enabled: recebeAvisoDireto,
  });

  const hoje = new Date();
  const anoAtual = hoje.getFullYear();
  const mesAtual = hoje.getMonth() + 1;

  const { data: minhasUnidades } = useQuery({
    queryKey: ["unidades", "minhas"],
    queryFn: () => listUnidades(),
    enabled: recebeAvisoDireto,
    select: (todas) => todas.filter((u) => user?.unidade_ids.includes(u.id)),
  });

  const previasPorUnidade = useQueries({
    queries: (minhasUnidades ?? []).map((unidade) => ({
      queryKey: ["previa-unidade", unidade.id, anoAtual, mesAtual],
      queryFn: () => getPreviaUnidade({ unidadeId: unidade.id, ano: anoAtual, mes: mesAtual }),
      enabled: recebeAvisoDireto,
    })),
  });

  return (
    <AppShell>
      <h1 className="text-xl font-bold text-slate-800">Olá, {user?.full_name ?? "usuário"}</h1>
      <p className="mt-1 text-sm text-slate-500">
        Perfil: <span className="font-medium">{user ? ROLE_LABELS[user.role] : ""}</span>
      </p>

      {user && !user.consent_lgpd_accepted_at && (
        <div className="mt-4 rounded-2xl bg-amber-50 p-4 shadow-sm">
          <p className="text-sm font-medium text-amber-800">Consentimento de dados (LGPD)</p>
          <p className="mt-1 text-sm text-amber-700">
            Para usar o sistema, você precisa concordar com o tratamento dos seus dados pessoais
            (nome, e-mail, unidade e histórico de uso) pelo MeuPrédio, conforme a Lei Geral de
            Proteção de Dados.
          </p>
          <button
            type="button"
            onClick={() => aceitarConsentimentoMutation.mutate()}
            disabled={aceitarConsentimentoMutation.isPending}
            className="mt-2 rounded-lg bg-amber-600 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-700 disabled:opacity-60"
          >
            Aceitar
          </button>
        </div>
      )}
      {user && user.consent_lgpd_accepted_at && (
        <p className="mt-1 text-xs text-slate-400">
          Consentimento LGPD aceito em{" "}
          {new Date(user.consent_lgpd_accepted_at).toLocaleDateString("pt-BR")} ·{" "}
          <button
            type="button"
            onClick={() => revogarConsentimentoMutation.mutate()}
            disabled={revogarConsentimentoMutation.isPending}
            className="font-medium text-slate-500 underline hover:text-slate-700"
          >
            Revogar
          </button>
        </p>
      )}

      <div className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div className="rounded-2xl bg-white p-4 shadow-sm">
          <p className="text-sm text-slate-500">Unidades e veículos</p>
          <p className="mt-1 text-sm text-slate-700">
            Use o menu abaixo para navegar entre unidades, veículos e (se você for gestor)
            usuários.
          </p>
        </div>
      </div>

      {recebeAvisoDireto && (
        <div className="mt-6">
          <h2 className="mb-2 text-sm font-semibold text-slate-700">Avisos para minha unidade</h2>
          {carregandoDiretos && <p className="text-sm text-slate-500">Carregando...</p>}
          <ul className="space-y-2">
            {avisosDiretos?.map((aviso) => (
              <li key={aviso.id} className="rounded-xl bg-white p-3 shadow-sm">
                <div className="flex items-start justify-between gap-2">
                  <p className="font-medium text-slate-800">{aviso.titulo}</p>
                  <span className="shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
                    {TIPO_AVISO_DIRETO_LABEL[aviso.tipo]}
                  </span>
                </div>
                <p className="mt-1 whitespace-pre-wrap text-sm text-slate-600">{aviso.mensagem}</p>
                <p className="mt-2 text-xs text-slate-400">
                  {formatarData(aviso.created_at)}
                  {!aviso.lida_em && " - não lido"}
                </p>
              </li>
            ))}
            {avisosDiretos?.length === 0 && (
              <li className="rounded-xl bg-white p-4 text-center text-sm text-slate-500 shadow-sm">
                Nenhum aviso direto para sua unidade.
              </li>
            )}
          </ul>
        </div>
      )}

      {recebeAvisoDireto && minhasUnidades && minhasUnidades.length > 0 && (
        <div className="mt-6">
          <h2 className="mb-2 text-sm font-semibold text-slate-700">
            Prévia do condomínio ({MESES_ABREV[mesAtual - 1]}/{anoAtual})
          </h2>
          <div className="space-y-3">
            {minhasUnidades.map((unidade, indice) => {
              const previa = previasPorUnidade[indice];
              return (
                <div key={unidade.id} className="rounded-xl bg-white p-3 shadow-sm">
                  <p className="mb-2 text-sm font-medium text-slate-800">
                    Bloco {unidade.bloco} - {unidade.numero}
                  </p>
                  {previa?.isLoading && <p className="text-sm text-slate-500">Carregando...</p>}
                  {previa?.data && (
                    <div className="grid grid-cols-3 gap-2">
                      <div className="rounded-lg bg-slate-50 p-2 text-center">
                        <p className="text-xs text-slate-500">Rateio</p>
                        <p className="text-sm font-semibold text-slate-700">
                          {formatarValor(previa.data.total_rateio)}
                        </p>
                      </div>
                      <div className="rounded-lg bg-slate-50 p-2 text-center">
                        <p className="text-xs text-slate-500">Multas</p>
                        <p className="text-sm font-semibold text-red-700">
                          {formatarValor(previa.data.total_multas)}
                        </p>
                      </div>
                      <div className="rounded-lg bg-slate-50 p-2 text-center">
                        <p className="text-xs text-slate-500">Total</p>
                        <p className="text-sm font-semibold text-slate-800">
                          {formatarValor(previa.data.total_geral)}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {!souAdministrador && (
        <div className="mt-6">
          <h2 className="mb-2 text-sm font-semibold text-slate-700">Avisos do condomínio</h2>
          {isLoading && <p className="text-sm text-slate-500">Carregando...</p>}
          <ul className="space-y-2">
            {avisosCondominio?.map((aviso) => (
              <li key={aviso.id} className="rounded-xl bg-white p-3 shadow-sm">
                <p className="font-medium text-slate-800">{aviso.titulo}</p>
                <p className="mt-1 whitespace-pre-wrap text-sm text-slate-600">{aviso.descricao}</p>
                <p className="mt-2 text-xs text-slate-400">{formatarData(aviso.created_at)}</p>
              </li>
            ))}
            {avisosCondominio?.length === 0 && (
              <li className="rounded-xl bg-white p-4 text-center text-sm text-slate-500 shadow-sm">
                Nenhum aviso de condomínio no momento.
              </li>
            )}
          </ul>
        </div>
      )}
    </AppShell>
  );
}
