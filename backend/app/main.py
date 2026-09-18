from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import (
    auth,
    despesas,
    fornecedores,
    health,
    predios,
    transparencia,
    unidades,
    usuarios,
    veiculos,
)

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.3.0",
    description=(
        "API do MeuPredio - multi-tenant por predio (isolamento entre "
        "condominios), usuarios/unidades/veiculos (Fase 1) e inicio do "
        "Motor Financeiro - fornecedores e lancamentos de despesa (Fase 2)."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(predios.router)
app.include_router(unidades.router)
app.include_router(veiculos.router)
app.include_router(fornecedores.router)
app.include_router(despesas.router)
app.include_router(transparencia.router)
