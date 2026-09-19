import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useFieldArray, useForm } from "react-hook-form";
import { z } from "zod";
import { AppShell } from "../../components/layout/AppShell";
import { useAuth } from "../../auth/AuthContext";
import { createVisitantesLote, listVisitantes } from "../../api/visitantes";
import { listUnidades } from "../../api/unidades";
import type { TipoDocumentoVisitanteEnum } from "../../api/types";

const TIPO_DOCUMENTO_LABEL: Record<TipoDocumentoVisitanteEnum, string> = {
  rg: "RG",
  cpf: "CPF",
  cin: "CIN",
  nao_informado: "Não informado",
};

const visitanteItemSchema = z
  .object({
    nome_completo: z.string().min(2, "Informe o nome completo."),
    tipo_documento: z.enum(["rg", "cpf", "cin", "nao_informado"]),
    numero_documento: z.string().optional(),
    veiculo_placa: z.string().optional(),
    veiculo_modelo: z.string().optional(),
    veiculo_cor: z.string().optional(),
  })
  .refine(
    (dados) =>
      dados.tipo_documento === "nao_informado" || (dados.numero_documento ?? "").trim().length > 0,
    { message: "Informe o número do documento, ou selecione 'Não informado'.", path: ["numero_documento"] }
  )
  .refine(
    (dados) => dados.tipo_documento !== "nao_informado" || !(dados.numero_documento ?? "").trim(),
    { message: "Não informe número quando o tipo for 'Não informado'.", path: ["numero_documento"] }
  );

const loteSchema = z.object({
  unidade_id: z.string().min(1, "Selecione a unidade."),
  visitantes: z.array(visitanteItemSchema).min(1),
});

type LoteFormValues = z.infer<typeof loteSchema>;

const VISITANTE_VAZIO = {
  nome_completo: "",
  tipo_documento: "rg" as TipoDocumentoVisitanteEnum,
  numero_documento: "",
  veiculo_placa: "",
  veiculo_modelo: "",
  veiculo_cor: "",
};

function formatarData(data: string): string {
  return new Date(data).toLocaleString("pt-BR");
}

