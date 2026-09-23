"""Simulador da movimentação diária do Protheus em cada empresa e filial.

A cada execução: inclui pedidos, altera parte dos pedidos em aberto (quantidade, preço ou faturamento),
exclui logicamente alguns pedidos (D_E_L_E_T_ = '*' e R_E_C_D_E_L_ = R_E_C_N_O_) e, ocasionalmente,
inclui ou altera cadastros. O S_T_A_M_P_ é atualizado pelo trigger do banco, não por este código.
Nunca exclui fisicamente nem reutiliza R_E_C_N_O_.
"""

from __future__ import annotations

import random
from collections import Counter
from datetime import date
from decimal import Decimal

import psycopg

from . import banco
from .carga_inicial import empresas
from .dados import gerar_cliente
from .pedidos import gerar_pedido
from .regras import numero_nota, proximo_codigo, tabela, valor_item


def _movimentar_cadastros(cur, config: dict, rng: random.Random, empresa: str, resumo: Counter) -> None:
    t_sa1, t_sa3 = tabela("sa1", empresa), tabela("sa3", empresa)
    vendedores = [v[0].strip() for v in banco.consultar(cur, t_sa3, ["a3_cod"])]
    if rng.random() < config["pct_novo_cliente"]:
        cur.execute(
            banco.sql.SQL("SELECT max(a1_cod) FROM {}").format(banco.sql.Identifier(t_sa1))
        )
        codigo = proximo_codigo(cur.fetchone()[0])
        banco.inserir(cur, t_sa1, banco.COLS_SA1, [gerar_cliente(rng, codigo, vendedores)])
        resumo["clientes_incluidos"] += 1
    if rng.random() < config["pct_alteracao_cadastro"]:
        clientes = banco.consultar(cur, t_sa1, ["r_e_c_n_o_"])
        if clientes:
            recno = rng.choice(clientes)[0]
            banco.executar(cur, "UPDATE {} SET a1_vend = %s WHERE r_e_c_n_o_ = %s", t_sa1,
                           (rng.choice(vendedores), recno))
            resumo["clientes_alterados"] += 1


def _movimentar_pedidos(cur, config: dict, rng: random.Random, unidade: dict, hoje: date, resumo: Counter) -> None:
    empresa, filial = unidade["empresa"], unidade["filial"]
    t_sc5, t_sc6 = tabela("sc5", empresa), tabela("sc6", empresa)

    abertos = [linha[0] for linha in banco.consultar(
        cur, t_sc5, ["c5_num"], "d_e_l_e_t_ = ' ' AND c5_filial = %s AND trim(c5_nota) = ''", (filial,)
    )]
    rng.shuffle(abertos)
    n_exc = round(len(abertos) * config["pct_exclusao"])
    n_fat = round(len(abertos) * config["pct_faturamento"])
    n_alt = round(len(abertos) * config["pct_alteracao"])
    excluir = abertos[:n_exc]
    faturar = abertos[n_exc:n_exc + n_fat]
    alterar = abertos[n_exc + n_fat:n_exc + n_fat + n_alt]

    for numero in excluir:
        banco.executar(cur, "UPDATE {} SET d_e_l_e_t_ = '*', r_e_c_d_e_l_ = r_e_c_n_o_ "
                       "WHERE c5_filial = %s AND c5_num = %s AND d_e_l_e_t_ = ' '", t_sc5, (filial, numero))
        banco.executar(cur, "UPDATE {} SET d_e_l_e_t_ = '*', r_e_c_d_e_l_ = r_e_c_n_o_ "
                       "WHERE c6_filial = %s AND c6_num = %s AND d_e_l_e_t_ = ' '", t_sc6, (filial, numero))
    resumo["pedidos_excluidos"] += len(excluir)

    for numero in faturar:
        nota = numero_nota(rng)
        banco.executar(cur, "UPDATE {} SET c6_qtdent = c6_qtdven, c6_nota = %s "
                       "WHERE c6_filial = %s AND c6_num = %s AND d_e_l_e_t_ = ' '", t_sc6, (nota, filial, numero))
        banco.executar(cur, "UPDATE {} SET c5_nota = %s WHERE c5_filial = %s AND c5_num = %s AND d_e_l_e_t_ = ' '",
                       t_sc5, (nota, filial, numero))
    resumo["pedidos_faturados"] += len(faturar)

    for numero in alterar:
        itens = banco.consultar(cur, t_sc6, ["r_e_c_n_o_", "c6_prcven"],
                                "d_e_l_e_t_ = ' ' AND c6_filial = %s AND c6_num = %s", (filial, numero))
        if not itens:
            continue
        recno, preco = rng.choice(itens)
        quantidade = Decimal(rng.randint(1, 50))
        banco.executar(cur, "UPDATE {} SET c6_qtdven = %s, c6_valor = %s WHERE r_e_c_n_o_ = %s", t_sc6,
                       (quantidade, valor_item(quantidade, Decimal(preco)), recno))
        resumo["itens_alterados"] += 1

    clientes = [(c[0].strip(), c[1].strip(), c[2].strip()) for c in banco.consultar(
        cur, tabela("sa1", empresa), ["a1_cod", "a1_loja", "a1_vend"], "d_e_l_e_t_ = ' ' AND a1_msblql <> '1'"
    )]
    produtos = [(p[0].strip(), p[1]) for p in banco.consultar(cur, tabela("sb1", empresa), ["b1_cod", "b1_prv1"])]
    cur.execute(banco.sql.SQL("SELECT max(c5_num) FROM {} WHERE c5_filial = %s").format(banco.sql.Identifier(t_sc5)),
                (filial,))
    numero = cur.fetchone()[0]
    media = unidade["pedidos_por_dia"]
    cabecalhos, novos_itens = [], []
    for _ in range(rng.randint(max(0, media - 2), media + 2)):
        numero = proximo_codigo(numero)
        cabecalho, linhas = gerar_pedido(
            rng, filial, numero, hoje, clientes, produtos,
            config["itens_por_pedido"]["min"], config["itens_por_pedido"]["max"], faturado=False,
        )
        cabecalhos.append(cabecalho)
        novos_itens.extend(linhas)
    banco.inserir(cur, t_sc5, banco.COLS_SC5, cabecalhos)
    banco.inserir(cur, t_sc6, banco.COLS_SC6, novos_itens)
    resumo["pedidos_incluidos"] += len(cabecalhos)


def executar(conn: psycopg.Connection, config: dict, rng: random.Random, hoje: date | None = None) -> dict:
    hoje = hoje or date.today()
    resumo: Counter = Counter()
    with conn.cursor() as cur:
        for empresa in empresas(config):
            _movimentar_cadastros(cur, config, rng, empresa, resumo)
        for unidade in config["unidades"]:
            _movimentar_pedidos(cur, config, rng, unidade, hoje, resumo)
    conn.commit()
    return dict(resumo)
