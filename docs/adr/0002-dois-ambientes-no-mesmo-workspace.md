# ADR 0002 — Desenvolvimento e Produção no mesmo workspace, separados por catálogo

- **Status:** aceita
- **Data:** 23/09/2026

## Contexto

A Free Edition permite um workspace por conta. Usar duas contas duplicaria configurações e acessos.

## Decisão

Um único workspace, com catálogos prefixados por ambiente (`dev_bronze`, `dev_silver`, `dev_gold` e `bronze`,
`silver`, `gold`) e os targets `dev` e `prd` do Asset Bundle. A landing e a fonte são compartilhadas, como um
ERP real consultado pelos dois ambientes; cada ambiente controla sua própria carga na Bronze.

## Consequências

- Isolamento lógico, não físico: garantido pela parametrização dos catálogos e pela verificação de isolamento
  no CI.
- Cota diária e limite de 5 tarefas simultâneas compartilhados entre os ambientes.
