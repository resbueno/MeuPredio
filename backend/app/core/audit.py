"""Utilitários para gravar entradas na trilha de auditoria imutável."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.models.log_auditoria import LogAuditoria

# Campos que nunca devem ir para o log de auditoria, mesmo em texto cifrado/hash.
_CAMPOS_SENSIVEIS = {"hashed_password", "groq_api_key_cifrada"}


def model_to_audit_dict(obj: Any, *, exclude: set[str] | None = None) -> dict[str, Any]:
    """Serializa um modelo ORM em um dict JSON-safe para `dados_antes`/`dados_depois`.

    Exclui sempre `hashed_password` (e qualquer outro campo em `exclude`).
    """
    exclude_final = _CAMPOS_SENSIVEIS | (exclude or set())
    mapper = inspect(obj).mapper
    result: dict[str, Any] = {}
    for column in mapper.columns:
        name = column.key
        if name in exclude_final:
            continue
        value = getattr(obj, name)
        if isinstance(value, (datetime, date)):
            value = value.isoformat()
        elif isinstance(value, Decimal):
            value = float(value)
        elif isinstance(value, Enum):
            value = value.value
        result[name] = value
    return result


def registrar_log(
    db: Session,
    *,
    usuario_id: int | None,
    acao: str,
    entidade: str,
    entidade_id: int | None,
    dados_antes: dict[str, Any] | None = None,
    dados_depois: dict[str, Any] | None = None,
    ip_origem: str | None = None,
    user_agent: str | None = None,
) -> LogAuditoria:
    """Adiciona uma entrada de auditoria à sessão corrente (sem commit).

    Propositalmente NÃO faz commit: o chamador deve commitar a entrada de
    auditoria na MESMA transação da operação de negócio que ela descreve,
    garantindo atomicidade — a mudança e seu registro de auditoria acontecem
    juntos, ou nenhum dos dois é persistido (ex.: se a operação de negócio
    falhar depois, o rollback desfaz ambos).

    A tabela `logs_auditoria` em si é protegida por trigger de banco contra
    UPDATE/DELETE (ver migration 0002_audit_log_immutability_trigger) — este
    helper só cobre a parte de "sempre registrar no INSERT", a imutabilidade
    depois de gravado é garantida pelo PostgreSQL, não pela aplicação.
    """
    log = LogAuditoria(
        usuario_id=usuario_id,
        acao=acao,
        entidade=entidade,
        entidade_id=entidade_id,
        dados_antes=dados_antes,
        dados_depois=dados_depois,
        ip_origem=ip_origem,
        user_agent=user_agent,
    )
    db.add(log)
    db.flush()
    return log
