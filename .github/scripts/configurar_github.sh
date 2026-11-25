#!/usr/bin/env bash
# =============================================================================
# configurar_github.sh — configura o repositório conforme o PGC (Aulas 1 a 4)
#
#  1. Somente squash merge (título e descrição do PR), auto-merge e exclusão de branches
#  2. Environments: staging (branches protegidas) e production (revisores obrigatórios,
#     branches protegidas, sem bypass de administradores)
#  3. Secrets do Databricks: repositório (CI), environments (CD) e Dependabot
#  4. Proteção da main: PR com 1 aprovação, aprovações descartadas em novos commits,
#     checks obrigatórios ci-ok e titulo-pr, histórico linear e sem exceções
#  5. Alertas e atualizações de segurança do Dependabot
#
# Uso (Git Bash, Linux ou Mac), na raiz do repositório, com "gh auth login" feito:
#   bash .github/scripts/configurar_github.sh [aprovador-adicional]   # padrão: GabBruno
#
# Host e token são lidos do teclado e enviados direto ao GitHub (nada é gravado em arquivo).
# =============================================================================
set -euo pipefail

APROVADOR="${1:-GabBruno}"
DESCRICAO="Plataforma de Dados Comercial — PoC de GCS e CI/CD (Databricks, Airflow e GitHub Actions)"

ok()    { printf '\033[0;32m    ✔ %s\033[0m\n' "$1"; }
etapa() { printf '\n\033[1;34m==> %s\033[0m\n' "$1"; }

command -v gh >/dev/null || { echo "GitHub CLI (gh) não encontrado: https://cli.github.com"; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "Execute antes: gh auth login"; exit 1; }
REPO="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"
DONO_ID="$(gh api user --jq .id)"
APROVADOR_ID="$(gh api "users/$APROVADOR" --jq .id)"
ok "Repositório: $REPO"

etapa "1. Merge"
gh repo edit "$REPO" --description "$DESCRICAO" --enable-auto-merge --delete-branch-on-merge \
  --enable-squash-merge --enable-merge-commit=false --enable-rebase-merge=false >/dev/null
gh api -X PATCH "repos/$REPO" -f squash_merge_commit_title=PR_TITLE -f squash_merge_commit_message=PR_BODY --silent
ok "Somente squash merge, com o título e a descrição do PR"

etapa "2. Environments"
gh api -X PUT "repos/$REPO/environments/staging" --silent --input - <<JSON
{"deployment_branch_policy": {"protected_branches": true, "custom_branch_policies": false}}
JSON
ok "staging: somente branches protegidas"
gh api -X PUT "repos/$REPO/environments/production" --silent --input - <<JSON
{
  "prevent_self_review": false,
  "can_admins_bypass": false,
  "reviewers": [{"type": "User", "id": $DONO_ID}, {"type": "User", "id": $APROVADOR_ID}],
  "deployment_branch_policy": {"protected_branches": true, "custom_branch_policies": false}
}
JSON
ok "production: revisores obrigatórios, somente branches protegidas, sem bypass"

etapa "3. Secrets do Databricks"
read -r  -p "    URL do workspace (https://dbc-....cloud.databricks.com): " DB_HOST
read -rs -p "    Token do Databricks (não aparece na tela): " DB_TOKEN; echo
DB_HOST="${DB_HOST%/}"
for destino in "--repo $REPO" "--env staging --repo $REPO" "--env production --repo $REPO" "--app dependabot --repo $REPO"; do
  # shellcheck disable=SC2086
  printf '%s' "$DB_HOST"  | gh secret set DATABRICKS_HOST  $destino
  # shellcheck disable=SC2086
  printf '%s' "$DB_TOKEN" | gh secret set DATABRICKS_TOKEN $destino
done
unset DB_TOKEN
ok "Repositório (CI), staging e production (CD) e Dependabot"

etapa "4. Proteção da main"
gh api -X PUT "repos/$REPO/branches/main/protection" --silent --input - <<JSON
{
  "required_status_checks": {"strict": true, "contexts": ["ci-ok", "titulo-pr"]},
  "enforce_admins": true,
  "required_pull_request_reviews": {"required_approving_review_count": 1, "dismiss_stale_reviews": true},
  "required_linear_history": true,
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON
ok "PR com 1 aprovação, checks ci-ok e titulo-pr, histórico linear e sem exceções"

etapa "5. Segurança de dependências"
gh api -X PUT "repos/$REPO/vulnerability-alerts" --silent
gh api -X PUT "repos/$REPO/automated-security-fixes" --silent
ok "Dependabot alerts e security updates ativos"

printf '\nConcluído.\n'
