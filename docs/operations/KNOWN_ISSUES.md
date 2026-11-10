# Known Issues

## ~~KI-001~~ — RESOLVIDO

Descrição:
Ausência de rate limiting na rota `POST /api/auth/login`. Qualquer agente podia realizar tentativas de
login ilimitadas sem bloqueio por IP ou por usuário.

Impacto:
Alto. O endpoint estava vulnerável a ataques de força bruta contra credenciais de usuários do sistema.

Status:
Resolvido em 2026-07-11 (Sprint 3, Unidade 1). Contador de tentativas em SQLite (tabela
`login_attempts`, `irflow_rate_limit.py`) — 5 tentativas/minuto por identificador, aplicado em
`POST /api/auth/login` (rota real usada pelo frontend) e `POST /login` (rota legada). Contador em SQLite
em vez de memória do processo porque o Gunicorn de produção roda com `--workers 2`
(`Dockerfile`) — memória de processo daria um limite efetivo mais fraco e contornável entre workers;
SQLite já é compartilhado entre eles via WAL. Identificador resolvido via `Fly-Client-IP` (header do
proxy da Fly.io) com fallback para `X-Forwarded-For`/`remote_addr` — nenhum desses headers era lido
antes. Coberto por `tests/test_rate_limit_login.py` (7 casos). Isolamento de teste garantido por fixture
autouse em `tests/conftest.py` (`_limpar_login_attempts`), já que o cliente de teste do Flask sempre usa
o mesmo IP.

Sprint prevista:
Sprint 3 — Segurança e Observabilidade. Resolvido em 2026-07-11.

Responsável:
—

---

## KI-002

Descrição:
Tokens de checklist público (`GET /api/checklist/<token>`) não possuem data de expiração. Uma vez gerado, o link permanece válido indefinidamente.

Impacto:
Médio. Links compartilhados com clientes para revisão do dispositivo continuam acessíveis após o encerramento da OS, expondo informações da ordem sem controle de tempo.

Status:
Aberto.

Sprint prevista:
Sprint 3 — Segurança e Observabilidade.

Responsável:
—

---

## ~~KI-003~~ — RESOLVIDO

Descrição:
O módulo `fluxoly_blueprints_api.py` (renomeado de `irflow_blueprints_api.py` na Sprint Housekeeping,
2026-08-03) possui ~130KB e concentra 70 rotas em 13 domínios de negócio sem separação — contagem exata
e mapeamento de acoplamento (78 dependências injetadas via `create_api_blueprint(deps)`) levantados em
`ADR-011`.

Impacto:
Alto. Dificulta manutenção, aumenta risco de regressão em qualquer alteração e torna o onboarding de novos colaboradores mais lento.

Status:
Resolvido em 2026-08-07 (TD-01 Phase 2, Extração Incremental, encerrada formalmente por decisão do
usuário — CTO). 12/12 domínios extraídos para blueprints próprios (`api_shopping.py`,
`api_garantias.py`, `api_costs.py`, `api_prices.py`, `api_users.py`, `api_auth.py`, `api_backup.py`,
`api_reports.py`, `api_mercadophone.py`, `api_system.py`, `api_stock.py`, `api_os.py`).
`fluxoly_blueprints_api.py` reduzido de ~130KB/3.368 linhas/70 rotas para 911 bytes/34 linhas/0 rotas —
só resta código morto sem consumidor (`_slug_estoque`/`_gerar_sku_estoque`, ver KI-032). Architecture
Checkpoint Final em `docs/operations/SPRINTS/SPRINT_TD01_MODULARIZACAO_API.md`. Remoção do arquivo e do
registro `create_api_blueprint({})` em `app.py` registrada como TD-18 (Phase 3 — Cleanup),
deliberadamente fora do escopo desta sprint.

Sprint prevista:
TD-01 — concluída (Phase 2) em 2026-08-07.

Responsável:
—

---

## ~~KI-004~~ — RESOLVIDO

Descrição:
O sistema de migrations do banco de dados utiliza `ALTER TABLE` com blocos `try/except` ad-hoc em `app.py`. Não há versionamento formal do schema.

Impacto:
Alto. Impossível determinar o estado exato do schema em diferentes ambientes (dev, prod) sem inspecionar o banco diretamente. Risco de divergência silenciosa.

Status:
Resolvido em 2026-08-08 (TD-03, 2/2 fatias). `app.py::criar_tabelas()` (695 linhas ad-hoc) substituída por
`migrations/` — registry Python de migrations com tabela de controle `schema_migrations`. Fatia 1
(`migrations/registry.py`/`runner.py`/`versions/m0001_baseline.py`, aditiva, `app.py` intocado) validada
contra um backup real de produção antes da Fatia 2 — schema/contagens de linhas idênticos entre o
mecanismo antigo e o novo, idempotência confirmada. Fatia 2 removeu `criar_tabelas()`/`SCHEMA_READY`/
`SCHEMA_LOCK` de `app.py`; `conectar()` virou conexão pura, schema garantido só pelo bootstrap
(`run_migrations()`). Ver `docs/operations/SPRINTS/SPRINT_TD03_MIGRATIONS_FORMAIS.md`.

Sprint prevista:
Sprint 4 — Decomposição do Módulo API e Migrations Formais (planejamento original, nunca executado).
Resolvido via TD-03 em 2026-08-08.

Responsável:
—

---

## KI-005

Descrição:
A listagem de Ordens de Serviço (`GET /api/ordens`) não possui paginação. Retorna todos os registros em uma única resposta.

Impacto:
Médio. Com volume crescente de OS, a rota degradará em performance e o frontend consumirá memória excessiva ao renderizar listas muito grandes.

Status:
Aberto — aguardando Sprint 5.

Sprint prevista:
Sprint 5 — Paginação, Performance e Refatoração Frontend.

Responsável:
—

---

## KI-006

Descrição:
Falhas no envio de backup por e-mail não geram alertas visíveis para o operador. O sistema registra o erro internamente, mas nenhuma notificação chega ao usuário da interface.

Impacto:
Baixo. O operador pode ficar sem backup por dias sem perceber, aumentando o risco de perda de dados em caso de falha de disco.

Status:
Aberto — parcialmente endereçado. Sprint Observabilidade (2026-07-25) migrou os `print()` da thread de
backup (`irflow_storage.py`) para `logger.warning`/`logger.error` estruturado, e a integração Sentry
(gated por `SENTRY_DSN`, ainda vazia — usuário não tem conta) captura automaticamente qualquer
`logger.error(..., exc_info=True)` quando ativada. Isso dá visibilidade ao operador técnico via Sentry
depois de configurada — mas continua sem nenhuma notificação visível na interface para o usuário da
loja, que é o gap original descrito acima. Não fechar este KI só por causa da mudança de logging.

**Atualização (2026-11-06):** o envio de backup por e-mail foi removido (KI-043). O gap continua valendo
para o backup diário local: se `executar_backup_diario_automatico` falhar, só há `logger.error` — nenhuma
notificação na interface. Mantido aberto com esse escopo.

Sprint prevista:
Sprint 3 — Segurança e Observabilidade (concluída parcialmente nesse ponto por
`docs/operations/SPRINTS/SPRINT_OBSERVABILIDADE.md`, 2026-07-25).

Responsável:
—

---

## KI-007

Descrição:
Mensagens de commit sem padrão ("att", "S", "att 09/06 5"). O histórico git não comunica intenção ou escopo das mudanças.

Impacto:
Baixo. Rastreabilidade de bugs e análise de regressão ficam prejudicadas. Impossível usar `git bisect` ou `git log` para investigar quando um comportamento foi introduzido.

Status:
Aberto — mitigação via adoção de Conventional Commits a partir da Sprint 2.

Sprint prevista:
Sprint 2 — Pipeline de CI e Testes Backend.

Responsável:
—

---

## ~~KI-008~~ — RESOLVIDO

Descrição:
Auto-preenchimento de `valor_cobrado` ausente em NewOrder e EditOrder.

Impacto:
Crítico. Usuário precisava consultar a tabela de preços manualmente e preencher o campo a cada OS criada.

Status:
Resolvido na Sprint 1. Commit `fix: auto-preencher valor_cobrado pela tabela de preços`.

Sprint prevista:
Sprint 1 — concluída.

Responsável:
—

---

## ~~KI-009~~ — RESOLVIDO

Descrição:
URL do endpoint de PDF do relatório IR Phones estava incorreta (`/irphones` ao invés de `/ir-phones`).

Impacto:
Alto. Exportação de PDF do relatório IR Phones falhava com 404.

Status:
Resolvido na Sprint 1. Correção em `frontend/src/api/client.js`.

Sprint prevista:
Sprint 1 — concluída.

Responsável:
—

---

## ~~KI-010~~ — RESOLVIDO

Descrição:
Rota de histórico de cliente apontava para endpoint inexistente no `client.js`.

Impacto:
Médio. Consulta de histórico do cliente na tela de OS retornava erro 404.

Status:
Resolvido na Sprint 1. Correção em `frontend/src/api/client.js`.

Sprint prevista:
Sprint 1 — concluída.

Responsável:
—

---

## ~~KI-011~~ — RESOLVIDO

Descrição:
Campo `cor` não era limpo ao trocar o modelo em `EditOrder.jsx`, podendo manter uma cor inválida para o novo modelo selecionado.

Impacto:
Médio. Dados inconsistentes entre modelo e cor em OS editadas.

Status:
Resolvido na Sprint 1. Correção em `frontend/src/pages/EditOrder.jsx`.

Sprint prevista:
Sprint 1 — concluída.

Responsável:
—

---

## ~~KI-012~~ — RESOLVIDO

Descrição:
`irflow_blueprints_api.py` continha duas funções `shopping_list()` (e as respectivas `shopping_create`,
`shopping_update`, `shopping_delete`) registradas na mesma rota `/shopping-list` — a versão atual
(tabela `shopping_list`, com paginação/prioridade/responsável) e um bloco legado de uma implementação
anterior baseada na tabela `compras`, aparentemente deixado para trás na `Merge branch
'feature/shopping-edit-os-pr'` (commit `7811846`). Como Flask não permite dois endpoints com o mesmo
nome de função no mesmo blueprint, `app.py` lançava `AssertionError` na inicialização — a aplicação
não conseguia nem ser importada.

Impacto:
Crítico. Bloqueava toda execução da aplicação e da suíte de testes (inclusive os testes de
autenticação da Sprint 2.2). Identificado ao tentar rodar `pytest` pela primeira vez nesta sprint.

Status:
Resolvido em 2026-07-07. Removido o bloco legado duplicado (baseado em `compras`) em
`irflow_blueprints_api.py`. Confirmado via `frontend/src/pages/ShoppingList.jsx` e
`frontend/src/api/client.js` que o frontend consome apenas a implementação baseada em `shopping_list`
(campo `items`, não `compras`) — nenhuma funcionalidade em uso foi removida.

Sprint prevista:
Identificado e corrigido fora de sprint — bloqueava a Sprint 2.2.

Responsável:
—

---

## ~~KI-013~~ — RESOLVIDO

Descrição:
Em `irflow_blueprints_api.py`, nove pontos de parsing de entrada (`int()`/`float()` sobre
`request.args`/corpo JSON) em `shopping_list`, `reposicao_sugerida_estoque`, `criar_ordem`,
`atualizar_ordem`, `criar_estoque`, `atualizar_estoque`, `criar_custo`, `atualizar_custo` e
`salvar_preco` não tinham tratamento de exceção — ocorriam antes de qualquer `try/except` da
rota. Um valor não numérico (ex.: `?page=abc`, `{"valor": "abc"}`) derrubava a rota com 500 não
tratado, fora do contrato JSON `{"ok": false, "erro": ...}` usado pelo resto da API.

Impacto:
Médio. Não expõe dados nem quebra integridade do banco, mas qualquer cliente (inclusive o
frontend, em caso de bug de digitação/formulário) que envie um valor não numérico nesses campos
recebe um erro de servidor genérico em vez de uma mensagem de validação utilizável.

Status:
Resolvido em 2026-07-07 (Sprint 2.6). Substituído por `parse_int`/`parse_float`
(`irflow_validation.py`), que retornam `None` para entrada presente porém inválida — o call site
rejeita explicitamente com `err(...)` e 400, em vez de mascarar como o valor default ou deixar a
exceção propagar. Coberto por `tests/test_api_parsing.py`.

Sprint prevista:
Identificado e corrigido na Sprint 2.6 — Padronização de Validação e Parsing.

Responsável:
—

---

## ~~KI-014~~ — RESOLVIDO

Descrição:
Em `irflow_blueprints_api.py`, existe uma definição de `def criar_estoque():` sem decorador
`@api.route` nas linhas 220-267 (função interna solta, incluindo uma linha órfã
`return bool(session.get("usuario_id"))` que pertence a `usuario_logado()`). Ela é
imediatamente sobrescrita pela definição real e roteada de `criar_estoque()` mais abaixo
(`@api.route("/estoque", methods=["POST"])`), tornando o primeiro bloco código morto — nunca é
chamado, `ruff check .` já acusa `F811 Redefinition of unused 'criar_estoque'`. Mesmo padrão de
origem do KI-012 (bloco deixado para trás em um merge), mas sem o efeito colateral de derrubar
`app.py` na inicialização, pois não há decorador duplicado.

Impacto:
Baixo. Sem efeito em runtime — apenas ruído de manutenção (48 linhas mortas, pode confundir
leitura futura do arquivo).

Status:
Resolvido em 2026-07-20, commit `c3294a3` (branch `chore/fix-ruff-lint-ki-017`). Bloco morto
removido por completo, incluindo a linha órfã. Achado no processo de corrigir KI-017 (o `F811`
era um dos 175 erros de `ruff check .`). Rota real de `criar_estoque()` e comportamento da API
não mudam — confirmado por `pytest tests/` (407 testes) sem regressão. Fecha também TD-11
(`docs/operations/PROJECT_STATUS.md`).

Sprint prevista:
Identificado durante a Sprint 2.6 (2026-07-07); resolvido em 2026-07-20 junto de KI-017.

Responsável:
—

---

## ~~KI-015~~ — RESOLVIDO

Descrição:
Em `irflow_blueprints_api.py`, `PATCH /api/ordens/<id>/status` e `PUT /api/ordens/<id>` chamavam
`normalizar_status_os(body.get("status") or "")` sem o parâmetro `status_padrao=""`. Como a função
tem `status_padrao=STATUS_EM_ANDAMENTO` por default, um `status` ausente ou inválido nunca retornava
vazio — a checagem `if not status: return err(...)` nunca disparava. Consequência em
`PATCH .../status`: um status desconhecido era silenciosamente normalizado para "Em andamento" em
vez de rejeitado com 400. Consequência mais grave em `PUT /api/ordens/<id>`: editar qualquer campo
de uma OS **Finalizada** sem reenviar `status` reabria a OS silenciosamente para "Em andamento" e
zerava `data_finalizado` — sem erro, sem aviso.

Impacto:
Crítico em `PUT /api/ordens/<id>` — perda silenciosa do dado de finalização de uma OS em rota
usada pelo frontend em produção (C-01 + C-04, `docs/engineering/ENGINEERING_GUIDE.md` §11). Médio em
`PATCH .../status` — grava estado incorreto sem erro, mesma rota real.

Status:
Resolvido em 2026-07-10 via `hotfix/status-os-padrao-vazio`. Ambos os call sites passam a usar
`normalizar_status_os(body.get("status") or "", status_padrao="")`. As correções já existiam prontas
(commits `c85a321`, `e755f25`, achados durante a Sprint 2.4 em 2026-07-07, com aprovação explícita do
usuário) mas nunca chegaram a `main` porque a branch `test/sprint-2-4-regras-negocio-os` que as
continha não havia sido mergeada — extraídas via `cherry-pick` para hotfix isolado ao retomar o
Sprint 2, conforme ADR-004. Suíte completa (180 testes) e `ruff check` confirmados sem regressão
antes do merge.

Sprint prevista:
Identificado durante a Sprint 2.4 (2026-07-07); hotfix efetivamente mergeado em 2026-07-10, ao
retomar o Sprint 2 após a frente de documentação de produto/marca.

Responsável:
—

---

## ~~KI-016~~ — RESOLVIDO

Descrição:
Em `irflow_blueprints_api.py`, `POST /api/shopping-list` calculava a quantidade solicitada com
`parse_int(body.get("quantidade_solicitada") or body.get("quantidade"), default=1)`. Como `0` é
falsy em Python, enviar `quantidade_solicitada: 0` fazia o `or` cair para
`body.get("quantidade")` (ausente), que por sua vez caía no `default=1` do `parse_int` — antes
mesmo de chegar na validação `if quantidade is None or quantidade <= 0: return err(...)`, que
nunca era alcançada com o valor real enviado pelo chamador.

Impacto:
Médio. `POST /api/shopping-list` (rota real usada por `Compras.jsx`) criava o item silenciosamente
com quantidade `1` em vez de rejeitar a entrada `0` — mutação silenciosa de dado persistido sem
erro (C-01 + C-04, `docs/engineering/ENGINEERING_GUIDE.md` §11).

