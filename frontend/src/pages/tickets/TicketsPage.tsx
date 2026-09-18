import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { AppShell } from "../../components/layout/AppShell";
import { useAuth } from "../../auth/AuthContext";
import {
  assumirTicket,
  cancelarTicket,
  comentarTicket,
  createTicket,
  listTickets,
  resolverTicket,
  updateTicket,
} from "../../api/tickets";
import type {
  CategoriaTicketEnum,
  PrioridadeTicketEnum,
  StatusTicketEnum,
  TicketAtendimento,
} from "../../api/types";

const ticketSchema = z.object({
  titulo: z.string().min(2, "Informe um titulo."),
  descricao: z.string().min(2, "Descreva o chamado."),
  categoria: z.enum(["manutencao", "duvida", "solicitacao", "outro"]),
  prioridade: z.enum(["baixa", "media", "alta"]),
});

type TicketFormValues = z.infer<typeof ticketSchema>;

const FORM_VAZIO: TicketFormValues = {
  titulo: "",
  descricao: "",
  categoria: "manutencao",
  prioridade: "media",
};

const CATEGORIA_LABEL: Record<CategoriaTicketEnum, string> = {
  manutencao: "Manutencao",
  duvida: "Duvida",
  solicitacao: "Solicitacao",
  outro: "Outro",
};

const PRIORIDADE_LABEL: Record<PrioridadeTicketEnum, string> = {
  baixa: "Baixa",
  media: "Media",
  alta: "Alta",
};

const STATUS_LABEL: Record<StatusTicketEnum, string> = {
  aberto: "Aberto",
  em_andamento: "Em andamento",
  resolvido: "Resolvido",
  cancelado: "Cancelado",
};

const STATUS_CLASSES: Record<StatusTicketEnum, string> = {
  aberto: "bg-amber-100 text-amber-700",
  em_andamento: "bg-sky-100 text-sky-700",
  resolvido: "bg-emerald-100 text-emerald-700",
  cancelado: "bg-slate-200 text-slate-500",
};

function ComentarioForm({ ticketId }: { ticketId: number }) {
  const queryClient = useQueryClient();
  const [mensagem, setMensagem] = useState("");

  const mutation = useMutation({
    mutationFn: () => comentarTicket(ticketId, mensagem.trim()),
    onSuccess: () => {
      setMensagem("");
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
    },
  });

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        if (mensagem.trim()) mutation.mutate();
      }}
      className="mt-2 flex gap-2"
    >
      <input
        value={mensagem}
        onChange={(event) => setMensagem(event.target.value)}
        placeholder="Escrever um comentario..."
        className="w-full rounded-lg border border-slate-300 px-3 py-1.5 text-sm"
      />
      <button
        type="submit"
        disabled={mutation.isPending || !mensagem.trim()}
        className="shrink-0 rounded-lg bg-brand-600 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-60"
      >
        Enviar
      </button>
    </form>
  );
}

