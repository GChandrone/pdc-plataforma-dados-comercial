# ADR 0003 — Repositório público no GitHub

- **Status:** aceita
- **Data:** 23/09/2026

## Contexto

No plano gratuito do GitHub, proteção de branch, secrets de Environment e aprovação manual de deploy
(required reviewers) só estão disponíveis em repositórios públicos.

## Decisão

O repositório é público. Isso é viável porque o projeto usa apenas dados fictícios e nenhum segredo é
versionado (tokens nos GitHub Secrets; senhas no `.env` local, ignorado pelo Git; gitleaks no pre-commit e no CI).
