# 0004 — Um único check obrigatório de CI (`ci-ok`) e versão calculada pelo título do PR

- Status: aceito
- Data: 24/11/2026

## Contexto

O CI tem cinco verificações independentes (qualidade, dependências, segredos, Airflow e bundle).
Marcar cada uma como obrigatória na proteção da `main` cria dois problemas: um job que não roda
(por exemplo, a análise de dependências em execução manual) deixa o PR travado em "Expected —
Waiting for status", e cada job novo exige alterar a proteção. Além disso, a versão era definida
manualmente por tag, sujeita a erro humano e sem ligação com o tipo de mudança.

## Decisão

1. Um job `ci-ok` roda sempre (`if: always()`) e só fica verde se nenhum outro job falhou.
   Somente `ci-ok` e `titulo-pr` são obrigatórios na proteção da `main`.
2. O título do PR, validado pelo `titulo-pr` (Conventional Commits), vira o commit na `main` (squash)
   e define a próxima versão no CD (`scripts/proxima-versao.mjs`): `feat` → MINOR, `fix`/`perf` →
   PATCH, `!` → MAJOR; `docs`, `chore`, `ci` e `test` não geram versão.

## Alternativas consideradas

- **Os cinco jobs obrigatórios:** frágil, como descrito no contexto.
- **Tag manual para cada release:** funcionava, mas dependia de alguém escolher o número correto.

## Consequências

- A proteção da `main` não muda quando um job é incluído no CI.
- A versão passa a refletir o tipo de mudança; um título errado gera versão errada, por isso o
  par de revisão confere o título na revisão do PR.
