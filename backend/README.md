# MeuPredio - Backend

API FastAPI da Fase 1 do MeuPredio. Veja `docs/setup.md` na raiz do repositório
para instruções completas de setup local (com ou sem Docker).

Resumo rápido:

```bash
cd backend
python -m venv .venv
. .venv/Scripts/activate   # Windows (PowerShell: .venv\Scripts\Activate.ps1)
pip install -e ".[dev]"
alembic upgrade head
python -m app.scripts.seed_admin
uvicorn app.main:app --reload
```

Testes: `pytest` (requer `DATABASE_URL_TEST` configurado e banco `meupredio_test`
acessível — veja `docker/postgres-init/01-create-test-db.sh`).
