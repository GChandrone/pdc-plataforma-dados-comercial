# 🛠️ Guia de desenvolvimento — da issue até Produção

Este guia descreve, passo a passo, como uma mudança sai da ideia e chega ao ambiente de **production**,
seguindo o processo de controle de mudanças do [Plano de Gerenciamento de Configuração](pgc/) (seção 8).

> **Regra de ouro:** pessoas decidem (o que mudar, quando integrar, quando liberar); a automação executa
> (testar, implantar e registrar). Nada é alterado manualmente em Produção.

---

## 🗺️ Visão geral

```mermaid
flowchart LR
    I["📝 0. Issue"] --> B["🌿 1. Branch"] --> D["💻 2-4. Desenvolver<br/>e testar"] --> P["🔀 5-6. Pull Request"]
    P --> CI{"🤖 7. CI<br/>5 checks"}
    CI -- "❌" --> D
    CI -- "✅" --> M["8. Merge automático"] --> S["🧪 Deploy em staging"]
    S --> T["🏷️ 10. Tag vX.Y.Z"] --> A{"👤 11. Aprovação"} --> PR["🌐 Deploy em production"] --> R["📦 12. Release"]
```

| Etapa | Onde acontece |
|---|---|
| Issue, branch, PR, CI, merge, tag, aprovação e Release | GitHub |
| Escrever o código e rodar os testes locais | VS Code (máquina local) |
| Executar o pipeline e conferir tabelas, jobs e dashboard | Databricks |
| PostgreSQL do ERP simulado, extrator e Airflow | Docker (máquina local) |

---

## ✅ Pré-requisitos (uma única vez)

1. Ferramentas instaladas: Git, GitHub CLI (`gh`), Python 3.11, Java 17+, Docker Desktop e Databricks CLI.
2. Login na GitHub CLI: `gh auth login`.
3. Ambiente local preparado:
   ```bash
   cp .env.example .env              # preencher senhas, DATABRICKS_HOST e DATABRICKS_TOKEN
   pip install -r requirements-dev.txt
   pre-commit install
   docker compose up -d --build
   ```
4. Os comandos deste guia usam o **Git Bash** (Windows) ou o terminal do Linux/Mac.

---

## 1️⃣ Planejamento

### Passo 0 — Abrir a issue

Toda mudança começa com uma issue, que registra **o que** será feito e **por quê**.

- **Pelo navegador:** *Issues › New issue* e escolha o template: Funcionalidade, Correção ou Mudança de dados.
- **Pelo terminal:**
  ```bash
  gh issue create --title "Incluir vlr_desconto na fato_pedido_venda" --label feat
  ```

