"""Regras de negócio do ERP simulado (funções puras, cobertas por testes unitários)."""

from __future__ import annotations

import random
import re
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

ALIASES = ("sc5", "sc6", "sa1", "sa3", "sb1")
FILIAL_COMPARTILHADA = "  "  # cadastros compartilhados entre filiais (xFilial em branco)
_CENTAVOS = Decimal("0.01")


def tabela(alias: str, empresa: str) -> str:
    """Nome físico da tabela no padrão do Protheus: <alias><empresa>0 (ex.: sc5080)."""
    if alias not in ALIASES or not re.fullmatch(r"\d{2}", empresa or ""):
        raise ValueError(f"Tabela inválida: {alias!r}/{empresa!r}")
    return f"{alias}{empresa}0"


def valor_item(quantidade: Decimal, preco: Decimal) -> Decimal:
    """C6_VALOR = quantidade × preço, arredondado em centavos."""
    return (quantidade * preco).quantize(_CENTAVOS, rounding=ROUND_HALF_UP)


def proximo_codigo(atual: str | None, tamanho: int = 6) -> str:
    """Próximo código sequencial com zeros à esquerda (C5_NUM, A1_COD...)."""
    numero = int(atual.strip()) + 1 if atual and atual.strip() else 1
    return str(numero).zfill(tamanho)


def data_protheus(valor: date) -> str:
    """Datas no Protheus são texto AAAAMMDD."""
    return valor.strftime("%Y%m%d")


def numero_nota(rng: random.Random) -> str:
    return str(rng.randint(1, 999_999_999)).zfill(9)


def _digitos_cnpj(base: list[int]) -> tuple[int, int]:
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6] + pesos1
    resto = sum(d * p for d, p in zip(base, pesos1, strict=True)) % 11
    d1 = 0 if resto < 2 else 11 - resto
    resto = sum(d * p for d, p in zip(base + [d1], pesos2, strict=True)) % 11
    d2 = 0 if resto < 2 else 11 - resto
    return d1, d2


def cnpj_valido(numero: str) -> bool:
    if not re.fullmatch(r"\d{14}", numero or ""):
        return False
    digitos = [int(c) for c in numero]
    return tuple(digitos[12:]) == _digitos_cnpj(digitos[:12])


def cnpj_ficticio(rng: random.Random) -> str:
    """CNPJ com formato válido e dígito verificador propositalmente INVÁLIDO (nunca coincide com um real)."""
    base = [rng.randint(0, 9) for _ in range(12)]
    d1, d2 = _digitos_cnpj(base)
    return "".join(map(str, base)) + str(d1) + str((d2 + 1) % 10)
