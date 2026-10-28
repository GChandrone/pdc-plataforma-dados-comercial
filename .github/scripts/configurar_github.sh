#!/usr/bin/env bash
# =============================================================================
# configurar_github.sh — aplica as configurações exigidas na atividade de GCS
#
#  1. Descrição do repositório, auto-merge e exclusão automática de branches
#  2. Environments "staging" e "production" (production com revisor obrigatório
#     e deploy restrito a tags v*.*.*), com os secrets do Databricks
#  3. Secrets do Dependabot
#  4. Proteção da main (PR obrigatório, 5 checks obrigatórios, sem bypass)
#  5. Conferência do par de revisão (permissão de escrita)
#  6. Evidências em docs/evidencias/ (push direto recusado + configurações em JSON)
#  7. Branch + commit + Pull Request com auto-merge (PGC, workflows, README e evidências)
#
# Pré-requisitos: git, GitHub CLI (gh) autenticado com "gh auth login" (escopo repo),
# executar na raiz do repositório, com os arquivos novos já copiados para a pasta
# (.github/workflows/ci.yml, .github/workflows/cd.yml, README.md e docs/pgc/).
#
# Uso (Git Bash no Windows, Linux ou Mac):
#   bash configurar_github.sh --revisor <usuario-github-do-andre>
#   bash configurar_github.sh --revisor <usuario> --aprovador <usuario>   # aprovador adicional; padrão: GabBruno
#   bash configurar_github.sh --remover-antigos      # depois que o CD rodar com staging
#
# Nenhum segredo é gravado em arquivo: host e token são lidos do teclado e enviados
# direto ao GitHub, que os armazena criptografados.
# =============================================================================
set -euo pipefail

REVISOR=""
APROVADOR="GabBruno"   # aprovador adicional (opcional) do Environment production, junto com o dono
REMOVER_ANTIGOS="nao"
BRANCH="docs/pgc-environments"
DESCRICAO="Plataforma de Dados Comercial — PoC de GCS e CI/CD (Databricks, Airflow e GitHub Actions)"
CHECKS='["Lint, isolamento e SAST","Testes unitários e de integração","Varredura de segredos (gitleaks)","Build da imagem do Airflow e importação das DAGs","Validação do Asset Bundle"]'

while [[ $# -gt 0 ]]; do
  case "$1" in
    --revisor) REVISOR="$2"; shift 2 ;;
    --aprovador) APROVADOR="$2"; shift 2 ;;
    --remover-antigos) REMOVER_ANTIGOS="sim"; shift ;;
    *) echo "Parâmetro desconhecido: $1"; exit 1 ;;
  esac
done

etapa() { printf '\n\033[1;34m==> %s\033[0m\n' "$1"; }
ok()    { printf '\033[0;32m    ✔ %s\033[0m\n' "$1"; }
aviso() { printf '\033[0;33m    ! %s\033[0m\n' "$1"; }

# ---------------------------------------------------------------- verificações
etapa "Verificando pré-requisitos"
command -v git >/dev/null || { echo "git não encontrado"; exit 1; }
command -v gh  >/dev/null || { echo "GitHub CLI (gh) não encontrado: https://cli.github.com"; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "Execute antes: gh auth login"; exit 1; }
git rev-parse --show-toplevel >/dev/null 2>&1 || { echo "Execute na raiz do repositório"; exit 1; }
cd "$(git rev-parse --show-toplevel)"

REPO="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"
DONO="$(gh api user --jq .login)"
DONO_ID="$(gh api user --jq .id)"
ok "Repositório: $REPO | usuário: $DONO"

# ---------------------------------------------------------------- remoção dos antigos
if [[ "$REMOVER_ANTIGOS" == "sim" ]]; then
  etapa "Removendo Environments antigos (dev e prd)"
  for amb in dev prd; do
    if gh api "repos/$REPO/environments/$amb" >/dev/null 2>&1; then
      gh api -X DELETE "repos/$REPO/environments/$amb" --silent && ok "Environment $amb removido"
    else
      ok "Environment $amb não existe"
    fi
  done
  exit 0
fi

[[ -n "$REVISOR" ]] || { echo "Informe o usuário do par de revisão: --revisor <usuario>"; exit 1; }
for arquivo in .github/workflows/ci.yml .github/workflows/cd.yml README.md; do
  [[ -f "$arquivo" ]] || { echo "Arquivo não encontrado: $arquivo"; exit 1; }
done
grep -q "environment: production" .github/workflows/cd.yml \
  || { echo "O cd.yml ainda usa os ambientes antigos: copie a versão nova antes de continuar"; exit 1; }