export function TicketsPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const souGestao = user?.role === "administrador" || user?.role === "sindico" || user?.role === "zelador";
  const souAdministrador = user?.role === "administrador";

  const [predioIdAdminInput, setPredioIdAdminInput] = useState("");
  const predioIdAdmin = predioIdAdminInput.trim() ? Number(predioIdAdminInput.trim()) : null;
  const bloqueadoSemPredio = souAdministrador && !predioIdAdmin;

  const [filtroStatus, setFiltroStatus] = useState<StatusTicketEnum | "">("");
  const [editing, setEditing] = useState<TicketAtendimento | null>(null);
  const [expandido, setExpandido] = useState<number | null>(null);

  const { data: tickets, isLoading } = useQuery({
    queryKey: ["tickets", souAdministrador ? predioIdAdmin : "proprio", filtroStatus],
    queryFn: () =>
      listTickets({
        predioId: souAdministrador ? predioIdAdmin : undefined,
        status: filtroStatus || undefined,
      }),
    enabled: !bloqueadoSemPredio,
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<TicketFormValues>({
    resolver: zodResolver(ticketSchema),
    defaultValues: FORM_VAZIO,
  });

  function limparFormulario(): void {
    reset(FORM_VAZIO);
    setEditing(null);
  }

  function iniciarEdicao(ticket: TicketAtendimento): void {
    setEditing(ticket);
    reset({
      titulo: ticket.titulo,
      descricao: ticket.descricao,
      categoria: ticket.categoria,
      prioridade: ticket.prioridade,
    });
  }

  const invalidateTickets = () => queryClient.invalidateQueries({ queryKey: ["tickets"] });

  const createMutation = useMutation({
    mutationFn: createTicket,
    onSuccess: () => {
      invalidateTickets();
      limparFormulario();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, input }: { id: number; input: TicketFormValues }) => updateTicket(id, input),
    onSuccess: () => {
      invalidateTickets();
      limparFormulario();
    },
  });

  const assumirMutation = useMutation({ mutationFn: (id: number) => assumirTicket(id), onSuccess: invalidateTickets });
  const resolverMutation = useMutation({ mutationFn: resolverTicket, onSuccess: invalidateTickets });
  const cancelarMutation = useMutation({ mutationFn: cancelarTicket, onSuccess: invalidateTickets });

  function onSubmit(values: TicketFormValues): void {
    if (souAdministrador && !predioIdAdmin) return;
    if (editing) {
      updateMutation.mutate({ id: editing.id, input: values });
      return;
    }
    createMutation.mutate({ ...values, predio_id: souAdministrador ? predioIdAdmin : undefined });
  }

  const souAutor = (ticket: TicketAtendimento) => ticket.created_by === user?.id;

  return (
    <AppShell>
      <h1 className="mb-4 text-xl font-bold text-slate-800">Tickets de Atendimento</h1>

      {souAdministrador && (
        <div className="mb-6 rounded-2xl bg-white p-4 shadow-sm">
          <label className="mb-1 block text-xs font-medium text-slate-600">ID do predio</label>
          <input
            inputMode="numeric"
            value={predioIdAdminInput}
            onChange={(event) => setPredioIdAdminInput(event.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            placeholder="Ex.: 1"
          />
        </div>
      )}

      <div className="mb-6 space-y-3 rounded-2xl bg-white p-4 shadow-sm">
        <h2 className="text-sm font-semibold text-slate-700">
          {editing ? `Editar chamado #${editing.id}` : "Abrir um chamado"}
        </h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-3" noValidate>
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">Titulo</label>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              {...register("titulo")}
            />
            {errors.titulo && <p className="mt-1 text-xs text-red-600">{errors.titulo.message}</p>}
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">Descricao</label>
            <textarea
              rows={3}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              {...register("descricao")}
            />
            {errors.descricao && (
              <p className="mt-1 text-xs text-red-600">{errors.descricao.message}</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Categoria</label>
              <select
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                {...register("categoria")}
              >
                {Object.entries(CATEGORIA_LABEL).map(([valor, label]) => (
                  <option key={valor} value={valor}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Prioridade</label>
              <select
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                {...register("prioridade")}
              >
                {Object.entries(PRIORIDADE_LABEL).map(([valor, label]) => (
                  <option key={valor} value={valor}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {(createMutation.isError || updateMutation.isError) && (
            <p className="text-sm text-red-600">Nao foi possivel salvar o chamado. Tente novamente.</p>
          )}
          {bloqueadoSemPredio && (
            <p className="text-sm text-amber-600">Informe o ID do predio acima para continuar.</p>
          )}

          <div className="flex gap-2">
            <button
              type="submit"
              disabled={isSubmitting || bloqueadoSemPredio}
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
            >
              {editing ? "Salvar alteracoes" : "Abrir chamado"}
            </button>
            {editing && (
              <button
                type="button"
                onClick={limparFormulario}
                className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600"
              >
                Cancelar edicao
              </button>
            )}
          </div>
        </form>
      </div>

      <div className="mb-3 flex items-center gap-2">
        <label className="text-xs font-medium text-slate-600">Status</label>
        <select
          value={filtroStatus}
          onChange={(event) => setFiltroStatus(event.target.value as StatusTicketEnum | "")}
          className="rounded-lg border border-slate-300 px-2 py-1 text-xs"
        >
          <option value="">Todos</option>
          {Object.entries(STATUS_LABEL).map(([valor, label]) => (
            <option key={valor} value={valor}>
              {label}
            </option>
          ))}
        </select>
      </div>

      {isLoading && <p className="text-sm text-slate-500">Carregando...</p>}

      <ul className="space-y-2">
        {tickets?.map((ticket) => (
          <li key={ticket.id} className="rounded-xl bg-white p-3 shadow-sm">
            <button
              type="button"
              onClick={() => setExpandido(expandido === ticket.id ? null : ticket.id)}
              className="flex w-full items-start justify-between gap-2 text-left"
            >
              <div>
                <p className="font-medium text-slate-800">{ticket.titulo}</p>
                <p className="text-xs text-slate-500">
                  {CATEGORIA_LABEL[ticket.categoria]} - {PRIORIDADE_LABEL[ticket.prioridade]}
                </p>
              </div>
              <span
                className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_CLASSES[ticket.status]}`}
              >
                {STATUS_LABEL[ticket.status]}
                {ticket.esta_atrasado ? " - atrasado" : ""}
              </span>
            </button>

            {expandido === ticket.id && (
              <div className="mt-3 border-t border-slate-100 pt-3">
                <p className="whitespace-pre-wrap text-sm text-slate-600">{ticket.descricao}</p>

                <div className="mt-3 flex flex-wrap gap-3">
                  {souAutor(ticket) && ticket.status === "aberto" && (
                    <button
                      type="button"
                      onClick={() => iniciarEdicao(ticket)}
                      className="text-xs font-medium text-brand-600"
                    >
                      Editar
                    </button>
                  )}
                  {souGestao && ticket.status === "aberto" && (
                    <button
                      type="button"
                      onClick={() => assumirMutation.mutate(ticket.id)}
                      className="text-xs font-medium text-sky-600"
                    >
                      Assumir
                    </button>
                  )}
                  {souGestao && (ticket.status === "aberto" || ticket.status === "em_andamento") && (
                    <button
                      type="button"
                      onClick={() => resolverMutation.mutate(ticket.id)}
                      className="text-xs font-medium text-emerald-600"
                    >
                      Marcar como resolvido
                    </button>
                  )}
                  {(souGestao || souAutor(ticket)) &&
                    (ticket.status === "aberto" || ticket.status === "em_andamento") && (
                      <button
                        type="button"
                        onClick={() => cancelarMutation.mutate(ticket.id)}
                        className="text-xs font-medium text-red-600"
                      >
                        Cancelar
                      </button>
                    )}
                </div>

                <div className="mt-3 space-y-2">
                  {ticket.comentarios.map((comentario) => (
                    <div key={comentario.id} className="rounded-lg bg-slate-50 p-2 text-sm text-slate-600">
                      {comentario.mensagem}
                    </div>
                  ))}
                  {ticket.comentarios.length === 0 && (
                    <p className="text-xs text-slate-400">Sem comentarios ainda.</p>
                  )}
                  <ComentarioForm ticketId={ticket.id} />
                </div>
              </div>
            )}
          </li>
        ))}
        {tickets?.length === 0 && (
          <li className="rounded-xl bg-white p-4 text-center text-sm text-slate-500 shadow-sm">
            Nenhum chamado encontrado.
          </li>
        )}
      </ul>
    </AppShell>
  );
}
