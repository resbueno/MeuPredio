import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { AppShell } from "../../components/layout/AppShell";
import { useAuth } from "../../auth/AuthContext";
import { temPapel } from "../../auth/roles";
import {
  createFuncionario,
  createPrestador,
  deleteFuncionario,
  deletePrestador,
  lancarCustoPrestador,
  listFuncionarios,
  listLancamentosPrestador,
  listPrestadores,
  updateFuncionario,
  updatePrestador,
} from "../../api/equipe";
import type { CriterioRateioEnum, Funcionario, PrestadorServico } from "../../api/types";

const CRITERIO_LABEL: Record<CriterioRateioEnum, string> = {
  igual: "divisão igual",
  fracao_ideal: "fração ideal",
};

function formatarValor(valor: string | null): string {
  if (valor == null) return "-";
  const numero = Number(valor);
  return Number.isFinite(numero)
    ? numero.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
    : valor;
}

function formatarData(data: string): string {
  return new Date(`${data}T00:00:00`).toLocaleDateString("pt-BR");
}

const campo = "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm";
const rotulo = "mb-1 block text-xs font-medium text-slate-600";
const valorPositivoOuVazio = (v?: string) => !v || (Number(v.replace(",", ".")) >= 0 && !Number.isNaN(Number(v.replace(",", "."))));

// ---------------------------------------------------------------- Funcionários

const funcionarioSchema = z.object({
  nome_completo: z.string().min(2, "Informe o nome completo."),
  cargo: z.string().min(2, "Informe o cargo."),
  cpf: z.string().optional(),
  telefone: z.string().optional(),
  email: z.string().email("E-mail inválido.").optional().or(z.literal("")),
  data_admissao: z.string().optional(),
  salario: z.string().optional().refine(valorPositivoOuVazio, "Valor inválido."),
  observacoes: z.string().optional(),
});
type FuncionarioForm = z.infer<typeof funcionarioSchema>;
const FUNCIONARIO_VAZIO: FuncionarioForm = {
  nome_completo: "", cargo: "", cpf: "", telefone: "", email: "", data_admissao: "", salario: "", observacoes: "",
};

