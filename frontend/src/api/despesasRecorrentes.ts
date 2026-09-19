import { apiClient } from "./client";
import type {
  DespesaLancamento,
  DespesaRecorrente,
  DespesaRecorrenteCreateInput,
} from "./types";

export async function listDespesasRecorrentes(filtro: {
  predioId?: number | null;
  incluirInativas?: boolean;
} = {}): Promise<DespesaRecorrente[]> {
  const { data } = await apiClient.get<DespesaRecorrente[]>("/despesas-recorrentes", {
    params: {
      predio_id: filtro.predioId ?? undefined,
      incluir_inativas: filtro.incluirInativas ?? undefined,
    },
  });
  return data;
}

export async function createDespesaRecorrente(
  input: DespesaRecorrenteCreateInput
): Promise<DespesaRecorrente> {
  const { data } = await apiClient.post<DespesaRecorrente>("/despesas-recorrentes", input);
  return data;
}

export async function updateDespesaRecorrente(
  id: number,
  input: Partial<DespesaRecorrenteCreateInput> & { ativo?: boolean }
): Promise<DespesaRecorrente> {
  const { data } = await apiClient.patch<DespesaRecorrente>(`/despesas-recorrentes/${id}`, input);
  return data;
}

export async function deleteDespesaRecorrente(id: number): Promise<void> {
  await apiClient.delete(`/despesas-recorrentes/${id}`);
}

export async function gerarPendentes(predioId?: number | null): Promise<DespesaLancamento[]> {
  const { data } = await apiClient.post<DespesaLancamento[]>(
    "/despesas-recorrentes/gerar-pendentes",
    null,
    { params: { predio_id: predioId ?? undefined } }
  );
  return data;
}
