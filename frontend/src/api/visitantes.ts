import { apiClient } from "./client";
import type { Visitante, VisitanteCreateInput, VisitanteLoteCreateInput } from "./types";

export async function listVisitantes(filtro: {
  predioId?: number | null;
  unidadeId?: number | null;
} = {}): Promise<Visitante[]> {
  const { data } = await apiClient.get<Visitante[]>("/visitantes", {
    params: { predio_id: filtro.predioId ?? undefined, unidade_id: filtro.unidadeId ?? undefined },
  });
  return data;
}

export async function createVisitante(input: VisitanteCreateInput): Promise<Visitante> {
  const { data } = await apiClient.post<Visitante>("/visitantes", input);
  return data;
}

export async function createVisitantesLote(input: VisitanteLoteCreateInput): Promise<Visitante[]> {
  const { data } = await apiClient.post<Visitante[]>("/visitantes/lote", input);
  return data;
}
