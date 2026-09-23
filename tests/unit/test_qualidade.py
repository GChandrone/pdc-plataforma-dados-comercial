from pdc_lib.qualidade import contar_duplicidades, contar_nulos, contar_orfaos, reconciliar


def test_duplicidades_e_nulos(spark):
    df = spark.createDataFrame([("08", 1), ("08", 1), ("08", None)], "cod_empresa string, num_recno long")
    assert contar_duplicidades(df, ["cod_empresa", "num_recno"]) == 1
    assert contar_nulos(df, ["cod_empresa", "num_recno"]) == 1


def test_orfaos(spark):
    fato = spark.createDataFrame([("08", "000001"), ("08", "000099")], "cod_empresa string, cod_produto string")
    dim = spark.createDataFrame([("08", "000001")], "cod_empresa string, cod_produto string")
    assert contar_orfaos(fato, dim, ["cod_empresa", "cod_produto"]) == 1


def test_reconciliar_aponta_divergencias(spark):
    manifesto = spark.createDataFrame(
        [("L1", "sc5", "08", 10), ("L1", "sc6", "08", 30), ("L1", "sa1", "08", 0)],
        "lote string, tabela string, empresa string, registros long")
    bronze = spark.createDataFrame([("L1", "sc5", "08", 10), ("L1", "sc6", "08", 29)],
                                   "lote string, tabela string, empresa string, qtd_bronze long")
    divergencias = reconciliar(manifesto, bronze).collect()
    assert [(d.tabela, d.registros, d.qtd_bronze) for d in divergencias] == [("sc6", 30, 29)]
