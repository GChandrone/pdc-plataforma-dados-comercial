"""Transformações das camadas Silver e Gold (funções puras de PySpark, testáveis localmente)."""

from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F

# Tipo de carga de cada tabela (igual ao conf/ingestao.json do extrator).
TIPOS_CARGA = {"sc5": "INCREMENTAL", "sc6": "INCREMENTAL", "sa1": "FULL", "sa3": "FULL", "sb1": "FULL"}

# De-para das colunas do Protheus para a Silver: coluna_origem -> (coluna_destino, tipo).
# Campos de documento (A1_CGC) não são levados à Silver: minimização de dados (LGPD).
MAPEAMENTOS: dict[str, dict[str, tuple[str, str]]] = {
    "sc5": {
        "c5_filial": ("cod_filial", "texto"),
        "c5_num": ("cod_pedido", "texto"),
        "c5_tipo": ("des_tipo", "texto"),
        "c5_cliente": ("cod_cliente", "texto"),
        "c5_lojacli": ("cod_loja", "texto"),
        "c5_vend1": ("cod_vendedor", "texto"),
        "c5_emissao": ("dat_emissao", "data"),
        "c5_nota": ("num_nota", "texto"),
    },
    "sc6": {
        "c6_filial": ("cod_filial", "texto"),
        "c6_num": ("cod_pedido", "texto"),
        "c6_item": ("cod_item", "texto"),
        "c6_produto": ("cod_produto", "texto"),
        "c6_qtdven": ("qtd_vendida", "decimal"),
        "c6_prcven": ("vlr_unitario", "decimal"),
        "c6_valor": ("vlr_total", "decimal"),
        "c6_qtdent": ("qtd_entregue", "decimal"),
        "c6_nota": ("num_nota", "texto"),
    },
    "sa1": {
        "a1_cod": ("cod_cliente", "texto"),
        "a1_loja": ("cod_loja", "texto"),
        "a1_nome": ("des_nome", "texto"),
        "a1_nreduz": ("des_nome_reduzido", "texto"),
        "a1_est": ("sig_uf", "texto"),
        "a1_mun": ("des_municipio", "texto"),
        "a1_vend": ("cod_vendedor", "texto"),
        "a1_msblql": ("flg_bloqueado", "bloqueio"),
    },
    "sa3": {
        "a3_cod": ("cod_vendedor", "texto"),
        "a3_nome": ("des_nome", "texto"),
    },
    "sb1": {
        "b1_cod": ("cod_produto", "texto"),
        "b1_desc": ("des_produto", "texto"),
        "b1_tipo": ("des_tipo", "texto"),
        "b1_um": ("des_unidade_medida", "texto"),
        "b1_grupo": ("cod_grupo", "texto"),
        "b1_prv1": ("vlr_preco_venda", "decimal"),
    },
}

# Unidades de negócio: (empresa, filial, nome).
UNIDADES = [
    ("01", "01", "Matriz"),
    ("05", "01", "Acessórios"),
    ("08", "01", "Nordeste"),
    ("08", "02", "Centro-Oeste"),
    ("13", "01", "TopMax"),
]

_MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro",
          "Novembro", "Dezembro"]


def _converter(coluna: str, tipo: str):
    c = F.col(coluna)
    if tipo == "texto":
        return F.trim(c.cast("string"))
    if tipo == "data":
        texto = F.trim(c.cast("string"))
        return F.when(texto == "", F.lit(None).cast("date")).otherwise(F.to_date(texto, "yyyyMMdd"))
    if tipo == "decimal":
        return c.cast("decimal(14,2)")
    if tipo == "bloqueio":
        return F.trim(c.cast("string")) == "1"
    raise ValueError(f"Tipo de conversão desconhecido: {tipo}")


