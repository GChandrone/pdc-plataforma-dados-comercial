# ADR 0001 — Extração no sentido inverso (máquina local envia os dados ao Databricks)

- **Status:** aceita
- **Data:** 23/09/2026

## Contexto

O projeto usa o Databricks Free Edition, que é gratuito, mas restringe o acesso de saída à internet a um
conjunto limitado de domínios confiáveis. Com isso, o Databricks não consegue se conectar a bancos externos
(Azure SQL, PostgreSQL na nuvem ou na máquina local), e o Azure Data Factory não integra nativamente com
workspaces que não são Azure Databricks.

## Decisão

A fonte (PostgreSQL que simula o Protheus) roda localmente em Docker. Um extrator Python, orquestrado pelo
Airflow local, lê o banco de forma incremental e **envia** arquivos Parquet a um volume de landing do Unity
Catalog pela Files API. No Databricks, a Bronze incorpora os arquivos com `COPY INTO`.

## Consequências

- Positivas: custo zero, extração de um banco relacional real (com trigger de `S_T_A_M_P_`) e separação clara
  entre sistema de origem e plataforma de dados.
- Negativas: a extração depende de uma máquina ligada no horário da DAG. Mitigação: o extrator é incremental e
  recupera os dias sem execução, e o dashboard exibe a data da última atualização.
