import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { useEffect, useRef, useState, type ChangeEvent } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { AppShell } from "../../components/layout/AppShell";
import { useAuth } from "../../auth/AuthContext";
import {
  anexarComprovante,
  cancelarDespesa,
  createDespesa,
  desfazerPagamento,
  extrairBoleto,
  listDespesas,
  registrarPagamento,
  updateDespesa,
} from "../../api/despesas";
import { baixarDocumento } from "../../api/documentos";
import {
  configurarIntegracaoOcr,
  obterIntegracaoOcr,
  removerIntegracaoOcr,
} from "../../api/predios";
import type {
  DespesaCreateInput,
  DespesaLancamento,
  ExtracaoBoleto,
  StatusDespesaEnum,
} from "../../api/types";

const despesaSchema = z.object({
  descricao: z.string().min(2, "Informe a descrição."),
  categoria: z.string().min(2, "Informe a categoria."),
  valor: z
    .string()
    .min(1, "Informe o valor.")
    .refine((v) => Number(v.replace(",", ".")) > 0, "Informe um valor maior que zero."),
  data_vencimento: z.string().min(1, "Informe o vencimento."),
  observacoes: z.string().optional(),
});

type DespesaFormValues = z.infer<typeof despesaSchema>;

const FORM_VAZIO: DespesaFormValues = {
  descricao: "",
  categoria: "",
  valor: "",
  data_vencimento: "",
  observacoes: "",
};

const STATUS_LABEL: Record<StatusDespesaEnum, string> = {
  pendente: "Pendente",
  pago: "Paga",
  cancelado: "Cancelada",
};

const STATUS_CLASSES: Record<StatusDespesaEnum, string> = {
  pendente: "bg-amber-100 text-amber-700",
  pago: "bg-emerald-100 text-emerald-700",
  cancelado: "bg-slate-200 text-slate-500",
};

function formatarValor(valor: string): string {
  const numero = Number(valor);
  return Number.isFinite(numero)
    ? numero.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
    : valor;
}

function observacoesSugeridas(extracao: ExtracaoBoleto): string {
  const partes: string[] = [];
  if (extracao.fornecedor_nome) partes.push(`Fornecedor: ${extracao.fornecedor_nome}`);
  if (extracao.fornecedor_documento) partes.push(`Documento: ${extracao.fornecedor_documento}`);
  if (extracao.linha_digitavel) partes.push(`Linha digitavel: ${extracao.linha_digitavel}`);
  return partes.join("\n");
}

function mensagemErroExtracao(erro: unknown): string {
  if (axios.isAxiosError(erro)) {
    if (erro.response?.status === 409) {
      return "Este prédio ainda não tem a integração com o Groq configurada (veja abaixo).";
    }
    if (erro.response?.status === 422) {
      return "Arquivo inválido - envie uma imagem (JPEG/PNG/WEBP) ou PDF de até 10MB.";
    }
    if (erro.response?.status === 502) {
      return "Não foi possível processar o documento agora (Groq indisponível ou limite de taxa atingido). Tente novamente em instantes, ou preencha manualmente.";
    }
  }
  return "Não foi possível extrair os dados do documento. Preencha manualmente, se preferir.";
}

