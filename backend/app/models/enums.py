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


class CategoriaTicketEnum(str, enum.Enum):
    MANUTENCAO = "manutencao"
    DUVIDA = "duvida"
    SOLICITACAO = "solicitacao"
    OUTRO = "outro"


class PrioridadeTicketEnum(str, enum.Enum):
    """Define o prazo de SLA do chamado (ver app/core/tickets.py)."""

    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"


class StatusTicketEnum(str, enum.Enum):
    ABERTO = "aberto"
    EM_ANDAMENTO = "em_andamento"
    RESOLVIDO = "resolvido"
    CANCELADO = "cancelado"


class TipoAvisoMuralEnum(str, enum.Enum):
    """Os dois blocos do mural (ver GET /avisos): 'condominio' só
    síndico/administrador publica, 'anuncio' qualquer morador/proprietário."""

    CONDOMINIO = "condominio"
    ANUNCIO = "anuncio"


class DestinatarioAvisoEnum(str, enum.Enum):
    """Para quem, dentro da unidade, um aviso direto vale - uma unidade pode
    ter morador(es) e proprietário(s) diferentes, então o emissor escolhe."""

    MORADOR = "morador"
    PROPRIETARIO = "proprietario"
    AMBOS = "ambos"


class TipoAvisoDiretoEnum(str, enum.Enum):
    """'multa' é a única variante que gera uma despesa vinculada exclusiva
    da unidade (ver DespesaLancamento.unidade_id e routers/avisos_diretos.py)."""

    AVISO = "aviso"
    ADVERTENCIA = "advertencia"
    MULTA = "multa"


class TipoReuniaoEnum(str, enum.Enum):
    ORDINARIA = "ordinaria"
    EXTRAORDINARIA = "extraordinaria"


class StatusReuniaoEnum(str, enum.Enum):
    """'convocada' aceita confirmação de presença e edição; some da lista
    de convocações ativas assim que vira 'realizada' (ata registrada) ou
    'cancelada' - nunca as duas coisas ao mesmo tempo."""

    CONVOCADA = "convocada"
    REALIZADA = "realizada"
    CANCELADA = "cancelada"


class TipoNotificacaoEnum(str, enum.Enum):
    """Origem de uma notificação no sino de alertas - cada valor mapeia a um
    evento gerado por outro módulo (ver app/core/notificacoes.py)."""

    AVISO_GERAL = "aviso_geral"
    AVISO_DIRETO = "aviso_direto"
    OCORRENCIA = "ocorrencia"
    REUNIAO = "reuniao"
    ENTREGA = "entrega"
