"""Geração de pedidos de venda (SC5 + SC6)."""

from __future__ import annotations

import random
from datetime import date
from decimal import Decimal

from .regras import data_protheus, numero_nota, valor_item


def gerar_pedido(
    rng: random.Random,
    filial: str,
    numero: str,
    emissao: date,
    clientes: list[tuple[str, str, str]],
    produtos: list[tuple[str, Decimal]],
    itens_min: int,
    itens_max: int,
    faturado: bool,
) -> tuple[tuple, list[tuple]]:
    """Retorna (cabeçalho SC5, itens SC6). clientes: (código, loja, vendedor); produtos: (código, preço)."""
    cliente, loja, vendedor = rng.choice(clientes)
    nota = numero_nota(rng) if faturado else " "
    cabecalho = (filial, numero, "N", cliente, loja, vendedor, data_protheus(emissao), nota)
    quantidade_itens = min(rng.randint(itens_min, itens_max), len(produtos))
    itens = []
    for indice, (produto, preco_base) in enumerate(rng.sample(produtos, k=quantidade_itens), start=1):
        quantidade = Decimal(rng.randint(1, 50))
        preco = (Decimal(preco_base) * Decimal(str(round(rng.uniform(0.95, 1.05), 4)))).quantize(Decimal("0.01"))
        entregue = quantidade if faturado else Decimal(0)
        itens.append((filial, numero, str(indice).zfill(2), produto, quantidade, preco,
                      valor_item(quantidade, preco), entregue, nota))
    return cabecalho, itens
