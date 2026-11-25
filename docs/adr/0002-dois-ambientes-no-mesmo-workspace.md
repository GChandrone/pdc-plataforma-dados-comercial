# 0002 — Staging e produção no mesmo workspace, separados por catálogo

- Status: aceito
- Data: 23/09/2026

## Contexto

A Free Edition permite um workspace por conta. O PGC exige ambientes separados de staging e
produção, promovidos pelo pipeline.

## Decisão

Um único workspace, com catálogos prefixados por ambiente (`dev_bronze`, `dev_silver`, `dev_gold`
em staging; `bronze`, `silver`, `gold` em produção) e os targets `dev` e `prd` do Asset Bundle,
ligados aos Environments `staging` e `production` do GitHub. A landing e a fonte são compartilhadas,
como um ERP real consultado pelos dois ambientes; cada ambiente controla sua própria carga na Bronze.

## Alternativas consideradas

- **Duas contas Free Edition (um workspace por ambiente):** isolamento físico, mas duplica acessos,
  tokens e configurações, e não há catálogo compartilhado entre contas.
- **Apenas um ambiente:** descumpre o PGC (seção 3.2).

## Consequências

- Isolamento lógico, não físico: garantido pela parametrização dos catálogos e pela verificação de
  isolamento no CI.
- Cota diária e limite de 5 tarefas simultâneas compartilhados entre os ambientes.
