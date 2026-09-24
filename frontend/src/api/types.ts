export type RoleEnum = "morador" | "proprietario" | "sindico" | "zelador" | "administrador";
export type TipoVeiculoEnum = "carro" | "moto" | "outro";
export type CategoriaTicketEnum = "manutencao" | "duvida" | "solicitacao" | "outro";
export type PrioridadeTicketEnum = "baixa" | "media" | "alta";
export type StatusTicketEnum = "aberto" | "em_andamento" | "resolvido" | "cancelado";
export type ModuloEnum =
  | "veiculos"
  | "financeiro"
  | "avisos"
  | "ocorrencias"
  | "chamados"
  | "reunioes"
  | "entregas"
  | "visitantes"
  | "reservas"
  | "equipe";

export const TODOS_MODULOS: { value: ModuloEnum; label: string }[] = [
  { value: "financeiro", label: "Financeiro (contas e transparência)" },
  { value: "veiculos", label: "Veículos" },
  { value: "avisos", label: "Avisos (mural e diretos)" },
  { value: "ocorrencias", label: "Ocorrências" },
  { value: "chamados", label: "Chamados" },
  { value: "reunioes", label: "Reuniões" },
  { value: "entregas", label: "Entregas" },
  { value: "visitantes", label: "Visitantes" },
  { value: "reservas", label: "Áreas comuns e reservas" },
  { value: "equipe", label: "Equipe e prestadores de serviço" },
];

export interface Usuario {
  id: number;
  email: string;
  full_name: string;
  role: RoleEnum;
  predio_id: number | null;
  unidade_ids: number[];
  papeis_extra: RoleEnum[];
  is_active: boolean;
  consent_lgpd_accepted_at: string | null;
  last_login_at: string | null;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
  anonymized_at: string | null;
  modulos_habilitados: ModuloEnum[];
}

export interface UsuarioCreateInput {
  email: string;
  full_name: string;
  role: RoleEnum;
  unidade_ids?: number[];
  papeis_extra?: RoleEnum[];
  predio_id?: number | null;
  password: string;
}

export interface UsuarioUpdateInput {
  full_name?: string;
  role?: RoleEnum;
  unidade_ids?: number[];
  papeis_extra?: RoleEnum[];
  is_active?: boolean;
  password?: string;
}

