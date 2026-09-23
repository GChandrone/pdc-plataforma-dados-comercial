# PDC — Plataforma de Dados Comercial

Plataforma de dados analíticos do domínio Comercial, com dados **100% fictícios** que simulam o ERP Protheus.
Este repositório implementa o Plano de Gerenciamento de Configuração (PGC) do projeto.

```
PostgreSQL (ERP simulado) ──► extrator Python ──► Parquet na landing (volume UC)
        ▲                          ▲                        │
  simulador diário           Airflow (DAG)                  ▼
                                   │           Databricks: Bronze (COPY INTO) ► Silver (MERGE) ► Gold
                                   └──────────► job_comercial_diario ───────────► gates de qualidade ► dashboard
```

| Componente | Onde roda | Pasta |
|---|---|---|
| ERP simulado (PostgreSQL, carga inicial e simulador) | Docker local | `erp_simulado/` |
| Extrator incremental | Airflow local | `extrator/` |
| Orquestração (DAGs) | Airflow local (Docker) | `airflow/` |
| Bronze, Silver, Gold, qualidade e dashboard | Databricks Free Edition | `src/`, `resources/`, `setup/` |
| CI/CD | GitHub Actions | `.github/workflows/` |

## Pré-requisitos

- Conta no GitHub (repositório **público**: no plano gratuito, a proteção de branch e a aprovação manual de
  deploy só funcionam em repositórios públicos).
- Uma conta Databricks Free Edition e um token pessoal (Settings > Developer > Access tokens).
- Docker Desktop (recomendado 8 GB de RAM livres) e Python 3.11.

## Primeira configuração

1. **Criar o repositório** público no GitHub e enviar este conteúdo para a branch `main`.
2. **Proteger a `main`** (Settings > Branches): exigir Pull Request, exigir os checks do workflow `CI` e bloquear
   push direto. Não é necessário exigir número mínimo de aprovações (equipe pequena).
3. **Criar os Environments** (Settings > Environments):
   1. `dev`: secrets `DATABRICKS_HOST` e `DATABRICKS_TOKEN`.
   2. `prd`: os mesmos secrets e a regra *Required reviewers* com Gabriel e André.
4. **Ajustar o `CODEOWNERS`** com os usuários do GitHub da equipe.
5. **Configurar o ambiente local**:
   ```bash
   cp .env.example .env        # preencha senhas, host e token (o .env não é versionado)
   pip install -r requirements-dev.txt
   pre-commit install
   docker compose up -d --build
   ```
   O Airflow fica em http://127.0.0.1:8080 (acesso somente pela própria máquina).
6. **Primeiro deploy no Databricks** (cria catálogos, schemas, volume de landing, jobs e dashboard):
   ```bash
   databricks bundle deploy -t dev
   databricks bundle run -t dev job_setup
   ```
   Depois do primeiro PR mesclado, o CD passa a fazer isso automaticamente.
7. **Carga inicial do ERP**: no Airflow, execute manualmente a DAG `dag_erp_carga_inicial` (uma única vez).
8. **Primeira carga**: execute a DAG `dag_comercial_diario`. Ela extrai o ERP, envia os arquivos para a landing
   e aciona o `job_comercial_diario` de Produção. Antes disso, faça a primeira release (seção abaixo) para que o
   job de Produção exista.

## Fluxo de trabalho

1. Abrir uma issue (templates: Funcionalidade, Correção ou Mudança de dados).
2. Criar a branch `feature/<issue>-<descrição>` e commitar no padrão Conventional Commits
   (ex.: `feat(gold): cria fato_pedido_venda`).
3. Abrir o PR: o CI roda lint, verificação de isolamento, Bandit, gitleaks, testes unitários e de integração,
   build da imagem do Airflow e validação do bundle.
4. Squash merge na `main`: o CD implanta em Desenvolvimento e executa o job com os gates de qualidade.
5. **Release**: criar a tag `vX.Y.Z` (SemVer aplicado ao modelo Gold) e aprovar o deploy no Environment `prd`.
   O CD implanta em Produção, roda o smoke test e publica o GitHub Release com as notas de versão.
6. **Ambiente local**: após a release, atualizar a máquina a partir da mesma tag:
   ```bash
   git fetch --tags && git checkout vX.Y.Z
   docker compose up -d --build
   ```

## Ambientes

| | Desenvolvimento | Produção |
|---|---|---|
| Target do bundle | `dev` (modo development) | `prd` (modo production) |
| Catálogos | `dev_bronze`, `dev_silver`, `dev_gold` | `bronze`, `silver`, `gold` |
| Landing | `landing.protheus.arquivos` (compartilhada) | `landing.protheus.arquivos` (compartilhada) |
| Execução do job | CD após cada merge | DAG `dag_comercial_diario` (diária) |

Nenhum código cita catálogo de forma fixa: tudo chega por parâmetro do job. O CI falha se isso for violado
(`.github/scripts/verificar_isolamento.py`).

## Rollback e recuperação

1. **Código**: reexecutar o workflow `CD` a partir da tag anterior (ou criar uma tag PATCH com a reversão) e, no
   ambiente local, `git checkout <tag-anterior> && docker compose up -d --build`.
2. **Dados**: restaurar as tabelas afetadas com Time Travel e reprocessar:
   ```sql
   DESCRIBE HISTORY silver.protheus.sc6;             -- localizar a versão anterior à carga incorreta
   RESTORE TABLE silver.protheus.sc6 TO VERSION AS OF <versão>;
   ```
   Se for preciso extrair de novo a partir de um ponto, retroceder o watermark no PostgreSQL:
   ```sql
   UPDATE controle.ingestion_control SET ultimo_watermark = '<data-hora UTC>' WHERE tabela = 'sc6';
   ```
3. **Contenção**: enquanto a correção não é implantada, desligar a extração da tabela afetada colocando
   `"ativo": false` em `conf/ingestao.json` (via PR).
4. Registrar o incidente e as ações em uma issue.

## Comandos úteis

```bash
docker compose exec airflow pdc-erp simular              # movimentação do ERP fora do agendamento
docker compose exec airflow pdc-extrator executar        # extração manual
pytest tests/unit                                        # testes unitários (requer Java para o PySpark)
ruff check . && python .github/scripts/verificar_isolamento.py
```

## Observações

- Somente dados fictícios: CPF/CNPJ são gerados com dígito verificador inválido e não são levados à Silver.
- O dashboard (`src/dashboards/comercial.lvdash.json`) é publicado pelo bundle. Se o layout precisar de ajuste,
  edite-o na interface do Databricks e exporte novamente com
  `databricks bundle generate dashboard --existing-id <id>`.
- Decisões de arquitetura estão em `docs/adr/`; o dicionário de dados da Gold, em `docs/dicionario-dados.md`.
