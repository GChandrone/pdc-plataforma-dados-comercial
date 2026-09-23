"""Montagem das consultas de extração e cálculo do watermark (funções puras)."""

from __future__ import annotations

import re
from datetime import datetime, timedelta

from psycopg import sql

_ALIAS = re.compile(r"^[a-z]{2}[0-9a-z]$")
_EMPRESA = re.compile(r"^\d{2}$")
TIPOS_CARGA = ("FULL", "INCREMENTAL")


def tabela_fisica(alias: str, empresa: str) -> str:
    """Nome físico no padrão do Protheus (<alias><empresa>0), validado contra injeção."""
    if not _ALIAS.fullmatch(alias or "") or not _EMPRESA.fullmatch(empresa or ""):
        raise ValueError(f"Tabela ou empresa inválida: {alias!r}/{empresa!r}")
    return f"{alias}{empresa}0"


def montar_consulta(alias: str, empresa: str, tipo_carga: str, watermark: datetime | None,
                    overlap_minutos: int) -> tuple[sql.Composed, tuple]:
    """FULL (ou primeira carga incremental) lê a tabela inteira; INCREMENTAL lê S_T_A_M_P_ > watermark - overlap.

    A janela de overlap protege contra transações gravadas durante a extração anterior; as duplicidades
    geradas por ela são eliminadas na Silver (MERGE por empresa + R_E_C_N_O_ com o maior S_T_A_M_P_).
    """
    if tipo_carga not in TIPOS_CARGA:
        raise ValueError(f"Tipo de carga inválido: {tipo_carga!r}")
    tabela = sql.Identifier(tabela_fisica(alias, empresa))
    if tipo_carga == "FULL" or watermark is None:
        return sql.SQL("SELECT * FROM {} ORDER BY r_e_c_n_o_").format(tabela), ()
    desde = watermark - timedelta(minutes=overlap_minutos)
    consulta = sql.SQL("SELECT * FROM {} WHERE s_t_a_m_p_ > %s ORDER BY s_t_a_m_p_, r_e_c_n_o_").format(tabela)
    return consulta, (desde,)


def proximo_watermark(atual: datetime | None, stamps: list[datetime | None]) -> datetime | None:
    """Novo watermark = maior S_T_A_M_P_ extraído; nunca retrocede."""
    validos = [s for s in stamps if s is not None]
    if not validos:
        return atual
    maior = max(validos)
    return maior if atual is None or maior > atual else atual
