# Aula 1 — Repositório, proteção da `main` e environments

| Arquivo | Item da atividade | Evidência |
|---|---|---|
| `01-push-direto-recusado-terminal.png` | Recusa do push direto na `main` | `git push` recusado com `GH006: Protected branch update failed` |
| `02-par-revisao-write.png` | Par de revisão com acesso de escrita | GabBruno como colaborador do repositório (repositório pessoal: colaboradores têm permissão de escrita) |
| `03-environments.png` | Environments | `staging` e `production` configurados |
| `04-production-revisor.png` | Revisor obrigatório em production (configuração **antiga**) | GChandrone em *Required reviewers* e deploy restrito às tags `v*.*.*` |
| `05-production-branches-protegidas.jpg` | Revisor obrigatório em production (configuração **atual**, Aula 3) | GChandrone em *Required reviewers*, sem bypass de administradores e *Protected branches only* (somente a `main`) |

O print `04` foi mantido como histórico: a regra por tag foi substituída por *Protected branches only*
quando o CD passou a rodar no merge da `main` e a criar a tag pelo próprio pipeline (Aula 3).
