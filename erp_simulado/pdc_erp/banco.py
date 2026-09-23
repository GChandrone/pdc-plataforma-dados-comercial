"""Operações de banco do ERP simulado. Nomes de tabela sempre via psycopg.sql.Identifier."""

from __future__ import annotations

from psycopg import Cursor, sql

COLS_SC5 = ["c5_filial", "c5_num", "c5_tipo", "c5_cliente", "c5_lojacli", "c5_vend1", "c5_emissao", "c5_nota"]
COLS_SC6 = ["c6_filial", "c6_num", "c6_item", "c6_produto", "c6_qtdven", "c6_prcven", "c6_valor", "c6_qtdent",
            "c6_nota"]
COLS_SA1 = ["a1_filial", "a1_cod", "a1_loja", "a1_nome", "a1_nreduz", "a1_est", "a1_mun", "a1_cgc", "a1_vend",
            "a1_msblql"]
COLS_SA3 = ["a3_filial", "a3_cod", "a3_nome"]
COLS_SB1 = ["b1_filial", "b1_cod", "b1_desc", "b1_tipo", "b1_um", "b1_grupo", "b1_prv1"]


def inserir(cur: Cursor, tabela: str, colunas: list[str], linhas: list[tuple]) -> None:
    if not linhas:
        return
    comando = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
        sql.Identifier(tabela),
        sql.SQL(", ").join(map(sql.Identifier, colunas)),
        sql.SQL(", ").join(sql.Placeholder() * len(colunas)),
    )
    cur.executemany(comando, linhas)


def contar(cur: Cursor, tabela: str) -> int:
    cur.execute(sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(tabela)))
    return cur.fetchone()[0]


def consultar(cur: Cursor, tabela: str, colunas: list[str], filtro: str = "d_e_l_e_t_ = ' '",
              parametros: tuple = ()) -> list[tuple]:
    # O filtro é sempre uma constante definida no código (nunca entrada externa); valores vão por parâmetro.
    comando = sql.SQL("SELECT {} FROM {} WHERE " + filtro).format(  # nosec B608 - filtro é constante do código
        sql.SQL(", ").join(map(sql.Identifier, colunas)), sql.Identifier(tabela)
    )
    cur.execute(comando, parametros)
    return cur.fetchall()


def executar(cur: Cursor, modelo: str, tabela: str, parametros: tuple = ()) -> int:
    """Executa um comando com {} no lugar do nome da tabela; valores sempre por parâmetro."""
    cur.execute(sql.SQL(modelo).format(sql.Identifier(tabela)), parametros)
    return cur.rowcount
