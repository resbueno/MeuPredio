import enum


class RoleEnum(str, enum.Enum):
    """Papéis de acesso (RBAC). O valor é o que fica persistido no banco e
    embutido no JWT — não alterar os valores sem migration correspondente."""

    MORADOR = "morador"
    PROPRIETARIO = "proprietario"
    SINDICO = "sindico"
    ZELADOR = "zelador"
    ADMINISTRADOR = "administrador"


class TipoVeiculoEnum(str, enum.Enum):
    CARRO = "carro"
    MOTO = "moto"
    OUTRO = "outro"


class StatusDespesaEnum(str, enum.Enum):
    """Status de um lançamento de despesa. 'Atrasado' não é um status
    persistido — é derivado (pendente + data_vencimento no passado) para
    nunca ficar dessincronizado do relógio atual (ver `DespesaLancamento.esta_atrasada`)."""

    PENDENTE = "pendente"
    PAGO = "pago"
    CANCELADO = "cancelado"


class CriterioRateioEnum(str, enum.Enum):
    """Critério usado para dividir uma despesa entre as unidades de um
    prédio (ver POST /despesas/{id}/ratear)."""

    IGUAL = "igual"
    FRACAO_IDEAL = "fracao_ideal"
