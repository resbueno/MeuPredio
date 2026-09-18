import { apiClient } from "./client";
import type { Balancete, DespesaTransparencia } from "./types";

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

export async function baixarDocumento(documentoUrl: string): Promise<string> {
  const { data } = await apiClient.get(documentoUrl, { responseType: "blob" });
  return URL.createObjectURL(data as Blob);
}
