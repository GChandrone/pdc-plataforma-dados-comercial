# 0003 — Repositório público no GitHub

- Status: aceito
- Data: 23/09/2026

## Contexto

No plano gratuito do GitHub, proteção de branch, secrets de Environment, aprovação manual de deploy
(required reviewers) e a análise de dependências no PR só estão disponíveis em repositórios públicos.

## Decisão

O repositório é público. Isso é viável porque o projeto usa apenas dados fictícios e nenhum segredo
é versionado (tokens nos GitHub Secrets; senhas no `.env` local, ignorado pelo Git; gitleaks no
pre-commit e no CI).

## Alternativas consideradas

- **Repositório privado com GitHub Pro/Team:** custo, e o Pro sozinho não libera aprovação de deploy
  em repositório privado.
- **Repositório privado sem os controles:** perderia a proteção da `main` e o gate de produção.

## Consequências

- Todos os controles do PGC disponíveis sem custo.
- Qualquer pessoa pode ler o código: exige disciplina com segredos e dados (somente fictícios).