ls docs/pgc/* >/dev/null 2>&1 || { echo "Coloque o PGC (.docx e .pdf) em docs/pgc/ antes de continuar"; exit 1; }

# ---------------------------------------------------------------- 1. repositório
etapa "1. Configurações gerais do repositório"
gh repo edit "$REPO" --description "$DESCRICAO" --enable-auto-merge --delete-branch-on-merge \
  --enable-squash-merge --enable-merge-commit=false --enable-rebase-merge=false >/dev/null
gh api -X PATCH "repos/$REPO" -f squash_merge_commit_title=PR_TITLE -f squash_merge_commit_message=PR_BODY --silent
ok "Descrição, auto-merge, somente squash merge (título e descrição do PR) e exclusão automática de branches"

# ---------------------------------------------------------------- 2. environments
etapa "2. Environments staging e production"
read -r  -p "    URL do workspace Databricks (https://dbc-....cloud.databricks.com): " DB_HOST
read -rs -p "    Token do Databricks (não aparece na tela): " DB_TOKEN; echo
DB_HOST="${DB_HOST%/}"
[[ "$DB_HOST" == https://* && -n "$DB_TOKEN" ]] || { echo "Host ou token inválido"; exit 1; }

gh api -X PUT "repos/$REPO/environments/staging" --silent --input - <<JSON
{"deployment_branch_policy": {"protected_branches": true, "custom_branch_policies": false}}
JSON
ok "staging criado, aceitando deploy somente de branches protegidas (main)"

APROVADOR_ID="$(gh api "users/$APROVADOR" --jq .id 2>/dev/null)" \
  || { echo "Usuário aprovador '$APROVADOR' não encontrado no GitHub"; exit 1; }

configurar_production() {
  gh api -X PUT "repos/$REPO/environments/production" --silent --input - <<JSON
{
  "wait_timer": 0,
  "prevent_self_review": false,
  "can_admins_bypass": false,
  "reviewers": [{"type": "User", "id": $DONO_ID}, {"type": "User", "id": $APROVADOR_ID}],
  "deployment_branch_policy": {"protected_branches": false, "custom_branch_policies": true}
}
JSON
}

if ! configurar_production 2>/dev/null; then
  # Todo revisor precisa ter acesso ao repositório: convida o aprovador adicional e tenta de novo.
  gh api -X PUT "repos/$REPO/collaborators/$APROVADOR" -f permission=push --silent || true
  if ! configurar_production 2>/dev/null; then
    aviso "Convite enviado a $APROVADOR. Peça para ele aceitar em github.com/notifications e rode o script de novo."
    exit 1
  fi
fi
ok "production criado com $DONO (obrigatório) e $APROVADOR como revisores; basta uma aprovação, sem bypass de administradores"

if gh api "repos/$REPO/environments/production/deployment-branch-policies" \
     --jq '.branch_policies[] | select(.name=="v*.*.*" and .type=="tag") | .id' | grep -q .; then
  ok "Regra de tag v*.*.* já existia"
else
  gh api -X POST "repos/$REPO/environments/production/deployment-branch-policies" \
     -f name='v*.*.*' -f type=tag --silent
  ok "production aceita deploy somente a partir de tags v*.*.*"
fi

for amb in staging production; do
  printf '%s' "$DB_HOST"  | gh secret set DATABRICKS_HOST  --env "$amb" --repo "$REPO"
  printf '%s' "$DB_TOKEN" | gh secret set DATABRICKS_TOKEN --env "$amb" --repo "$REPO"
  ok "Secrets DATABRICKS_HOST e DATABRICKS_TOKEN em $amb"
done

# Secrets do repositório: usados pela validação do bundle no CI (branches dos Pull Requests).
printf '%s' "$DB_HOST"  | gh secret set DATABRICKS_HOST  --repo "$REPO"
printf '%s' "$DB_TOKEN" | gh secret set DATABRICKS_TOKEN --repo "$REPO"
ok "Secrets do repositório para a validação do bundle no CI"

# ---------------------------------------------------------------- 3. dependabot
etapa "3. Secrets do Dependabot"
printf '%s' "$DB_HOST"  | gh secret set DATABRICKS_HOST  --app dependabot --repo "$REPO"
printf '%s' "$DB_TOKEN" | gh secret set DATABRICKS_TOKEN --app dependabot --repo "$REPO"
unset DB_TOKEN
ok "PRs do Dependabot também conseguem validar o bundle"

# ---------------------------------------------------------------- 4. proteção da main
etapa "4. Proteção da branch main"
gh api -X PUT "repos/$REPO/branches/main/protection" --silent --input - <<JSON
{
  "required_status_checks": {"strict": true, "contexts": $CHECKS},
  "enforce_admins": true,
  "required_pull_request_reviews": {"required_approving_review_count": 1, "dismiss_stale_reviews": true},
  "required_linear_history": true,
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": false
}
JSON
ok "PR com 1 aprovação, aprovações descartadas em novos commits, 5 checks, histórico linear e sem exceções"

# ---------------------------------------------------------------- 5. par de revisão
etapa "5. Par de revisão ($REVISOR)"
PERMISSAO="$(gh api "repos/$REPO/collaborators/$REVISOR/permission" --jq .permission 2>/dev/null || echo none)"
case "$PERMISSAO" in
  admin|write|maintain) ok "$REVISOR é colaborador com permissão '$PERMISSAO'" ;;
  *)
    gh api -X PUT "repos/$REPO/collaborators/$REVISOR" -f permission=push --silent
    aviso "Convite com permissão de escrita enviado a $REVISOR: ele precisa aceitar em github.com/notifications"
    ;;
esac

# ---------------------------------------------------------------- 6. evidências
etapa "6. Gerando evidências em docs/evidencias/"
mkdir -p docs/evidencias
git fetch origin main --quiet

# Push direto na main: cria um commit vazio em memória (sem alterar nada local) e tenta enviá-lo.
TESTE="$(git commit-tree "origin/main^{tree}" -p origin/main -m "teste de push direto na main")"
{
  echo "# Evidência: push direto na main recusado"
  echo "# Data (UTC): $(date -u '+%Y-%m-%d %H:%M:%S')"
  echo "# Comando: git push origin <commit>:refs/heads/main"
  echo
  if git push origin "$TESTE:refs/heads/main" 2>&1; then
    echo; echo "ATENÇÃO: o push foi ACEITO — a proteção não está ativa."
  fi
} > docs/evidencias/01-push-direto-recusado.txt
if grep -q "ATENÇÃO" docs/evidencias/01-push-direto-recusado.txt; then
  aviso "O push direto foi aceito! Verifique a proteção da main antes de continuar."; exit 1
fi
ok "01-push-direto-recusado.txt"

gh api "repos/$REPO/branches/main/protection" > docs/evidencias/02-protecao-main.json
gh api "repos/$REPO/collaborators/$REVISOR/permission" \
  --jq '{usuario: .user.login, permissao: .permission, papel: .role_name}' \
  > docs/evidencias/03-par-revisao.json 2>/dev/null || echo '{"pendente": "convite enviado"}' > docs/evidencias/03-par-revisao.json
gh api "repos/$REPO/environments" \
  --jq '[.environments[] | {nome: .name, regras: [.protection_rules[]? | {tipo: .type, revisores: [.reviewers[]?.reviewer.login]}], politica_de_deploy: .deployment_branch_policy}]' \
  > docs/evidencias/04-environments.json
gh api "repos/$REPO/environments/production/deployment-branch-policies" \
  --jq '[.branch_policies[] | {padrao: .name, tipo: .type}]' > docs/evidencias/05-production-tags.json
ok "02 a 05: configurações exportadas em JSON (nenhum segredo é exportado pela API)"

cat > docs/evidencias/README.md <<'MD'
# Evidências de configuração do repositório

Geradas automaticamente pelo script `configurar_github.sh` a partir da API do GitHub.

| Arquivo | Evidência |
|---|---|
| `01-push-direto-recusado.txt` | Tentativa de push direto na `main` recusada pela proteção da branch |
| `02-protecao-main.json` | Regra da `main`: PR obrigatório, 5 checks obrigatórios e `enforce_admins` (sem bypass) |
| `03-par-revisao.json` | Par de revisão como colaborador com permissão de escrita |
| `04-environments.json` | Environments `staging` e `production`, este com o dono do repositório como revisor obrigatório e um aprovador adicional |
| `05-production-tags.json` | `production` aceita deploy somente a partir de tags `v*.*.*` |

Prints complementares (aprovação em *Review deployments*, PR com checks verdes) podem ser adicionados nesta pasta.
MD
ok "README.md das evidências"

# ---------------------------------------------------------------- 7. pull request
etapa "7. Branch, commit e Pull Request"
git checkout -B "$BRANCH" >/dev/null 2>&1
git add -A
git commit -m "docs: publica PGC, evidências e environments staging/production" >/dev/null
git push -u origin "$BRANCH" --force-with-lease >/dev/null 2>&1
URL_PR="$(gh pr create --base main --head "$BRANCH" \
  --title "docs: publica PGC, evidências e environments staging/production" \
  --body "Publica o PGC como item de configuração (docs/pgc/), ajusta os workflows para os Environments staging e production e adiciona as evidências de configuração (docs/evidencias/)." \
  2>/dev/null || gh pr view "$BRANCH" --json url --jq .url)"
gh pr merge "$BRANCH" --auto --squash >/dev/null
ok "PR com auto-merge: $URL_PR"

etapa "Concluído"
cat <<TXT
    Próximos passos (manuais, por serem decisões):
      1. Aguarde os 5 checks do PR; o merge acontece sozinho e o CD faz o deploy em staging.
      2. Gere a primeira release em production:
           git checkout main && git pull && git tag v0.1.1 && git push origin v0.1.1
         e aprove em Actions > CD > Review deployments (você ou $APROVADOR).
      3. Depois do deploy com sucesso, remova os Environments antigos:
           bash configurar_github.sh --remover-antigos
TXT
