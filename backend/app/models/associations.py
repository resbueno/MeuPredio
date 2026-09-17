"""Tabelas de associação (many-to-many) puras, sem atributos próprios."""
from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Table

from app.core.database import Base

# Um usuário (morador, proprietário...) pode estar vinculado a mais de uma
# unidade do MESMO prédio (ex.: um proprietário com dois apartamentos) - ver
# CHECK constraint em Usuario garantindo que só administrador (papel global,
# sem prédio) fica de fora dessa exigência de vínculo.
usuario_unidades = Table(
    "usuario_unidades",
    Base.metadata,
    Column("usuario_id", ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True),
    Column("unidade_id", ForeignKey("unidades.id", ondelete="CASCADE"), primary_key=True),
)
