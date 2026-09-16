# Guia de setup local - MeuPrédio (Fase 1)

Este guia cobre duas formas de rodar o projeto localmente: **via Docker
Compose** (recomendado, sobe tudo de uma vez) e **manualmente** (backend e
frontend rodando direto na máquina, útil para debugar/editar com mais
controle).

## Pré-requisitos

| Ferramenta | Necessária para |
|---|---|
| Docker + Docker Compose | Caminho via Docker (recomendado) |
| Python 3.11+ | Backend fora do Docker |
| Node.js 20+ e npm | Frontend (com ou sem Docker) |
| PostgreSQL 16 (se não usar Docker para o banco) | Backend fora do Docker |
| Terraform >= 1.7 (opcional) | Só para revisar `infra/terraform/oci/` |

## 1. Configurar variáveis de ambiente

Na raiz do repositório:

```bash
cp .env.example .env
```

Edite `.env` e ajuste, no mínimo:

- `POSTGRES_PASSWORD` — senha do banco local.
- `SECRET_KEY` — chave de assinatura dos JWTs. Gere um valor aleatório, por
  exemplo:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(64))"
  ```
  A aplicação **recusa subir** (`RuntimeError`) se `SECRET_KEY` estiver
  vazia fora de ambiente de teste — isso é proposital, para nunca rodar
  com um segredo previsível.
- `FIRST_ADMIN_EMAIL` / `FIRST_ADMIN_PASSWORD` — credenciais do primeiro
  usuário Administrador, criado de forma idempotente por
  `app/scripts/seed_admin.py` (ou automaticamente ao subir o container do
  backend via `docker compose up`).

**Nunca commite o arquivo `.env`** (já está no `.gitignore`).

## 2. Caminho recomendado: Docker Compose

Suba primeiro só o banco, para confirmar que ele sobe saudável:

```bash
docker compose up -d db
docker compose ps        # "db" deve aparecer como healthy
```

Depois suba a stack completa:

```bash
docker compose up
```

Isso vai, na ordem:

1. Subir o PostgreSQL (`db`), criando `meupredio` e `meupredio_test`.
2. Subir o `backend`: aplicar as migrations Alembic (`alembic upgrade
   head`), criar o admin inicial (`app/scripts/seed_admin`, idempotente) e
   então iniciar o Uvicorn com reload em `http://localhost:8000`.
3. Subir o `frontend`: `vite` em modo dev em `http://localhost:5173`,
   consumindo a API em `VITE_API_URL` (por padrão, `http://localhost:8000`).

Acesse:

- Swagger/OpenAPI: http://localhost:8000/docs
- Frontend: http://localhost:5173

> **Nota sobre este scaffolding:** os comandos `docker compose up` acima
> não puderam ser executados durante a geração deste repositório porque o
> Docker não estava disponível no ambiente usado para o scaffolding. A
> configuração foi escrita e revisada manualmente, mas a subida real da
> stack via Docker ainda precisa ser validada no seu ambiente.

## 3. Alternativa: rodar sem Docker

### 3.1 Banco de dados

Suba um PostgreSQL 16 local (ou continue usando `docker compose up -d db`
só para o banco) e crie os dois bancos:

```sql
CREATE DATABASE meupredio;
CREATE DATABASE meupredio_test;
```

### 3.2 Backend

```bash
cd backend
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Linux/macOS
source .venv/bin/activate

pip install -e ".[dev]"

# Configure DATABASE_URL/SECRET_KEY etc. em backend/.env (ou exporte no shell)
cp ../.env.example .env   # ajuste os valores conforme necessário

alembic upgrade head
python -m app.scripts.seed_admin
uvicorn app.main:app --reload
```

A API sobe em `http://localhost:8000` (Swagger em `/docs`).

Rodar os testes:

```bash
pytest
```

A suíte usa `DATABASE_URL_TEST` (ou deriva de `DATABASE_URL` + sufixo
`_test`) e aplica as migrations reais do Alembic contra esse banco antes de
rodar os testes — inclusive o trigger de imutabilidade da auditoria.

### 3.3 Frontend

```bash
cd frontend
cp .env.example .env   # ajusta VITE_API_URL se necessário
npm install
npm run dev
```

Acesse `http://localhost:5173`. Login com o e-mail/senha definidos em
`FIRST_ADMIN_EMAIL`/`FIRST_ADMIN_PASSWORD`.

Build de produção (gera `dist/`, incluindo `manifest.webmanifest` e o
service worker via Workbox):

```bash
npm run build
```

> Os ícones em `frontend/public/icon-192.png` e `icon-512.png` são
> **placeholders** (1x1 pixel transparente) gerados durante o scaffolding —
> substitua por artes finais antes de qualquer publicação real (loja de
> apps, produção).

## 4. Fluxo de verificação end-to-end sugerido

1. Login como administrador (via frontend ou `POST /auth/login` no
   Swagger).
2. Criar uma unidade (`POST /unidades`).
3. Criar um usuário morador vinculado a essa unidade (`POST /usuarios`).
4. Criar um veículo para a unidade (`POST /veiculos`).
5. Soft-deletar o veículo (`DELETE /veiculos/{id}`) e confirmar que ele some
   da listagem padrão, mas continua no banco com `deleted_at` preenchido.
6. Anonimizar o usuário morador (`POST /usuarios/{id}/anonimizar`) e
   conferir que os dados pessoais foram substituídos.
7. Conferir, via banco (`SELECT * FROM logs_auditoria ORDER BY id`), que
   cada uma dessas ações gerou uma entrada de auditoria — e que uma
   tentativa manual de `UPDATE`/`DELETE` nessa tabela é rejeitada pelo
   PostgreSQL.

## 5. Infraestrutura de deploy (Terraform / OCI)

`infra/terraform/oci/` é um esqueleto **documentado, não aplicado**. Veja
`infra/terraform/oci/README.md` para o que falta antes de um deploy real
(credenciais, `terraform init/validate/plan`, revisão do recurso de banco
gerenciado contra a versão atual do provider).