function FuncionariosSecao() {
  const queryClient = useQueryClient();
  const [editando, setEditando] = useState<Funcionario | null>(null);
  const [mostrarInativos, setMostrarInativos] = useState(false);

  const { data: funcionarios, isLoading } = useQuery({
    queryKey: ["funcionarios", mostrarInativos],
    queryFn: () => listFuncionarios(mostrarInativos),
  });

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<FuncionarioForm>({
    resolver: zodResolver(funcionarioSchema),
    defaultValues: FUNCIONARIO_VAZIO,
  });

  useEffect(() => {
    reset(
      editando
        ? {
            nome_completo: editando.nome_completo,
            cargo: editando.cargo,
            cpf: editando.cpf ?? "",
            telefone: editando.telefone ?? "",
            email: editando.email ?? "",
            data_admissao: editando.data_admissao ?? "",
            salario: editando.salario ?? "",
            observacoes: editando.observacoes ?? "",
          }
        : FUNCIONARIO_VAZIO
    );
  }, [editando, reset]);

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["funcionarios"] });
  const aoSalvar = () => { invalidate(); setEditando(null); reset(FUNCIONARIO_VAZIO); };

  const criar = useMutation({ mutationFn: createFuncionario, onSuccess: aoSalvar });
  const atualizar = useMutation({
    mutationFn: ({ id, input }: { id: number; input: Parameters<typeof updateFuncionario>[1] }) => updateFuncionario(id, input),
    onSuccess: aoSalvar,
  });
  const alternarAtivo = useMutation({
    mutationFn: (f: Funcionario) => updateFuncionario(f.id, { ativo: !f.ativo }),
    onSuccess: invalidate,
  });
  const remover = useMutation({ mutationFn: deleteFuncionario, onSuccess: invalidate });

  function onSubmit(v: FuncionarioForm): void {
    const input = {
      nome_completo: v.nome_completo,
      cargo: v.cargo,
      cpf: v.cpf?.trim() || null,
      telefone: v.telefone?.trim() || null,
      email: v.email?.trim() || null,
      data_admissao: v.data_admissao || null,
      salario: v.salario?.trim() ? v.salario.replace(",", ".") : null,
      observacoes: v.observacoes?.trim() || null,
    };
    if (editando) atualizar.mutate({ id: editando.id, input });
    else criar.mutate(input);
  }

  const erro = criar.isError || atualizar.isError;

  return (
    <>
      <form onSubmit={handleSubmit(onSubmit)} noValidate className="mb-6 space-y-3 rounded-2xl bg-white p-4 shadow-sm">
        <h2 className="text-sm font-semibold text-slate-700">
          {editando ? `Editar ${editando.nome_completo}` : "Novo funcionário"}
        </h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div>
            <label className={rotulo}>Nome completo</label>
            <input className={campo} {...register("nome_completo")} />
            {errors.nome_completo && <p className="mt-1 text-xs text-red-600">{errors.nome_completo.message}</p>}
          </div>
          <div>
            <label className={rotulo}>Cargo</label>
            <input className={campo} placeholder="Ex.: Porteiro" {...register("cargo")} />
            {errors.cargo && <p className="mt-1 text-xs text-red-600">{errors.cargo.message}</p>}
          </div>
          <div>
            <label className={rotulo}>CPF (opcional)</label>
            <input className={campo} inputMode="numeric" {...register("cpf")} />
          </div>
          <div>
            <label className={rotulo}>Telefone (opcional)</label>
            <input className={campo} {...register("telefone")} />
          </div>
          <div>
            <label className={rotulo}>E-mail (opcional)</label>
            <input className={campo} {...register("email")} />
            {errors.email && <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>}
          </div>
          <div>
            <label className={rotulo}>Admissão (opcional)</label>
            <input type="date" className={campo} {...register("data_admissao")} />
          </div>
          <div>
            <label className={rotulo}>Salário (R$, opcional)</label>
            <input className={campo} inputMode="decimal" placeholder="0,00" {...register("salario")} />
            {errors.salario && <p className="mt-1 text-xs text-red-600">{errors.salario.message}</p>}
          </div>
        </div>
        <div>
          <label className={rotulo}>Observações (opcional)</label>
          <textarea rows={2} className={campo} {...register("observacoes")} />
        </div>
        {erro && <p className="text-sm text-red-600">Não foi possível salvar. Verifique os dados.</p>}
        <div className="flex gap-2">
          <button type="submit" disabled={isSubmitting} className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60">
            {editando ? "Salvar" : "Cadastrar"}
          </button>
          {editando && (
            <button type="button" onClick={() => setEditando(null)} className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600">
              Cancelar
            </button>
          )}
        </div>
      </form>

      <label className="mb-3 flex items-center gap-2 text-sm text-slate-600">
        <input type="checkbox" checked={mostrarInativos} onChange={(e) => setMostrarInativos(e.target.checked)} />
        Mostrar desligados
      </label>
      {isLoading && <p className="text-sm text-slate-500">Carregando...</p>}
      <ul className="space-y-2">
        {funcionarios?.map((f) => (
          <li key={f.id} className="rounded-xl bg-white p-3 shadow-sm">
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="font-medium text-slate-800">{f.nome_completo}</p>
                <p className="text-xs text-slate-500">
                  {f.cargo}
                  {f.data_admissao ? ` - desde ${formatarData(f.data_admissao)}` : ""}
                </p>
              </div>
              <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${f.ativo ? "bg-emerald-100 text-emerald-700" : "bg-slate-200 text-slate-500"}`}>
                {f.ativo ? "Ativo" : "Desligado"}
              </span>
            </div>
            <p className="mt-1 text-xs text-slate-500">
              {[f.telefone, f.email, f.cpf ? `CPF ${f.cpf}` : null].filter(Boolean).join(" - ")}
            </p>
            {f.salario && <p className="mt-1 text-sm font-semibold text-slate-700">Salário: {formatarValor(f.salario)}</p>}
            <div className="mt-2 flex gap-3 border-t border-slate-100 pt-2">
              <button type="button" onClick={() => setEditando(f)} className="text-xs font-medium text-brand-600">Editar</button>
              <button type="button" onClick={() => alternarAtivo.mutate(f)} className="text-xs font-medium text-amber-600">
                {f.ativo ? "Marcar como desligado" : "Reativar"}
              </button>
              <button type="button" onClick={() => remover.mutate(f.id)} className="text-xs font-medium text-red-600">Remover</button>
            </div>
          </li>
        ))}
        {funcionarios?.length === 0 && (
          <li className="rounded-xl bg-white p-4 text-center text-sm text-slate-500 shadow-sm">Nenhum funcionário cadastrado.</li>
        )}
      </ul>
    </>
  );
}

// ------------------------------------------------------------------ Prestadores

const prestadorSchema = z.object({
  nome: z.string().min(2, "Informe o nome."),
  tipo_servico: z.string().min(2, "Informe o tipo de serviço."),
  razao_social: z.string().optional(),
  cnpj: z.string().optional(),
  telefone: z.string().optional(),
  email: z.string().email("E-mail inválido.").optional().or(z.literal("")),
  custo_mensal: z.string().min(1, "Informe o custo.").refine((v) => Number(v.replace(",", ".")) >= 0, "Valor inválido."),
  incluir_no_rateio: z.boolean(),
  criterio_rateio: z.enum(["igual", "fracao_ideal"]),
  observacoes: z.string().optional(),
});
type PrestadorForm = z.infer<typeof prestadorSchema>;
const PRESTADOR_VAZIO: PrestadorForm = {
  nome: "", tipo_servico: "", razao_social: "", cnpj: "", telefone: "", email: "",
  custo_mensal: "", incluir_no_rateio: false, criterio_rateio: "igual", observacoes: "",
};

function LancarCusto({ prestador, podeLancar }: { prestador: PrestadorServico; podeLancar: boolean }) {
  const queryClient = useQueryClient();
  const [data, setData] = useState(new Date().toISOString().slice(0, 10));
  const [historico, setHistorico] = useState(false);

  const { data: lancamentos } = useQuery({
    queryKey: ["prestador-lancamentos", prestador.id],
    queryFn: () => listLancamentosPrestador(prestador.id),
    enabled: historico,
  });

  const lancar = useMutation({
    mutationFn: () => lancarCustoPrestador(prestador.id, { data_vencimento: data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["prestador-lancamentos", prestador.id] });
      queryClient.invalidateQueries({ queryKey: ["despesas"] });
    },
  });

  const mensagemErro =
    axios.isAxiosError(lancar.error) && lancar.error.response?.status === 409
      ? (lancar.error.response.data as { detail?: string }).detail ?? "Já lançado neste mês."
      : "Não foi possível lançar o custo.";

  return (
    <div className="mt-2 border-t border-slate-100 pt-2">
      {podeLancar && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-slate-500">Vencimento</span>
          <input type="date" value={data} onChange={(e) => setData(e.target.value)} className="rounded-lg border border-slate-300 px-2 py-1 text-xs" />
          <button type="button" onClick={() => lancar.mutate()} disabled={lancar.isPending || !data} className="rounded-lg bg-brand-600 px-3 py-1 text-xs font-semibold text-white disabled:opacity-60">
            Lançar custo do mês
          </button>
        </div>
      )}
      {lancar.isSuccess && (
        <p className="mt-1 text-xs text-emerald-600">
          Custo lançado em Contas{prestador.incluir_no_rateio ? " e rateado entre as unidades" : " (sem cobrança às unidades)"}.
        </p>
      )}
      {lancar.isError && <p className="mt-1 text-xs text-red-600">{mensagemErro}</p>}
      <button type="button" onClick={() => setHistorico((v) => !v)} className="mt-2 text-xs font-medium text-brand-600">
        {historico ? "Ocultar lançamentos" : "Ver lançamentos"}
      </button>
      {historico && (
        <ul className="mt-1 space-y-1">
          {lancamentos?.map((l) => (
            <li key={l.id} className="flex justify-between text-xs text-slate-600">
              <span>{formatarData(l.data_vencimento)} - {l.status}{l.rateado_em ? " - rateado" : ""}</span>
              <span className="font-medium">{formatarValor(l.valor)}</span>
            </li>
          ))}
          {lancamentos?.length === 0 && <li className="text-xs text-slate-400">Nenhum custo lançado ainda.</li>}
        </ul>
      )}
    </div>
  );
}

function PrestadoresSecao({ podeLancar }: { podeLancar: boolean }) {
  const queryClient = useQueryClient();
  const [editando, setEditando] = useState<PrestadorServico | null>(null);
  const [mostrarInativos, setMostrarInativos] = useState(false);

  const { data: prestadores, isLoading } = useQuery({
    queryKey: ["prestadores", mostrarInativos],
    queryFn: () => listPrestadores(mostrarInativos),
  });

  const { register, handleSubmit, reset, watch, formState: { errors, isSubmitting } } = useForm<PrestadorForm>({
    resolver: zodResolver(prestadorSchema),
    defaultValues: PRESTADOR_VAZIO,
  });
  const incluirNoRateio = watch("incluir_no_rateio");

  useEffect(() => {
    reset(
      editando
        ? {
            nome: editando.nome,
            tipo_servico: editando.tipo_servico,
            razao_social: editando.razao_social ?? "",
            cnpj: editando.cnpj ?? "",
            telefone: editando.telefone ?? "",
            email: editando.email ?? "",
            custo_mensal: editando.custo_mensal,
            incluir_no_rateio: editando.incluir_no_rateio,
            criterio_rateio: editando.criterio_rateio,
            observacoes: editando.observacoes ?? "",
          }
        : PRESTADOR_VAZIO
    );
  }, [editando, reset]);

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["prestadores"] });
  const aoSalvar = () => { invalidate(); setEditando(null); reset(PRESTADOR_VAZIO); };

  const criar = useMutation({ mutationFn: createPrestador, onSuccess: aoSalvar });
  const atualizar = useMutation({
    mutationFn: ({ id, input }: { id: number; input: Parameters<typeof updatePrestador>[1] }) => updatePrestador(id, input),
    onSuccess: aoSalvar,
  });
  const alternarAtivo = useMutation({
    mutationFn: (p: PrestadorServico) => updatePrestador(p.id, { ativo: !p.ativo }),
    onSuccess: invalidate,
  });
  const remover = useMutation({ mutationFn: deletePrestador, onSuccess: invalidate });

  function onSubmit(v: PrestadorForm): void {
    const input = {
      nome: v.nome,
      tipo_servico: v.tipo_servico,
      razao_social: v.razao_social?.trim() || null,
      cnpj: v.cnpj?.trim() || null,
      telefone: v.telefone?.trim() || null,
      email: v.email?.trim() || null,
      custo_mensal: v.custo_mensal.replace(",", "."),
      incluir_no_rateio: v.incluir_no_rateio,
      criterio_rateio: v.criterio_rateio,
      observacoes: v.observacoes?.trim() || null,
    };
    if (editando) atualizar.mutate({ id: editando.id, input });
    else criar.mutate(input);
  }

  return (
    <>
      <form onSubmit={handleSubmit(onSubmit)} noValidate className="mb-6 space-y-3 rounded-2xl bg-white p-4 shadow-sm">
        <h2 className="text-sm font-semibold text-slate-700">
          {editando ? `Editar ${editando.nome}` : "Novo prestador de serviço"}
        </h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div>
            <label className={rotulo}>Nome / nome fantasia</label>
            <input className={campo} {...register("nome")} />
            {errors.nome && <p className="mt-1 text-xs text-red-600">{errors.nome.message}</p>}
          </div>
          <div>
            <label className={rotulo}>Tipo de serviço</label>
            <input className={campo} placeholder="Ex.: Limpeza, Elevadores" {...register("tipo_servico")} />
            {errors.tipo_servico && <p className="mt-1 text-xs text-red-600">{errors.tipo_servico.message}</p>}
          </div>
          <div>
            <label className={rotulo}>Razão social (opcional)</label>
            <input className={campo} {...register("razao_social")} />
          </div>
          <div>
            <label className={rotulo}>CNPJ (opcional)</label>
            <input className={campo} inputMode="numeric" {...register("cnpj")} />
          </div>
          <div>
            <label className={rotulo}>Telefone (opcional)</label>
            <input className={campo} {...register("telefone")} />
          </div>
          <div>
            <label className={rotulo}>E-mail (opcional)</label>
            <input className={campo} {...register("email")} />
            {errors.email && <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>}
          </div>
          <div>
            <label className={rotulo}>Custo mensal (R$)</label>
            <input className={campo} inputMode="decimal" placeholder="0,00" {...register("custo_mensal")} />
            {errors.custo_mensal && <p className="mt-1 text-xs text-red-600">{errors.custo_mensal.message}</p>}
          </div>
        </div>

        <div className="rounded-lg bg-slate-50 p-3">
          <label className="flex items-center gap-2 text-sm font-medium text-slate-700">
            <input type="checkbox" {...register("incluir_no_rateio")} />
            Incluir este custo no rateio entre as unidades
          </label>
          {incluirNoRateio && (
            <div className="mt-2">
              <label className={rotulo}>Critério do rateio</label>
              <select className={campo} {...register("criterio_rateio")}>
                <option value="igual">Divisão igual entre as unidades</option>
                <option value="fracao_ideal">Por fração ideal</option>
              </select>
            </div>
          )}
          <p className="mt-2 text-xs text-slate-500">
            Marcado: ao lançar o custo do mês, ele é dividido entre as unidades. Desmarcado: vira só uma
            despesa do condomínio, sem cobrança por unidade.
          </p>
        </div>

        <div>
          <label className={rotulo}>Observações (opcional)</label>
          <textarea rows={2} className={campo} {...register("observacoes")} />
        </div>
        {(criar.isError || atualizar.isError) && (
          <p className="text-sm text-red-600">Não foi possível salvar. Verifique os dados.</p>
        )}
        <div className="flex gap-2">
          <button type="submit" disabled={isSubmitting} className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60">
            {editando ? "Salvar" : "Cadastrar"}
          </button>
          {editando && (
            <button type="button" onClick={() => setEditando(null)} className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600">
              Cancelar
            </button>
          )}
        </div>
      </form>

      <label className="mb-3 flex items-center gap-2 text-sm text-slate-600">
        <input type="checkbox" checked={mostrarInativos} onChange={(e) => setMostrarInativos(e.target.checked)} />
        Mostrar inativos
      </label>
      {isLoading && <p className="text-sm text-slate-500">Carregando...</p>}
      <ul className="space-y-2">
        {prestadores?.map((p) => (
          <li key={p.id} className="rounded-xl bg-white p-3 shadow-sm">
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="font-medium text-slate-800">{p.nome}</p>
                <p className="text-xs text-slate-500">
                  {p.tipo_servico}
                  {p.razao_social ? ` - ${p.razao_social}` : ""}
                </p>
                <p className="text-xs text-slate-500">
                  {[p.telefone, p.email, p.cnpj ? `CNPJ ${p.cnpj}` : null].filter(Boolean).join(" - ")}
                </p>
              </div>
              <div className="flex shrink-0 flex-col items-end gap-1">
                <span className="text-sm font-semibold text-slate-800">{formatarValor(p.custo_mensal)}/mês</span>
                <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${p.incluir_no_rateio ? "bg-brand-100 text-brand-700" : "bg-slate-100 text-slate-500"}`}>
                  {p.incluir_no_rateio ? `No rateio (${CRITERIO_LABEL[p.criterio_rateio]})` : "Fora do rateio"}
                </span>
                {!p.ativo && <span className="rounded-full bg-slate-200 px-2 py-0.5 text-xs font-medium text-slate-500">Inativo</span>}
              </div>
            </div>
            {p.ativo && <LancarCusto prestador={p} podeLancar={podeLancar} />}
            <div className="mt-2 flex gap-3 border-t border-slate-100 pt-2">
              <button type="button" onClick={() => setEditando(p)} className="text-xs font-medium text-brand-600">Editar</button>
              <button type="button" onClick={() => alternarAtivo.mutate(p)} className="text-xs font-medium text-amber-600">
                {p.ativo ? "Desativar" : "Reativar"}
              </button>
              <button type="button" onClick={() => remover.mutate(p.id)} className="text-xs font-medium text-red-600">Remover</button>
            </div>
          </li>
        ))}
        {prestadores?.length === 0 && (
          <li className="rounded-xl bg-white p-4 text-center text-sm text-slate-500 shadow-sm">Nenhum prestador cadastrado.</li>
        )}
      </ul>
    </>
  );
}

// ------------------------------------------------------------------------ Página

export function EquipePage() {
  const { user } = useAuth();
  const [aba, setAba] = useState<"funcionarios" | "prestadores">("funcionarios");
  const souSindico = temPapel(user, "sindico");

  return (
    <AppShell>
      <h1 className="mb-4 text-xl font-bold text-slate-800">Equipe e Serviços</h1>
      <div className="mb-4 flex gap-1 rounded-xl bg-slate-100 p-1">
        {(["funcionarios", "prestadores"] as const).map((id) => (
          <button
            key={id}
            type="button"
            onClick={() => setAba(id)}
            className={`flex-1 rounded-lg px-3 py-2 text-sm font-medium ${aba === id ? "bg-white text-brand-600 shadow-sm" : "text-slate-600"}`}
          >
            {id === "funcionarios" ? "Funcionários" : "Prestadores de serviço"}
          </button>
        ))}
      </div>
      {aba === "funcionarios" ? <FuncionariosSecao /> : <PrestadoresSecao podeLancar={souSindico} />}
    </AppShell>
  );
}
