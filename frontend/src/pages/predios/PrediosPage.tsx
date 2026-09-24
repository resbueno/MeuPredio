import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useFieldArray, useForm } from "react-hook-form";
import { z } from "zod";
import axios from "axios";
import { AppShell } from "../../components/layout/AppShell";
import { atualizarModulos, createPredio, gerarConvite, listPredios } from "../../api/predios";
import { TODOS_MODULOS, type ModuloEnum, type Predio } from "../../api/types";

const predioSchema = z.object({
  nome: z.string().min(2, "Informe o nome do prédio."),
  cep: z.string().regex(/^\d{5}-?\d{3}$/, "CEP inválido (formato 00000-000)."),
  numero: z.string().min(1, "Informe o número do prédio."),
  complemento: z.string().optional(),
  unidades: z
    .array(z.object({ bloco: z.string().min(1, "Bloco obrigatório."), numero: z.string().min(1, "Número obrigatório.") }))
    .default([]),
  modulos_habilitados: z.array(z.string()).default(TODOS_MODULOS.map((m) => m.value)),
});

type PredioFormValues = z.infer<typeof predioSchema>;

function linkDeCadastro(token: string): string {
  const base = window.location.origin + import.meta.env.BASE_URL.replace(/\/$/, "");
  return `${base}/cadastro/${token}`;
}

