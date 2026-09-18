import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { AppShell } from "../../components/layout/AppShell";
import { useAuth } from "../../auth/AuthContext";
import { createVeiculo, deleteVeiculo, listVeiculos, updateVeiculo } from "../../api/veiculos";
import type { TipoVeiculoEnum, Veiculo, VeiculoInput } from "../../api/types";

const TIPOS: TipoVeiculoEnum[] = ["carro", "moto", "outro"];

const veiculoSchema = z.object({
  unidade_id: z.string().min(1, "Informe o id da unidade."),
  placa: z.string().min(6, "Informe uma placa válida."),
  modelo: z.string().min(1, "Informe o modelo."),
  cor: z.string().min(1, "Informe a cor."),
  tipo: z.enum(["carro", "moto", "outro"]),
});

type VeiculoFormValues = z.infer<typeof veiculoSchema>;

function toVeiculoInput(values: VeiculoFormValues): VeiculoInput {
  return {
    unidade_id: Number(values.unidade_id),
    placa: values.placa,
    modelo: values.modelo,
    cor: values.cor,
    tipo: values.tipo,
  };
}

const TIPO_LABELS: Record<TipoVeiculoEnum, string> = {
  carro: "Carro",
  moto: "Moto",
  outro: "Outro",
};

export function VeiculosPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<Veiculo | null>(null);
  const podeGerenciar =
    user?.role === "administrador" || user?.role === "sindico" || user?.role === "zelador";

  const { data: veiculos, isLoading } = useQuery({
    queryKey: ["veiculos"],
    queryFn: listVeiculos,
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<VeiculoFormValues>({
    resolver: zodResolver(veiculoSchema),
    defaultValues: { unidade_id: "", placa: "", modelo: "", cor: "", tipo: "carro" },
  });

  useEffect(() => {
    if (editing) {
      reset({
        unidade_id: String(editing.unidade_id),
        placa: editing.placa,
        modelo: editing.modelo,
        cor: editing.cor,
        tipo: editing.tipo,
      });
    } else {
      reset({ unidade_id: "", placa: "", modelo: "", cor: "", tipo: "carro" });
    }
  }, [editing, reset]);

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["veiculos"] });

  const createMutation = useMutation({
    mutationFn: createVeiculo,
    onSuccess: () => {
      invalidate();
      reset({ unidade_id: "", placa: "", modelo: "", cor: "", tipo: "carro" });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, input }: { id: number; input: VeiculoInput }) => updateVeiculo(id, input),
    onSuccess: () => {
      invalidate();
      setEditing(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteVeiculo,
    onSuccess: invalidate,
  });

  function onSubmit(values: VeiculoFormValues): void {
    const input = toVeiculoInput(values);
    if (editing) {
      updateMutation.mutate({ id: editing.id, input });
    } else {
      createMutation.mutate(input);
    }
  }

  const erroMutacao = createMutation.error ?? updateMutation.error;

  return (
    <AppShell>
      <h1 className="mb-4 text-xl font-bold text-slate-800">Veículos</h1>

      {podeGerenciar && (
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="mb-6 space-y-3 rounded-2xl bg-white p-4 shadow-sm"
          noValidate
        >
          <h2 className="text-sm font-semibold text-slate-700">
            {editing ? `Editar veículo #${editing.id}` : "Novo veículo"}
          </h2>

          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">ID da unidade</label>
            <input
              inputMode="numeric"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              {...register("unidade_id")}
            />
            {errors.unidade_id && (
              <p className="mt-1 text-xs text-red-600">{errors.unidade_id.message}</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Placa</label>
              <input
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm uppercase"
                {...register("placa")}
              />
              {errors.placa && <p className="mt-1 text-xs text-red-600">{errors.placa.message}</p>}
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Tipo</label>
              <select
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                {...register("tipo")}
              >
                {TIPOS.map((tipo) => (
                  <option key={tipo} value={tipo}>
                    {TIPO_LABELS[tipo]}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Modelo</label>
              <input
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                {...register("modelo")}
              />
              {errors.modelo && (
                <p className="mt-1 text-xs text-red-600">{errors.modelo.message}</p>
              )}
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Cor</label>
              <input
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                {...register("cor")}
              />
              {errors.cor && <p className="mt-1 text-xs text-red-600">{errors.cor.message}</p>}
            </div>
          </div>

          {erroMutacao && (
            <p className="text-sm text-red-600">
              Não foi possível salvar o veículo. Verifique os dados e tente novamente.
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
        {veiculos?.map((veiculo) => (
          <li
            key={veiculo.id}
            className="flex items-center justify-between rounded-xl bg-white p-3 shadow-sm"
          >
            <div>
              <p className="font-medium text-slate-800">
                {veiculo.placa} - {veiculo.modelo}
              </p>
              <p className="text-xs text-slate-500">
                {TIPO_LABELS[veiculo.tipo]} - {veiculo.cor} - Unidade #{veiculo.unidade_id}
              </p>
            </div>
            {podeGerenciar && (
              <div className="flex shrink-0 gap-3">
                <button
                  type="button"
                  onClick={() => setEditing(veiculo)}
                  className="text-xs font-medium text-brand-600"
                >
                  Editar
                </button>
                <button
                  type="button"
                  onClick={() => deleteMutation.mutate(veiculo.id)}
                  className="text-xs font-medium text-red-600"
                >
                  Remover
                </button>
              </div>
            )}
          </li>
        ))}
        {veiculos?.length === 0 && (
          <li className="rounded-xl bg-white p-4 text-center text-sm text-slate-500 shadow-sm">
            Nenhum veículo cadastrado.
          </li>
        )}
      </ul>
    </AppShell>
  );
}
