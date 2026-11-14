# Auditoria de Cobertura de Rotas — 2026-11

**Data:** 2026-11-14
**Base auditada:** `main` em `1e9c265` (a matriz foi gerada na branch do PR #106, `00dce1d`, e repetida em
`1e9c265`, com resultado idêntico: o #106 não altera nenhum `.py` nem `frontend/src`).
**Tipo:** análise estática, sem executar o app, sem acessar produção e sem alterar código.
**Achados registrados:** KI-069 a KI-076 em `docs/operations/KNOWN_ISSUES.md`.

> **Este documento é um retrato do commit `1e9c265`, não uma fotografia permanente do sistema.** Quando os
> hotfixes #101 a #106 forem integrados, rotas, permissões e testes podem mudar. Para saber o estado atual,
> refaça a auditoria; não atualize esta matriz à mão.

> **Ausência de teste não é vulnerabilidade confirmada.** A matriz aponta onde o comportamento **não está
> comprovado** por teste automatizado. Ela não afirma que alguma rota esteja com defeito ou com falha de
> autorização.

---

## 1. Método

1. **Rotas:** parse (AST) de todos os `.py` da raiz. Cada decorator `@<blueprint>.route/get/post/...` foi
   combinado com o `url_prefix` do `Blueprint(...)` do mesmo arquivo; as 5 rotas declaradas direto em
   `app.py` (`/health`, `/ready`, `/metrics`, `/app/...`) foram somadas à mão. Resultado: **150 rotas, 153
   pares rota + método** (151 sem contar os 2 `OPTIONS`, que são as linhas da matriz).
2. **Autorização:** leitura do corpo de cada handler. `logado` = checa `session["usuario_id"]`/`usuario_logado()`;
   `perfis: ...` = devolve 403 para perfis fora da lista (inclusive via helpers como `usuario_pode_financeiro()`);
   rotas legadas (`main_views`, `auth_views`) seguem o `ROUTE_PERMISSIONS` de `app.py`. Onde o perfil só
   esconde campos (sem 403), a coluna diz "máscara". Valores marcados com ✔ foram conferidos manualmente no
   código; os demais são heurísticos.
3. **Testes:** busca do path (com parâmetros como `{id}`/`123`) em `tests/*.py`, identificando o método pelo
   `client.get/post/...` da mesma linha. A coluna 401/403 conta as funções de teste que citam a rota **e** o
   código de status.
4. **Frontend:** cruzamento dos endpoints chamados em `frontend/src/api/client.js` com as rotas do backend, e
   das rotas do SPA (`App.jsx`) com os cenários do E2E (`frontend/tests/e2e/app.spec.js`).

### Limitações (o que esta auditoria NÃO comprova)

- A classificação de autorização é heurística fora das linhas marcadas com ✔.
- Testes que montam a URL por variável ou por helper podem não ter sido reconhecidos, gerando falsos "sem
  teste". Linhas com `?` têm o path no teste, mas o método não foi identificado na mesma linha (em geral, são
  chamadas quebradas em várias linhas).
- Testes de serviço (sem HTTP) não contam como cobertura da rota, de propósito: eles não exercitam a
  checagem de sessão e de perfil, que fica no controller.
- Os 211 testes unitários do frontend não foram mapeados tela por tela.
- Nada foi executado: nenhuma afirmação aqui é sobre comportamento observado em execução.

---

## 2. Resumo

| Indicador | Valor |
|---|---|
| Pares rota + método (sem `OPTIONS`) | 151 |
| Com teste HTTP identificado | 95 |
| Path presente no teste, método não identificado (`?`) | 11 |
| **Sem teste HTTP identificado** | **45** |
| Rotas autenticadas sem nenhum teste de 401 identificado | 87 de 136 |
| Rotas com restrição de perfil (403) sem teste de 403 identificado | 30 de 64 |
| Testes HTTP identificados para caixa, contas a pagar e contas a receber | 0 (19 pares) |
| Telas do SPA percorridas pelo E2E | cerca de 6 de 28 |

> Nota: o relatório preliminar apresentado em chat no mesmo dia citava "89/138" e "13 ambíguos". A diferença
> vem da conferência manual da autorização de algumas rotas (públicas por design e máscaras de campo) e da
> exclusão das linhas `OPTIONS`; os números acima são os finais.