Status:
Resolvido em 2026-07-11 via `hotfix/quantidade-zero-shopping-list`. Trocado o `or` por
`body.get("quantidade_solicitada", body.get("quantidade"))` — `dict.get` com fallback só usa o
segundo valor quando a chave está de fato ausente, preservando `0` explícito para a validação
existente rejeitar. Achado durante a escrita de `tests/test_shopping.py` (restante da Sprint 2).
Suíte completa (331 testes) confirmada sem regressão antes do merge.

Sprint prevista:
Identificado e corrigido fora de sprint — bloqueava o fechamento da Sprint 2 (política de
interrupção do `CLAUDE.md`).

Responsável:
—

---

## ~~KI-017~~ — RESOLVIDO

Descrição:
`ruff check .` falhava em `main` com 20 erros (`F841` variáveis não usadas em
`irflow_blueprints_api.py` linhas 28-70, `SIM105`/`SIM102` em vários pontos, `E401` imports
múltiplos em uma linha, e o `F811` já conhecido de KI-014). O job `Lint` do CI
(`.github/workflows/ci.yml`) marca o passo `ruff check .` como BLOQUEANTE, e os jobs `backend` e
`frontend` dependem de `Lint` via `needs: lint` — ou seja, nenhum desses jobs roda enquanto o lint
estiver vermelho.

Impacto:
Alto (operacional, não funcional). Nenhum dos 20 erros é bug de comportamento — não foram gerados
por nenhuma mudança desta sessão (confirmado: nenhum está nas linhas tocadas pelo hotfix
KI-016/`quantidade-zero-shopping-list`). O risco real é que o CI pode estar vermelho em `main` há
algum tempo sem que `PROJECT_STATUS.md` refletisse isso — merece verificação do histórico real de
execuções no GitHub Actions antes de assumir desde quando.

Status:
Aberto — identificado em 2026-07-11 ao rodar `ruff check .` localmente antes de mergear o hotfix
KI-016. Fora de escopo corrigir aqui (seria refatoração de ~20 pontos em vários arquivos, viola a
regra de mudança única do `CLAUDE.md`). Candidato a uma sprint de limpeza isolada (`chore:` ou
`refactor:`, nunca junto de uma feature/fix).

**Correção de escopo (2026-07-11, Sprint 3 Unidade 1):** a contagem de "20 erros" acima media só
`irflow_blueprints_api.py`. Rodando `ruff check app.py irflow_blueprints_api.py` juntos (os dois
arquivos críticos que a Sprint 3 está tocando) o total real é **60 erros** — `app.py` sozinho
contribui um bloco grande de `F401` (imports não usados) nunca contado antes. Confirmado via
`git stash` que os 60 já existiam em `main` antes de qualquer mudança desta sessão — nenhuma unidade
da Sprint 3/P0.1 piora esse número, cada uma é checada com `ruff check <arquivos tocados>` antes do
commit para garantir isso.

**Exceção documentada (2026-07-11, Sprint P0.1 Unidade 5):** o total subiu para **61** com a adição de
`os.cliente_id` — um novo bloco `try: ALTER TABLE ... / except sqlite3.OperationalError: pass`, que
segue exatamente o idioma já documentado em `DATABASE.md`/`ENGINEERING_GUIDE.md` para migração aditiva
de coluna (repetido ~15 vezes em `app.py`, cada instância já contava para os 60 originais via `SIM105`).
Escrever esse bloco de outra forma (`contextlib.suppress`, sugestão do `ruff`) deixaria essa única
instância inconsistente com todas as outras ao redor — optado por manter consistência com o padrão
estabelecido do arquivo em vez de silenciar o lint em um ponto isolado. Confirmado: subiu para **62**
na Unidade 6 (`estoque.requer_imei`), mesma justificativa.

**Correção de escopo definitiva (2026-07-11, Sprint 3 Unidade 8):** todas as contagens acima (20 → 60 →
61 → 62) mediam apenas `app.py` + `irflow_blueprints_api.py`. `.github/workflows/ci.yml` roda
`ruff check .` — **o repositório inteiro**, não só esses dois arquivos. Rodando o comando real do CI:
**175 erros**, incluindo módulos nunca antes contados (`irflow_blueprints_orders.py`,
`irflow_mercadophone.py`, `irflow_os.py`, `irflow_price_tables.py`, `irflow_reports.py`,
`irflow_storage.py`, `irflow_reference_data.py`, `irflow_blueprints_admin.py`) e, principalmente, uma
dezena de scripts soltos na raiz do repo (`diagnose_dashboard_filter.py`, `test_sync.py`,
`validate_changes.py`, `test_dashboard_filter.py`, `test_solution.py`, `test_update_os.py`,
`test_shopping_list.py`, `test_routes.py`, `debug_shopping.py`, `smoke_test_full.py`,
`check_old_orders.py`) — scripts de debug/smoke pré-pytest (`docs/operations/SPRINTS/SPRINT_02.md` os
cita como "7 scripts ad-hoc no banco real"), fora de `tests/` e por isso nunca rodados pelo pytest, mas
ainda escaneados pelo `ruff check .` do CI. Nenhum dos 9 arquivos novos desta sprint
(`irflow_rate_limit.py`, `irflow_audit.py`, `irflow_clientes_*.py`, `irflow_estoque_unidades_*.py`,
`irflow_vendas_service.py`) aparece nessa lista — confirmado zero regressão. **62 continua sendo o
número relevante para o que a Sprint 3/P0.1 tocou**, mas **175 é o número real que bloqueia o CI**.

**Resolvido em 2026-07-20 (branch `chore/fix-ruff-lint-ki-017`, 6 commits atômicos), decisão do
usuário (CTO) de destravar o CI antes de iniciar o Épico Vendas — todo PR futuro dependeria de um
pipeline que já nascia bloqueado.** Categorização dos 175 erros reais:

- **95 (54%)** viviam em 11 scripts de debug/smoke pré-pytest soltos na raiz do repo (já citados
  acima como causa do salto de 62→175) — nenhum coletado pelo pytest (`testpaths=["tests"]`),
  nenhum invocado pelo `ci.yml`. Movidos para `scripts/` (já excluído do ruff em `pyproject.toml`,
  mesmo lugar de `diagnose_mercadophone.py`/`import_legacy_db.py`) — zero mudança de conteúdo,
  commit `94cfdb2`.
- **24** resolvidos por `ruff check --fix` (imports não usados, espaço em branco, f-strings sem
  placeholder, etc.) nos módulos de produção — commit `2cd3822`.
- **28** (`SIM105`) convertidos para `contextlib.suppress` — 18 no idioma de `ALTER TABLE` de
  `app.py` (já documentado acima como intencional; convertidas todas juntas nesta mudança, o que
  preserva a consistência interna do arquivo em vez de quebrá-la) e 10 no idioma de limpeza
  best-effort de `irflow_blueprints_api.py` — commit `f00a993`.
- **1** (`F811`) era o bloco morto de `criar_estoque()` — resolvido junto de KI-014, commit
  `c3294a3`.
- **10** (`F841`) eram bindings `deps[...]` nunca referenciados — commit `ba0edd3`.
- **17** restantes (`B904`, `B007`, `E741`, `C414`, `SIM102/103/110/115/118`) corrigidos
  pontualmente, cada um reescrito 1:1 do mesmo comportamento — commit `605b5f5`. Uma exceção
  documentada: `SIM115` em `irflow_blueprints_api.py` (restauração de backup) foi suprimida com
  `# noqa` em vez de convertida para `with`, porque fechar o handle do `NamedTemporaryFile` antes
  do `os.unlink()` manual no `finally` falharia com `PermissionError` no Windows enquanto o
  arquivo ainda está em uso por `sqlite3.connect()`/`shutil.copy2()`.

`ruff check .` → 0 erros (era exatamente o comando que o job `Lint` do CI roda). 407 testes,
100% passando, cobertura 48% (gate ≥ 40%) — confirmado após cada um dos 6 commits, não só no
final. R-08 (`docs/operations/PROJECT_STATUS.md`) mitigado junto — `backend`/`frontend` voltam a
rodar via `needs: lint` para qualquer PR novo, inclusive os do Épico Vendas.

**Correção de registro (2026-07-21):** o commit local/branch existia desde 2026-07-20, mas o merge
efetivo em `origin/main` só aconteceu em 2026-07-21, junto do merge de `feat/produtos-catalogo`
(Sprint Comercial 1.1) — a branch de lint era pré-requisito dela e nunca havia sido mesclada em
`origin/main` isoladamente. Achado ao mesclar a Tela Produtos; `ruff check .` confirmado em 0 erros
no repositório inteiro após o merge, 434 testes (407 + 27 de `test_produtos.py`) passando.

Sprint prevista:
Não definida — recomendado priorizar antes da Sprint 3, já que um lint vermelho bloqueia todo o
resto do pipeline de CI para qualquer PR. Commit criado em 2026-07-20, mergeado em `origin/main`
em 2026-07-21.

Responsável:
—

---

## ~~KI-018~~ — RESOLVIDO

Descrição:
`IPHONE_MODELS`/`IPHONE_COLORS` (`irflow_reference_data.py`) — fonte única do catálogo de modelos
usado em `GET /api/constantes` e consumido por `NewOrder.jsx`/`EditOrder.jsx`/`Stock.jsx`/
`PriceTables.jsx` — parava em "iPhone 16e", sem os modelos da linha iPhone 17 (lançamento 2025:
iPhone 17, iPhone 17 Air, iPhone 17 Pro, iPhone 17 Pro Max).

Impacto:
Alto (operacional). Impedia abrir Ordem de Serviço para qualquer aparelho da linha iPhone 17 — o
modelo simplesmente não aparecia no dropdown de seleção, já que o backend não valida `modelo` contra
uma whitelist (a lista só alimenta as opções do frontend).

Status:
Resolvido em 2026-07-21 via `fix/catalogo-iphone-17` (Hotfix H-002), branch a partir de `main`.
Adicionados os 4 modelos a `IPHONE_MODELS`. Cores em `IPHONE_COLORS` usam uma lista genérica
(`Preto`/`Branco`/`Azul`/`Verde`/`Rosa`, mesmo padrão de outras gerações) em vez de nomes específicos
do catálogo oficial Apple — decisão deliberada do usuário (CTO) em revisão: sem necessidade comercial
ainda de precisão de cor por variante, o risco de publicar um nome de cor incorreto supera o
benefício; trocar pelos nomes oficiais quando/se houver essa demanda (ex.: Vendas/Produtos). Regex de
extração de modelo por descrição livre (`extrair_modelo_da_descricao_aparelho`) ajustado para
reconhecer o sufixo "air", nunca usado antes nesta lista — sem o ajuste, uma descrição como "iPhone
17 Air 256GB" seria extraída incorretamente como "iPhone 17", perdendo a distinção do modelo.
Comentário adicionado acima de `IPHONE_MODELS` documentando que é fonte única consumida por Nova
OS/Editar OS/Estoque/Tabela de Preços/`API /api/constantes`, para reduzir o risco de o catálogo ficar
desatualizado de novo sem que o próximo desenvolvedor perceba o alcance da lista. Nenhuma mudança de
schema/endpoint/regra de negócio. Confirmado que `IPHONE_MODELS`/`IPHONE_COLORS` é fonte única, sem
lista duplicada em nenhum outro módulo, antes de editar. Suíte completa (407 testes) sem regressão.
Validado manualmente: criação real de OS com modelo "iPhone 17 Pro Max" via API e via tela
`NewOrder.jsx` (servidor local, banco isolado).

Sprint prevista:
Fora de sprint — pedido direto do usuário (CTO), prioridade por bloqueio operacional imediato.

Responsável:
—

---

## KI-019

Descrição:
No modo "processo único" (Flask servindo o build do React — `serve_react`/`serve_react_assets`,
`app.py`), os `<script>`/`<link>` gerados pelo Vite em `frontend/dist/index.html` usam caminho
absoluto `/assets/...` (`base: '/'` em `vite.config.js`), mas a rota Flask que serve esses arquivos é
`/app/assets/<filename>` (prefixo `/app`). Toda requisição de asset (`.js`/`.css`) retorna 404, e a
SPA nunca monta — tela em branco.

Impacto:
Alto no modo processo único especificamente (torna essa forma de deploy inutilizável), mas **zero
impacto na produção real hoje** — produção roda backend (Render) e frontend (Vercel) como serviços
separados, onde a Vercel serve `frontend/dist` na sua própria raiz e o caminho absoluto `/assets/...`
funciona sem problema. Só afeta quem tentar rodar `app.py` localmente/como deploy alternativo servindo
o build React embutido.

Status:
Aberto — identificado em 2026-07-21 durante o smoke test de RC da migração `unidades_serializadas`
(`docs/engineering/migrations/MIGRATION_unidades_serializadas.md`), ao tentar validar visualmente
contra `http://.../app` local. Contornado para o smoke test usando `npm run dev` (proxy do Vite para
a API) em vez do modo processo único — não bloqueou a validação da migração. Não corrigido nesta
sessão por estar fora do escopo da migração (regra de mudança única do `CLAUDE.md`); corrigir exigiria
decidir entre alinhar `vite.config.js` (`base: '/app/'`) ou a rota Flask (`/assets/<filename>` sem
prefixo) — decisão de arquitetura pequena, mas real, não tomada unilateralmente aqui.

Sprint prevista:
Não definida — sem urgência, já que o modo afetado não é o usado em produção.

Responsável:
—

---

## ~~KI-020~~ — RESOLVIDO

Descrição:
`POST /api/estoque` (`criar_estoque`) e `PUT /api/estoque/<id>` (`atualizar_estoque`), em
`irflow_blueprints_api.py`, nunca liam `body.get("requer_imei")` — a coluna `estoque.requer_imei`
(existe desde a Sprint 3 Unidade 6, `DEFAULT 0`) não fazia parte do `INSERT`/`UPDATE` de nenhuma das
duas rotas. Por comparação, o domínio `produtos` tem o campo equivalente (`requer_rastreio_unidade`)
totalmente cabeado em `irflow_produtos_controller.py`/`_service.py`/`_repository.py` — a assimetria era
só do lado Estoque. O nome da coluna é histórico (IMEI); o conceito é rastreabilidade individual do
item (IMEI hoje, outros identificadores de série no futuro).

Impacto:
Médio/Alto (funcional, não de segurança). Não existia **nenhum caminho via API/UI** para marcar um
item de `estoque` como `requer_imei=1` — todo item criado nascia com o default `0` e nunca podia mudar.
Na prática, isso tornava o caminho "unidade serializada com origem em Estoque" (`irflow_
unidades_serializadas_service.py::criar_unidade`, parâmetro `estoque_id`) inutilizável em produção —
só o caminho com origem em `produtos` funcionava de ponta a ponta. Achado ao semear dados de teste
reais para a Sprint Comercial C1.3.1 (Tela Unidades Serializadas): setar `requer_imei` exigia escrever
direto no banco, contornando a API por completo.

Status:
Resolvido em 2026-07-27 (Sprint Comercial C1.3.5 — Rastreabilidade Individual de Itens de Estoque,
branch `feat/estoque-requer-imei`). `listar_estoque()`/`criar_estoque()`/`atualizar_estoque()` passam a
ler/gravar/expor `requer_imei`, mesmo padrão já usado em `produtos.requer_rastreio_unidade`.
`frontend/src/pages/Stock.jsx` ganhou o checkbox correspondente. 8 novos testes, incluindo o fluxo
completo via API (criar item rastreável → criar unidade serializada com sucesso) e a confirmação de que
um item sem a flag continua rejeitado (regressão). Ver `docs/operations/SPRINTS/SPRINT_COMERCIAL_1.3.5.md`.

Sprint prevista:
Sprint Comercial C1.3.5 — concluída em 2026-07-27.

Responsável:
—

---

## ~~KI-021~~ — RESOLVIDO

Descrição:
`getOrderDisplayNumber` (`frontend/src/lib/constants.js`) sempre exibia o `id` interno da OS (`#866`),
mesmo para Ordens de Serviço importadas do MercadoPhone — que deveriam mostrar o número real da
integração (`os.id_externo_integracao`) para permitir localizar a OS pelo número que o cliente/
MercadoPhone usa, sincronizar atualizações e evitar duplicidade ao importar.

Impacto:
Alto (operacional). Usado em produção real — dificultava conferência cruzada entre o sistema e o
MercadoPhone para toda OS de origem `mercado_phone`. `os.origem_integracao`/`os.id_externo_integracao`
já existiam no schema e já eram retornados por `GET /api/ordens` (`_os_row_to_dict`); o dado nunca
esteve ausente, só não era usado pela função de exibição.

