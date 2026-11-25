# Aula 3 — Entrega contínua: staging, aprovação, baseline e rollback

## Entrega

| Item | Link |
|---|---|
| Release **v1.0.0** (primeira baseline automática, `.zip` anexado) | [v1.0.0](https://github.com/GChandrone/pdc-plataforma-dados-comercial/releases/tag/v1.0.0) |
| Execução do CD em que a produção foi aprovada | [run 45522060498](https://github.com/GChandrone/pdc-plataforma-dados-comercial/actions/runs/45522060498) |
| Release **v1.0.1** (`fix`) | ⏳ |
| Release **v1.1.0** (`feat`) | ⏳ |
| PR `docs: ...` que não dispara o CD | ⏳ |
| Execução do Rollback | ⏳ |
| PR `revert: ...` | ⏳ |

## Primeira versão automática (v1.0.0)

- Merge do PR [#29](https://github.com/GChandrone/pdc-plataforma-dados-comercial/pull/29) na `main`
  (commit [`4520bc2`](https://github.com/GChandrone/pdc-plataforma-dados-comercial/commit/4520bc291235f31bf3c5487acf25d6f0924c52f7)).
- Job **Versão e pacote**: `atual=0.1.4`, `versao=1.0.0`, `release=true` (o `!` do título `ci!:` gerou MAJOR).
- Job **Staging**: deploy do pacote no target `dev`, `job_setup` e `job_comercial_diario`.
  Na primeira tentativa o Databricks recusou iniciar jobs (`Triggering new runs ... is currently disabled
  temporarily`); os jobs que falharam foram reexecutados na mesma execução e passaram, com o mesmo pacote.
- Job **Produção**: aprovado por GChandrone no Environment `production` em 25/11/2026 01:11 UTC;
  deploy do mesmo pacote no target `prd`, smoke test, tag `v1.0.0` e Release com notas e
  `pdc-plataforma-dados-comercial-1.0.0.zip`.

## Critérios de conferência

| Critério | Situação |
|---|---|
| `cd.yml`, `rollback.yml` e `scripts/proxima-versao.mjs` no repositório | ✅ |
| Releases v1.0.0, v1.0.1 e v1.1.0 com notas e pacote anexado | ⏳ v1.0.0 ✅ |
| Toda produção aprovada no Environment `production` | ✅ até aqui (v1.0.0) |
| Rollback executado e aprovado; v1.0.0 marcada como *Latest* depois dele | ⏳ |
| Revert feito por PR, não por push direto | ⏳ |