export interface Unidade {
  id: number;
  predio_id: number;
  bloco: string;
  numero: string;
  vaga: string | null;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

export interface UnidadeInput {
  bloco: string;
  numero: string;
  vaga?: string | null;
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
  modulos_habilitados: ModuloEnum[];
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
  modulos_habilitados?: ModuloEnum[];
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
  unidade_id: number | null;
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
  unidade_id: number | null;
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

export interface BalanceteMensal {
  ano: number;
  mes: number;
  total_pago: string;
  total_pendente: string;
  total_geral: string;
}

export interface PreviaUnidadeItem {
  despesa_id: number;
  descricao: string;
  categoria: string;
  tipo: "rateio" | "multa";
  valor: string;
  status: StatusDespesaEnum;
  data_vencimento: string;
}

export interface PreviaUnidade {
  unidade_id: number;
  ano: number;
  mes: number | null;
  total_rateio: string;
  total_multas: string;
  total_geral: string;
  itens: PreviaUnidadeItem[];
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

export type TipoAvisoMuralEnum = "condominio" | "anuncio";
export type DestinatarioAvisoEnum = "morador" | "proprietario" | "ambos";
export type TipoAvisoDiretoEnum = "aviso" | "advertencia" | "multa";

export interface AvisoMural {
  id: number;
  predio_id: number;
  tipo: TipoAvisoMuralEnum;
  titulo: string;
  descricao: string;
  preco: string | null;
  created_by: number | null;
  created_at: string;
  updated_at: string;
}

export interface AvisoMuralCreateInput {
  tipo: TipoAvisoMuralEnum;
  titulo: string;
  descricao: string;
  preco?: string | null;
  predio_id?: number | null;
}

export interface AvisoMuralAtualizarInput {
  titulo?: string;
  descricao?: string;
  preco?: string | null;
}

export interface AvisoDireto {
  id: number;
  predio_id: number;
  unidade_id: number;
  destinatario: DestinatarioAvisoEnum;
  tipo: TipoAvisoDiretoEnum;
  titulo: string;
  mensagem: string;
  valor: string | null;
  despesa_lancamento_id: number | null;
  lida_em: string | null;
  resposta: string | null;
  respondido_por: number | null;
  respondido_em: string | null;
  created_by: number | null;
  created_at: string;
  updated_at: string;
}

export interface AvisoDiretoCreateInput {
  unidade_id: number;
  destinatario: DestinatarioAvisoEnum;
  tipo: TipoAvisoDiretoEnum;
  titulo: string;
  mensagem: string;
  valor?: string | null;
  data_vencimento?: string | null;
  predio_id?: number | null;
}

export interface Ocorrencia {
  id: number;
  predio_id: number;
  unidade_id: number | null;
  titulo: string;
  descricao: string;
  editado_em: string | null;
  editado_por: number | null;
  created_by: number | null;
  created_at: string;
  updated_at: string;
}

export interface OcorrenciaCreateInput {
  titulo: string;
  descricao: string;
  unidade_id?: number | null;
  predio_id?: number | null;
}

export interface OcorrenciaAtualizarInput {
  titulo?: string;
  descricao?: string;
}

export type TipoReuniaoEnum = "ordinaria" | "extraordinaria";
export type StatusReuniaoEnum = "convocada" | "realizada" | "cancelada";

export interface ReuniaoPresenca {
  id: number;
  reuniao_id: number;
  unidade_id: number;
  created_by: number | null;
  created_at: string;
}

export interface Reuniao {
  id: number;
  predio_id: number;
  tipo: TipoReuniaoEnum;
  status: StatusReuniaoEnum;
  titulo: string;
  data_hora: string;
  local: string;
  pauta: string;
  ata: string | null;
  ata_registrada_em: string | null;
  ata_registrada_por: number | null;
  created_by: number | null;
  presencas: ReuniaoPresenca[];
  created_at: string;
  updated_at: string;
}

export interface ReuniaoCreateInput {
  tipo: TipoReuniaoEnum;
  titulo: string;
  data_hora: string;
  local: string;
  pauta: string;
  predio_id?: number | null;
}

export interface ReuniaoAtualizarInput {
  tipo?: TipoReuniaoEnum;
  titulo?: string;
  data_hora?: string;
  local?: string;
  pauta?: string;
}

export type TipoNotificacaoEnum = "aviso_geral" | "aviso_direto" | "ocorrencia" | "reuniao" | "entrega";

export interface Notificacao {
  id: number;
  tipo: TipoNotificacaoEnum;
  titulo: string;
  mensagem: string;
  referencia_tipo: string | null;
  referencia_id: number | null;
  lida_em: string | null;
  created_at: string;
}

export interface NotificacaoContagem {
  nao_lidas: number;
}

export interface Entrega {
  id: number;
  predio_id: number;
  unidade_id: number;
  descricao: string;
  localizacao: string;
  retirada_em: string | null;
  retirada_por: number | null;
  created_by: number | null;
  created_at: string;
  updated_at: string;
}

export interface EntregaCreateInput {
  unidade_id: number;
  descricao: string;
  localizacao: string;
  predio_id?: number | null;
}

export type TipoDocumentoVisitanteEnum = "rg" | "cpf" | "cin" | "nao_informado";

export interface Visitante {
  id: number;
  predio_id: number;
  unidade_id: number;
  nome_completo: string;
  tipo_documento: TipoDocumentoVisitanteEnum;
  numero_documento: string | null;
  veiculo_placa: string | null;
  veiculo_modelo: string | null;
  veiculo_cor: string | null;
  created_by: number | null;
  created_at: string;
}

export interface VisitanteItemInput {
  nome_completo: string;
  tipo_documento: TipoDocumentoVisitanteEnum;
  numero_documento?: string | null;
  veiculo_placa?: string | null;
  veiculo_modelo?: string | null;
  veiculo_cor?: string | null;
}

export interface VisitanteCreateInput extends VisitanteItemInput {
  unidade_id: number;
  predio_id?: number | null;
}

export interface VisitanteLoteCreateInput {
  unidade_id: number;
  visitantes: VisitanteItemInput[];
  predio_id?: number | null;
}

export interface AreaComum {
  id: number;
  predio_id: number;
  nome: string;
  descricao: string | null;
  capacidade: number | null;
  ativo: boolean;
  agenda_liberada_ate: string | null;
  created_at: string;
  updated_at: string;
}

export interface AreaComumCreateInput {
  nome: string;
  descricao?: string | null;
  capacidade?: number | null;
  predio_id?: number | null;
}

export interface AreaComumAtualizarInput {
  nome?: string;
  descricao?: string | null;
  capacidade?: number | null;
  ativo?: boolean;
}

export type StatusReservaEnum = "confirmada" | "cancelada";

export interface Reserva {
  id: number;
  predio_id: number;
  area_comum_id: number;
  unidade_id: number;
  data: string;
  status: StatusReservaEnum;
  observacoes: string | null;
  cancelada_em: string | null;
  cancelada_por: number | null;
  created_by: number | null;
  created_at: string;
}

export interface ReservaCreateInput {
  area_comum_id: number;
  data: string;
  observacoes?: string | null;
  unidade_id?: number | null;
  predio_id?: number | null;
}

export interface Fornecedor {
  id: number;
  predio_id: number;
  nome: string;
  documento: string | null;
  cnpj: string | null;
  razao_social: string | null;
  nome_fantasia: string | null;
  categoria: string;
  telefone: string | null;
  email: string | null;
  observacoes: string | null;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

export interface FornecedorCreateInput {
  nome: string;
  documento?: string | null;
  cnpj?: string | null;
  razao_social?: string | null;
  nome_fantasia?: string | null;
  categoria: string;
  telefone?: string | null;
  email?: string | null;
  observacoes?: string | null;
  predio_id?: number | null;
}

export interface DespesaRecorrente {
  id: number;
  predio_id: number;
  fornecedor_id: number | null;
  unidade_id: number | null;
  descricao: string;
  categoria: string;
  valor: string;
  dia_vencimento: number;
  ativo: boolean;
  data_inicio: string;
  data_fim: string | null;
  ultima_geracao: string | null;
  observacoes: string | null;
  created_at: string;
  updated_at: string;
}

export interface DespesaRecorrenteCreateInput {
  fornecedor_id?: number | null;
  unidade_id?: number | null;
  descricao: string;
  categoria: string;
  valor: string;
  dia_vencimento: number;
  data_inicio: string;
  data_fim?: string | null;
  observacoes?: string | null;
  predio_id?: number | null;
}

export interface ContatoLeadCreateInput {
  nome: string;
  email: string;
  telefone?: string | null;
  mensagem?: string | null;
}

export interface Funcionario {
  id: number;
  predio_id: number;
  nome_completo: string;
  cargo: string;
  cpf: string | null;
  telefone: string | null;
  email: string | null;
  data_admissao: string | null;
  salario: string | null;
  ativo: boolean;
  observacoes: string | null;
  created_at: string;
  updated_at: string;
}

export interface FuncionarioInput {
  nome_completo: string;
  cargo: string;
  cpf?: string | null;
  telefone?: string | null;
  email?: string | null;
  data_admissao?: string | null;
  salario?: string | null;
  observacoes?: string | null;
  ativo?: boolean;
}

export interface PrestadorServico {
  id: number;
  predio_id: number;
  nome: string;
  tipo_servico: string;
  razao_social: string | null;
  cnpj: string | null;
  telefone: string | null;
  email: string | null;
  custo_mensal: string;
  incluir_no_rateio: boolean;
  criterio_rateio: CriterioRateioEnum;
  ativo: boolean;
  observacoes: string | null;
  created_at: string;
  updated_at: string;
}

export interface PrestadorServicoInput {
  nome: string;
  tipo_servico: string;
  razao_social?: string | null;
  cnpj?: string | null;
  telefone?: string | null;
  email?: string | null;
  custo_mensal: string;
  incluir_no_rateio: boolean;
  criterio_rateio: CriterioRateioEnum;
  observacoes?: string | null;
  ativo?: boolean;
}
