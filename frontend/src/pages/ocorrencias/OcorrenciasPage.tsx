import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { AppShell } from "../../components/layout/AppShell";
import { useAuth } from "../../auth/AuthContext";
import { createOcorrencia, listOcorrencias, updateOcorrencia } from "../../api/ocorrencias";
import type { Ocorrencia } from "../../api/types";

const ocorrenciaSchema = z.object({
  titulo: z.string().min(2, "Informe um título."),
  descricao: z.string().min(2, "Descreva a ocorrência."),
});

type OcorrenciaFormValues = z.infer<typeof ocorrenciaSchema>;

function formatarData(data: string): string {
  return new Date(data).toLocaleString("pt-BR");
}

export function OcorrenciasPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const podeEditar = user?.role === "administrador" || user?.role === "sindico";
  const souAdministrador = user?.role === "administrador";

  const [predioIdAdminInput, setPredioIdAdminInput] = useState("");
  const predioIdAdmin = predioIdAdminInput.trim() ? Number(predioIdAdminInput.trim()) : null;
  const bloqueadoSemPredio = souAdministrador && !predioIdAdmin;

  const [editing, setEditing] = useState<Ocorrencia | null>(null);

  const { data: ocorrencias, isLoading } = useQuery({
    queryKey: ["ocorrencias", souAdministrador ? predioIdAdmin : "proprio"],
    queryFn: () => listOcorrencias(souAdministrador ? predioIdAdmin : undefined),
    enabled: !bloqueadoSemPredio,
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<OcorrenciaFormValues>({
    resolver: zodResolver(ocorrenciaSchema),
    defaultValues: { titulo: "", descricao: "" },
  });

  function limparFormulario(): void {
    reset({ titulo: "", descricao: "" });
    setEditing(null);
  }

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["ocorrencias"] });

  const createMutation = useMutation({
    mutationFn: createOcorrencia,
    onSuccess: () => {
      invalidate();
      limparFormulario();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, input }: { id: number; input: OcorrenciaFormValues }) => updateOcorrencia(id, input),
    onSuccess: () => {
      invalidate();
      limparFormulario();
    },
  });

  function onSubmit(values: OcorrenciaFormValues): void {
    if (souAdministrador && !predioIdAdmin) return;
    if (editing) {
      updateMutation.mutate({ id: editing.id, input: values });
      return;
    }
    createMutation.mutate({ ...values, predio_id: souAdministrador ? predioIdAdmin : undefined });
  }

  function iniciarEdicao(ocorrencia: Ocorrencia): void {
    setEditing(ocorrencia);
    reset({ titulo: ocorrencia.titulo, descricao: ocorrencia.descricao });
  }

  return (
    <AppShell>
      <h1 className="mb-4 text-xl font-bold text-slate-800">Livro de Ocorrências</h1>

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

      <div className="mb-6 space-y-3 rounded-2xl bg-white p-4 shadow-sm">
        <h2 className="text-sm font-semibold text-slate-700">
          {editing ? `Editar ocorrência #${editing.id}` : "Registrar ocorrência"}
        </h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-3" noValidate>
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">Título</label>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              {...register("titulo")}
            />
            {errors.titulo && <p className="mt-1 text-xs text-red-600">{errors.titulo.message}</p>}
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">Descrição</label>
            <textarea
              rows={3}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              {...register("descricao")}
            />
            {errors.descricao && (
              <p className="mt-1 text-xs text-red-600">{errors.descricao.message}</p>
            )}
          </div>

          {(createMutation.isError || updateMutation.isError) && (
            <p className="text-sm text-red-600">Não foi possível salvar. Tente novamente.</p>
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
              {editing ? "Salvar alterações" : "Registrar"}
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

      {isLoading && <p className="text-sm text-slate-500">Carregando...</p>}

      <ul className="space-y-2">
        {ocorrencias?.map((ocorrencia) => (
          <li key={ocorrencia.id} className="rounded-xl bg-white p-3 shadow-sm">
            <div className="flex items-start justify-between gap-2">
              <p className="font-medium text-slate-800">{ocorrencia.titulo}</p>
              {podeEditar && (
                <button
                  type="button"
                  onClick={() => iniciarEdicao(ocorrencia)}
                  className="shrink-0 text-xs font-medium text-brand-600"
                >
                  Editar
                </button>
              )}
            </div>
            <p className="mt-1 whitespace-pre-wrap text-sm text-slate-600">{ocorrencia.descricao}</p>
            <div className="mt-2 flex items-center justify-between">
              <span className="text-xs text-slate-400">{formatarData(ocorrencia.created_at)}</span>
              {ocorrencia.editado_em && (
                <span className="text-xs italic text-slate-400">Mensagem editada</span>
              )}
            </div>
          </li>
        ))}
        {ocorrencias?.length === 0 && (
          <li className="rounded-xl bg-white p-4 text-center text-sm text-slate-500 shadow-sm">
            Nenhuma ocorrência registrada.
          </li>
        )}
      </ul>
    </AppShell>
  );
}
