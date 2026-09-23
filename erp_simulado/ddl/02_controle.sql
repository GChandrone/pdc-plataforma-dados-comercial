-- Tabela de controle da extração (IngestionControl), mantida pelo extrator.
-- O conteúdo (tabelas, empresas, tipo de carga, ativo) é sincronizado a partir de conf/ingestao.json;
-- o watermark e o status são estado de execução.

CREATE SCHEMA IF NOT EXISTS controle;

CREATE TABLE IF NOT EXISTS controle.ingestion_control (
    tabela               varchar(3)  NOT NULL,
    empresa              char(2)     NOT NULL,
    tipo_carga           varchar(11) NOT NULL CHECK (tipo_carga IN ('FULL', 'INCREMENTAL')),
    ativo                boolean     NOT NULL DEFAULT true,
    ultimo_watermark     timestamp,
    status_ultima_carga  varchar(10),
    data_ultima_execucao timestamp,
    qtd_ultima_carga     integer,
    PRIMARY KEY (tabela, empresa)
);
