import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { AppShell } from "../../components/layout/AppShell";
import { useAuth } from "../../auth/AuthContext";
import { temPapel } from "../../auth/roles";
import { createEntrega, listEntregas, marcarEntregaRetirada } from "../../api/entregas";
import { listUnidades } from "../../api/unidades";

const entregaSchema = z.object({
  unidade_id: z.string().min(1, "Selecione a unidade."),
  descricao: z.string().min(2, "Descreva o que chegou."),
  localizacao: z.string().min(2, "Informe onde está guardada."),
});

type EntregaFormValues = z.infer<typeof entregaSchema>;

function formatarData(data: string): string {
  return new Date(data).toLocaleString("pt-BR");
}

export function EntregasPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const souRegistrador = temPapel(user, "administrador", "sindico", "zelador");
  const souAdministrador = user?.role === "administrador";

  const [predioIdAdminInput, setPredioIdAdminInput] = useState("");
  const predioIdAdmin = predioIdAdminInput.trim() ? Number(predioIdAdminInput.trim()) : null;
  const bloqueadoSemPredio = souAdministrador && !predioIdAdmin;

  const { data: entregas, isLoading } = useQuery({
    queryKey: ["entregas", souAdministrador ? predioIdAdmin : "proprio"],
    queryFn: () => listEntregas({ predioId: souAdministrador ? predioIdAdmin : undefined }),
    enabled: !bloqueadoSemPredio,
  });

  const { data: unidades } = useQuery({
    queryKey: ["unidades", "combo", souAdministrador ? predioIdAdmin : "proprio"],
    queryFn: () => listUnidades(souAdministrador ? predioIdAdmin : undefined),
    enabled: souRegistrador && !bloqueadoSemPredio,
  });

  function labelUnidade(unidadeId: number): string {
    const unidade = unidades?.find((u) => u.id === unidadeId);
    return unidade ? `Bloco ${unidade.bloco} - ${unidade.numero}` : `Unidade #${unidadeId}`;
  }

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<EntregaFormValues>({
    resolver: zodResolver(entregaSchema),
    defaultValues: { unidade_id: "", descricao: "", localizacao: "" },
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["entregas"] });

  const createMutation = useMutation({
    mutationFn: createEntrega,
    onSuccess: () => {
      invalidate();
      reset({ unidade_id: "", descricao: "", localizacao: "" });
    },
  });

  const retirarMutation = useMutation({ mutationFn: marcarEntregaRetirada, onSuccess: invalidate });

  function onSubmit(values: EntregaFormValues): void {
    if (souAdministrador && !predioIdAdmin) return;
    createMutation.mutate({
      unidade_id: Number(values.unidade_id),
      descricao: values.descricao,
      localizacao: values.localizacao,
      predio_id: souAdministrador ? predioIdAdmin : undefined,
    });
  }

  return (
    <AppShell>
      <h1 className="mb-4 text-xl font-bold text-slate-800">Entregas</h1>

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

      {souRegistrador && (
        <div className="mb-6 space-y-3 rounded-2xl bg-white p-4 shadow-sm">
          <h2 className="text-sm font-semibold text-slate-700">Registrar entrega recebida</h2>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-3" noValidate>
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
              <label className="mb-1 block text-xs font-medium text-slate-600">O que chegou</label>
              <input
                placeholder="Ex.: Pacote Amazon, caixa dos Correios..."
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                {...register("descricao")}
              />
              {errors.descricao && (
                <p className="mt-1 text-xs text-red-600">{errors.descricao.message}</p>
              )}
            </div>

            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Onde está guardada</label>
              <input
                placeholder="Ex.: Portaria, prateleira 3"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                {...register("localizacao")}
              />
              {errors.localizacao && (
                <p className="mt-1 text-xs text-red-600">{errors.localizacao.message}</p>
              )}
            </div>

            {createMutation.isError && (
              <p className="text-sm text-red-600">Não foi possível registrar. Verifique os dados.</p>
            )}
            {bloqueadoSemPredio && (
              <p className="text-sm text-amber-600">Informe o ID do prédio acima para continuar.</p>
            )}

            <button
              type="submit"
              disabled={isSubmitting || bloqueadoSemPredio}
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
            >
              Registrar e avisar a unidade
            </button>
          </form>
        </div>
      )}

      {isLoading && <p className="text-sm text-slate-500">Carregando...</p>}

      {!bloqueadoSemPredio && (
        <ul className="space-y-2">
          {entregas?.map((entrega) => (
            <li key={entrega.id} className="rounded-xl bg-white p-3 shadow-sm">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="font-medium text-slate-800">{entrega.descricao}</p>
                  {souRegistrador && (
                    <p className="text-xs text-slate-500">{labelUnidade(entrega.unidade_id)}</p>
                  )}
                  <p className="text-sm text-slate-600">📍 {entrega.localizacao}</p>
                </div>
                <span
                  className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${
                    entrega.retirada_em
                      ? "bg-emerald-100 text-emerald-700"
                      : "bg-amber-100 text-amber-700"
                  }`}
                >
                  {entrega.retirada_em ? "Retirada" : "Aguardando retirada"}
                </span>
              </div>

              <div className="mt-2 flex items-center justify-between border-t border-slate-100 pt-2">
                <span className="text-xs text-slate-400">
                  {entrega.retirada_em
                    ? `Retirada em ${formatarData(entrega.retirada_em)}`
                    : `Recebida em ${formatarData(entrega.created_at)}`}
                </span>
                {!entrega.retirada_em && (
                  <button
                    type="button"
                    onClick={() => retirarMutation.mutate(entrega.id)}
                    className="text-xs font-medium text-brand-600"
                  >
                    Marcar como retirada
                  </button>
                )}
              </div>
            </li>
          ))}
          {entregas?.length === 0 && (
            <li className="rounded-xl bg-white p-4 text-center text-sm text-slate-500 shadow-sm">
              Nenhuma entrega registrada.
            </li>
          )}
        </ul>
      )}
    </AppShell>
  );
}
