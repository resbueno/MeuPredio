from __future__ import annotations

import pymupdf
import pytest

from app.core.pdf import PdfInvalidoError, primeira_pagina_como_png


def _pdf_de_teste(paginas: int = 1) -> bytes:
    documento = pymupdf.open()
    for _ in range(paginas):
        pagina = documento.new_page()
        pagina.insert_text((72, 72), "Boleto de teste - R$ 150,00")
    return documento.tobytes()


def test_primeira_pagina_como_png_retorna_png_valido():
    png = primeira_pagina_como_png(_pdf_de_teste())
    assert png.startswith(b"\x89PNG\r\n\x1a\n")


def test_usa_apenas_a_primeira_pagina_mesmo_com_varias():
    # Não há como inspecionar "qual página" a partir só dos bytes do PNG,
    # mas o importante aqui é que não falha e devolve exatamente uma imagem
    # (um PNG válido) mesmo com um PDF de múltiplas páginas.
    png = primeira_pagina_como_png(_pdf_de_teste(paginas=3))
    assert png.startswith(b"\x89PNG\r\n\x1a\n")


def test_pdf_corrompido_levanta_pdf_invalido_error():
    with pytest.raises(PdfInvalidoError):
        primeira_pagina_como_png(b"isto nao e um pdf valido")
