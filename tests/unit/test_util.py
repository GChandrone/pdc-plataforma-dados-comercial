import pytest

from pdc_lib.util import nome_tabela, validar_identificador, validar_tabela_protheus


@pytest.mark.parametrize("valor", ["silver", "dev_gold", "protheus", "a1"])
def test_identificador_valido_e_devolvido(valor):
    assert validar_identificador(valor) == valor


@pytest.mark.parametrize(
    "valor",
    ["", None, "Silver", "1bronze", "silver.protheus", "gold; DROP TABLE x", "dev-gold", "a" * 64],
)
def test_identificador_invalido_e_recusado(valor):
    with pytest.raises(ValueError):
        validar_identificador(valor)


@pytest.mark.parametrize("valor", ["sc5", "sc6", "sa1", "sa3", "sb1"])
def test_tabela_protheus_valida(valor):
    assert validar_tabela_protheus(valor) == valor


@pytest.mark.parametrize("valor", ["sc", "sc50", "SC5", "s15", "sc5080", ""])
def test_tabela_protheus_invalida(valor):
    with pytest.raises(ValueError):
        validar_tabela_protheus(valor)


def test_nome_tabela_monta_tres_partes():
    esperado = "dev_silver.protheus.sc6"
    assert nome_tabela("dev_silver", "protheus", "sc5") == esperado


def test_nome_tabela_recusa_parte_maliciosa():
    with pytest.raises(ValueError):
        nome_tabela("dev_silver", "protheus", "sc5 --")
