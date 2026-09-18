import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { AppShell } from "../../components/layout/AppShell";
import { useAuth } from "../../auth/AuthContext";
import { temPapel } from "../../auth/roles";
import {
  baixarDocumento,
  getBalancete,
  getBalanceteSerie,
  getPreviaUnidade,
  listDespesasTransparencia,
} from "../../api/transparencia";
import { listUnidades } from "../../api/unidades";
import { GraficoCategoria, GraficoTendencia } from "../../components/charts/TransparenciaCharts";
import type { DespesaTransparencia, StatusDespesaEnum } from "../../api/types";

const STATUS_LABEL: Record<StatusDespesaEnum, string> = {
  pendente: "Pendente",
  pago: "Paga",
  cancelado: "Cancelada",
};

const STATUS_CLASSES: Record<StatusDespesaEnum, string> = {
  pendente: "bg-amber-100 text-amber-700",
  pago: "bg-emerald-100 text-emerald-700",
  cancelado: "bg-slate-200 text-slate-500",
};

const MESES = [
  "Janeiro",
  "Fevereiro",
  "Março",
  "Abril",
  "Maio",
  "Junho",
  "Julho",
  "Agosto",
  "Setembro",
  "Outubro",
  "Novembro",
  "Dezembro",
];

function formatarValor(valor: string): string {
  const numero = Number(valor);
  return Number.isFinite(numero)
    ? numero.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
    : valor;
}

