import { apiClient } from "./client";
import type { AvisoMural, AvisoMuralAtualizarInput, AvisoMuralCreateInput, TipoAvisoMuralEnum } from "./types";

export async function listAvisosMural(filtro: {
  predioId?: number | null;
  tipo?: TipoAvisoMuralEnum;
} = {}): Promise<AvisoMural[]> {
  const { data } = await apiClient.get<AvisoMural[]>("/avisos-mural", {
    params: { predio_id: filtro.predioId ?? undefined, tipo: filtro.tipo },
  });
  return data;
}

export async function createAvisoMural(input: AvisoMuralCreateInput): Promise<AvisoMural> {
  const { data } = await apiClient.post<AvisoMural>("/avisos-mural", input);
  return data;
}

export async function updateAvisoMural(
  id: number,
  input: AvisoMuralAtualizarInput
): Promise<AvisoMural> {
  const { data } = await apiClient.patch<AvisoMural>(`/avisos-mural/${id}`, input);
  return data;
}

export async function deleteAvisoMural(id: number): Promise<void> {
  await apiClient.delete(`/avisos-mural/${id}`);
}
