import { apiClient } from "./client";
import type {
  StatusTicketEnum,
  TicketAtendimento,
  TicketAtualizarInput,
  TicketComentario,
  TicketCreateInput,
} from "./types";

export async function listTickets(filtro: {
  predioId?: number | null;
  status?: StatusTicketEnum;
} = {}): Promise<TicketAtendimento[]> {
  const { data } = await apiClient.get<TicketAtendimento[]>("/tickets", {
    params: { predio_id: filtro.predioId ?? undefined, status: filtro.status },
  });
  return data;
}

export async function createTicket(input: TicketCreateInput): Promise<TicketAtendimento> {
  const { data } = await apiClient.post<TicketAtendimento>("/tickets", input);
  return data;
}

export async function updateTicket(
  id: number,
  input: TicketAtualizarInput
): Promise<TicketAtendimento> {
  const { data } = await apiClient.patch<TicketAtendimento>(`/tickets/${id}`, input);
  return data;
}

export async function assumirTicket(
  id: number,
  responsavelId?: number | null
): Promise<TicketAtendimento> {
  const { data } = await apiClient.post<TicketAtendimento>(`/tickets/${id}/assumir`, {
    responsavel_id: responsavelId ?? undefined,
  });
  return data;
}

export async function resolverTicket(id: number): Promise<TicketAtendimento> {
  const { data } = await apiClient.post<TicketAtendimento>(`/tickets/${id}/resolver`);
  return data;
}

export async function cancelarTicket(id: number): Promise<TicketAtendimento> {
  const { data } = await apiClient.post<TicketAtendimento>(`/tickets/${id}/cancelar`);
  return data;
}

export async function comentarTicket(id: number, mensagem: string): Promise<TicketComentario> {
  const { data } = await apiClient.post<TicketComentario>(`/tickets/${id}/comentarios`, {
    mensagem,
  });
  return data;
}
