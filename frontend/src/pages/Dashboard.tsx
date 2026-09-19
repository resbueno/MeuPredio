import { useMutation, useQueries, useQuery } from "@tanstack/react-query";
import { AppShell } from "../components/layout/AppShell";
import { useAuth } from "../auth/AuthContext";
import { temPapel } from "../auth/roles";
import { listAvisosMural } from "../api/avisosMural";
import { listAvisosDiretos } from "../api/avisosDiretos";
import { aceitarConsentimentoLgpd, revogarConsentimentoLgpd } from "../api/usuarios";
import { listUnidades } from "../api/unidades";
import { getBalanceteSerie, getPreviaUnidade } from "../api/transparencia";
import { listReunioes } from "../api/reunioes";
import { listUsuarios } from "../api/usuarios";
import { listTickets } from "../api/tickets";
import { listEntregas } from "../api/entregas";
import type { TipoReuniaoEnum } from "../api/types";

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

const TIPO_REUNIAO_LABEL: Record<TipoReuniaoEnum, string> = {
  ordinaria: "Ordinária",
  extraordinaria: "Extraordinária",
};

function formatarData(data: string): string {
  return new Date(data).toLocaleDateString("pt-BR");
}

function formatarConvocacao(dataHora: string): { data: string; diaSemana: string; hora: string } {
  const d = new Date(dataHora);
  return {
    data: d.toLocaleDateString("pt-BR"),
    diaSemana: d.toLocaleDateString("pt-BR", { weekday: "long" }),
    hora: d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
  };
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
  const souSindico = temPapel(user, "sindico");
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

  const { data: convocacoes, isLoading: carregandoConvocacoes } = useQuery({
    queryKey: ["reunioes", "proprio", "convocada"],
    queryFn: () => listReunioes({ status: "convocada" }),
    enabled: !souAdministrador,
  });

  const { data: usuariosPredio } = useQuery({
    queryKey: ["usuarios", "visao-geral"],
    queryFn: listUsuarios,
    enabled: souSindico,
  });

  const { data: ticketsPredio } = useQuery({
    queryKey: ["tickets", "visao-geral"],
    queryFn: () => listTickets(),
    enabled: souSindico,
  });

  const { data: entregasPendentes } = useQuery({
    queryKey: ["entregas", "visao-geral"],
    queryFn: () => listEntregas({ apenasPendentes: true }),
    enabled: souSindico,
  });

  const { data: serieMensal } = useQuery({
    queryKey: ["transparencia", "serie", "visao-geral"],
    queryFn: () => getBalanceteSerie({ meses: 6 }),
    enabled: souSindico,
  });

  const totalMoradores =
    usuariosPredio?.filter(
      (u) =>
        u.role === "morador" ||
        u.role === "proprietario" ||
        u.papeis_extra.includes("morador") ||
        u.papeis_extra.includes("proprietario")
    ).length ?? 0;

  const novosAcessosHoje =
    usuariosPredio?.filter((u) => {
      if (!u.last_login_at) return false;
      return new Date(u.last_login_at).toDateString() === new Date().toDateString();
    }).length ?? 0;

  const manutencoesEmAndamento =
    ticketsPredio?.filter(
      (t) => t.categoria === "manutencao" && (t.status === "aberto" || t.status === "em_andamento")
    ).length ?? 0;

  const valoresSerie = (serieMensal ?? []).map((m) => Number(m.total_geral));
  const maxSerie = Math.max(1, ...valoresSerie);

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

      {souSindico ? (
        <div className="mt-6 rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
          <p className="mb-3 text-sm font-semibold text-slate-700">Visão geral do condomínio</p>

          <div className="grid grid-cols-3 gap-2">
            <div className="rounded-xl bg-slate-50 p-2.5 text-center sm:text-left">
              <p className="text-[11px] text-slate-500">Moradores</p>
              <p className="text-lg font-bold text-ink">{totalMoradores}</p>
              <p className="text-[10px] text-emerald-600">Vinculados</p>
            </div>
            <div className="rounded-xl bg-slate-50 p-2.5 text-center sm:text-left">
              <p className="text-[11px] text-slate-500">Manutenções</p>
              <p className="text-lg font-bold text-ink">{String(manutencoesEmAndamento).padStart(2, "0")}</p>
              <p className="text-[10px] text-amber-600">Em andamento</p>
            </div>
            <div className="rounded-xl bg-slate-50 p-2.5 text-center sm:text-left">
              <p className="text-[11px] text-slate-500">Entregas</p>
              <p className="text-lg font-bold text-ink">{entregasPendentes?.length ?? 0}</p>
              <p className="text-[10px] text-brand-600">Aguardando retirada</p>
            </div>
          </div>

          {valoresSerie.length > 0 && (
            <div className="mt-3 rounded-xl bg-slate-50 p-3">
              <p className="text-[11px] font-medium text-slate-500">Atividade financeira (6 meses)</p>
              <div className="mt-2 flex h-14 items-end gap-1.5">
                {valoresSerie.map((valor, indice) => (
                  <div
                    key={indice}
                    className={`w-full rounded-t-sm ${
                      indice === valoresSerie.length - 1 ? "bg-brand-600" : "bg-brand-200"
                    }`}
                    style={{ height: `${Math.max(8, (valor / maxSerie) * 100)}%` }}
                  />
                ))}
              </div>
            </div>
          )}

          <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
            <div className="rounded-xl bg-slate-50 p-3">
              <p className="text-[11px] font-medium text-slate-500">Avisos recentes</p>
              <ul className="mt-1.5 space-y-1 text-[11px] text-slate-600">
                {avisosCondominio?.slice(0, 2).map((aviso) => <li key={aviso.id}>• {aviso.titulo}</li>)}
                {(!avisosCondominio || avisosCondominio.length === 0) && (
                  <li className="text-slate-400">Nenhum aviso recente.</li>
                )}
              </ul>
            </div>
            <div className="rounded-xl bg-slate-50 p-3">
              <p className="text-[11px] font-medium text-slate-500">Moradores</p>
              <ul className="mt-1.5 space-y-1 text-[11px] text-slate-600">
                <li>• {novosAcessosHoje} novo(s) acesso(s) hoje</li>
              </ul>
            </div>
          </div>
        </div>
      ) : (
        <div className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div className="rounded-2xl bg-white p-4 shadow-sm">
            <p className="text-sm text-slate-500">Unidades e veículos</p>
            <p className="mt-1 text-sm text-slate-700">
              Use o menu abaixo para navegar entre unidades, veículos e (se você for gestor)
              usuários.
            </p>
          </div>
        </div>
      )}

      {!souAdministrador && (
        <div className="mt-6">
          <h2 className="mb-2 text-sm font-semibold text-slate-700">Próximas reuniões</h2>
          {carregandoConvocacoes && <p className="text-sm text-slate-500">Carregando...</p>}
          <ul className="space-y-2">
            {convocacoes?.map((reuniao) => {
              const { data, diaSemana, hora } = formatarConvocacao(reuniao.data_hora);
              return (
                <li key={reuniao.id} className="rounded-xl bg-white p-3 shadow-sm">
                  <div className="flex items-start justify-between gap-2">
                    <p className="font-medium text-slate-800">{reuniao.titulo}</p>
                    <span className="shrink-0 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">
                      {TIPO_REUNIAO_LABEL[reuniao.tipo]}
                    </span>
                  </div>
                  <p className="mt-1 text-sm capitalize text-slate-600">
                    {diaSemana}, {data} às {hora}
                  </p>
                  <p className="text-xs text-slate-500">{reuniao.local}</p>
                </li>
              );
            })}
            {convocacoes?.length === 0 && (
              <li className="rounded-xl bg-white p-4 text-center text-sm text-slate-500 shadow-sm">
                Nenhuma reunião convocada no momento.
              </li>
            )}
          </ul>
        </div>
      )}

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
