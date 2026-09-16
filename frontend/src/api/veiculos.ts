import { apiClient } from "./client";
import type { Veiculo, VeiculoInput } from "./types";

export async function listVeiculos(): Promise<Veiculo[]> {
  const { data } = await apiClient.get<Veiculo[]>("/veiculos");
  return data;
}

export async function createVeiculo(input: VeiculoInput): Promise<Veiculo> {
  const { data } = await apiClient.post<Veiculo>("/veiculos", input);
  return data;
}

export async function updateVeiculo(id: number, input: Partial<VeiculoInput>): Promise<Veiculo> {
  const { data } = await apiClient.patch<Veiculo>(`/veiculos/${id}`, input);
  return data;
}

export async function deleteVeiculo(id: number): Promise<void> {
  await apiClient.delete(`/veiculos/${id}`);
}
