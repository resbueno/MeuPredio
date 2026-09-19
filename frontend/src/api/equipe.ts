import { apiClient } from "./client";
import type {
  DespesaLancamento,
  Funcionario,
  FuncionarioInput,
  PrestadorServico,
  PrestadorServicoInput,
} from "./types";

export async function listFuncionarios(incluirInativos = false): Promise<Funcionario[]> {
  const { data } = await apiClient.get<Funcionario[]>("/funcionarios", {
    params: { incluir_inativos: incluirInativos || undefined },
  });
  return data;
}

export async function createFuncionario(input: FuncionarioInput): Promise<Funcionario> {
  const { data } = await apiClient.post<Funcionario>("/funcionarios", input);
  return data;
}

export async function updateFuncionario(id: number, input: Partial<FuncionarioInput>): Promise<Funcionario> {
  const { data } = await apiClient.patch<Funcionario>(`/funcionarios/${id}`, input);
  return data;
}

export async function deleteFuncionario(id: number): Promise<void> {
  await apiClient.delete(`/funcionarios/${id}`);
}

export async function listPrestadores(incluirInativos = false): Promise<PrestadorServico[]> {
  const { data } = await apiClient.get<PrestadorServico[]>("/prestadores-servico", {
    params: { incluir_inativos: incluirInativos || undefined },
  });
  return data;
}

export async function createPrestador(input: PrestadorServicoInput): Promise<PrestadorServico> {
  const { data } = await apiClient.post<PrestadorServico>("/prestadores-servico", input);
  return data;
}

export async function updatePrestador(
  id: number,
  input: Partial<PrestadorServicoInput>
): Promise<PrestadorServico> {
  const { data } = await apiClient.patch<PrestadorServico>(`/prestadores-servico/${id}`, input);
  return data;
}

export async function deletePrestador(id: number): Promise<void> {
  await apiClient.delete(`/prestadores-servico/${id}`);
}

export async function lancarCustoPrestador(
  id: number,
  input: { data_vencimento: string; observacoes?: string | null }
): Promise<DespesaLancamento> {
  const { data } = await apiClient.post<DespesaLancamento>(`/prestadores-servico/${id}/lancar-custo`, input);
  return data;
}

export async function listLancamentosPrestador(id: number): Promise<DespesaLancamento[]> {
  const { data } = await apiClient.get<DespesaLancamento[]>(`/prestadores-servico/${id}/lancamentos`);
  return data;
}
