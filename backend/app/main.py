from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import auth, despesas, fornecedores, health, unidades, usuarios, veiculos

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.2.0",
    description=(
        "API do MeuPredio - Fase 1 (usuarios, unidades, veiculos, auditoria) "
        "e inicio da Fase 2 (fornecedores e lancamentos de despesa)."
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
app.include_router(unidades.router)
app.include_router(veiculos.router)
app.include_router(fornecedores.router)
app.include_router(despesas.router)
