from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CategoriaTicketEnum, PrioridadeTicketEnum, StatusTicketEnum


class TicketComentarioCreate(BaseModel):
    mensagem: str = Field(min_length=1, max_length=2000)


class TicketComentarioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    created_by: int | None
    mensagem: str
    created_at: datetime


class TicketAtendimentoCreate(BaseModel):
    titulo: str = Field(min_length=2, max_length=200)
    descricao: str = Field(min_length=2, max_length=4000)
    categoria: CategoriaTicketEnum
    prioridade: PrioridadeTicketEnum
    unidade_id: int | None = None
    # Só usado quando quem cria é o ADMINISTRADOR (sem prédio próprio) -
    # mesmo padrão de DespesaLancamentoCreate.predio_id.
    predio_id: int | None = None


class TicketAtendimentoAtualizar(BaseModel):
    """Só o autor pode usar, e só enquanto o chamado está 'aberto' (ver
    `_exigir_aberto` no router) - reclassificar/corrigir antes de alguém
    começar a atender."""

    titulo: str | None = Field(default=None, min_length=2, max_length=200)
    descricao: str | None = Field(default=None, min_length=2, max_length=4000)
    categoria: CategoriaTicketEnum | None = None
    prioridade: PrioridadeTicketEnum | None = None


class TicketAtendimentoAssumir(BaseModel):
    # Nulo = o próprio chamador assume; informar para atribuir a outro
    # membro da gestão (ex.: síndico atribuindo ao zelador).
    responsavel_id: int | None = None


class TicketAtendimentoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    predio_id: int
    unidade_id: int | None
    responsavel_id: int | None
    created_by: int | None
    titulo: str
    descricao: str
    categoria: CategoriaTicketEnum
    prioridade: PrioridadeTicketEnum
    status: StatusTicketEnum
    prazo_sla: datetime
    resolvido_em: datetime | None
    esta_atrasado: bool
    comentarios: list[TicketComentarioRead] = []
    created_at: datetime
    updated_at: datetime