Anote o número da issue (nos exemplos abaixo, **#15**). Se a mudança se encaixar nos critérios do CCM
(mudança incompatível na Gold, alteração de regra de negócio, RESTORE ou reprocessamento em Produção),
adicione também a label `ccm`.

### Passo 1 — Criar a branch ligada à issue

```bash
git checkout main
git pull
gh issue develop 15 --name feature/15-vlr-desconto --checkout
```

| Tipo de mudança | Padrão de nome da branch |
|---|---|
| Funcionalidade | `feature/<issue>-<descricao-curta>` |
| Correção | `fix/<issue>-<descricao-curta>` |
| Correção emergencial em Produção | `hotfix/<descricao-curta>` |

---

## 2️⃣ Desenvolvimento

### Passo 2 — Desenvolver no VS Code

| O que mudar | Onde |
|---|---|
| Regras de transformação e qualidade | `src/pdc_lib/` |
| Notebooks Bronze, Silver, Gold e qualidade | `src/ingestao/`, `src/silver/`, `src/gold/`, `src/qualidade/` |
| Jobs e dashboard do Databricks | `resources/`, `src/dashboards/` |
| Extração e ERP simulado | `extrator/`, `erp_simulado/`, `conf/` |
| DAGs do Airflow | `airflow/dags/` |
| Testes | `tests/unit/`, `tests/integration/` |

Boas práticas do projeto:

- Nunca escreva o nome de um catálogo de forma fixa (ex.: `silver.protheus.sc5`): use sempre o parâmetro do job.
- Toda coluna nova da Gold precisa de descrição em `src/pdc_lib/comentarios.py`.
- Somente dados fictícios: nada de dados reais, tokens ou senhas no código.

### Passo 3 — Validar localmente

```bash
ruff check .
python .github/scripts/verificar_isolamento.py
pytest tests/unit
```

Para o teste de integração, use **sempre** o banco de teste (ele apaga as tabelas antes de rodar):

```bash
PG_HOST=localhost PG_DB=erp_protheus_teste PG_USER=<usuario> PG_PASSWORD=<senha> \
  pytest tests/integration -m integration
```

### Passo 4 — Testar no Databricks (opcional)

Recomendado quando a mudança altera notebooks, jobs ou o dashboard. Publica a **sua branch** no target `dev`
(catálogos `dev_*`, jobs com o prefixo do seu usuário):

```bash
databricks bundle deploy -t dev
databricks bundle run -t dev job_comercial_diario
```

Confira o resultado no Databricks (Catalog, Jobs & Pipelines e o dashboard de Desenvolvimento).
Os catálogos `dev_*` são compartilhados: combine com o colega antes de testar ao mesmo tempo.

---

## 3️⃣ Integração

### Passo 5 — Commitar e enviar

Mensagens no padrão [Conventional Commits](https://www.conventionalcommits.org/pt-br/):

```bash
git add .
git commit -m "feat(gold): inclui vlr_desconto na fato_pedido_venda"
git push -u origin feature/15-vlr-desconto
```

| Tipo | Uso | Escopos comuns |
|---|---|---|
| `feat` | Nova funcionalidade | `bronze`, `silver`, `gold`, `dag`, `dashboard` |
| `fix` | Correção | `extrator`, `erp`, `infra` |
| `docs` | Documentação | — |
| `test`, `refactor`, `ci`, `chore` | Testes, refatoração, pipeline e manutenção | `ci`, `deps` |

O **pre-commit** roda automaticamente no commit (ruff, gitleaks e limpeza dos outputs dos notebooks) e
bloqueia o commit se encontrar algum problema.

### Passo 6 — Abrir o Pull Request com auto-merge

```bash
gh pr create --fill --body "Closes #15"
gh pr merge --auto --squash
```

Preencha o checklist do template do PR. A revisão pelo colega é recomendada e **obrigatória** quando a
mudança aciona o CCM.

### Passo 7 — Acompanhar o CI

```bash
gh pr checks --watch
```

| Check | O que verifica |
|---|---|
| Lint, isolamento e SAST | ruff, catálogo fixo e Bandit |
| Testes unitários e de integração | pytest, com PostgreSQL real |
| Varredura de segredos (gitleaks) | Tokens e senhas no histórico |
| Build da imagem do Airflow e importação das DAGs | Dockerfile e DAGs válidos |
| Validação do Asset Bundle | `databricks.yml` e `resources/` válidos |

Se algum check falhar: abra *Details* no PR, corrija na mesma branch, faça um novo commit e `git push`.
O CI roda de novo e o auto-merge continua ativo.

### Passo 8 — Merge e deploy em staging (automáticos)

Com os 5 checks verdes, o GitHub faz o **squash merge**, apaga a branch e fecha a issue (por causa do
`Closes #15`). O CD faz o deploy em **staging** e executa o job com os gates de qualidade:

```bash
gh run list --workflow cd.yml --limit 3
gh run watch
```

---

## 4️⃣ Produção

### Passo 9 — Atualizar a `main`

```bash
git checkout main
git pull
```

### Passo 10 — Criar a tag da versão

O número segue o [SemVer](https://semver.org/lang/pt-BR/) aplicado ao modelo Gold. Consulte a última versão
com `git tag --sort=-v:refname | head -1`.

| Mudança desde a última versão | Exemplo | Incremento |
|---|---|---|
| Correção, sem impacto no modelo Gold | Corrigir regra, ajustar documentação | PATCH — `v0.2.0` → `v0.2.1` |
| Algo novo e compatível | Nova coluna ou tabela na Gold | MINOR — `v0.2.1` → `v0.3.0` |
| Mudança incompatível (aciona o CCM) | Remover coluna, mudar o grão | MAJOR — `v0.3.0` → `v1.0.0` |

```bash
git tag v0.3.0
git push origin v0.3.0
```

### Passo 11 — Aprovar o deploy

No GitHub: *Actions › CD › v0.3.0 › Review deployments › production › Approve and deploy*.
O deploy só continua após a aprovação de um dos revisores do Environment `production`.

### Passo 12 — Acompanhar e conferir

```bash
gh run watch
gh release view v0.3.0
```

Confira:

- o **Release** publicado em *Code › Releases*, com as notas geradas automaticamente;
- o registro do deploy em *Settings › Environments › production* (quem aprovou e quando);
- no Databricks, a execução do `job_comercial_diario` de Produção e o dashboard atualizado.

### Passo 13 — Atualizar o ambiente local

Necessário quando a mudança alterou o extrator, o ERP simulado ou as DAGs:

```bash
git checkout v0.3.0
docker compose up -d --build
git checkout main
```

---

## ⚡ Resumo em uma tela

```bash
# 0-1. Planejamento
gh issue create --title "..." --label feat
git checkout main && git pull
gh issue develop 15 --name feature/15-descricao --checkout

# 2-4. Desenvolvimento
ruff check . && python .github/scripts/verificar_isolamento.py && pytest tests/unit
databricks bundle deploy -t dev && databricks bundle run -t dev job_comercial_diario   # opcional

# 5-8. Integração
git add . && git commit -m "feat(gold): descrição"
git push -u origin feature/15-descricao
gh pr create --fill --body "Closes #15" && gh pr merge --auto --squash
gh pr checks --watch

# 9-13. Produção (após o merge)
git checkout main && git pull
git tag v0.3.0 && git push origin v0.3.0
# aprovar em Actions › CD › Review deployments
gh run watch && gh release view v0.3.0
git checkout v0.3.0 && docker compose up -d --build && git checkout main
```

---

## ⏪ Rollback

1. **Código:** reexecute o CD da tag anterior e aprove em *Review deployments*:
   ```bash
   gh run list --workflow cd.yml        # localize a execução da tag anterior
   gh run rerun <id-da-execucao>
   ```
2. **Ambiente local:** `git checkout <tag-anterior> && docker compose up -d --build`.
3. **Dados:** restaure a tabela com Time Travel e, se necessário, retroceda o watermark:
   ```sql
   DESCRIBE HISTORY silver.protheus.sc6;
   RESTORE TABLE silver.protheus.sc6 TO VERSION AS OF <versão>;
   UPDATE controle.ingestion_control SET ultimo_watermark = '<data-hora UTC>' WHERE tabela = 'sc6';
   ```
4. **Contenção:** desligue a extração da tabela com `"ativo": false` em `conf/ingestao.json` (via PR).
5. Registre o incidente e as ações em uma issue.

---

## 🤖 Pull Requests do Dependabot

O Dependabot abre PRs agrupados com atualizações **MINOR** e **PATCH** de bibliotecas, Actions e imagem Docker.
Eles passam pelo mesmo CI. Com os 5 checks verdes:

1. Abra o PR e clique em *Squash and merge*.
2. Se houver mais de um PR, após o primeiro merge use *Update branch* (ou comente `@dependabot rebase`) nos demais.
3. As atualizações chegam a Produção na próxima tag.

Versões **MAJOR** são ignoradas automaticamente e exigem avaliação manual (CCM).

---

## 🧯 Problemas comuns

| Sintoma | Causa provável | Solução |
|---|---|---|
| Commit bloqueado pelo pre-commit | ruff, gitleaks ou notebook com outputs | Leia a mensagem, corrija e commite de novo (o ruff já aplica correções simples) |
| Check "Lint, isolamento e SAST" vermelho | Lint, catálogo fixo ou alerta do Bandit | Rode `ruff check .` e `python .github/scripts/verificar_isolamento.py` localmente |
| Botão de merge bloqueado com checks verdes | Branch desatualizada em relação à `main` | Clique em *Update branch* no PR |
| Deploy em production parado | Aguardando aprovação | *Actions › CD › Review deployments* |
| Environment `dev` ou `prd` reaparece | Branch antiga com workflow antigo | Atualize ou feche a branch e exclua o environment |
| Job falha nos gates de qualidade | Dado inconsistente na carga | Veja a mensagem do notebook `qualidade_dados` no Databricks e abra uma issue de correção |
| `push` direto na `main` recusado | Proteção da branch (comportamento esperado) | Use uma branch e um Pull Request |
