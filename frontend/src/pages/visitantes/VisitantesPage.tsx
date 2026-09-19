import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { AppShell } from "../../components/layout/AppShell";
import { useAuth } from "../../auth/AuthContext";
import { createVisitante, listVisitantes } from "../../api/visitantes";
import { listUnidades } from "../../api/unidades";
import type { TipoDocumentoVisitanteEnum } from "../../api/types";

const TIPO_DOCUMENTO_LABEL: Record<TipoDocumentoVisitanteEnum, string> = {
  rg: "RG",
  cpf: "CPF",
  cin: "CIN",
  nao_informado: "Não informado",
};

const visitanteSchema = z
  .object({
    unidade_id: z.string().min(1, "Selecione a unidade."),
    nome_completo: z.string().min(2, "Informe o nome completo."),
    tipo_documento: z.enum(["rg", "cpf", "cin", "nao_informado"]),
    numero_documento: z.string().optional(),
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

type VisitanteFormValues = z.infer<typeof visitanteSchema>;

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
    handleSubmit,
    reset,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<VisitanteFormValues>({
    resolver: zodResolver(visitanteSchema),
    defaultValues: {
      unidade_id: "",
      nome_completo: "",
      tipo_documento: "rg",
      numero_documento: "",
    },
  });

  const tipoSelecionado = watch("tipo_documento");
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["visitantes"] });

  const createMutation = useMutation({
    mutationFn: createVisitante,
    onSuccess: () => {
      invalidate();
      reset({ unidade_id: "", nome_completo: "", tipo_documento: "rg", numero_documento: "" });
    },
  });

  function onSubmit(values: VisitanteFormValues): void {
    if (souAdministrador && !predioIdAdmin) return;
    createMutation.mutate({
      unidade_id: Number(values.unidade_id),
      nome_completo: values.nome_completo,
      tipo_documento: values.tipo_documento,
      numero_documento: values.tipo_documento === "nao_informado" ? undefined : values.numero_documento,
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
        <h2 className="text-sm font-semibold text-slate-700">Registrar entrada de visitante</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-3" noValidate>
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

          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">Nome completo</label>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              {...register("nome_completo")}
            />
            {errors.nome_completo && (
              <p className="mt-1 text-xs text-red-600">{errors.nome_completo.message}</p>
            )}
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Documento</label>
              <select
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                {...register("tipo_documento")}
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
                  {...register("numero_documento")}
                />
              </div>
            )}
          </div>
          {errors.numero_documento && (
            <p className="text-xs text-red-600">{errors.numero_documento.message}</p>
          )}

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
            Registrar entrada
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
