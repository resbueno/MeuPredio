"""Conversão da primeira página de um PDF em imagem PNG.

Usado só pelo pipeline de OCR (`app/routers/despesas.py`): o modelo com
visão do Groq (ver `app/core/groq_ocr.py`) não aceita PDF como entrada,
apenas imagem - então quando o boleto é enviado em PDF, convertemos a
primeira página (onde o boleto normalmente está) para PNG antes de mandar
para a IA. O arquivo original enviado (PDF) continua sendo o que fica
salvo em disco/`documento_url` - a conversão é só para a chamada de OCR.
"""
from __future__ import annotations

import pymupdf


class PdfInvalidoError(ValueError):
    """PDF corrompido, protegido por senha, ou sem nenhuma página."""


def primeira_pagina_como_png(conteudo_pdf: bytes, *, dpi: int = 200) -> bytes:
    try:
        documento = pymupdf.Document(stream=conteudo_pdf, filetype="pdf")
    except Exception as exc:  # pymupdf levanta tipos variados para PDF corrompido/protegido
        raise PdfInvalidoError(
            "Nao foi possivel abrir o PDF - arquivo corrompido, protegido por senha ou invalido."
        ) from exc

    if documento.page_count == 0:
        raise PdfInvalidoError("O PDF nao tem nenhuma pagina.")

    pagina = documento.load_page(0)
    zoom = dpi / 72
    pixmap = pagina.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
    return pixmap.tobytes(output="png")
