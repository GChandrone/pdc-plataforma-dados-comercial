# Evidências de configuração do repositório

Geradas automaticamente pelo script `configurar_github.sh` a partir da API do GitHub.

| Arquivo | Evidência |
|---|---|
| `01-push-direto-recusado.txt` | Tentativa de push direto na `main` recusada pela proteção da branch |
| `02-protecao-main.json` | Regra da `main`: PR obrigatório, 5 checks obrigatórios e `enforce_admins` (sem bypass) |
| `03-par-revisao.json` | Par de revisão como colaborador com permissão de escrita |
| `04-environments.json` | Environments `staging` e `production`, este com o dono do repositório como revisor obrigatório e um aprovador adicional |
| `05-production-tags.json` | `production` aceita deploy somente a partir de tags `v*.*.*` |

Prints complementares (aprovação em *Review deployments*, PR com checks verdes) podem ser adicionados nesta pasta.