function IntegracaoOcrPanel({ predioId }: { predioId: number }) {
  const queryClient = useQueryClient();
  const [chave, setChave] = useState("");

  const { data: integracao, isLoading } = useQuery({
    queryKey: ["integracao-ocr", predioId],
    queryFn: () => obterIntegracaoOcr(predioId),
  });

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ["integracao-ocr", predioId] });

  const salvarMutation = useMutation({
    mutationFn: () => configurarIntegracaoOcr(predioId, chave.trim()),
    onSuccess: () => {
      setChave("");
      invalidate();
    },
  });

  const removerMutation = useMutation({
    mutationFn: () => removerIntegracaoOcr(predioId),
    onSuccess: invalidate,
  });

  if (isLoading) {
    return null;
  }

  return (
    <div className="mb-6 rounded-2xl bg-white p-4 shadow-sm">
      <h2 className="text-sm font-semibold text-slate-700">Leitura automática de boletos (IA)</h2>
      {integracao?.configurado ? (
        <div className="mt-2 flex items-center justify-between">
          <p className="text-sm text-emerald-700">
            <span className="font-medium">Configurada.</span> Conta do Groq vinculada a este
            prédio.
          </p>
          <button
            type="button"
            onClick={() => removerMutation.mutate()}
            disabled={removerMutation.isPending}
            className="shrink-0 text-xs font-medium text-red-600 disabled:opacity-60"
          >
            Remover
          </button>
        </div>
      ) : (
        <div className="mt-2 space-y-2">
          <p className="text-xs text-slate-500">
            Cole aqui a chave de API do Groq de uma conta do próprio condomínio
            (console.groq.com) para poder extrair boletos automaticamente ao subir uma conta.
          </p>
          <div className="flex gap-2">
            <input
              type="password"
              value={chave}
              onChange={(event) => setChave(event.target.value)}
              placeholder="Chave de API do Groq"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <button
              type="button"
              onClick={() => salvarMutation.mutate()}
              disabled={salvarMutation.isPending || chave.trim().length < 10}
              className="shrink-0 rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
            >
              Salvar
            </button>
          </div>
          {salvarMutation.isError && (
            <p className="text-xs text-red-600">Não foi possível salvar a chave. Tente novamente.</p>
          )}
        </div>
      )}
    </div>
  );
}

