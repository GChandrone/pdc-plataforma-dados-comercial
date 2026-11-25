# Aula 2 — Integração contínua

## Entrega

| Item | Link |
|---|---|
| PR que adicionou o CI (mesclado por squash) | [#29 — `ci!: adota CI/CD do PGC com versão automática`](https://github.com/GChandrone/pdc-plataforma-dados-comercial/pull/29) |
| Execução do CI verde no PR #29 (`ci-ok`) | [run 45520430846](https://github.com/GChandrone/pdc-plataforma-dados-comercial/actions/runs/45520430846) |
| Execução do `titulo-pr` verde no PR #29 | [run 45520430871](https://github.com/GChandrone/pdc-plataforma-dados-comercial/actions/runs/45520430871) |
| PR de teste em que as falhas foram provocadas (revisado, comentado e mesclado) | [#34 — `test(lib): cobre validações de identificadores do pdc_lib.util`](https://github.com/GChandrone/pdc-plataforma-dados-comercial/pull/34) |
| Revisão feita no repositório do par | ⏳ link do PR revisado por GChandrone no repositório do GabBruno |

## Três falhas provocadas e corrigidas (PR #34)

| # | Provocado | Check que falhou | Execução que falhou | Correção |
|---|---|---|---|---|
| 1 | Título do PR alterado para `ajustes` | `titulo-pr` | [run 45524678914](https://github.com/GChandrone/pdc-plataforma-dados-comercial/actions/runs/45524678914) | título trocado para `test(lib): ...` |
| 2 | Variável `esperado` declarada e não usada | `qualidade` → Lint (`F841`) | [run 45524742006](https://github.com/GChandrone/pdc-plataforma-dados-comercial/actions/runs/45524742006) | variável passou a ser usada no `assert` |
| 3 | Valor esperado errado (`sc5` → `sc6`) | `qualidade` → Testes (`AssertionError`) | [run 45525036271](https://github.com/GChandrone/pdc-plataforma-dados-comercial/actions/runs/45525036271) | valor esperado corrigido |

## Critérios de conferência

| Critério | Situação |
|---|---|
| `ci.yml` com lint, testes, quality gate de cobertura e análise de dependências | ✅ jobs `qualidade`, `dependencias`, `segredos`, `airflow`, `bundle` e `ci-ok` |
| `pr-titulo.yml` presente e funcionando | ✅ falha 1 acima |
| `ci-ok` e `titulo-pr` obrigatórios na proteção da `main` | ✅ `checks-obrigatorios-main.jpg` |
| Pelo menos 1 teste; limite de 60% configurado | ✅ `--cov-fail-under=60`; cobertura de **70,8%** no PR #29 |
| Três falhas provocadas e corrigidas, com links | ✅ tabela acima |
| PR revisado pelo par, com comentário respondido, e mesclado por squash | ✅ PR #34: [comentário do GabBruno](https://github.com/GChandrone/pdc-plataforma-dados-comercial/pull/34#discussion_r4689029173) em `tests/unit/test_util.py` (linha 13), [resposta de GChandrone](https://github.com/GChandrone/pdc-plataforma-dados-comercial/pull/34#discussion_r4689041133), aprovação de GabBruno e squash merge ([`d441dda`](https://github.com/GChandrone/pdc-plataforma-dados-comercial/commit/d441dda)). O PR #29 foi aprovado sem comentário em linha (falha de processo corrigida no #34) |
| Revisão feita no repositório do par | ⏳ |

## Prints

- `checks-obrigatorios-main.jpg` — regra da `main` com somente `ci-ok` e `titulo-pr` obrigatórios.