export function TransparenciaPage() {
  const { user } = useAuth();
  const souAdministrador = user?.role === "administrador";
  const souGestao = temPapel(user, "administrador", "sindico", "zelador");

  const hoje = new Date();
  const [predioIdAdminInput, setPredioIdAdminInput] = useState("");
  const predioIdAdmin = predioIdAdminInput.trim() ? Number(predioIdAdminInput.trim()) : null;
  const bloqueadoSemPredio = souAdministrador && !predioIdAdmin;

  const [ano, setAno] = useState(hoje.getFullYear());
  const [mes, setMes] = useState(hoje.getMonth() + 1);
  const [unidadeIdPreviaInput, setUnidadeIdPreviaInput] = useState("");

  const filtro = { predioId: souAdministrador ? predioIdAdmin : undefined, ano, mes };

  const { data: balancete, isLoading: carregandoBalancete } = useQuery({
    queryKey: ["transparencia-balancete", filtro],
    queryFn: () => getBalancete(filtro),
    enabled: !bloqueadoSemPredio,
  });

  const { data: serieMensal } = useQuery({
    queryKey: ["transparencia-balancete-serie", filtro.predioId],
    queryFn: () => getBalanceteSerie({ predioId: filtro.predioId, meses: 6 }),
    enabled: !bloqueadoSemPredio,
  });

  const { data: despesas, isLoading: carregandoDespesas } = useQuery({
    queryKey: ["transparencia-despesas", filtro],
    queryFn: () => listDespesasTransparencia(filtro),
    enabled: !bloqueadoSemPredio,
  });

  const { data: unidadesCombo } = useQuery({
    queryKey: ["unidades", "combo", filtro.predioId],
    queryFn: () => listUnidades(filtro.predioId),
    enabled: souGestao && !bloqueadoSemPredio,
  });

  const unidadeIdPrevia = souGestao
    ? unidadeIdPreviaInput
      ? Number(unidadeIdPreviaInput)
      : null
    : undefined;

  const { data: previaUnidade, isLoading: carregandoPrevia } = useQuery({
    queryKey: ["transparencia-previa-unidade", filtro.predioId, unidadeIdPrevia, ano, mes],
    queryFn: () => getPreviaUnidade({ predioId: filtro.predioId, unidadeId: unidadeIdPrevia, ano, mes }),
    enabled: !bloqueadoSemPredio && (!souGestao || unidadeIdPrevia != null),
  });

  async function verDocumento(despesa: DespesaTransparencia): Promise<void> {
    if (!despesa.documento_url) return;
    const url = await baixarDocumento(despesa.documento_url);
    window.open(url, "_blank", "noopener,noreferrer");
  }

  return (
    <AppShell>
      <h1 className="mb-4 text-xl font-bold text-slate-800">Portal da Transparência</h1>

      {souAdministrador && (
        <div className="mb-6 rounded-2xl bg-white p-4 shadow-sm">
          <label className="mb-1 block text-xs font-medium text-slate-600">ID do prédio</label>
          <input
            inputMode="numeric"
            value={predioIdAdminInput}
            onChange={(event) => setPredioIdAdminInput(event.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            placeholder="Ex.: 1"
          />
        </div>
      )}

      <div className="mb-6 flex gap-3 rounded-2xl bg-white p-4 shadow-sm">
        <div className="flex-1">
          <label className="mb-1 block text-xs font-medium text-slate-600">Mês</label>
          <select
            value={mes}
            onChange={(event) => setMes(Number(event.target.value))}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          >
            {MESES.map((nome, indice) => (
              <option key={nome} value={indice + 1}>
                {nome}
              </option>
            ))}
          </select>
        </div>
        <div className="flex-1">
          <label className="mb-1 block text-xs font-medium text-slate-600">Ano</label>
          <input
            inputMode="numeric"
            value={ano}
            onChange={(event) => setAno(Number(event.target.value) || hoje.getFullYear())}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
      </div>

      {bloqueadoSemPredio && (
        <p className="mb-4 text-sm text-amber-600">Informe o ID do prédio acima para continuar.</p>
      )}

      {!bloqueadoSemPredio && (
        <>
          <div className="mb-6 grid grid-cols-3 gap-2">
            <div className="rounded-2xl bg-white p-3 text-center shadow-sm">
              <p className="text-xs text-slate-500">Pago</p>
              <p className="text-sm font-semibold text-emerald-700">
                {carregandoBalancete ? "..." : formatarValor(balancete?.total_pago ?? "0")}
              </p>
            </div>
            <div className="rounded-2xl bg-white p-3 text-center shadow-sm">
              <p className="text-xs text-slate-500">Pendente</p>
              <p className="text-sm font-semibold text-amber-700">
                {carregandoBalancete ? "..." : formatarValor(balancete?.total_pendente ?? "0")}
              </p>
            </div>
            <div className="rounded-2xl bg-white p-3 text-center shadow-sm">
              <p className="text-xs text-slate-500">Total</p>
              <p className="text-sm font-semibold text-slate-800">
                {carregandoBalancete ? "..." : formatarValor(balancete?.total_geral ?? "0")}
              </p>
            </div>
          </div>

          {serieMensal && serieMensal.length >= 2 && (
            <div className="mb-6 rounded-2xl bg-white p-4 shadow-sm">
              <h2 className="mb-2 text-sm font-semibold text-slate-700">Tendência (últimos 6 meses)</h2>
              <GraficoTendencia
                pontos={serieMensal.map((p) => ({
                  ano: p.ano,
                  mes: p.mes,
                  total_geral: Number(p.total_geral),
                }))}
              />
            </div>
          )}

          {balancete && balancete.por_categoria.length > 0 && (
            <div className="mb-6 rounded-2xl bg-white p-4 shadow-sm">
              <h2 className="mb-2 text-sm font-semibold text-slate-700">Por categoria</h2>
              <GraficoCategoria
                itens={balancete.por_categoria.map((item) => ({
                  categoria: item.categoria,
                  total: Number(item.total),
                }))}
              />
            </div>
          )}

          {(!souGestao || unidadesCombo) && (
            <div className="mb-6 rounded-2xl bg-white p-4 shadow-sm">
              <h2 className="mb-2 text-sm font-semibold text-slate-700">Prévia da conta da unidade</h2>
              {souGestao && (
                <div className="mb-3">
                  <label className="mb-1 block text-xs font-medium text-slate-600">Unidade</label>
                  <select
                    value={unidadeIdPreviaInput}
                    onChange={(event) => setUnidadeIdPreviaInput(event.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  >
                    <option value="">Selecione...</option>
                    {unidadesCombo?.map((unidade) => (
                      <option key={unidade.id} value={unidade.id}>
                        Bloco {unidade.bloco} - {unidade.numero}
                      </option>
                    ))}
                  </select>
                </div>
              )}
              {carregandoPrevia && <p className="text-sm text-slate-500">Carregando...</p>}
              {previaUnidade && (
                <>
                  <div className="mb-3 grid grid-cols-3 gap-2">
                    <div className="rounded-xl bg-slate-50 p-2 text-center">
                      <p className="text-xs text-slate-500">Rateio</p>
                      <p className="text-sm font-semibold text-slate-700">
                        {formatarValor(previaUnidade.total_rateio)}
                      </p>
                    </div>
                    <div className="rounded-xl bg-slate-50 p-2 text-center">
                      <p className="text-xs text-slate-500">Multas</p>
                      <p className="text-sm font-semibold text-red-700">
                        {formatarValor(previaUnidade.total_multas)}
                      </p>
                    </div>
                    <div className="rounded-xl bg-slate-50 p-2 text-center">
                      <p className="text-xs text-slate-500">Total a pagar</p>
                      <p className="text-sm font-semibold text-slate-800">
                        {formatarValor(previaUnidade.total_geral)}
                      </p>
                    </div>
                  </div>
                  <ul className="space-y-1">
                    {previaUnidade.itens.map((item) => (
                      <li
                        key={`${item.tipo}-${item.despesa_id}`}
                        className="flex justify-between text-sm text-slate-600"
                      >
                        <span>
                          {item.descricao}
                          {item.tipo === "multa" && (
                            <span className="ml-1 text-xs text-red-600">(multa)</span>
                          )}
                        </span>
                        <span className="font-medium">{formatarValor(item.valor)}</span>
                      </li>
                    ))}
                    {previaUnidade.itens.length === 0 && (
                      <li className="text-sm text-slate-500">Nenhum item neste período.</li>
                    )}
                  </ul>
                </>
              )}
            </div>
          )}

          <h2 className="mb-2 text-sm font-semibold text-slate-700">Prestação de contas</h2>
          {carregandoDespesas && <p className="text-sm text-slate-500">Carregando...</p>}
          <ul className="space-y-2">
            {despesas?.map((despesa) => (
              <li key={despesa.id} className="rounded-xl bg-white p-3 shadow-sm">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-medium text-slate-800">{despesa.descricao}</p>
                    <p className="text-xs text-slate-500">
                      {despesa.categoria} - Vencimento{" "}
                      {new Date(`${despesa.data_vencimento}T00:00:00`).toLocaleDateString("pt-BR")}
                    </p>
                  </div>
                  <span
                    className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_CLASSES[despesa.status]}`}
                  >
                    {STATUS_LABEL[despesa.status]}
                    {despesa.esta_atrasada ? " - atrasada" : ""}
                  </span>
                </div>
                <div className="mt-2 flex items-center justify-between">
                  <p className="text-sm font-semibold text-slate-700">{formatarValor(despesa.valor)}</p>
                  {despesa.documento_url && (
                    <button
                      type="button"
                      onClick={() => verDocumento(despesa)}
                      className="text-xs font-medium text-brand-600"
                    >
                      Ver documento
                    </button>
                  )}
                </div>
              </li>
            ))}
            {despesas?.length === 0 && (
              <li className="rounded-xl bg-white p-4 text-center text-sm text-slate-500 shadow-sm">
                Nenhuma conta neste período.
              </li>
            )}
          </ul>
        </>
      )}
    </AppShell>
  );
}
