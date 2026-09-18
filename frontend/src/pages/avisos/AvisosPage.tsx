import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { AppShell } from "../../components/layout/AppShell";
import { useAuth } from "../../auth/AuthContext";
import { temPapel } from "../../auth/roles";
import {
  createAvisoMural,
  deleteAvisoMural,
  listAvisosMural,
  updateAvisoMural,
} from "../../api/avisosMural";
import type { AvisoMural } from "../../api/types";

const avisoSchema = z.object({
  tipo: z.enum(["condominio", "anuncio"]),
  titulo: z.string().min(2, "Informe um título."),
  descricao: z.string().min(2, "Informe uma descrição."),
  preco: z.string().optional(),
});

type AvisoFormValues = z.infer<typeof avisoSchema>;

function formatarValor(valor: string): string {
  const numero = Number(valor);
  return Number.isFinite(numero)
    ? numero.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
    : valor;
}

function formatarData(data: string): string {
  return new Date(data).toLocaleDateString("pt-BR");
}

function Bloco({
  titulo,
  itens,
  vazio,
  souGestao,
  userId,
  onEditar,
  onRemover,
}: {
  titulo: string;
  itens: AvisoMural[];
  vazio: string;
  souGestao: boolean;
  userId: number | undefined;
  onEditar: (aviso: AvisoMural) => void;
  onRemover: (id: number) => void;
}) {
  return (
    <div className="mb-6">
      <h2 className="mb-2 text-sm font-semibold text-slate-700">{titulo}</h2>
      <ul className="space-y-2">
        {itens.map((aviso) => {
          const podeEditar = aviso.tipo === "condominio" ? souGestao : aviso.created_by === userId;
          const podeRemover = podeEditar || (aviso.tipo === "anuncio" && souGestao);
          return (
            <li key={aviso.id} className="rounded-xl bg-white p-3 shadow-sm">
              <div className="flex items-start justify-between gap-2">
                <p className="font-medium text-slate-800">{aviso.titulo}</p>
                {aviso.preco && (
                  <span className="shrink-0 text-sm font-semibold text-brand-600">
                    {formatarValor(aviso.preco)}
                  </span>
                )}
              </div>
              <p className="mt-1 whitespace-pre-wrap text-sm text-slate-600">{aviso.descricao}</p>
              <div className="mt-2 flex items-center justify-between">
                <span className="text-xs text-slate-400">{formatarData(aviso.created_at)}</span>
                <div className="flex gap-3">
                  {podeEditar && (
                    <button
                      type="button"
                      onClick={() => onEditar(aviso)}
                      className="text-xs font-medium text-brand-600"
                    >
                      Editar
                    </button>
                  )}
                  {podeRemover && (
                    <button
                      type="button"
                      onClick={() => onRemover(aviso.id)}
                      className="text-xs font-medium text-red-600"
                    >
                      Remover
                    </button>
                  )}
                </div>
              </div>
            </li>
          );
        })}
        {itens.length === 0 && (
          <li className="rounded-xl bg-white p-4 text-center text-sm text-slate-500 shadow-sm">
            {vazio}
          </li>
        )}
      </ul>
    </div>
  );
}

export function AvisosPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const souGestao = temPapel(user, "administrador", "sindico");
  const souAdministrador = user?.role === "administrador";

  const [predioIdAdminInput, setPredioIdAdminInput] = useState("");
  const predioIdAdmin = predioIdAdminInput.trim() ? Number(predioIdAdminInput.trim()) : null;
  const bloqueadoSemPredio = souAdministrador && !predioIdAdmin;

  const [editing, setEditing] = useState<AvisoMural | null>(null);

  const { data: avisos, isLoading } = useQuery({
    queryKey: ["avisos-mural", souAdministrador ? predioIdAdmin : "proprio"],
    queryFn: () => listAvisosMural({ predioId: souAdministrador ? predioIdAdmin : undefined }),
    enabled: !bloqueadoSemPredio,
  });

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<AvisoFormValues>({
    resolver: zodResolver(avisoSchema),
    defaultValues: { tipo: "anuncio", titulo: "", descricao: "", preco: "" },
  });

  const tipoSelecionado = watch("tipo");

  function limparFormulario(): void {
    reset({ tipo: "anuncio", titulo: "", descricao: "", preco: "" });
    setEditing(null);
  }

  function iniciarEdicao(aviso: AvisoMural): void {
    setEditing(aviso);
    reset({ tipo: aviso.tipo, titulo: aviso.titulo, descricao: aviso.descricao, preco: aviso.preco ?? "" });
  }

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["avisos-mural"] });

  const createMutation = useMutation({
    mutationFn: createAvisoMural,
    onSuccess: () => {
      invalidate();
      limparFormulario();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, input }: { id: number; input: { titulo: string; descricao: string; preco?: string | null } }) =>
      updateAvisoMural(id, input),
    onSuccess: () => {
      invalidate();
      limparFormulario();
    },
  });

  const deleteMutation = useMutation({ mutationFn: deleteAvisoMural, onSuccess: invalidate });

  function onSubmit(values: AvisoFormValues): void {
    if (souAdministrador && !predioIdAdmin) return;
    const preco = values.preco?.trim() ? values.preco.replace(",", ".") : null;
    if (editing) {
      updateMutation.mutate({ id: editing.id, input: { titulo: values.titulo, descricao: values.descricao, preco } });
      return;
    }
    createMutation.mutate({
      tipo: values.tipo,
      titulo: values.titulo,
      descricao: values.descricao,
      preco,
      predio_id: souAdministrador ? predioIdAdmin : undefined,
    });
  }

  const avisosCondominio = avisos?.filter((a) => a.tipo === "condominio") ?? [];
  const anuncios = avisos?.filter((a) => a.tipo === "anuncio") ?? [];

  return (
    <AppShell>
      <h1 className="mb-4 text-xl font-bold text-slate-800">Avisos</h1>

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
          {editing ? `Editar ${editing.tipo === "condominio" ? "aviso" : "anúncio"}` : "Publicar"}
        </h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-3" noValidate>
          {!editing && (
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Tipo</label>
              <select
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                {...register("tipo")}
              >
                <option value="anuncio">Anúncio (classificado)</option>
                {souGestao && <option value="condominio">Aviso de condomínio</option>}
              </select>
            </div>
          )}

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

          {(editing ? editing.tipo === "anuncio" : tipoSelecionado === "anuncio") && (
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Preço (opcional)</label>
              <input
                inputMode="decimal"
                placeholder="0,00"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                {...register("preco")}
              />
            </div>
          )}

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
              {editing ? "Salvar alterações" : "Publicar"}
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

      {!bloqueadoSemPredio && (
        <>
          <Bloco
            titulo="Avisos do condomínio"
            itens={avisosCondominio}
            vazio="Nenhum aviso de condomínio no momento."
            souGestao={souGestao}
            userId={user?.id}
            onEditar={iniciarEdicao}
            onRemover={(id) => deleteMutation.mutate(id)}
          />
          <Bloco
            titulo="Classificados"
            itens={anuncios}
            vazio="Nenhum anúncio no momento."
            souGestao={souGestao}
            userId={user?.id}
            onEditar={iniciarEdicao}
            onRemover={(id) => deleteMutation.mutate(id)}
          />
        </>
      )}
    </AppShell>
  );
}
