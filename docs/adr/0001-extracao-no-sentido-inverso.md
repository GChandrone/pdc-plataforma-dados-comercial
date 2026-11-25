# 0001 — Extração no sentido inverso: a máquina local envia os dados ao Databricks

- Status: aceito
- Data: 23/09/2026

## Contexto

O projeto usa o Databricks Free Edition, que é gratuito, mas restringe o acesso de saída à internet
a um conjunto limitado de domínios confiáveis. Com isso, o Databricks não consegue se conectar a
bancos externos (Azure SQL, PostgreSQL na nuvem ou na máquina local), e o Azure Data Factory não
integra nativamente com workspaces que não são Azure Databricks. O orçamento do projeto é zero.

## Decisão

A fonte (PostgreSQL que simula o Protheus) roda localmente em Docker. Um extrator Python,
orquestrado pelo Airflow local, lê o banco de forma incremental e **envia** arquivos Parquet a um
volume de landing do Unity Catalog pela Files API. No Databricks, a Bronze incorpora os arquivos
com `COPY INTO`.

## Alternativas consideradas

- **Azure Data Factory + Azure Databricks:** padrão da arquitetura de referência, mas exige
  assinatura paga e não integra com a Free Edition.
- **Databricks lendo o banco direto (JDBC):** bloqueado pela restrição de saída da Free Edition.
- **Lakebase (Postgres interno do Databricks):** viável, mas não demonstra a extração de um banco
  transacional externo, que é parte do objetivo do projeto.

## Consequências

- Custo zero e extração de um banco relacional real, com trigger de `S_T_A_M_P_`.
- Separação clara entre sistema de origem e plataforma de dados.
- A extração depende de uma máquina ligada no horário da DAG. Mitigação: o extrator é incremental
  e recupera os dias sem execução, e o dashboard exibe a data da última atualização.
