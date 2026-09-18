import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { AppShell } from "../../components/layout/AppShell";
import { useAuth } from "../../auth/AuthContext";
import { temPapel } from "../../auth/roles";
import {
  createUnidade,
  createUnidadesLote,
  deleteUnidade,
  listUnidades,
  updateUnidade,
} from "../../api/unidades";
import type { Unidade, UnidadeInput } from "../../api/types";

const unidadeSchema = z.object({
  bloco: z.string().min(1, "Informe o bloco."),
  numero: z.string().min(1, "Informe o número."),
  predio_id: z.string().optional(),
});

type UnidadeFormValues = z.infer<typeof unidadeSchema>;

function toUnidadeInput(values: UnidadeFormValues): UnidadeInput {
  const predioId = values.predio_id?.trim();
  return {
    bloco: values.bloco,
    numero: values.numero,
    predio_id: predioId ? Number(predioId) : null,
  };
}

/** Gera os números por andar: térreo (se incluído) é o andar "0", depois
 * 1, 2, 3... - cada número é "<andar><posição>" (posição preenchida com
 * zeros à esquerda até caber a quantidade de unidades por andar). Ex.: 5
 * andares, 3 por andar, com térreo -> 01,02,03, 11,12,13, 21,22,23... */
function gerarNumerosLote(andares: number, porAndar: number, incluirTerreo: boolean): string[] {
  if (andares < 1 || porAndar < 1) return [];
  const andarInicial = incluirTerreo ? 0 : 1;
  const andarFinal = incluirTerreo ? andares - 1 : andares;
  const digitosPosicao = String(porAndar).length;
  const numeros: string[] = [];
  for (let andar = andarInicial; andar <= andarFinal; andar++) {
    for (let posicao = 1; posicao <= porAndar; posicao++) {
      numeros.push(`${andar}${String(posicao).padStart(digitosPosicao, "0")}`);
    }
  }
  return numeros;
}

