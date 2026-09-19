import { apiClient } from "./client";
import type { Fornecedor, FornecedorCreateInput } from "./types";

export async function listFornecedores(filtro: {
  predioId?: number | null;
  categoria?: string;
} = {}): Promise<Fornecedor[]> {
  const { data } = await apiClient.get<Fornecedor[]>("/fornecedores", {
    params: { predio_id: filtro.predioId ?? undefined, categoria: filtro.categoria },
  });
  return data;
}

export async function createFornecedor(input: FornecedorCreateInput): Promise<Fornecedor> {
  const { data } = await apiClient.post<Fornecedor>("/fornecedores", input);
  return data;
}