export function PrediosPage() {
  const queryClient = useQueryClient();
  const [convitesGerados, setConvitesGerados] = useState<Record<number, string>>({});
  const [erroCriacao, setErroCriacao] = useState<string | null>(null);

  const { data: predios, isLoading } = useQuery({ queryKey: ["predios"], queryFn: listPredios });

  const valoresIniciais = {
    nome: "",
    cep: "",
    numero: "",
    complemento: "",
    unidades: [{ bloco: "", numero: "" }],
    modulos_habilitados: TODOS_MODULOS.map((m) => m.value),
  };

  const {
    register,
    control,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<PredioFormValues>({
    resolver: zodResolver(predioSchema),
    defaultValues: valoresIniciais,
  });

  const { fields, append, remove } = useFieldArray({ control, name: "unidades" });

  const createMutation = useMutation({
    mutationFn: createPredio,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["predios"] });
      reset(valoresIniciais);
      setErroCriacao(null);
    },
    onError: (err) => {
      if (axios.isAxiosError(err) && err.response?.status === 404) {
        setErroCriacao("CEP não encontrado.");
      } else if (axios.isAxiosError(err) && err.response?.status === 409) {
        setErroCriacao("Já existe um prédio cadastrado com este CEP e número.");
      } else {
        setErroCriacao("Não foi possível cadastrar o prédio.");
      }
    },
  });

  const conviteMutation = useMutation({
    mutationFn: gerarConvite,
    onSuccess: (convite) => {
      setConvitesGerados((atual) => ({ ...atual, [convite.predio_id]: convite.token }));
    },
  });

  const modulosMutation = useMutation({
    mutationFn: ({ predioId, modulos }: { predioId: number; modulos: string[] }) =>
      atualizarModulos(predioId, modulos),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["predios"] });
    },
  });

  function onSubmit(values: PredioFormValues): void {
    setErroCriacao(null);
    createMutation.mutate({
      nome: values.nome,
      cep: values.cep,
      numero: values.numero,
      complemento: values.complemento || undefined,
      unidades: values.unidades.filter((u) => u.bloco && u.numero),
      modulos_habilitados: values.modulos_habilitados as ModuloEnum[],
    });
  }

  function alternarModulo(predio: Predio, modulo: ModuloEnum): void {
    const ativos = new Set(predio.modulos_habilitados);
    if (ativos.has(modulo)) {
      ativos.delete(modulo);
    } else {
      ativos.add(modulo);
    }
    modulosMutation.mutate({ predioId: predio.id, modulos: Array.from(ativos) });
  }

  async function copiarLink(link: string): Promise<void> {
    try {
      await navigator.clipboard.writeText(link);
    } catch {
      // Clipboard indisponivel (ex.: contexto nao seguro) - o link ainda
      // fica visivel na tela para copiar manualmente.
    }
  }

  return (
    <AppShell>
      <h1 className="mb-4 text-xl font-bold text-slate-800">Prédios</h1>

      <form
        onSubmit={handleSubmit(onSubmit)}
        className="mb-6 space-y-3 rounded-2xl bg-white p-4 shadow-sm"
        noValidate
      >
        <h2 className="text-sm font-semibold text-slate-700">Novo prédio</h2>

        <div>
          <label className="mb-1 block text-xs font-medium text-slate-600">Nome</label>
          <input
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            placeholder="Ex.: Edifício Aurora"
            {...register("nome")}
          />
          {errors.nome && <p className="mt-1 text-xs text-red-600">{errors.nome.message}</p>}
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">CEP</label>
            <input
              placeholder="00000-000"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              {...register("cep")}
            />
            {errors.cep && <p className="mt-1 text-xs text-red-600">{errors.cep.message}</p>}
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">Número</label>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              {...register("numero")}
            />
            {errors.numero && <p className="mt-1 text-xs text-red-600">{errors.numero.message}</p>}
          </div>
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-slate-600">
            Complemento (opcional)
          </label>
          <input
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            {...register("complemento")}
          />
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-slate-600">
            Unidades iniciais
          </label>
          <div className="space-y-2">
            {fields.map((field, index) => (
              <div key={field.id} className="flex gap-2">
                <input
                  placeholder="Bloco"
                  className="w-1/2 rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  {...register(`unidades.${index}.bloco` as const)}
                />
                <input
                  placeholder="Número"
                  className="w-1/2 rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  {...register(`unidades.${index}.numero` as const)}
                />
                <button
                  type="button"
                  onClick={() => remove(index)}
                  className="shrink-0 rounded-lg border border-slate-300 px-3 text-sm text-slate-500"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
          <button
            type="button"
            onClick={() => append({ bloco: "", numero: "" })}
            className="mt-2 text-xs font-medium text-brand-600"
          >
            + Adicionar unidade
          </button>
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-slate-600">
            Módulos habilitados
          </label>
          <div className="grid grid-cols-1 gap-1.5 sm:grid-cols-2">
            {TODOS_MODULOS.map((modulo) => (
              <label key={modulo.value} className="flex items-center gap-2 text-xs text-slate-600">
                <input
                  type="checkbox"
                  value={modulo.value}
                  className="h-4 w-4 rounded border-slate-300"
                  {...register("modulos_habilitados")}
                />
                {modulo.label}
              </label>
            ))}
          </div>
        </div>

        {erroCriacao && <p className="text-sm text-red-600">{erroCriacao}</p>}

        <button
          type="submit"
          disabled={isSubmitting}
          className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
        >
          Cadastrar prédio
        </button>
      </form>

      {isLoading && <p className="text-sm text-slate-500">Carregando...</p>}

      <ul className="space-y-2">
        {predios?.map((predio: Predio) => {
          const token = convitesGerados[predio.id];
          return (
            <li key={predio.id} className="rounded-xl bg-white p-3 shadow-sm">
              <p className="font-medium text-slate-800">{predio.nome}</p>
              <p className="text-xs text-slate-500">
                {predio.logradouro ? `${predio.logradouro}, ` : ""}
                {predio.numero} {predio.complemento ? `- ${predio.complemento}` : ""} · {predio.cidade}
                {predio.uf ? `/${predio.uf}` : ""}
              </p>

              <div className="mt-2 flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => conviteMutation.mutate(predio.id)}
                  className="text-xs font-medium text-brand-600"
                >
                  Gerar link de autocadastro
                </button>
              </div>

              <div className="mt-3 rounded-lg bg-slate-50 p-2">
                <p className="mb-1.5 text-xs font-semibold text-slate-600">Módulos habilitados</p>
                <div className="grid grid-cols-1 gap-1 sm:grid-cols-2">
                  {TODOS_MODULOS.map((modulo) => (
                    <label key={modulo.value} className="flex items-center gap-2 text-xs text-slate-600">
                      <input
                        type="checkbox"
                        className="h-4 w-4 rounded border-slate-300"
                        checked={predio.modulos_habilitados.includes(modulo.value)}
                        disabled={modulosMutation.isPending}
                        onChange={() => alternarModulo(predio, modulo.value)}
                      />
                      {modulo.label}
                    </label>
                  ))}
                </div>
              </div>

              {token && (
                <div className="mt-2 rounded-lg bg-slate-50 p-2">
                  <p className="break-all text-xs text-slate-600">{linkDeCadastro(token)}</p>
                  <button
                    type="button"
                    onClick={() => copiarLink(linkDeCadastro(token))}
                    className="mt-1 text-xs font-medium text-brand-600"
                  >
                    Copiar link
                  </button>
                </div>
              )}
            </li>
          );
        })}
        {predios?.length === 0 && (
          <li className="rounded-xl bg-white p-4 text-center text-sm text-slate-500 shadow-sm">
            Nenhum prédio cadastrado.
          </li>
        )}
      </ul>
    </AppShell>
  );
}
