"""Modelos ORM. Importar este pacote garante que todos os modelos sejam
registrados em `Base.metadata` (necessário para Alembic autogenerate e para
resolver os relacionamentos declarados por nome de string)."""
from app.models.associations import usuario_unidades  # noqa: F401
from app.models.aviso_direto import AvisoDireto  # noqa: F401
from app.models.aviso_mural import AvisoMural  # noqa: F401
from app.models.despesa_lancamento import DespesaLancamento  # noqa: F401
from app.models.fornecedor import Fornecedor  # noqa: F401
from app.models.log_auditoria import LogAuditoria  # noqa: F401
from app.models.ocorrencia import Ocorrencia  # noqa: F401
from app.models.predio import Predio  # noqa: F401
from app.models.predio_convite import PredioConvite  # noqa: F401
from app.models.rateio_despesa_item import RateioDespesaItem  # noqa: F401
from app.models.reuniao import Reuniao  # noqa: F401
from app.models.reuniao_presenca import ReuniaoPresenca  # noqa: F401
from app.models.ticket_atendimento import TicketAtendimento  # noqa: F401
from app.models.ticket_comentario import TicketComentario  # noqa: F401
from app.models.unidade import Unidade  # noqa: F401
from app.models.usuario import Usuario  # noqa: F401
from app.models.usuario_papel_extra import UsuarioPapelExtra  # noqa: F401
from app.models.veiculo import Veiculo  # noqa: F401

__all__ = [
    "Usuario",
    "UsuarioPapelExtra",
    "Unidade",
    "Veiculo",
    "LogAuditoria",
    "Fornecedor",
    "DespesaLancamento",
    "Predio",
    "PredioConvite",
    "RateioDespesaItem",
    "Reuniao",
    "ReuniaoPresenca",
    "TicketAtendimento",
    "TicketComentario",
    "AvisoMural",
    "AvisoDireto",
    "Ocorrencia",
    "usuario_unidades",
]
