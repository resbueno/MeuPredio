variable "tenancy_ocid" {
  description = "OCID do tenancy OCI."
  type        = string
}

variable "user_ocid" {
  description = "OCID do usuario usado para autenticacao na API da OCI."
  type        = string
}

variable "fingerprint" {
  description = "Fingerprint da chave API do usuario."
  type        = string
}

variable "private_key_path" {
  description = "Caminho local para a chave privada da API (PEM). NUNCA versionar este arquivo nem colocar o valor da chave diretamente numa .tfvars commitada."
  type        = string
}

variable "region" {
  description = "Regiao OCI onde os recursos serao provisionados."
  type        = string
  default     = "sa-saopaulo-1"
}

variable "compartment_ocid" {
  description = "OCID do compartment onde os recursos do MeuPredio serao criados."
  type        = string
}

variable "project_name" {
  description = "Prefixo usado para nomear os recursos criados (ex.: meupredio)."
  type        = string
  default     = "meupredio"
}

variable "environment" {
  description = "Nome do ambiente (dev, staging, production)."
  type        = string
  default     = "dev"
}

variable "vcn_cidr_block" {
  description = "Bloco CIDR da VCN."
  type        = string
  default     = "10.20.0.0/16"
}

variable "public_subnet_cidr_block" {
  description = "Bloco CIDR da subnet publica (load balancer / instancia com IP publico)."
  type        = string
  default     = "10.20.0.0/24"
}

variable "private_subnet_cidr_block" {
  description = "Bloco CIDR da subnet privada (banco de dados gerenciado)."
  type        = string
  default     = "10.20.1.0/24"
}

variable "compute_shape" {
  description = "Shape da instancia compute. VM.Standard.A1.Flex e elegivel ao Always Free da OCI (ate 4 OCPUs / 24GB no total da conta)."
  type        = string
  default     = "VM.Standard.A1.Flex"
}

variable "compute_ocpus" {
  description = "Numero de OCPUs da instancia compute."
  type        = number
  default     = 2
}

variable "compute_memory_in_gbs" {
  description = "Memoria (GB) da instancia compute."
  type        = number
  default     = 12
}

variable "ssh_public_key_path" {
  description = "Caminho local para a chave publica SSH usada para acessar a instancia."
  type        = string
}

variable "db_admin_password" {
  description = "Senha do usuario administrador do banco gerenciado. Fornecer via TF_VAR_db_admin_password ou um cofre de segredos — nunca em texto plano num arquivo versionado."
  type        = string
  sensitive   = true
}
