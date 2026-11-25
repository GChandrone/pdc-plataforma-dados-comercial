# Guia de onboarding — PDC Plataforma de Dados Comercial

Este guia é suficiente para instalar o projeto, rodar os testes e abrir o seu primeiro Pull Request
sem precisar perguntar nada a ninguém (PGC 12). O passo a passo completo, com rollback e problemas
comuns, está em [guia-desenvolvimento.md](guia-desenvolvimento.md).

## 1. Ambiente

- Git, Python 3.11, Java 17 ou superior (PySpark nos testes) e Docker Desktop
- No Windows, use o **Git Bash** para os comandos abaixo
- Acesso ao workspace Databricks do projeto (peça o convite ao responsável)

```bash
git clone https://github.com/GChandrone/pdc-plataforma-dados-comercial.git
cd pdc-plataforma-dados-comercial
cp .env.example .env              # preencha senhas, DATABRICKS_HOST e DATABRICKS_TOKEN
pip install -r requirements-dev.txt
pre-commit install
```

## 2. Rodar e testar

```bash
ruff check .                                       # lint
python .github/scripts/verificar_isolamento.py     # nenhum catálogo fixo no código
python -m pytest tests/unit                        # testes unitários
docker compose up -d --build                       # ERP simulado (PostgreSQL) + Airflow
```

- Airflow: <http://127.0.0.1:8080>. A DAG `dag_erp_carga_inicial` cria a base fictícia (uma única vez).
- Testes de integração: use um banco separado (eles apagam as tabelas antes de rodar):
  ```bash
  docker compose exec erp-db createdb -U <PG_USER> erp_protheus_teste
  PG_HOST=localhost PG_DB=erp_protheus_teste PG_USER=<PG_USER> PG_PASSWORD=<senha> \
    python -m pytest tests/integration -m integration
  ```

## 3. Seu primeiro Pull Request

1. Pegue uma Issue (ou abra uma pelos templates *Funcionalidade* ou *Defeito*) e atribua a você.
2. Crie a branch a partir da `main` atualizada:
   ```bash
   git switch main && git pull
   git switch -c feature/42-descricao-curta
   ```
3. Commits e **título do PR** em Conventional Commits. O título vira o commit na `main` e decide a
   próxima versão:

   | Título | Versão |
   |---|---|
   | `feat(gold): ...` | MINOR (1.**1**.0) |
   | `fix(extrator): ...` | PATCH (1.0.**1**) |
   | `docs: ...`, `chore: ...`, `ci: ...` | sem versão nova |

4. Envie e abra o PR:
   ```bash
   git push -u origin feature/42-descricao-curta
   ```
5. Preencha o template (Contexto, Decisão tomada, Como testar e Checklist) e escreva `Closes #42`.
   O par de revisão é chamado automaticamente (CODEOWNERS) e precisa aprovar.

## 4. Lendo o resultado do pipeline

| Check | O que verifica | Se ficar vermelho |
|---|---|---|
| `titulo-pr` | título em Conventional Commits | edite o título do PR |
| `Lint, testes e cobertura` | ruff, catálogo fixo, Bandit, testes e cobertura ≥ 60% | **Details** → passo que falhou |
| `Análise de dependências (SCA)` | dependência nova com vulnerabilidade crítica | troque a versão da dependência |
| `Varredura de segredos (gitleaks)` | token ou senha no histórico | remova o segredo e troque-o no serviço de origem |
| `Build do Airflow e importação das DAGs` | Dockerfile e DAGs válidos | **Details** → erro de importação |
| `Validação do Asset Bundle` | `databricks.yml` e `resources/` | **Details** → mensagem do CLI |
| `ci-ok` | resumo: todos os anteriores passaram | veja qual job falhou acima dele |

## 5. Depois do merge

O CD calcula a versão, publica o pacote em **staging** (catálogos `dev_*` no Databricks) e roda o job
com os gates de qualidade. Se houver versão nova, a **produção** espera a aprovação em
*Actions → CD → Review deployments*. Aprovada, vira a Release `vX.Y.Z` com o pacote anexado.
