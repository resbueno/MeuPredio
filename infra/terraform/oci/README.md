# Terraform - OCI (placeholder, NÃO aplicado)

Este diretório é um **esqueleto documentado** de infraestrutura como código
para uma futura fase de deploy real do MeuPrédio na Oracle Cloud
Infrastructure (OCI). Ele foi escrito durante o scaffolding da Fase 1 apenas
para:

- fixar a convenção de nomes/tags dos recursos (`meupredio-<ambiente>-*`);
- documentar a topologia de rede pretendida (VCN com subnet pública para a
  instância de aplicação e subnet privada para o banco de dados);
- servir de ponto de partida para quando a fase de deploy for de fato
  executada.

## O que NÃO foi feito (de propósito)

- **`terraform apply` nunca foi executado.** Nenhum recurso real foi
  provisionado na OCI a partir deste diretório.
- **`terraform validate` não pôde ser executado nesta sessão** porque o
  binário `terraform` não está instalado no ambiente local usado para gerar
  este scaffolding. Os arquivos foram escritos e revisados manualmente, mas
  a validação sintática/de schema pelo Terraform em si ainda está pendente.
- Os argumentos exatos do recurso `oci_psql_db_system` (`database.tf`) devem
  ser reconferidos contra a versão do provider `oracle/oci` em uso no
  momento do deploy real — a API desse serviço específico evoluiu nas
  últimas versões do provider.

## Antes de rodar isto de verdade

1. Instalar o Terraform (`>= 1.7`) e o CLI da OCI.
2. Criar um arquivo `terraform.tfvars` (NUNCA commitar) com as credenciais e
   OCIDs necessários (veja as variáveis obrigatórias em `variables.tf`).
3. Rodar `terraform init`, depois `terraform validate` e `terraform plan`
   para revisar o que seria criado.
4. Só então considerar `terraform apply` — com revisão humana do plano.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `versions.tf` | Versão do Terraform e do provider `oracle/oci`. |
| `variables.tf` | Variáveis de entrada (credenciais, região, sizing, CIDRs). |
| `main.tf` | Provider `oci` e locals compartilhados (prefixo de nome, tags). |
| `network.tf` | VCN, subnets pública/privada, gateway, route tables, security lists. |
| `compute.tf` | Instância única rodando o `docker-compose` de produção (backend+frontend). |
| `database.tf` | Banco gerenciado (OCI Database with PostgreSQL) — **placeholder a revisar**. |
| `object_storage.tf` | Buckets de uploads (Fase 2/IA-OCR) e backups. |
| `outputs.tf` | IP público da instância, IDs de rede/banco, nomes dos buckets. |
