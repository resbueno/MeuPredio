import { apiClient } from "./client";
import type {
  CadastroViaConviteInput,
  Predio,
  PredioConvite,
  PredioConviteInfo,
  PredioCreateInput,
  PredioIdentificado,
  Usuario,
} from "./types";

export async function identificarPredio(cep: string, numero: string): Promise<PredioIdentificado> {
  const { data } = await apiClient.post<PredioIdentificado>("/predios/identificar", { cep, numero });
  return data;
}

export async function listPredios(): Promise<Predio[]> {
  const { data } = await apiClient.get<Predio[]>("/predios");
  return data;
}

export async function createPredio(input: PredioCreateInput): Promise<Predio> {
  const { data } = await apiClient.post<Predio>("/predios", input);
  return data;
}

export async function gerarConvite(predioId: number): Promise<PredioConvite> {
  const { data } = await apiClient.post<PredioConvite>(`/predios/${predioId}/convite`);
  return data;
}

export async function revogarConvite(predioId: number): Promise<void> {
  await apiClient.delete(`/predios/${predioId}/convite`);
}

export async function obterInfoConvite(token: string): Promise<PredioConviteInfo> {
  const { data } = await apiClient.get<PredioConviteInfo>(`/predios/convite/${token}`);
  return data;
}

export async function cadastrarViaConvite(
  token: string,
  input: CadastroViaConviteInput
): Promise<Usuario> {
  const { data } = await apiClient.post<Usuario>(`/predios/convite/${token}/cadastro`, input);
  return data;
}
