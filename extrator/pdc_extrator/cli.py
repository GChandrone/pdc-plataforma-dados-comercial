"""Linha de comando do extrator: pdc-extrator sincronizar-config | executar."""

from __future__ import annotations

import argparse
import json
import logging
import os
from dataclasses import asdict
from pathlib import Path

import psycopg

from . import controle, extracao
from .destino import DestinoLocal, DestinoVolume


def conectar() -> psycopg.Connection:
    return psycopg.connect(
        host=os.environ.get("PG_HOST", "localhost"),
        port=int(os.environ.get("PG_PORT", "5432")),
        dbname=os.environ.get("PG_DB", "erp_protheus"),
        user=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
    )


def sincronizar_configuracao(caminho: str | None = None) -> int:
    arquivo = Path(caminho or os.environ.get("INGESTAO_CONFIG", "conf/ingestao.json"))
    with conectar() as conn:
        return controle.sincronizar(conn, json.loads(arquivo.read_text(encoding="utf-8")))


def executar_extracao() -> dict:
    """Executa a extração; levanta erro se alguma tabela falhar (para a DAG não acionar o Databricks)."""
    saida_local = os.environ.get("LOCAL_OUTPUT_DIR")
    destino = DestinoLocal(saida_local) if saida_local else DestinoVolume(
        os.environ.get("LANDING_PATH", "/Volumes/landing/protheus/arquivos"))
    with conectar() as conn:
        resumo = extracao.executar(conn, destino, int(os.environ.get("OVERLAP_MINUTES", "10")))
    if resumo.falhas:
        raise RuntimeError(f"Extração com falhas: {resumo.falhas}")
    return asdict(resumo)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(prog="pdc-extrator", description="Extrator incremental do PDC")
    parser.add_argument("comando", choices=["sincronizar-config", "executar"])
    parser.add_argument("--arquivo", help="Caminho do ingestao.json (padrão: INGESTAO_CONFIG ou conf/ingestao.json)")
    args = parser.parse_args()
    if args.comando == "sincronizar-config":
        print(f"{sincronizar_configuracao(args.arquivo)} itens de controle sincronizados.")
    else:
        print(json.dumps(executar_extracao(), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
