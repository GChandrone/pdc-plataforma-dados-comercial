"""Descrições (COMMENT) das tabelas e colunas da Gold, publicadas no Unity Catalog."""

from __future__ import annotations

COMENTARIOS: dict[str, tuple[str, dict[str, str]]] = {
    "fato_pedido_venda": (
        "Pedidos de venda no grão item do pedido, sem registros excluídos logicamente. Fonte: SC5 e SC6.",
        {
            "cod_empresa": "Código da empresa no Protheus",
            "cod_filial": "Código da filial",
            "cod_pedido": "Número do pedido de venda (C5_NUM)",
            "cod_item": "Item do pedido (C6_ITEM)",
            "dat_emissao": "Data de emissão do pedido",
            "cod_cliente": "Código do cliente",
            "cod_loja": "Loja do cliente",
            "cod_vendedor": "Código do vendedor do pedido",
            "cod_produto": "Código do produto",
            "qtd_vendida": "Quantidade vendida",
            "qtd_entregue": "Quantidade já faturada/entregue",
            "qtd_saldo": "Quantidade em carteira (vendida menos entregue)",
            "vlr_unitario": "Preço unitário de venda",
            "vlr_total": "Valor total do item",
            "vlr_saldo": "Valor em carteira (saldo × preço unitário)",
            "des_status": "Situação do item: Aberto, Parcial ou Faturado",
            "dat_atualizacao": "Data e hora da última carga da Gold",
        },
    ),
    "dim_cliente": (
        "Clientes ativos por empresa (cadastro compartilhado entre filiais). Fonte: SA1.",
        {
            "cod_empresa": "Código da empresa",
            "cod_cliente": "Código do cliente",
            "cod_loja": "Loja do cliente",
            "des_nome": "Razão social",
            "des_nome_reduzido": "Nome fantasia",
            "sig_uf": "UF",
            "des_municipio": "Município",
            "cod_vendedor": "Vendedor responsável pelo cliente",
            "flg_bloqueado": "Cliente bloqueado para novos pedidos",
        },
    ),
    "dim_vendedor": (
        "Vendedores por empresa. Fonte: SA3.",
        {"cod_empresa": "Código da empresa", "cod_vendedor": "Código do vendedor", "des_nome": "Nome do vendedor"},
    ),
    "dim_produto": (
        "Produtos por empresa. Fonte: SB1.",
        {
            "cod_empresa": "Código da empresa",
            "cod_produto": "Código do produto",
            "des_produto": "Descrição do produto",
            "des_tipo": "Tipo do produto (ex.: PA — produto acabado)",
            "des_unidade_medida": "Unidade de medida",
            "cod_grupo": "Grupo do produto",
            "vlr_preco_venda": "Preço de venda de referência",
        },
    ),
    "dim_unidade": (
        "Unidades de negócio: combinação de empresa e filial.",
        {"cod_empresa": "Código da empresa", "cod_filial": "Código da filial", "des_unidade": "Nome da unidade"},
    ),
    "dim_calendario": (
        "Calendário diário do período dos pedidos.",
        {
            "dat_data": "Data",
            "num_ano": "Ano",
            "num_mes": "Mês (1 a 12)",
            "des_mes": "Nome do mês",
            "num_trimestre": "Trimestre",
            "des_ano_mes": "Ano e mês (yyyy-MM)",
            "num_dia_semana": "Dia da semana (1 = domingo)",
        },
    ),
}


def _escapar(texto: str) -> str:
    return texto.replace("\\", "\\\\").replace("'", "\\'")


def comandos_comentario(tabela_completa: str, tabela: str) -> list[str]:
    """Gera os comandos COMMENT ON TABLE / ALTER COLUMN para uma tabela da Gold."""
    descricao, colunas = COMENTARIOS[tabela]
    comandos = [f"COMMENT ON TABLE {tabela_completa} IS '{_escapar(descricao)}'"]
    comandos += [
        f"ALTER TABLE {tabela_completa} ALTER COLUMN {coluna} COMMENT '{_escapar(texto)}'"
        for coluna, texto in colunas.items()
    ]
    return comandos
