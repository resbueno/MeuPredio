import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { AppShell } from "../../components/layout/AppShell";
import { useAuth } from "../../auth/AuthContext";
import { temPapel } from "../../auth/roles";
import {
  createAreaComum,
  deleteAreaComum,
  liberarAgendaAreaComum,
  listAreasComuns,
  updateAreaComum,
} from "../../api/areasComuns";
import { cancelarReserva, createReserva, listReservas } from "../../api/reservas";
import { listUnidades } from "../../api/unidades";
import type { AreaComum } from "../../api/types";

const areaSchema = z.object({
  nome: z.string().min(2, "Informe o nome da área."),
  descricao: z.string().optional(),
  capacidade: z.string().optional(),
});

type AreaFormValues = z.infer<typeof areaSchema>;

const reservaSchema = z.object({
  area_comum_id: z.string().min(1, "Selecione a área."),
  data: z.string().min(1, "Selecione a data."),
  unidade_id: z.string().optional(),
  observacoes: z.string().optional(),
});

type ReservaFormValues = z.infer<typeof reservaSchema>;

function formatarData(data: string): string {
  return new Date(`${data}T00:00:00`).toLocaleDateString("pt-BR");
}

function LiberarAgendaForm({ area }: { area: AreaComum }) {
  const queryClient = useQueryClient();
  const [dias, setDias] = useState("60");

  const mutation = useMutation({
    mutationFn: () => liberarAgendaAreaComum(area.id, { dias: Number(dias) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["areas-comuns"] }),
  });

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        if (Number(dias) > 0) mutation.mutate();
      }}
      className="mt-2 flex items-center gap-2"
    >
      <span className="text-xs text-slate-500">Liberar próximos</span>
      <input
        inputMode="numeric"
        value={dias}
        onChange={(event) => setDias(event.target.value)}
        className="w-16 rounded-lg border border-slate-300 px-2 py-1 text-xs"
      />
      <span className="text-xs text-slate-500">dias</span>
      <button
        type="submit"
        disabled={mutation.isPending}
        className="rounded-lg bg-brand-600 px-3 py-1 text-xs font-semibold text-white disabled:opacity-60"
      >
        Aplicar
      </button>
    </form>
  );
}

