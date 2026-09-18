import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { AppShell } from "../../components/layout/AppShell";
import { useAuth } from "../../auth/AuthContext";
import { temPapel } from "../../auth/roles";
import {
  cancelarReuniao,
  confirmarPresenca,
  createReuniao,
  listReunioes,
  registrarAta,
  removerPresenca,
  updateReuniao,
} from "../../api/reunioes";
import { listUnidades } from "../../api/unidades";
import type { Reuniao, TipoReuniaoEnum } from "../../api/types";

const TIPO_LABEL: Record<TipoReuniaoEnum, string> = {
  ordinaria: "Ordinária",
  extraordinaria: "Extraordinária",
};

const STATUS_LABEL = {
  convocada: "Convocada",
  realizada: "Realizada",
  cancelada: "Cancelada",
} as const;

const STATUS_CLASSES = {
  convocada: "bg-amber-100 text-amber-700",
  realizada: "bg-emerald-100 text-emerald-700",
  cancelada: "bg-slate-200 text-slate-500",
} as const;

const reuniaoSchema = z.object({
  tipo: z.enum(["ordinaria", "extraordinaria"]),
  titulo: z.string().min(2, "Informe um título."),
  data: z.string().min(1, "Informe a data."),
  hora: z.string().min(1, "Informe o horário."),
  local: z.string().min(2, "Informe o local."),
  pauta: z.string().min(2, "Informe a pauta."),
});

type ReuniaoFormValues = z.infer<typeof reuniaoSchema>;

function formatarDataHora(dataHora: string): { data: string; diaSemana: string; hora: string } {
  const d = new Date(dataHora);
  return {
    data: d.toLocaleDateString("pt-BR"),
    diaSemana: d.toLocaleDateString("pt-BR", { weekday: "long" }),
    hora: d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
  };
}

function AtaForm({ reuniaoId }: { reuniaoId: number }) {
  const queryClient = useQueryClient();
  const [texto, setTexto] = useState("");

  const mutation = useMutation({
    mutationFn: () => registrarAta(reuniaoId, texto.trim()),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["reunioes"] }),
  });

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        if (texto.trim()) mutation.mutate();
      }}
      className="mt-2 space-y-2"
    >
      <textarea
        rows={3}
        value={texto}
        onChange={(event) => setTexto(event.target.value)}
        placeholder="Registrar a ata da reunião..."
        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
      />
      <button
        type="submit"
        disabled={mutation.isPending || !texto.trim()}
        className="rounded-lg bg-brand-600 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-60"
      >
        Registrar ata e encerrar reunião
      </button>
    </form>
  );
}

