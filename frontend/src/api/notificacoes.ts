import { apiClient } from "./client";
import type { Notificacao, NotificacaoContagem } from "./types";

export async function listNotificacoes(filtro: { apenasNaoLidas?: boolean } = {}): Promise<Notificacao[]> {
  const { data } = await apiClient.get<Notificacao[]>("/notificacoes", {
    params: { apenas_nao_lidas: filtro.apenasNaoLidas ?? undefined },
  });
  return data;
}

export async function contarNotificacoesNaoLidas(): Promise<NotificacaoContagem> {
  const { data } = await apiClient.get<NotificacaoContagem>("/notificacoes/contagem-nao-lidas");
  return data;
}

export async function marcarNotificacaoLida(id: number): Promise<Notificacao> {
  const { data } = await apiClient.post<Notificacao>(`/notificacoes/${id}/marcar-lida`);
  return data;
}

export async function marcarTodasNotificacoesLidas(): Promise<void> {
  await apiClient.post("/notificacoes/marcar-todas-lidas");
}
