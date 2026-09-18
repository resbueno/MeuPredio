import { apiClient } from "./client";
import type { Unidade, UnidadeInput } from "./types";

export async function listUnidades(predioId?: number | null): Promise<Unidade[]> {
  const { data } = await apiClient.get<Unidade[]>("/unidades", {
    params: { predio_id: predioId ?? undefined },
  });
  return data;
}

export async function createUnidade(input: UnidadeInput): Promise<Unidade> {
  const { data } = await apiClient.post<Unidade>("/unidades", input);
  return data;
}

export async function createUnidadesLote(input: {
  unidades: { bloco: string; numero: string }[];
  predio_id?: number | null;
}): Promise<Unidade[]> {
  const { data } = await apiClient.post<Unidade[]>("/unidades/lote", input);
  return data;
}

export async function updateUnidade(id: number, input: Partial<UnidadeInput>): Promise<Unidade> {
  const { data } = await apiClient.patch<Unidade>(`/unidades/${id}`, input);
  return data;
}

export async function deleteUnidade(id: number): Promise<void> {
  await apiClient.delete(`/unidades/${id}`);
}
