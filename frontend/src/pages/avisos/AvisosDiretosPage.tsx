import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { AppShell } from "../../components/layout/AppShell";
import { useAuth } from "../../auth/AuthContext";
import { temPapel } from "../../auth/roles";
import {
  createAvisoDireto,
  deleteAvisoDireto,
  listAvisosDiretos,
  marcarAvisoDiretoLido,
  responderAvisoDireto,
} from "../../api/avisosDiretos";
import { listUnidades } from "../../api/unidades";
import type { AvisoDireto, DestinatarioAvisoEnum, TipoAvisoDiretoEnum } from "../../api/types";

const DESTINATARIO_LABEL: Record<DestinatarioAvisoEnum, string> = {
  morador: "Morador",
  proprietario: "Proprietário",
  ambos: "Ambos",
};

const TIPO_LABEL: Record<TipoAvisoDiretoEnum, string> = {
  aviso: "Aviso",
  advertencia: "Advertência",
  multa: "Multa",
};

const TIPO_CLASSES: Record<TipoAvisoDiretoEnum, string> = {
  aviso: "bg-sky-100 text-sky-700",
  advertencia: "bg-amber-100 text-amber-700",
  multa: "bg-red-100 text-red-700",
};

const avisoDiretoSchema = z.object({
  unidade_id: z.string().min(1, "Selecione a unidade."),
  destinatario: z.enum(["morador", "proprietario", "ambos"]),
  tipo: z.enum(["aviso", "advertencia", "multa"]),
  titulo: z.string().min(2, "Informe um título."),
  mensagem: z.string().min(2, "Informe a mensagem."),
  valor: z.string().optional(),
  data_vencimento: z.string().optional(),
});

type AvisoDiretoFormValues = z.infer<typeof avisoDiretoSchema>;

function formatarValor(valor: string): string {
  const numero = Number(valor);
  return Number.isFinite(numero)
    ? numero.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
    : valor;
}

function ResponderForm({ avisoId }: { avisoId: number }) {
  const queryClient = useQueryClient();
  const [resposta, setResposta] = useState("");

  const mutation = useMutation({
    mutationFn: () => responderAvisoDireto(avisoId, resposta.trim()),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["avisos-diretos"] }),
  });

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        if (resposta.trim()) mutation.mutate();
      }}
      className="mt-2 flex gap-2"
    >
      <input
        value={resposta}
        onChange={(event) => setResposta(event.target.value)}
        placeholder="Responder (uma unica vez)..."
        className="w-full rounded-lg border border-slate-300 px-3 py-1.5 text-sm"
      />
      <button
        type="submit"
        disabled={mutation.isPending || !resposta.trim()}
        className="shrink-0 rounded-lg bg-brand-600 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-60"
      >
        Enviar
      </button>
    </form>
  );
}

