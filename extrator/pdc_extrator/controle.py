"""Acesso à tabela de controle controle.ingestion_control (IngestionControl)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import psycopg


@dataclass(frozen=True)
class ItemControle:
    tabela: str
    empresa: str
    tipo_carga: str
    ultimo_watermark: datetime | None


def sincronizar(conn: psycopg.Connection, configuracao: dict) -> int:
    """Aplica o conf/ingestao.json na tabela de controle preservando os watermarks. Retorna itens ativos."""
    chaves = []
    with conn.cursor() as cur:
        for item in configuracao["tabelas"]:
            for empresa in item["empresas"]:
                chaves.append((item["tabela"], empresa))
                cur.execute(
                    """
                    INSERT INTO controle.ingestion_control (tabela, empresa, tipo_carga, ativo)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (tabela, empresa)
                    DO UPDATE SET tipo_carga = EXCLUDED.tipo_carga, ativo = EXCLUDED.ativo
                    """,
                    (item["tabela"], empresa, item["tipo_carga"], item.get("ativo", True)),
                )
        cur.execute("SELECT tabela, empresa FROM controle.ingestion_control")
        for tabela, empresa in cur.fetchall():
            if (tabela, empresa.strip()) not in chaves:
                cur.execute(
                    "UPDATE controle.ingestion_control SET ativo = false WHERE tabela = %s AND empresa = %s",
                    (tabela, empresa),
                )
    conn.commit()
    return len(chaves)


def listar_ativos(conn: psycopg.Connection) -> list[ItemControle]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT tabela, empresa, tipo_carga, ultimo_watermark FROM controle.ingestion_control "
            "WHERE ativo ORDER BY tabela, empresa"
        )
        return [ItemControle(t, e.strip(), tipo, wm) for t, e, tipo, wm in cur.fetchall()]


def registrar_sucesso(conn: psycopg.Connection, item: ItemControle, watermark: datetime | None, qtd: int) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE controle.ingestion_control
               SET ultimo_watermark = %s, status_ultima_carga = 'SUCESSO',
                   data_ultima_execucao = timezone('UTC', now()), qtd_ultima_carga = %s
             WHERE tabela = %s AND empresa = %s
            """,
            (watermark, qtd, item.tabela, item.empresa),
        )
    conn.commit()


def registrar_falha(conn: psycopg.Connection, item: ItemControle) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE controle.ingestion_control
               SET status_ultima_carga = 'FALHA', data_ultima_execucao = timezone('UTC', now())
             WHERE tabela = %s AND empresa = %s
            """,
            (item.tabela, item.empresa),
        )
    conn.commit()
