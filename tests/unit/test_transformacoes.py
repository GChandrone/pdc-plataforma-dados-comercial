from datetime import date, datetime
from decimal import Decimal

from pdc_lib.transformacoes import montar_calendario, montar_fato, padronizar, ultima_versao, ultimo_snapshot


def _bronze_sc5(spark, **alteracoes):
    linha = {
        "c5_filial": "01", "c5_num": "000123", "c5_tipo": "N", "c5_cliente": "000001", "c5_lojacli": "01",
        "c5_vend1": "000002", "c5_emissao": "20261013", "c5_nota": "         ", "d_e_l_e_t_": " ",
        "r_e_c_n_o_": 10, "r_e_c_d_e_l_": 0, "s_t_a_m_p_": datetime(2026, 10, 13, 9, 0), "_empresa": "08",
        "_lote": "20261013T090000Z",
    }
    linha.update(alteracoes)
    return spark.createDataFrame([linha])


def test_padronizar_sc5_converte_nomes_tipos_e_flags(spark):
    resultado = padronizar(_bronze_sc5(spark, d_e_l_e_t_="*"), "sc5").first()
    assert resultado.cod_empresa == "08"
    assert resultado.cod_pedido == "000123"
    assert resultado.dat_emissao == date(2026, 10, 13)
    assert resultado.num_nota == ""
    assert resultado.flg_deletado is True
    assert resultado.num_recno == 10


def test_padronizar_data_em_branco_vira_nula(spark):
    resultado = padronizar(_bronze_sc5(spark, c5_emissao="        "), "sc5").first()
    assert resultado.dat_emissao is None


def test_ultima_versao_mantem_maior_stamp(spark):
    antigo = _bronze_sc5(spark, c5_cliente="000001", s_t_a_m_p_=datetime(2026, 10, 13, 9, 0))
    novo = _bronze_sc5(spark, c5_cliente="000009", s_t_a_m_p_=datetime(2026, 10, 14, 9, 0))
    resultado = ultima_versao(padronizar(antigo.unionByName(novo), "sc5")).collect()
    assert len(resultado) == 1
    assert resultado[0].cod_cliente == "000009"


def test_ultimo_snapshot_por_empresa(spark):
    base = {"a3_filial": "  ", "a3_cod": "000001", "a3_nome": "Vendedor 001", "d_e_l_e_t_": " ",
            "r_e_c_n_o_": 1, "r_e_c_d_e_l_": 0, "s_t_a_m_p_": datetime(2026, 10, 1)}
    linhas = [
        {**base, "_empresa": "01", "_lote": "20261001T000000Z"},
        {**base, "_empresa": "01", "_lote": "20261002T000000Z"},
        {**base, "_empresa": "05", "_lote": "20261001T000000Z"},
    ]
    resultado = ultimo_snapshot(padronizar(spark.createDataFrame(linhas), "sa3")).collect()
    assert sorted((r.cod_empresa, r._lote) for r in resultado) == [
        ("01", "20261002T000000Z"), ("05", "20261001T000000Z")]


def _silver(spark):
    sc5 = spark.createDataFrame([
        ("08", "01", "000001", date(2026, 10, 1), "000001", "01", "000002", False),
        ("08", "01", "000002", date(2026, 10, 2), "000001", "01", "000002", True),
    ], "cod_empresa string, cod_filial string, cod_pedido string, dat_emissao date, cod_cliente string, "
       "cod_loja string, cod_vendedor string, flg_deletado boolean")
    sc6 = spark.createDataFrame([
        ("08", "01", "000001", "01", "TB00001", Decimal("10"), Decimal("2.00"), Decimal("20.00"), Decimal("0"), False),
        ("08", "01", "000001", "02", "TB00002", Decimal("10"), Decimal("1.00"), Decimal("10.00"), Decimal("4"), False),
        ("08", "01", "000001", "03", "TB00003", Decimal("5"), Decimal("1.00"), Decimal("5.00"), Decimal("5"), False),
        ("08", "01", "000002", "01", "TB00001", Decimal("1"), Decimal("1.00"), Decimal("1.00"), Decimal("0"), False),
    ], "cod_empresa string, cod_filial string, cod_pedido string, cod_item string, cod_produto string, "
       "qtd_vendida decimal(14,2), vlr_unitario decimal(14,2), vlr_total decimal(14,2), "
       "qtd_entregue decimal(14,2), flg_deletado boolean")
    return sc5, sc6


def test_montar_fato_exclui_deletados_e_calcula_status_e_saldo(spark):
    sc5, sc6 = _silver(spark)
    fato = {r.cod_item: r for r in montar_fato(sc5, sc6).collect()}
    assert set(fato) == {"01", "02", "03"}  # pedido 000002 foi excluído logicamente
    assert fato["01"].des_status == "Aberto" and fato["01"].vlr_saldo == Decimal("20.00")
    assert fato["02"].des_status == "Parcial" and fato["02"].qtd_saldo == Decimal("6.00")
    assert fato["03"].des_status == "Faturado" and fato["03"].vlr_saldo == Decimal("0.00")


def test_calendario_cobre_intervalo(spark):
    calendario = montar_calendario(spark, "2026-01-01", "2026-12-31")
    assert calendario.count() == 365
    primeiro = calendario.orderBy("dat_data").first()
    assert primeiro.des_mes == "Janeiro" and primeiro.des_ano_mes == "2026-01"