export function AvisosDiretosPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const souGestao = temPapel(user, "administrador", "sindico");
  const souAdministrador = user?.role === "administrador";

  const [predioIdAdminInput, setPredioIdAdminInput] = useState("");
  const predioIdAdmin = predioIdAdminInput.trim() ? Number(predioIdAdminInput.trim()) : null;
  const bloqueadoSemPredio = souAdministrador && !predioIdAdmin;

  const { data: avisos, isLoading } = useQuery({
    queryKey: ["avisos-diretos", souAdministrador ? predioIdAdmin : "proprio"],
    queryFn: () => listAvisosDiretos({ predioId: souAdministrador ? predioIdAdmin : undefined }),
    enabled: !bloqueadoSemPredio,
  });

  const { data: unidades } = useQuery({
    queryKey: ["unidades", "combo", souAdministrador ? predioIdAdmin : "proprio"],
    queryFn: () => listUnidades(souAdministrador ? predioIdAdmin : undefined),
    enabled: souGestao && !bloqueadoSemPredio,
  });

  function labelUnidade(unidadeId: number): string {
    const unidade = unidades?.find((u) => u.id === unidadeId);
    return unidade ? `Bloco ${unidade.bloco} - ${unidade.numero}` : `Unidade #${unidadeId}`;
  }

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<AvisoDiretoFormValues>({
    resolver: zodResolver(avisoDiretoSchema),
    defaultValues: {
      unidade_id: "",
      destinatario: "ambos",
      tipo: "aviso",
      titulo: "",
      mensagem: "",
      valor: "",
      data_vencimento: "",
    },
  });

  const tipoSelecionado = watch("tipo");
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["avisos-diretos"] });

  const createMutation = useMutation({
    mutationFn: createAvisoDireto,
    onSuccess: () => {
      invalidate();
      reset({
        unidade_id: "",
        destinatario: "ambos",
        tipo: "aviso",
        titulo: "",
        mensagem: "",
        valor: "",
        data_vencimento: "",
      });
    },
  });

  const marcarLidoMutation = useMutation({ mutationFn: marcarAvisoDiretoLido, onSuccess: invalidate });
  const removerMutation = useMutation({ mutationFn: deleteAvisoDireto, onSuccess: invalidate });

  function onSubmit(values: AvisoDiretoFormValues): void {
    if (souAdministrador && !predioIdAdmin) return;
    createMutation.mutate({
      unidade_id: Number(values.unidade_id),
      destinatario: values.destinatario,
      tipo: values.tipo,
      titulo: values.titulo,
      mensagem: values.mensagem,
      valor: values.tipo === "multa" ? values.valor?.replace(",", ".") : undefined,
      data_vencimento: values.tipo === "multa" ? values.data_vencimento : undefined,
      predio_id: souAdministrador ? predioIdAdmin : undefined,
    });
  }

  function statusAviso(aviso: AvisoDireto): string {
    if (aviso.resposta) return "Respondido";
    if (aviso.lida_em) return "Lido";
    return "Não lido";
  }

  return (
    <AppShell>
      <h1 className="mb-4 text-xl font-bold text-slate-800">Avisos Diretos</h1>

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
          <h2 className="text-sm font-semibold text-slate-700">Enviar aviso direto</h2>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-3" noValidate>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600">Unidade</label>
                <select
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  {...register("unidade_id")}
                >
                  <option value="">Selecione...</option>
                  {unidades?.map((unidade) => (
                    <option key={unidade.id} value={unidade.id}>
                      Bloco {unidade.bloco} - {unidade.numero}
                    </option>
                  ))}
                </select>
                {errors.unidade_id && (
                  <p className="mt-1 text-xs text-red-600">{errors.unidade_id.message}</p>
                )}
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600">Para</label>
                <select
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  {...register("destinatario")}
                >
                  {Object.entries(DESTINATARIO_LABEL).map(([valor, label]) => (
                    <option key={valor} value={valor}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Tipo</label>
              <select
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                {...register("tipo")}
              >
                {Object.entries(TIPO_LABEL).map(([valor, label]) => (
                  <option key={valor} value={valor}>
                    {label}
                  </option>
                ))}
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

            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Mensagem</label>
              <textarea
                rows={3}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                {...register("mensagem")}
              />
              {errors.mensagem && (
                <p className="mt-1 text-xs text-red-600">{errors.mensagem.message}</p>
              )}
            </div>

            {tipoSelecionado === "multa" && (
              <div className="grid grid-cols-2 gap-3 rounded-lg bg-red-50 p-3">
                <div>
                  <label className="mb-1 block text-xs font-medium text-slate-600">Valor (R$)</label>
                  <input
                    inputMode="decimal"
                    placeholder="0,00"
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    {...register("valor")}
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-slate-600">Vencimento</label>
                  <input
                    type="date"
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    {...register("data_vencimento")}
                  />
                </div>
                <p className="col-span-2 text-xs text-red-700">
                  Gera uma despesa exclusiva desta unidade, além das contas gerais do condomínio.
                </p>
              </div>
            )}

            {createMutation.isError && (
              <p className="text-sm text-red-600">Não foi possível enviar. Verifique os dados.</p>
            )}
            {bloqueadoSemPredio && (
              <p className="text-sm text-amber-600">Informe o ID do prédio acima para continuar.</p>
            )}

            <button
              type="submit"
              disabled={isSubmitting || bloqueadoSemPredio}
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
            >
              Enviar
            </button>
          </form>
        </div>
      )}

      {isLoading && <p className="text-sm text-slate-500">Carregando...</p>}

      {!bloqueadoSemPredio && (
        <ul className="space-y-2">
          {avisos?.map((aviso) => (
            <li key={aviso.id} className="rounded-xl bg-white p-3 shadow-sm">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="font-medium text-slate-800">{aviso.titulo}</p>
                  {souGestao && (
                    <p className="text-xs text-slate-500">{labelUnidade(aviso.unidade_id)}</p>
                  )}
                </div>
                <span
                  className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${TIPO_CLASSES[aviso.tipo]}`}
                >
                  {TIPO_LABEL[aviso.tipo]}
                </span>
              </div>
              <p className="mt-1 whitespace-pre-wrap text-sm text-slate-600">{aviso.mensagem}</p>
              {aviso.valor && (
                <p className="mt-1 text-sm font-semibold text-red-700">{formatarValor(aviso.valor)}</p>
              )}

              {aviso.resposta ? (
                <div className="mt-2 rounded-lg bg-slate-50 p-2 text-sm text-slate-600">
                  <span className="font-medium">Resposta:</span> {aviso.resposta}
                </div>
              ) : (
                !souGestao && (
                  <div className="mt-2 flex flex-col gap-2">
                    {!aviso.lida_em && (
                      <button
                        type="button"
                        onClick={() => marcarLidoMutation.mutate(aviso.id)}
                        className="self-start text-xs font-medium text-brand-600"
                      >
                        Marcar como lido
                      </button>
                    )}
                    <ResponderForm avisoId={aviso.id} />
                  </div>
                )
              )}

              <div className="mt-2 flex items-center justify-between border-t border-slate-100 pt-2">
                <span className="text-xs text-slate-400">{statusAviso(aviso)}</span>
                {souGestao && (
                  <button
                    type="button"
                    onClick={() => removerMutation.mutate(aviso.id)}
                    className="text-xs font-medium text-red-600"
                  >
                    Remover
                  </button>
                )}
              </div>
            </li>
          ))}
          {avisos?.length === 0 && (
            <li className="rounded-xl bg-white p-4 text-center text-sm text-slate-500 shadow-sm">
              Nenhum aviso direto.
            </li>
          )}
        </ul>
      )}
    </AppShell>
  );
}
