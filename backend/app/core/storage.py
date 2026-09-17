"""Armazenamento local dos documentos enviados para OCR (boletos/comprovantes).

Guarda em disco, sob `settings.UPLOADS_DIR`, escopado por prédio - não é a
solução final (o esqueleto Terraform já reserva Object Storage para isso na
fase de deploy real na OCI, ver `infra/terraform/oci/object_storage.tf`),
mas evita depender daquela infraestrutura ainda não provisionada para esta
fatia da Fase 2. Em produção/homologação, `UPLOADS_DIR` aponta para um
volume Docker persistente (não o filesystem efêmero do container) - ver
docker-compose.yml.
"""
from __future__ import annotations

import re
import uuid
from pathlib import Path

from app.core.config import get_settings

# Nome de arquivo gerado por `salvar_documento` (uuid4 hex + extensao curta)
# - usado para validar o parametro de path vindo do cliente em
# `obter_documento` antes de tocar o filesystem (nunca confiar em input de
# URL para montar um caminho sem essa validacao - traversal via "../").
_NOME_ARQUIVO_RE = re.compile(r"^[0-9a-f]{32}\.[A-Za-z0-9]{1,10}$")


def _raiz() -> Path:
    return Path(get_settings().UPLOADS_DIR).resolve()


def _diretorio_predio(predio_id: int) -> Path:
    diretorio = _raiz() / "despesas" / str(predio_id)
    diretorio.mkdir(parents=True, exist_ok=True)
    return diretorio


def salvar_documento(predio_id: int, nome_original: str, conteudo: bytes) -> str:
    """Salva `conteudo` em disco e devolve o `documento_url` estável a
    persistir em `DespesaLancamento.documento_url` - o caminho da API
    (relativo, sem o host) que serve o arquivo de volta, ver
    `GET /despesas/documentos/{predio_id}/{nome_arquivo}` - nunca o caminho
    absoluto do disco, que pode mudar entre ambientes."""
    extensao = Path(nome_original).suffix.lstrip(".").lower() or "bin"
    nome_arquivo = f"{uuid.uuid4().hex}.{extensao}"
    (_diretorio_predio(predio_id) / nome_arquivo).write_bytes(conteudo)
    return f"despesas/documentos/{predio_id}/{nome_arquivo}"


def caminho_documento(predio_id: int, nome_arquivo: str) -> Path | None:
    """Resolve `nome_arquivo` (só o nome, nunca um caminho) para o arquivo
    real em disco. Devolve None se o nome tiver formato inesperado (possível
    tentativa de path traversal) ou se o arquivo não existir."""
    if not _NOME_ARQUIVO_RE.match(nome_arquivo):
        return None
    caminho = _diretorio_predio(predio_id) / nome_arquivo
    if not caminho.is_file():
        return None
    return caminho