export function VisitantesPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const souAdministrador = user?.role === "administrador";

  const [predioIdAdminInput, setPredioIdAdminInput] = useState("");
  const predioIdAdmin = predioIdAdminInput.trim() ? Number(predioIdAdminInput.trim()) : null;
  const bloqueadoSemPredio = souAdministrador && !predioIdAdmin;

  const { data: visitantes, isLoading } = useQuery({
    queryKey: ["visitantes", souAdministrador ? predioIdAdmin : "proprio"],
    queryFn: () => listVisitantes({ predioId: souAdministrador ? predioIdAdmin : undefined }),
    enabled: !bloqueadoSemPredio,
  });

  const { data: unidades } = useQuery({
    queryKey: ["unidades", "combo", souAdministrador ? predioIdAdmin : "proprio"],
    queryFn: () => listUnidades(souAdministrador ? predioIdAdmin : undefined),
    enabled: !bloqueadoSemPredio,
  });

  function labelUnidade(unidadeId: number): string {
    const unidade = unidades?.find((u) => u.id === unidadeId);
    return unidade ? `Bloco ${unidade.bloco} - ${unidade.numero}` : `Unidade #${unidadeId}`;
  }

  const {
    register,
    control,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<LoteFormValues>({
    resolver: zodResolver(loteSchema),
    defaultValues: { unidade_id: "", visitantes: [VISITANTE_VAZIO] },
  });

  const { fields, append, remove } = useFieldArray({ control, name: "visitantes" });
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["visitantes"] });

  const createMutation = useMutation({
    mutationFn: createVisitantesLote,
    onSuccess: () => {
      invalidate();
      reset({ unidade_id: "", visitantes: [VISITANTE_VAZIO] });
    },
  });

  function onSubmit(values: LoteFormValues): void {
    if (souAdministrador && !predioIdAdmin) return;
    createMutation.mutate({
      unidade_id: Number(values.unidade_id),
      visitantes: values.visitantes.map((v) => ({
        nome_completo: v.nome_completo,
        tipo_documento: v.tipo_documento,
        numero_documento: v.tipo_documento === "nao_informado" ? undefined : v.numero_documento,
        veiculo_placa: v.veiculo_placa || undefined,
        veiculo_modelo: v.veiculo_modelo || undefined,
        veiculo_cor: v.veiculo_cor || undefined,
      })),
      predio_id: souAdministrador ? predioIdAdmin : undefined,
    });
  }

  return (
    <AppShell>
      <h1 className="mb-4 text-xl font-bold text-slate-800">Visitantes</h1>

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
        <h2 className="text-sm font-semibold text-slate-700">Registrar entrada de visitantes</h2>
        <p className="text-xs text-slate-500">
          Registre um ou vários visitantes de uma vez (ex.: convidados de um evento) para a mesma
          unidade.
        </p>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">Unidade visitada</label>
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

          <div className="space-y-3">
            {fields.map((field, index) => {
              const tipoSelecionado = watch(`visitantes.${index}.tipo_documento`);
              const erroItem = errors.visitantes?.[index];
              return (
                <div key={field.id} className="rounded-xl border border-slate-200 p-3">
                  <div className="mb-2 flex items-center justify-between">
                    <p className="text-xs font-semibold text-slate-500">Visitante {index + 1}</p>
                    {fields.length > 1 && (
                      <button
                        type="button"
                        onClick={() => remove(index)}
                        className="text-xs font-medium text-red-600"
                      >
                        Remover
                      </button>
                    )}
                  </div>

                  <div>
                    <label className="mb-1 block text-xs font-medium text-slate-600">
                      Nome completo
                    </label>
                    <input
                      className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                      {...register(`visitantes.${index}.nome_completo`)}
                    />
                    {erroItem?.nome_completo && (
                      <p className="mt-1 text-xs text-red-600">{erroItem.nome_completo.message}</p>
                    )}
                  </div>

                  <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
                    <div>
                      <label className="mb-1 block text-xs font-medium text-slate-600">Documento</label>
                      <select
                        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                        {...register(`visitantes.${index}.tipo_documento`)}
                      >
                        {Object.entries(TIPO_DOCUMENTO_LABEL).map(([valor, label]) => (
                          <option key={valor} value={valor}>
                            {label}
                          </option>
                        ))}
                      </select>
                    </div>
                    {tipoSelecionado !== "nao_informado" && (
                      <div>
                        <label className="mb-1 block text-xs font-medium text-slate-600">
                          Número do documento
                        </label>
                        <input
                          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                          {...register(`visitantes.${index}.numero_documento`)}
                        />
                      </div>
                    )}
                  </div>
                  {erroItem?.numero_documento && (
                    <p className="mt-1 text-xs text-red-600">{erroItem.numero_documento.message}</p>
                  )}

                  <div className="mt-3 rounded-lg bg-slate-50 p-3">
                    <p className="mb-2 text-xs font-medium text-slate-600">Veículo (opcional)</p>
                    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                      <input
                        placeholder="Placa"
                        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                        {...register(`visitantes.${index}.veiculo_placa`)}
                      />
                      <input
                        placeholder="Modelo"
                        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                        {...register(`visitantes.${index}.veiculo_modelo`)}
                      />
                      <input
                        placeholder="Cor"
                        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                        {...register(`visitantes.${index}.veiculo_cor`)}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <button
            type="button"
            onClick={() => append(VISITANTE_VAZIO)}
            className="text-sm font-medium text-brand-600"
          >
            + Adicionar outro visitante
          </button>

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
            {fields.length > 1 ? `Registrar ${fields.length} visitantes` : "Registrar entrada"}
          </button>
        </form>
      </div>

      {isLoading && <p className="text-sm text-slate-500">Carregando...</p>}

      {!bloqueadoSemPredio && (
        <ul className="space-y-2">
          {visitantes?.map((visitante) => (
            <li key={visitante.id} className="rounded-xl bg-white p-3 shadow-sm">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="font-medium text-slate-800">{visitante.nome_completo}</p>
                  <p className="text-xs text-slate-500">{labelUnidade(visitante.unidade_id)}</p>
                </div>
                <span className="shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
                  {TIPO_DOCUMENTO_LABEL[visitante.tipo_documento]}
                  {visitante.numero_documento ? `: ${visitante.numero_documento}` : ""}
                </span>
              </div>
              {(visitante.veiculo_placa || visitante.veiculo_modelo || visitante.veiculo_cor) && (
                <p className="mt-1 text-xs text-slate-500">
                  🚗 {[visitante.veiculo_modelo, visitante.veiculo_cor, visitante.veiculo_placa]
                    .filter(Boolean)
                    .join(" - ")}
                </p>
              )}
              <p className="mt-2 border-t border-slate-100 pt-2 text-xs text-slate-400">
                {formatarData(visitante.created_at)}
              </p>
            </li>
          ))}
          {visitantes?.length === 0 && (
            <li className="rounded-xl bg-white p-4 text-center text-sm text-slate-500 shadow-sm">
              Nenhum visitante registrado.
            </li>
          )}
        </ul>
      )}
    </AppShell>
  );
}
