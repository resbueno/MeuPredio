"""Regras de SLA dos tickets de atendimento (Fase 3 do roadmap)."""
from __future__ import annotations

from datetime import datetime, timedelta

from app.models.enums import PrioridadeTicketEnum

# Prazo de atendimento por prioridade - escolha de produto, nao configuravel
# por predio nesta fatia (ver roadmap): alta = 1 dia util aproximado, media =
# 3 dias, baixa = 1 semana.
_PRAZO_SLA_HORAS: dict[PrioridadeTicketEnum, int] = {
    PrioridadeTicketEnum.ALTA: 24,
    PrioridadeTicketEnum.MEDIA: 72,
    PrioridadeTicketEnum.BAIXA: 168,
}


def calcular_prazo_sla(prioridade: PrioridadeTicketEnum, agora: datetime) -> datetime:
    """`agora` explicito (em vez de `datetime.now()` interno) para o prazo
    ficar fixo no momento da abertura do ticket e o calculo ser testavel sem
    mockar relogio."""
    return agora + timedelta(hours=_PRAZO_SLA_HORAS[prioridade])
