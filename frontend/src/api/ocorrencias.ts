import { apiClient } from "./client";
import type { Ocorrencia, OcorrenciaAtualizarInput, OcorrenciaCreateInput } from "./types";

export async function listOcorrencias(predioId?: number | null): Promise<Ocorrencia[]> {
  const { data } = await apiClient.get<Ocorrencia[]>("/ocorrencias", {
    params: { predio_id: predioId ?? undefined },
  });
  return data;
}

export async function createOcorrencia(input: OcorrenciaCreateInput): Promise<Ocorrencia> {
  const { data } = await apiClient.post<Ocorrencia>("/ocorrencias", input);
  return data;
}

export async function updateOcorrencia(
  id: number,
  input: OcorrenciaAtualizarInput
): Promise<Ocorrencia> {
  const { data } = await apiClient.patch<Ocorrencia>(`/ocorrencias/${id}`, input);
  return data;
}
