# MeuPrédio

SaaS de gestão de condomínios. Este repositório contém o **scaffolding da
Fase 1**: backend de API, frontend PWA e infraestrutura de desenvolvimento
para as entidades centrais do sistema (usuários, unidades e veículos), com
autenticação, controle de acesso por papel (RBAC) e trilha de auditoria
imutável.

> Fases 2 (motor financeiro, IA/OCR) e 3 (WhatsApp, portal de transparência,
> tickets) estão fora do escopo deste repositório na sua forma atual — ver
> `Documentação/` para o roadmap completo.

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | FastAPI + SQLAlchemy 2.0 + Alembic + PostgreSQL 16 |
| Autenticação | JWT (OAuth2 Password Flow) + Argon2 para hashing de senha |
| Frontend | React + Vite + TypeScript + Tailwind CSS, PWA via `vite-plugin-pwa` |
| Dados no frontend | `@tanstack/react-query`, `react-hook-form` + `zod`, `axios` |
| Infraestrutura local | Docker Compose (PostgreSQL + backend + frontend) |
| Infraestrutura de deploy (futura) | Terraform (OCI) — esqueleto documentado, **não aplicado** |

## Estrutura do repositório

```
MeuPredio/
├── backend/                 # API FastAPI (ver backend/README.md)
├── frontend/                 # SPA/PWA React (Vite + TS + Tailwind)
├── infra/terraform/oci/      # Esqueleto Terraform - NAO aplicado nesta fase
├── docker/postgres-init/     # Script de bootstrap do banco de teste
├── docs/setup.md              # Guia de setup detalhado (com e sem Docker)
├── docker-compose.yml
├── .env.example
└── Documentação/               # Documentação técnica original do projeto
```

## Modelo de domínio (Fase 1)

- **Usuario** — email, senha (hash Argon2), papel (`morador` / `sindico` /
  `zelador` / `administrador`), vínculo opcional com uma unidade.
- **Unidade** — bloco + número (únicos entre si), proprietário (usuário).
- **Veiculo** — placa, modelo, cor, tipo, vinculado a uma unidade.
- **LogAuditoria** — trilha de auditoria **imutável**: um trigger de banco
  bloqueia `UPDATE`/`DELETE` na tabela `logs_auditoria`, mesmo que a camada
  de aplicação seja comprometida.

Todas as entidades de negócio usam **soft-delete** (`deleted_at`) — nunca
`DELETE` físico. `Usuario` também suporta **anonimização** (`POST
/usuarios/{id}/anonimizar`), pensada para atender solicitações de exclusão
de dados pessoais sob a LGPD sem perder a integridade do histórico
financeiro/de auditoria.

## Como rodar localmente

Veja o guia completo em [`docs/setup.md`](docs/setup.md). Resumo rápido com
Docker:

```bash
cp .env.example .env
# edite .env: defina SECRET_KEY, POSTGRES_PASSWORD e (opcional) o admin inicial
docker compose up -d db
docker compose up
```

- Backend: http://localhost:8000/docs (Swagger)
- Frontend: http://localhost:5173

## Segurança (resumo)

- Senhas: hash Argon2id (`passlib`), nunca armazenadas em texto plano.
- JWT: assinado com `SECRET_KEY` (obrigatória via ambiente, sem default de
  produção), algoritmo fixado explicitamente na validação (`HS256`).
- RBAC: dependency `require_role(*papeis)` em cada endpoint sensível;
  decisões de autorização sempre consultam o papel atual do usuário no
  banco (nunca confiam cegamente no claim `role` do JWT).
- Auditoria: toda escrita relevante (`CREATE`/`UPDATE`/`SOFT_DELETE`/
  `ANONYMIZE`/`LOGIN`) gera uma entrada em `logs_auditoria`, protegida por
  trigger de banco contra alteração posterior.
- Segredos: apenas em `.env` (fora do controle de versão) — ver
  `.env.example`. Nenhum segredo está hardcoded no código.

## Testes

```bash
cd backend
pytest
```

A suíte aplica as migrations Alembic reais (incluindo o trigger de
imutabilidade) contra um banco de teste dedicado (`meupredio_test`) e cobre
CRUD das três entidades, RBAC (401/403), soft-delete e geração de trilha de
auditoria.
