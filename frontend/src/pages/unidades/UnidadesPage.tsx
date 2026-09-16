import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { AppShell } from "../../components/layout/AppShell";
import { useAuth } from "../../auth/AuthContext";
import { createUnidade, deleteUnidade, listUnidades, updateUnidade } from "../../api/unidades";
import type { Unidade, UnidadeInput } from "../../api/types";

const unidadeSchema = z.object({
  bloco: z.string().min(1, "Informe o bloco."),
  numero: z.string().min(1, "Informe o numero."),
  proprietario_id: z.string().optional(),
});

type UnidadeFormValues = z.infer<typeof unidadeSchema>;

function toUnidadeInput(values: UnidadeFormValues): UnidadeInput {
  const proprietarioId = values.proprietario_id?.trim();
  return {
    bloco: values.bloco,
    numero: values.numero,
    proprietario_id: proprietarioId ? Number(proprietarioId) : null,
  };
}

export function UnidadesPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<Unidade | null>(null);
  const podeGerenciar = user?.role === "administrador" || user?.role === "sindico";

  const { data: unidades, isLoading } = useQuery({
    queryKey: ["unidades"],
    queryFn: listUnidades,
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<UnidadeFormValues>({
    resolver: zodResolver(unidadeSchema),
    defaultValues: { bloco: "", numero: "", proprietario_id: "" },
  });

  useEffect(() => {
    if (editing) {
      reset({
        bloco: editing.bloco,
        numero: editing.numero,
        proprietario_id: editing.proprietario_id ? String(editing.proprietario_id) : "",
      });
    } else {
      reset({ bloco: "", numero: "", proprietario_id: "" });
    }
  }, [editing, reset]);

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["unidades"] });

  const createMutation = useMutation({
    mutationFn: createUnidade,
    onSuccess: () => {
      invalidate();
      reset({ bloco: "", numero: "", proprietario_id: "" });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, input }: { id: number; input: UnidadeInput }) => updateUnidade(id, input),
    onSuccess: () => {
      invalidate();
      setEditing(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteUnidade,
    onSuccess: invalidate,
  });

  function onSubmit(values: UnidadeFormValues): void {
    const input = toUnidadeInput(values);
    if (editing) {
      updateMutation.mutate({ id: editing.id, input });
    } else {
      createMutation.mutate(input);
    }
  }

  const erroMutacao = createMutation.error ?? updateMutation.error;

  return (
    <AppShell>
      <h1 className="mb-4 text-xl font-bold text-slate-800">Unidades</h1>

      {podeGerenciar && (
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="mb-6 space-y-3 rounded-2xl bg-white p-4 shadow-sm"
          noValidate
        >
          <h2 className="text-sm font-semibold text-slate-700">
            {editing ? `Editar unidade #${editing.id}` : "Nova unidade"}
          </h2>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Bloco</label>
              <input
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                {...register("bloco")}
              />
              {errors.bloco && <p className="mt-1 text-xs text-red-600">{errors.bloco.message}</p>}
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Numero</label>
              <input
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                {...register("numero")}
              />
              {errors.numero && (
                <p className="mt-1 text-xs text-red-600">{errors.numero.message}</p>
              )}
            </div>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">
              ID do proprietario (opcional)
            </label>
            <input
              inputMode="numeric"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              {...register("proprietario_id")}
            />
          </div>

          {erroMutacao && (
            <p className="text-sm text-red-600">
              Nao foi possivel salvar a unidade. Verifique os dados e tente novamente.
            </p>
          )}

          <div className="flex gap-2">
            <button
              type="submit"
              disabled={isSubmitting}
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
            >
              {editing ? "Salvar" : "Adicionar"}
            </button>
            {editing && (
              <button
                type="button"
                onClick={() => setEditing(null)}
                className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600"
              >
                Cancelar
              </button>
            )}
          </div>
        </form>
      )}

      {isLoading && <p className="text-sm text-slate-500">Carregando...</p>}

      <ul className="space-y-2">
        {unidades?.map((unidade) => (
          <li
            key={unidade.id}
            className="flex items-center justify-between rounded-xl bg-white p-3 shadow-sm"
          >
            <div>
              <p className="font-medium text-slate-800">
                Bloco {unidade.bloco} - {unidade.numero}
              </p>
              <p className="text-xs text-slate-500">
                Proprietario: {unidade.proprietario_id ?? "nao definido"}
              </p>
            </div>
            {podeGerenciar && (
              <div className="flex shrink-0 gap-3">
                <button
                  type="button"
                  onClick={() => setEditing(unidade)}
                  className="text-xs font-medium text-brand-600"
                >
                  Editar
                </button>
                <button
                  type="button"
                  onClick={() => deleteMutation.mutate(unidade.id)}
                  className="text-xs font-medium text-red-600"
                >
                  Remover
                </button>
              </div>
            )}
          </li>
        ))}
        {unidades?.length === 0 && (
          <li className="rounded-xl bg-white p-4 text-center text-sm text-slate-500 shadow-sm">
            Nenhuma unidade cadastrada.
          </li>
        )}
      </ul>
    </AppShell>
  );
}
