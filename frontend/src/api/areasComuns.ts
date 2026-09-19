import { apiClient } from "./client";
import type { AreaComum, AreaComumAtualizarInput, AreaComumCreateInput } from "./types";

export async function listAreasComuns(filtro: {
  predioId?: number | null;
  apenasAtivas?: boolean;
} = {}): Promise<AreaComum[]> {
  const { data } = await apiClient.get<AreaComum[]>("/areas-comuns", {
    params: { predio_id: filtro.predioId ?? undefined, apenas_ativas: filtro.apenasAtivas ?? undefined },
  });
  return data;
}

export async function createAreaComum(input: AreaComumCreateInput): Promise<AreaComum> {
  const { data } = await apiClient.post<AreaComum>("/areas-comuns", input);
  return data;
}

export async function updateAreaComum(id: number, input: AreaComumAtualizarInput): Promise<AreaComum> {
  const { data } = await apiClient.patch<AreaComum>(`/areas-comuns/${id}`, input);
  return data;
}

export async function liberarAgendaAreaComum(
  id: number,
  opcoes: { dias?: number; ate?: string }
): Promise<AreaComum> {
  const { data } = await apiClient.post<AreaComum>(`/areas-comuns/${id}/liberar-agenda`, opcoes);
  return data;
}

export async function deleteAreaComum(id: number): Promise<void> {
  await apiClient.delete(`/areas-comuns/${id}`);
}
