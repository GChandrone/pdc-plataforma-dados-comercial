"""Carga inicial do ERP simulado: cadastros por empresa e histórico de pedidos."""

from __future__ import annotations

import random
from datetime import date, timedelta

import psycopg

from . import banco
from .dados import gerar_cliente, gerar_produtos, gerar_vendedores
from .pedidos import gerar_pedido
from .regras import proximo_codigo, tabela


def empresas(config: dict) -> list[str]:
    return sorted({u["empresa"] for u in config["unidades"]})


def executar(conn: psycopg.Connection, config: dict, rng: random.Random, hoje: date | None = None) -> dict:
    hoje = hoje or date.today()
    parametros = config["carga_inicial"]
    resumo: dict[str, int] = {}
    with conn.cursor() as cur:
        for empresa in empresas(config):
            if banco.contar(cur, tabela("sa1", empresa)) > 0:
                raise RuntimeError(f"Empresa {empresa} já possui cadastros; carga inicial não é repetida.")

        cadastros = {}
        for empresa in empresas(config):
            vendedores = gerar_vendedores(rng, parametros["vendedores_por_empresa"])
            produtos = gerar_produtos(rng, parametros["produtos_por_empresa"])
            codigos_vendedor = [v[1] for v in vendedores]
            clientes, codigo = [], None
            for _ in range(parametros["clientes_por_empresa"]):
                codigo = proximo_codigo(codigo)
                clientes.append(gerar_cliente(rng, codigo, codigos_vendedor))
            banco.inserir(cur, tabela("sa3", empresa), banco.COLS_SA3, vendedores)
            banco.inserir(cur, tabela("sb1", empresa), banco.COLS_SB1, produtos)
            banco.inserir(cur, tabela("sa1", empresa), banco.COLS_SA1, clientes)
            cadastros[empresa] = ([(c[1], c[2], c[8]) for c in clientes], [(p[1], p[6]) for p in produtos])
            resumo[f"cadastros_{empresa}"] = len(vendedores) + len(produtos) + len(clientes)

        for unidade in config["unidades"]:
            empresa, filial = unidade["empresa"], unidade["filial"]
            clientes, produtos = cadastros[empresa]
            cabecalhos, itens, numero = [], [], None
            media = unidade["pedidos_por_dia"]
            for dias_atras in range(parametros["dias_historico"], 0, -1):
                emissao = hoje - timedelta(days=dias_atras)
                probabilidade_faturado = 0.9 if dias_atras > 30 else 0.3
                for _ in range(rng.randint(max(0, media - 2), media + 2)):
                    numero = proximo_codigo(numero)
                    cabecalho, linhas = gerar_pedido(
                        rng, filial, numero, emissao, clientes, produtos,
                        config["itens_por_pedido"]["min"], config["itens_por_pedido"]["max"],
                        faturado=rng.random() < probabilidade_faturado,
                    )
                    cabecalhos.append(cabecalho)
                    itens.extend(linhas)
            banco.inserir(cur, tabela("sc5", empresa), banco.COLS_SC5, cabecalhos)
            banco.inserir(cur, tabela("sc6", empresa), banco.COLS_SC6, itens)
            resumo[f"pedidos_{unidade['nome']}"] = len(cabecalhos)
    conn.commit()
    return resumo
