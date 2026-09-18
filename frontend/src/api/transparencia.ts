import { apiClient } from "./client";
import type { Balancete, BalanceteMensal, DespesaTransparencia, PreviaUnidade } from "./types";

export { baixarDocumento } from "./documentos";

interface FiltroPeriodo {
  predioId?: number | null;
  ano?: number;
  mes?: number;
}

export async function listDespesasTransparencia(
  filtro: FiltroPeriodo = {}
): Promise<DespesaTransparencia[]> {
  const { data } = await apiClient.get<DespesaTransparencia[]>("/transparencia/despesas", {
    params: {
      predio_id: filtro.predioId ?? undefined,
      ano: filtro.ano,
      mes: filtro.mes,
    },
  });
  return data;
}

export async function getBalancete(filtro: FiltroPeriodo = {}): Promise<Balancete> {
  const { data } = await apiClient.get<Balancete>("/transparencia/balancete", {
    params: {
      predio_id: filtro.predioId ?? undefined,
      ano: filtro.ano,
      mes: filtro.mes,
    },
  });
  return data;
}

export async function getBalanceteSerie(
  filtro: { predioId?: number | null; meses?: number } = {}
): Promise<BalanceteMensal[]> {
  const { data } = await apiClient.get<BalanceteMensal[]>("/transparencia/balancete/serie", {
    params: { predio_id: filtro.predioId ?? undefined, meses: filtro.meses },
  });
  return data;
}

export async function getPreviaUnidade(filtro: {
  predioId?: number | null;
  unidadeId?: number | null;
  ano?: number;
  mes?: number;
} = {}): Promise<PreviaUnidade> {
  const { data } = await apiClient.get<PreviaUnidade>("/transparencia/previa-unidade", {
    params: {
      predio_id: filtro.predioId ?? undefined,
      unidade_id: filtro.unidadeId ?? undefined,
      ano: filtro.ano,
      mes: filtro.mes,
    },
  });
  return data;
}