export function DespesasPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const souAdministrador = user?.role === "administrador";
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [predioIdAdminInput, setPredioIdAdminInput] = useState("");
  const predioIdAdmin = predioIdAdminInput.trim() ? Number(predioIdAdminInput.trim()) : null;
  const predioIdEfetivo = souAdministrador ? predioIdAdmin : (user?.predio_id ?? null);

  const [documentoUrl, setDocumentoUrl] = useState<string | null>(null);
  const [avisoExtracao, setAvisoExtracao] = useState<string | null>(null);
  const [editing, setEditing] = useState<DespesaLancamento | null>(null);

  const { data: despesas, isLoading } = useQuery({
    queryKey: ["despesas", souAdministrador ? predioIdAdmin : "proprio"],
    queryFn: () => listDespesas(souAdministrador ? predioIdAdmin : undefined),
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<DespesaFormValues>({
    resolver: zodResolver(despesaSchema),
    defaultValues: FORM_VAZIO,
  });

  function limparFormulario(): void {
    reset(FORM_VAZIO);
    setDocumentoUrl(null);
    setAvisoExtracao(null);
    setEditing(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  useEffect(() => {
    if (!editing) {
      return;
    }
    reset({
      descricao: editing.descricao,
      categoria: editing.categoria,
      valor: editing.valor,
      data_vencimento: editing.data_vencimento,
      observacoes: editing.observacoes ?? "",
    });
    setDocumentoUrl(editing.documento_url);
    setAvisoExtracao(null);
  }, [editing, reset]);

  const invalidateDespesas = () => queryClient.invalidateQueries({ queryKey: ["despesas"] });

  const extrairMutation = useMutation({
    mutationFn: (arquivo: File) => extrairBoleto(arquivo, predioIdAdmin),
    onSuccess: (extracao) => {
      setAvisoExtracao(null);
      setDocumentoUrl(extracao.documento_url);
      reset({
        descricao: extracao.descricao_sugerida ?? "",
        categoria: extracao.categoria_sugerida ?? "",
        valor: extracao.valor ?? "",
        data_vencimento: extracao.data_vencimento ?? "",
        observacoes: observacoesSugeridas(extracao),
      });
    },
    onError: (erro) => setAvisoExtracao(mensagemErroExtracao(erro)),
  });

  const createMutation = useMutation({
    mutationFn: createDespesa,
    onSuccess: () => {
      invalidateDespesas();
      limparFormulario();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, input }: { id: number; input: Partial<DespesaCreateInput> }) =>
      updateDespesa(id, input),
    onSuccess: () => {
      invalidateDespesas();
      limparFormulario();
    },
  });

  const pagarMutation = useMutation({ mutationFn: registrarPagamento, onSuccess: invalidateDespesas });
  const cancelarMutation = useMutation({ mutationFn: cancelarDespesa, onSuccess: invalidateDespesas });
  const desfazerPagamentoMutation = useMutation({
    mutationFn: desfazerPagamento,
    onSuccess: invalidateDespesas,
  });
  const anexarComprovanteMutation = useMutation({
    mutationFn: ({ id, arquivo }: { id: number; arquivo: File }) => anexarComprovante(id, arquivo),
    onSuccess: invalidateDespesas,
  });

  function onSelecionarComprovante(despesaId: number, event: ChangeEvent<HTMLInputElement>): void {
    const arquivo = event.target.files?.[0];
    event.target.value = "";
    if (!arquivo) return;
    anexarComprovanteMutation.mutate({ id: despesaId, arquivo });
  }

  async function verComprovante(url: string): Promise<void> {
    const blobUrl = await baixarDocumento(url);
    window.open(blobUrl, "_blank", "noopener,noreferrer");
  }

  function onSelecionarArquivo(event: ChangeEvent<HTMLInputElement>): void {
    const arquivo = event.target.files?.[0];
    if (!arquivo) {
      return;
    }
    if (souAdministrador && !predioIdAdmin) {
      setAvisoExtracao("Informe o ID do prédio antes de enviar um documento.");
      event.target.value = "";
      return;
    }
    setAvisoExtracao(null);
    extrairMutation.mutate(arquivo);
  }

  function onSubmit(values: DespesaFormValues): void {
    if (souAdministrador && !predioIdAdmin) {
      return;
    }
    const campos = {
      descricao: values.descricao,
      categoria: values.categoria,
      valor: values.valor.replace(",", "."),
      data_vencimento: values.data_vencimento,
      observacoes: values.observacoes || null,
      documento_url: documentoUrl,
    };
    if (editing) {
      updateMutation.mutate({ id: editing.id, input: campos });
      return;
    }
    createMutation.mutate({ ...campos, predio_id: souAdministrador ? predioIdAdmin : undefined });
  }

  const bloqueadoSemPredio = souAdministrador && !predioIdAdmin;

  return (
    <AppShell>
      <h1 className="mb-4 text-xl font-bold text-slate-800">Contas / Despesas</h1>

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
          <p className="mt-1 text-xs text-slate-400">
            Administrador não pertence a um prédio - informe qual prédio está gerenciando.
          </p>
        </div>
      )}

      {predioIdEfetivo != null && <IntegracaoOcrPanel predioId={predioIdEfetivo} />}

      <div className="mb-6 space-y-3 rounded-2xl bg-white p-4 shadow-sm">
        <h2 className="text-sm font-semibold text-slate-700">
          {editing ? `Editar conta #${editing.id}` : "Subir uma conta"}
        </h2>

        <div>
          <label className="mb-1 block text-xs font-medium text-slate-600">
            {editing
              ? "Trocar foto ou PDF do boleto (opcional)"
              : "Foto ou PDF do boleto (opcional - a IA preenche o formulário abaixo)"}
          </label>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp,application/pdf"
            onChange={onSelecionarArquivo}
            disabled={bloqueadoSemPredio || extrairMutation.isPending}
            className="w-full text-sm text-slate-600 file:mr-3 file:rounded-lg file:border-0 file:bg-brand-50 file:px-3 file:py-2 file:text-sm file:font-semibold file:text-brand-700 hover:file:bg-brand-100"
          />
          {extrairMutation.isPending && (
            <p className="mt-1 text-xs text-slate-500">Lendo o documento com IA...</p>
          )}
          {avisoExtracao && <p className="mt-1 text-xs text-amber-600">{avisoExtracao}</p>}
          {documentoUrl && !extrairMutation.isPending && (
            <p className="mt-1 text-xs text-emerald-600">
              {editing
                ? "Documento anexado - revise os campos abaixo antes de salvar."
                : "Dados extraídos - revise os campos abaixo antes de salvar."}
            </p>
          )}
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-3" noValidate>
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">Descrição</label>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              {...register("descricao")}
            />
            {errors.descricao && (
              <p className="mt-1 text-xs text-red-600">{errors.descricao.message}</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Categoria</label>
              <input
                list="categorias-despesa"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                {...register("categoria")}
              />
              <datalist id="categorias-despesa">
                <option value="agua" />
                <option value="luz" />
                <option value="gas" />
                <option value="condominio" />
                <option value="manutencao" />
                <option value="outros" />
              </datalist>
              {errors.categoria && (
                <p className="mt-1 text-xs text-red-600">{errors.categoria.message}</p>
              )}
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Valor (R$)</label>
              <input
                inputMode="decimal"
                placeholder="0,00"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                {...register("valor")}
              />
              {errors.valor && <p className="mt-1 text-xs text-red-600">{errors.valor.message}</p>}
            </div>
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">Vencimento</label>
            <input
              type="date"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              {...register("data_vencimento")}
            />
            {errors.data_vencimento && (
              <p className="mt-1 text-xs text-red-600">{errors.data_vencimento.message}</p>
            )}
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">
              Observações (opcional)
            </label>
            <textarea
              rows={2}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              {...register("observacoes")}
            />
          </div>

          {(createMutation.isError || updateMutation.isError) && (
            <p className="text-sm text-red-600">
              Não foi possível salvar a conta. Verifique os dados e tente novamente.
            </p>
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
              {editing ? "Salvar alterações" : "Salvar conta"}
            </button>
            <button
              type="button"
              onClick={limparFormulario}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600"
            >
              {editing ? "Cancelar edição" : "Limpar"}
            </button>
          </div>
        </form>
      </div>

      {isLoading && <p className="text-sm text-slate-500">Carregando...</p>}

      <ul className="space-y-2">
        {despesas?.map((despesa: DespesaLancamento) => (
          <li key={despesa.id} className="rounded-xl bg-white p-3 shadow-sm">
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="font-medium text-slate-800">{despesa.descricao}</p>
                <p className="text-xs text-slate-500">
                  {despesa.categoria} - Vencimento{" "}
                  {new Date(`${despesa.data_vencimento}T00:00:00`).toLocaleDateString("pt-BR")}
                </p>
              </div>
              <span
                className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_CLASSES[despesa.status]}`}
              >
                {STATUS_LABEL[despesa.status]}
                {despesa.esta_atrasada ? " - atrasada" : ""}
              </span>
            </div>
            <div className="mt-2 flex items-center justify-between">
              <p className="text-sm font-semibold text-slate-700">{formatarValor(despesa.valor)}</p>
              {despesa.status === "pendente" && (
                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => setEditing(despesa)}
                    className="text-xs font-medium text-brand-600"
                  >
                    Editar
                  </button>
                  <button
                    type="button"
                    onClick={() => pagarMutation.mutate(despesa.id)}
                    className="text-xs font-medium text-emerald-600"
                  >
                    Marcar como paga
                  </button>
                  <button
                    type="button"
                    onClick={() => cancelarMutation.mutate(despesa.id)}
                    className="text-xs font-medium text-red-600"
                  >
                    Cancelar
                  </button>
                </div>
              )}
              {despesa.status === "pago" && (
                <button
                  type="button"
                  onClick={() => desfazerPagamentoMutation.mutate(despesa.id)}
                  disabled={desfazerPagamentoMutation.isPending}
                  className="text-xs font-medium text-amber-600 disabled:opacity-60"
                >
                  Desfazer pagamento
                </button>
              )}
            </div>
            {despesa.status === "pago" && (
              <div className="mt-2 flex items-center justify-between border-t border-slate-100 pt-2">
                {despesa.comprovante_pagamento_url ? (
                  <button
                    type="button"
                    onClick={() => verComprovante(despesa.comprovante_pagamento_url!)}
                    className="text-xs font-medium text-brand-600"
                  >
                    Ver comprovante
                  </button>
                ) : (
                  <span className="text-xs text-slate-400">Sem comprovante anexado</span>
                )}
                <label className="text-xs font-medium text-brand-600 hover:cursor-pointer">
                  {despesa.comprovante_pagamento_url ? "Trocar comprovante" : "Anexar comprovante"}
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/webp,application/pdf"
                    className="hidden"
                    disabled={anexarComprovanteMutation.isPending}
                    onChange={(event) => onSelecionarComprovante(despesa.id, event)}
                  />
                </label>
              </div>
            )}
          </li>
        ))}
        {despesas?.length === 0 && (
          <li className="rounded-xl bg-white p-4 text-center text-sm text-slate-500 shadow-sm">
            Nenhuma conta cadastrada.
          </li>
        )}
      </ul>
    </AppShell>
  );
}
