export type RoleEnum = "morador" | "sindico" | "zelador" | "administrador";
export type TipoVeiculoEnum = "carro" | "moto" | "outro";

export interface Usuario {
  id: number;
  email: string;
  full_name: string;
  role: RoleEnum;
  unidade_id: number | null;
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
  unidade_id?: number | null;
  password: string;
}

export interface UsuarioUpdateInput {
  full_name?: string;
  role?: RoleEnum;
  unidade_id?: number | null;
  is_active?: boolean;
  password?: string;
}

export interface Unidade {
  id: number;
  bloco: string;
  numero: string;
  proprietario_id: number | null;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

export interface UnidadeInput {
  bloco: string;
  numero: string;
  proprietario_id?: number | null;
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