export function ReservasPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const souGestao = temPapel(user, "administrador", "sindico");
  const souAdministrador = user?.role === "administrador";

  const [predioIdAdminInput, setPredioIdAdminInput] = useState("");
  const predioIdAdmin = predioIdAdminInput.trim() ? Number(predioIdAdminInput.trim()) : null;
  const bloqueadoSemPredio = souAdministrador && !predioIdAdmin;

  const { data: areas, isLoading: carregandoAreas } = useQuery({
    queryKey: ["areas-comuns", souAdministrador ? predioIdAdmin : "proprio"],
    queryFn: () => listAreasComuns({ predioId: souAdministrador ? predioIdAdmin : undefined }),
    enabled: !bloqueadoSemPredio,
  });

  const { data: reservas, isLoading: carregandoReservas } = useQuery({
    queryKey: ["reservas", souAdministrador ? predioIdAdmin : "proprio"],
    queryFn: () => listReservas({ predioId: souAdministrador ? predioIdAdmin : undefined }),
    enabled: !bloqueadoSemPredio,
  });

  const { data: unidades } = useQuery({
    queryKey: ["unidades", "combo", souAdministrador ? predioIdAdmin : "proprio"],
    queryFn: () => listUnidades(souAdministrador ? predioIdAdmin : undefined),
    enabled: souGestao && !bloqueadoSemPredio,
  });

  function labelArea(areaId: number): string {
    return areas?.find((a) => a.id === areaId)?.nome ?? `Área #${areaId}`;
  }

  function labelUnidade(unidadeId: number): string {
    const unidade = unidades?.find((u) => u.id === unidadeId);
    return unidade ? `Bloco ${unidade.bloco} - ${unidade.numero}` : `Unidade #${unidadeId}`;
  }

  const areaForm = useForm<AreaFormValues>({
    resolver: zodResolver(areaSchema),
    defaultValues: { nome: "", descricao: "", capacidade: "" },
  });

  const invalidateAreas = () => queryClient.invalidateQueries({ queryKey: ["areas-comuns"] });
  const invalidateReservas = () => queryClient.invalidateQueries({ queryKey: ["reservas"] });

  const criarAreaMutation = useMutation({
    mutationFn: createAreaComum,
    onSuccess: () => {
      invalidateAreas();
      areaForm.reset({ nome: "", descricao: "", capacidade: "" });
    },
  });

  const toggleAtivoMutation = useMutation({
    mutationFn: ({ id, ativo }: { id: number; ativo: boolean }) => updateAreaComum(id, { ativo }),
    onSuccess: invalidateAreas,
  });

  const removerAreaMutation = useMutation({ mutationFn: deleteAreaComum, onSuccess: invalidateAreas });

  function onSubmitArea(values: AreaFormValues): void {
    if (souAdministrador && !predioIdAdmin) return;
    criarAreaMutation.mutate({
      nome: values.nome,
      descricao: values.descricao || undefined,
      capacidade: values.capacidade ? Number(values.capacidade) : undefined,
      predio_id: souAdministrador ? predioIdAdmin : undefined,
    });
  }

  const reservaForm = useForm<ReservaFormValues>({
    resolver: zodResolver(reservaSchema),
    defaultValues: { area_comum_id: "", data: "", unidade_id: "", observacoes: "" },
  });

  const criarReservaMutation = useMutation({
    mutationFn: createReserva,
    onSuccess: () => {
      invalidateReservas();
      reservaForm.reset({ area_comum_id: "", data: "", unidade_id: "", observacoes: "" });
    },
  });

  const cancelarReservaMutation = useMutation({ mutationFn: cancelarReserva, onSuccess: invalidateReservas });

  function onSubmitReserva(values: ReservaFormValues): void {
    if (souAdministrador && !predioIdAdmin) return;
    criarReservaMutation.mutate({
      area_comum_id: Number(values.area_comum_id),
      data: values.data,
      unidade_id: souGestao && values.unidade_id ? Number(values.unidade_id) : undefined,
      observacoes: values.observacoes || undefined,
      predio_id: souAdministrador ? predioIdAdmin : undefined,
    });
  }

  const areaSelecionadaId = reservaForm.watch("area_comum_id");
  const areaSelecionada = areas?.find((a) => a.id === Number(areaSelecionadaId));
  const areasReservaveis = areas?.filter((a) => a.ativo && a.agenda_liberada_ate) ?? [];

  return (
    <AppShell>
      <h1 className="mb-4 text-xl font-bold text-slate-800">Reserva de Espaços</h1>

      {souAdministrador && (
        <div className="mb-6 rounded-2xl bg-white p-4 shadow-sm">
          <label className="mb-1 block text-xs font-medium text-slate-600">ID do prédio</label>
          <input
            inputMode="numeric"
            value={predioIdAdminInput}
            onChange={(event) => setPredioIdAdminInput(event.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            placeholder="Ex.: 1"
          />
        </div>
      )}

      {souGestao && (
        <div className="mb-6 space-y-3 rounded-2xl bg-white p-4 shadow-sm">
          <h2 className="text-sm font-semibold text-slate-700">Cadastrar área comum</h2>
          <form onSubmit={areaForm.handleSubmit(onSubmitArea)} className="space-y-3" noValidate>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Nome</label>
              <input
                placeholder="Ex.: Salão de festas"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                {...areaForm.register("nome")}
              />
              {areaForm.formState.errors.nome && (
                <p className="mt-1 text-xs text-red-600">{areaForm.formState.errors.nome.message}</p>
              )}
            </div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600">
                  Descrição (opcional)
                </label>
                <input
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  {...areaForm.register("descricao")}
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600">
                  Capacidade (opcional)
                </label>
                <input
                  inputMode="numeric"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  {...areaForm.register("capacidade")}
                />
              </div>
            </div>
            {bloqueadoSemPredio && (
              <p className="text-sm text-amber-600">Informe o ID do prédio acima para continuar.</p>
            )}
            <button
              type="submit"
              disabled={areaForm.formState.isSubmitting || bloqueadoSemPredio}
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
            >
              Cadastrar área
            </button>
          </form>
        </div>
      )}

      {carregandoAreas && <p className="text-sm text-slate-500">Carregando áreas...</p>}

      {!bloqueadoSemPredio && (
        <div className="mb-6 space-y-2">
          <h2 className="text-sm font-semibold text-slate-700">Áreas do condomínio</h2>
          {areas?.map((area) => (
            <div key={area.id} className="rounded-xl bg-white p-3 shadow-sm">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="font-medium text-slate-800">{area.nome}</p>
                  {area.descricao && <p className="text-sm text-slate-600">{area.descricao}</p>}
                  {area.capacidade && (
                    <p className="text-xs text-slate-500">Capacidade: {area.capacidade} pessoas</p>
                  )}
                </div>
                <span
                  className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${
                    area.ativo ? "bg-emerald-100 text-emerald-700" : "bg-slate-200 text-slate-500"
                  }`}
                >
                  {area.ativo ? "Ativa" : "Inativa"}
                </span>
              </div>
              <p className="mt-2 text-xs text-slate-500">
                {area.agenda_liberada_ate
                  ? `Agenda liberada até ${formatarData(area.agenda_liberada_ate)}`
                  : "Agenda ainda não liberada para reservas"}
              </p>
              {souGestao && (
                <>
                  <LiberarAgendaForm area={area} />
                  <div className="mt-2 flex items-center justify-between border-t border-slate-100 pt-2">
                    <button
                      type="button"
                      onClick={() => toggleAtivoMutation.mutate({ id: area.id, ativo: !area.ativo })}
                      className="text-xs font-medium text-brand-600"
                    >
                      {area.ativo ? "Desativar" : "Reativar"}
                    </button>
                    <button
                      type="button"
                      onClick={() => removerAreaMutation.mutate(area.id)}
                      className="text-xs font-medium text-red-600"
                    >
                      Remover
                    </button>
                  </div>
                </>
              )}
            </div>
          ))}
          {areas?.length === 0 && (
            <p className="rounded-xl bg-white p-4 text-center text-sm text-slate-500 shadow-sm">
              Nenhuma área cadastrada ainda.
            </p>
          )}
        </div>
      )}

      {!bloqueadoSemPredio && areasReservaveis.length > 0 && (
        <div className="mb-6 space-y-3 rounded-2xl bg-white p-4 shadow-sm">
          <h2 className="text-sm font-semibold text-slate-700">Reservar um espaço</h2>
          <form onSubmit={reservaForm.handleSubmit(onSubmitReserva)} className="space-y-3" noValidate>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600">Área</label>
                <select
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  {...reservaForm.register("area_comum_id")}
                >
                  <option value="">Selecione...</option>
                  {areasReservaveis.map((area) => (
                    <option key={area.id} value={area.id}>
                      {area.nome}
                    </option>
                  ))}
                </select>
                {reservaForm.formState.errors.area_comum_id && (
                  <p className="mt-1 text-xs text-red-600">
                    {reservaForm.formState.errors.area_comum_id.message}
                  </p>
                )}
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600">Data</label>
                <input
                  type="date"
                  min={new Date().toISOString().slice(0, 10)}
                  max={areaSelecionada?.agenda_liberada_ate ?? undefined}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  {...reservaForm.register("data")}
                />
                {reservaForm.formState.errors.data && (
                  <p className="mt-1 text-xs text-red-600">{reservaForm.formState.errors.data.message}</p>
                )}
              </div>
            </div>

            {souGestao && (
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600">
                  Unidade (opcional - padrão: sua própria)
                </label>
                <select
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  {...reservaForm.register("unidade_id")}
                >
                  <option value="">Selecione...</option>
                  {unidades?.map((unidade) => (
                    <option key={unidade.id} value={unidade.id}>
                      Bloco {unidade.bloco} - {unidade.numero}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">
                Observações (opcional)
              </label>
              <textarea
                rows={2}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                {...reservaForm.register("observacoes")}
              />
            </div>

            {criarReservaMutation.isError && (
              <p className="text-sm text-red-600">
                Não foi possível reservar - a data pode já estar ocupada ou fora da agenda liberada.
              </p>
            )}

            <button
              type="submit"
              disabled={reservaForm.formState.isSubmitting}
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
            >
              Reservar
            </button>
          </form>
        </div>
      )}

      {carregandoReservas && <p className="text-sm text-slate-500">Carregando reservas...</p>}

      {!bloqueadoSemPredio && (
        <div className="space-y-2">
          <h2 className="text-sm font-semibold text-slate-700">
            {souGestao ? "Todas as reservas" : "Minhas reservas"}
          </h2>
          <ul className="space-y-2">
            {reservas?.map((reserva) => (
              <li key={reserva.id} className="rounded-xl bg-white p-3 shadow-sm">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-medium text-slate-800">{labelArea(reserva.area_comum_id)}</p>
                    <p className="text-sm text-slate-600">{formatarData(reserva.data)}</p>
                    {souGestao && (
                      <p className="text-xs text-slate-500">{labelUnidade(reserva.unidade_id)}</p>
                    )}
                    {reserva.observacoes && (
                      <p className="mt-1 text-xs text-slate-500">{reserva.observacoes}</p>
                    )}
                  </div>
                  <span
                    className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${
                      reserva.status === "confirmada"
                        ? "bg-emerald-100 text-emerald-700"
                        : "bg-slate-200 text-slate-500"
                    }`}
                  >
                    {reserva.status === "confirmada" ? "Confirmada" : "Cancelada"}
                  </span>
                </div>
                {reserva.status === "confirmada" && (
                  <div className="mt-2 flex justify-end border-t border-slate-100 pt-2">
                    <button
                      type="button"
                      onClick={() => cancelarReservaMutation.mutate(reserva.id)}
                      className="text-xs font-medium text-red-600"
                    >
                      Cancelar reserva
                    </button>
                  </div>
                )}
              </li>
            ))}
            {reservas?.length === 0 && (
              <li className="rounded-xl bg-white p-4 text-center text-sm text-slate-500 shadow-sm">
                Nenhuma reserva encontrada.
              </li>
            )}
          </ul>
        </div>
      )}
    </AppShell>
  );
}
