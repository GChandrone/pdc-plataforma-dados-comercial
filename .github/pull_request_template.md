<!--
Título do PR: siga Conventional Commits — ele vira a mensagem do commit na main
e define a próxima versão. Ex.: feat(gold): inclui vlr_desconto na fato_pedido_venda
feat -> MINOR · fix/perf -> PATCH · "!" ou BREAKING CHANGE -> MAJOR · docs/chore/ci/test -> sem versão
-->

## Contexto
<!-- Por que esta mudança é necessária? Qual Issue ela resolve? -->

## Decisão tomada
<!-- O que foi feito e por quê. Alternativas descartadas, se houver. -->

## Como testar
1.
2.

## Checklist (PGC 5.2)
- [ ] O PR é pequeno e trata de um único assunto
- [ ] Há testes cobrindo o caso principal
- [ ] Branch e título seguem a convenção (`feature/<issue>-<descricao>`, Conventional Commits)
- [ ] Nenhum segredo, token ou senha no código (use GitHub Secrets)
- [ ] Nenhum catálogo citado de forma fixa e notebooks salvos sem outputs
- [ ] Impacto no modelo Gold avaliado (colunas, grão, COMMENT)
- [ ] Mudança de alto risco? (modelo Gold incompatível, regra de indicador, RESTORE/reprocessamento, LGPD, hotfix) → abri a Issue de CCM

Closes #