export function UnidadesPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<Unidade | null>(null);
  const souAdministrador = user?.role === "administrador";
  const podeGerenciar = temPapel(user, "administrador", "sindico");

  const { data: unidades, isLoading } = useQuery({
    queryKey: ["unidades"],
    queryFn: () => listUnidades(),
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<UnidadeFormValues>({
    resolver: zodResolver(unidadeSchema),
    defaultValues: { bloco: "", numero: "", predio_id: "" },
  });

  useEffect(() => {
    if (editing) {
      reset({ bloco: editing.bloco, numero: editing.numero, predio_id: String(editing.predio_id) });
    } else {
      reset({ bloco: "", numero: "", predio_id: "" });
    }
  }, [editing, reset]);

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["unidades"] });

  const createMutation = useMutation({
    mutationFn: createUnidade,
    onSuccess: () => {
      invalidate();
      reset({ bloco: "", numero: "", predio_id: "" });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, input }: { id: number; input: Partial<UnidadeInput> }) =>
      updateUnidade(id, input),
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
    if (editing) {
      updateMutation.mutate({ id: editing.id, input: { bloco: values.bloco, numero: values.numero } });
      return;
    }
    createMutation.mutate(toUnidadeInput(values));
  }

  const erroMutacao = createMutation.error ?? updateMutation.error;

  const [mostrarLote, setMostrarLote] = useState(false);
  const [loteBloco, setLoteBloco] = useState("");
  const [loteAndares, setLoteAndares] = useState("1");
  const [lotePorAndar, setLotePorAndar] = useState("1");
  const [loteIncluirTerreo, setLoteIncluirTerreo] = useState(true);
  const [lotePredioId, setLotePredioId] = useState("");

  const loteNumeros = useMemo(
    () => gerarNumerosLote(Number(loteAndares) || 0, Number(lotePorAndar) || 0, loteIncluirTerreo),
    [loteAndares, lotePorAndar, loteIncluirTerreo]
  );

  const loteMutation = useMutation({
    mutationFn: createUnidadesLote,
    onSuccess: () => {
      invalidate();
      setLoteBloco("");
      setLoteAndares("1");
      setLotePorAndar("1");
      setLoteIncluirTerreo(true);
      setLotePredioId("");
      setMostrarLote(false);
    },
  });

  function onSubmitLote(): void {
    if (!loteBloco.trim() || loteNumeros.length === 0) return;
    if (souAdministrador && !lotePredioId.trim()) return;
    loteMutation.mutate({
      unidades: loteNumeros.map((numero) => ({ bloco: loteBloco.trim(), numero })),
      predio_id: souAdministrador ? Number(lotePredioId.trim()) : undefined,
    });
  }

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
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Bloco</label>
              <input
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                {...register("bloco")}
              />
              {errors.bloco && <p className="mt-1 text-xs text-red-600">{errors.bloco.message}</p>}
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Número</label>
              <input
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                {...register("numero")}
              />
              {errors.numero && (
                <p className="mt-1 text-xs text-red-600">{errors.numero.message}</p>
              )}
            </div>
          </div>
          {souAdministrador && !editing && (
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">
                ID do prédio (obrigatório para administrador)
              </label>
              <input
                inputMode="numeric"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                {...register("predio_id")}
              />
              <p className="mt-1 text-xs text-slate-400">
                Síndico não precisa preencher - a unidade sempre vai para o próprio prédio.
              </p>
            </div>
          )}

          {erroMutacao && (
            <p className="text-sm text-red-600">
              Não foi possível salvar a unidade. Verifique os dados e tente novamente.
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

      {podeGerenciar && (
        <div className="mb-6 rounded-2xl bg-white p-4 shadow-sm">
          <button
            type="button"
            onClick={() => setMostrarLote((v) => !v)}
            className="text-sm font-semibold text-brand-600"
          >
            {mostrarLote ? "Fechar cadastro em lote" : "Cadastrar em lote (ex.: um bloco inteiro)"}
          </button>

          {mostrarLote && (
            <div className="mt-3 space-y-3">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-xs font-medium text-slate-600">Bloco</label>
                  <input
                    value={loteBloco}
                    onChange={(event) => setLoteBloco(event.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    placeholder="Ex.: 1"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-slate-600">
                    Unidades por andar
                  </label>
                  <input
                    inputMode="numeric"
                    value={lotePorAndar}
                    onChange={(event) => setLotePorAndar(event.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-xs font-medium text-slate-600">
                    Quantidade de andares
                  </label>
                  <input
                    inputMode="numeric"
                    value={loteAndares}
                    onChange={(event) => setLoteAndares(event.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>
                <div className="flex items-end pb-2">
                  <label className="flex items-center gap-2 text-sm text-slate-700">
                    <input
                      type="checkbox"
                      checked={loteIncluirTerreo}
                      onChange={(event) => setLoteIncluirTerreo(event.target.checked)}
                      className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-400"
                    />
                    Considerar o térreo
                  </label>
                </div>
              </div>

              {souAdministrador && (
                <div>
                  <label className="mb-1 block text-xs font-medium text-slate-600">
                    ID do prédio
                  </label>
                  <input
                    inputMode="numeric"
                    value={lotePredioId}
                    onChange={(event) => setLotePredioId(event.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>
              )}

              <div>
                <p className="mb-1 text-xs font-medium text-slate-600">
                  Prévia ({loteNumeros.length} unidade{loteNumeros.length === 1 ? "" : "s"})
                </p>
                <p className="rounded-lg bg-slate-50 p-2 text-sm text-slate-600">
                  {loteNumeros.length > 0
                    ? loteNumeros.join(", ")
                    : "Ajuste os campos acima para gerar a prévia."}
                </p>
              </div>

              {loteMutation.isError && (
                <p className="text-sm text-red-600">
                  Não foi possível criar o lote. Verifique se alguma unidade já existe.
                </p>
              )}

              <button
                type="button"
                onClick={onSubmitLote}
                disabled={
                  loteMutation.isPending ||
                  !loteBloco.trim() ||
                  loteNumeros.length === 0 ||
                  (souAdministrador && !lotePredioId.trim())
                }
                className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
              >
                Criar {loteNumeros.length} unidade{loteNumeros.length === 1 ? "" : "s"}
              </button>
            </div>
          )}
        </div>
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
