# Aula 4 — Governança: dependências, CCM e rastreabilidade

## Entrega

| Item | Link |
|---|---|
| `dependabot.yml` | [.github/dependabot.yml](../../../.github/dependabot.yml) |
| PR do Dependabot revisado (mesclado ou fechado com justificativa) | ⏳ [#27](https://github.com/GChandrone/pdc-plataforma-dados-comercial/pull/27) aguardando revisão |
| Issue de CCM com a decisão registrada | ⏳ |
| ADRs | [0001](../../adr/0001-extracao-no-sentido-inverso.md) · [0002](../../adr/0002-dois-ambientes-no-mesmo-workspace.md) · [0003](../../adr/0003-repositorio-publico.md) · [0004](../../adr/0004-check-agregador-ci-ok.md) · [0005 (risco aceito)](../../adr/0005-limite-de-vulnerabilidades-no-ci.md) |
| Onboarding | [docs/onboarding.md](../../onboarding.md) |
| PR do par seguindo o onboarding | ⏳ |
| Tabela de rastreabilidade da v1.1.0 | ⏳ abaixo (preenchida por enquanto com a v1.0.0) |

## Segurança de dependências (PGC 13)

- *Settings → Advanced Security*: **Dependency graph**, **Dependabot alerts** e **Dependabot security
  updates** ativos desde 25/11/2026.
- O CI bloqueia apenas vulnerabilidades `critical` (risco aceito no ADR 0005, revisão em 30/01/2027).

## Rastreabilidade de ponta a ponta (PGC 10)

A entrega pede a **v1.1.0**. Até ela existir, a cadeia abaixo mostra o mesmo caminho para a **v1.0.0**.

| Elo | v1.0.0 | v1.1.0 |
|---|---|---|
| Release | [v1.0.0](https://github.com/GChandrone/pdc-plataforma-dados-comercial/releases/tag/v1.0.0) | ⏳ |
| Commit da tag | [`4520bc2`](https://github.com/GChandrone/pdc-plataforma-dados-comercial/commit/4520bc291235f31bf3c5487acf25d6f0924c52f7) | ⏳ |
| Pull Request | [#29](https://github.com/GChandrone/pdc-plataforma-dados-comercial/pull/29) | ⏳ |
| Revisão e aprovação do par | GabBruno aprovou o #29 (sem comentário em linha — falha de processo registrada) | ⏳ |
| CI que liberou o merge | [run 45520430846](https://github.com/GChandrone/pdc-plataforma-dados-comercial/actions/runs/45520430846) e [titulo-pr](https://github.com/GChandrone/pdc-plataforma-dados-comercial/actions/runs/45520430871) | ⏳ |
| Issue de origem | [#28](https://github.com/GChandrone/pdc-plataforma-dados-comercial/issues/28) (`Closes #28`) | ⏳ |
| Aprovação da produção | GChandrone, 25/11/2026 01:11 UTC — [run 45522060498](https://github.com/GChandrone/pdc-plataforma-dados-comercial/actions/runs/45522060498) | ⏳ |

## Critérios de conferência

| Critério | Situação |
|---|---|
| Alertas e atualizações de segurança do Dependabot ativos | ✅ |
| `dependabot.yml` com o ecossistema da stack e com `github-actions`, prefixo `chore(deps)` | ✅ |
| PR do Dependabot tratado com revisão e justificativa | ⏳ |
| Issue de CCM com critério de risco, plano de rollback citando tag real e decisão do par | ⏳ |
| Dois ADRs completos, um deles sobre o risco aceito | ✅ ADRs 0004 e 0005 |
| Onboarding seguido pelo par sem ajuda, com PR de melhoria | ⏳ |
| Cadeia Release → commit → PR → revisão → CI → Issue → aprovação completa | ⏳ v1.0.0 ✅ (com a falha do comentário apontada) |
