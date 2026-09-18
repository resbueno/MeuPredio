import { apiClient } from "./client";
import type { AvisoDireto, AvisoDiretoCreateInput } from "./types";

export async function listAvisosDiretos(filtro: {
  predioId?: number | null;
  unidadeId?: number | null;
} = {}): Promise<AvisoDireto[]> {
  const { data } = await apiClient.get<AvisoDireto[]>("/avisos-diretos", {
    params: { predio_id: filtro.predioId ?? undefined, unidade_id: filtro.unidadeId ?? undefined },
  });
  return data;
}

export async function createAvisoDireto(input: AvisoDiretoCreateInput): Promise<AvisoDireto> {
  const { data } = await apiClient.post<AvisoDireto>("/avisos-diretos", input);
  return data;
}

export async function marcarAvisoDiretoLido(id: number): Promise<AvisoDireto> {
  const { data } = await apiClient.post<AvisoDireto>(`/avisos-diretos/${id}/marcar-lido`);
  return data;
}

export async function responderAvisoDireto(id: number, resposta: string): Promise<AvisoDireto> {
  const { data } = await apiClient.post<AvisoDireto>(`/avisos-diretos/${id}/responder`, { resposta });
  return data;
}

export async function deleteAvisoDireto(id: number): Promise<void> {
  await apiClient.delete(`/avisos-diretos/${id}`);
}
