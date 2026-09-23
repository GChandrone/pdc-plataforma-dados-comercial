# Dicionário de dados — Gold (`<catálogo gold>.comercial`)

As descrições completas de cada coluna também são publicadas no Unity Catalog (COMMENT), a partir de
`src/pdc_lib/comentarios.py`.

## fato_pedido_venda

Grão: item do pedido de venda. Fonte: SC5 (cabeçalho) e SC6 (itens), sem registros excluídos logicamente.

| Coluna | Descrição |
|---|---|
| cod_empresa, cod_filial | Empresa e filial do pedido (ver `dim_unidade`) |
| cod_pedido, cod_item | Número do pedido (C5_NUM) e item (C6_ITEM) |
| dat_emissao | Data de emissão |
| cod_cliente, cod_loja | Cliente (ver `dim_cliente`) |
| cod_vendedor | Vendedor (ver `dim_vendedor`) |
| cod_produto | Produto (ver `dim_produto`) |
| qtd_vendida, qtd_entregue, qtd_saldo | Quantidades vendida, entregue e em carteira |
| vlr_unitario, vlr_total, vlr_saldo | Preço unitário, valor total e valor em carteira |
| des_status | Aberto, Parcial ou Faturado |
| dat_atualizacao | Data e hora da última carga |

## Dimensões

| Tabela | Chave | Fonte |
|---|---|---|
| dim_cliente | cod_empresa, cod_cliente, cod_loja | SA1 |
| dim_vendedor | cod_empresa, cod_vendedor | SA3 |
| dim_produto | cod_empresa, cod_produto | SB1 |
| dim_unidade | cod_empresa, cod_filial | Fixa: Matriz (01/01), Acessórios (05/01), Nordeste (08/01), Centro-Oeste (08/02), TopMax (13/01) |
| dim_calendario | dat_data | Gerada |

Os cadastros (SA1, SA3, SB1) são compartilhados entre as filiais de uma empresa (filial em branco, como o
xFilial do Protheus); por isso as dimensões são chaveadas por empresa, sem filial.
