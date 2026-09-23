from datetime import datetime, timedelta

import pytest

from pdc_extrator.consulta import montar_consulta, proximo_watermark, tabela_fisica


def test_tabela_fisica_padrao_protheus():
    assert tabela_fisica("sc5", "08") == "sc5080"


@pytest.mark.parametrize("alias,empresa", [("sc5;drop", "08"), ("SC5", "08"), ("sc5", "8"), ("sc5", "08 or 1=1")])
def test_tabela_fisica_rejeita_entradas_invalidas(alias, empresa):
    with pytest.raises(ValueError):
        tabela_fisica(alias, empresa)


def test_consulta_full_nao_usa_watermark():
    consulta, parametros = montar_consulta("sa1", "01", "FULL", datetime(2026, 1, 1), 10)
    assert parametros == ()
    assert "s_t_a_m_p_ >" not in repr(consulta)


def test_primeira_carga_incremental_le_tudo():
    _, parametros = montar_consulta("sc5", "01", "INCREMENTAL", None, 10)
    assert parametros == ()


def test_consulta_incremental_aplica_overlap():
    watermark = datetime(2026, 10, 13, 6, 0)
    consulta, parametros = montar_consulta("sc6", "13", "INCREMENTAL", watermark, 10)
    assert parametros == (watermark - timedelta(minutes=10),)
    assert "s_t_a_m_p_ >" in repr(consulta)


def test_tipo_de_carga_invalido():
    with pytest.raises(ValueError):
        montar_consulta("sc5", "01", "DELTA", None, 0)


def test_proximo_watermark_avanca_e_nunca_retrocede():
    atual = datetime(2026, 10, 13)
    assert proximo_watermark(atual, [datetime(2026, 10, 14), None]) == datetime(2026, 10, 14)
    assert proximo_watermark(atual, [datetime(2026, 10, 12)]) == atual
    assert proximo_watermark(atual, []) == atual
    assert proximo_watermark(None, []) is None