export function ReunioesPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const souGestao = temPapel(user, "administrador", "sindico");
  const souAdministrador = user?.role === "administrador";

  const [predioIdAdminInput, setPredioIdAdminInput] = useState("");
  const predioIdAdmin = predioIdAdminInput.trim() ? Number(predioIdAdminInput.trim()) : null;
  const bloqueadoSemPredio = souAdministrador && !predioIdAdmin;

  const [editing, setEditing] = useState<Reuniao | null>(null);
  const [expandida, setExpandida] = useState<number | null>(null);

  const { data: reunioes, isLoading } = useQuery({
    queryKey: ["reunioes", souAdministrador ? predioIdAdmin : "proprio"],
    queryFn: () => listReunioes({ predioId: souAdministrador ? predioIdAdmin : undefined }),
    enabled: !bloqueadoSemPredio,
  });

  const { data: minhasUnidades } = useQuery({
    queryKey: ["unidades", "minhas"],
    queryFn: () => listUnidades(souAdministrador ? predioIdAdmin : undefined),
    enabled: !bloqueadoSemPredio,
    select: (todas) =>
      souGestao ? todas : todas.filter((u) => user?.unidade_ids.includes(u.id)),
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ReuniaoFormValues>({
    resolver: zodResolver(reuniaoSchema),
    defaultValues: { tipo: "ordinaria", titulo: "", data: "", hora: "19:00", local: "", pauta: "" },
  });

  function limparFormulario(): void {
    reset({ tipo: "ordinaria", titulo: "", data: "", hora: "19:00", local: "", pauta: "" });
    setEditing(null);
  }

  function iniciarEdicao(reuniao: Reuniao): void {
    const d = new Date(reuniao.data_hora);
    setEditing(reuniao);
    reset({
      tipo: reuniao.tipo,
      titulo: reuniao.titulo,
      data: d.toISOString().slice(0, 10),
      hora: d.toTimeString().slice(0, 5),
      local: reuniao.local,
      pauta: reuniao.pauta,
    });
  }

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["reunioes"] });

  const createMutation = useMutation({
    mutationFn: createReuniao,
    onSuccess: () => {
      invalidate();
      limparFormulario();
    },
  });
  const updateMutation = useMutation({
    mutationFn: ({ id, input }: { id: number; input: Partial<ReuniaoFormValues> & { data_hora?: string } }) =>
      updateReuniao(id, input),
    onSuccess: () => {
      invalidate();
      limparFormulario();
    },
  });
  const cancelarMutation = useMutation({ mutationFn: cancelarReuniao, onSuccess: invalidate });
  const confirmarPresencaMutation = useMutation({
    mutationFn: ({ id, unidadeId }: { id: number; unidadeId: number }) =>
      confirmarPresenca(id, unidadeId),
    onSuccess: invalidate,
  });
  const removerPresencaMutation = useMutation({
    mutationFn: ({ id, unidadeId }: { id: number; unidadeId: number }) =>
      removerPresenca(id, unidadeId),
    onSuccess: invalidate,
  });

  function onSubmit(values: ReuniaoFormValues): void {
    if (souAdministrador && !predioIdAdmin) return;
    const data_hora = new Date(`${values.data}T${values.hora}:00`).toISOString();

    if (editing) {
      updateMutation.mutate({
        id: editing.id,
        input: { tipo: values.tipo, titulo: values.titulo, local: values.local, pauta: values.pauta, data_hora },
      });
      return;
    }
    createMutation.mutate({
      tipo: values.tipo,
      titulo: values.titulo,
      local: values.local,
      pauta: values.pauta,
      data_hora,
      predio_id: souAdministrador ? predioIdAdmin : undefined,
    });
  }

  function unidadeIdDoUsuario(): number | null {
    if (!minhasUnidades || minhasUnidades.length === 0) return null;
    return minhasUnidades[0].id;
  }

  return (
    <AppShell>
      <h1 className="mb-4 text-xl font-bold text-slate-800">Reuniões</h1>

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
          <h2 className="text-sm font-semibold text-slate-700">
            {editing ? `Editar reunião #${editing.id}` : "Convocar reunião"}
          </h2>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-3" noValidate>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Tipo</label>
              <select
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                {...register("tipo")}
              >
                <option value="ordinaria">Ordinária</option>
                <option value="extraordinaria">Extraordinária</option>
              </select>
            </div>

            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Título</label>
              <input
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                {...register("titulo")}
              />
              {errors.titulo && <p className="mt-1 text-xs text-red-600">{errors.titulo.message}</p>}
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600">Data</label>
                <input
                  type="date"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  {...register("data")}
                />
                {errors.data && <p className="mt-1 text-xs text-red-600">{errors.data.message}</p>}
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600">Horário</label>
                <input
                  type="time"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  {...register("hora")}
                />
                {errors.hora && <p className="mt-1 text-xs text-red-600">{errors.hora.message}</p>}
              </div>
            </div>

            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Local</label>
              <input
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                placeholder="Ex.: Salão de festas"
                {...register("local")}
              />
              {errors.local && <p className="mt-1 text-xs text-red-600">{errors.local.message}</p>}
            </div>

            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">
                Pauta (um item por linha)
              </label>
              <textarea
                rows={4}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                {...register("pauta")}
              />
              {errors.pauta && <p className="mt-1 text-xs text-red-600">{errors.pauta.message}</p>}
            </div>

            {(createMutation.isError || updateMutation.isError) && (
              <p className="text-sm text-red-600">Não foi possível salvar. Verifique os dados.</p>
            )}
            {bloqueadoSemPredio && (
              <p className="text-sm text-amber-600">Informe o ID do prédio acima para continuar.</p>
            )}

            <div className="flex gap-2">
              <button
                type="submit"
                disabled={isSubmitting || bloqueadoSemPredio}
                className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
              >
                {editing ? "Salvar alterações" : "Convocar"}
              </button>
              {editing && (
                <button
                  type="button"
                  onClick={limparFormulario}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600"
                >
                  Cancelar edição
                </button>
              )}
            </div>
          </form>
        </div>
      )}

      {isLoading && <p className="text-sm text-slate-500">Carregando...</p>}

      {!bloqueadoSemPredio && (
        <ul className="space-y-2">
          {reunioes?.map((reuniao) => {
            const { data, diaSemana, hora } = formatarDataHora(reuniao.data_hora);
            const minhaUnidadeId = unidadeIdDoUsuario();
            const jaConfirmou =
              minhaUnidadeId != null &&
              reuniao.presencas.some((p) => p.unidade_id === minhaUnidadeId);
            return (
              <li key={reuniao.id} className="rounded-xl bg-white p-3 shadow-sm">
                <button
                  type="button"
                  onClick={() => setExpandida(expandida === reuniao.id ? null : reuniao.id)}
                  className="flex w-full items-start justify-between gap-2 text-left"
                >
                  <div>
                    <p className="font-medium text-slate-800">{reuniao.titulo}</p>
                    <p className="text-xs capitalize text-slate-500">
                      {TIPO_LABEL[reuniao.tipo]} · {diaSemana}, {data} às {hora} · {reuniao.local}
                    </p>
                  </div>
                  <span
                    className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_CLASSES[reuniao.status]}`}
                  >
                    {STATUS_LABEL[reuniao.status]}
                  </span>
                </button>

                {expandida === reuniao.id && (
                  <div className="mt-3 space-y-3 border-t border-slate-100 pt-3">
                    <div>
                      <p className="text-xs font-medium text-slate-600">Pauta</p>
                      <p className="whitespace-pre-wrap text-sm text-slate-600">{reuniao.pauta}</p>
                    </div>

                    <div className="flex flex-wrap items-center gap-3">
                      {souGestao && reuniao.status === "convocada" && (
                        <>
                          <button
                            type="button"
                            onClick={() => iniciarEdicao(reuniao)}
                            className="text-xs font-medium text-brand-600"
                          >
                            Editar
                          </button>
                          <button
                            type="button"
                            onClick={() => cancelarMutation.mutate(reuniao.id)}
                            className="text-xs font-medium text-red-600"
                          >
                            Cancelar reunião
                          </button>
                        </>
                      )}
                      {!souGestao && reuniao.status === "convocada" && minhaUnidadeId != null && (
                        <button
                          type="button"
                          onClick={() =>
                            jaConfirmou
                              ? removerPresencaMutation.mutate({ id: reuniao.id, unidadeId: minhaUnidadeId })
                              : confirmarPresencaMutation.mutate({ id: reuniao.id, unidadeId: minhaUnidadeId })
                          }
                          className={`text-xs font-medium ${jaConfirmou ? "text-slate-500" : "text-emerald-600"}`}
                        >
                          {jaConfirmou ? "Desmarcar presença" : "Confirmar presença"}
                        </button>
                      )}
                    </div>

                    <div>
                      <p className="text-xs font-medium text-slate-600">
                        Presença confirmada ({reuniao.presencas.length} unidade
                        {reuniao.presencas.length === 1 ? "" : "s"})
                      </p>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {reuniao.presencas.map((p) => {
                          const unidade = minhasUnidades?.find((u) => u.id === p.unidade_id);
                          return (
                            <span
                              key={p.id}
                              className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600"
                            >
                              {unidade ? `Bloco ${unidade.bloco} - ${unidade.numero}` : `Unidade #${p.unidade_id}`}
                            </span>
                          );
                        })}
                        {reuniao.presencas.length === 0 && (
                          <span className="text-xs text-slate-400">Ninguém confirmou ainda.</span>
                        )}
                      </div>
                    </div>

                    {reuniao.ata ? (
                      <div>
                        <p className="text-xs font-medium text-slate-600">Ata</p>
                        <p className="whitespace-pre-wrap text-sm text-slate-600">{reuniao.ata}</p>
                      </div>
                    ) : (
                      souGestao && reuniao.status === "convocada" && <AtaForm reuniaoId={reuniao.id} />
                    )}
                  </div>
                )}
              </li>
            );
          })}
          {reunioes?.length === 0 && (
            <li className="rounded-xl bg-white p-4 text-center text-sm text-slate-500 shadow-sm">
              Nenhuma reunião registrada.
            </li>
          )}
        </ul>
      )}
    </AppShell>
  );
}
