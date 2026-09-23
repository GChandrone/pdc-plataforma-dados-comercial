"""Utilitários de segurança para montar nomes de objetos a partir de parâmetros."""

from __future__ import annotations

import re

_IDENTIFICADOR = re.compile(r"^[a-z][a-z0-9_]{0,62}$")
_TABELA_PROTHEUS = re.compile(r"^[a-z]{2}[0-9a-z]$")


def validar_identificador(valor: str) -> str:
    """Garante que um catálogo/schema recebido por parâmetro é um identificador simples (evita injeção de SQL)."""
    if not _IDENTIFICADOR.fullmatch(valor or ""):
        raise ValueError(f"Identificador inválido: {valor!r}")
    return valor


def validar_tabela_protheus(valor: str) -> str:
    """Valida um alias de tabela do Protheus (ex.: sc5, sa1)."""
    if not _TABELA_PROTHEUS.fullmatch(valor or ""):
        raise ValueError(f"Tabela do Protheus inválida: {valor!r}")
    return valor


def nome_tabela(catalogo: str, schema: str, tabela: str) -> str:
    """Monta catalogo.schema.tabela validando cada parte."""
    return ".".join(validar_identificador(parte) for parte in (catalogo, schema, tabela))
