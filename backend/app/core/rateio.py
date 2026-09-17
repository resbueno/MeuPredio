"""Cálculo do motor de rateio: divide um valor entre unidades por peso,
sem perder nem sobrar centavo (método dos maiores restos)."""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal


def calcular_rateio(valor: Decimal, pesos: list[tuple[int, Decimal]]) -> dict[int, Decimal]:
    """Distribui `valor` entre `pesos` (lista de `(unidade_id, peso)`,
    pesos > 0) proporcionalmente a cada peso sobre a soma total.

    Trabalha em centavos inteiros e usa o método dos maiores restos: cada
    unidade recebe o piso (`floor`) da sua fração exata, e os centavos que
    sobraram do arredondamento vão, um a um, para quem tinha o maior resto
    (empate desempatado por `unidade_id` crescente, para ser determinístico
    entre chamadas). Isso garante que a SOMA dos valores retornados é
    sempre exatamente igual a `valor` — nunca fica faltando nem sobrando
    centavo por causa de arredondamento por unidade.
    """
    valor_centavos = int(valor.scaleb(2).to_integral_value(rounding=ROUND_HALF_UP))
    peso_total = sum(peso for _, peso in pesos)

    exatos = [(unidade_id, (valor_centavos * peso) / peso_total) for unidade_id, peso in pesos]
    piso = {unidade_id: int(exato) for unidade_id, exato in exatos}
    restante = valor_centavos - sum(piso.values())

    ordenados = sorted(exatos, key=lambda item: (-(item[1] - piso[item[0]]), item[0]))
    for unidade_id, _ in ordenados[:restante]:
        piso[unidade_id] += 1

    return {unidade_id: Decimal(centavos) / 100 for unidade_id, centavos in piso.items()}
