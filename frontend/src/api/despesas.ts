import { apiClient } from "./client";
import type { DespesaCreateInput, DespesaLancamento, ExtracaoBoleto } from "./types";

export async function listDespesas(predioId?: number | null): Promise<DespesaLancamento[]> {
  const { data } = await apiClient.get<DespesaLancamento[]>("/despesas", {
    params: predioId != null ? { predio_id: predioId } : undefined,
  });
  return data;
}

export async function createDespesa(input: DespesaCreateInput): Promise<DespesaLancamento> {
  const { data } = await apiClient.post<DespesaLancamento>("/despesas", input);
  return data;
}

export async function updateDespesa(
  id: number,
  input: Partial<DespesaCreateInput>
): Promise<DespesaLancamento> {
  const { data } = await apiClient.patch<DespesaLancamento>(`/despesas/${id}`, input);
  return data;
}

export async function registrarPagamento(id: number): Promise<DespesaLancamento> {
  const { data } = await apiClient.post<DespesaLancamento>(`/despesas/${id}/pagar`, {});
  return data;
}

export async function cancelarDespesa(id: number): Promise<DespesaLancamento> {
  const { data } = await apiClient.post<DespesaLancamento>(`/despesas/${id}/cancelar`);
  return data;
}

export async function desfazerPagamento(id: number): Promise<DespesaLancamento> {
  const { data } = await apiClient.post<DespesaLancamento>(`/despesas/${id}/desfazer-pagamento`);
  return data;
}

export async function extrairBoleto(
  arquivo: File,
  predioId?: number | null
): Promise<ExtracaoBoleto> {
  const formData = new FormData();
  formData.append("arquivo", arquivo);
  if (predioId != null) {
    formData.append("predio_id", String(predioId));
  }
  const { data } = await apiClient.post<ExtracaoBoleto>("/despesas/ocr/extrair", formData);
  return data;
}
