import random
from datetime import date
from decimal import Decimal

import pytest

from pdc_erp.pedidos import gerar_pedido
from pdc_erp.regras import cnpj_ficticio, cnpj_valido, proximo_codigo, tabela, valor_item


def test_cnpj_ficticio_tem_digito_verificador_invalido():
    rng = random.Random(1)
    assert cnpj_valido("11222333000181")  # CNPJ válido conhecido, usado apenas para validar o algoritmo
    for _ in range(200):
        numero = cnpj_ficticio(rng)
        assert len(numero) == 14 and numero.isdigit()
        assert not cnpj_valido(numero)


def test_valor_item_e_codigos():
    assert valor_item(Decimal("3"), Decimal("1.335")) == Decimal("4.01")
    assert proximo_codigo(None) == "000001"
    assert proximo_codigo("000099") == "000100"


def test_tabela_protheus():
    assert tabela("sc5", "08") == "sc5080"
    with pytest.raises(ValueError):
        tabela("sx5", "08")


@pytest.mark.parametrize("faturado", [False, True])
def test_gerar_pedido_respeita_regras(faturado):
    rng = random.Random(7)
    clientes = [("000001", "01", "000001")]
    produtos = [(f"TB{i:05d}", Decimal("10.00")) for i in range(1, 11)]
    cabecalho, itens = gerar_pedido(rng, "02", "000010", date(2026, 10, 13), clientes, produtos, 1, 5, faturado)
    assert cabecalho[:2] == ("02", "000010") and cabecalho[6] == "20261013"
    assert 1 <= len(itens) <= 5
    for item in itens:
        _, numero, _, _, quantidade, preco, valor, entregue, _ = item
        assert numero == "000010"
        assert valor == valor_item(quantidade, preco)
        assert entregue == (quantidade if faturado else Decimal(0))
