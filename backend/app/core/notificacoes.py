"""Fan-out de notificações para o sino de alertas: um evento de negócio
(aviso publicado, ocorrência registrada, reunião convocada, entrega
recebida) vira UMA linha de `Notificacao` por destinatário. Quem chama
`notificar_usuarios` ainda é responsável pelo commit - esta função só
adiciona à sessão corrente, para participar da mesma transação do evento
que a originou (se o commit falhar, a notificação some junto)."""
from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy.orm import Session

from app.models.enums import RoleEnum, TipoNotificacaoEnum
from app.models.notificacao import Notificacao
from app.models.unidade import Unidade
from app.models.usuario import Usuario
from app.models.usuario_papel_extra import UsuarioPapelExtra


def notificar_usuarios(
    db: Session,
    *,
    predio_id: int,
    usuario_ids: Iterable[int],
    tipo: TipoNotificacaoEnum,
    titulo: str,
    mensagem: str,
    referencia_tipo: str | None = None,
    referencia_id: int | None = None,
) -> None:
    for usuario_id in set(usuario_ids):
        db.add(
            Notificacao(
                predio_id=predio_id,
                usuario_id=usuario_id,
                tipo=tipo,
                titulo=titulo,
                mensagem=mensagem,
                referencia_tipo=referencia_tipo,
                referencia_id=referencia_id,
            )
        )


def ids_usuarios_do_predio(
    db: Session, predio_id: int, *, excluir_papel: RoleEnum | None = RoleEnum.ADMINISTRADOR
) -> set[int]:
    query = db.query(Usuario.id).filter(
        Usuario.predio_id == predio_id, Usuario.deleted_at.is_(None)
    )
    if excluir_papel is not None:
        query = query.filter(Usuario.role != excluir_papel)
    return {uid for (uid,) in query.all()}


def ids_usuarios_com_papel(db: Session, predio_id: int, papel: RoleEnum) -> set[int]:
    """Une papel principal e papéis extras (ver `Usuario.roles_efetivos`) -
    um síndico que acumula outra função continua sendo síndico para fins de
    notificação."""
    diretos = db.query(Usuario.id).filter(
        Usuario.predio_id == predio_id, Usuario.deleted_at.is_(None), Usuario.role == papel
    )
    extras = (
        db.query(UsuarioPapelExtra.usuario_id)
        .join(Usuario, Usuario.id == UsuarioPapelExtra.usuario_id)
        .filter(
            Usuario.predio_id == predio_id,
            Usuario.deleted_at.is_(None),
            UsuarioPapelExtra.role == papel,
        )
    )
    return {uid for (uid,) in diretos.all()} | {uid for (uid,) in extras.all()}


def ids_usuarios_da_unidade(db: Session, unidade_id: int) -> set[int]:
    unidade = db.get(Unidade, unidade_id)
    if unidade is None:
        return set()
    return {u.id for u in unidade.usuarios if u.deleted_at is None}
