from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import RoleEnum
from app.models.unidade import Unidade
from app.models.usuario import Usuario

# Papéis sujeitos à regra "no máximo um por unidade" - síndico, zelador e
# administrador são papéis de equipe/plataforma, não de ocupação da unidade,
# então não entram nessa exclusividade.
_PAPEIS_EXCLUSIVOS_POR_UNIDADE = (RoleEnum.MORADOR, RoleEnum.PROPRIETARIO)

_LABEL_PAPEL = {
    RoleEnum.MORADOR: "morador",
    RoleEnum.PROPRIETARIO: "proprietário",
}


def validar_unicidade_papel_por_unidade(
    db: Session,
    role: RoleEnum,
    unidades: list[Unidade],
    usuario_id_excluir: int | None = None,
) -> None:
    """Garante no máximo um morador e um proprietário cadastrados por
    unidade (regra de negócio do condomínio - não confundir com "uma pessoa
    pode ter mais de uma unidade", que continua permitido). Levanta 409 se
    alguma das `unidades` já tiver outro usuário ativo com o mesmo `role`.

    `usuario_id_excluir` existe para o caso de UPDATE: ao revalidar os
    vínculos do próprio usuário sendo editado, ele não deve colidir consigo
    mesmo."""
    if role not in _PAPEIS_EXCLUSIVOS_POR_UNIDADE:
        return

    for unidade in unidades:
        conflito_query = (
            db.query(Usuario)
            .join(Usuario.unidades)
            .filter(
                Unidade.id == unidade.id,
                Usuario.role == role,
                Usuario.deleted_at.is_(None),
            )
        )
        if usuario_id_excluir is not None:
            conflito_query = conflito_query.filter(Usuario.id != usuario_id_excluir)

        if conflito_query.first() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"A unidade {unidade.bloco}/{unidade.numero} já tem um "
                    f"{_LABEL_PAPEL[role]} cadastrado."
                ),
            )
