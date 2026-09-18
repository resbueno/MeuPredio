export type RoleEnum = "morador" | "proprietario" | "sindico" | "zelador" | "administrador";
export type TipoVeiculoEnum = "carro" | "moto" | "outro";
export type CategoriaTicketEnum = "manutencao" | "duvida" | "solicitacao" | "outro";
export type PrioridadeTicketEnum = "baixa" | "media" | "alta";
export type StatusTicketEnum = "aberto" | "em_andamento" | "resolvido" | "cancelado";

export interface Usuario {
  id: number;
  email: string;
  full_name: string;
  role: RoleEnum;
  predio_id: number | null;
  unidade_ids: number[];
  is_active: boolean;
  consent_lgpd_accepted_at: string | null;
  last_login_at: string | null;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
  anonymized_at: string | null;
}

export interface UsuarioCreateInput {
  email: string;
  full_name: string;
  role: RoleEnum;
  unidade_ids?: number[];
  predio_id?: number | null;
  password: string;
}

export interface UsuarioUpdateInput {
  full_name?: string;
  role?: RoleEnum;
  unidade_ids?: number[];
  is_active?: boolean;
  password?: string;
}

export interface Unidade {
  id: number;
  predio_id: number;
  bloco: string;
  numero: string;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

export interface UnidadeInput {
  bloco: string;
  numero: string;
  predio_id?: number | null;
}

export interface Veiculo {
  id: number;
  unidade_id: number;
  placa: string;
  modelo: string;
  cor: string;
  tipo: TipoVeiculoEnum;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

export interface VeiculoInput {
  unidade_id: number;
  placa: string;
  modelo: string;
  cor: string;
  tipo: TipoVeiculoEnum;
}

export interface Predio {
  id: number;
  nome: string;
  cep: string;
  numero: string;
  complemento: string | null;
  logradouro: string | null;
  bairro: string | null;
  cidade: string | null;
  uf: string | null;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

export interface PredioCreateInput {
  nome: string;
  cep: string;
  numero: string;
  complemento?: string | null;
  unidades?: { bloco: string; numero: string }[];
}

export interface PredioIdentificado {
  id: number;
  nome: string;
  cidade: string | null;
  uf: string | null;
}

export interface PredioConvite {
  id: number;
  predio_id: number;
  token: string;
  ativo: boolean;
  expira_em: string | null;
  esta_valido: boolean;
}

export interface PredioConviteInfo {
  predio_nome: string;
  predio_id: number;
  unidades: { id: number; bloco: string; numero: string }[];
}

export interface CadastroViaConviteInput {
  email: string;
  password: string;
  full_name: string;
  role: "morador" | "proprietario";
  unidade_ids: number[];
}

export interface PredioIntegracaoOcrStatus {
  configurado: boolean;
}

export type StatusDespesaEnum = "pendente" | "pago" | "cancelado";
export type CriterioRateioEnum = "igual" | "fracao_ideal";

export interface RateioDespesaItem {
  id: number;
  despesa_lancamento_id: number;
  unidade_id: number;
  valor: string;
  criterio: CriterioRateioEnum;
  created_at: string;
}

export interface DespesaLancamento {
  id: number;
  predio_id: number;
  fornecedor_id: number | null;
  descricao: string;
  categoria: string;
  valor: string;
  data_vencimento: string;
  data_pagamento: string | null;
  status: StatusDespesaEnum;
  esta_atrasada: boolean;
  documento_url: string | null;
  comprovante_pagamento_url: string | null;
  observacoes: string | null;
  rateado_em: string | null;
  itens_rateio: RateioDespesaItem[];
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

export interface DespesaCreateInput {
  descricao: string;
  categoria: string;
  valor: string;
  data_vencimento: string;
  observacoes?: string | null;
  documento_url?: string | null;
  predio_id?: number | null;
}

export interface DespesaTransparencia {
  id: number;
  descricao: string;
  categoria: string;
  valor: string;
  data_vencimento: string;
  data_pagamento: string | null;
  status: StatusDespesaEnum;
  esta_atrasada: boolean;
  documento_url: string | null;
  comprovante_pagamento_url: string | null;
}

export interface TotalPorCategoria {
  categoria: string;
  total: string;
}

export interface Balancete {
  ano: number;
  mes: number | null;
  total_pago: string;
  total_pendente: string;
  total_cancelado: string;
  total_geral: string;
  por_categoria: TotalPorCategoria[];
}

export interface TicketComentario {
  id: number;
  ticket_id: number;
  created_by: number | null;
  mensagem: string;
  created_at: string;
}

export interface TicketAtendimento {
  id: number;
  predio_id: number;
  unidade_id: number | null;
  responsavel_id: number | null;
  created_by: number | null;
  titulo: string;
  descricao: string;
  categoria: CategoriaTicketEnum;
  prioridade: PrioridadeTicketEnum;
  status: StatusTicketEnum;
  prazo_sla: string;
  resolvido_em: string | null;
  esta_atrasado: boolean;
  comentarios: TicketComentario[];
  created_at: string;
  updated_at: string;
}

export interface TicketCreateInput {
  titulo: string;
  descricao: string;
  categoria: CategoriaTicketEnum;
  prioridade: PrioridadeTicketEnum;
  unidade_id?: number | null;
  predio_id?: number | null;
}

export interface TicketAtualizarInput {
  titulo?: string;
  descricao?: string;
  categoria?: CategoriaTicketEnum;
  prioridade?: PrioridadeTicketEnum;
}

export interface ExtracaoBoleto {
  documento_url: string;
  fornecedor_nome: string | null;
  fornecedor_documento: string | null;
  valor: string | null;
  data_vencimento: string | null;
  linha_digitavel: string | null;
  descricao_sugerida: string | null;
  categoria_sugerida: string | null;
}
