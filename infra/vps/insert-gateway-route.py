#!/usr/bin/env python3
"""Insere o bloco de rota do MeuPredio no nginx.conf do gateway compartilhado,
antes do "location = /" da raiz. So roda uma vez, e falha (sem tocar no
arquivo) se a rota ja existir ou se o ponto de insercao nao for encontrado.
"""
import sys

GATEWAY_CONF = "/root/gateway/nginx.conf"
SNIPPET_FILE = "/root/meupredio/infra/vps/gateway-location-snippet.conf"
ANCHOR = "        location = / {\n"

with open(GATEWAY_CONF, "r", encoding="utf-8") as f:
    conf = f.read()

if "/meupredio/" in conf:
    print("ABORTADO: '/meupredio/' ja aparece em nginx.conf - nao vou duplicar.")
    sys.exit(1)

with open(SNIPPET_FILE, "r", encoding="utf-8") as f:
    snippet_lines = f.read().splitlines(keepends=True)

# Pula o cabecalho de comentario explicativo do arquivo de snippet (ate a
# primeira linha em branco), mantendo so o bloco de config nginx de fato.
blank_idx = snippet_lines.index("\n")
snippet_code = "".join(snippet_lines[blank_idx + 1:])

if ANCHOR not in conf:
    print("ABORTADO: ponto de insercao (location = /) nao encontrado.")
    sys.exit(1)

new_conf = conf.replace(ANCHOR, snippet_code + "\n" + ANCHOR, 1)

with open(GATEWAY_CONF, "w", encoding="utf-8") as f:
    f.write(new_conf)

print("OK: rota /meupredio/ inserida em", GATEWAY_CONF)
