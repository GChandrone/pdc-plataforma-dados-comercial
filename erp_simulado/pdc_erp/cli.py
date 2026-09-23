"""Linha de comando do ERP simulado: pdc-erp carga-inicial | simular."""

from __future__ import annotations

import argparse
import json
import os
import random
from datetime import date
from pathlib import Path

from . import carga_inicial, simulador
from .conexao import conectar


def carregar_config(caminho: str | None = None) -> dict:
    arquivo = Path(caminho or os.environ.get("ERP_CONFIG", "conf/simulador.json"))
    return json.loads(arquivo.read_text(encoding="utf-8"))


def _rng(config: dict, semente: int | None) -> random.Random:
    return random.Random(semente if semente is not None else config.get("semente"))


def executar_carga_inicial(caminho_config: str | None = None, semente: int | None = None) -> dict:
    config = carregar_config(caminho_config)
    with conectar() as conn:
        return carga_inicial.executar(conn, config, _rng(config, semente))


def executar_simulacao(caminho_config: str | None = None, semente: int | None = None,
                       hoje: date | None = None) -> dict:
    config = carregar_config(caminho_config)
    with conectar() as conn:
        return simulador.executar(conn, config, _rng(config, semente), hoje)


def main() -> None:
    parser = argparse.ArgumentParser(prog="pdc-erp", description="ERP Protheus simulado do projeto PDC")
    parser.add_argument("comando", choices=["carga-inicial", "simular"])
    parser.add_argument("--config", help="Caminho do simulador.json (padrão: ERP_CONFIG ou conf/simulador.json)")
    parser.add_argument("--semente", type=int, help="Semente aleatória (execuções reprodutíveis)")
    parser.add_argument("--data", type=date.fromisoformat, help="Data da movimentação (AAAA-MM-DD)")
    args = parser.parse_args()
    if args.comando == "carga-inicial":
        resumo = executar_carga_inicial(args.config, args.semente)
    else:
        resumo = executar_simulacao(args.config, args.semente, args.data)
    print(json.dumps(resumo, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
