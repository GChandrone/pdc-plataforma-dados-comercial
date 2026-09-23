"""Gates de qualidade de dados executados a cada carga."""

from __future__ import annotations

from functools import reduce

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def contar_duplicidades(df: DataFrame, chaves: list[str]) -> int:
    return df.groupBy(*chaves).count().filter(F.col("count") > 1).count()


def contar_nulos(df: DataFrame, colunas: list[str]) -> int:
    condicao = reduce(lambda a, b: a | b, [F.col(c).isNull() for c in colunas])
    return df.filter(condicao).count()


def contar_orfaos(fato: DataFrame, dimensao: DataFrame, chaves: list[str]) -> int:
    """Quantidade de combinações de chave da fato sem correspondência na dimensão."""
    return fato.select(*chaves).distinct().join(dimensao.select(*chaves).distinct(), chaves, "left_anti").count()


def reconciliar(manifesto: DataFrame, contagens_bronze: DataFrame) -> DataFrame:
    """Compara a contagem de registros declarada no manifesto do extrator com o que chegou na Bronze.

    manifesto: lote, tabela, empresa, registros
    contagens_bronze: lote, tabela, empresa, qtd_bronze
    """
    return (
        manifesto.filter(F.col("registros") > 0)
        .join(contagens_bronze, ["lote", "tabela", "empresa"], "left")
        .withColumn("qtd_bronze", F.coalesce(F.col("qtd_bronze"), F.lit(0)))
        .filter(F.col("qtd_bronze") != F.col("registros"))
    )
