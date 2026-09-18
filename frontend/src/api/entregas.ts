import { apiClient } from "./client";
import type { Entrega, EntregaCreateInput } from "./types";

export async function listEntregas(filtro: {
  predioId?: number | null;
  unidadeId?: number | null;
  apenasPendentes?: boolean;
} = {}): Promise<Entrega[]> {
  const { data } = await apiClient.get<Entrega[]>("/entregas", {
    params: {
      predio_id: filtro.predioId ?? undefined,
      unidade_id: filtro.unidadeId ?? undefined,
      apenas_pendentes: filtro.apenasPendentes ?? undefined,
    },
  });
  return data;
}

export async function createEntrega(input: EntregaCreateInput): Promise<Entrega> {
  const { data } = await apiClient.post<Entrega>("/entregas", input);
  return data;
}

export async function marcarEntregaRetirada(id: number): Promise<Entrega> {
  const { data } = await apiClient.post<Entrega>(`/entregas/${id}/retirar`);
  return data;
}