### Os 45 pares sem teste HTTP, por grupo

| Grupo | Pares | KI |
|---|---|---|
| Caixa, contas a pagar, contas a receber | 19 | KI-069 |
| Reparos (CRUD) | 4 | KI-071 |
| Relatórios de técnicos e custos operacionais (JSON e PDF) | 4 | KI-071 |
| Custos operacionais (`GET`, `DELETE`) | 2 | KI-071 |
| Backup (`listar`, `download`) | 2 | KI-071 |
| Alertas, exportação de logs da lista de compras | 2 | KI-071 |
| Views legadas (redirecionamento para o SPA e PDF/backup legados) | 11 | KI-070 (as 4 de admin) |
| `GET /app/assets/<path>` (estático) | 1 | — |

---

## 3. Achados

| KI | Achado | Natureza |
|---|---|---|
| KI-069 | Financeiro (caixa e contas) sem nenhum teste HTTP nem de autorização | Lacuna de teste |
| KI-070 | 401 e 403 sem teste em rotas autenticadas e administrativas | Lacuna de teste (sem falha de autorização afirmada) |
| KI-071 | Reparos, custos, relatórios, backup e alertas sem teste HTTP | Lacuna de teste |
| KI-072 | E2E percorre cerca de 6 das 28 telas | Lacuna de teste |
| KI-073 | `GET /api/constantes` responde sem login | **A investigar** (precisa de decisão do PO) |
| KI-074 | Perfil `comprador` fora de `PERFIS_OPCOES`; perfil `estoque` fora da lista de compras | **A investigar** |
| KI-075 | Rota `/compras` declarada duas vezes; `fetch('/api/...')` sem `BASE` | **A investigar** (não confirmado em execução) |
| KI-076 | Achados menores: função de frontend para rota inexistente, fallback `onrender.com`, `ARCHITECTURE.md` desatualizado, rotas sem consumidor no frontend | Dívida (documentação e código morto) |

Detalhes, impacto e status de cada um estão no `KNOWN_ISSUES.md`.

### Cobertura do E2E por tela (`App.jsx` × `app.spec.js`)

