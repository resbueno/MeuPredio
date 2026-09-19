import { apiClient } from "./client";
import type { Reserva, ReservaCreateInput } from "./types";

export async function listReservas(filtro: {
  predioId?: number | null;
  areaComumId?: number | null;
  unidadeId?: number | null;
} = {}): Promise<Reserva[]> {
  const { data } = await apiClient.get<Reserva[]>("/reservas", {
    params: {
      predio_id: filtro.predioId ?? undefined,
      area_comum_id: filtro.areaComumId ?? undefined,
      unidade_id: filtro.unidadeId ?? undefined,
    },
  });
  return data;
}

export async function createReserva(input: ReservaCreateInput): Promise<Reserva> {
  const { data } = await apiClient.post<Reserva>("/reservas", input);
  return data;
}

export async function cancelarReserva(id: number): Promise<Reserva> {
  const { data } = await apiClient.post<Reserva>(`/reservas/${id}/cancelar`);
  return data;
}
