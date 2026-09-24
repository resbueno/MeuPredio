from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.dependencies import require_modulo
from app.models.enums import ModuloEnum
from app.routers import (
    areas_comuns,
    auth,
    avisos_diretos,
    avisos_mural,
    contato,
    despesas,
    despesas_recorrentes,
    entregas,
    fornecedores,
    funcionarios,
    health,
    notificacoes,
    ocorrencias,
    predios,
    prestadores_servico,
    reservas,
    reunioes,
    tickets,
    transparencia,
    unidades,
    usuarios,
    veiculos,
    visitantes,
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


def _modulo(modulo: ModuloEnum) -> list[Depends]:
    return [Depends(require_modulo(modulo))]


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(predios.router)
app.include_router(unidades.router)
app.include_router(veiculos.router, dependencies=_modulo(ModuloEnum.VEICULOS))
app.include_router(fornecedores.router, dependencies=_modulo(ModuloEnum.FINANCEIRO))
app.include_router(despesas.router, dependencies=_modulo(ModuloEnum.FINANCEIRO))
app.include_router(despesas_recorrentes.router, dependencies=_modulo(ModuloEnum.FINANCEIRO))
app.include_router(transparencia.router, dependencies=_modulo(ModuloEnum.FINANCEIRO))
app.include_router(tickets.router, dependencies=_modulo(ModuloEnum.CHAMADOS))
app.include_router(avisos_mural.router, dependencies=_modulo(ModuloEnum.AVISOS))
app.include_router(avisos_diretos.router, dependencies=_modulo(ModuloEnum.AVISOS))
app.include_router(ocorrencias.router, dependencies=_modulo(ModuloEnum.OCORRENCIAS))
app.include_router(reunioes.router, dependencies=_modulo(ModuloEnum.REUNIOES))
app.include_router(entregas.router, dependencies=_modulo(ModuloEnum.ENTREGAS))
app.include_router(notificacoes.router)
app.include_router(visitantes.router, dependencies=_modulo(ModuloEnum.VISITANTES))
app.include_router(areas_comuns.router, dependencies=_modulo(ModuloEnum.RESERVAS))
app.include_router(reservas.router, dependencies=_modulo(ModuloEnum.RESERVAS))
app.include_router(contato.router)
app.include_router(funcionarios.router, dependencies=_modulo(ModuloEnum.EQUIPE))
app.include_router(prestadores_servico.router, dependencies=_modulo(ModuloEnum.EQUIPE))