Percorridas pelos 4 cenários: `/login`, `/` (dashboard), `/estoque`, `/ordens` (`/nova`, `/editar/:id`),
`/backup`, `/usuarios`. Sem E2E: `/vendas`, `/vendas/:id`, `/lembretes`, `/clientes`, `/produtos`,
`/unidades-serializadas`, `/financeiro`, `/compras`, `/compras-aparelhos`, `/garantias`, `/tipos-garantia`,
`/kanban`, `/reparos`, `/precos`, `/custos`, `/relatorios`, `/dados-loja`, `/auditoria`, `/checklist/:token`.
Em `1e9c265` a infraestrutura do E2E ainda é a anterior ao KI-068 (corrigida no PR #106, não integrado).

### Frontend × backend

- Chamada sem rota correspondente: `estoque.get(id)` → `GET /api/estoque/<id>` (`client.js:266`); nenhum
  lugar chama a função (KI-076).
- Rotas sem consumidor no frontend (excluída a integração MercadoPhone, desligada pela ADR-014):
  `GET /api/shopping-list/grouped`, `GET /api/shopping-list/<id>/logs`, `GET /api/shopping-list/logs/export`,
  `POST /api/usuarios/<id>/reset-token`, `POST /api/password-reset/<token>`, `GET /api/caixa/relatorio`
  (KI-076). Não significa código morto: podem ser usadas por fora do SPA. Nada deve ser removido sem
  confirmação.

---

## 4. Matriz completa

Legenda: **Testes HTTP** = arquivos que chamam a rota com esse método · **?** = path achado, método não
identificado · **—** = nenhum teste HTTP identificado · **401/403** = nº de funções de teste que citam a rota e
o código · ✔ = autorização conferida manualmente.

| Método | Rota | Autorização | Testes HTTP | 401 | 403 | Origem |
|---|---|---|---|---|---|---|
| GET | `/` | ROUTE_PERMISSIONS: logado | ? test_backup_restore.py,test_sentry_init.py | 0 | 0 | `fluxoly_blueprints_main.py:19` |
| GET | `/api/alertas` | logado | — | 0 | 0 | `api_system.py:97` |
| GET | `/api/auditoria` | perfis: admin,financeiro ✔ | test_auditoria.py | 1 | 2 | `fluxoly_auditoria_controller.py:27` |
| POST | `/api/auth/login` | público ✔ | test_auth.py, test_inc001_login_connection_leak.py, test_rate_limit_login.py, test_security.py | 9 | 0 | `api_auth.py:24` |
| POST | `/api/auth/logout` | público (limpa a sessão) ✔ | test_auditoria.py, test_auth.py, test_session.py | 3 | 1 | `api_auth.py:73` |
| GET | `/api/auth/me` | logado | test_auth.py, test_session.py, test_session_inactivity.py | 9 | 0 | `api_auth.py:78` |
| POST | `/api/backup/criar` | logado | test_backup_somente_local.py | 0 | 0 | `api_backup.py:27` |
| GET | `/api/backup/download/<path:filename>` | logado | — | 0 | 0 | `api_backup.py:72` |
| GET | `/api/backup/listar` | logado | — | 0 | 0 | `api_backup.py:47` |
| POST | `/api/backup/restaurar` | logado | ? test_backup_restore.py | 0 | 2 | `api_backup.py:78` |
| GET | `/api/caixa` | perfis: admin,financeiro | — | 0 | 0 | `fluxoly_caixa_controller.py:41` |
| POST | `/api/caixa` | perfis: admin,financeiro | — | 0 | 0 | `fluxoly_caixa_controller.py:80` |
| POST | `/api/caixa/<int:movimentacao_id>/estornar` | perfis: admin,financeiro | — | 0 | 0 | `fluxoly_caixa_controller.py:96` |
| GET | `/api/caixa/relatorio` | perfis: admin,financeiro | — | 0 | 0 | `fluxoly_caixa_controller.py:69` |
| GET | `/api/caixa/saldo` | perfis: admin,financeiro | — | 0 | 0 | `fluxoly_caixa_controller.py:60` |
| GET | `/api/checklist/<token>` | token/próprio | test_inc001_checklist_connection_leak.py | 0 | 0 | `api_os.py:557` |
| POST | `/api/checklist/<token>` | token/próprio | test_inc001_checklist_connection_leak.py | 0 | 0 | `api_os.py:604` |
| GET | `/api/clientes` | logado; CPF/CNPJ só admin,financeiro (máscara) ✔ | test_clientes.py, test_clientes_pii_acesso.py | 2 | 0 | `fluxoly_clientes_controller.py:57` |
| POST | `/api/clientes` | logado; CPF/CNPJ só admin,financeiro (máscara) ✔ | test_clientes.py, test_clientes_anonimizacao.py, test_clientes_pii_acesso.py | 2 | 0 | `fluxoly_clientes_controller.py:85` |
| DELETE | `/api/clientes/<int:cliente_id>` | perfis: admin | test_clientes.py | 2 | 2 | `fluxoly_clientes_controller.py:129` |
| GET | `/api/clientes/<int:cliente_id>` | perfis: admin,financeiro | test_clientes.py, test_clientes_pii_acesso.py, test_vendas.py | 2 | 2 | `fluxoly_clientes_controller.py:73` |
| PUT | `/api/clientes/<int:cliente_id>` | logado | test_clientes.py | 2 | 2 | `fluxoly_clientes_controller.py:104` |
| POST | `/api/clientes/<int:cliente_id>/anonimizar` | perfis: admin | test_clientes_anonimizacao.py | 0 | 2 | `fluxoly_clientes_controller.py:140` |
| GET | `/api/compras-aparelhos` | perfis: admin,financeiro,vendedor ✔ | test_compras_aparelhos.py | 1 | 1 | `fluxoly_compras_aparelhos_controller.py:45` |
| POST | `/api/compras-aparelhos` | perfis: admin,financeiro,vendedor ✔ | test_compras_aparelhos.py | 1 | 1 | `fluxoly_compras_aparelhos_controller.py:72` |
| GET | `/api/compras-aparelhos/<int:compra_id>` | perfis: admin,financeiro,vendedor ✔ | test_compras_aparelhos.py, test_compras_custo_lucro.py, test_os_interna.py | 0 | 1 | `fluxoly_compras_aparelhos_controller.py:119` |
| POST | `/api/compras-aparelhos/<int:compra_id>/cancelar` | perfis: admin,financeiro,vendedor ✔ | test_compras_aparelhos.py | 0 | 0 | `fluxoly_compras_aparelhos_controller.py:130` |
| GET | `/api/compras-aparelhos/relatorio` | perfis: admin,financeiro | test_compras_custo_lucro.py | 0 | 1 | `fluxoly_compras_aparelhos_controller.py:106` |
| GET | `/api/constantes` | **público (sem login)** ✔ | test_constantes_os.py, test_metrics.py, test_produtos.py, test_request_id.py, test_security_headers.py | 0 | 0 | `api_system.py:76` |
| GET | `/api/contas-pagar` | perfis: admin,financeiro | — | 0 | 0 | `fluxoly_contas_pagar_controller.py:41` |
| POST | `/api/contas-pagar` | perfis: admin,financeiro | — | 0 | 0 | `fluxoly_contas_pagar_controller.py:69` |
| DELETE | `/api/contas-pagar/<int:conta_id>` | perfis: admin,financeiro | — | 0 | 0 | `fluxoly_contas_pagar_controller.py:113` |
| GET | `/api/contas-pagar/<int:conta_id>` | perfis: admin,financeiro | — | 0 | 0 | `fluxoly_contas_pagar_controller.py:57` |
| PUT | `/api/contas-pagar/<int:conta_id>` | perfis: admin,financeiro | — | 0 | 0 | `fluxoly_contas_pagar_controller.py:90` |
| POST | `/api/contas-pagar/<int:conta_id>/cancelar` | perfis: admin,financeiro | — | 0 | 0 | `fluxoly_contas_pagar_controller.py:139` |
| POST | `/api/contas-pagar/<int:conta_id>/pagar` | perfis: admin,financeiro | — | 0 | 0 | `fluxoly_contas_pagar_controller.py:126` |
| GET | `/api/contas-receber` | perfis: admin,financeiro | — | 0 | 0 | `fluxoly_contas_receber_controller.py:42` |
| POST | `/api/contas-receber` | perfis: admin,financeiro | — | 0 | 0 | `fluxoly_contas_receber_controller.py:70` |
| DELETE | `/api/contas-receber/<int:conta_id>` | perfis: admin,financeiro | — | 0 | 0 | `fluxoly_contas_receber_controller.py:114` |
| GET | `/api/contas-receber/<int:conta_id>` | perfis: admin,financeiro | — | 0 | 0 | `fluxoly_contas_receber_controller.py:58` |
| PUT | `/api/contas-receber/<int:conta_id>` | perfis: admin,financeiro | — | 0 | 0 | `fluxoly_contas_receber_controller.py:91` |
| POST | `/api/contas-receber/<int:conta_id>/cancelar` | perfis: admin,financeiro | — | 0 | 0 | `fluxoly_contas_receber_controller.py:140` |
| POST | `/api/contas-receber/<int:conta_id>/receber` | perfis: admin,financeiro | — | 0 | 0 | `fluxoly_contas_receber_controller.py:127` |
| GET | `/api/custos` | logado | — | 0 | 0 | `api_costs.py:21` |
| POST | `/api/custos` | logado | test_api_parsing.py | 0 | 0 | `api_costs.py:31` |
| DELETE | `/api/custos/<int:custo_id>` | logado | — | 0 | 0 | `api_costs.py:102` |
| PUT | `/api/custos/<int:custo_id>` | logado | test_api_parsing.py | 0 | 0 | `api_costs.py:63` |
| GET | `/api/dados-loja` | logado | test_dados_loja.py | 2 | 1 | `fluxoly_dados_loja_controller.py:25` |
| PUT | `/api/dados-loja` | perfis: admin | test_dados_loja.py | 2 | 1 | `fluxoly_dados_loja_controller.py:31` |
| GET | `/api/dashboard` | logado; oculta campos por perfil ✔ | test_os_data_previsao.py, test_os_interna.py, test_vendas.py | 0 | 0 | `api_system.py:127` |
| GET | `/api/estoque` | logado | test_stock_creation_query.py, test_stock_security.py | 2 | 1 | `api_stock.py:69` |
| POST | `/api/estoque` | perfis: admin | test_stock_creation_query.py, test_stock_security.py | 2 | 1 | `api_stock.py:277` |
| DELETE | `/api/estoque/<int:item_id>` | perfis: admin | test_stock_security.py | 3 | 2 | `api_stock.py:466` |
| PUT | `/api/estoque/<int:item_id>` | perfis: admin | test_stock_movement.py, test_stock_security.py | 3 | 2 | `api_stock.py:353` |
| GET | `/api/estoque/movimentacoes` | logado | test_stock_movement.py | 1 | 0 | `api_stock.py:494` |
| GET | `/api/estoque/reposicao-sugerida` | logado | test_api_parsing.py | 0 | 0 | `api_stock.py:196` |
| GET | `/api/garantias` | logado ✔ | test_constantes_os.py, test_listar_garantias.py, test_os_interna.py | 0 | 0 | `api_garantias.py:30` |
| POST | `/api/integracoes/mercadophone/config` | logado | test_api_parsing_refactor.py, test_mercadophone_integracao_desligada.py | 0 | 0 | `api_mercadophone.py:245` |
| POST | `/api/integracoes/mercadophone/os` | token/próprio | test_mercadophone_integracao_desligada.py, test_mercadophone_webhook_auth.py | 2 | 0 | `api_mercadophone.py:353` |
| POST | `/api/integracoes/mercadophone/reimportar` | perfis: admin,tecnico | ? test_ki037_guard_integracoes.py,test_mercadophone_integracao_desligada.py,test_mercadophone_permissions.py | 0 | 0 | `api_mercadophone.py:189` |
| GET | `/api/integracoes/mercadophone/reimportar/status` | logado | ? test_mercadophone_integracao_desligada.py | 0 | 0 | `api_mercadophone.py:224` |
| POST | `/api/integracoes/mercadophone/reprocessar` | perfis: admin,tecnico | ? test_ki037_guard_integracoes.py,test_mercadophone_integracao_desligada.py,test_mercadophone_permissions.py | 0 | 0 | `api_mercadophone.py:148` |
| GET | `/api/integracoes/mercadophone/reprocessar/status` | logado | ? test_mercadophone_integracao_desligada.py | 0 | 0 | `api_mercadophone.py:183` |
| POST | `/api/integracoes/mercadophone/sincronizar` | perfis: admin,tecnico | ? test_ki037_guard_integracoes.py,test_mercadophone_integracao_desligada.py,test_mercadophone_permissions.py | 0 | 0 | `api_mercadophone.py:129` |
| GET | `/api/integracoes/mercadophone/status` | logado | test_mercadophone_integracao_desligada.py | 0 | 0 | `api_mercadophone.py:230` |
| GET | `/api/ordens` | logado | test_os_creation_query.py, test_os_data_previsao.py, test_os_deletion_security.py | 2 | 1 | `api_os.py:264` |
| POST | `/api/ordens` | perfis: admin,tecnico,vendedor | test_os_creation_query.py, test_os_data_previsao.py, test_os_deletion_security.py, test_os_interna.py, test_os_relato_laudo.py, test_stock_os_integration.py, test_stock_security.py | 2 | 1 | `api_os.py:667` |
| DELETE | `/api/ordens/<int:os_id>` | perfis: admin,tecnico | test_os_deletion_security.py, test_stock_os_integration.py | 5 | 1 | `api_os.py:1006` |
| GET | `/api/ordens/<int:os_id>` | logado | test_clientes.py, test_os_creation_query.py, test_os_data_previsao.py, test_os_deletion_security.py, test_os_interna.py, test_os_relato_laudo.py, test_permissions.py, test_security_headers.py | 5 | 1 | `api_os.py:338` |
| PUT | `/api/ordens/<int:os_id>` | perfis: admin,tecnico,vendedor | test_garantia_reparo.py, test_os_data_previsao.py, test_os_deletion_security.py, test_os_interna.py, test_os_relato_laudo.py, test_os_update_status.py | 5 | 1 | `api_os.py:790` |
| GET | `/api/ordens/<int:os_id>/checklist` | logado | test_inc001_checklist_connection_leak.py | 0 | 0 | `api_os.py:470` |
| POST | `/api/ordens/<int:os_id>/checklist/token` | logado | test_inc001_checklist_connection_leak.py | 0 | 0 | `api_os.py:509` |
| GET | `/api/ordens/<int:os_id>/documento` | logado; dados do cliente por perfil (máscara) ✔ | test_faturamento_os.py, test_os_documento.py, test_os_relato_laudo.py | 0 | 0 | `api_os.py:429` |
| PATCH | `/api/ordens/<int:os_id>/reparos/<int:reparo_id>/garantia` | perfis: admin | test_garantia_reparo.py | 0 | 2 | `api_os.py:1176` |
| GET | `/api/ordens/<int:os_id>/reparos/<int:reparo_id>/historico-garantia` | logado | test_garantia_reparo.py | 0 | 0 | `api_os.py:1248` |
| PATCH | `/api/ordens/<int:os_id>/status` | perfis: admin,tecnico | test_compras_custo_lucro.py, test_garantia_reparo.py, test_os_deletion_security.py, test_os_interna.py, test_os_update_status.py, test_stock_os_integration.py | 1 | 0 | `api_os.py:1057` |
| GET | `/api/ordens/historico-cliente` | logado | test_os_creation_query.py | 1 | 0 | `api_os.py:1276` |
| POST | `/api/password-reset/<token>` | token de reset | test_password_reset.py | 0 | 0 | `api_users.py:178` |
| GET | `/api/pendencias` | perfis: admin,financeiro | test_pendencias.py | 1 | 1 | `api_system.py:109` |
| GET | `/api/precos` | logado | test_pricing.py | 1 | 3 | `api_prices.py:21` |
| POST | `/api/precos` | logado | ? test_api_parsing.py,test_pricing.py | 1 | 3 | `api_prices.py:27` |
| POST | `/api/precos/excluir` | logado | test_pricing.py | 0 | 0 | `api_prices.py:48` |
| GET | `/api/precos/sugerir` | logado | test_pricing.py | 1 | 0 | `api_prices.py:71` |
| GET | `/api/produtos` | logado | test_produtos.py | 1 | 1 | `fluxoly_produtos_controller.py:52` |
| POST | `/api/produtos` | perfis: admin | test_produtos.py | 1 | 1 | `fluxoly_produtos_controller.py:80` |
| DELETE | `/api/produtos/<int:produto_id>` | perfis: admin | test_produtos.py | 0 | 3 | `fluxoly_produtos_controller.py:157` |
| GET | `/api/produtos/<int:produto_id>` | logado | test_produtos.py | 0 | 3 | `fluxoly_produtos_controller.py:70` |
| PUT | `/api/produtos/<int:produto_id>` | perfis: admin | test_produtos.py | 0 | 3 | `fluxoly_produtos_controller.py:117` |
| GET | `/api/relatorios/custos-operacionais` | logado | — | 0 | 0 | `api_reports.py:33` |
| GET | `/api/relatorios/pdf/custos-operacionais` | logado | — | 0 | 0 | `api_reports.py:72` |
| GET | `/api/relatorios/pdf/tecnicos` | logado | — | 0 | 0 | `api_reports.py:57` |
| GET | `/api/relatorios/tecnicos` | logado | — | 0 | 0 | `api_reports.py:23` |
| GET | `/api/reparos` | logado | — | 0 | 0 | `api_os.py:1318` |
| POST | `/api/reparos` | logado | — | 0 | 0 | `api_os.py:1330` |
| DELETE | `/api/reparos/<int:reparo_id>` | logado | — | 0 | 0 | `api_os.py:1383` |
| PUT | `/api/reparos/<int:reparo_id>` | logado | — | 0 | 0 | `api_os.py:1357` |
| GET | `/api/shopping-list` | logado | test_api_parsing.py, test_shopping.py | 2 | 0 | `api_shopping.py:46` |
| POST | `/api/shopping-list` | logado | test_api_parsing_refactor.py, test_shopping.py, test_shopping_hotfix_quantidade_zero.py | 2 | 0 | `api_shopping.py:161` |
| DELETE | `/api/shopping-list/<int:item_id>` | perfis: admin,tecnico,comprador ✔ | test_shopping.py | 3 | 0 | `api_shopping.py:389` |
| GET | `/api/shopping-list/<int:item_id>` | logado | test_shopping.py, test_shopping_hotfix_quantidade_zero.py | 3 | 0 | `api_shopping.py:120` |
| PUT | `/api/shopping-list/<int:item_id>` | logado | test_api_parsing_refactor.py, test_shopping.py | 3 | 0 | `api_shopping.py:227` |
| GET | `/api/shopping-list/<int:item_id>/logs` | logado | test_shopping.py | 1 | 0 | `api_shopping.py:448` |
| PATCH | `/api/shopping-list/<int:item_id>/status` | perfis: admin,tecnico,comprador ✔ | test_shopping.py | 1 | 1 | `api_shopping.py:279` |
| GET | `/api/shopping-list/grouped` | logado | test_shopping.py | 1 | 0 | `api_shopping.py:420` |
| GET | `/api/shopping-list/logs/export` | logado | — | 0 | 0 | `api_shopping.py:491` |
| GET | `/api/tipos-garantia` | logado; inativos só para admin ✔ | test_tipos_garantia.py | 2 | 0 | `fluxoly_tipos_garantia_controller.py:43` |
| POST | `/api/tipos-garantia` | perfis: admin | test_tipos_garantia.py | 2 | 0 | `fluxoly_tipos_garantia_controller.py:57` |
| PUT | `/api/tipos-garantia/<int:tipo_garantia_id>` | perfis: admin | test_tipos_garantia.py | 0 | 1 | `fluxoly_tipos_garantia_controller.py:71` |
| GET | `/api/unidades-serializadas` | logado | test_compras_custo_lucro.py, test_unidades_serializadas.py | 1 | 2 | `fluxoly_unidades_serializadas_controller.py:45` |
| POST | `/api/unidades-serializadas` | perfis: admin,tecnico | test_unidades_serializadas.py | 1 | 2 | `fluxoly_unidades_serializadas_controller.py:84` |
| GET | `/api/unidades-serializadas/<int:unidade_id>` | perfis: admin,financeiro | test_compras_custo_lucro.py, test_unidades_serializadas.py | 0 | 1 | `fluxoly_unidades_serializadas_controller.py:71` |
| PATCH | `/api/unidades-serializadas/<int:unidade_id>` | perfis: admin,tecnico | test_unidades_serializadas.py | 0 | 1 | `fluxoly_unidades_serializadas_controller.py:128` |
| GET | `/api/unidades-serializadas/<int:unidade_id>/historico` | logado | test_unidades_serializadas.py | 1 | 0 | `fluxoly_unidades_serializadas_controller.py:105` |
| PATCH | `/api/unidades-serializadas/<int:unidade_id>/status` | perfis: admin,tecnico | test_unidades_serializadas.py | 0 | 1 | `fluxoly_unidades_serializadas_controller.py:115` |
| GET | `/api/usuarios` | logado | test_permissions.py, test_session.py, test_users.py | 0 | 5 | `api_users.py:32` |
| POST | `/api/usuarios` | logado | test_users.py | 0 | 5 | `api_users.py:46` |
| DELETE | `/api/usuarios/<int:uid>` | logado | test_users.py | 0 | 2 | `api_users.py:120` |
| PUT | `/api/usuarios/<int:uid>` | logado | ? test_users.py | 0 | 2 | `api_users.py:82` |
| POST | `/api/usuarios/<int:uid>/reset-token` | logado | test_password_reset.py | 0 | 2 | `api_users.py:140` |
| GET | `/api/vendas` | logado | test_vendas.py | 2 | 3 | `fluxoly_vendas_controller.py:72` |
| POST | `/api/vendas` | perfis: admin,vendedor | test_vendas.py | 2 | 3 | `fluxoly_vendas_controller.py:138` |
| GET | `/api/vendas/<int:venda_id>` | perfis: admin,financeiro | test_compras_custo_lucro.py, test_vendas.py | 3 | 1 | `fluxoly_vendas_controller.py:172` |
| POST | `/api/vendas/<int:venda_id>/cancelar` | perfis: admin,vendedor | test_vendas.py | 1 | 2 | `fluxoly_vendas_controller.py:213` |
| PATCH | `/api/vendas/<int:venda_id>/itens/<int:item_id>/ajuste-desconto` | perfis: admin | ? test_vendas.py | 0 | 1 | `fluxoly_vendas_controller.py:242` |
| PATCH | `/api/vendas/<int:venda_id>/itens/<int:item_id>/comissao` | perfis: admin,financeiro | test_vendas.py | 0 | 3 | `fluxoly_vendas_controller.py:277` |
| PATCH | `/api/vendas/<int:venda_id>/itens/<int:item_id>/garantia` | perfis: admin | test_vendas.py | 0 | 2 | `fluxoly_vendas_controller.py:315` |
| GET | `/api/vendas/<int:venda_id>/itens/<int:item_id>/historico-comissao` | perfis: admin,financeiro | test_vendas.py | 0 | 1 | `fluxoly_vendas_controller.py:302` |
| GET | `/api/vendas/<int:venda_id>/itens/<int:item_id>/historico-desconto` | logado | test_vendas.py | 0 | 0 | `fluxoly_vendas_controller.py:267` |
| GET | `/api/vendas/<int:venda_id>/itens/<int:item_id>/historico-garantia` | logado | test_vendas.py | 0 | 0 | `fluxoly_vendas_controller.py:342` |
| GET | `/api/vendas/<int:venda_id>/recibo` | logado; dados do cliente por perfil (máscara) ✔ | test_vendas.py | 1 | 0 | `fluxoly_vendas_controller.py:191` |
| GET | `/api/vendas/garantias` | logado | test_vendas.py | 1 | 0 | `fluxoly_vendas_controller.py:110` |
| GET | `/api/vendas/lembretes` | perfis: admin,vendedor | test_vendas.py | 1 | 1 | `fluxoly_vendas_controller.py:121` |
| GET | `/app/<path:path>` | público (infra/estático) | ? test_auth.py,test_permissions.py,test_route_permissions_fail_secure.py | 0 | 0 | `app.py:1041` |
| GET | `/app/assets/<path:filename>` | público (infra/estático) | — | 0 | 0 | `app.py:1053` |
| GET | `/backup` | ROUTE_PERMISSIONS: admin | — | 0 | 0 | `fluxoly_blueprints_main.py:48` |
| GET | `/backup/download/<path:nome>` | ROUTE_PERMISSIONS: admin | — | 0 | 0 | `fluxoly_blueprints_main.py:52` |
| GET | `/dashboard` | ROUTE_PERMISSIONS: logado | — | 0 | 0 | `fluxoly_blueprints_main.py:19` |
| GET | `/dashboard.html` | ROUTE_PERMISSIONS: logado | — | 0 | 0 | `fluxoly_blueprints_main.py:19` |
| GET | `/dashboard/` | ROUTE_PERMISSIONS: logado | — | 0 | 0 | `fluxoly_blueprints_main.py:19` |
| GET | `/garantias` | ROUTE_PERMISSIONS: logado | — | 0 | 0 | `fluxoly_blueprints_main.py:44` |
| GET | `/health` | público (infra/estático) | test_health_ready.py | 0 | 0 | `app.py:980` |
| GET | `/index` | ROUTE_PERMISSIONS: logado | — | 0 | 0 | `fluxoly_blueprints_main.py:19` |
| GET | `/index.html` | ROUTE_PERMISSIONS: logado | — | 0 | 0 | `fluxoly_blueprints_main.py:19` |
| GET | `/kanban` | ROUTE_PERMISSIONS: logado | — | 0 | 0 | `fluxoly_blueprints_main.py:40` |
| GET | `/login` | ROUTE_PERMISSIONS: público | test_auth.py | 0 | 0 | `fluxoly_blueprints_auth.py:33` |
| POST | `/login` | ROUTE_PERMISSIONS: público | conftest.py, test_ki037_guard_integracoes.py, test_mercadophone_integracao_desligada.py, test_mercadophone_permissions.py, test_permissions.py, test_rate_limit_login.py, test_route_permissions_fail_secure.py | 0 | 0 | `fluxoly_blueprints_auth.py:33` |
| GET | `/logout` | ROUTE_PERMISSIONS: público | test_auth.py, test_password_reset.py | 0 | 0 | `fluxoly_blueprints_auth.py:74` |
| GET | `/metrics` | token (METRICS_TOKEN em prod) | test_metrics.py | 3 | 0 | `app.py:1014` |
| GET | `/ready` | público (infra/estático) | test_health_ready.py | 0 | 0 | `app.py:986` |
| GET | `/relatorios` | ROUTE_PERMISSIONS: admin | — | 0 | 0 | `fluxoly_blueprints_main.py:23` |
| GET | `/relatorios/pdf/tecnicos` | ROUTE_PERMISSIONS: admin | — | 0 | 0 | `fluxoly_blueprints_main.py:27` |
