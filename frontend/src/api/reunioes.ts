import { apiClient } from "./client";
import type {
  Reuniao,
  ReuniaoAtualizarInput,
  ReuniaoCreateInput,
  ReuniaoPresenca,
  StatusReuniaoEnum,
} from "./types";

export async function listReunioes(filtro: {
  predioId?: number | null;
  status?: StatusReuniaoEnum;
} = {}): Promise<Reuniao[]> {
  const { data } = await apiClient.get<Reuniao[]>("/reunioes", {
    params: { predio_id: filtro.predioId ?? undefined, status: filtro.status },
  });
  return data;
}

export async function createReuniao(input: ReuniaoCreateInput): Promise<Reuniao> {
  const { data } = await apiClient.post<Reuniao>("/reunioes", input);
  return data;
}

export async function updateReuniao(id: number, input: ReuniaoAtualizarInput): Promise<Reuniao> {
  const { data } = await apiClient.patch<Reuniao>(`/reunioes/${id}`, input);
  return data;
}

export async function cancelarReuniao(id: number): Promise<Reuniao> {
  const { data } = await apiClient.post<Reuniao>(`/reunioes/${id}/cancelar`);
  return data;
}

export async function registrarAta(id: number, ata: string): Promise<Reuniao> {
  const { data } = await apiClient.post<Reuniao>(`/reunioes/${id}/ata`, { ata });
  return data;
}

export async function confirmarPresenca(id: number, unidadeId: number): Promise<ReuniaoPresenca> {
  const { data } = await apiClient.post<ReuniaoPresenca>(`/reunioes/${id}/presenca`, {
    unidade_id: unidadeId,
  });
  return data;
}

export async function removerPresenca(id: number, unidadeId: number): Promise<void> {
  await apiClient.delete(`/reunioes/${id}/presenca/${unidadeId}`);
}
