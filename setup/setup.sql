-- Setup idempotente do Unity Catalog para um ambiente do PDC.
-- Os marcadores ${...} são substituídos pelo notebook executar_setup com os parâmetros do target.
-- Na Free Edition, catálogos não podem ser criados pelo Asset Bundle; por isso este script.

CREATE CATALOG IF NOT EXISTS ${catalogo_bronze} COMMENT 'Camada Bronze: espelho da origem';
CREATE CATALOG IF NOT EXISTS ${catalogo_silver} COMMENT 'Camada Silver: origem tratada e padronizada';
CREATE CATALOG IF NOT EXISTS ${catalogo_gold} COMMENT 'Camada Gold: modelo de negócio';

CREATE SCHEMA IF NOT EXISTS ${catalogo_bronze}.protheus COMMENT 'Tabelas do ERP Protheus (simulado)';
CREATE SCHEMA IF NOT EXISTS ${catalogo_silver}.protheus COMMENT 'Tabelas do ERP Protheus tratadas';
CREATE SCHEMA IF NOT EXISTS ${catalogo_gold}.comercial COMMENT 'Modelo dimensional do domínio Comercial';

-- Landing compartilhada pelos dois ambientes, gravada somente pelo extrator local.
CREATE CATALOG IF NOT EXISTS landing COMMENT 'Arquivos recebidos de sistemas de origem';
CREATE SCHEMA IF NOT EXISTS landing.protheus COMMENT 'Arquivos Parquet enviados pelo extrator do Protheus';
CREATE VOLUME IF NOT EXISTS landing.protheus.arquivos COMMENT 'Parquet por tabela e empresa, com manifestos';
