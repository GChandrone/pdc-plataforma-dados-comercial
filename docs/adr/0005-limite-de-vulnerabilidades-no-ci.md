# 0005 — Limite de vulnerabilidades no CI: bloquear apenas `critical` (risco aceito)

- Status: aceito
- Data: 24/11/2026
- Revisão: 30/01/2027

## Contexto

O job `dependencias` (dependency-review) compara as dependências do PR com a `main` e pode bloquear
vulnerabilidades a partir de um nível de severidade (PGC 5.3). A maior parte das dependências do
projeto é de **desenvolvimento e teste** (pytest, PySpark local, ruff, Bandit, pre-commit), que não vão
para produção; em produção rodam o extrator (psycopg, pyarrow, databricks-sdk), as DAGs e os notebooks
no runtime gerenciado do Databricks.

## Decisão

O CI bloqueia somente vulnerabilidades **críticas**. Alertas `high` ou menores aparecem em
*Security → Dependabot alerts* e são tratados pelo Dependabot (security updates) e pela revisão
semanal dos PRs de dependência. Esta decisão é revista em **30/01/2027** ou antes, se surgir
um alerta `high` em dependência que vá para produção.

## Alternativas consideradas

- **Bloquear a partir de `high`:** mais seguro, mas travaria PRs por alertas em ferramentas que só
  rodam no CI e na máquina do desenvolvedor.
- **Sem bloqueio:** descumpre o PGC 5.3.

## Consequências

- Risco aceito e documentado para vulnerabilidades `high` em dependências de desenvolvimento.
- Exige acompanhar os alertas do Dependabot; o prazo de revisão está registrado acima.