def padronizar(df: DataFrame, tabela: str) -> DataFrame:
    """Converte uma tabela da Bronze para o padrão da Silver (nomes semânticos, tipos e flags)."""
    mapeamento = MAPEAMENTOS[tabela]
    colunas = [F.trim(F.col("_empresa")).alias("cod_empresa")]
    colunas += [_converter(origem, tipo).alias(destino) for origem, (destino, tipo) in mapeamento.items()]
    colunas += [
        (F.trim(F.col("d_e_l_e_t_")) == "*").alias("flg_deletado"),
        F.col("r_e_c_n_o_").cast("long").alias("num_recno"),
        F.col("s_t_a_m_p_").cast("timestamp").alias("dat_stamp"),
        F.col("_lote"),
    ]
    return df.select(*colunas)


def ultima_versao(df: DataFrame, chaves: tuple[str, ...] = ("cod_empresa", "num_recno")) -> DataFrame:
    """Mantém somente a versão mais recente de cada registro (maior S_T_A_M_P_; desempate pelo lote)."""
    janela = Window.partitionBy(*chaves).orderBy(F.col("dat_stamp").desc(), F.col("_lote").desc())
    return df.withColumn("_ordem", F.row_number().over(janela)).filter(F.col("_ordem") == 1).drop("_ordem")


def ultimo_snapshot(df: DataFrame) -> DataFrame:
    """Para cargas FULL: mantém apenas o lote mais recente de cada empresa."""
    janela = Window.partitionBy("cod_empresa")
    return (
        df.withColumn("_lote_max", F.max("_lote").over(janela))
        .filter(F.col("_lote") == F.col("_lote_max"))
        .drop("_lote_max")
    )


def dim_unidade(spark: SparkSession) -> DataFrame:
    return spark.createDataFrame(UNIDADES, "cod_empresa string, cod_filial string, des_unidade string")


def montar_fato(sc5: DataFrame, sc6: DataFrame) -> DataFrame:
    """Fato de pedidos de venda no grão item do pedido, sem registros excluídos logicamente."""
    cabecalhos = sc5.filter(~F.col("flg_deletado")).select(
        "cod_empresa", "cod_filial", "cod_pedido", "dat_emissao", "cod_cliente", "cod_loja", "cod_vendedor"
    )
    itens = sc6.filter(~F.col("flg_deletado"))
    fato = itens.join(cabecalhos, ["cod_empresa", "cod_filial", "cod_pedido"], "inner")
    saldo = F.col("qtd_vendida") - F.col("qtd_entregue")
    status = (
        F.when(saldo <= 0, F.lit("Faturado"))
        .when(F.col("qtd_entregue") > 0, F.lit("Parcial"))
        .otherwise(F.lit("Aberto"))
    )
    return fato.select(
        "cod_empresa",
        "cod_filial",
        "cod_pedido",
        "cod_item",
        "dat_emissao",
        "cod_cliente",
        "cod_loja",
        "cod_vendedor",
        "cod_produto",
        "qtd_vendida",
        "qtd_entregue",
        saldo.cast("decimal(14,2)").alias("qtd_saldo"),
        "vlr_unitario",
        "vlr_total",
        (saldo * F.col("vlr_unitario")).cast("decimal(14,2)").alias("vlr_saldo"),
        status.alias("des_status"),
        F.current_timestamp().alias("dat_atualizacao"),
    )


def montar_calendario(spark: SparkSession, inicio: str, fim: str) -> DataFrame:
    """Dimensão calendário diária entre duas datas (formato yyyy-MM-dd)."""
    meses = F.array(*[F.lit(m) for m in _MESES])
    datas = spark.range(1).select(
        F.explode(F.sequence(F.to_date(F.lit(inicio)), F.to_date(F.lit(fim)))).alias("dat_data")
    )
    return datas.select(
        "dat_data",
        F.year("dat_data").alias("num_ano"),
        F.month("dat_data").alias("num_mes"),
        F.element_at(meses, F.month("dat_data")).alias("des_mes"),
        F.quarter("dat_data").alias("num_trimestre"),
        F.date_format("dat_data", "yyyy-MM").alias("des_ano_mes"),
        F.dayofweek("dat_data").alias("num_dia_semana"),
    )
