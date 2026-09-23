"""Integração: PostgreSQL real (service container no CI) + carga inicial + simulador + extrator."""

import os
import random
from datetime import date
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

psycopg = pytest.importorskip("psycopg")
pq = pytest.importorskip("pyarrow.parquet")

from pdc_erp import carga_inicial, simulador  # noqa: E402
from pdc_extrator import controle, extracao  # noqa: E402
from pdc_extrator.destino import DestinoLocal  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
EMPRESAS = ["01", "05", "08", "13"]
CONFIG_INGESTAO = {"tabelas": [
    {"tabela": t, "tipo_carga": tipo, "ativo": True, "empresas": EMPRESAS}
    for t, tipo in [("sc5", "INCREMENTAL"), ("sc6", "INCREMENTAL"), ("sa1", "FULL"), ("sa3", "FULL"), ("sb1", "FULL")]
]}
CONFIG_SIMULADOR = {
    "semente": None,
    "unidades": [
        {"empresa": "01", "filial": "01", "nome": "Matriz", "pedidos_por_dia": 3},
        {"empresa": "05", "filial": "01", "nome": "Acessórios", "pedidos_por_dia": 3},
        {"empresa": "08", "filial": "01", "nome": "Nordeste", "pedidos_por_dia": 3},
        {"empresa": "08", "filial": "02", "nome": "Centro-Oeste", "pedidos_por_dia": 3},
        {"empresa": "13", "filial": "01", "nome": "TopMax", "pedidos_por_dia": 3},
    ],
    "itens_por_pedido": {"min": 1, "max": 3},
    "pct_alteracao": 0.3, "pct_faturamento": 0.3, "pct_exclusao": 0.1,
    "pct_novo_cliente": 1.0, "pct_alteracao_cadastro": 1.0,
    "carga_inicial": {"clientes_por_empresa": 5, "vendedores_por_empresa": 2, "produtos_por_empresa": 6,
                      "dias_historico": 3},
}


@pytest.fixture(scope="module")
def conn():
    if not os.environ.get("PG_HOST"):
        pytest.skip("PG_HOST não definido; teste de integração ignorado.")
    conexao = psycopg.connect(host=os.environ["PG_HOST"], port=int(os.environ.get("PG_PORT", "5432")),
                              dbname=os.environ["PG_DB"], user=os.environ["PG_USER"],
                              password=os.environ["PG_PASSWORD"])
    with conexao.cursor() as cur:
        for ddl in sorted((RAIZ / "erp_simulado" / "ddl").glob("*.sql")):
            cur.execute(ddl.read_text(encoding="utf-8"))
        tabelas = [f"{t}{e}0" for t in ["sc5", "sc6", "sa1", "sa3", "sb1"] for e in EMPRESAS]
        cur.execute("TRUNCATE " + ", ".join(tabelas) + ", controle.ingestion_control RESTART IDENTITY")
    conexao.commit()
    yield conexao
    conexao.close()


def _linhas(base: Path, lote: str, alias: str) -> list[tuple]:
    arquivos = base.glob(f"{alias}/empresa=*/{alias}_{lote}.parquet")
    return [(arquivo.parent.name.split("=")[1], recno)
            for arquivo in arquivos for recno in pq.read_table(arquivo).column("r_e_c_n_o_").to_pylist()]


def _todos(conn, alias: str) -> set[tuple]:
    resultado = set()
    with conn.cursor() as cur:
        for empresa in EMPRESAS:
            cur.execute(f"SELECT r_e_c_n_o_ FROM {alias}{empresa}0")  # nosec B608 - nomes fixos do teste
            resultado |= {(empresa, r[0]) for r in cur.fetchall()}
    conn.rollback()
    return resultado


def test_extracao_incremental_sem_perda_nem_duplicidade(conn, tmp_path):
    controle.sincronizar(conn, CONFIG_INGESTAO)
    carga_inicial.executar(conn, CONFIG_SIMULADOR, random.Random(42), hoje=date(2026, 10, 13))
    destino = DestinoLocal(tmp_path)

    # 1ª execução: carga completa de todas as tabelas
    r1 = extracao.executar(conn, destino, overlap_minutos=0, lote="20261013T060000Z")
    assert not r1.falhas
    assert set(_linhas(tmp_path, r1.lote, "sc5")) == _todos(conn, "sc5")
    assert (tmp_path / "_manifest" / f"{r1.lote}.json").exists()

    # 2ª execução sem movimentação: incrementais não trazem nada; FULL traz o cadastro completo
    r2 = extracao.executar(conn, destino, overlap_minutos=0, lote="20261013T070000Z")
    por_tabela = {(i["tabela"], i["empresa"]): i["registros"] for i in r2.itens}
    assert all(por_tabela[("sc5", e)] == 0 and por_tabela[("sc6", e)] == 0 for e in EMPRESAS)
    assert all(por_tabela[("sa1", e)] > 0 for e in EMPRESAS)

    # Movimentação do ERP e 3ª execução: somente o que mudou, sem perder nenhum registro
    simulador.executar(conn, CONFIG_SIMULADOR, random.Random(7), hoje=date(2026, 10, 14))
    r3 = extracao.executar(conn, destino, overlap_minutos=0, lote="20261014T060000Z")
    novos = _linhas(tmp_path, r3.lote, "sc5")
    assert novos, "a movimentação deveria gerar registros incrementais"
    assert len(novos) == len(set(novos))
    assert set(_linhas(tmp_path, r1.lote, "sc5")) | set(novos) == _todos(conn, "sc5")