Status:
Resolvido em 2026-07-22 via `hotfix/os-numero-mercadophone` (Hotfix H-003, pedido do usuário — CTO).
Regressão identificada no commit `fda0929` (2026-06-09, co-autoria "Copilot", mensagem "fix shopping
list mismatch"): a versão original de `getOrderDisplayNumber` já preferia `id_externo_integracao`
quando `origem_integracao === "mercado_phone"`, com fallback para `String(order.id).slice(-5)` — o
truncamento (`.slice(-5)`) era o bug real por trás daquele commit, mas a correção da época removeu a
preferência pelo número externo inteira, não só o truncamento. Restaurada a preferência pelo número
externo, sem reintroduzir o truncamento. Nenhuma mudança de schema/backend — os dados já existiam e já
eram retornados pela API; só a exibição no frontend estava errada. Validado manualmente: OS nativa
exibe `#1` (id interno), OS com `origem_integracao='mercado_phone'` exibe `#MP-90210` (número externo
semeado via API/banco isolado para o teste).

Sprint prevista:
Fora de sprint — pedido direto do usuário (CTO), prioridade por bloqueio operacional imediato
(Hotfix H-003, junto do achado de deploy pendente descrito no Problema 1 do mesmo pedido).

Responsável:
—

---

## ~~KI-025~~ — RESOLVIDO

Descrição:
As rotas legadas de escrita baseadas em formulário HTML (`irflow_blueprints_orders.py`,
`irflow_blueprints_inventory.py`, `irflow_blueprints_admin.py`, e as views de gestão de usuário em
`irflow_blueprints_auth.py`/`POST /usuarios/novo|editar|deletar`) faziam mutações reais no banco
(criar/editar/excluir OS, estoque, custos, reparos, tabelas de preço, usuários) protegidas só por
cookie de sessão — sem nenhum token CSRF. Em produção, `SESSION_COOKIE_SAMESITE = "None"` (`app.py`,
necessário porque frontend/backend são origens diferentes — Vercel/Render) faz o cookie ser enviado em
requisições cross-site. `flask-wtf` nunca esteve instalado, não havia `CSRFProtect` em lugar nenhum, e
`tests/conftest.py` chegou a ter uma config `WTF_CSRF_ENABLED = False` sem efeito nenhum (evidência de
que alguém assumiu uma proteção que nunca existiu). Achado durante a Fase 1 (API endpoints/banco) de uma
auditoria de segurança pedida pelo usuário (CTO).

Impacto:
Crítico. Uma página maliciosa com um `<form>` auto-submit para `POST /usuarios/novo` (`perfil=admin`),
visitada por um admin autenticado, criava uma conta admin controlada pelo atacante — tomada de conta
completa. Mesma classe de ataque contra `/deletar/<id>` (OS), `/estoque/deletar/<id>`,
`/custos-operacionais`, `/backup` (criar backup/disparar e-mail), etc.

Status:
Resolvido em 2026-07-26. Removidas por completo as rotas de escrita vulneráveis, em vez de adicionar
Flask-WTF para proteger uma superfície já confirmada sem uso real: `irflow_blueprints_orders.py`,
`irflow_blueprints_inventory.py` e `irflow_blueprints_admin.py` deletados por inteiro;
`irflow_blueprints_auth.py` perdeu as views de gestão de usuário (mantidos só `login`/`logout`);
`irflow_blueprints_main.py::backup()` perdeu a lógica de escrita (POST), virando GET-only. Confirmado
antes de remover: o frontend React usa exclusivamente os equivalentes JSON em `/api/*`
(`frontend/src/api/client.js`, grep sem nenhuma chamada às rotas removidas); não existe pasta
`templates/` no repositório (os `render_template()` no fim dessas views eram código morto
inalcançável); todo redirecionamento GET dessas rotas continua idêntico via
`LEGACY_REACT_REDIRECTS`/`destino_react_legado()`, que roda no `before_request` antes da resolução de
rota e não depende da view function existir. `POST /api/backup/criar` já existe e já é o que o
frontend usa. Testes das rotas removidas (`test_auth.py::TestControleDeAcessoPorPerfil`,
`test_permissions.py::TestPermissoesEditarUsuarioLegado`/`TestPermissoesDeletarUsuarioLegado`,
`test_session_inactivity.py::TestInatividadeSessaoViewLegada`) removidos — cobertura equivalente já
existe em `test_users.py` (`/api/usuarios`) e `TestInatividadeSessaoApi`. 514 testes passando (queda em
relação à contagem anterior é esperada — testes de funcionalidade removida, não regressão),
`ruff check .` limpo.

Sprint prevista:
Fora de sprint — achado durante auditoria de segurança pedida pelo usuário (CTO), corrigido via branch
`fix/csrf-rotas-legadas-escrita`.

Responsável:
—

---

## ~~KI-022~~ — RESOLVIDO

Descrição:
`POST /api/integracoes/mercadophone/{sincronizar,reprocessar,reimportar}` (`irflow_blueprints_api.py`)
só checavam `usuario_logado()` — qualquer perfil autenticado, inclusive `vendedor`, podia disparar essas
operações. O mais grave era `/reimportar` → `reimportar_todas_os_mercado_phone()`
(`irflow_mercadophone.py:1220-1255`): apaga **todas** as OS com `origem_integracao='mercado_phone'` (mais
`os_reparos`/`integracao_os_vistas` relacionados) e reimporta do zero — mesmo efeito de um
`DELETE /api/ordens` em massa, mas por um caminho de código que ficou fora da restrição já aplicada a
`/api/ordens*` em 2026-07-25 (`docs/security/SECURITY_AUDIT_2026-07.md` item 14). `/sincronizar` e
`/reprocessar` sobrescrevem campos de OS existentes a partir da API externa — mesma categoria, sem
deletar. Achado durante auditoria de segurança pedida pelo usuário (CTO), Fase 1 (integração
MercadoPhone).

Impacto:
Alto. Qualquer perfil autenticado (inclusive `vendedor`, que segundo os documentos de produto não
deveria ter acesso administrativo a Estoque/OS) podia apagar e reimportar em massa as OS de origem
MercadoPhone, ou sobrescrever campos existentes a partir da API externa, sem nenhuma confirmação de
perfil.

Status:
Resolvido em 2026-07-26. Adicionada a mesma checagem já usada em `criar_ordem`/`atualizar_ordem`/
`deletar_ordem` (`session.get("usuario_perfil") not in ("admin", "tecnico")` → 403) aos 3 endpoints de
mutação. Endpoints de status (GET, só leitura) e `salvar_config_mercadophone` (já exigia `admin`) não
alterados. Módulo não tinha nenhum teste de autorização antes (R-07) — 4 novos testes em
`tests/test_mercadophone_permissions.py` (sem sessão, `vendedor`, `tecnico`, `admin` × 3 endpoints).
529 testes no total, `ruff check .` limpo.

Sprint prevista:
Fora de sprint — achado durante auditoria de segurança pedida pelo usuário (CTO), corrigido via branch
`fix/mercadophone-mutacao-em-massa-permissao`.

Responsável:
—

---

## ~~KI-023~~ — RESOLVIDO

Descrição:
`app.py`, `autenticar_integracao_mercado_phone()` (autenticação do webhook `POST
/api/integracoes/mercadophone/os`): quando `MERCADO_PHONE_WEBHOOK_TOKEN` não está configurada, a função
tinha um early-return que pulava toda a validação — o endpoint ficava aberto sem autenticação alguma.
`.env.example`/`DEPLOY.md` chegavam a documentar esse comportamento como aceitável em dev local. Achado
durante a Fase 1 (Auth/Middleware) de uma auditoria de segurança pedida pelo usuário (CTO).

Impacto:
Alto (potencial). Se a variável estivesse vazia em produção, qualquer requisição não autenticada poderia
injetar Ordens de Serviço falsas na tabela `os` real via webhook público. Confirmado com o usuário (CTO)
que a variável está configurada com valor forte em produção hoje — não houve exploração ativa.

Status:
Resolvido em 2026-07-26. Removido o early-return: sem token configurado, nenhum candidato corresponde e a
rota rejeita com 401 por padrão (fail secure). Comparação do token trocada de `in`/`==` para
`hmac.compare_digest` (constant-time), fechando também um timing side-channel teórico (CWE-208)
encontrado na mesma função. `.env.example`/`DEPLOY.md` atualizados para marcar a variável como
obrigatória. 3 testes novos (`tests/test_mercadophone_webhook_auth.py`).

Sprint prevista:
Fora de sprint — achado durante auditoria de segurança pedida pelo usuário (CTO), corrigido via branch
`fix/mercadophone-webhook-fail-secure`.

Responsável:
—

---

## ~~KI-024~~ — RESOLVIDO

Descrição:
`app.py`, `verificar_autenticacao()`: `ROUTE_PERMISSIONS.get(endpoint)` retorna `None` tanto para uma
entrada explícita `None` no dict (qualquer perfil logado) quanto para uma chave ausente — um endpoint
legado novo adicionado sem entrada correspondente em `ROUTE_PERMISSIONS` ficava liberado por padrão para
qualquer usuário autenticado, em vez de negado. Achado durante a mesma auditoria de segurança do KI-023.
Confirmadas 6 entradas já mortas no dict (`sync_os_mercado_phone`, `status_sync_mercado_phone`,
`order_views.autocomplete_clientes`/`api_buscar_pecas`/`api_remover_peca`/`api_adicionar_peca`) apontando
para funções que não existem mais em nenhum blueprint — prova de que o dict já divergia do código real.

Impacto:
Médio (arquitetural, não exploit ativo). Verificado manualmente que todos os endpoints hoje registrados em
`main_views`/`order_views`/`inventory_views`/`admin_views`/`auth_views` estão cobertos no dict — nenhum
endpoint real está sendo liberado indevidamente hoje. O risco era o padrão de falha silenciosa no futuro.

Status:
Resolvido em 2026-07-26. Adicionado um sentinel em `verificar_autenticacao()` para distinguir os dois
casos — endpoint ausente do dict agora é negado por padrão (fail secure). As 6 entradas mortas
permanecem no dict sem efeito (limpeza fica para um `chore:` separado, não misturado com a correção de
segurança). 3 testes novos (`tests/test_route_permissions_fail_secure.py`).

Sprint prevista:
Fora de sprint — achado durante auditoria de segurança pedida pelo usuário (CTO), corrigido via branch
`fix/mercadophone-webhook-fail-secure`.

Responsável:
—

---

## ~~KI-026~~ — RESOLVIDO (causa 3); mitigado (governança, ver TD-13)

Descrição:
O workflow `CI` (`.github/workflows/ci.yml`) não registrava nenhum sucesso em `main` até esta revisão —
confirmado via `gh api repos/.../actions/workflows/ci.yml/runs?branch=main` (campo `total_count`
autoritativo da API, não a listagem client-side de `gh run list`, que trunca por paginação): **84 de 84
execuções em `main` terminaram em falha** (`status=failure`, `status=success` retorna `total_count: 0`),
do primeiro run (2026-07-07) até o mais recente antes desta revisão (2026-07-27). Considerando todas as
branches do repositório (não só `main`), o total sobe para 105 runs, também 0 sucessos — número usado
por engano como "105/105 em `main`" numa versão anterior desta entrada, corrigido nesta revisão. A causa
raiz mudou ao longo do tempo, sempre no mesmo job (`Frontend Quality`, que roda `npm ci` + `npm run
lint`):

1. **2026-07-07 a ~2026-07-20:** `ruff check .` vermelho (KI-017, já documentado e resolvido — mas o
   job `Frontend Quality`/ESLint nunca foi mencionado nessa investigação, então ninguém percebeu que ele
   também estava vermelho o tempo todo).
2. **~2026-07-23 a ~2026-07-26:** o próprio `npm ci` falhava antes de chegar a rodar o ESLint —
   `frontend/package-lock.json` fora de sincronia com `frontend/package.json` (`npm error Missing:
   @emnapi/core@1.9.2`, `@emnapi/runtime@1.9.2`, `@emnapi/wasi-threads@1.2.1` — dependências opcionais
   nativas do motor Oxide do Tailwind CSS v4, `@tailwindcss/vite`/`tailwindcss` em `package.json`).
   `npm ci` é estrito e falha nessa divergência; rodar `npm install` localmente (que atualiza o
   lockfile silenciosamente) mascarava o problema sem ninguém perceber.
3. **~2026-07-26 até esta revisão (2026-07-27):** `npm ci` passa, mas `npm run lint` falha de verdade —
   4 erros pré-existentes, não relacionados a nenhuma sprint recente: `Compras.jsx:20`
   (`react-hooks/set-state-in-effect`), `Compras.jsx:28`, `ShoppingModal.jsx:46`,
   `ServicesChartCard.jsx:38`, `TechnicianProfitChartCard.jsx:48` (`no-unused-vars`). Mais 2 warnings
   não bloqueantes (`react-hooks/exhaustive-deps` em `ShoppingList.jsx`/`Stock.jsx`).

Achado ao investigar o CI da branch `feat/vendas-historico-detalhe` (Sprint Vendas 1.1): o commit WIP
dessa branch falhava no `Frontend Quality` por um erro próprio (corrigido nesta sprint, ver
`PROJECT_STATUS.md`), o que levou a verificar se `main` também estava afetado — estava, e por um motivo
diferente e mais antigo, não introduzido por essa branch.

Impacto:
Alto (processo, não funcional em produção — nenhuma das três causas envolve regra de negócio ou dado). O
job `Frontend Build` depende de `Frontend Quality` (`needs: frontend`) e nunca chega a rodar enquanto ela
falhar — ou seja, **o build do frontend não é verificado pelo CI há pelo menos 20 dias**, apesar de
`PROJECT_STATUS.md` descrever o CI como saudável (`ruff check .` → 0 erros é verdade, mas cobre só o job
`Lint`/Ruff — backend). `Backend Tests`/`Coverage`/`Lint` (Ruff) não são afetados e continuam passando
normalmente em cada run — só o gate de qualidade do frontend está sistematicamente quebrado.

Status:
**Causa 3 (ESLint) resolvida em 2026-07-27, Sprint Infra 1.1** — branch `chore/frontend-eslint-cleanup`
a partir de `main` (regra de mudança única do `CLAUDE.md` preservada: só os 4 arquivos com erro, nenhuma
mudança de comportamento), mergeada em `main`. Primeiro sucesso do workflow `CI` identificado nas
execuções verificadas (`total_count` da API, run `30313428268`, commit `a86cc62`). Causa 1 (Ruff) já era
história. Causa 2 (`npm ci`) recorreu (ver nota abaixo) — não é mais um problema encerrado.

**Recorrência da causa 2 (2026-08-17, PR #49 — Landing Page):** `npm install @radix-ui/react-accordion`
rodado no Windows local removeu de novo as entradas top-level `node_modules/@emnapi/core`/
`node_modules/@emnapi/runtime` do `frontend/package-lock.json` (o npm no Windows só resolve a build nativa
da plataforma atual, mas o `npm ci --strict` do runner Linux do CI exige as duas para validar
`bundleDependencies` de `@tailwindcss/oxide-wasm32-wasi`). `Frontend Quality`/`Frontend Unit Tests`
falharam na primeira execução; corrigido no mesmo ciclo com um commit `fix:` isolado (versões/hashes
reconferidos contra o registry antes de reaplicar), CI reexecutado do zero: 8/8 verde. Registrado por
decisão do CTO — não é mais um caso isolado resolvido em 2026-07, é uma fragilidade estrutural do fluxo
`npm install` (Windows) → `npm ci` (CI Linux) sempre que uma dependência nova é adicionada a partir de uma
máquina Windows. Nenhuma correção estrutural aplicada ainda (ex.: gerar/validar o lockfile a partir de um
ambiente Linux, ou script de verificação pré-push) — fica como possível item futuro, fora do escopo do
PR #49 (ver `docs/engineering/plans/PLAN-landing-page-implementacao.md`).

**Achado relacionado, mais grave (2026-07-27, mesma investigação):** o motivo de 84/84 falhas nunca terem
travado um merge é que `main` **não tinha nenhuma proteção de branch configurada** — confirmado via
`gh api repos/.../branches/main/protection` retornando `404 Branch not protected` (não "sem status check
obrigatório": não existia objeto de proteção nenhum — sem revisão obrigatória, sem status check
obrigatório, sem bloqueio de force-push a nível de GitHub). O CI existia e rodava, mas nunca funcionou
como gate — qualquer PR/push podia mergear em `main` independente do resultado. **Mitigado em
2026-07-27**, mesma sessão, imediatamente após confirmar `main` verde: proteção ativada via `gh api`
exigindo os 5 status checks (`Lint`, `Backend Tests`, `Frontend Quality`, `Frontend Build`, `Coverage
Report`), `strict: true`, bloqueio de force-push/deleção. `enforce_admins` deixado em `false`
deliberadamente — não quebra o fluxo atual de merge local + push direto do usuário (CTO, único mantenedor
hoje); ver TD-13 para o endurecimento completo quando a equipe crescer. Ver R-10/R-11 em
`PROJECT_STATUS.md`.

Sprint prevista:
Sprint Infra 1.1 — concluída em 2026-07-27.

Responsável:
—

---

## ~~KI-027~~ — RESOLVIDO (causa raiz reclassificada)

Descrição:
Ambiente de automação de navegador (Chrome via ferramenta de automação) não persiste o cookie de sessão
`HttpOnly` gerado por `POST /api/auth/login`: o login retorna `200 ok:true`, mas a próxima requisição
same-origin na mesma aba (`GET /api/auth/me` ou qualquer rota autenticada) recebe `401`. Testado com
múltiplas abas/tab groups novas, cliques reais na UI e `fetch` direto via JS no console da página —
sempre o mesmo resultado. O mesmo fluxo de login, contra o mesmo backend, funciona instantaneamente via
`curl` (tanto direto na porta do Flask quanto através do proxy do Vite), e um cookie não-`HttpOnly` de
teste (`document.cookie`) persiste normalmente na mesma aba — descarta bloqueio geral de cookies do
perfil. Não há ferramenta disponível para inspecionar o cookie `HttpOnly` armazenado pelo Chrome nessa
automação (JS não pode lê-lo, por design do navegador), então não foi possível confirmar se o cookie é
rejeitado no armazenamento ou apenas não reenviado.

Impacto:
Médio, só para o processo de trabalho — impede QA Manual via navegador real dentro deste ambiente de
automação para qualquer feature que dependa de sessão autenticada. Nenhum impacto em produção nem no
código da aplicação (o mesmo fluxo funciona normalmente em `curl`, e a suíte automatizada cobre a lógica
de sessão via `flask.testing` client, que não depende deste mecanismo de cookie do navegador).

Status:
**Causa raiz real encontrada em 2026-07-30**, durante QA manual da UX-001 (Preservação de Contexto da
Navegação) — não é característica do ambiente de automação, como suposto em 2026-07-29. `app.py` liga
`IS_SERVER_RUNTIME=True` sempre que `IR_FLOW_DATA_DIR` está definido (linha ~187) — a mesma variável usada
para isolar qualquer sessão de QA local do `database.db` real. Com `IS_SERVER_RUNTIME=True`, o cookie de
sessão sai com `Secure; SameSite=None; Partitioned` (confirmado via `curl -i` contra `http://127.0.0.1:5080`
rodando com `IR_FLOW_DATA_DIR` setado: `Set-Cookie: session=...; Secure; HttpOnly; Path=/; SameSite=None;
Partitioned`). O atributo `Secure` exige HTTPS — um navegador real (Chrome via Claude in Chrome, ou
qualquer outro) descarta silenciosamente esse cookie numa conexão `http://localhost` pura, exatamente o
sintoma original (login `200`, toda requisição seguinte `401`). `curl` com `-b`/`-c` (cookie jar) é mais
permissivo que um navegador real quanto ao atributo `Secure` sobre `http://`, o que explica por que o
mesmo fluxo "funcionava instantaneamente via curl" — não é um cookie geral bloqueado, é especificamente a
combinação `Secure` + `http://`.

**Confirmado resolvido**: rodando o backend com um override local de `app.config["SESSION_COOKIE_SECURE"] =
False` / `SESSION_COOKIE_SAMESITE = "Lax"` / `SESSION_COOKIE_PARTITIONED = False` (só no processo da sessão
de QA, nenhuma mudança em `app.py`), o cookie passou a persistir normalmente no Chrome real via Claude in
Chrome — login, navegação autenticada, scroll/filtro/destaque da UX-001 validados ponta a ponta sem
nenhum 401. Zero impacto em produção (lá é HTTPS real via Render/Vercel, `Secure` é o comportamento
correto) — o problema só existe ao rodar `IR_FLOW_DATA_DIR` + servidor real + navegador real + `http://`
simultaneamente, combinação que só acontece em QA manual local, nunca em produção nem na suíte automatizada
(`flask.testing` não depende do mecanismo de cookie do navegador).

**Não corrigido em código** — nenhuma mudança em `app.py` feita a partir deste achado; ver "Próximos
passos" abaixo para a decisão pendente sobre se vale introduzir uma flag de override para facilitar QA
manual local futura.

Sprint prevista:
Não definida.

Responsável:
—

Próximos passos (não decidido, registrado para referência futura):
Considerar uma variável de ambiente dedicada (ex.: `IR_FLOW_FORCE_INSECURE_COOKIE=1`) para permitir QA
manual local com `IR_FLOW_DATA_DIR` + navegador real sem precisar de um script wrapper ad-hoc como o usado
nesta sessão — decisão de arquitetura pequena, não tomada unilateralmente aqui.

**Observação (2026-07-30, QA Manual da V1.5 — Garantia):** login e navegação autenticada via Claude in
Chrome funcionaram normalmente nesta sessão com `IR_FLOW_DATA_DIR` setado (`IS_SERVER_RUNTIME=True`,
cookie `Secure; SameSite=None; Partitioned`), sem nenhum wrapper/override de `SESSION_COOKIE_SECURE` —
mesma combinação que reproduzia o 401 na sessão da UX-001. Hipótese não confirmada: `localhost`/`127.0.0.1`
são tratados por Chrome como origens "potencialmente confiáveis" havia algumas versões, o que satisfaria o
atributo `Secure` mesmo sem HTTPS — se essa for a causa, o sintoma pode depender da versão do Chrome usada
pela ferramenta de automação em cada sessão, não ser 100% determinístico. Não investigado a fundo (fora do
escopo da sessão de V1.5); registrado só para não assumir que o wrapper de `SESSION_COOKIE_SECURE` é
sempre necessário daqui pra frente.

**Nova reprodução (2026-08-16, QA Manual do PR 7 — Final QA da Fase 1 do Design System):** com o wrapper
de override já aplicado (`SESSION_COOKIE_SECURE=False`/`SAMESITE=Lax`/`PARTITIONED=False`, confirmado via
`curl -i` que o header `Set-Cookie` de fato saía sem `Secure`), o login via Claude in Chrome ainda assim não
persistiu a sessão entre requisições: `POST /api/auth/login` retornou `200` e populou o estado do usuário no
React (a UI mostrou nome/perfil corretamente, porque `Login.jsx` usa a resposta do próprio login, sem
depender de um `GET /api/auth/me` separado), mas a chamada seguinte real (`GET /api/dashboard`) voltou
`401`, e um `fetch('/api/auth/me', {credentials:'include'})` manual confirmou `401`/`{"ok":false}`.
**Confirmado que não é bug de código:** o mesmo fluxo (login → cookie → `/api/auth/me`) via `curl` com
cookie jar, passando pelo mesmo proxy do Vite (`http://localhost:5173`), funcionou perfeitamente (`200`,
sessão reconhecida) — o backend, o proxy e o `SESSION_COOKIE_*` override estão corretos; o problema é
inteiramente da persistência de cookie dentro do navegador de automação nesta sessão específica, reforçando
a hipótese de dependência de versão/perfil do Chrome já registrada acima. Também testado e descartado:
`127.0.0.1:5173` não é uma alternativa via este ambiente (Vite não aceita conexão nesse host aqui — só
`localhost`). **Efeito colateral útil:** essa reprodução acabou validando organicamente o estado de erro do
Dashboard (`DashboardError`, PR #46) — a tela mostrou exatamente "Erro ao carregar dashboard." com botão
"Tentar novamente", disparado por um 401 real, não simulado.

---

## KI-029

Descrição:
Dois arquivos de backup de banco de dados estão versionados no git e presentes em `main` até hoje:
`backup-20260429-015724.db` (commit `8b69767`, 2026-04-28) e
`database-pre-cleanup-20260517-123834.db` (commit `252815a`, 2026-05-17). Ambos parecem conter dados
operacionais reais — o primeiro tem 74 linhas em `os` e 2 em `usuarios`; nesse snapshot a tabela
`clientes` ainda não existia, então nomes de cliente ficavam em campo de texto livre dentro de `os`.
Achado incidentalmente durante `AUDIT_LEGACY.md` (Sprint Housekeeping, Fase 1), ao buscar por
`assistencia-system` como parte da varredura de nomenclatura legada.

**Atualização (2026-07-31, `AUDIT_REPOSITORY.md`):** mesmo padrão encontrado em mais dois arquivos,
ainda presentes em `main`: `database.db-shm` (32KB — índice de memória compartilhada do modo WAL do
SQLite, pode conter fragmentos de dados de transações recentes) e `database.db-wal` (0 bytes no momento
da auditoria, mas já foi commitado com conteúdo em algum ponto do histórico — commits `4fef090`
2026-06-09 e `f20521f` 2026-05-05). `database.db` em si já está no `.gitignore`, mas o padrão exato não
cobre os sidecars `-shm`/`-wal` do modo WAL, então eles vazaram pela mesma lacuna.

Impacto:
Alto em potencial (dado operacional/possivelmente PII no histórico do git, acessível a qualquer clone
do repositório), mas sem exploração confirmada — não é uma vulnerabilidade explorável remotamente, é
exposição de dado em um artefato versionado. Contraria diretamente os princípios "O banco é sagrado" e
"sempre manter testes isolados" do `CLAUDE.md`. As regras de `.gitignore` adicionadas depois
(`database.db`, `backups/`) não cobrem esses nomes de arquivo específicos (nem os dois backups, nem os
sidecars `-shm`/`-wal`) e não afetam arquivos já commitados de qualquer forma.

Status:
Aberto — parcialmente endereçado. **Fase 1 concluída em 2026-08-17** (branch `feat/lgpd-compliance-fase1`,
commit `c5e64f37`, ver `docs/engineering/plans/PLAN-LGPD-Compliance.md`): os dois arquivos removidos do
índice (`git rm --cached`, não do histórico) e `.gitignore` reforçado para impedir recorrência. **Fase 2
(reescrita de histórico) permanece não executada** — decisão explícita necessária do CTO antes de
qualquer mudança, dado que reescrever histórico (`git filter-repo`/BFG + force-push) é uma operação
destrutiva que exige aprovação própria e específica, separada desta Fase 1.

Sprint prevista:
Não definida — decisão pendente sobre remover do working tree vs. reescrever histórico vs. avaliar
se os dados ainda são sensíveis o suficiente para justificar a operação destrutiva. Para os dois
sidecars `-shm`/`-wal`, a ação de baixo risco (destrackear + ajustar `.gitignore` para `database.db-*`)
pode ser feita independentemente da decisão maior sobre os dois backups.

Responsável:
—

---

## ~~KI-028~~ — RESOLVIDO

Descrição:
Datas "puras" (`YYYY-MM-DD`, sem componente de horário) são exibidas um dia antes do valor real gravado
no banco em qualquer tela que use o padrão `new Date(string).toLocaleDateString("pt-BR")`. Causa:
`new Date("2027-07-30")` é interpretado pelo JavaScript como meia-noite UTC; `.toLocaleDateString()`
renderiza no fuso horário local do navegador — em `America/Sao_Paulo` (UTC-3), isso sempre volta um dia
(`29/07/2027`). Confirmado via `Intl.DateTimeFormat().resolvedOptions().timeZone` (`America/Sao_Paulo`,
offset 180min) e comparação direta com o valor cru da API (`garantia_data_fim: "2027-07-30"` no banco vs.
"29/07/2027" na tela). O dado persistido está sempre correto — o problema é exclusivamente de exibição.

Impacto:
Médio. Achado durante o QA Manual da V1.5 (Garantia) em `VendaDetalhe.jsx` (`garantia_data_fim`), mas o
mesmo padrão (`new Date(<campo_date_only>).toLocaleDateString("pt-BR")`) já existe em outras telas com
campos que podem ser data pura: `Garantias.jsx` (`data_finalizado`), `Clientes.jsx` (`o.data`),
`OperationalCosts.jsx` (`c.data`), `Reports.jsx` (`item.data`), `Stock.jsx` (`item.data_compra`) — nem
todos esses campos são necessariamente gravados sem horário (alguns podem ter
`datetime('now')`/`HH:MM:SS`, o que mitigaria o efeito), não auditado campo a campo nesta sessão. Os
campos novos da V1.5 (`garantia_data_inicio`/`garantia_data_fim`, sempre `date.isoformat()`, nunca com
horário) são afetados 100% das vezes, para qualquer usuário em fuso UTC-negativo — relevante para uma
feature de garantia, onde a data de vencimento exibida importa para a decisão de cobrir ou não um reparo.
Nenhum critério objetivo de interrupção de `ENGINEERING_GUIDE.md` §11 é atendido (não é mutação de dado
persistido — só exibição; não há perda de dado nem bypass de autorização), por isso não interrompeu a
sessão — caracterizado e registrado aqui, conforme o fluxo "não interrompa" da mesma seção.

Status:
Resolvido em 2026-07-30, no Encerramento da V1.5 (decisão do usuário — CTO, de corrigir dentro do escopo
da própria feature em vez de adiar). Escopo cirúrgico: só o único ponto onde `garantia_data_fim` é
exibido (`VendaDetalhe.jsx`) — as outras telas com o mesmo padrão (`Garantias.jsx`, `Clientes.jsx`,
`OperationalCosts.jsx`, `Reports.jsx`, `Stock.jsx`) usam campos que não são exclusivos da V1.5 e ficam
fora do escopo desta correção, registradas acima como conhecidas. Corrigido reaproveitando
`formatDateTime()`, helper já existente no próprio arquivo (usado para `criado_em`/`cancelado_em`/eventos
de auditoria) que já fazia o parse manual de ano/mês/dia em vez de `new Date(string)` — zero código novo,
só trocar a chamada. Validado: venda criada com `garantia_data_fim: "2027-07-30"` (confirmado via API)
agora exibe "até 30/07/2027" (antes: "29/07/2027").

Sprint prevista:
Não definida.

Responsável:
—

---

## KI-030

Descrição:
`tests/test_sentry_init.py::test_com_sentry_dsn_valido_inicializa_sem_erro` falha localmente em ambiente
Windows com Python 3.14: `import app` (via subprocess) carrega `sentry_sdk`, que importa `asyncio`, que
em `asyncio/windows_events.py` tenta importar `_overlapped` e recebe `OSError: [WinError 10106] O
provedor de serviços solicitado não pôde ser carregado ou inicializado` — falha ao inicializar um
provedor de rede do Winsock nesta máquina, não um bug de código. Achado durante a suíte completa rodada
antes do commit do Lote 4a (Sprint Housekeeping, rename `irflow_os.py` → `fluxoly_os.py`); confirmado via
`git stash` que o teste já falhava da mesma forma em `main` antes do rename — não é uma regressão
introduzida por ele.

Impacto:
Baixo. Nenhum critério objetivo de `ENGINEERING_GUIDE.md` §11 é atendido — não muta dado, não perde dado,
não faz bypass de autorização, e o código do teste em si (`import asyncio` dentro do `sentry_sdk`) não é
um caminho de produção real acessado pelo frontend. CI roda em runner Linux (GitHub Actions), onde
`asyncio/windows_events.py` nunca é importado — não deve reproduzir lá. Efeito prático: mais um teste
"vermelho" a ignorar mentalmente ao rodar a suíte localmente nesta máquina, o que atrapalha
`ENGINEERING_GUIDE.md` "nunca ignorar testes falhando" se não for documentado.

Status:
Aberto — não investigado a fundo. Atualização (2026-08-04, bootstrap de ambiente Windows nesta mesma
máquina): reproduzido de forma idêntica (`WinError 10106` no mesmo ponto) numa `.venv` nova criada com
Python 3.12.10, não só 3.14.

Hipótese descartada: o problema não é específico do Python 3.14, pois foi reproduzido também em uma
instalação limpa com Python 3.12.10. Aponta mais para driver/serviço Winsock ausente ou desabilitado
nesta instalação Windows especificamente (afeta qualquer versão de Python nesta máquina, não é por
versão). Nenhuma ação tomada; suíte segue sendo tratada como "681 passed, 1 failed (ambiente)" nesta
máquina até confirmação em CI ou outro ambiente.

Sprint prevista:
Não definida — não bloqueia a Sprint Housekeeping (achado incidental, caracterizado e reportado aqui,
conforme o fluxo "não interrompa" de `ENGINEERING_GUIDE.md` §11).

Responsável:
—

## KI-031

Descrição:
As 6 rotas do domínio Relatórios (`GET /api/relatorios/ir-phones`, `/tecnicos`, `/custos-operacionais` e
as 3 variantes `/pdf/*`) não têm nenhum teste dedicado — `grep -rl "relatorio" tests/` retorna vazio.
Achado durante a Discovery de extração de `api_reports.py` (TD-01 Phase 2, 8º domínio, 2026-08-06):
diferente dos 7 domínios já extraídos, a suíte completa (683 testes) passar não é evidência de que essas
6 rotas continuam funcionando após a extração, porque nenhum teste as exercita.

Impacto:
Baixo a médio. Nenhum critério objetivo de `ENGINEERING_GUIDE.md` §11 é atendido pela ausência de teste
em si (não é um bug de comportamento, é uma lacuna de cobertura). Mas significa que qualquer regressão
futura nessas 6 rotas (nesta extração ou em qualquer mudança seguinte) não será pega pela suíte —
depende de verificação manual ou de uso real em produção para ser detectada.

Status:
Aberto. Decisão do CTO (2026-08-06): não misturar escrita de testes novos com a extração de blueprint
(escopo cirúrgico da TD-01) — a extração segue verbatim, e esta lacuna fica registrada aqui para ser
endereçada em sprint própria de cobertura de testes.

Sprint prevista:
Não definida — candidata a sprint de cobertura de testes, fora do escopo da TD-01.

Responsável:
—

---

## ~~KI-032~~ — RESOLVIDO

Descrição:
Em `fluxoly_blueprints_api.py`, `_slug_estoque()`/`_gerar_sku_estoque()` (linhas 79-109) geram um SKU
automaticamente a partir de modelo/tipo/qualidade/descrição, mas nunca são chamados por nenhuma das 6
rotas do domínio Estoque — `criar_estoque()`/`atualizar_estoque()` usam `body.get("sku")` enviado pelo
cliente diretamente, sem gerar. Achado durante a Discovery de extração de `api_stock.py` (TD-01 Phase 2,
11º domínio, 2026-08-07): não capturado pela matriz de dependências da Phase 1
(`docs/engineering/API_DEPENDENCY_MATRIX.md`), que listava só os 4 helpers efetivamente usados
(`_normalizar_tipo_estoque`, `_normalizar_qualidade_estoque`, `_recalcular_custo_medio`,
`_status_item_estoque`).

Impacto:
Baixo. Sem efeito em runtime — código morto (mesmo padrão de KI-014), só ruído de manutenção (~30
linhas). Não migrado para `api_stock.py` nesta extração, para não misturar refatoração estrutural com
limpeza de código (mesma regra já seguida para a dep morta `garantir_pasta_backup_google_drive` na
extração de Backup) — permanece em `fluxoly_blueprints_api.py`.

Status:
Resolvido em 2026-08-08 (TD-18 — TD-01 Phase 3, Cleanup). `fluxoly_blueprints_api.py` removido por
inteiro (continha só o `Blueprint("api")` vazio, sem nenhuma rota registrada, mais estes dois helpers
mortos) — confirmado por Discovery que nenhum código consumia `_slug_estoque`/`_gerar_sku_estoque`
(geração de SKU real vive só em `api_stock.py`, via `body.get("sku")`). Único consumidor do arquivo
(`app.register_blueprint(create_api_blueprint({}))` em `fluxoly_blueprint_registry.py`) removido junto.
`app.url_map` idêntico antes/depois (122 rotas), 683 testes passando, `ruff check .` limpo. Ver
`docs/operations/PROJECT_STATUS.md` (TD-18).

Sprint prevista:
Não definida — candidato a Phase 3 (Cleanup) da TD-01
(`docs/operations/SPRINTS/SPRINT_TD01_MODULARIZACAO_API.md`). Resolvido via TD-18 em 2026-08-08.

Responsável:
—

---

## KI-033

Descrição:
As 4 rotas do catálogo de Reparos (`GET/POST /reparos`, `PUT/DELETE /reparos/<id>`) não têm nenhum
teste dedicado — grep por `criar_reparo`/`atualizar_reparo`/`deletar_reparo`/`/api/reparos` em `tests/`
não retorna nada. Achado durante a Discovery de extração de `api_os.py` (TD-01 Phase 2, 12º e último
domínio, 2026-08-07): diferente do domínio OS propriamente dito (boa cobertura real — 8 módulos de
teste), essas 4 rotas nunca foram exercitadas por teste automatizado. Mesmo padrão de KI-031
(Relatórios).

Impacto:
Baixo a médio. Nenhum critério objetivo de `ENGINEERING_GUIDE.md` §11 é atendido (não é bug de
comportamento, é lacuna de cobertura). Mas significa que a suíte completa passar não é evidência de que
essas 4 rotas continuam funcionando após a extração — depende de verificação manual para ser detectada.

Status:
Aberto. Decisão do CTO (2026-08-07): não misturar escrita de testes novos com a extração final de
blueprint (escopo cirúrgico da TD-01) — a extração segue verbatim, validada por smoke test manual
(mesma técnica já usada em Relatórios/Sistema/MercadoPhone), e esta lacuna fica registrada aqui para
ser endereçada em sprint própria de cobertura de testes.

Sprint prevista:
Não definida — candidata a sprint de cobertura de testes, fora do escopo da TD-01 (mesmo destino de
KI-031).

Responsável:
—

---

## KI-034

Descrição:
`fluxoly_vendas_service.py::ajustar_desconto_item()` (BR-043 — Ajuste Comercial Autorizado, admin-only,
permite corrigir o preço de um item já vendido) recalcula e grava `vendas.valor_total` via
`repo.recalcular_valor_total_venda(cursor, venda_id)`, mas **nunca chama `fluxoly_caixa_service`** — os
únicos dois pontos de integração Vendas↔Caixa são `iniciar_venda()` e `cancelar_venda()`
(`fluxoly_vendas_service.py`, comentários "Financeiro Mínimo (BR-069)"). Achado durante a Revisão
Arquitetural do ciclo ADR-010 do Financeiro Mínimo (2026-08-10), ao rastrear todo ponto de escrita de
`vendas.valor_total` e cruzar com todo ponto de integração com `movimentacoes_caixa`.

Não é só uma divergência visual — é uma inconsistência real de dado entre `vendas.valor_total` e a
`movimentacoes_caixa` correspondente (`origem='venda'`, `origem_id=vendas.id`):

1. A movimentação de caixa é criada em `iniciar_venda()` com o `valor_unitario` da venda no momento da
   criação — um snapshot, nunca resincronizado.
2. Se um admin usa o Ajuste Comercial (BR-043) para corrigir o preço de uma venda já `concluida` (ex.:
   R$1.000 → R$800), `vendas.valor_total` passa a refletir R$800, mas a movimentação de caixa continua
   registrada com R$1.000 — o saldo do Caixa (`SOMA(entradas não estornadas) − SOMA(saídas não
   estornadas)`) fica sistematicamente R$200 maior do que deveria, sem qualquer erro ou aviso.
3. Se essa mesma venda for cancelada depois do ajuste, `cancelar_venda()` → `estornar_entrada_de_venda()`
   estorna a movimentação pelo valor original registrado nela (R$1.000), não pelo `valor_total` corrigido
   (R$800) — o estorno também carrega o valor desatualizado.

BR-043 já existia desde a V1.3 (Descontos e Aprovação, antes do Financeiro Mínimo) — este não é um
comportamento introduzido nesta sprint, é uma interação nova entre uma regra de negócio antiga
(permissão explícita de editar o preço de uma venda concluída) e uma feature nova (Caixa reagindo por
snapshot ao valor da venda no momento da criação).

Impacto:
Médio. Não atende C-03 (sem bypass de autorização) nem C-02 (nenhum dado é perdido, a movimentação
original continua íntegra no histórico), mas atende parcialmente C-01 (mutação indireta: o `valor_total`
da venda muda, mas o valor correspondente no Caixa não acompanha, e ninguém é avisado) em um caminho real
de produção (C-04 — Ajuste Comercial é uma rota ativa, usada por admin). O gatilho exige uma ação
deliberada e pouco frequente (Ajuste Comercial pós-venda), não o fluxo padrão de venda/cancelamento — por
isso não foi classificado como bloqueante para o encerramento do ciclo do Financeiro Mínimo.

Status:
Aberto. Decisão do CTO (2026-08-10, Revisão Arquitetural do ADR-010 do Financeiro Mínimo): não corrigir
nesta sprint — ampliaria o escopo justamente no encerramento do ciclo. Registrado aqui para correção em
sprint própria. A correção futura deve preservar a atomicidade já estabelecida pelo padrão do domínio:
atualizar `vendas.valor_total` e resincronizar/ajustar a `movimentacoes_caixa` correspondente na mesma
transação (mesmo cursor), nunca em dois commits separados — mesmo princípio já usado em
`iniciar_venda()`/`cancelar_venda()` com `unidades_service`/`caixa_service`.

Sprint prevista:
Não definida — candidata a sprint de correção do domínio Vendas/Financeiro, fora do escopo do
Encerramento do ADR-010 do Financeiro Mínimo.

Responsável:
—

---

## ~~KI-035~~ — RESOLVIDO

Descrição:
`migrations/runner.py::run_migrations()` tem uma condição de corrida real quando múltiplos workers
Gunicorn (`--workers 2`, `gunicorn.conf.py`) sobem simultaneamente contra um banco com uma ou mais
migrations pendentes. Cada worker lê `SELECT id FROM schema_migrations` (linhas 59-60) antes de qualquer
commit do outro, então os dois podem concluir que a mesma migration ainda não foi aplicada e tentar
inseri-la — o segundo `INSERT INTO schema_migrations (id) VALUES (?)` (linha 67) recebe
`sqlite3.IntegrityError: UNIQUE constraint failed: schema_migrations.id`. O `except
sqlite3.OperationalError` existente (linhas 71-76) só trata o caso "database is locked" —
`IntegrityError` não é subclasse de `OperationalError` (as duas são subclasses irmãs de
`sqlite3.DatabaseError`), então a exceção não é capturada e propaga, derrubando o boot do worker
(`Worker failed to boot`, exit code 3).

Achado em produção real (2026-08-10), durante deploy manual do commit `d7ef012` no Render — não é
hipótese de código, é evidência de log real: a primeira tentativa falhou com esse exato traceback
(`app.py` linha 484 → `run_migrations()` → `migrations/runner.py` linha 67), o Gunicorn encerrou o worker
com `Worker failed to boot`/exit code 3, e o Render manteve o deploy anterior ao vivo (comportamento
padrão da plataforma — deploy que falha não substitui o que está rodando). Contexto que tornou a corrida
mais provável que o normal: o deploy anterior ao vivo (`14ec238`, 3 de agosto) era anterior à TD-03 — o
banco de produção nunca tinha rodado `run_migrations()` antes, então havia mais de uma migration pendente
para aplicar de uma vez no mesmo boot (`m0001_baseline` + `m0002_financeiro_minimo`), ampliando a janela
da corrida. Uma segunda tentativa de deploy manual do mesmo commit teve sucesso — consistente com
condição de corrida intermitente, não um erro determinístico.

Impacto:
Alto em potencial, intermitente na prática. Pode derrubar o boot de um deploy sempre que houver mais de
uma migration pendente sendo aplicada no mesmo boot com múltiplos workers — cenário que se repete em
qualquer ambiente que fique atrasado (ex.: um futuro ambiente de demonstração/preview criado do zero, ou
qualquer rollback/roll-forward que precise aplicar migrations acumuladas). Relevante diretamente para a
política de Rollback (`docs/company/GO_LIVE_PLAN.md`/`DEPLOY.md`): a regra "rollback de código nunca
cruza uma migration já aplicada" pressupõe que a aplicação de migrations em si é confiável — este achado
mostra que o bootstrap de migrations pode falhar de forma não determinística quando há mais de uma
pendente, o que precisa ser considerado antes de qualquer Dry-Run de infraestrutura envolvendo Render.
Sem risco de dado incorreto — a migration que "perde" a corrida simplesmente não é registrada como
aplicada (o `INSERT` falha antes do `commit`), então uma nova tentativa de boot reaplica corretamente
(idempotência preservada); o risco é só de disponibilidade (worker/deploy não sobe), não de integridade.

Status:
Resolvido em 2026-08-11 (`docs/engineering/plans/PLAN-preview-seguro-inc003-ki035.md`, branch
`fix/preview-seguro-inc003-ki035`, commit `e202002`). `migrations/runner.py::run_migrations()` passa a
capturar `sqlite3.IntegrityError` por migration (não pela função inteira), tratando como no-op **só**
quando a mensagem confirma a constraint `schema_migrations.id` — qualquer outro `IntegrityError` (ex.:
violação de dado real dentro de uma migration) continua propagando, sem mascarar falha real (restrição
adicionada na revisão do CTO durante a aprovação do plano). Regressão confirmada: o teste dedicado
(`tests/test_migrations.py::TestProtecaoContraCorridaDeMigrations`) falha contra o código anterior e passa
depois da correção. QA Manual e Revisão Arquitetural do ciclo `ADR-010` concluídas em 2026-08-11.

Sprint prevista:
Preview Seguro (INC-003 Frente B) — concluída em 2026-08-11.

Responsável:
—

---

## ~~KI-036~~ — RESOLVIDO

Descrição:
`app.py`, inicialização do Sentry (linha 156): `environment="production" if IS_SERVER_RUNTIME else
"development"`. `IS_SERVER_RUNTIME` (`fluxoly_config.py`) é `True` tanto em produção quanto em qualquer
Render PR Preview — ambos setam `RENDER`/`RENDER_SERVICE_ID`. Não existe hoje nenhuma distinção entre os
dois no código (mesma lacuna de fundo do INC-003: nenhuma checagem de `IS_PULL_REQUEST` em lugar
nenhum). Achado durante a Discovery da arquitetura de "Preview seguro" (Operação Release 1.0, Parte B,
2026-08-11), ao inventariar toda credencial/config potencialmente herdada por um preview.

Impacto:
Médio (observabilidade, não dado/autorização). Qualquer erro real ocorrido dentro de um Render PR Preview
seria reportado ao Sentry marcado como `environment=production` — poluiria/mascararia o monitoramento de
erros de produção real com ruído de um ambiente de teste. Não exercitado ainda na prática (o preview do
INC-003 foi suspenso antes de gerar qualquer exceção capturada pelo Sentry), mas é uma lacuna real e
confirmada por leitura de código, não hipótese.

Status:
Resolvido em 2026-08-11 (`docs/engineering/plans/PLAN-preview-seguro-inc003-ki035.md`, branch
`fix/preview-seguro-inc003-ki035`, commit `e202002`). `environment` do Sentry passa a checar
`IS_PULL_REQUEST` antes de `IS_SERVER_RUNTIME`, reportando `"preview"` em vez de `"production"` quando é
um Render PR Preview. Confirmado por teste automatizado (`tests/test_ambiente_preview.py::
TestSentryEnvironmentPreview`) e por QA manual (log estruturado `sentry_inicializado` inspecionado num
boot real com `IS_PULL_REQUEST=true`).

Sprint prevista:
Preview Seguro (INC-003 Frente B) — concluída em 2026-08-11.

Responsável:
—

---

## ~~KI-037~~ — RESOLVIDO

Descrição:
A correção de "Preview seguro" (`docs/engineering/plans/PLAN-preview-seguro-inc003-ki035.md`, INC-003
Frente B) desliga a sincronização **automática** do MercadoPhone e o backup automático em qualquer preview
via `IS_PULL_REQUEST`, mas os endpoints **manuais/sob demanda** de `api_mercadophone.py`
(`POST /api/integracoes/mercadophone/sincronizar`, `/reprocessar`, `/reimportar`) continuavam sem qualquer
checagem de `IS_PULL_REQUEST` — protegidos só por sessão `admin`/`tecnico` (KI-022). Achado durante a
Revisão Arquitetural (eixo 3 — Risco de vazamento de dado, `ADR-010.md`) da correção acima, 2026-08-11.

Impacto:
Médio (residual, requer ação humana deliberada — não é automático como o INC-003 original). Se um Render
PR Preview for reativado no futuro e alguém autenticar com uma sessão `admin`/`tecnico` real (usuário
seedado ou herdado), chamar manualmente um desses 3 endpoints usaria o `MERCADO_PHONE_API_TOKEN` herdado
do serviço-base para uma chamada real à API externa do MercadoPhone — o guard de boot desta correção não
cobria esse caminho, só o disparo automático na inicialização do processo.

Status:
Resolvido em 2026-08-12, como parte da implementação do Ambiente de Demonstração/Homologação
(`ADR-012`, `docs/engineering/plans/PLAN-ambiente-demo-homologacao.md`). Nova função
`integracao_externa_bloqueada_neste_ambiente()` (`fluxoly_config.py`) — `return IS_PULL_REQUEST or
IS_DEMO_ENVIRONMENT` — aplicada nos 4 endpoints de escrita/ação de `api_mercadophone.py`
(`sincronizar`/`reprocessar`/`reimportar`/`config`, o último incluído por decisão do CTO na aprovação do
plano, para o Demo nunca armazenar uma credencial real que não pode usar), inserida depois das checagens
de permissão existentes, sem alterá-las. `status_mercadophone` (leitura) permanece intocado. 20 testes
novos (`tests/test_ambiente_demo.py`, `tests/test_ki037_guard_integracoes.py`), CI 6/6 verde (Linux),
QA manual em backend real e descartável confirmou os 4 endpoints retornando 403 em Preview e em Demo,
`/config` sem persistir o token bloqueado, e nenhuma regressão em produção/dev. Revisão Arquitetural
(4 eixos do `ADR-010`) rastreou todo call site de `chamar_api_mercado_phone()` e confirmou que os únicos
caminhos alcançáveis (os 3 endpoints manuais + a thread de sync via `BACKGROUND_JOBS_ENABLED` + o webhook,
já fail-secure por design quando `MERCADO_PHONE_WEBHOOK_TOKEN` está ausente, KI-023) estão todos cobertos.
Branch `feat/ambiente-demo-homologacao`, commits `59597bd8`/`a14db05e`.

Sprint prevista:
Ambiente de Demonstração/Homologação — concluído (código) em 2026-08-12. Reativar o preview suspenso
continua sendo decisão separada do CTO, fora deste escopo.

Responsável:
—

---

## ~~KI-039~~ — RESOLVIDO

Descrição:
A tela de edição de usuário (`frontend/src/pages/Users.jsx`) enviava o campo `senha` no `PUT
/api/usuarios/<id>` para trocar a senha de um usuário existente. O backend (`api_users.py::atualizar_usuario`)
lê `senha_nova` nesse endpoint — nome deliberadamente distinto de `senha` (usado só na criação, via `POST
/api/usuarios`), para diferenciar "sem alteração" de "nova senha" num formulário de edição. Como os nomes
não batiam, qualquer troca de senha pela tela de Usuários era silenciosamente ignorada: `nome`/`perfil`/
`ativo` eram salvos normalmente, a rota comitava e respondia sucesso, mas `senha_hash` nunca era tocado.
Achado em 2026-08-13, durante a Discovery do KI-038, ao tentar trocar a senha da conta `admin` de
produção como mitigação imediata da exposição da credencial hardcoded — a tela confirmou "Usuário
atualizado!", mas a senha antiga continuou sendo a única válida.

Impacto:
Alto (potencial). Qualquer admin que use a tela de Usuários para trocar a própria senha ou a de outra
conta — inclusive em resposta a um desligamento ou suspeita de vazamento de credencial — acredita que a
troca funcionou, sem nenhum erro visível, mas a senha antiga permanece ativa. Caminho real de produção
(critério C-04 de `ENGINEERING_GUIDE.md` §11), mesma categoria de risco do critério C-01 (dado que o
operador acredita ter mudado diverge do dado real, sem erro).

Status:
Resolvido em 2026-08-13 (`hotfix/usuarios-senha-nao-persiste`, PR #25, commit `ba2d6294`, merge
`ccf94baa`, branch a partir de `main`). Correção mínima e cirúrgica, um arquivo: no caminho de edição,
`handleSubmit` (`Users.jsx`) agora envia `senha_nova` (fluxo de criação, campo `senha`, inalterado).
`pytest tests/test_users.py` (22/22, backend não alterado, confirma nenhuma regressão), `npm run lint`/
`npm run build` limpos, CI 6/6 verde.

Sprint prevista:
Hotfix imediato — achado durante a Discovery do KI-038, corrigido antes de retomar o ciclo.

Responsável:
—

---

## ~~KI-038~~ — RESOLVIDO

Descrição:
`app.py::criar_admin_padrao()` rodava incondicionalmente na importação do módulo (fora de qualquer guard
de ambiente) e criava um usuário `admin`/`irflow@2024` (senha hardcoded no código-fonte) sempre que não
existia nenhum usuário `admin`. Achado durante o smoke test manual de `scripts/seed_demo.py`
(`docs/engineering/plans/PLAN-ambiente-demo-homologacao.md`, ADR-012), 2026-08-12, contra um banco
descartável. Discovery aprofundada em 2026-08-13 revelou que essa era, até então, a conta real de
produção do CTO — comportamento pré-existente desde a implementação original de autenticação, não uma
regressão.

Impacto:
Alto (potencial). Introduzia uma conta privilegiada com senha fixa e conhecida (visível no código-fonte)
em qualquer ambiente novo com banco vazio — inclusive um futuro Demo com acesso externo (prospects). A
senha de produção já foi trocada manualmente pelo CTO em 2026-08-13 como mitigação imediata (o que, por
sua vez, revelou o KI-039, já resolvido).

Status:
Resolvido em 2026-08-13 (`feat/ki-038-admin-senha-configuravel`, PR #26, commit `303c05c3`, branch a
partir de `main`). Decisão arquitetural do CTO: escopo amplo — `criar_admin_padrao()` reestruturada para
exigir `IR_FLOW_ADMIN_PASSWORD` fora de dev local (`IS_SERVER_RUNTIME`), mesmo padrão já usado para
`FLASK_SECRET_KEY` (`SECURITY_AUDIT_2026-07.md` item 3); ausente nesse caso, o boot falha com
`RuntimeError` propagado (checagem fora do `try/except` que protege só a inserção, para não ser engolida
como warning). Em dev local mantém o fallback `irflow@2024`, documentado em `.env.example`, sem quebrar
onboarding. Produção atual não é afetada — o admin já existe, a função é um no-op independente da
variável. 3 testes novos (`tests/test_ki038_admin_senha_configuravel.py`, mesmo padrão de subprocesso
isolado de `test_security_flask_secret_key_fallback.py`); `tests/conftest.py` e os demais testes que
importam `app` em subprocesso (`test_ambiente_preview.py`, `test_sentry_init.py`,
`test_security_flask_secret_key_fallback.py`) ganharam `IR_FLOW_ADMIN_PASSWORD` para não quebrar. Suíte
completa local: 751/754 (3 falhas pré-existentes de ambiente Windows, `sentry_sdk`/`_overlapped`,
confirmadas idênticas via `git stash` antes desta mudança — não é regressão). CI 6/6 verde.

**Achado registrado durante a Revisão Arquitetural, não um bug:** `scripts/seed_demo.py` importa `app.py`
(via `conectar()`), herdando o mesmo `criar_admin_padrao()` na importação. Quando o Demo for provisionado
com banco vazio pela primeira vez, `IR_FLOW_ADMIN_PASSWORD` vai precisar estar setada no Render **além**
de `DEMO_SEED_ADMIN_PASSWORD` (usada pelo `seed_demo.py` para as 3 contas de demonstração) — variáveis
distintas, para propósitos distintos. Pertence ao Runbook de Provisionamento do plano do Ambiente de Demo (`PLAN-ambiente-demo-homologacao.md`)
— já incorporado ao Runbook em 2026-08-14 (Discovery final de provisionamento) e confirmado funcionando
no primeiro boot real do serviço `fluxoly-demo`.

Sprint prevista:
Ciclo `ADR-010` completo (Discovery → decisão arquitetural → Plano Técnico → Implementação → Testes →
Revisão Arquitetural → Encerramento) — concluído em 2026-08-13.

Responsável:
—

---

## KI-040

Descrição:
`app.py::criar_admin_padrao()` faz `SELECT` para checar se `admin` já existe e só then `INSERT` se não
existir — sem lock nem `INSERT OR IGNORE`. O Gunicorn de produção/Demo roda com `--workers 2`
(`Dockerfile`), e cada worker importa `app.py` de forma independente no boot, cada um chamando
`criar_admin_padrao()`. Contra um banco vazio, os dois workers podem passar pelo `SELECT` antes de
qualquer um comitar o `INSERT`, e o segundo cai em `UNIQUE constraint failed: usuarios.usuario`. Achado
observado ao vivo no primeiro boot real do serviço `fluxoly-demo` (2026-08-14, log
`criar_admin_padrao_falhou`), mas a condição de corrida em si é pré-existente — mesmo formato de função
desde a implementação original de autenticação, nunca alterado por nenhuma correção do KI-038.

Impacto:
Baixo, comportamento observado até agora. O worker perdedor só loga um `warning` e segue (`except
Exception` já existente, não derruba o boot); o worker vencedor cria a conta corretamente, com a mesma
senha que o outro teria usado (ambos leem a mesma `IR_FLOW_ADMIN_PASSWORD`) — não há dado inconsistente
resultante. Não atende nenhum critério objetivo de interrupção do `ENGINEERING_GUIDE.md` §11 (não é C-01,
o dado final está correto; é C-04, caminho real de boot, mas isso sozinho não basta). Ruído de log em todo
primeiro boot com banco vazio (produção já passou por isso há muito tempo, sem ninguém notar; agora visível
de novo no Demo).

Status:
Aberto — sem decisão do CTO ainda. Correção candidata: `INSERT OR IGNORE INTO usuarios (...)` seguido de
checagem via `changes()`/`rowcount`, eliminando a janela de corrida entre `SELECT` e `INSERT` sem exigir
lock explícito.

Sprint prevista:
Não definida — candidata a limpeza futura, sem urgência.

Responsável:
—

---

## KI-041

Descrição:
`scripts/seed_demo.py` não popula nenhum registro em Tipos de Garantia durante o provisionamento do
Ambiente Demo. Achado durante a Homologação Interna Controlada (2026-08-15, ver
`docs/engineering/plans/ROTEIRO-homologacao-interna-controlada.md`) ao executar os fluxos de Finalizar OS
(perfil `tecnico.demo`) e Registrar Venda (perfil `vendedor.demo`): ambos exigem selecionar um Tipo de
Garantia (`Selecione o Tipo de Garantia *`), e o dropdown estava vazio — "Nenhum Tipo de Garantia
cadastrado — crie um em Tipos de Garantia antes de concluir/vender." Reproduzido de forma determinística
após restore do backup `seed-inicial` (o Tipo de Garantia criado manualmente durante a execução some,
confirmando que o gap está no seed, não em dado transitório).

Impacto:
Alto para o propósito do Ambiente Demo, mas não é bug de lógica de negócio — a validação de
`Tipo de Garantia *` obrigatório está correta e funcionando (`api_os.py`, `fluxoly_vendas_controller.py`).
Sem esse dado, **nenhum perfil** consegue finalizar uma OS ou registrar uma venda no Demo, os dois fluxos
centrais do sistema. Não atende nenhum critério objetivo de interrupção do `ENGINEERING_GUIDE.md` §11 (não
é C-01/C-02/C-03; é C-04 sozinho, que não basta) — por isso não virou hotfix imediato durante a execução,
mas bloqueia a homologação em si.

Status:
**Resolvido em 2026-08-15** (PR #38, `fix/seed-demo-tipo-garantia`, mergeada, CI 6/6 verde). Escopo: dado
de seed, não lógica de negócio (não precisou do ciclo completo `ADR-010`).

**Evidência de resolução — reexecução no Demo real (2026-08-15), não só localmente:**
- Deploy automático do `fluxoly-demo` confirmado live para o commit `5a1bbdb` (auto-deploy do `main`).
- Banco do Demo esvaziado (`database.db` renomeado, não apagado) e serviço reiniciado — boot confirmado
  contra schema vazio (a mensagem `criar_admin_padrao_falhou`/`UNIQUE constraint` nesse boot é o KI-040 já
  conhecido, condição de corrida entre os 2 workers do Gunicorn — não confundir com falha deste KI).
- `scripts/seed_demo.py` executado via Web Shell do Render: saída confirmou `Tipos de Garantia: 1
  (Garantia Padrão, 3 meses)`, junto dos demais volumes (18 clientes, 10 produtos/unidades, 24 OS, 8
  vendas).
- Novo backup `seed-inicial` criado (`backup-vseed-inicial-20260815-172644.db`) a partir desse estado.
- **Finalizar OS** reexecutado como `tecnico.demo` na OS #12 real do Demo → "Ordem finalizada!" (12→13
  finalizadas).
- **Registrar Venda** reexecutado como `vendedor.demo` (cliente `Ana Beatriz Ferreira`, iPhone 14, Pix,
  R$ 4.300,00) → "Venda concluída!", confirmada em Vendas > Histórico (Venda #9, status Concluída).
- Demo restaurado ao backup `seed-inicial` recém-criado após a reexecução — 18 clientes confirmados, estado
  limpo, dados de teste removidos.
- Produção confirmada saudável (`https://irflow-backend.onrender.com/health` → `{"status":"ok"}`) durante
  toda a operação — nunca tocada.
- Achado incidental durante a reexecução: Dashboard ("Faturamento") continua sem refletir a venda de
  produto registrada — mesmo comportamento já registrado no KI-042, não é regressão nova.

**Discovery — decidido (CTO, 2026-08-15):**
1 Tipo de Garantia sintético: **"Garantia Padrão", 90 dias (3 meses)**. Suficiente para exercitar os fluxos
principais — não é objetivo do seed simular o catálogo comercial completo de uma assistência. Variedade
adicional fica para uma frente futura, só se uma demonstração mais rica exigir.

**Plano Técnico — aprovado (CTO, 2026-08-15), aguardando implementação:**
- Arquivo: `scripts/seed_demo.py` (único arquivo alterado).
- Nova função `seed_tipos_garantia(cursor)`, seguindo o mesmo padrão direto de `seed_usuarios`/
  `seed_clientes` (sem checagem de duplicata — `_garantir_banco_vazio(cursor)` já garante banco limpo no
  início do `main()`, então uma única execução do seed nunca encontra dado pré-existente):
  ```python
  import fluxoly_tipos_garantia_repository as tipos_garantia_repo
  # ...
  def seed_tipos_garantia(cursor):
      return tipos_garantia_repo.inserir(cursor, "Garantia Padrão", 3)  # duracao_meses
  ```
- Chamar `seed_tipos_garantia(cursor)` em `main()`, mesmo bloco `try` dos demais `seed_*`, antes de
  `seed_os`/`seed_vendas` (nenhuma dependência de ordem com as demais chamadas, mas fica junto das outras
  entidades de cadastro).
- Testar localmente contra banco descartável (`IR_FLOW_DATA_DIR` isolado, nunca `database.db`): rodar o
  script, confirmar 1 linha em `tipos_garantia`, depois validar manualmente (ou via teste automatizado, se
  existir suíte para `seed_demo.py`) que Finalizar OS e Registrar Venda completam sem o erro "Nenhum Tipo de
  Garantia cadastrado".
- Branch: `fix/seed-demo-tipo-garantia` (a partir de `main`, escopo isolado — só o seed, sem misturar com o
  KI-042).
- Após aprovação final do PR e merge em `main`: gerar novo backup `seed-inicial` no Demo (rodar o script
  corrigido contra o Demo, criar backup via `POST /api/backup/criar` ou pela tela de Backups, mesmo
  procedimento já documentado em `PLAN-ambiente-demo-homologacao.md`), depois reset do Demo com esse novo
  backup.
- Reexecução dos fluxos afetados (Finalizar OS, Registrar Venda, reflexo em Vendas > Histórico) via Claude
  in Chrome antes de qualquer nova decisão de homologação.

Sprint prevista:
Resolvido dentro do próprio ciclo de Homologação Interna Controlada, 2026-08-15.

Responsável:
—

---

## KI-042

Descrição:
Duas divergências de escopo por perfil encontradas durante a Homologação Interna Controlada (2026-08-15,
ver `docs/engineering/plans/ROTEIRO-homologacao-interna-controlada.md`), ambas com o mesmo padrão: o menu
do frontend expõe uma tela para um perfil que não deveria tê-la, mas o backend bloqueia corretamente
qualquer escrita — não há bypass de autorização confirmado, apenas inconsistência de UX/visão.

1. `vendedor.demo` vê e acessa **Kanban** e **Garantias** no menu, com dados reais e completos (leitura),
   contradizendo o que o `ADR-012` documentou como validado na mesma data ("vendedor.demo... sem
   Kanban/Garantias"). Escrita confirmada bloqueada: `PUT /ordens/<id>` e `PATCH /ordens/<id>/status`
   verificam `session.get("usuario_perfil") not in ("admin", "tecnico")` → 403 (`api_os.py:671,905`).
2. `tecnico.demo` acessa `/vendas` e vê o formulário completo "Nova Venda" (busca de cliente, aparelho),
   quando o menu já esconde esse item para o perfil. Escrita confirmada bloqueada:
   `POST /api/vendas` verifica `usuario_pode_vender()` (`admin`/`vendedor` apenas) → 403 "Permissão
   negada." (`fluxoly_vendas_controller.py:108-109`).

Também observado na mesma sessão, sem risco de segurança: o Dashboard ("Faturamento") não inclui receita
de Vendas de produto, só de OS/serviço — a venda de teste (#9, R$ 4.900,00) não refletiu no card
"Faturamento", mas apareceu corretamente em Vendas > Histórico.

Impacto:
Baixo/médio — nenhum bypass de autorização confirmado (backend protege as duas rotas de escrita
verificadas), mas a experiência do usuário é inconsistente: `/usuarios` e `/financeiro` mostram tela de
"acesso negado" explícita para perfis sem permissão, enquanto `/vendas` (para técnico) e Kanban/Garantias
(para vendedor) não seguem o mesmo padrão.

Status:
Aberto — não atende critério objetivo de interrupção do `ENGINEERING_GUIDE.md` §11 (nenhum C-01/C-02/C-03
confirmado). Registrado como frente de trabalho futura de consistência de autorização/UX entre perfis,
salvo decisão do CTO de alinhar estritamente ao `ADR-012` antes de retomar a homologação.

Sprint prevista:
Não definida — não bloqueia a correção do KI-041 nem a retomada da homologação.

Responsável:
—

---

## ~~KI-043~~ — DESTINOS EXTERNOS REMOVIDOS (2026-11-06); criptografia do backup local pendente (pós-release)

Descrição:
Nenhum backup do banco de dados é criptografado em nenhum ponto do fluxo. `criar_backup()`
(`fluxoly_storage.py`) faz uma cópia binária (`sqlite3.Connection.backup()`) do `database.db` sem
criptografia própria — o arquivo `.db` resultante contém todo o dado pessoal de `clientes` (nome,
telefone, e-mail, CPF/CNPJ) em texto puro, legível por qualquer processo com acesso ao arquivo. O mesmo
arquivo não-criptografado é copiado (`shutil.copy2`) para `IR_FLOW_GOOGLE_DRIVE_BACKUP_DIR` quando
configurado, e anexado a e-mail via SMTP (`enviar_backup_email`) quando `IR_FLOW_BACKUP_EMAIL_SENHA` está
configurado — nesse último caso, a única proteção em trânsito é o TLS do próprio SMTP, sem criptografia
adicional do anexo. Achado durante a Discovery de LGPD (2026-08-16, pesquisa somente-leitura, ver
`docs/product/research/DISCOVERY_LGPD.md`).

Impacto:
Alto em potencial (dado pessoal real exposto em múltiplos destinos sem proteção adicional — disco local,
possível pasta de Drive sincronizada, caixa de e-mail), mas sem exploração confirmada — é exposição por
ausência de controle, não uma vulnerabilidade explorável remotamente. Relevante diretamente para LGPD
(princípio de segurança/proteção do dado armazenado).

Status:
**Mitigado em 2026-08-17** (branch `feat/lgpd-compliance-fase1`, commit `025278f6`,
`docs/engineering/plans/PLAN-LGPD-Compliance.md`): destinos externos (Google Drive, e-mail) contidos —
`EXTERNAL_BACKUP_DESTINATIONS_ENABLED = False`, único ponto de verdade em `fluxoly_config.py`, testado
(6 testes) e validado em QA Manual contra servidor real com os dois destinos configurados. Backup local
não afetado. **Criptografia de backup em repouso permanece pendente** — decisão de escopo/gestão de
chave/rotação/recuperação, pós-release.

**Atualização (2026-11-06, branch `feat/remover-backup-externo`):** por decisão do CTO, os dois destinos
externos foram **removidos do código** (não só contidos): saem `enviar_backup_email`, as funções de
Google Drive em `fluxoly_storage.py`, as variáveis `IR_FLOW_GOOGLE_DRIVE_BACKUP_DIR`/`IR_FLOW_BACKUP_EMAIL*`
e a própria contenção `EXTERNAL_BACKUP_DESTINATIONS_ENABLED`, que perdeu o objeto. O backup fica só no
disco local (`<IR_FLOW_DATA_DIR>/backups`). `tests/test_backup_contencao_externa.py` substituído por
`tests/test_backup_somente_local.py`. **Risco remanescente:** o backup local continua sem criptografia
em repouso — a parte "pendente" deste KI segue aberta.

Sprint prevista:
Não definida — candidato a entrar no escopo de qualquer sprint de implementação de medidas de LGPD.

Responsável:
—

---

## ~~KI-044~~ — RESOLVIDO

Descrição:
A "exclusão" de cliente (`DELETE /api/clientes/<id>`, `fluxoly_clientes_service.py::excluir_cliente`) tem
duas limitações relevantes para direito de apagamento/anonimização (tema típico de LGPD): (1) é
**bloqueada** com 409 sempre que o cliente tem qualquer OS vinculada (`possui_os_vinculada`) — não existe
caminho de anonimização alternativo, então nenhum cliente com histórico real de atendimento pode ser
removido, hoje ou no futuro; (2) mesmo quando a exclusão ocorre (cliente órfão, sem OS), o snapshot
completo do registro (nome, telefone, e-mail, CPF/CNPJ) é gravado em `audit_log.valor_anterior` como JSON
em texto puro — o dado sobrevive indefinidamente na tabela de auditoria, que também não tem nenhuma
política de retenção. Achado durante a Discovery de LGPD (2026-08-16, ver
`docs/product/research/DISCOVERY_LGPD.md`).

Impacto:
Médio/Alto para fins de compliance — não é um bug de comportamento (o bloqueio de exclusão com histórico
vinculado é uma decisão de integridade referencial razoável, e o log de auditoria existe por design), mas
significa que hoje **não existe nenhum mecanismo real de apagamento ou anonimização de dado pessoal** no
sistema, o que pode ser um requisito direto dependendo do que a Discovery de LGPD concluir ser necessário
para o primeiro cliente.

Status:
**Resolvido em 2026-08-17** (branch `feat/lgpd-compliance-fase1`, commit `02efbb9a`,
`docs/engineering/plans/PLAN-LGPD-Compliance.md`): novo `POST /api/clientes/<id>/anonimizar` (admin-only)
mascara PII preservando `id`/FK de OS/vendas; complementa, não substitui, o `DELETE` (que continua só
para órfãos, decisão explícita do CTO). `audit_log` registra a ação (`acao='anonymize'`). 5 testes novos,
validado em QA Manual contra servidor real (preservação de FK, bloqueio para perfil não-admin,
mascaramento confirmado no banco). Mecanismo de retenção do `audit_log` (mascaramento/expurgo
parametrizável, prazo real pendente) tratado junto, ver `fluxoly_audit.py`.

Sprint prevista:
Não definida — candidato a entrar no escopo de qualquer sprint de implementação de medidas de LGPD.

Responsável:
—

---

## ~~KI-045~~ — RESOLVIDO

Descrição:
`GET/POST/PUT /api/clientes` (`fluxoly_clientes_controller.py`) exigem só `usuario_logado()` — qualquer
perfil autenticado (`admin`/`tecnico`/`vendedor`/`estoque`) pode ler e escrever o dado pessoal completo de
qualquer cliente (nome, telefone, e-mail, CPF/CNPJ), sem segregação por perfil. `GET /api/garantias`
(`api_garantias.py`) tem o mesmo padrão — qualquer perfil vê nome de cliente + IMEI agregados. É mais
amplo que o padrão já aplicado a outras entidades sensíveis do sistema (Financeiro e Usuários restritos a
`admin`/perfis específicos). Achado durante a Discovery de LGPD (2026-08-16, ver
`docs/product/research/DISCOVERY_LGPD.md`).

Impacto:
Baixo/médio hoje (não é bypass de autorização — é o desenho atual, intencional ou não) — mas contradiz o
princípio de minimização de acesso frequentemente exigido por LGPD para dado pessoal, especialmente CPF.
Não há evidência de que isso tenha sido uma decisão deliberada de produto.

Status:
**Resolvido em 2026-08-17** (branch `feat/lgpd-compliance-fase1`, commit `02efbb9a`,
`docs/engineering/plans/PLAN-LGPD-Compliance.md`): leitura de `cpf_cnpj` restrita a `admin`/`financeiro`
em `GET /api/clientes`/`GET /api/clientes/<id>`; escrita permanece liberada a todo perfil (decisão
explícita do CTO). Edição por perfil restrito sem `cpf_cnpj` no payload preserva o valor existente em vez
de apagá-lo (sentinel `CPF_NAO_INFORMADO`). 9 testes novos, validado em QA Manual contra servidor real
com os 5 perfis. **Achado residual durante a Revisão Arquitetural, não bloqueante:** a busca
(`GET /api/clientes?q=`) casa contra `cpf_cnpj` antes deste filtro decidir a visibilidade — registrado
separadamente como **KI-046**, pós-release.

Sprint prevista:
Não definida — candidato a entrar no escopo de qualquer sprint de implementação de medidas de LGPD.

Responsável:
—

---

## KI-046

Descrição:
`GET /api/clientes?q=<termo>` (`fluxoly_clientes_repository.py::buscar_paginado`/`contar`) casa o termo de
busca contra `cpf_cnpj` (`WHERE ... OR lower(COALESCE(cpf_cnpj, '')) LIKE ?`) **antes** do filtro de
leitura do KI-045 ser aplicado no controller — a decisão de quais clientes entram no resultado já usa o
CPF completo, e só depois o campo é removido da resposta para quem não é admin/financeiro. Um perfil
restrito não recebe o valor, mas pode inferir por tentativa (`?q=123`, `?q=1234`, ...) se algum cliente
tem aquele prefixo/substring de CPF — um oráculo de correspondência, não o valor em si. Achado durante a
Revisão Arquitetural da Fase 1 de LGPD/Compliance (2026-08-17, eixo "risco de vazamento de dado" do
`ADR-010`), ao enumerar toda rota que devolve `cpf_cnpj` e confirmar que passam pelo único ponto de
filtragem — a busca é a única que decide *quais linhas retornam* usando o campo, sem passar por esse
ponto.

Impacto:
Baixo — exige tentativa deliberada e repetida (não é a UI normal fazendo isso), produz só um sinal de
match/no-match por substring, não o valor. Não atende nenhum critério objetivo de interrupção do
`ENGINEERING_GUIDE.md` §11 (não é C-01/C-02/C-03; é uma nuance de C-04 que sozinha não basta). Não
bloqueia o Encerramento da Fase 1 do Plano Técnico de LGPD/Compliance — mesmo padrão de residual risk já
aceito para o KI-037 durante o ciclo de Preview Seguro.

Status:
Aberto — identificado em 2026-08-17. Correção candidata: excluir `cpf_cnpj` da cláusula de busca quando
`termo` parece um CPF/CNPJ (ou, mais simples, remover `cpf_cnpj` da busca por completo e depender só de
nome/telefone) — decisão de escopo pendente do CTO, não implementada nesta Revisão Arquitetural.

Sprint prevista:
Não definida — candidato a entrar no escopo de qualquer sprint futura de LGPD, não bloqueia o Encerramento
da Fase 1.

Responsável:
—

---

## KI-047

Descrição:
A grade de touch de `ChecklistDevice.jsx` (20 células, `frontend/src/pages/ChecklistDevice.jsx`) renderiza
cada célula como `<button type="button" data-cell-index={index} ...>` sem `aria-label` nem qualquer texto
acessível — um leitor de tela anuncia "botão" 20 vezes, sem indicar posição na grade nem estado
tocado/não-tocado. Comportamento pré-existente, confirmado idêntico antes e depois do PR 2 da Fase 2 do
Design System (`docs/engineering/plans/PLAN-design-system-fase2.md`) — o diff dessa mudança tocou só
`className` (cor/token), nunca os atributos do elemento; achado durante a Revisão Arquitetural desse PR,
não introduzido por ele.

Impacto:
Baixo/Médio — `ChecklistDevice.jsx` é a única tela pública do sistema (sem login, acessada via link de
checklist), potencialmente usada por cliente final da loja em qualquer dispositivo/tecnologia assistiva.
Não impede o uso por mouse/toque; afeta apenas navegação por leitor de tela.

Status:
Aberto — identificado em 2026-08-19. Correção candidata: `aria-label={`Célula ${index + 1} de 20 —
${touched ? "tocada" : "não tocada"}`}` em cada célula. Não corrigido nesta Revisão Arquitetural por estar
fora do escopo puramente visual do PR 2 (regra da Fase 2: achado fora do escopo é registrado, não
corrigido automaticamente).

Sprint prevista:
Não definida — candidato a qualquer sprint futura de acessibilidade ou à próxima vez que
`ChecklistDevice.jsx` for tocado.

Responsável:
—

---

## ~~KI-048~~ — RESOLVIDO

Descrição:
`NewOrder.jsx`, `EditOrder.jsx`, `Kanban.jsx`, `Stock.jsx::fetchItems`, `Vendas.jsx::NovaVenda` (3 pontos —
`tiposGarantiaApi`/`clientesApi`/`unidadesApi`), `VendaDetalhe.jsx` (`tiposGarantiaApi`),
`Clientes.jsx::PerfilCliente` (`Promise.all`) e `Financeiro.jsx` (busca de saldo do componente pai, ver
correção abaixo) (`frontend/src/pages/`) buscam dados iniciais via `Promise.all([...]).then(...)` ou
`<api>.list()/.saldo().then(...)`, sem nenhum `.catch()`. Se a chamada rejeitar (erro de rede, não apenas
`{ok: false}` — que já é tratado), a `Promise` nunca chega ao `.then()`, `setLoading(false)` nunca é
chamado, e a tela fica presa no spinner de carregamento indefinidamente, sem nenhum aviso ao usuário.
Achado durante a Revisão Arquitetural do PR 3 da Fase 2 do Design System
(`docs/engineering/plans/PLAN-design-system-fase2.md`), estendido no PR 4 (`Stock.jsx`) e no PR 5 (`Vendas.jsx`,
`VendaDetalhe.jsx`, `Clientes.jsx`) — confirmado pré-existente em todos os pontos (os PRs 3/4/5 só trocaram
classes/ícones/estrutura visual, nunca tocaram a cadeia de promises). **Correção de escopo (2026-08-26,
Fase 3.3, Fatia 3.3.4):** a auditoria do PR 5 que deu `Financeiro.jsx` como "limpo" checou só os
`buscar()` de `Movimentacoes`/`ContasTab` — não viu que o componente pai (`Financeiro`) tem sua própria
busca de saldo (`caixaApi.saldo()`), também sem `try/catch`. Ficou mais visível ao promover o saldo a
métrica dominante (`Panel`) nesta mesma fatia.

Impacto:
Baixo/Médio — exige falha de rede real (não `{ok: false}` do backend, que já tem tratamento), mas afeta
telas de uso frequente (criar/editar OS, Kanban, Estoque, Nova Venda, Detalhe de Venda, Perfil de Cliente).
Sem crash, sem perda de dado — só a UX de "tela travada sem explicação".

Status:
**Resolvido em 2026-08-26.** Identificado em 2026-08-19 (PR 3), estendido em 2026-08-20 (PR 4 e PR 5).
**`Kanban.jsx` (Fatia 3.3.1), `Vendas.jsx::NovaVenda` (Fatia 3.3.2), `Stock.jsx::fetchItems` (Fatia
3.3.3), `Financeiro.jsx` — busca de saldo (Fatia 3.3.4) — e `Clientes.jsx::PerfilCliente` (Fatia 3.3.5)
resolvidos em 2026-08-26** (Fase 3.3 — `PLAN-design-system-fase3.3-operacao.md`), mesmo padrão já usado
em `Orders.jsx::fetchOrdens`/`fetchReposicao`. No caso de `Clientes.jsx::PerfilCliente`, o `.finally()`
já existente já garantia que `setLoading(false)` rodasse mesmo em rejeição — o gap real ali era só a
rejection não tratada (ruído no console), não tela presa; `.catch()` adicionado por consistência.
**`NewOrder.jsx`/`EditOrder.jsx` resolvidos em 2026-08-26** (Fase 3.4, Fatia 3.4.1 —
`PLAN-design-system-fase3.4-formularios.md`, Task 1), mesmo padrão. Em `EditOrder.jsx` o `.catch()`
também navega para `/ordens` (não só `toast.error`+`setLoading(false)`): diferente das outras telas do
KI, `form` começa em `null` e só é populado no branch de sucesso do `.then()` — sem navegar para longe,
o restante do componente tentaria renderizar `form.cliente` contra `null` e quebraria. Também foi
adicionada uma guarda defensiva (`if (loading || !form)`) para cobrir a janela entre o `catch` chamar
`setLoading(false)`/`navigate` e o React efetivamente desmontar o componente na troca de rota — sem ela,
esse frame intermediário quebra (reproduzido durante o teste desta correção). **`VendaDetalhe.jsx`
resolvido em 2026-08-26** (Fase 3.4, Fatia 3.4.2 — `PLAN-design-system-fase3.4-formularios.md`, Task 2),
3º e último ponto do KI: `tiposGarantiaApi.list().then()` (sem `.finally()` associado) ganhou `.catch(()
=> toast.error("Erro ao carregar tipos de garantia"))`, mesma mensagem já usada no ponto equivalente de
`Vendas.jsx::NovaVenda` (Fatia 3.3.2). 1 teste novo (rejeição da busca de tipos de garantia dispara
`toast.error` sem travar a tela). Todos os pontos originais do KI (8 arquivos) estão corrigidos.
Fora de escopo: `EditOrder.jsx` (`checklistApi.getByOrder(id).then(...)`) e `precosApi.sugerir(...).then(...)`
em `NewOrder.jsx`/`EditOrder.jsx` continuam sem `.catch()`, mas nenhum dos três segura spinner nem bloqueia
render (o Impacto deste KI é especificamente "tela travada sem explicação") — exclusão deliberada, não
descuido.

Sprint prevista:
Fase 3.3 (Kanban/Stock/Vendas/Financeiro/Clientes) — concluída em 2026-08-26. Fase 3.4 (NewOrder/EditOrder
— Fatia 3.4.1 — e VendaDetalhe — Fatia 3.4.2 — concluídas em 2026-08-26).

Responsável:
—

---

## ~~KI-049~~ — RESOLVIDO

Descrição:
`Clientes.jsx::fetchItems` (`frontend/src/pages/Clientes.jsx`) usa `try/catch` corretamente (não tem o
padrão do KI-048), mas não tem um estado de erro dedicado — no `catch`, só dispara `toast.error(...)`. Se a
chamada rejeitar, `items` permanece com o valor anterior (vazio, na carga inicial), e a tela renderiza o
`EmptyState` "Nenhum cliente cadastrado ainda." — indistinguível de uma lista genuinamente vazia. O toast
desaparece sozinho; se o usuário não estava olhando a tela nesse instante, não há como saber que a lista
vazia é resultado de uma falha, não do estado real dos dados.

Impacto:
Baixo — exige falha de rede real na carga inicial de Clientes, tela de uso frequente mas não crítica
(diferente de criar/editar OS). Sem crash, sem perda de dado — só ambiguidade de UX entre "vazio de
verdade" e "falhou ao carregar".

Status:
Resolvido em 2026-08-26 (Fase 3.3, Fatia 3.3.5 — `PLAN-design-system-fase3.3-operacao.md`). `fetchItems`
ganhou `loadError` dedicado + `ErrorState` com retry, mesmo padrão já usado em `Orders.jsx`/`Stock.jsx`. 2
testes novos ({ok:false} e rejeição de promise).

Sprint prevista:
Não definida — candidato a qualquer sprint futura que toque `Clientes.jsx` novamente, ou a uma correção
isolada de baixo risco (`fix:`, um arquivo).

Responsável:
—

---

## ~~KI-050~~ — RESOLVIDO

Descrição:
9 telas ainda usam classes Tailwind hardcoded calibradas só para Dark Mode, em vez dos tokens de tema
(`text-success`, `text-warning`, etc.) introduzidos na Fase 3.0 do Fluxoly Design System
(`docs/engineering/plans/PLAN-design-system-fase3.0-theme-infra.md`): `KpiCard.jsx` (10 ocorrências),
`Reports.jsx` (7), `Dashboard.jsx` (4), `OperationalCosts.jsx` (3), `Garantias.jsx` (3), `Vendas.jsx` (2),
`Users.jsx` (2), `VendaDetalhe.jsx` (1), `TiposGarantia.jsx` (1) — ex.: `text-emerald-300`,
`text-amber-400`. Achado na revisão final (whole-branch) da Fase 3.0, 2026-08-20 — só visível a partir de
uma visão cruzada de todas as 6 tasks da fase, não de nenhuma revisão isolada por task. Em Light Mode,
essas cores caem para contraste tão baixo quanto ~1,5:1 contra o fundo claro.

Impacto:
Mitigado por decisão do CTO (2026-08-20, revisão final da Fase 3.0) — o tema padrão para quem não tem
preferência salva continua Dark, idêntico a hoje (`frontend/src/contexts/ThemeContext.jsx`,
`readStoredTheme()`), então nenhum usuário é afetado até que ele mesmo escolha Light/Automático
explicitamente no toggle. Ainda assim é dívida real: quem escolher Light Mode manualmente vai ver essas 9
telas com contraste ruim.

Status:
**Resolvido em 2026-08-22** (Fase 3.1, `PLAN-design-system-fase3.1-foundation-v2.md`, Tasks 4-5) — as 9
telas migradas para os tokens de tema (`text-success`/`warning`/`destructive`/`info`). Exceção: o papel
"financeiro" em `Users.jsx` não tem token semântico de roxo equivalente na paleta Pulse — registrado
separadamente como KI-051 (não bloqueante). Escopo desta correção: exatamente os 9 arquivos listados
acima; `GlobalAlerts.jsx` tem 3 classes hardcoded adicionais nunca inventariadas no KI-050 original, fora
de escopo.

Sprint prevista:
Fase 3.1 (Foundation v2) — ver `docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md`
seção 12.

Responsável:
—

---

## KI-051

Descrição:
`Users.jsx` (`perfilColor`, papel "financeiro") usa `text-purple-400` (Tailwind cru) para diferenciar o
perfil de usuário "financeiro" na lista de usuários. Ao corrigir o KI-050 (Fase 3.1), os outros 3 papéis
(`tecnico`/`vendedor`/`estoque`) foram migrados para tokens de tema já existentes (`info`/`success`/
`warning`) — "financeiro" não tem equivalente: os 4 tokens semânticos da paleta Pulse (destructive/
success/warning/info) não incluem roxo, e criar um token novo não é escopo de uma correção de bug.

Impacto:
Mesmo impacto de contraste do KI-050 original (calibrado só para Dark Mode, ~baixo contraste em Light
Mode), mas isolado a 1 célula de 1 tela — a lista de usuários já é uma tela administrativa de baixo
tráfego (Tier 4, `PLAN-design-system-fase3-visual-experience.md` §9).

Status:
Aberto — decisão de produto pendente: adicionar um 5º token semântico à paleta (decisão de marca, CTO) ou
remover a diferenciação de cor por papel (mudança de composição, fora de escopo de correção de bug).

Sprint prevista:
Sem sprint — fica para quando a Fase 3.2+ tocar `Users.jsx` diretamente, ou decisão isolada do CTO.

Responsável:
—

---

## KI-052

Descrição:
`lib/chart-theme.js` (Fase 3.1) define `CHART_PALETTE` com 5 cores categóricas
(`--color-chart-1` a `--color-chart-5`). `ServicesChartCard.jsx` usa essa paleta tanto no
gráfico de pizza quanto na legenda (até 10 itens exibidos, `slice(0, 10)`) — a partir do 6º
serviço, a cor se repete (`chartColor()` cicla via módulo), então duas fatias/itens de legenda
podem ficar com a mesma cor. A implementação anterior a esta fase tinha um array `COLORS[]`
local com exatamente 10 cores, sem essa repetição.

Impacto:
Cosmético, não esconde dado — a legenda continua listando cada serviço pelo nome, só a cor do
indicador se repete. Visível em qualquer loja com 6+ tipos de serviço distintos no período
filtrado (cenário plausível, não extremo).

Status:
Aberto — identificado na revisão final (whole-branch) da Fase 3.1. Correção adequada exigiria
mudar a composição de `ServicesChartCard.jsx` (ex.: limitar a 5 fatias + agrupar o resto em
"Outros"), fora do escopo desta fase (só Foundation/tokens, sem mudança de composição de tela).

Sprint prevista:
Fase 3.2+ (Vitrine/Operação — quando `ServicesChartCard.jsx` for revisitado para composição).

Responsável:
—

---

## ~~KI-053~~ — RESOLVIDO

Descrição:
`components/ui/data-table.jsx` (Fase 3.1) — quando `onRowClick` é passado, a `<tr>` fica
focável (`tabIndex={0}`) e responde a clique e à tecla Enter, mas não à tecla Espaço (padrão
comum de ativação de linha/botão) nem expõe `role="button"` ou equivalente — o leitor de tela
anuncia a linha como `row` comum, não como algo ativável além do foco.

Impacto:
Nenhum hoje — `DataTable` ainda não é consumido por nenhuma página (Fase 3.1 só construiu o
componente). Mas como `DataTable` está destinado a substituir toda tabela HTML manual do app a
partir da Fase 3.2+, essa lacuna de acessibilidade se propagaria silenciosamente para cada tela
migrada se não for corrigida antes.

Status:
Resolvido em 2026-08-26 (Fase 3.3, Fatia 3.3.1 — `PLAN-design-system-fase3.3-operacao.md`),
corrigido antes de `OrderTable.jsx` se tornar o primeiro consumidor real do componente.
`onKeyDown` passa a tratar `e.key === " "` (com `preventDefault`, já que Espaço por padrão rola a
página) além de `Enter`; `role="button"` adicionado à `<tr>` quando `onRowClick` está presente
(ausente quando não há linha clicável, sem regressão do caso simples). 4 testes novos em
`data-table.test.jsx`.

Sprint prevista:
Antes ou durante a primeira migração de tela para `DataTable` — Fase 3.3, Fatia 3.3.1, 2026-08-26.

Responsável:
—

---

## ~~KI-054~~ — RESOLVIDO

Descrição:
`docs/company/BRAND_IDENTITY.md` §10.1 decidiu em 2026-08-20 (direção "Pulse") substituir o ícone da
marca pelo traço de batimento/ECG estilizado terminando numa seta ascendente, no lugar do monograma
abstrato da letra "F" da decisão anterior (2026-08-18). Nenhuma arte vetorial do ícone Pulse foi
produzida — os 5 arquivos reais em `frontend/public/brand/fluxoly-icon-*.svg`, aplicados em produção
(`Layout.jsx`, `Login.jsx`, componentes da Landing, `ChecklistDevice.jsx`), continuam sendo o monograma
"F" antigo. Adicionalmente, o SVG usa a cor antiga `#FF0125` hardcoded, não `#FF3D5A` (a cor de
assinatura Pulse já aplicada via tokens CSS desde a Fase 3.0/PR #59) — ou seja, o ícone diverge da marca
decidida tanto na forma quanto na cor.

Impacto:
Médio (marca/produto, não funcional). O ícone visível em toda tela autenticada, no login e na Landing
não corresponde à identidade visual decidida e documentada como vigente — inconsistência perceptível ao
lado do vermelho-sinal correto usado no resto da UI (botões, badges) via `--color-primary`.

Status:
Resolvido em 2026-08-24, mesma sessão do achado. O path SVG real do traço Pulse (nunca antes extraído
para um arquivo de produção) foi localizado no artifact de exploração "Fluxoly Identity Directions"
(Claude Design, direção B) lendo o conteúdo publicado do artifact e isolando o documento da direção
Pulse dentro do bundle — não uma reconstrução aproximada. Os 5 arquivos em `frontend/public/brand/
fluxoly-icon-*.svg` foram reescritos com esse path, mapeados às cores da tabela §10.1 do
`BRAND_IDENTITY.md` (`red`→`#FF3D5A`, `white`→`#FFFFFF`, `cyan`→`#29E0C9` novo, substituindo o arquivo
`black` que nunca fez parte das 5 variações documentadas, `gray`→`#5B6178`, `inverted`→ícone branco sobre
badge `#FF3D5A`). `favicon.svg` (cópia do padrão `inverted`) recebeu o mesmo tratamento. Lint (0 erros,
2 warnings pré-existentes não relacionados) e build de produção confirmados sem erro. QA visual real em
Chrome (`/login` e `/`, branch `feat/wordmark-space-grotesk`) confirmou o ícone renderizando como o
traço de pulso com seta ascendente, não mais o monograma "F".

Sprint prevista:
Fora de sprint — resolvido na mesma sessão do achado, a pedido do usuário (CTO).

Responsável:
—

---

## KI-055

Descrição:
`docs/company/BRAND_IDENTITY.md` §10.2 documentava a fonte Onest como "mantida" para UI/corpo de texto,
resultado de um comparativo entre ~15 fontes candidatas decidido em 2026-08-18. Essa decisão nunca foi
de fato aplicada: `body` em `frontend/src/index.css` sempre usou a pilha `system-ui` (nunca Onest); o
único ponto do código que carregava Onest era `.font-wordmark` (peso 700, usado só no logotipo
"Fluxoly"), não o corpo de texto. Com a troca do wordmark para Space Grotesk nesta mesma sessão
(KI-054/branch `feat/wordmark-space-grotesk`), Onest deixou de ter qualquer consumidor — `grep -rn
"Onest" frontend/src frontend/index.html` não retorna nenhum resultado.

Impacto:
Baixo/médio (marca/produto, não funcional). A fonte "decidida" para toda a UI do produto nunca esteve
de fato em uso — o corpo de texto sempre rodou na pilha padrão do sistema operacional, não na fonte da
identidade. Nenhum critério de `ENGINEERING_GUIDE.md` §11 é atendido (não muta dado, não é caminho de
produção com regra de negócio).

Status:
Decidido não aplicar por ora (2026-08-24). Três motivos: (1) escopo desproporcional — troca de fonte de
corpo afeta toda tela do produto, não os 3-5 pontos de uso do wordmark/ícone corrigidos em KI-054, e
exigiria carregar pesos extras (400/500/600) além do único peso 700 já usado; (2) a decisão de 2026-08-18
é anterior à reinvenção de marca da direção "Pulse" (2026-08-20), e `ENGINEERING_GUIDE.md` §3.2 registra
que tipografia não foi redecidida na formalização do Design System mesmo após a marca girar duas vezes —
sinal de que não é prioridade, não de esquecimento; (3) nenhuma queixa de UX registrada contra
`system-ui` no corpo de texto, diferente do ícone/wordmark, que o usuário identificou ativamente como
errados. `system-ui` permanece a fonte real do corpo de texto — `BRAND_IDENTITY.md` §10.2 atualizado para
refletir isso como decisão explícita, não pendência.

Sprint prevista:
Reabrir na Fase 3.2 (Vitrine) apenas se houver uma tela de referência concreta que justifique a troca —
não como substituição mecânica global.

Responsável:
—

---

## KI-056

Descrição:
`frontend/src/components/dashboard/KpiCard.jsx` ficou sem nenhum consumidor depois da Fase 3.2 (Vitrine) —
`Dashboard.jsx` (único lugar que o usava) migrou os 8 KPIs para `LooseMetric`/`Panel` da Foundation v2
(hierarquia real: 1 métrica dominante + 7 métricas soltas, ver
`docs/engineering/plans/PLAN-design-system-fase3.2-vitrine.md`, Task 3). Confirmado via
`grep -rn "KpiCard" frontend/src --include="*.jsx" --include="*.js" | grep -v "KpiCard.jsx\|KpiCard.test.jsx"`
→ nenhum resultado.

Impacto:
Nenhum em runtime — o componente simplesmente não é importado por ninguém, não afeta build nem
comportamento. É código morto (`KpiCard.jsx` + `KpiCard.test.jsx`), mesma categoria de dívida visível já
registrada para outros achados de "componente descontinuado sem remoção" neste projeto.

Status:
Aberto — não removido nesta fase por decisão deliberada (`CLAUDE.md`: nunca remover código sem confirmar).
Remoção é uma ação de baixo risco mas requer decisão explícita do CTO, já que `KpiCard` foi o padrão de
composição do Dashboard desde a Fase 1 e sua remoção também apagaria `KpiCard.test.jsx` (5 testes).

Sprint prevista:
Não definida — decisão do CTO: remover agora (branch `chore/remove-kpicard-orfao`, separado desta Fase
3.2 por não ser mudança visual) ou manter como legado sem uso até algum outro consumidor surgir.

Responsável:
—

---

## ~~KI-057~~ — RESOLVIDO

Descrição:
Teste intermitente no frontend: `Dashboard.test.jsx` › "clique em Filtrar dispara uma nova busca" falhou
no CI do PR #76 (`Unable to find an accessible element with the role "button" and name "Filtrar"`) e
passou na segunda execução sem mudança de código. O teste esperava só a primeira chamada à API
(`mockGet` chamado 1 vez) e já procurava o botão com `getByRole` — mas a chamada acontece antes de o
Dashboard sair do estado de carregamento e renderizar o botão, então às vezes o botão ainda não existia.

Impacto:
Baixo — só CI (falso vermelho em PR que nem toca o frontend). Nenhum efeito em produção.

Status:
Resolvido em 2026-11-08 (branch `fix/teste-dashboard-filtrar-intermitente`): o teste passa a esperar o
botão com `findByRole` antes de clicar.

Sprint prevista:
—

Responsável:
—

## ~~KI-058~~ — RESOLVIDO

Descrição:
No primeiro boot com a `m0003_compras_aparelhos` pendente (servidor próprio, 2026-11-09, deploy do PR #79),
os 2 workers do Gunicorn rodaram `run_migrations()` juntos. Os dois viram `os.unidade_serializada_id`
ausente na checagem `_coluna_existe`; um criou a coluna e o outro caiu no `ALTER TABLE` com
`sqlite3.OperationalError: duplicate column name: unidade_serializada_id` → `Worker failed to boot`. Mesma
família de KI-035 (corrida entre workers no bootstrap), mas na checagem de coluna dentro do `apply()`, não no
`INSERT` de `schema_migrations` — o DDL do `sqlite3` faz autocommit, então a checagem e o `ALTER` não são
atômicos entre processos.

Impacto:
Alto e intermitente — derrubou o boot do deploy. Sem dado incorreto: a coluna é criada uma vez só e a
migration, que é idempotente, é reaplicada no boot seguinte.

Status:
Resolvido em 2026-11-09 (branch `hotfix/migration-0003-corrida-workers`): na m0003, `duplicate column name`
no `ALTER` vira no-op (qualquer outro erro propaga). Testes em `tests/test_migrations.py`
(`TestM0003CorridaEntreWorkers`). Para migrations futuras com `ALTER TABLE ADD COLUMN`, seguir o mesmo
padrão; serializar o runner entre processos (lock) fica como melhoria, não feita neste hotfix mínimo.

Sprint prevista:
—

Responsável:
—

---

## ~~KI-059~~ — RESOLVIDO

Descrição:
Na OS, o campo "Valor com Desconto" (`os.valor_descontado`, rótulo em `NewOrder.jsx`/`EditOrder.jsx`) é o
preço final já com desconto, não o valor do desconto. Mas `fluxoly_core.py::calcular_faturamento_os`
devolve o Valor Cobrado sempre que ele é maior que zero, e só usa o Valor com Desconto quando o cobrado é
zero. Quando a OS tem os dois preenchidos, o desconto é ignorado no faturamento, no lucro, na coluna Valor
da listagem e, desde 2026-11-10, no valor impresso nos comprovantes de OS para o cliente (BR-095/BR-096).
Achado ao implementar os documentos da OS (`docs/engineering/plans/PLAN-documentos-os-cliente.md`).

Impacto:
Médio. Se a loja usa os dois campos (cobrado + com desconto), o cliente recebe um comprovante com o valor
sem desconto, e o faturamento/lucro aparecem maiores do que o valor de fato recebido. Não muta dado, mas
afeta número financeiro e documento entregue ao cliente.

Status:
Resolvido em 2026-11-10 (commit `969a5a2`). Decisão do CTO: quando o Valor com Desconto está preenchido, é
ele que vale; sem ele, vale o Valor Cobrado. Corrigido só em `calcular_faturamento_os` (fonte única), o
que acerta junto listagem, relatórios, lucro e os comprovantes para o cliente; a coluna Valor da
listagem (`OrderTable.jsx`) passou a usar o `faturamento` do backend em vez de repetir a regra.
Coberto por `tests/test_faturamento_os.py`. Números de faturamento/lucro de OS antigas com os dois campos
preenchidos mudam (para menor) em relatórios recalculados.

Sprint prevista:
Documentos da OS para o cliente (2026-11-10).

Responsável:
—
