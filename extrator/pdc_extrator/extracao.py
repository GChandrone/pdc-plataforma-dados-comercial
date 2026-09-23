"""Execução da extração: lê a IngestionControl, extrai cada tabela/empresa ativa e grava Parquet + manifesto."""

from __future__ import annotations

import io
import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime

import psycopg
import pyarrow as pa
import pyarrow.parquet as pq

from . import controle
from .consulta import montar_consulta, proximo_watermark
from .destino import Destino

log = logging.getLogger(__name__)


@dataclass
class Resumo:
    lote: str
    itens: list[dict] = field(default_factory=list)
    falhas: list[dict] = field(default_factory=list)


def gerar_lote(agora: datetime | None = None) -> str:
    return (agora or datetime.now(UTC)).strftime("%Y%m%dT%H%M%SZ")


def para_parquet(colunas: list[str], linhas: list[tuple], lote: str) -> bytes:
    dados = {coluna: [linha[i] for linha in linhas] for i, coluna in enumerate(colunas)}
    dados["_lote"] = [lote] * len(linhas)
    buffer = io.BytesIO()
    pq.write_table(pa.table(dados), buffer)
    return buffer.getvalue()


def executar(conn: psycopg.Connection, destino: Destino, overlap_minutos: int = 10,
             lote: str | None = None) -> Resumo:
    resumo = Resumo(lote=lote or gerar_lote())
    for item in controle.listar_ativos(conn):
        try:
            consulta, parametros = montar_consulta(item.tabela, item.empresa, item.tipo_carga,
                                                   item.ultimo_watermark, overlap_minutos)
            with conn.cursor() as cur:
                cur.execute(consulta, parametros)
                colunas = [d.name for d in cur.description]
                linhas = cur.fetchall()
            conn.rollback()  # encerra a transação de leitura

            arquivo = None
            if linhas:
                arquivo = f"{item.tabela}/empresa={item.empresa}/{item.tabela}_{resumo.lote}.parquet"
                destino.gravar(arquivo, para_parquet(colunas, linhas, resumo.lote))

            watermark = item.ultimo_watermark
            if item.tipo_carga == "INCREMENTAL":
                indice = colunas.index("s_t_a_m_p_")
                watermark = proximo_watermark(item.ultimo_watermark, [linha[indice] for linha in linhas])
            # O watermark só avança depois que o arquivo foi gravado com sucesso.
            controle.registrar_sucesso(conn, item, watermark, len(linhas))
            resumo.itens.append({"tabela": item.tabela, "empresa": item.empresa, "tipo_carga": item.tipo_carga,
                                 "registros": len(linhas), "arquivo": arquivo})
            log.info("%s/%s: %s registros", item.tabela, item.empresa, len(linhas))
        except Exception as erro:  # registra a falha e segue com as demais tabelas
            conn.rollback()
            controle.registrar_falha(conn, item)
            resumo.falhas.append({"tabela": item.tabela, "empresa": item.empresa, "erro": str(erro)})
            log.exception("Falha na extração de %s/%s", item.tabela, item.empresa)

    manifesto = {"lote": resumo.lote, "gerado_em": datetime.now(UTC).isoformat(), "itens": resumo.itens}
    destino.gravar(f"_manifest/{resumo.lote}.json", json.dumps(manifesto, ensure_ascii=False).encode("utf-8"))
    return resumo
