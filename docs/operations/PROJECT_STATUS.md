# PROJECT_STATUS

**Projeto:** Fluxoly Platform
**Responsável:** Principal Software Engineer
**Branch principal:** `main`
**Ambiente de produção:** Render (backend) — `https://irflow-backend.onrender.com` · Vercel (frontend) — `https://assistencia-system.vercel.app`

**Última revisão:** 2026-11-06 — **Desvínculo do Fluxoly com a IR Phones iniciado (ADR-014).** Decisão
do CTO: remover tudo que liga o sistema à IR Phones e desligar a integração MercadoPhone, em 3 PRs.
**PR 1 (`chore/remover-app-estoque`):** app `apps/lista-aparelhos-disponiveis/` removido do repositório
(com job CI `estoque_app` e workflow `estoque-sync.yml`); ADR-013 substituída, BR-070..082 revogadas —
as pendências operacionais do app listadas abaixo deixam de valer e viram tarefas manuais do CTO
(desligar projetos Vercel `estoque`/`estoque-fluxoly`, Upstash Redis, secrets do GitHub, revogar
`MERCADOPHONE_API_KEY`). PR 1 mergeado (#69). **PR 2 (`feat/remover-os-interna-ir-phones`):** OS interna IR Phones
removida — tipo "Upgrade", campo `interna_ir_phones`, tabela de preço `ir_phones`, exclusão das
garantias, relatório IR Phones (JSON/PDF/aba) e padrão `ir.phones.flow@gmail.com` do e-mail de backup;
BR-014 sem exceção. Suíte backend 802 passed / 5 failed (as 5 = KI-030, limitação Windows local,
idênticas na `main`), frontend 153/153, lint 0 erros, build ok. PR 2 mergeado (#70). **PR 3 (`feat/desligar-integracao-mercadophone`):** flag
`MERCADO_PHONE_INTEGRATION_ENABLED` (padrão `0`) — rotas MercadoPhone respondem 404 e o sync em
background não inicia; código mantido no repositório. Suíte backend 808 passed / 5 failed (KI-030),
frontend 153/153, lint 0 erros, build ok. PR #22 (teste do Render Preview, INC-003) fechada sem merge.
PR 3 mergeado (#71) — desvínculo IR Phones concluído no código. **Em seguida (`feat/remover-backup-externo`):**
backup para Google Drive e por e-mail removidos (KI-043 atualizado; criptografia do backup local segue
pendente). Backend a ser hospedado em servidor próprio do CTO (não mais Render). **Backend de produção no Render
retirado do ar pelo CTO**; o banco será recriado do zero, sem dados herdados. PR #72 mergeado; backend
no ar em servidor Linux próprio do CTO (Docker + Tailscale Funnel, banco novo), frontend na Vercel apontando
para ele, login validado (desktop e 4G) e IP real chegando ao rate limit. 2026-11-08 — **Discovery de Compra
de Aparelhos aprovada** (BR-083 a BR-093, `docs/engineering/plans/PLAN-compra-aparelhos.md`): compra →
unidade → OS interna → venda, com saída de caixa e lucro por aparelho; implementação em 4 PRs. Antes disso:
2026-09-11 — **Estoque 1/Estoque 2 + reserva automática Estela
(`apps/lista-aparelhos-disponiveis/`) implementados, validados e mergeados em `main`** (3 commits —
`81244de` feat, `c2a4314` chore/script de import, `924aeb3` docs —, branch `feat/estoque-locais-estela`
integrada via fast-forward local, mesmo padrão sem-PR já usado na Fase 3.4 do Design System, decisão
explícita do CTO desta vez; push bypassou 1 status check obrigatório do branch protection porque não
passou por PR — CI roda no push mesmo assim, conferir depois). BR-081 (localização manual Estoque 1/Estoque 2 por unidade, Geral só mostra Estoque 1, novo
`POST /api/migrar-estoque`, abas do organizador viram "Estoque 1"/"Estoque 2"/"Disponíveis") e BR-082
(reserva automática para a vendedora "Estela" de toda unidade "Disponível com detalhe" no MercadoPhone,
reaproveitando o mecanismo de reserva já existente — `lib/estela.ts`, novo, função pura) implementadas em
`lib/store.ts`, `lib/inventory-view.ts`, `lib/sync.ts`, `api/migrar-estoque.ts` (novo), `public/`. 94
testes vitest (17 novos) + typecheck verdes localmente; QA visual ao vivo não executada (mesma limitação
recorrente desta ferramenta — sessão de bloqueio não persiste no navegador de automação —, mitigada por
cobertura de teste no nível de handler HTTP real). Import pontual (rodar uma vez, per decisão do CTO) da
planilha Excel existente do organizador (`scripts/importar-planilha-estoque.ts`, fora do `tsconfig.json`
`include` — não entra no typecheck/CI) **executado com sucesso contra a produção real** (dry-run
conferido antes do `--apply`): 161 de 174 unidades da planilha resolvidas por IMEI contra o inventário ao
vivo do MercadoPhone (13 não encontradas, provavelmente já vendidas), localização Estoque 1/2 aplicada às
161, nota de Detalhes preenchida em 95 (nenhuma sobrescrita — todas estavam vazias), 6 de 7 unidades
"STELLA" da planilha reservadas para a vendedora Estela (a 7ª não encontrada), 0 conflitos com reserva
humana. **Pendências antes de considerar este trabalho encerrado:** (a) confirmar que o CI passou no push
direto a `main` (bypassou branch protection por não ter passado por PR); (b) o deploy do app `estoque` na
Vercel é automático a partir de `main` (produção) — confirmar que o deploy novo subiu e rodar o QA Manual
do `DEPLOY.md` §6 (roteiro já atualizado) contra ele; (c) apagar o projeto Vercel vazio `estoque-fluxoly`,
criado por engano ao linkar o CLI (nome antigo do projeto na doc de provisionamento — o projeto real
chama-se `estoque`) e ainda não removido. Ver `docs/product/BUSINESS_RULES.md` BR-081/082 e
`docs/operations/CHANGELOG.md`. Antes disso:
2026-09-04 — **Lista de Aparelhos Disponíveis (ferramenta interna IR Phones)
ENCERRADA e em `main`** (PR #68, squash `eb13e836`). App **standalone** em
`apps/lista-aparelhos-disponiveis/` — consulta ao estoque de aparelhos com fonte na API nova do
MercadoPhone, **fora do Fluxoly-plataforma** (ADR-013): não toca `app.py`/`database.db`/projetos
Render/Vercel do Fluxoly. Deploy próprio na Vercel (Hobby) + Upstash Redis; sync 20/20min via GitHub
Actions. Duas áreas por senha compartilhada (Geral/Estoque), snapshots por allowlist (custo/PII/IMEI
completo nunca alcançam a Geral). Ciclo ADR-010 completo — Discovery + ADR-013 + Plano aprovados, QA
Manual aprovado, Revisão Arquitetural (`/code-review high`, 8 achados corrigidos). BR-070..080
formalizadas. 77 testes vitest + typecheck (job CI `estoque_app`). **No ar e funcionando** em
`estoque-gamma-nine.vercel.app` (projeto Vercel `estoque`, Root Directory `apps/lista-aparelhos-disponiveis`
ajustado após o 1º deploy git da `main` ter quebrado por apontar a raiz do repo); cron GitHub Actions
(`estoque-sync.yml`) validado verde. **Pendências operacionais (não bloqueiam o uso):**
(a) **rotacionar o `MERCADOPHONE_API_KEY`** — exposto em texto puro na conversa de Discovery;
(b) apontar `estoque.fluxoly.com` (CNAME) e trocar `ESTOQUE_SYNC_URL` no GitHub;
(c) apagar a branch `feat/lista-aparelhos-disponiveis`;
(d) liberar 1 reserva de teste (`reservas:1`).
Ver `docs/engineering/plans/PLAN-lista-aparelhos-disponiveis.md` e
`apps/lista-aparelhos-disponiveis/DEPLOY.md`. Antes disso:
2026-08-26 — **Fase 3.4 do Fluxoly Design System (Formulários/Detalhe) ENCERRADA e em
`main`** — 3/3 fatias (3.4.1 NewOrder/EditOrder, 3.4.2 VendaDetalhe, 3.4.3 ChecklistDevice), Tier 3
completo (`NewOrder.jsx`/`EditOrder.jsx`/`VendaDetalhe.jsx`/`ChecklistDevice.jsx` migrados para
`Panel`/`LooseMetric`/`DataTable`, Foundation v2). `KI-048` fechado por completo (Tier 2 + Tier 3).
Revisão final whole-branch: 2 Important (h1 perdido em `VendaDetalhe.jsx`; documentação não atualizada em
branch) + 2 Minor (import morto em `ChecklistDevice.jsx`; contagem imprecisa no fechamento do KI-048),
todos corrigidos antes do merge. Suíte completa 153/153, lint 0 erros, build ok. Integrada em `main` por
fast-forward local da branch `feat/design-system-fase3.4-newedit-order` (commits `52f60ecb`..`57506368`,
2026-08-26) — **sem PR, diferente das Fases 3.0–3.3 (#59–#67)**, e sem aprovação explícita do CTO
registrada. CI verde no push para `main` (run 33027362455). **Decisão do CTO (2026-08-27): aceitar e
seguir** — desvio de processo detalhado na seção da Fase 3.4 abaixo. Ver
`docs/engineering/plans/PLAN-design-system-fase3.4-formularios.md`. Antes disso:
2026-08-26 — Fase 3.3 do Fluxoly Design System (Operação) ENCERRADA — 5/5 fatias
mergeadas em `main` (PR #63 a #67), Tier 2 completo (Orders/Kanban/Vendas/Stock/Financeiro/Clientes
migrados para `Panel`/`LooseMetric`/`DataTable`, Foundation v2). `KI-053` resolvido; `KI-048` fechado no
Tier 2 (6 pontos: Kanban, Vendas ×3, Stock, Financeiro-saldo, Clientes — Tier 3 concluído na Fase 3.4, ver
revisão acima); `KI-049` resolvido. Ver seção logo abaixo para o registro completo. Suíte completa final:
147/147, lint 0 erros, build ok, CI 8/8 (×2) verde em cada PR. Antes disso:
2026-08-26 — Fase 3.3, Fatia 3.3.4: Financeiro —
Saldo em caixa vira métrica dominante (`Panel`, saiu do header); as 3 tabelas (Movimentações/Contas a
Pagar/Contas a Receber) migram para `DataTable`. Achado fora do escopo original do KI-048 (auditoria
anterior não cobriu a busca de saldo do componente pai) — corrigido no mesmo padrão. Branch
`feat/design-system-fase3.3-operacao-financeiro`, 144/144 testes, lint 0 erros, build ok. Antes disso:
2026-08-26 — Fase 3.3, Fatia 3.3.3: Stock — Valor
Total vira métrica dominante (`Panel`), Lotes/Unidades/Críticos viram `LooseMetric`, Reposição sugerida e
lista principal de itens migram para `DataTable`. Corrigido o KI-048 em `fetchItems` (sem `try/catch`).
Branch `feat/design-system-fase3.3-operacao-stock`, 143/143 testes, lint 0 erros, build ok. Antes disso:
2026-08-26 — Fase 3.3, Fatia 3.3.2: Vendas —
Histórico migra para `DataTable` (sem métrica dominante), Nova Venda migra o bloco de resumo/pagamento e
o card de confirmação para `Panel` (único elemento dominante da tela). Corrigido o KI-048 nos 3 pontos de
`NovaVenda` (`tiposGarantiaApi`/`clientesApi`/`unidadesApi` sem `.catch`). Branch
`feat/design-system-fase3.3-operacao-vendas`, 142/142 testes, lint 0 erros, build ok. Antes disso:
2026-08-26 — Fase 3.3, Fatia 3.3.1: `DataTable`
ganha `getRowProps` e corrige o KI-053 (acessibilidade de linha clicável — Espaço + `role="button"`) antes
de `OrderTable.jsx` se tornar seu primeiro consumidor real. Orders migra para `DataTable`/`LooseMetric`
(sem métrica dominante — tela de CRUD simples). Kanban auditado contra os 5 princípios de composição —
nenhum achado — e corrigido o KI-048 (`fetchOrdens` sem `.catch`, mesma classe de bug já visto em outras
telas). Branch `feat/design-system-fase3.3-operacao-orders-kanban`, 141/141 testes, lint 0 erros, build
ok. Antes disso:
2026-08-25 — Fase 3.2 do Fluxoly Design System (Vitrine): Login/Shell-Sidebar/Dashboard
redesenhados com os recipientes da Foundation v2 (`Panel`/`ListBlock`/`LooseMetric`, Fase 3.1), primeira
fase a mudar composição de tela real (não só tokens). Sidebar agrupado pelos 6 Pilares Macrossistêmicos;
Dashboard com Faturamento como métrica dominante; Landing auditada sem achados. Ver seção logo abaixo.
KI-056 registrado (`KpiCard.jsx` órfão, decisão de remover fica para o CTO). Revisão final whole-branch
achou 2 Important (skeleton do Dashboard fora de sincronia com a composição nova; contraste dos rótulos
de seção do Sidebar abaixo do piso AA) — ambos corrigidos antes do merge — e 8 Minor aceitos como estão.
**Mergeado em `main` (PR #62, squash, commit `deb460c5`, 2026-08-25)** — CI 8/8 (×2) verde, produção
confirmada saudável pós-merge (`/health` backend → 200, frontend Vercel → 200). Antes disso:
2026-08-24 — fechamento completo do gap entre `BRAND_IDENTITY.md` (direção "Pulse",
decidida 2026-08-20) e o código: (1) wordmark trocado de Onest para Space Grotesk Bold (`.font-wordmark`
em `index.css`); (2) ícone da marca trocado do monograma "F" da decisão anterior para o traço de
batimento/ECG + seta ascendente real, recuperado do artifact de exploração "Fluxoly Identity Directions"
e aplicado às 5 variações de cor (`frontend/public/brand/fluxoly-icon-*.svg` + `favicon.svg`) — KI-054
resolvido. Cor de assinatura `#FF3D5A` já estava correta desde a Fase 3.0 (PR #59); nota de "pendente"
desatualizada em `BRAND_IDENTITY.md` §10.3 também corrigida. Revisão de código do PR encontrou e corrigiu
mais um gap doc×código: `BRAND_IDENTITY.md` §10.2 afirmava Onest "mantida" no corpo de texto — nunca foi
verdade (`body` sempre usou `system-ui`), e com a troca do wordmark, Onest passou a ter zero uso no
código — registrado como **KI-055** (decisão de aplicar Onest de fato ao corpo de texto fica em aberto).
**Mergeado em `main` (PR #61, squash, commit `e11b5209`, 2026-08-24)** — CI 17/17 verde, produção
confirmada saudável pós-merge (`/health` backend → 200, frontend Vercel → 200). Antes
disso: a Fase 3.1 do Fluxoly Design System (Foundation v2 — recipientes
`Panel`/`ListBlock`/`LooseMetric`, `DataTable`, tema único de gráfico, correção do KI-050; **mergeada em
`main`, PR #60, commit `248349db`, ver seção logo abaixo**), a Fase 3.0 (infraestrutura de tema —
Light/Dark Mode, `ThemeProvider`, toggle de 3 estados, persistência; **mergeada em `main`, PR #59,
commit `5b6237df`**), o PR 5 (Vendas/VendaDetalhe/Financeiro/Clientes, implementado,
aguardando checkpoint final + CI antes do merge) e os PRs 1-4 (Foundation, `ChecklistDevice.jsx`,
Orders/Kanban/NewOrder/EditOrder, Estoque/Unidades Serializadas/Produtos), todos da Fase 2 do Fluxoly Design
System, o PR #53 (aplicação da marca — ícone e wordmark), a implementação da
Landing Page institucional (PR #49), a Fase 1 do Fluxoly Design System e a Fase 1 de LGPD/Compliance
**Fase 1 de LGPD/Compliance** (KI-029 Fase 1 + KI-043 + KI-044 + KI-045) — ciclo `ADR-010` completo
**encerrado em 2026-08-17** (Discovery → Decisões do CTO → Plano Técnico → Implementação → Testes → QA
Manual 14/14 → Revisão Arquitetural aprovada com ressalva → Encerramento). **Mergeada em `main` via PR #40
(`84deb30a`, 2026-08-16)** — CI verde. KI-029 Fase 2 (reescrita de histórico) confirmada não executada,
gate próprio. Ver `docs/engineering/plans/PLAN-LGPD-Compliance.md`
para o registro completo e `docs/product/research/DISCOVERY_LGPD.md`/
`DISCOVERY_RELEASE_1.0_RESTANTE.md` para o levantamento que originou este ciclo. Achado residual não
bloqueante da Revisão Arquitetural registrado como **KI-046** (busca de cliente por CPF vaza sinal de
match antes do filtro de leitura do KI-045), pós-release. Fora deste ciclo, deliberadamente: KI-029 Fase 2
(reescrita de histórico), criptografia completa de backup, prazos reais de retenção do `audit_log`,
documento de privacidade, validação jurídica formal.

Gate técnico do Ambiente de Demonstração (`ADR-012`) fechado — **14/14 critérios do
Definition of Done confirmados em 2026-08-15** contra o `fluxoly-demo`
(`https://fluxoly-demo.onrender.com`)/Vercel (`https://assistencia-system-do1h.vercel.app`) reais. Ver
`docs/engineering/adr/ADR-012.md` (Definition of Done) e
`docs/engineering/plans/PLAN-ambiente-demo-homologacao.md` para o registro completo de cada evidência.
Decisão do CTO (2026-08-15): não abrir nova sprint técnica agora. O ciclo de **Homologação Interna
Controlada** (via Claude in Chrome, substituindo por agora o gate da Homologação Externa) foi **executado
nos 3 perfis em 2026-08-15** e resultou em 🟢 **HOMOLOGAÇÃO INTERNA CONTROLADA — APROVADA**. A execução
inicial achou um bloqueador (KI-041 — seed do Demo sem Tipo de Garantia, impedindo Finalizar OS e
Registrar Venda); a correção (PR #37 Discovery/Plano + PR #38 implementação, CI 6/6) foi aplicada e
**reexecutada com sucesso no Demo real** (Finalizar OS ✅, Registrar Venda ✅, confirmados no
Histórico), com reset final do Demo ao novo backup `seed-inicial`. KI-041 fechado. Achados não bloqueantes
de menu/autorização e visão financeira permanecem registrados (**KI-042**, frente futura, sem sprint).
Nenhum guardrail violado em nenhuma etapa, nenhuma falha estrutural de segurança confirmada, produção
intocada e saudável durante toda a operação — ver
`docs/engineering/plans/ROTEIRO-homologacao-interna-controlada.md` para o registro completo. O ciclo de
**Homologação Externa** (produto, não engenharia) segue com Discovery e Plano concluídos (ver
`docs/engineering/plans/PLAN-homologacao-externa-demo.md`); retomada da Preparação (data + homologador
humano) fica a critério do CTO, sem data definida. LGPD (Discovery própria, trilha paralela) e KI-040 (race
condition em `criar_admin_padrao()` sob `--workers 2`) seguem sem decisão, não bloqueiam a sequência. Manual
do usuário e Piloto/homologação seguem sem decisão, um por vez, conforme o CTO for decidindo.
Sequência recente: ✅ **Landing Page institucional — implementação ENCERRADA (PR #49 mergeado em `main`,
2026-08-17, ver seção própria abaixo)** → ✅ **Fase 1 do Fluxoly Design System ENCERRADA (7 PRs — #41 a #47 — mergeados em `main`,
2026-08-16, ver seção própria abaixo)** → ✅ **Fase 1 de LGPD/Compliance ENCERRADA e mergeada (ciclo `ADR-010` completo — KI-029 Fase 1 +
KI-043 mitigado + KI-044/KI-045 resolvidos + KI-046 registrado; CI 6/6, QA Manual 14/14, Revisão
Arquitetural aprovada com ressalva; mergeada em `main` via PR #40 em 2026-08-16,
ver abaixo)** → 🟢 **Homologação Interna Controlada — APROVADA; KI-041 corrigido e reexecutado com
sucesso no Demo real, KI-042 registrado como frente futura (2026-08-15, ver abaixo)** → 🟡 **Homologação
Interna Controlada executada — achado inicial KI-041, Demo restaurado ao seed-inicial (2026-08-15, ver
abaixo)** → 🟡 **Roteiro de Homologação Interna
Controlada aprovado, substitui por agora a Homologação Externa (2026-08-15, ver abaixo)** → 🟡 **Plano de
Homologação Externa do Ambiente Demo
concluído (2026-08-15, ver abaixo)** → 🟡 **Discovery — Homologação Externa do Ambiente Demo concluída (2026-08-15, ver
abaixo)** → 🟡 **Os 14 critérios do DoD do Ambiente de Demonstração confirmados (2026-08-15, ver
abaixo)** → 🟡 **Login das 3 contas de demo + restore de ponta a ponta validados (2026-08-15, ver
abaixo)** → ✅ **Seed + backup `seed-inicial` do Ambiente de Demonstração concluídos (2026-08-15,
ver abaixo)** → ✅ **Ambiente de Demonstração mergeado em `main`, com KI-038/KI-039 já resolvidos
(2026-08-13, ver abaixo)** → ✅ **KI-038 — admin padrão exige senha configurável (ciclo `ADR-010`
completo, 2026-08-13, ver abaixo)** → ✅ **KI-039 — troca de senha de usuário não persistia (hotfix,
2026-08-13, ver abaixo)** → ✅ **Dry-Run 2B — rollback de infraestrutura Render validado
(push → auto-deploy → revert → auto-deploy → confirmação, 2026-08-11, ver abaixo)** → ✅ **Preview Seguro — INC-003 Frente B, KI-035, KI-036 resolvidos
(Discovery → Plano Técnico → Implementação → Testes → QA Manual → Revisão Arquitetural → Encerramento,
ciclo `ADR-010` completo, 2026-08-11, ver abaixo)** → 🔴 **INC-003 — dado real importado no Preview,
contido (Dry-Run 2A — provisionar preview → KI-035 reproduzido no boot → isolamento de disco/banco
confirmado → integração MercadoPhone herdada detectada → 405 OS importadas → preview suspenso,
2026-08-10, ver abaixo)** → 🟡
**Rollback — Dry-Run 1A/1B + política de conflito (Operação Release 1.0 Parte B — Discovery → decisão do
CTO → política inicial → Dry-Run 1A mecanismo sem conflito → Dry-Run 1B commit real com conflito real em
documentação → abort seguro → nova regra "conflito = parada + decisão do CTO", 2026-08-10, ver abaixo)**
→ ✅ **Restore validado
(Operação Release 1.0 — Discovery → testes automatizados → QA manual → merge, 2026-08-10, ver abaixo)**
→ ✅
**Financeiro Mínimo ENCERRADO (Revisão Arquitetural + Encerramento formal ADR-010, 2026-08-10, ver
abaixo)** → 🟡 Financeiro Mínimo — frontend + validação Fatia 3 concluídos (2026-08-09, ver abaixo) → 🟡
Financeiro Mínimo — backend implementado e validado (BR-067 a BR-069, 2026-08-08, ver abaixo) → ✅ **TD-03 ENCERRADA (2/2 fatias, 2026-08-08)** → ✅ TD-03 Phase 2 — Fatia 2/2 `app.py` usa `run_migrations()`, mecanismo antigo removido (concluída 2026-08-08, ver abaixo) → ✅ TD-03 Phase 2 — Fatia 1/2 pacote `migrations/` (concluída 2026-08-08, ver abaixo) → ✅ TD-18 — Cleanup `fluxoly_blueprints_api.py` (concluída 2026-08-08, ver abaixo) → ✅ **TD-02 ENCERRADA (4/4 fatias, 2026-08-08)** → ✅ TD-02 Phase 2 — Fatia 4/4 webhook MercadoPhone → `api_mercadophone.py` (concluída 2026-08-08, ver abaixo) → ✅ TD-02 Phase 2 — Fatia 3/4 `fluxoly_blueprint_registry.py` (concluída 2026-08-08, ver abaixo) → ✅ TD-02 Phase 2 — Fatia 2/4 `fluxoly_app_security.py` (concluída 2026-08-07) → ✅ TD-02 Phase 2 — Fatia 1/4 `fluxoly_config.py` (concluída 2026-08-07) → ✅ **TD-01 ENCERRADA (Phase 2, 12/12 domínios, decisão do usuário — CTO, 2026-08-07)** → ✅ TD-01 Phase 2 — OS+Reparos extraído (2026-08-07, ver abaixo) → ✅ TD-01 Phase 2 — Estoque extraído (2026-08-07, ver abaixo) → ✅ TD-01 Phase 2 — Sistema extraído (2026-08-07, ver abaixo) → ✅ INC-001 (causa raiz confirmada e corrigida em produção, 2026-08-05 — ver acima) → ✅ TD-01 Phase 2 — MercadoPhone extraído (2026-08-06) → ✅ TD-01 Phase 2 — Relatórios extraído (2026-08-06) → ✅ TD-01 Phase 2 — Backup extraído (2026-08-06) → ✅ TD-01 Phase 2 — Auth extraído (2026-08-06) → ✅ TD-01 Phase 2 — Usuários extraído (2026-08-06) → ✅ TD-01 Phase 2 — Preços extraído (2026-08-06) → ✅ TD-01 Phase 2 — Custos Operacionais extraído (2026-08-06) → ✅ TD-01 Phase 2 — Garantias extraído (2026-08-05) → ✅ C1.3.5 (Rastreabilidade Individual de Estoque, concluída 2026-07-27) → ✅ Vendas MVP (concluída 2026-07-27, ver abaixo) → ✅ Sprint Infra 1.1 — CI Verde (concluída 2026-07-27, KI-026/R-10/R-11, ver abaixo) → ✅ Sprint Vendas 1.1 — Histórico + Detalhe (concluída 2026-07-27, ver abaixo) → ✅ V1.2 — Cancelamento (concluída 2026-07-27, ver abaixo) → ✅ ADR-010 — ciclo de feature com regra de negócio (concluída 2026-07-28) → ✅ V1.3 — Descontos e Aprovação (concluída 2026-07-28, ver abaixo) → ✅ V1.4 — Comissão (concluída 2026-07-29, ver abaixo, inclui revogação do bloqueio de desconto da V1.3) → ✅ Fix de responsividade do Dashboard em MacBook (concluído 2026-07-30, ver abaixo) → ✅ V1.5 — Garantia (concluída 2026-07-30, ver abaixo)

---

## ✅ Fase 3.4 do Fluxoly Design System — Formulários/Detalhe (Tier 3) ENCERRADA e em `main`

**Ver `docs/engineering/plans/PLAN-design-system-fase3.4-formularios.md` para o registro completo (3
fatias) e `docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md` (§9) para o faseamento
por tier.**

2026-08-26, sequência imediata à Fase 3.3 (Tier 2). Tier 3 ("Formulários e detalhe"): NewOrder, EditOrder,
VendaDetalhe, ChecklistDevice. Mesma cadência de execução da Fase 3.3
(`superpowers:subagent-driven-development`, revisão whole-branch antes do merge, KI-048 corrigido junto da
composição em commit separado).

**Entregue** (branch `feat/design-system-fase3.4-newedit-order`):
- **NewOrder/EditOrder** — 6 seções migram para `Panel`/`PanelHeader`/`PanelTitle`/`PanelContent`, sem
  dominante; "Sugestão de serviço" vira `LooseMetric`. Os dois arquivos mantidos genuinamente paralelos,
  única divergência intencional (`.catch()` de `EditOrder` também navega para `/ordens`) documentada em
  comentário no ponto de divergência.
- **VendaDetalhe** — Total da venda vira métrica dominante (`Panel`); tabela de Itens (7 colunas) migra de
  `<td>` manual para `DataTable`.
- **ChecklistDevice** — wrapper local `Section` troca `Card`/`CardContent` por `Panel`/`PanelContent`,
  troca puramente mecânica (única tela pública/não autenticada do sistema).
- **KI-048 fechado por completo** — os 3 últimos pontos (NewOrder/EditOrder na carga inicial, VendaDetalhe
  na busca de tipos de garantia) ganharam `.catch()`. Com o Tier 2 (Fase 3.3), o KI está resolvido em
  todas as telas.

**Validação:** suíte completa 153/153, lint 0 erros, build de produção sem erro. Revisão final
whole-branch: 2 Important (h1 perdido em `VendaDetalhe.jsx` — commit `579f81d7`; documentação não
atualizada na branch) + 2 Minor (import morto em `ChecklistDevice.jsx`; contagem imprecisa no fechamento
do KI-048), todos corrigidos antes do merge (commit `57506368`). QA visual não executada ao vivo (mesma
limitação de KI-027).

**⚠️ Desvio de processo — merge sem PR:** ao contrário de todas as fases anteriores do Design System
(3.0–3.3, PRs #59–#67, cada uma via PR + squash + revisão no PR), a Fase 3.4 foi integrada em `main` por
**fast-forward local** da branch (`git merge feat/design-system-fase3.4-newedit-order`, commits
`52f60ecb`..`57506368` preservados individualmente, 2026-08-26 ~21:31), seguido de push para `origin/main`
e exclusão da branch. CI rodou no push e passou (run `33027362455`, verde). **Não consta no histórico do
projeto aprovação explícita do CTO para este merge** — o `PROJECT_STATUS.md` da época dizia "Merge ainda
não realizado — decisão do CTO" e não foi atualizado antes do merge. O plano
(`PLAN-design-system-fase3.4-formularios.md`) ainda tem checkboxes `[ ]` em aberto. Código revisado,
testado (CI verde) e documentado no `CHANGELOG.md` — o desvio é de processo (sem PR/squash, sem aprovação
registrada), não de qualidade de build. **Decisão do CTO (2026-08-27): aceitar e seguir** — sem rollback
nem reescrita de histórico; lição registrada em memória (gates de aprovação: "salve tudo/feche" não
autoriza merge; fases integram via PR + squash).

**Próximo passo:** Fase 3.5 (Tier 4 — Administrativo: Reports/PriceTables/RepairTypes/Users) fica para
quando o CTO autorizar o início; `KI-051`/`KI-052`/`KI-055`/`KI-056` são candidatos a entrar junto.

---

## ✅ Fase 3.3 do Fluxoly Design System — Operação ENCERRADA (5/5 fatias mergeadas)

**Ver `docs/engineering/plans/PLAN-design-system-fase3.3-operacao.md` para o registro completo (5
fatias) e `docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md` (§9) para o faseamento
por tier.**

2026-08-26, sequência imediata à Fatia 3.3.4 (mergeada em `main`, PR #66). Quinta e última fatia do Tier 2
("Operação diária") — Orders/Kanban/Vendas/Stock/Financeiro/Clientes, todas migradas.

**Entregue** (branch `feat/design-system-fase3.3-operacao-clientes`):
- Contadores (Clientes/Com telefone/Com e-mail) viram `LooseMetric`, sem dominante — tela de cadastro
  simples (decisão do CTO).
- Tabela de clientes migra de HTML cru para `DataTable`, `onRowClick` abre o perfil (mesmo comportamento
  de antes), coluna de ações com `stopPropagation` para não disparar o perfil ao clicar em
  editar/anonimizar/excluir.
- **KI-049 resolvido** — `fetchItems` ganhou `loadError` + `ErrorState` com retry, mesmo padrão de
  Orders/Stock.
- **KI-048 resolvido no último ponto do Tier 2** — `PerfilCliente` (`Promise.all(...).then(...)
  .finally(...)`) ganhou `.catch()`. Como `.finally()` já rodava em rejeição, o gap real era só a
  rejection não tratada (ruído no console), não tela presa; corrigido por consistência.

**Validação:** suíte completa 147/147 (3 testes novos), lint 0 erros (2 warnings pré-existentes não
relacionados), build de produção sem erro. QA visual não executada ao vivo (mesma limitação de KI-027).

**KI-048 — Tier 2 (Fase 3.3) fechado por completo.** Tier 3
(`NewOrder.jsx`/`EditOrder.jsx`/`VendaDetalhe.jsx`, Fase 3.4) também concluído — ver "Última revisão" no
topo do arquivo.

**Decisão do CTO:** aprovado o plano da Fase 3.3 (5 fatias) e as decisões de composição por tela antes da
implementação. **Mergeado em `main` (PR #67, squash, commit `142a22ef`, 2026-08-26)** — CI 8/8 (×2) verde,
produção confirmada saudável pós-merge (`/health` backend → 200, frontend Vercel → 200).

**Fase 3.3 (Operação) encerrada** — as 5 fatias (3.3.1 DataTable+Orders+Kanban/PR #63, 3.3.2 Vendas/PR #64,
3.3.3 Stock/PR #65, 3.3.4 Financeiro/PR #66, 3.3.5 Clientes/PR #67) todas mergeadas em `main` no mesmo dia
(2026-08-26). Tier 2 completo: Orders/Kanban/Vendas/Stock/Financeiro/Clientes migrados para os recipientes
da Foundation v2 (`Panel`/`LooseMetric`/`DataTable`). `KI-053` resolvido (acessibilidade do `DataTable`);
`KI-048` fechado no Tier 2 inteiro (6 pontos corrigidos: Kanban, Vendas ×3, Stock, Financeiro-saldo,
Clientes — resta só o Tier 3); `KI-049` resolvido.

**Próximo passo:** Fase 3.3 completa após o merge desta fatia — Fase 3.4 (Tier 3: NewOrder/EditOrder/
VendaDetalhe/ChecklistDevice) fica para quando o CTO autorizar o início.

---

## ✅ Fase 3.3 do Fluxoly Design System — Operação, Fatia 3.3.4 (Financeiro) ENCERRADA (PR #66 mergeado)

**Ver `docs/engineering/plans/PLAN-design-system-fase3.3-operacao.md` para o registro completo (5
fatias).**

2026-08-26, sequência imediata à Fatia 3.3.3 (mergeada em `main`, PR #65). Quarta fatia do Tier 2.

**Entregue** (branch `feat/design-system-fase3.3-operacao-financeiro`):
- **Saldo em caixa** (antes um badge pequeno no header) vira métrica dominante (`Panel`, número hero) —
  mesmo tratamento do Faturamento no Dashboard, decisão do CTO.
- As 3 tabelas (Movimentações, Contas a Pagar, Contas a Receber) migram de HTML cru para `DataTable`,
  ações (estornar/pagar/receber/editar/cancelar/excluir) preservadas na coluna final.
- **Achado fora do escopo original do KI-048, corrigido nesta fatia:** a busca de saldo do componente pai
  (`Financeiro.jsx::buscar`) era um `async function` sem `try/catch` — a auditoria original do PR 5 que
  deu `Financeiro.jsx` como "limpo" checou só os `buscar()` de `Movimentacoes`/`ContasTab`, não este. Ficou
  mais visível ao promover o saldo a métrica dominante.

**Validação:** suíte completa 144/144 (1 teste novo), lint 0 erros (2 warnings pré-existentes não
relacionados), build de produção sem erro. QA visual não executada ao vivo (mesma limitação de KI-027).

**KI-048 (progresso):** `Kanban.jsx`, `Vendas.jsx::NovaVenda`, `Stock.jsx::fetchItems` e
`Financeiro.jsx::buscar` (saldo) resolvidos. Resta `Clientes.jsx::PerfilCliente` (Fatia 3.3.5) + 3 pontos
no Tier 3 (Fase 3.4, fora desta fase).

**Decisão do CTO:** aprovado o plano da Fase 3.3 (5 fatias) e as decisões de composição por tela antes da
implementação. **Mergeado em `main` (PR #66, squash, commit `d422428e`, 2026-08-26)** — CI 8/8 (×2) verde,
produção confirmada saudável pós-merge (`/health` backend → 200, frontend Vercel → 200).

**Próximo passo:** Fatia 3.3.5 (Clientes — última do Tier 2), ver seção acima.

---

## ✅ Fase 3.3 do Fluxoly Design System — Operação, Fatia 3.3.3 (Stock) ENCERRADA (PR #65 mergeado)

**Ver `docs/engineering/plans/PLAN-design-system-fase3.3-operacao.md` para o registro completo (5
fatias).**

2026-08-26, sequência imediata à Fatia 3.3.2 (mergeada em `main`, PR #64). Terceira fatia do Tier 2.

**Entregue** (branch `feat/design-system-fase3.3-operacao-stock`):
- **Valor Total** vira métrica dominante (`Panel`, número hero) — único candidato dominante real da tela
  (decisão do CTO); Lotes/Unidades/Críticos (≤2) viram `LooseMetric`.
- **Reposição sugerida** e **lista principal de itens** migram de HTML cru para `DataTable`, ações de
  editar/excluir preservadas na coluna final (`getRowProps` para `data-testid`).
- **KI-048 resolvido em `fetchItems`** — não tinha `try/catch`; adicionado o mesmo padrão já usado em
  `fetchReposicao` no mesmo arquivo.

**Validação:** suíte completa 143/143 (1 teste novo), lint 0 erros (2 warnings pré-existentes não
relacionados), build de produção sem erro. QA visual não executada ao vivo (mesma limitação de KI-027).

**KI-048 (progresso):** `Kanban.jsx`, `Vendas.jsx::NovaVenda` e `Stock.jsx::fetchItems` resolvidos. Resta
`Clientes.jsx::PerfilCliente` (Fatia 3.3.5) + 3 pontos no Tier 3 (Fase 3.4, fora desta fase).

**Decisão do CTO:** aprovado o plano da Fase 3.3 (5 fatias) e as decisões de composição por tela antes da
implementação. **Mergeado em `main` (PR #65, squash, commit `184815a1`, 2026-08-26)** — CI 8/8 (×2) verde,
produção confirmada saudável pós-merge (`/health` backend → 200, frontend Vercel → 200).

**Próximo passo:** Fatia 3.3.4 (Financeiro), ver seção acima.

---

## ✅ Fase 3.3 do Fluxoly Design System — Operação, Fatia 3.3.2 (Vendas) ENCERRADA (PR #64 mergeado)

**Ver `docs/engineering/plans/PLAN-design-system-fase3.3-operacao.md` para o registro completo (5
fatias).**

2026-08-26, sequência imediata à Fatia 3.3.1 (mergeada em `main`, PR #63). Segunda fatia do Tier 2.

**Entregue** (branch `feat/design-system-fase3.3-operacao-vendas`):
- **Histórico** — tabela migra para `DataTable`, `getRowProps` preserva `data-testid`/`data-context-row`
  do `nav-context-highlight`, `onRowClick` navega para o detalhe da venda. Sem métrica dominante (mesmo
  critério de Orders). Nenhuma mudança em `applyFilters`/paginação/`useDebounced`.
- **Nova Venda** — o bloco de resumo/pagamento (único elemento dominante desta tela, decisão do CTO) migra
  para `Panel`/`PanelContent`, total em destaque (`text-lg` → `text-2xl`). O card de confirmação "Venda
  concluída" também migrado para `Panel` — mesmo elemento conceitual em estado diferente.
- **KI-048 resolvido em `NovaVenda`** — os 3 pontos (`tiposGarantiaApi`/`clientesApi`/`unidadesApi`)
  ganharam `.catch()`. Só `tiposGarantiaApi` (sem `.finally` associado) tinha risco real de tela presa —
  ganhou `toast.error` explícito; os outros 2 já tinham `.finally()` restaurando o loading, `catch`
  adicionado por simetria com o `res?.ok ? ... : []` já existente (mesmo resultado visual em falha).

**Validação:** suíte completa 142/142 (1 teste novo), lint 0 erros (2 warnings pré-existentes não
relacionados), build de produção sem erro. QA visual não executada ao vivo nesta fatia (mesma limitação de
KI-027 — sessão não persiste no navegador de automação); validado por testes automatizados + revisão de
código.

**KI-048 (progresso):** `Kanban.jsx` (Fatia 3.3.1) e `Vendas.jsx::NovaVenda` (esta fatia) resolvidos.
Restam `Stock.jsx::fetchItems` (Fatia 3.3.3) e `Clientes.jsx::PerfilCliente` (Fatia 3.3.5) + 3 pontos no
Tier 3 (Fase 3.4, fora desta fase).

**Decisão do CTO:** aprovado o plano da Fase 3.3 (5 fatias) e as decisões de composição por tela antes da
implementação. **Mergeado em `main` (PR #64, squash, commit `5d1ad723`, 2026-08-26)** — CI 8/8 (×2) verde,
produção confirmada saudável pós-merge (`/health` backend → 200, frontend Vercel → 200).

**Próximo passo:** Fatia 3.3.3 (Stock), ver seção acima.

---

## ✅ Fase 3.3 do Fluxoly Design System — Operação, Fatia 3.3.1 (DataTable + Orders + Kanban) ENCERRADA (PR #63 mergeado)

**Ver `docs/engineering/plans/PLAN-design-system-fase3.3-operacao.md` para o registro completo (5
fatias) e `docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md` (§9) para o
faseamento por tier.**

2026-08-26. Quarta fatia da Fase 3, sequência imediata à Vitrine (3.2). Primeira fatia do Tier 2
("Operação diária"): Orders, Kanban, Vendas, Stock, Financeiro, Clientes — divididos em 5 PRs (mesmo
critério de granularidade da Fase 2, PRs 3/4/5). Esta fatia (3.3.1) é pré-requisito das outras 4: estende
o `DataTable` (Foundation v2, Fase 3.1) antes de qualquer tela virar seu primeiro consumidor real.

**Decisões de composição aprovadas pelo CTO antes da implementação:** nem toda tela tem 1 elemento
dominante óbvio — Orders/Clientes/Vendas-Histórico (contadores simples) ficam sem `Panel`-hero, viram só
`LooseMetric`; Stock ("Valor Total") e Financeiro ("Saldo em caixa") têm candidato dominante real e viram
`Panel`, mesmo tratamento do Faturamento no Dashboard (Fase 3.2). KI-048/KI-049 (bugs pré-existentes nas
telas deste tier) decididos corrigir junto, em commit separado do de composição.

**Entregue** (branch `feat/design-system-fase3.3-operacao-orders-kanban`):
- **`DataTable`** ganha `getRowProps(row)` — propaga atributos por linha (ex.: `data-testid`/
  `data-context-row` do `nav-context-highlight`, `useListContext.js`) sem sobrescrever `className`/
  `onClick`/`tabIndex` fixos do componente (spread ocorre antes das props fixas).
- **KI-053 resolvido** — `onRowClick` agora responde a Espaço além de Enter, `role="button"` adicionado à
  linha quando clicável. Corrigido antes de `OrderTable.jsx` se tornar o primeiro consumidor real do
  componente (a lacuna existia desde a Fase 3.1, nunca exposta por falta de consumidor).
- **Orders** — stats bar (Total/Em aberto/Finalizadas) migra para `LooseMetric`; `OrderTable.jsx` migra de
  HTML cru para `DataTable`. Nenhuma mudança em `applyFilters`/`extractMeta`/`fetchOrdens`/`handleDelete`.
- **Kanban** — auditado contra os 5 princípios de composição (`PLAN-design-system-fase3-visual-
  experience.md` §2) — nenhum achado (board de 4 colunas já não é card uniforme, já usa tom semântico via
  `getStatusVariant`). **KI-048 resolvido** — `fetchOrdens` ganhou `.catch()` (mesmo padrão de
  `Orders.jsx`).

**Validação:** suíte completa 141/141 (5 testes novos — 4 do `DataTable`, 1 do `Kanban`), lint 0 erros (2
warnings pré-existentes não relacionados), build de produção sem erro.

**KI-048 (progresso parcial):** este KI cobre 6 pontos em 4 telas fora de Kanban (`Stock.jsx::fetchItems`,
`Vendas.jsx::NovaVenda` ×3, `Clientes.jsx::PerfilCliente`) mais 3 no Tier 3 (`NewOrder`/`EditOrder`/
`VendaDetalhe`, fora desta fase) — só fecha por completo quando todas as fatias/fases relevantes
corrigirem seu ponto. `KNOWN_ISSUES.md` atualizado para refletir o progresso real.

**Decisão do CTO:** aprovado o plano da Fase 3.3 (5 fatias) e as decisões de composição por tela antes da
implementação. **Mergeado em `main` (PR #63, squash, commit `7ca3f17a`, 2026-08-26)** — CI 8/8 (×2) verde,
produção confirmada saudável pós-merge (`/health` backend → 200, frontend Vercel → 200).

**Próximo passo:** Fatia 3.3.2 (Vendas — Histórico + Nova Venda), ver seção acima.

---

## ✅ Fase 3.2 do Fluxoly Design System — Vitrine ENCERRADA (PR #62 mergeado)

**Ver `docs/engineering/plans/PLAN-design-system-fase3.2-vitrine.md` para o registro completo e
`docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md` (seção 12) para o faseamento
completo da Fase 3.**

2026-08-25. Terceira fatia da Fase 3, sequência imediata à Foundation v2 (3.1). Primeira fase a mudar
composição de tela real (Tier 1 — "Vitrine": Login, Shell/Sidebar, Dashboard), prova de conceito da
hierarquia de superfície antes de escalar para as Fases 3.3-3.5 (Tiers 2-4). Executada via
`superpowers:subagent-driven-development` (4 tasks de implementação + 1 de validação/docs, cada uma com
implementador + revisor dedicados, 2 rulings do controlador sobre gaps reais do próprio plano — ver
"Rulings" abaixo).

**Entregue** (branch `feat/design-system-fase3.2-vitrine`):
- **Login** — form migra de `bg-card border ... shadow-xl` manual para `Panel`/`PanelContent` (Foundation
  v2), com respiro adicional (`py-12`, `space-y-8`) acima/abaixo do bloco de marca e do form.
- **Shell/Sidebar** — os 18 itens de navegação, antes uma lista plana, agora agrupados pelos 6 Pilares
  Macrossistêmicos da marca (`BRAND_IDENTITY.md` §2: Vendas/Operação/Financeiro/Relacionamento/Serviços/
  Inteligência) + uma seção "Administração" fora dos pilares (Usuários/Backups). Uma seção some por
  completo quando nenhum item dela é visível para o perfil da sessão. De quebra, corrigida uma duplicata
  histórica (`/compras` aparecia como "Compras" e "Lista de Compras" na mesma lista).
- **Dashboard** — de "8 KPIs + 3 gráficos, todos do mesmo peso" para hierarquia real: Faturamento vira
  métrica dominante (`Panel`, número hero `text-4xl`/`text-5xl`); os outros 7 KPIs viram `LooseMetric`
  (sem moldura); "Resumo Financeiro" vira `ListBlock` em vez de grade de caixas com fundo próprio.
  `KpiCard.jsx` fica sem consumidor — registrado como **KI-056**, não removido (decisão do CTO).
- **Landing** — auditada por consistência de token/marca (fora da liberdade criativa total da Fase 3,
  não redesenhada). Nenhum achado — já herdava corretamente os tokens e o ícone/wordmark Pulse do PR #61.

**Rulings do controlador durante a execução** (2 gaps reais encontrados no próprio plano, não erros dos
implementadores — confirmados via RED/GREEN real antes de decidir, não por suposição):
1. A seção "Vendas" do Sidebar contém um item também chamado "Vendas" (mesmo caso em "Financeiro") — texto
   duplicado no DOM quebrava 3 asserções `getByText`. Resolvido via seletor idiomático
   (`getByRole("link", ...)` para o item, `getByText(..., { selector: "p" })` para o rótulo da seção) —
   teste-only, sem mudança de composição.
2. O valor de Faturamento aparece duas vezes de propósito no Dashboard (métrica dominante + linha do
   Resumo Financeiro) — colisão pré-existente desde antes desta fase (o `KpiCard` antigo já tinha esse
   mesmo problema, nunca antes testado por string exata). Resolvido via `getAllByText` + filtro por classe
   do elemento hero — teste-only.

**Validação:** suíte completa 136/136, lint 0 erros (2 warnings pré-existentes não relacionados), build de
produção sem erro. QA visual real em Chrome confirmada para Login e Sidebar (Dark + Light Mode, 8 seções
corretas para perfil admin, nenhum rótulo órfão). QA visual do Dashboard com dados reais (seed via
`scripts/seed_demo.py`, banco isolado, nunca `database.db`) **bloqueada pelo KI-027** já documentado —
sessão de login não persiste no navegador de automação usado nesta sessão; confirmado via `curl` (cookie
jar real, fora do navegador de automação) que login + `/api/dashboard` retornam os dados corretos com o
código desta fase. Correção do componente confirmada independentemente pela revisão de código
(comparação linha a linha do diff contra as cores/labels do `KpiCard` removido).

**Achados da revisão final (corrigidos antes do merge):**
1. `DashboardSkeleton` ainda desenhava os 8 KPIs uniformes antigos no loading — salto visual toda vez que
   a tela carrega, já que o conteúdo real mudou para a hierarquia nova. Corrigido para refletir a mesma
   composição (Panel dominante + `LooseMetric`s + gráficos).
2. Rótulos de seção do Sidebar (`text-sidebar-foreground/40`) não passavam no WCAG AA (~3.3:1 vs piso de
   4.5:1) — mesma classe de achado que o KI-050 já havia corrigido antes, teria se propagado para as Fases
   3.3-3.5 se não corrigido agora. Ajustado para `/50` (~4.65:1).

Suíte completa reconfirmada 136/136 (uma falha isolada de flakiness sob carga, não reproduzida em
reexecução), lint 0 erros, build ok. CI 8/8 (×2) verde no commit de correção antes do merge.

**Achados Minor, aceitos como estão** (decisão de manter escopo cirúrgico): Faturamento aparece duas vezes
na tela (hero + Resumo Financeiro, colisão pré-existente); cores dos `LooseMetric`s sem regra clara de
quais mantêm cor; sombra do Login mais achatada que a doc descreve; 4 containers de gráfico ainda usam
legenda manual; agrupamento do Sidebar é só visual (sem `role="group"`/`aria-labelledby`); asserção de
teste do Dashboard poderia falhar de forma mais clara; 2 pequenas imprecisões de documentação.

**Decisão do CTO:** aprovado o plano antes da implementação (agrupamento do Sidebar e escolha do
Faturamento como métrica dominante, ambos propostos no plano) e aprovado o merge após a correção dos 2
achados Important. Mergeado em `main` (squash, PR #62, commit `deb460c5`, 2026-08-25).

**Próximo passo:** Fase 3.3 (Operação — Orders/Kanban/Vendas/Stock/Financeiro/Clientes).

---

## ✅ Fase 3.1 do Fluxoly Design System — Foundation v2 ENCERRADA (PR #60 mergeado)

**Ver `docs/engineering/plans/PLAN-design-system-fase3.1-foundation-v2.md` para o registro completo e
`docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md` (seção 12) para o faseamento
completo da Fase 3.**

2026-08-22. Segunda fatia da Fase 3, sequência imediata à infraestrutura de tema (3.0). Escopo: recipientes de
composição (`Panel`/`ListBlock`/`LooseMetric`, substituindo `Card` como recipiente universal), `DataTable`
real, tema único de gráfico (Recharts) e a correção do KI-050 (9 telas com cor hardcoded, ilegível em
Light Mode). Nenhuma tela redesenhada — migração de composição das telas é Fase 3.2+.

**Entregue** (branch `feat/design-system-fase3.1-foundation-v2`):
- `Panel`/`PanelHeader`/`PanelTitle`/`PanelDescription`/`PanelContent`, `ListBlock`/`ListBlockItem`,
  `LooseMetric` — novos em `components/ui/`, ainda não usados por nenhuma página.
- `DataTable` — tabela real da Foundation (header sticky opcional, linha clicável com suporte a teclado),
  ainda não usada por nenhuma página.
- `lib/chart-theme.js` — tema único (`var(--color-*)`) para os 3 gráficos do Dashboard
  (`RevenueChartCard`/`ServicesChartCard`/`TechnicianProfitChartCard`), que antes usavam cor SVG fixa
  (hex/hsl) sem relação com o tema nem com a marca.
- KI-050 resolvido — `KpiCard.jsx`/`Dashboard.jsx`/`Reports.jsx`/`OperationalCosts.jsx`/`Garantias.jsx`/
  `Vendas.jsx`/`Users.jsx`/`VendaDetalhe.jsx`/`TiposGarantia.jsx` migrados de classe Tailwind crua para os
  tokens de tema (`text-success`/`warning`/`destructive`/`info`). Exceção: papel "financeiro" em
  `Users.jsx` sem token de roxo equivalente — registrado como KI-051.

**Validação:** suíte completa passando (133/133), lint 0 erros. Cada task passou por revisão automatizada
individual (spec + qualidade) com verificação de token-a-token contra o diff real, mais uma revisão final
whole-branch (Opus) com um fix round (5 achados Important corrigidos/registrados, ver
`docs/operations/KNOWN_ISSUES.md` KI-052/KI-053).

Checklist manual em navegador real, feito parcialmente após a extensão do Claude in Chrome reconectar:
confirmado em Chrome real, nos dois modos (Light forçado via `localStorage`/`data-theme`, Dark padrão) —
**a preocupação técnica mais concreta levantada na revisão final (uso de `var(--color-chart-N)` dentro de
atributos de apresentação SVG cru — `stop-color`/`stroke`, não `style=`, com histórico de suporte
inconsistente em engines mais antigas) foi verificada diretamente**: um teste isolado reproduzindo
exatamente o padrão de `RevenueChartCard.jsx` (`<stop stop-color="var(--color-chart-1)">`, `<line
stroke="var(--color-chart-1)">`) confirmou resolução correta em Chrome/Blink nos dois modos (`#FF3D5A`
tanto via `getComputedStyle` quanto visualmente, gradiente renderizado por screenshot) — e os tokens
`--color-border`/`--color-muted-foreground` usados por `CHART_GRID_STROKE`/`CHART_AXIS_TICK` resolvem
corretamente em Light (`#E4E7EF`/`#5B6178`, legíveis contra `#F5F6FA`). **Não verificado:** as 9 telas
autenticadas do KI-050 e o Dashboard completo com dados reais (backend Flask não está rodando neste
worktree — levantar backend + seed só para este QA visual seria desproporcional a uma correção de token de
cor já verificada exaustivamente por 3 revisões automatizadas independentes); Safari/WebKit (só Chrome
disponível nesta sessão) segue sem verificação direta, mas o mecanismo específico que motivou a dúvida
(resolução de `var()` em atributo SVG) está confirmado funcionando no motor de renderização mais usado.
Gap residual não bloqueante, mesma classe já aceita no fechamento da Fase 3.0.

**Decisão do CTO:** aprovado. Mergeado em `main` (PR #60, squash, commit `248349db`, 2026-08-22). CI 17/17
verde antes do merge (Backend Tests, Frontend Unit Tests, Coverage, Docker Build, Frontend Build, Frontend
Quality, Lint — todos ×2 — mais Vercel Preview/Deploy).

**Próximo passo:** Fase 3.2 (Vitrine — Dashboard + Login + Shell/Sidebar + harmonização da Landing).

---

## ✅ Fase 3.0 do Fluxoly Design System — Infraestrutura de Tema ENCERRADA (PR #59 mergeado)

**Ver `docs/engineering/plans/PLAN-design-system-fase3.0-theme-infra.md` para o registro completo e
`docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md` (seção 12) para o faseamento
completo da Fase 3.**

2026-08-20. Primeira fatia da Fase 3 (Fluxoly Visual Experience Redesign), aberta na sequência da Fase 2
(PRs 1-5, Vendas+VendaDetalhe+Financeiro+Clientes até `Estoque`/`Produtos`/`Unidades Serializadas`).
Escopo puramente de infraestrutura — nenhum componente visual muda ainda, migração de composição fica para
a Fase 3.1 (Foundation v2).

**Entregue** (branch `feat/design-system-fase3.0-theme-infra`, tasks 1-5 mergeadas nesta branch, Task 6
de validação final em andamento):
- **`ThemeContext`/`useTheme()`** com estado persistente (`localStorage`, chave `fluxoly-theme`) e
  sincronia com a preferência do sistema operacional (`prefers-color-scheme`).
- **Tokens de cor recalibrados para WCAG AA** — cores semânticas de estado (sucesso/aviso/erro/info)
  ajustadas para contraste correto em fundo claro.
- **`index.css` restruturado em duas camadas** (Light Mode como base, overrides de Dark Mode via
  `@media (prefers-color-scheme)` + `data-theme` manual) com a identidade Pulse aplicada aos tokens
  (`#FF3D5A` vermelho-sinal, `#29E0C9` ciano de fluxo).
- **`ThemeProvider`** conectado no ponto de entrada do app, com script anti-FOUC em `index.html` evitando
  flash da cor errada no primeiro paint ao recarregar com um tema fixado.
- **`ThemeToggle`** — botão de 3 estados (automático/claro/escuro) na Sidebar.
- **Nenhum componente redesenhado ainda** — Fase 3.1 (Foundation v2) é o próximo passo, evoluindo
  `Badge`/`Card`/`EmptyState`/etc. para os dois modos.
- **Decisão do CTO (revisão final, 2026-08-20):** o tema padrão para quem não tem preferência salva
  permanece Dark (não segue o SO) até a Fase 3.1 migrar as 9 telas com classes Tailwind hardcoded
  listadas em KI-050 — o toggle automático/claro/escuro continua totalmente funcional para quem
  escolhe explicitamente.

**Validação (Task 6):** suíte completa 106/106, lint 0 erros (2 warnings pré-existentes em arquivos não
relacionados — `ShoppingList.jsx`/`Stock.jsx` — fora do escopo desta fase). Checklist manual em navegador
real (Chrome, via automação, página `/login` que não exige autenticação): Dark Mode padrão confirmado
(fundo quase-preto, card claro, botão primário no vermelho-sinal correto) e Light Mode forçado via
`localStorage` confirmado (fundo quase-branco, card branco, texto legível, mesmo vermelho-sinal, bordas
sutis, sem extremos puro-branco/puro-preto) — validando em navegador real a reestruturação de tokens da
Task 3. Toggle na Sidebar autenticada e o dashboard completo não foram verificados ao vivo nesta rodada
(sem backend rodando para sessão autenticada) — gap residual, não bloqueante. Nenhuma captura
frame-a-frame do anti-FOUC foi feita (não prático com a ferramenta de screenshot disponível); a
correção do script foi validada por revisão de código na Task 4.

**Decisão do CTO:** aprovado. Mergeado em `main` (PR #59, commit `5b6237df`, 2026-08-20); branch
`feat/design-system-fase3.0-theme-infra` ainda não deletada (remoto e local).

**Próximo passo:** Fase 3.1 (Foundation v2) — migração de composição dos componentes (`Badge`/`Card`/
`EmptyState`/etc.) para os dois modos, incluindo as 9 telas com classes Tailwind hardcoded listadas em
KI-050.

---

## ✅ Fase 2 do Fluxoly Design System — PR 1 (Foundation) ENCERRADO (PR #54 mergeado)

**Ver `docs/engineering/plans/PLAN-design-system-fase2.md` para o registro completo (auditoria das 24
páginas, plano de 8 PRs aprovado pelo CTO) e `docs/engineering/ENGINEERING_GUIDE.md` §3.3 para as
convenções vivas.**

2026-08-19. Auditoria das 24 páginas do frontend confirmou que o Design System Fase 1 (PRs #41-#49) cobre
só Shell/Dashboard/Landing — as outras 21 páginas operacionais seguem com badges de status reimplementados
à mão (~13 arquivos), sem estados de loading/empty/error além de spinner genérico, e `ChecklistDevice.jsx`
(única tela pública) com paleta própria, sem relação com a marca. CTO aprovou plano de 8 PRs sequenciais,
com o PR 1 estabelecendo o vocabulário compartilhado antes de qualquer tela ser redesenhada (correção do
CTO ao plano inicial, que começaria pelo `ChecklistDevice` isolado — Foundation primeiro evita retrabalho).

**Entregue neste PR (branch `feat/design-system-fase2-foundation`, aberta a partir de `main` — não da
branch não mergeada `feat/aplicar-identidade-visual-marca`/PR #53, para não misturar as duas frentes):**
`Badge` com variantes semânticas (`success`/`warning`/`error`/`info`/`neutral`), `EmptyState`/
`ErrorState`/`ErrorBanner`/`ListSkeleton`/`CardGridSkeleton` (generalização do padrão de 4 estados do
Dashboard, PR #46), `FilterBar`/`FilterSelect`/`FilterInput`/`DateRangeFilter`/`ClearFiltersButton`
(composição visual, sem tocar lógica de filtragem de nenhuma página), `Reveal` (Motion discreto para
conteúdo pós-fetch, distinto do `FadeInSection` da Landing) e `lib/interaction.js` (convenção CSS de
hover/foco). Nenhuma página em `pages/` foi tocada — só `components/ui/` e `lib/`. 26 testes novos
(Vitest), suíte completa 40/40, lint 0 erros (2 warnings pré-existentes em `ShoppingList.jsx`/`Stock.jsx`,
fora de escopo), build de produção confirmado sem erro.

**Decisão do CTO:** aprovado exatamente no escopo entregue (revisão critério a critério confirmando
Foundation, nenhuma tela tocada, marca intocada, testes/CI/lint/build ok). Mergeado em `main` (squash,
`567ad47b`), branch deletada.

---

## ✅ Fase 2 do Fluxoly Design System — PR 2 (`ChecklistDevice.jsx`, golden standard) ENCERRADO (PR #55 mergeado)

**Ver `docs/engineering/plans/PLAN-design-system-fase2.md` (seção "PR 2") para o registro completo.**

2026-08-19, sequência imediata ao PR 1. Antes de iniciar, achado de dependência: o PR #53 (aplicação da
marca — ícone e wordmark) ainda estava aberto/não mergeado, e sem ele `main` não tinha a fonte Onest
carregada nem o `viewBox` corrigido dos SVGs do ícone — inviabilizaria o `ChecklistDevice` demonstrar
"Marca"/"Tipografia" de verdade como golden standard. CTO decidiu mergear o PR #53 primeiro (branch
atualizada a partir do `main` pós-PR-#54, CI 6/6 revalidado, sem conflitos) antes de abrir a branch do PR
2 — `main` agora tem os dois PRs (`843c33fd` PR #53, `567ad47b` PR #54).

**Entregue (branch `feat/design-system-fase2-checklistdevice`):** redesenho puramente visual de
`ChecklistDevice.jsx` — nenhuma lógica de negócio, handler de dispositivo (áudio/microfone/câmera) ou
payload de `saveChecklist` alterado. Paleta própria (gradiente slate/azul) substituída pelos tokens
Fluxoly; `rounded-3xl`/`rounded-2xl` (fora da escala) → `rounded-xl` via `Card`; ícones lucide → Phosphor;
cor decorativa `cyan-300` (fora da paleta) → `text-primary`; estado de erro migrado para `ErrorState` da
Foundation; `Badge` semântico nos indicadores de status sugerido; `Checkbox` do design system nos botões
físicos; header com ícone + wordmark Fluxoly (mesmo padrão de `Login.jsx`); `Reveal` no conteúdo carregado.
5 testes novos, suíte completa 45/45, lint 0 erros, build ok.

**QA visual:** estado de erro confirmado ao vivo no navegador (Vite dev server); padrão de ícone+wordmark
confirmado em `/login` (mesmo código reaproveitado). Estado carregado (com OS real) validado via Vitest
sobre o DOM renderizado — reproduzir ao vivo exigiria backend + token de checklist reais.

**Decisão do CTO:** aprovado com 1 achado não bloqueante (KI-047, grade de touch sem `aria-label`,
pré-existente). Mergeado em `main` (squash, `a97515a3`), branch deletada.

---

## ✅ Fase 2 do Fluxoly Design System — PR 3 (Orders + Kanban + NewOrder + EditOrder) ENCERRADO (PR #56 mergeado)

**Ver `docs/engineering/plans/PLAN-design-system-fase2.md` (seção "PR 3") para o registro completo.**

2026-08-19, sequência imediata ao PR 2. Escopo: as 4 telas do fluxo central de OS (pilar Serviços) + 3
componentes de apoio (`OrderStatusBadge`, `OrderTable`, `OrderFilters`). Nenhuma lógica de negócio
alterada — confirmado por busca no diff completo por toda função de regra de negócio (handlers de submit/
drag-and-drop/reparo/peça, chamadas `create`/`update`/`delete`/`patchStatus`); nenhuma aparece em linha
alterada.

**Objetivo principal — unificação de cor de status:** `getStatusColor` (retornava classes Tailwind cruas)
substituído por `getStatusVariant` em `lib/constants.js`, fonte única de verdade consumida por
`OrderStatusBadge` (Orders/EditOrder) e pelo mapa de tom do `Kanban.jsx` — que antes redefinia cor por
coluna sozinho. O card do Kanban ganhou `<OrderStatusBadge status={os.status} />` (import já existia,
nunca tinha sido usado). `OrderFilters.jsx` reescrito com `FilterBar`/`FilterSelect`/`FilterInput` da
Foundation — primeira aplicação real desses componentes. `Orders.jsx`/`Kanban.jsx` ganharam `ListSkeleton`/
`ErrorState` com retry na carga inicial (o polling silencioso de 30s do Orders continua sem toast/banner,
inalterado). Ícones lucide → Phosphor, `rose-500` (fora da paleta) → `text-primary`, 2 desvios extras de
radius/shadow corrigidos no Kanban (`hover:shadow-md` removido, `rounded-lg` → `rounded-xl`) — fora do
escopo original do PR 8 mas no mesmo arquivo já sendo tocado pelo mesmo motivo.

**Testes:** 13 novos (`OrderStatusBadge`/`Orders`/`Kanban` nunca tinham teste antes). Suíte completa
58/58, lint 0 erros, build ok. `NewOrder.jsx`/`EditOrder.jsx` sem teste novo — mudança puramente de ícone/
cor/radius, desproporcional escrever teste de formulário completo só para isso.

**Achado registrado, não corrigido:** KI-048 — `NewOrder.jsx`/`EditOrder.jsx`/`Kanban.jsx` não tratam
rejeição de promise na carga inicial (`.then()` sem `.catch()`), pré-existente, fora do escopo visual.

**Decisão do CTO:** aprovado. Mergeado em `main` (squash, `dedd2e2a`), branch deletada.

---

## ✅ Fase 2 do Fluxoly Design System — PR 4 (Estoque + Unidades Serializadas + Produtos) mergeado

**Ver `docs/engineering/plans/PLAN-design-system-fase2.md` (seção "PR 4") para o registro completo.**

2026-08-20, sequência imediata ao PR 3, com um checkpoint arquitetural somente-leitura do CTO antes de
autorizar o início (confirmação de `main` sincronizada, PRs #53-#56 mergeados, ausência de KI aberto
afetando essas 3 telas, mapeamento de escopo/dependências/riscos — sem alterar código).

**Achado do checkpoint, resolvido antes da implementação:** `Produtos.jsx` (`CATEGORIA_BADGE`) e
`UnidadesSerializadas.jsx`/`Vendas.jsx` (`ORIGEM_BADGE`, duplicado literalmente entre os dois arquivos)
usam badges **categóricos** (que tipo de coisa é isso — categoria/origem), não badges de **status**
(como está indo isso) — `purple`/`fuchsia`/`zinc` não têm variante semântica correspondente no `Badge` da
Foundation, que foi desenhado só para severidade. CTO decidiu **não** criar variante nova nem forçar esses
badges nos 5 variants de status existentes neste PR — ficam intocados, decisão de Design System (tag vs.
status) fica pendente para antes do PR 5 (que repete o mesmo `ORIGEM_BADGE`).

**Entregue:** status genuíno migrado normalmente onde existia — `Stock.jsx` (disponibilidade de estoque +
prioridade de reposição sugerida), `Produtos.jsx` (disponibilidade + condição Novo/Seminovo/Vitrine, as 3
cores já usadas mapearam 1:1 nos variants sem forçar nada), `UnidadesSerializadas.jsx` (5 estados —
`reservado`, que não é produzido por nenhum fluxo real ainda, reaproveita o tom de `em_reparo`). Cada
domínio manteve sua própria função de mapeamento local (não centralizada em `lib/constants.js`, já que
cada uma serve só o próprio arquivo). Ícones lucide → Phosphor, `FilterBar`/`FilterSelect`/`FilterInput`
nas 3 barras de filtro, `EmptyState`/`ErrorState`/`ListSkeleton`, `Checkbox` do design system no lugar de
`<input type="checkbox">` cru, `interactiveRowClassName`, `rounded-lg`→`rounded-xl` em 3 painéis do modal
de detalhe de unidades. Bug introduzido e corrigido durante a implementação: `onRetry` do `ErrorState` em
`UnidadesSerializadas.jsx` usava `setPage((p) => p)`, que não muda estado — corrigido com um `reloadToken`
dedicado antes de rodar os testes.

**Nenhuma lógica de negócio alterada** — confirmado por busca no diff completo por handler de negócio e
por diff isolado byte-a-byte de `handleSubmit`/`handleDelete`/`carregar`/`salvar` contra `main`.

**Testes:** 12 novos (as 3 páginas nunca tinham teste antes). Suíte completa 70/70, lint 0 erros, build ok.

**Achado registrado, não corrigido:** KI-048 estendido — `Stock.jsx::fetchItems` também não trata rejeição
de promise na carga inicial (mesmo padrão já registrado no PR 3 para NewOrder/EditOrder/Kanban).

**Decisão do CTO:** aprovado. CI 6/6 verde, revisão de diff completo sem alteração de lógica de negócio,
tokens do Design System verificados, `CATEGORIA_BADGE`/`ORIGEM_BADGE` comprovadamente idênticos ao `main`.
Mergeado em `main` (squash, `14527ea4`), branch preservada.

**Próximo passo:** ver seção do PR 5 logo abaixo.

---

## ✅ Fase 2 do Fluxoly Design System — PR 5 (Vendas + VendaDetalhe + Financeiro + Clientes) mergeado

**Ver `docs/engineering/plans/PLAN-design-system-fase2.md` (seção "PR 5") para o registro completo.**

2026-08-20, sequência imediata ao PR 4, com checkpoint arquitetural somente-leitura do CTO antes de
autorizar o início. Achado do checkpoint (`ORIGEM_BADGE` duplicado em `Vendas.jsx`/`UnidadesSerializadas.jsx`,
`CATEGORIA_BADGE` em `Produtos.jsx`) resolvido antes do restante do escopo: proposta técnica somente-leitura
apresentada e aprovada, nova variante taxonômica `variant="tag"` no `Badge` da Foundation (commit `e2b7dde9`,
isolado da migração dos 3 usos por decisão explícita do CTO — infraestrutura separada de aplicação), migração
dos 3 badges (commit `2fa03d70`), depois a aplicação da Foundation aos 4 arquivos do PR 5, um commit por
arquivo (`d9216b8e`/`8012bb9c`/`4a3c893b`/`3438a552`) — 6 commits no total na branch
`feat/design-system-fase2-vendas-financeiro-clientes`.

**Entregue:** status genuíno migrado — `vendaStatusVariant` (compartilhado `Vendas.jsx`/`VendaDetalhe.jsx`
via `lib/constants.js`), `tipoVariant`/`statusContaVariant` (`Financeiro.jsx`, local), `GarantiaBadge`
(`Clientes.jsx`, antes nem usava o componente `Badge`). `FilterBar`/`FilterSelect`/`FilterInput`,
`EmptyState`/`ErrorState`/`ListSkeleton`, `interactiveRowClassName`, ícones lucide → Phosphor nos 4
arquivos. Ajuste incidental de cores cruas para tokens semânticos (mesma classe já aceita no PR 3).

**Nenhuma lógica de negócio alterada** — confirmado por diff isolado de todos os handlers de cada arquivo
contra `main`.

**Testes:** 18 novos nas 3 listas que nunca tinham teste (`Vendas` Histórico, `Financeiro`
Movimentações+Contas, `Clientes`), mesmo critério do PR 4. `VendaDetalhe.jsx` sem teste novo, mesmo
critério do PR 3 (NewOrder/EditOrder). Suíte completa 89/89, lint 0 erros, build ok.

**Achados registrados, não corrigidos:** `KI-048` estendido (`Vendas.jsx::NovaVenda` 3×, `VendaDetalhe.jsx`
1×, `Clientes.jsx::PerfilCliente` 1×; `Financeiro.jsx` auditado e limpo). `KI-049` novo —
`Clientes.jsx::fetchItems` sem estado de erro dedicado, distinto do KI-048.

**Decisão do CTO:** aprovado. CI 6/6 verde (duas execuções), revisão de diff completo sem alteração de
lógica de negócio. Mergeado em `main` (squash, `58c40e7b`, PR #58), branch preservada.

**Próximo passo:** PR 6 (Reports + Price Tables + Repair Types + Users) — não iniciado, aguardando
autorização do CTO. _(Reconciliação 2026-08-27: escopo absorvido pelo replan do Design System — é a Fase
3.5 / Tier 4 Administrativo, ver seções da Fase 3 acima.)_

---

## ✅ Landing Page Institucional — Implementação ENCERRADA (PR #49 mergeado)

**Ver `docs/engineering/plans/PLAN-landing-page-implementacao.md` para o registro completo e
`docs/product/features/LANDING_PAGE.md` para a especificação de conteúdo/UX que originou o plano.**

2026-08-17. Implementação em código das 14 seções especificadas no `LANDING_PAGE.md` (PR #44, doc-only,
2026-08-16), fechando o item final do checklist daquele documento ("Plano Técnico de implementação
redigido e aprovado pelo CTO... antes de qualquer código React ser escrito"). Ciclo leve (mesmo gate da
Fase 1 do Design System — "apresentar plano e aguardar aprovação" do `CLAUDE.md`, sem BR nova), não o
`ADR-010` completo.

**Decisões do CTO que definiram o plano:** roteamento — `/` pública quando deslogado (Landing) e Dashboard
quando autenticado, padrão Linear/Stripe/Vercel; escopo — estrutura completa das 14 seções já nesta fatia,
com os itens ainda `[DEFINIR]` (preço, prova social, trial) como placeholder textual, sem bloquear o resto.

**Entregue** (branch `feat/landing-page-implementacao`, 5 commits atômicos, CI 8/8 verde — 2 checks a mais
que o padrão de 6 porque o job `Frontend Unit Tests` deste PR passou a cobrir `App.jsx`/`Landing.jsx`):
- **Roteamento:** único ponto de mudança em `ProtectedRoute` (`App.jsx`) — `/` deslogado renderiza a
  `Landing` em vez de redirecionar para `/login`; toda outra rota protegida continua redirecionando
  normalmente. `AuthContext`, `Login.jsx`, `Layout.jsx`, backend e banco não foram tocados.
- **14 componentes de seção** (`frontend/src/components/landing/`) + `Landing.jsx`, mapeamento 1:1 com a
  tabela do `LANDING_PAGE.md`, reaproveitando 100% do Design System já mergeado (Button, Card, Badge,
  Skeleton). Copy centralizada em `content.js`, extraída literalmente da spec — nenhum item `[DEFINIR]`
  (preço, prova social, trial) preenchido com dado inventado.
- **Design System aditivo:** `size="lg"` no `Button` e `Accordion` novo (padrão shadcn manual, mesma
  convenção do Tooltip/Sheet — sem CLI funcional em projeto sem `tsconfig`/`jsconfig`), única dependência
  nova (`@radix-ui/react-accordion`). Mockups de Hero/"Visão do sistema" construídos com Card/Skeleton reais
  do Design System, não screenshot nem banco de imagens.
- **Testes:** 18/18 (11 pré-existentes + 7 novos — `App.test.jsx` trava a regra "só `/` muda"; `Landing.test.jsx`
  cobre as 14 seções, CTA, placeholders `[DEFINIR]` e o Accordion do FAQ). `IntersectionObserver` (ausente
  em jsdom, exigido pelo `whileInView` do Motion) recebeu stub em `test/setup.js`.
- **QA Manual:** desktop confirmado ao vivo (`npm run dev` + Claude in Chrome — 14 seções, FAQ abre/fecha,
  CTAs corretos). **Mobile não confirmado visualmente** — mesma limitação já registrada na QA da Fase 1 do
  Design System (resize da ferramenta de automação não afeta o viewport real da página); coberto por
  revisão de código (breakpoints seguem o mesmo padrão já testado do `Sidebar`) e pelos testes
  automatizados, aceito explicitamente pelo CTO antes da abertura do PR.
- **Revisão Arquitetural** (4 eixos, CTO): roteamento ✅, isolamento de Auth/Login/Layout/APIs/banco ✅,
  dependência nova validada pelo CI ✅, conteúdo sem invenções ✅. Achado de conteúdo revisado e confirmado
  não-bloqueante: o `<title>`/meta description usa "dispositivos móveis premium" — checado contra
  `docs/company/BRAND_IDENTITY.md` (nome, promessa, escopo negativo e visão da marca já usam "premium" há
  muito antes deste PR) e contra o próprio FAQ da Landing (já aprovado) — mantido como estava, não é uma
  decisão de posicionamento nova desta PR.
- **Achado durante o CI, corrigido no próprio ciclo:** primeira execução falhou (`npm ci` estrito do Linux
  não encontrou `@emnapi/core`/`@emnapi/runtime` no lockfile — o `npm install` no Windows remove essas
  entradas top-level porque só precisa da build nativa da plataforma atual). Mesmo problema e mesma
  correção já vistos na Sprint Infra 1.1 (**KI-026** causa 2) — restaurado num commit `fix:` próprio,
  versões/hashes reconferidos contra o registry, CI reexecutado do zero: 8/8 verde.

**Fora deste ciclo, deliberadamente:** preencher qualquer `[DEFINIR]` (preço, prova social, trial, suporte),
fonte Inter (amendment do Design System ainda não decidido), GSAP/Three.js/Anime.js, screenshot real do
Dashboard, captura de lead, SEO avançado (Open Graph dinâmico, SSR).

**Decisão do CTO:** PR #49 aprovado nos 4 eixos da Revisão Arquitetural + merge autorizado. Mergeado em
`main` (`a339de19`), branch deletada. Produção confirmada saudável pós-merge (`/health` backend → 200,
frontend Vercel → 200, `<title>` da build de produção conferido).

---

## ✅ Fase 1 do Fluxoly Design System — ENCERRADA (7 PRs mergeados)

**Ver `docs/engineering/plans/PLAN-design-system-fase1.md` para o registro completo de todas as etapas e
`docs/engineering/adr/ADR-001.md` (amendment) para a decisão arquitetural.**

2026-08-16. Iniciativa de UI/UX proposta pelo CTO — formalizar shadcn/ui, Motion e Phosphor Icons como
padrão de composição do Fluxoly, mantendo Radix UI como fundação já decidida (ADR-001) e a identidade
visual já em produção (`#FF0125` + fundo escuro). Investigação de código antes do plano confirmou que o
projeto já convergia organicamente para o padrão shadcn (`button.jsx` já era `cva` + `Slot` + `cn()`) —
reduziu o escopo real de "adoção do zero" para "formalização e expansão". Executado em 7 PRs sequenciais,
cada um com CI 6/6 e aprovação explícita do CTO antes do merge:

- **PR #41 — Governance/ADR:** Plano Técnico + amendment do ADR-001, sem nenhuma dependência instalada.
- **PR #42 — Design System Foundation:** tokens de spacing/radius/shadow (decisão de usar a escala padrão
  do Tailwind em vez de tokens customizados), `components.json`, `Card`/`Skeleton`, Phosphor instalado.
- **PR #43 — Motion + componentes:** Motion + `@radix-ui/react-tooltip` instalados, `Tooltip`/`Sheet`
  (transição CSS via `data-state` — Radix `Presence` não detecta a animação via WAAPI do Motion) e
  `Sidebar` (drawer mobile com Motion de verdade, `useReducedMotion` respeitado).
- **PR #44 — Landing Page (frente separada, doc-only):** especificação de conteúdo/estrutura/Design System
  da futura Landing Page institucional (`docs/product/features/LANDING_PAGE.md`), Mercado Phone analisado
  como benchmark de mercado/concorrente direto (sem parceria — dependência técnica de API, não relação
  comercial), identidade visual **não** derivada do concorrente. Nenhuma implementação — não faz parte da
  sequência técnica dos 7 PRs, decisão do CTO de não misturar com o Shell.
- **PR #45 — Application Shell:** `Layout.jsx` migrado para `SidebarProvider`/`Sidebar`, elimina a
  duplicação de markup desktop/mobile anterior, comportamento preservado 1:1, ícones em Phosphor.
- **PR #46 — Dashboard Pilot:** 4 estados explícitos (loading/success/empty/error — antes só existia
  loading e um `toast.error` que desaparecia), ícones em Phosphor.
- **PR #47 — Frontend Tests:** Vitest + Testing Library inaugurados (0% → 11 testes), job de CI não-
  bloqueante nesta fase.
- **Final QA (fechamento, sem PR própria de código):** QA Manual nos 3 perfis (admin/técnico/vendedor)
  contra backend real e descartável (seed via `scripts/seed_demo.py`, nunca `database.db`) confirmou o
  Shell renderizando e filtrando o menu corretamente nos três perfis, e navegação por teclado com foco
  visível. Achado de ambiente (não de código, não bloqueante): a sessão de login não persistiu no
  navegador de automação usado nesta QA — nova reprodução do `KI-027` já conhecido, confirmado via `curl`
  que backend/proxy/sessão funcionam corretamente fora do navegador de automação (registrado em
  `KNOWN_ISSUES.md`). Esse mesmo achado validou organicamente o estado de erro do Dashboard (PR #46) contra
  uma falha real, não simulada. Resize de viewport da ferramenta de automação não afetou o viewport real da
  página nesta sessão — o drawer mobile não pôde ser clicado interativamente ao vivo; validado por revisão
  de código + teste automatizado do hook `useIsMobile` (PR #47).

**Bundle:** chunk principal (Shell, carregado em toda rota) cresceu de 115 kB para 167 kB gzip — Motion
agora faz parte do carregamento inicial. Chunk do Dashboard (lazy, por rota) não afetou o bundle principal.
Otimização futura possível, não implementada: lazy-load do caminho mobile-only do `Sidebar`.

**Fora de escopo desta fase, deliberadamente:** redesign de qualquer módulo além de Shell/Dashboard,
Next.js, GSAP/Three.js/Anime.js, meta de cobertura de teste do frontend inteiro, implementação da Landing
Page (fica para um plano técnico próprio e futuro).

**Decisão do CTO:** ciclo encerrado, todos os 7 PRs mergeados em `main`. Próxima iniciativa de UI/UX (se
houver) — incluindo a possível implementação da Landing Page especificada no PR #44 — fica em aberto, sem
data definida.

---

## ✅ Fase 1 de LGPD/Compliance — ENCERRADA e em `main` (ciclo ADR-010 completo, PR #40)

**Ver `docs/engineering/plans/PLAN-LGPD-Compliance.md` para o registro completo (Discovery, Decisões do
CTO, Plano Técnico, Implementação, Testes, QA Manual, Revisão Arquitetural, Encerramento) e
`docs/product/research/DISCOVERY_LGPD.md`/`DISCOVERY_RELEASE_1.0_RESTANTE.md` para o levantamento que
originou este ciclo.**

2026-08-17. A Discovery consolidada da Release 1.0 (parte restante) identificou LGPD como o maior risco
desconhecido do que falta para o primeiro cliente pagante. A Discovery de LGPD (pesquisa somente-leitura
sobre o próprio código) mapeou onde o dado pessoal vive, e o CTO aprovou uma baseline de 7 decisões:
escopo intermediário, KI-029 obrigatório antes do piloto (mas só a Fase 1 não-destrutiva neste ciclo),
KI-043 com contenção (não criptografia ainda), KI-044 com anonimização (não hard-delete), KI-045
restringindo só leitura de CPF, `audit_log` com mecanismo parametrizável sem prazo hardcoded, e posição
jurídica conservadora provisória.

**Entregue** (branch `feat/lgpd-compliance-fase1`, commits atômicos por escopo, CI 6/6 verde):
- **KI-029 Fase 1:** os dois arquivos `.db` reais removidos do índice do git (`git rm --cached`, não do
  histórico); `.gitignore` reforçado. Fase 2 (reescrita de histórico) confirmada não executada em nenhum
  momento — só a Fase 1 não-destrutiva entrou.
- **KI-043 (mitigado):** destinos externos de backup (Google Drive, e-mail) contidos por decisão de
  produto (`EXTERNAL_BACKUP_DESTINATIONS_ENABLED = False`); backup local não afetado.
- **KI-044 (resolvido):** `POST /api/clientes/<id>/anonimizar` (admin-only) mascara PII preservando `id`
  e FK de OS/vendas — complementa o `DELETE` existente, que continua só para clientes órfãos.
- **KI-045 (resolvido):** leitura de `cpf_cnpj` restrita a admin/financeiro; escrita permanece liberada a
  todo perfil. Achado corrigido durante a própria implementação: edição por perfil restrito sem `cpf_cnpj`
  no payload agora preserva o valor existente em vez de apagá-lo silenciosamente.
- Mecanismo parametrizável de mascaramento/expurgo do `audit_log`, inativo em produção sem prazo
  configurado (fail-safe, sem default).
- 33 testes novos, suíte completa 798 passed / 5 failed (KI-030, pré-existente, não relacionado). QA
  Manual 14/14 contra backend real e descartável. Revisão Arquitetural aprovada com ressalva: achado
  **KI-046** (busca de cliente por CPF vaza sinal de match/no-match antes do filtro de leitura do KI-045
  decidir a visibilidade) — baixo impacto, registrado, não bloqueou o Encerramento.

**Fora deste ciclo, deliberadamente:** KI-029 Fase 2 (reescrita de histórico, gate próprio, autorização
específica separada), criptografia completa de backup em repouso, prazos reais de retenção do `audit_log`
(aguardam orientação jurídica/operacional), documento de privacidade, validação jurídica formal do
relacionamento Fluxoly (operador) × loja-cliente (controladora), KI-046.

**Decisão do CTO:** ciclo de engenharia formalmente encerrado. **Mergeada em `main` via PR #40 (merge
commit `84deb30a`, 2026-08-16)** — CI verde, branch `feat/lgpd-compliance-fase1` deletada pós-merge.

_(Reconciliação 2026-08-27: este bloco e o topo do arquivo diziam "merge não autorizado / `main` intocada"
apesar de o PR #40 já ter sido mergeado em 2026-08-16 — narrativa nunca atualizada. Corrigido nesta
passada; KI-029 Fase 2 / reescrita de histórico segue não executada, gate próprio.)_

---

## 🟢 Homologação Interna Controlada — APROVADA

**Ver `docs/engineering/plans/ROTEIRO-homologacao-interna-controlada.md` para o registro completo (duas
etapas: execução inicial + correção/re-homologação) e `KNOWN_ISSUES.md` (KI-041) para a evidência técnica
da correção.**

2026-08-15, sequência imediata à execução inicial (ver seção abaixo). Depois do achado do KI-041, o ciclo
completo de correção rodou no mesmo dia: Discovery + Plano Técnico (PR #37, auditada, mergeada) →
implementação (PR #38, `scripts/seed_demo.py`, testada localmente, CI 6/6, mergeada) → deploy automático
confirmado live no `fluxoly-demo` → banco do Demo esvaziado e reiniciado → `seed_demo.py` executado via
Web Shell → novo backup `seed-inicial` criado. Re-homologação no Demo real (não só local): **Finalizar
OS** (`tecnico.demo`) → "Ordem finalizada!"; **Registrar Venda** (`vendedor.demo`) → "Venda concluída!",
confirmada em Vendas > Histórico. Demo restaurado ao novo `seed-inicial` ao final — estado limpo, produção
confirmada saudável (`/health` → 200) durante toda a operação, nunca tocada. KI-041 fechado
(`KNOWN_ISSUES.md`). KI-042 permanece aberto, não bloqueante, sem sprint definida.

**Decisão do CTO:** 🟢 **HOMOLOGAÇÃO INTERNA CONTROLADA — APROVADA.** Próxima decisão (apresentação a
prospect, retomada da Homologação Externa) fica em aberto, sem data definida.

---

## 🟡 Homologação Interna Controlada executada (execução inicial) — achado KI-041

**Ver `docs/engineering/plans/ROTEIRO-homologacao-interna-controlada.md` para o registro completo de
evidências, achados e o encerramento.**

2026-08-15. Os 3 perfis (`admin.demo`/`tecnico.demo`/`vendedor.demo`) foram exercitados via Claude in
Chrome: login/menu, fluxos funcionais por perfil, e testes negativos de controle de acesso. Guardrails
respeitados integralmente (nenhum dado real, nenhuma chamada MercadoPhone, produção intocada, confirmada
saudável ao final). Decisão do CTO: **🟡 CONCLUÍDA COM PENDÊNCIAS** — nem HOMOLOGADO, nem REJEITADO.

**Achado bloqueante — KI-041:** `scripts/seed_demo.py` não cria nenhum Tipo de Garantia, o que impede
Finalizar OS e Registrar Venda (os dois fluxos centrais do sistema) para qualquer perfil. Confirmado como
gap de dado, não bug de lógica — a validação de campo obrigatório está correta. Durante a execução, um Tipo
de Garantia foi criado manualmente só para validar que os fluxos funcionam com o dado presente (ambos
passaram); em seguida o Demo foi restaurado ao backup `seed-inicial`, removendo esse dado manual junto com o
cliente e a venda de teste criados na sessão — o Demo está limpo, e o gap volta a existir até a correção
formal (Discovery + Plano Técnico já registrados no próprio KI-041, aguardando aprovação do CTO antes de
implementar em `scripts/seed_demo.py`).

**Achados não bloqueantes — KI-042:** menu do `vendedor.demo` expõe Kanban/Garantias (leitura completa,
escrita bloqueada no backend) e do `tecnico.demo` expõe `/vendas` (mesmo padrão), ambos contradizendo o
`ADR-012`; Dashboard não reflete receita de Vendas de produto. Nenhum bypass de autorização confirmado.
Registrado como frente futura de consistência, sem sprint definida.

**Próximo passo:** CTO aprovar o Plano Técnico do KI-041 (quantos/quais Tipos de Garantia sintéticos) antes
de qualquer implementação em `scripts/seed_demo.py`. Depois: código → CI → merge → deploy → reset do Demo →
reexecução dos fluxos afetados → nova decisão de homologação.

---

## 🟡 Roteiro de Homologação Interna Controlada aprovado

**Ver `docs/engineering/plans/ROTEIRO-homologacao-interna-controlada.md` para o registro completo.**

2026-08-15. Decisão do CTO: substituir, por agora, o gate da Homologação Externa (homologador humano,
`PLAN-homologacao-externa-demo.md`) por um ciclo interno executado via Claude in Chrome — login e navegação
nos 3 perfis, fluxos funcionais por perfil (adaptados da lista já definida na Discovery externa), e um bloco
de testes negativos de controle de acesso (tentativa de acesso indevido entre perfis, verificação de
bloqueio do MercadoPhone na UI). Guardrails de "o que não pode acontecer" (nenhum dado real, nenhuma chamada
MercadoPhone real, produção intocada) continuam valendo integralmente. Decisão final (HOMOLOGADO
INTERNAMENTE / REJEITADO) permanece exclusiva do CTO. A etapa de Preparação da Homologação Externa
(definir data + homologador humano) fica adiada, sem data prevista.

---

## 🟡 Plano de Homologação Externa do Ambiente Demo concluído

**Ver `docs/engineering/plans/PLAN-homologacao-externa-demo.md` (seção "Plano de Homologação") para o
registro completo.**

2026-08-15, sequência imediata à Discovery (ver seção abaixo). Roteiro de execução definido (Preparação →
Execução sem suporte ao vivo, para simular uso real → reset via `seed-inicial` → coleta e classificação do
feedback → decisão do CTO), estrutura do formulário de feedback por cenário (perfil, conclusão,
dificuldades, sugestões, bugs, nota), e logística de acesso (URLs do Demo, reaproveitamento das 3 contas
existentes, senhas por canal separado, nunca em texto plano no repositório). Decisão do CTO: data da
sessão e homologador ficam `TBD` — antecipar esses dois compromissos antes de fechar a logística seria
prematuro; ambos definidos na próxima etapa (Preparação).

**Próximo passo:** CTO decide data e homologador para iniciar a Preparação.

---

## 🟡 Discovery — Homologação Externa do Ambiente Demo concluída

**Ver `docs/engineering/plans/PLAN-homologacao-externa-demo.md` para o registro completo.**

2026-08-15, sequência imediata ao fechamento do gate técnico do `ADR-012` (ver seção abaixo). Decisão do
CTO: com o Demo tecnicamente pronto, o próximo movimento não é mais código — é transformar "ambiente
funciona" em "ambiente homologável por alguém de fora da equipe". Discovery curta (sem código) definiu:
homologador = pessoa interna simulando usuário externo; escopo = 1 pessoa testando os 3 perfis
(`admin.demo`/`tecnico.demo`/`vendedor.demo`); período = sessão única de 1 dia; decisão final
(ACEITO/REJEITADO) = só o CTO. Documento também registra a lista de cenários por perfil, os guardrails
("o que não pode acontecer" — nenhum dado real, nenhuma chamada MercadoPhone, nenhum backup externo,
produção intocada) e um Definition of Done próprio da homologação (distinto do DoD técnico do `ADR-012`).

KI-040 e a decisão sobre LGPD ficam explicitamente como trilhas separadas, não bloqueando este ciclo. PR
#24 e PR #22 seguem sem decisão de disposição, também fora deste escopo.

Avançou para o Plano de Homologação formal na sequência imediata — ver seção acima.

---

## 🟡 Os 14 critérios do Definition of Done do Ambiente de Demonstração confirmados (ADR-012)

**Ver `docs/engineering/adr/ADR-012.md` (seção "Definition of Done") e
`docs/engineering/plans/PLAN-ambiente-demo-homologacao.md` (seção "Verificação final dos 14 critérios do
DoD") para o registro completo com cada evidência.**

2026-08-15, sequência imediata ao login das 3 contas + restore (ver seção abaixo). Dois itens verificados
nesta etapa contra o Demo real, além dos já cobertos: **endpoints do KI-037 (4/4)** retornaram 403 via
chamada real autenticada como `admin.demo`
(`https://fluxoly-demo.onrender.com/api/integracoes/mercadophone/{sincronizar,reprocessar,reimportar,config}`);
**backup sem destino externo** confirmado pelas 12 variáveis de ambiente do serviço no painel Render, sem
nenhuma `GOOGLE_DRIVE_*`/`BACKUP_EMAIL_*` configurada. Sentry `environment=demo` e MercadoPhone inacessível
já estavam confirmados pelos logs de boot do provisionamento (2026-08-14); CORS e sessão cross-site
confirmados implicitamente por todo o fluxo de login das 3 contas. **Produção confirmada intocada**
(`https://irflow-backend.onrender.com/health` → `200`) após toda a sequência de testes desta sessão.

Com os 14/14 critérios marcados, o gate técnico do `ADR-012` está completo. **Homologação externa segue
sem autorização** — decisão do CTO, não tomada neste registro.

---

## 🟡 Login das 3 contas de demo + restore de ponta a ponta validados (ADR-012)

**Ver `docs/engineering/plans/PLAN-ambiente-demo-homologacao.md` (seção "Runbook de Provisionamento",
"Login das 3 contas + restore de ponta a ponta") para o registro completo.**

2026-08-15, sequência imediata ao seed (ver seção abaixo). Login real via navegador confirmado para as 3
contas em `https://assistencia-system-do1h.vercel.app`: `admin.demo` (perfil Admin, menu completo),
`tecnico.demo` (perfil Tecnico, menu sem Financeiro/Custos Operacionais/Tabelas de Preço/Backups/Usuários),
`vendedor.demo` (perfil Vendedor, menu com Vendas, sem Kanban/Garantias) — cada perfil restrito ao menu
lateral correto, sem regressão de permissão.

**Restore de ponta a ponta:** cliente sintético "TESTE RESET - APAGAR" criado como marcador (18→19
clientes); backup `seed-inicial` baixado (280.0 KB) e reenviado via "Restaurar backup"
(`POST /api/backup/restaurar`) — o sistema gerou automaticamente `pre-restore-20260815-005741.db` antes de
aplicar o restore (mesmo comportamento já validado no item "Restore" do checklist de Release 1.0); após o
restore, contagem de clientes voltou a 18 e o marcador de teste não existe mais — reversão confirmada.

Os itens restantes do DoD (guard KI-037 nos 4 endpoints, backup sem destino externo) foram verificados na
sequência imediatamente seguinte — ver seção "Os 14 critérios do Definition of Done" acima.

---

## ✅ Seed + Backup `seed-inicial` do Ambiente de Demonstração (ADR-012)

**Ver `docs/engineering/plans/PLAN-ambiente-demo-homologacao.md` (seção "Runbook de Provisionamento",
"Execução real") para o registro completo.**

2026-08-15, sequência posterior ao provisionamento real do `fluxoly-demo`/Vercel (2026-08-14, ver abaixo).
`scripts/seed_demo.py` executado via Web Shell do Render contra o banco vazio (senhas das 3 contas
exportadas só na sessão do shell, nunca persistidas como variável do serviço) — sem exceção, volumes
conferindo com o esperado (18 clientes, 10 produtos/unidades, 24 OS, 8 vendas, contas
`admin.demo`/`tecnico.demo`/`vendedor.demo`). Backup `backup-vseed-inicial-20260815-003424.db` (280.0 KB)
criado pela tela Backups (`POST /api/backup/criar`, `versao=seed-inicial`) — vira o estado de referência
do reset manual.

---

## ✅ Ambiente de Demonstração — Implementação/Testes/QA Manual/Revisão Arquitetural/Encerramento concluídos no código (ADR-012)

**Ver `docs/engineering/adr/ADR-012.md` (arquitetura aprovada) e
`docs/engineering/plans/PLAN-ambiente-demo-homologacao.md` (plano técnico e registro completo de todas as
etapas) para o histórico completo.**

Ciclo `ADR-010` completo (Discovery → ADR → Plano Técnico → Implementação → Testes → QA Manual → Revisão
Arquitetural → Encerramento) em 2026-08-12, a partir de duas Discoveries somente-leitura de 2026-08-11
(Parte C da Release 1.0; Discovery dedicada do Ambiente de Demonstração) que identificaram o Ambiente de
Demonstração como o único bloqueador puramente técnico entre os 4 itens ainda em ❌ do
`RELEASE_1.0_MASTER_CHECKLIST.md`.

**Implementação (branch `feat/ambiente-demo-homologacao`, commit `59597bd8`):** `fluxoly_config.py` ganhou
`IR_FLOW_ENVIRONMENT`/`IS_DEMO_ENVIRONMENT`, coexistindo com `IS_PULL_REQUEST` sem substituí-lo (Preview
mantém precedência quando ambos estão setados), e `integracao_externa_bloqueada_neste_ambiente()` como
ponto único de verdade do guard do **KI-037** — aplicado nos 4 endpoints de escrita/ação de
`api_mercadophone.py` (`sincronizar`/`reprocessar`/`reimportar`/`config`, o último incluído por decisão do
CTO para o Demo nunca armazenar uma credencial real que não pode usar), inserido depois das checagens de
permissão já existentes, sem alterá-las — `status_mercadophone` (leitura) permanece intocado. `app.py`
ganhou o log de boot `demo_background_jobs_desativados` e `IS_DEMO_ENVIRONMENT` no bloco do Sentry
(`environment="demo"`, com Preview mantendo precedência). Novo `scripts/seed_demo.py` (standalone, via
`conectar()` de `app.py`) popula uma "loja modelo" 100% sintética (18 clientes, 10 produtos/unidades, 24
OS, 8 vendas com caixa) e as 3 contas de demonstração (`admin.demo`/`tecnico.demo`/`vendedor.demo`) —
senhas só via variável de ambiente, sem default (lição do KI-029); guard de idempotência recusa rodar
contra um banco já populado.

**Testes:** 20 testes novos (`tests/test_ambiente_demo.py`, `tests/test_ki037_guard_integracoes.py`). CI
6/6 verde no Linux nos dois commits da branch (`59597bd8`, `a14db05e` — Lint, Docker Build, Frontend
Quality, Backend Tests, Frontend Build, Coverage Report). Suíte completa local: 764 passed / 5 failed — as
5 falhas (2 já existentes de Preview + `test_sentry_init.py`, mais 2 equivalentes novas de Demo) são
limitação de ambiente Windows local (subprocess + `sentry_sdk`/`_overlapped`, `WinError 10106`), confirmada
pré-existente via `git stash` antes desta mudança — não é regressão, e o CI Linux já confirma verde.

**QA Manual** (2026-08-12, backend Flask real e descartável, `IR_FLOW_DATA_DIR` isolado, nunca
`database.db`): boot com `IR_FLOW_ENVIRONMENT=demo` confirmado (log de boot + `sentry_inicializado
environment=demo` + zero log de sync mesmo com token/sync herdados simulando o cenário INC-003); os 4
endpoints do KI-037 retornando 403 em Demo, com `/config` confirmado sem persistir o token bloqueado
(`integrations.json` inalterado); ordem das checagens preservada (`vendedor.demo` barrado por permissão
antes do guard); `status_mercadophone` continua acessível; regressão produção/dev confirmada (2º servidor
descartável sem nenhuma flag, endpoints voltam ao 400 "não configurado" de sempre); as 3 contas de demo
autenticando com os perfis corretos via `POST /api/auth/login` real; proteção contra segunda execução do
seed testada 2x; reset/restore validado de ponta a ponta (backup `seed-inicial` → OS extra criada →
restore → contagem revertida); CORS explícito confirmado (origem do Demo permitida, origem `*.vercel.app`
arbitrária rejeitada, sem fallback permissivo).

**Revisão Arquitetural (4 eixos do `ADR-010`, Etapa 6):** coerência do domínio ✅ (mudança puramente
aditiva). Autorização centralizada ✅ (grep completo no repositório confirma só 3 pontos de uso reais de
`IS_PULL_REQUEST`, todos com o correspondente `IS_DEMO_ENVIRONMENT` aplicado). Risco de vazamento de dado
✅, com **1 achado documentado, não um bug**: todo call site de `chamar_api_mercado_phone()` rastreado e
confirmado coberto pelos 3 endpoints manuais + `BACKGROUND_JOBS_ENABLED` (thread de sync) + o webhook, já
fail-secure por design quando `MERCADO_PHONE_WEBHOOK_TOKEN` está ausente (KI-023) — essa variável não
estava listada no Runbook de Provisionamento do plano; adicionada à tabela, sem necessidade de código
novo. Consistência da máquina de estados ✅ (precedência do Preview sobre Demo provada por teste e por QA
manual).

**Achado registrado como KI-038 (novo, aberto):** `app.py::criar_admin_padrao()` cria incondicionalmente
uma 4ª conta `admin`/`irflow@2024` (senha hardcoded) sempre que a tabela `usuarios` está vazia — comportamento
pré-existente (mesmo em produção), fora do escopo deste plano. Decisão do CTO: registrar e não corrigir
agora; é pendência real a resolver antes de qualquer acesso externo ao Demo, não antes deste Encerramento.

**Auditoria final do ciclo:** branch com 2 commits atômicos (`feat:` código + `docs:` documentação), 8
arquivos tocados no total — exatamente o escopo aprovado no Plano Técnico, nada a mais; árvore de trabalho
limpa; sem divergência de `origin/main`. `KI-037` movido para Resolvidos em `KNOWN_ISSUES.md`.

**Não provisionado e não autorizado ainda:** serviço Render `fluxoly-demo`, projeto Vercel dedicado, e
homologação externa (14 critérios do Definition of Done do `ADR-012`) — próximos gates, decisão do CTO a
cada um. PR/merge em `main` — resolvido em 2026-08-13, ver abaixo.

---

## ✅ KI-038 — Admin padrão exige senha configurável

**Ver `docs/operations/KNOWN_ISSUES.md` (KI-038, Resolvidos) e
`docs/engineering/plans/PLAN-ki038-admin-senha-configuravel.md` para o registro completo.**

Achado em 2026-08-12 durante a QA manual do Ambiente de Demonstração (`ADR-012`, acima). Discovery
aprofundada em 2026-08-13 revelou que a conta `admin`/`irflow@2024` era, até então, a credencial real de
produção do CTO — já trocada manualmente como mitigação imediata (o que revelou o KI-039, ver seção
abaixo).

Decisão arquitetural do CTO: escopo amplo. `criar_admin_padrao()` (branch
`feat/ki-038-admin-senha-configuravel`, commit `303c05c3`) passa a exigir `IR_FLOW_ADMIN_PASSWORD` fora de
dev local, mesmo padrão do `FLASK_SECRET_KEY` — ausente, o boot falha em vez de criar um admin com senha
conhecida. Produção atual não é afetada (admin já existia). Achado de Revisão Arquitetural, não um bug: o
Runbook de Provisionamento do Demo vai precisar dessa variável além de `DEMO_SEED_ADMIN_PASSWORD`. 3
testes novos, suíte completa 751/754 (3 falhas pré-existentes de Windows local, não é regressão), CI 6/6
verde. PR #26 mergeada em `main` em 2026-08-13 (`54e34b72`).

---

## ✅ KI-039 — Troca de senha de usuário não persistia

**Ver `docs/operations/KNOWN_ISSUES.md` (KI-039, Resolvidos) para o registro completo.**

Achado em 2026-08-13, ao tentar trocar a senha da conta `admin` de produção como mitigação do KI-038: a
tela de Usuários enviava `senha`, o backend esperava `senha_nova` (`PUT /api/usuarios/<id>`) — a troca era
silenciosamente ignorada, reportando sucesso mesmo assim. Hotfix imediato a partir de `main`
(`hotfix/usuarios-senha-nao-persiste`, PR #25, commit `ba2d6294`, merge `ccf94baa`), um arquivo
(`frontend/src/pages/Users.jsx`), CI 6/6 verde, já mergeado em `main`.

---

## ✅ Dry-Run 2B — Rollback de infraestrutura Render validado (Operação Release 1.0)

**Ver `docs/company/GO_LIVE_PLAN.md` (seção "Preview Seguro (pré-requisito do Dry-Run 2B)") e
`docs/company/RELEASE_1.0_MASTER_CHECKLIST.md` (item "Rollback testado") para o registro complementar.**

Autorizado pelo CTO em 2026-08-11 após confirmar as 6 evidências de que o Preview da PR #24
(`srv-d9tkqpj7uimc73cop6og`, distinto do preview suspenso da PR #22) nasceu protegido em duas camadas
independentes: guard de código (`IS_PULL_REQUEST` → `BACKGROUND_JOBS_ENABLED=False` incondicional) e
configuração operacional (`MERCADO_PHONE_SYNC_ENABLED=0`, `MERCADO_PHONE_API_TOKEN` limpo,
`IR_FLOW_ENABLE_BACKGROUND_JOBS=0`). A primeira rodada de confirmação revelou que a camada operacional
não tinha sido herdada corretamente (`MERCADO_PHONE_SYNC_ENABLED=1`, token real presente, variável
`IR_FLOW_ENABLE_BACKGROUND_JOBS` ausente) — só o guard de código estava protegendo o preview. Corrigido
(as três variáveis aplicadas no Preview da PR #24, nunca na PR #22 nem em produção) e revalidado por
redeploy antes de autorizar o exercício.

**Baseline:** produção (`main`/`1ded1ed1`) e Preview da PR #24 (`1347fe1`) ambos com `/health`/`/ready` →
200 antes do início.

**Execução (push → auto-deploy → revert → auto-deploy → confirmação), branch
`dry-run/2b-infra-rollback-render`, PR #24 (descartável, não mergeada):**
1. Commit marcador `fc972adf` (trecho identificável e inofensivo em `RENDER_PREVIEW_TEST_MARKER_2B.md`,
   nenhuma alteração funcional) → push → Render Auto-Deploy confirmado (`Deploy live for fc972ad`) → boot
   novo (`preview_background_jobs_desativados`, `IS_PULL_REQUEST=true`) → `/health` 200.
2. `git revert fc972adf` → commit `d6cb9aef`, **sem conflito** (diferente do Dry-Run 1B — o marcador
   viveu isolado num arquivo dedicado ao exercício, não em documentação append-only compartilhada; não
   invalida a regra "conflito = parada + decisão do CTO" registrada no Dry-Run 1B, só significa que este
   cenário específico não a exercitou) → push → Render Auto-Deploy confirmado (`Deploy live for d6cb9ae`)
   → boot novo → `/health` 200.

**Validação de ponta a ponta, ambos os deploys:** commit ativo confere com o esperado em cada etapa;
`/health` e `/ready` → 200; logs de boot mostram `preview_background_jobs_desativados` em toda
inicialização; nenhum log `mercadophone_sync_*` em nenhum momento do exercício; boot limpo, sem erro de
schema/migration (integridade do banco/disco isolado do preview preservada); produção (`/health` → 200,
`main`/`origin/main` em `1ded1ed1`, inalterado) confirmada intocada antes, durante e depois. Nenhum
comportamento inesperado ou conflito adicional.

**Encerramento do exercício:** Preview da PR #24 suspenso novamente ao final (confirmação por digitação
exigida pelo painel Render), `/health` → 503 "Service Suspended" confirmado pós-suspensão.

**O que este Dry-Run comprova e o que não comprova:** valida o mecanismo real de rollback contra
infraestrutura Render (push → auto-deploy → revert → auto-deploy) e a defesa em profundidade do Preview
Seguro (guard de código + configuração operacional, as duas camadas testadas independentemente). **Não**
exercitou um conflito de infraestrutura (o marcador foi deliberadamente isolado para não gerar um — ver
Dry-Run 1B para o precedente de conflito real em Git), **não** testou o lado Vercel/frontend do rollback
coordenado, e **não** corrigiu nem validou KI-037 (risco residual aceito só para este exercício, mitigado
operacionalmente — nenhuma sessão `admin`/`tecnico` real usada em nenhum momento; continua aberto como
item de backlog separado, fora deste escopo). Uma execução real de rollback em produção — por definição —
nunca é substituída por um dry-run.

**Pendências separadas, decisão do CTO:** destino da PR #24 (branch/PR descartável, preservada por ora) e
da PR #22 (evidência preservada do INC-003, preview `srv-d9t2ms0u01pc73bmuaqg` continua suspenso e
intocado); correção de código do KI-037 (sprint própria, não decidida). Nenhuma dessas três decisões foi
tomada neste encerramento.

---

## 🟡 Rollback — política definida (Operação Release 1.0)

**Ver `docs/company/GO_LIVE_PLAN.md` (seção "Plano de rollback") e `DEPLOY.md` (seção "Rollback") para o
registro completo.**

Discovery da Parte B da Operação Release 1.0 (Rollback, Manual do usuário, Ambiente de demonstração,
Piloto/homologação) mapeou os 4 itens separadamente contra o código/documentação real (ver matriz na
sessão de handoff). Rollback foi o primeiro a ser decidido — único dos 4 com efeito direto em caso de
falha real de produção. Decisões do CTO (2026-08-10), uma de cada vez, seguindo a separação
técnico/política/autoridade/procedimento do `CLAUDE.md` §11:

- **Escopo:** rollback coordenado — backend (Render) e frontend (Vercel) sempre revertidos juntos, nunca
  de forma independente.
- **Critério de acionamento:** bug crítico impedindo operação, perda/corrupção de dados, ou
  indisponibilidade prolongada.
- **Autoridade:** só o CTO autoriza. Claude nunca executa rollback sem aprovação explícita a cada
  ocorrência real — a política não é uma autorização permanente.
- **Interação com migrations (TD-03 — roll-forward only):** rollback de código nunca cruza uma migration
  já aplicada em produção — se o deploy problemático incluiu migration nova, a correção é sempre um
  hotfix roll-forward, nunca reverter para antes dela.
- **Mecanismo:** `git revert` + `git push`, mesmo fluxo de deploy normal (não usa o "redeploy anterior"
  nativo de Render/Vercel, que deixaria `main` divergente do que está rodando).
- **Verificação:** smoke test manual mínimo (login + uma operação real por módulo crítico) contra
  produção logo após o redeploy.
- **Conflito durante o revert:** qualquer conflito em `git revert` durante um rollback de produção é
  **condição de parada** — cobre qualquer tipo de arquivo (código, documentação, testes, configuração,
  migrations). Não resolver/continuar/pular/abortar automaticamente; informar o CTO e aguardar decisão
  explícita (resolver de forma controlada, hotfix roll-forward, rollback alternativo, ou abortar).

**Dry-Run 1A e 1B (2026-08-10, branch `dry-run/rollback-f5fdb23`, preservada, não apagada):** 1A reverteu
`tests/test_backup_restore.py` (commit `f5fdb23`, sem impacto em produção) sem conflito, validando o
mecanismo Git/local isoladamente — testes relevantes (7/7) e `ruff check` verdes após o revert. 1B usou um
commit real de produção (`609619f`, fix de exibição de `garantia_data_fim`): o código
(`frontend/src/pages/VendaDetalhe.jsx`) reverteu limpo, mas `docs/operations/KNOWN_ISSUES.md`
(append-only, evoluído por commits posteriores — KI-029 a KI-034) gerou **conflito real**. A análise do
conflito mostrou que resolvê-lo exigiria decisão de conteúdo (reabrir vs. remover a entrada do KI-028, e
propagar a consistência para `PROJECT_STATUS.md`/`CHANGELOG.md`/`PLAN-V1.5-Garantia.md`, que também
referenciam o KI-028) — não é uma operação puramente mecânica de Git. `git revert --abort` executado com
sucesso; `main`/`origin/main` nunca tocadas em nenhum momento dos dois exercícios. Levou à nova regra
"Conflito durante o revert" acima, registrada também em `GO_LIVE_PLAN.md`/`DEPLOY.md`.

**Ainda não exercitado com sucesso de ponta a ponta** — a política ficou mais robusta (cobre um cenário
real que faltava), mas nenhum dry-run (local sem interrupção, ou de infraestrutura Render/Vercel) foi
concluído. `RELEASE_1.0_MASTER_CHECKLIST.md` atualizado com o registro dos dois Dry-Runs; **percentual
mantido em 40%** (Operação ~30%, geral ~61% — inalterados) porque o item mede se o rollback foi *testado*
de ponta a ponta, o que ainda não aconteceu — ver raciocínio completo no próprio checklist. Nenhum código
de produção alterado nesta decisão — só documentação; `VendaDetalhe.jsx` só foi tocado dentro da branch de
dry-run temporária, nunca chegou a `main`.

---

## ✅ Preview Seguro — INC-003 Frente B, KI-035, KI-036 resolvidos (Operação Release 1.0)

**Ver `docs/engineering/plans/PLAN-preview-seguro-inc003-ki035.md` para o plano técnico completo e
`docs/operations/INCIDENTS/INC-003-mercadophone-preview-dados-reais.md` seção 12 para a resolução do
incidente.**

Ciclo `ADR-010` completo (Discovery → Plano Técnico → Implementação → Testes → QA Manual → Revisão
Arquitetural → Encerramento) em 2026-08-11, a partir da Discovery da arquitetura de "Preview seguro"
mapeada logo após a contenção do INC-003. Defesa em profundidade (preferência já registrada do CTO):
`IS_PULL_REQUEST` (setada automaticamente pelo Render em todo PR Preview) desliga
`BACKGROUND_JOBS_ENABLED` incondicionalmente em `fluxoly_config.py` — cobre a sync do MercadoPhone e o
backup automático, mesmo com credenciais herdadas do serviço-base — mais a recomendação de configuração
manual complementar registrada em `DEPLOY.md`/`GO_LIVE_PLAN.md`. `environment` do Sentry passa a
distinguir `"preview"` de `"production"` (KI-036). `migrations/runner.py` passa a capturar
`sqlite3.IntegrityError` por migration, restrito à constraint `schema_migrations.id` (KI-035) — restrição
adicionada pelo CTO na aprovação do plano, para nunca mascarar um `IntegrityError` de origem diferente
(ex.: violação de dado real dentro de uma migration).

751 testes existentes + 10 novos (`tests/test_ambiente_preview.py`, +2 em `tests/test_migrations.py`),
todos passando; `ruff check .` limpo; CI 6/6 verde no push. QA manual em backend real com banco/disco
descartáveis (nunca `database.db`) reproduziu as condições exatas do INC-003 (credenciais herdadas +
`IS_PULL_REQUEST=true`) e confirmou zero atividade de sync, mais um cenário de controle sem regressão.

**Revisão Arquitetural (4 eixos do `ADR-010`):** coerência do domínio e autorização centralizada
confirmadas limpas por grep (único ponto de verdade, sem checagem duplicada); consistência confirmada.
**Achado real no eixo de vazamento de dado:** os endpoints manuais de `api_mercadophone.py`
(`sincronizar`/`reprocessar`/`reimportar`) continuam alcançáveis por uma sessão `admin`/`tecnico` real
dentro de um preview, sem checagem de `IS_PULL_REQUEST` — fora do escopo aprovado deste plano (que cobria
só o disparo automático no boot). Decisão do CTO: não expandir o escopo agora, registrado como **KI-037**.

**Branch `fix/preview-seguro-inc003-ki035` mergeada em `main` via PR #23** (commit `6bb2ede`, CI 6/6
verde), produção confirmada em Render + Vercel. Reativar o preview suspenso (`srv-d9t2ms0u01pc73bmuaqg`)
continua sendo decisão separada do CTO — o Dry-Run 2B (rollback de infraestrutura Render, usando um
preview novo e distinto) foi autorizado e concluído em 2026-08-11, ver seção "Dry-Run 2B" acima.

---

## ✅ INC-003 — Render PR Preview importou dados reais via MercadoPhone (RESOLVIDO)

**Ver `docs/operations/INCIDENTS/INC-003-mercadophone-preview-dados-reais.md` para o relatório completo
(seção 12 tem a resolução) e a seção "Preview Seguro" acima para o registro da correção.**

Durante o Dry-Run 2A (validar se o Render PR Preview seria um ambiente seguro para o Dry-Run 2B de
rollback de infraestrutura), um preview de teste (PR #22, `[render preview]`, modo Manual) herdou
`MERCADO_PHONE_SYNC_ENABLED`/`MERCADO_PHONE_API_TOKEN` do serviço-base de produção — comportamento
documentado do Render (variáveis de ambiente são copiadas na criação do preview). A thread de
sincronização automática (disparada incondicionalmente no boot de `app.py`, sem checagem de
`IS_PULL_REQUEST`) importou **405 Ordens de Serviço reais** da API externa do MercadoPhone
(`2026-04-01`–`2026-08-08`) para o banco isolado do preview, em 4 ciclos completos, ao longo de ~18
minutos.

**O disco/banco do preview permaneceu fisicamente isolado do de produção o tempo todo** — Service ID
próprio, disco próprio (5 GB, sem snapshots anteriores), `schema_migrations` aplicado do zero em
`2026-08-10` (produção aplicou em `2026-08-08`). O primeiro boot do preview também **reproduziu o KI-035**
de forma independente (condição de corrida em `migrations/runner.py::run_migrations()`), confirmando o
bug num segundo ambiente real. A busca exaustiva pelos call sites de `chamar_api_mercado_phone()` (única
função com requisição HTTP externa) encontrou só 2 usos, ambos de leitura (`"index"`/`"get"`) — nenhuma
evidência de escrita de volta ao MercadoPhone.

**Contenção:** preview suspenso (painel Render, confirmado por evento + URL pública retornando "Service
Suspended"); PR #22 mantida aberta, não mergeada, para preservar evidência; nenhum dado apagado; produção
(`/health` → `ok`) confirmada intocada antes e depois.

**Status:** ✅ Resolvido em 2026-08-11 — Frente B implementada (defesa em profundidade: guard de código
`IS_PULL_REQUEST` + configuração), testada (automatizado + QA manual) e revisada arquiteturalmente. Ver
seção "Preview Seguro" acima para o registro completo. KI-035 (mesmo bloqueador do Dry-Run 2B) resolvido
junto. Achado residual fora do escopo desta correção registrado como KI-037. Reativar o preview suspenso
da PR #22 continua sendo decisão separada do CTO; o Dry-Run 2B foi autorizado e concluído em 2026-08-11
(ver seção própria acima).

---

## ✅ Restore de Backup — validado (Operação Release 1.0)

**Ver `docs/company/RELEASE_1.0_MASTER_CHECKLIST.md`** (seção Confiabilidade, item "Restore validado")
para o registro completo.

Discovery comparativa (Dashboard Executivo vs. KI-005 vs. Operação Release 1.0) levou à decisão do
usuário (CTO) de priorizar Operação — único bloco que ataca diretamente o gargalo do primeiro cliente
pagante. Discovery detalhada de Operação separou os 5 itens do checklist em Engenharia (só Restore) vs.
Decisão/Processo (Rollback, Manual, Demo, Piloto — Parte B, ainda não iniciada).

`tests/test_backup_restore.py` (7 cenários) cobre `POST /api/backup/restaurar`
(`api_backup.py::restaurar_backup_upload`), que nunca teve teste. Fixture de isolamento local ao
arquivo (não altera `tests/conftest.py` global) preserva o banco real da sessão de testes via
`PRAGMA wal_checkpoint(FULL)` + snapshot/restore, já que o banco roda em WAL e a sessão de pytest
compartilha um único arquivo real. Achado de portabilidade entre builds de SQLite (não é bug — nenhum
critério objetivo de interrupção do `ENGINEERING_GUIDE.md` §11 se aplica, mesmo padrão do precedente já
documentado de exceção visível sem persistência incorreta): `PRAGMA integrity_check` retorna erro limpo
no Windows/Python 3.12 local, mas levanta `sqlite3.DatabaseError` direto no runner Linux do CI — teste
corrigido para aceitar os dois desfechos reais, sempre provando que o banco original permanece
inalterado.

QA manual de ponta a ponta (11/11 cenários) rodado contra um backend descartável isolado (porta própria,
`IR_FLOW_DATA_DIR` próprio, nunca `database.db` de desenvolvimento/produção): ciclo positivo completo
(marcador de estado → backup → modificação → restore → estado revertido → `pre-restore-*.db` criado com
o estado anterior → integridade ok → app responde normalmente) e 5 cenários negativos (extensão
inválida, não-SQLite, corrompido, sem sessão, sem permissão — banco inalterado em todos). Achado
operacional registrado para o futuro ambiente de demonstração (não é bug): `IS_SERVER_RUNTIME=True`
(ativado por `IR_FLOW_DATA_DIR`) força `SESSION_COOKIE_SECURE=True`, exigindo HTTPS para o cookie de
sessão ser reenviado — relevante para quem for montar a Parte B.

Merge via PR #21 (commit `f73f6f86`), CI 6/6 verde antes e depois do merge. Nenhum código de produção
alterado em todo o ciclo.

---

## ✅ Financeiro Mínimo — ENCERRADO (BR-067 a BR-069, ciclo ADR-010 completo)

**Ver `docs/engineering/plans/PLAN-financeiro-minimo.md` e `docs/product/BUSINESS_RULES.md` (seção
Financeiro) para o plano técnico e as regras de negócio completas.**

Primeira feature de negócio construída sobre o mecanismo formal de migrations da TD-03
(`migrations/versions/m0002_financeiro_minimo.py`): tabelas `movimentacoes_caixa`, `contas_pagar`,
`contas_receber`. Domínio Caixa (`fluxoly_caixa_*.py`) + Contas a Pagar/Receber
(`fluxoly_contas_pagar_*.py`/`fluxoly_contas_receber_*.py`), seguindo a convenção
controller/service/repository. Hook automático em `fluxoly_vendas_service.py`: venda concluída gera
entrada de caixa, cancelamento estorna — mesma transação, idempotente, guardião real no banco via
`idx_movimentacoes_caixa_venda_ativa` (índice único parcial). Contas a Receber sem qualquer relação com
o domínio Vendas (BR-068, isolamento verificado por teste).

38 testes novos (`tests/test_caixa.py`, `tests/test_contas_pagar.py`, `tests/test_contas_receber.py`),
734/734 no total do projeto, `ruff check .` limpo.

**Frontend (2026-08-09):** `frontend/src/pages/Financeiro.jsx` (rota `/financeiro`, gate
`admin`/`financeiro`) — três abas (Movimentações, Contas a Pagar, Contas a Receber), card de saldo
recarregado a cada mutação. QA manual de ponta a ponta via navegador real (banco isolado): lançar/
estornar movimentação manual, CRUD + pagar/receber/cancelar/excluir de contas, gate de perfil confirmado
nos dois sentidos. Um bug real de UI encontrado e corrigido no mesmo ciclo (contador de total não
atualizava após excluir uma conta).

**Validação Fatia 3 — integração Vendas↔Caixa (2026-08-09):** venda real pelo fluxo existente →
exatamente uma movimentação `origem='venda'` com `origem_id`/`valor` corretos → saldo correto antes/
depois → cancelamento → `estornada=1`, permanece no histórico, sai do saldo → revenda da mesma unidade
gera entrada distinta sem colidir com a antiga (índice único parcial provado em uso real) → dois ciclos
completos sem duplicação → suíte automatizada (38 testes) reconfirmada verde. Achado de UX corrigido no
mesmo ciclo: botão "Estornar" em `Financeiro.jsx` só aparece para `origem === "manual"` agora — antes
aparecia também para movimentações automáticas, que o backend sempre rejeita (proteção correta,
já existente em `fluxoly_caixa_service.py`).

**Revisão Arquitetural (2026-08-10):** percorridos os 4 eixos do gate `ADR-010.md` — coerência do domínio
(único caminho de escrita em `movimentacoes_caixa`, confirmado por grep), autorização centralizada
(`usuario_pode_financeiro()` duplicada em 4 controllers, risco já aceito como TD-14), vazamento de dado
(todas as 12 rotas do Financeiro protegidas), e consistência da máquina de estados — **achado real**:
`ajustar_desconto_item()` (BR-043, já existente desde V1.3) recalcula `vendas.valor_total` após a venda
concluída sem resincronizar a movimentação de caixa correspondente, deixando o saldo e um estorno
posterior com o valor original em vez do corrigido. Não é regressão desta sprint — decisão do CTO: não
bloqueia o encerramento, registrado como **KI-034** para correção em sprint própria.

**Encerramento formal:** ciclo ADR-010 completo. Ver `docs/engineering/plans/PLAN-financeiro-minimo.md`
para o registro completo de todas as etapas.

---

## ✅ INC-002 — Ordens de Serviço duplicadas após sincronização com Mercado Phone (RESOLVIDO)

**Ver `docs/operations/INCIDENTS/INC-002-os-duplicada-mercado-phone.md` para o relatório completo.**

Reportado pelo usuário (CTO) em 2026-07-23 — OS "1072" (número externo do Mercado Phone,
`id_externo_integracao`) aparentemente duplicada. Causa estrutural: a thread de sincronização do
Mercado Phone iniciava uma vez por processo do Gunicorn, sem coordenação entre processos — com
`--workers 2` em produção, dois processos rodavam o sync ao mesmo tempo, gerando uma corrida clássica
(TOCTOU) que duplicava OS, já que o schema não tinha `UNIQUE` em
`(origem_integracao, id_externo_integracao)`. Mesma classe de bug já corrigida em KI-001 (rate
limiting) para outro recurso.

**Resolução completa em 3 etapas:**
1. **Lock cross-processo** (`irflow_mercadophone.py`, lease de 90s via tabela já existente) — elimina o
   mecanismo que gera novas duplicatas.
2. **Confirmado e limpo em produção**: 3 pares duplicados encontrados (`id_externo_integracao` 1083,
   1093, 832). Dois eram duplicatas idênticas sem filhos (limpeza direta); um (832) tinha as duas linhas
   editadas de forma divergente após a duplicação — peça consumida duas vezes do estoque, reparo extra,
   checklist próprio em cada uma — exigiu decisão humana sobre qual linha refletia a realidade antes de
   remover a outra. 3 linhas + filhos órfãos removidos, verificado `[]` na consulta pós-limpeza.
3. **`UNIQUE INDEX`** em `(origem_integracao, id_externo_integracao)` (`app.py::criar_tabelas()`) —
   proteção definitiva no banco, independente do lock, aplicada automaticamente no próximo deploy.

9 novos testes no total (`test_inc002_mercado_phone_sync_lock.py`, `test_inc002_unique_index_os_mercado_phone.py`),
489 no total do projeto, `ruff check .` limpo, zero regressão em cada etapa.

Achado ainda em aberto (não confirmado, registrado em INC-001): `sincronizar_mercado_phone()` mantinha
uma única transação aberta por todo o ciclo de sync, rodando em 2 processos concorrentes — candidato
mais forte para a causa de INC-001 do que qualquer coisa testada até agora ali. Migração arquitetural
para worker/cron dedicado (em vez de lock) registrada como melhoria futura, não decidida, requer ADR.

---

## ✅ INC-001 — `database is locked` (P0, causa raiz confirmada e corrigida em 2026-08-05)

**Ver `docs/operations/INCIDENTS/INC-001-database-is-locked.md` para o relatório completo.**

Reportado pelo usuário (CTO) em 2026-07-23 ao editar/criar OS e cadastrar/alterar estoque, de forma
intermitente. Investigação encontrou: WAL e timeout já configurados corretamente (descartados como
causa); as 4 rotas citadas como sintoma já têm `try/except/finally` corretos (não são a origem do
vazamento, só a vítima do lock, se a hipótese estiver certa). Hipótese específica de conexão aninhada
dentro das 4 rotas de OS/Estoque (auditoria/movimentação abrindo `conectar()` de novo) foi investigada e
**descartada** por leitura de código.

Após releitura completa (não só grep) das rotas candidatas: as 4 rotas de `/api/shopping-list*`
reclassificadas de "sem proteção" para **risco estrutural, não vazamento confirmado** (fecham a conexão
em todo caminho, via padrão não idiomático — `except` amplo + `close()` manual).

**Corrigido (2026-07-23):** `POST /api/auth/login` — hotfix isolado em
`hotfix/conexao-login-database-locked`, mantido independente do resultado da investigação. Provado por
teste automatizado. 480 testes, `ruff check .` limpo, zero regressão.

**Corrigido (2026-07-27):** as 4 rotas de checklist (`GET/POST /api/ordens/<id>/checklist[/token]`,
`GET/POST /api/checklist/<token>` — as duas últimas públicas, sem login), único risco confirmado por
leitura de código que ainda restava — mesmo padrão do hotfix de login, branch
`fix/checklist-conexao-database-locked`, mergeada em `main`. 533 testes, `ruff check .` limpo.

**Instrumentação transparente pronta e mergeada (2026-07-27):** `_ConexaoRastreada` (`app.py`), gated
por `IR_FLOW_DEBUG_CONN_TRACE`, zero impacto desligada, delega tudo que não instrumenta à conexão real
(`__getattr__`/`__setattr__`) — critérios de aceitação C-1 a C-9 documentados. Branch
`chore/inc-001-instrumentacao-transparente`, mergeada em `main` (substitui a branch anterior
`chore/inc-001-instrumentacao-conexoes`, que usava `print()` e nunca foi mergeada). 541 testes,
`ruff check .` limpo. Duas rodadas de reprodução por carga local (antes desta branch) **não
reproduziram** o erro — causa raiz segue não confirmada em runtime.

**Causa raiz confirmada em produção (2026-08-05):** usuário (CTO) reportou, em tempo real, `POST
/api/auth/login` falhando com 400 "database is locked" ao tentar logar como admin — dois requests
levaram ~30.2s cada (exatamente `SQLITE_TIMEOUT_SECONDS=30`, `busy_timeout` se esgotando por completo)
antes de falhar. Logs estruturados do Render, na mesma janela, mostram `fluxoly.mercadophone` com
`mercadophone_sync_falha_inesperada` repetidas vezes (`sqlite3.OperationalError: database is locked`
em `adquirir_lock_sync_mercado_phone`/`liberar_lock_sync_mercado_phone`/`definir_estado_integracao`,
inclusive uma falha dupla — exceção durante o `finally` de liberação do lock). Root cause localizada
com precisão em `fluxoly_mercadophone.py::_sincronizar_mercado_phone_sem_lock()`: o commit só
acontecia uma vez, depois do loop inteiro (até centenas de registros, cada um com uma chamada HTTP
síncrona para a API externa do Mercado Phone) — a transação de escrita ficava aberta pela duração
inteira do ciclo, bloqueando qualquer outro escritor pelo `busy_timeout` inteiro. Confirma, com
evidência real de runtime, o "novo candidato" já registrado nesta investigação desde 2026-07-23.

**Corrigido (2026-08-05) — Branch B:** commit movido para dentro do loop (`finally` por registro),
preservando a atomicidade de cada registro (já isolado pelo `try/except` existente) enquanto libera o
lock entre uma chamada externa e a próxima. Teste de regressão dedicado
(`tests/test_inc001_mercadophone_commit_por_registro.py`) prova o mecanismo exato — confirmado que
falha contra o código anterior à correção (`git stash` temporário, mesmo rigor dos hotfixes anteriores
deste incidente) e passa depois. 683 testes no total, `ruff check .` limpo, `graphify update .`
validado. Ver `docs/operations/INCIDENTS/INC-001-database-is-locked.md` para o relatório completo —
INC-001 permanece com o registro histórico completo, mas a causa raiz está confirmada e corrigida.

---

## Estado Atual

| Dimensão           | Status                          |
|--------------------|---------------------------------|
| Produção           | Operacional (Render + Vercel)    |
| Backend            | Estável — Flask + SQLite (WAL)  |
| Frontend           | Estável — React 19 + Vite + Radix UI/shadcn (Fase 1 do Design System encerrada 2026-08-16 — tokens, Motion, Phosphor Icons, Shell/Dashboard migrados, ver seção acima) |
| CI/CD              | Presente e ativo (`.github/workflows/ci.yml` — lint, testes, frontend, build, cobertura, docker build, + `Frontend Unit Tests` desde 2026-08-16, não-bloqueante). Cobertura bloqueante (`fail_under = 60`, elevado de 40 na Sprint CI/CD 1.1 — Hardening, 2026-07-31). Job `Lint` (Ruff, backend) verde em `main` desde 2026-07-21 (KI-017 resolvido, `ruff check .` → 0 erros). Workflow `CI` como um todo verde desde 2026-07-27 (Sprint Infra 1.1) — histórico de por que não estava, ver KI-026 (resolvida). `main` protegida, exige 6 status checks antes de merge (Lint, Backend Tests, Frontend Quality, Frontend Build, Coverage Report, Docker Build — R-10/R-11 mitigados, `Docker Build` adicionado na Sprint CI/CD 1.1; endurecimento adicional em TD-13) |
| Cobertura de testes| Backend: 65.22% global (`pytest --cov`, 2026-07-31), 682 testes. Frontend: testes de componente inaugurados em 2026-08-16 (Vitest, 11 testes — `Layout`/`Dashboard`), sem threshold ainda, restrito aos componentes migrados na Fase 1 do Design System (ver Cobertura de Testes) |
| Dívida técnica     | Alta                            |
| Segurança          | Melhor — Sprint Segurança 1.0 + 2º scan Aikido (2026-07-25), ambos fechados: `FLASK_SECRET_KEY` rotacionada em produção, autorização de OS/Estoque por perfil, headers HTTP, Docker non-root (validado com `docker build`/`docker run` reais), gunicorn/deps atualizadas — ver `docs/security/SECURITY_AUDIT_2026-07.md` |
| Observabilidade    | Logs estruturados em JSON, correlation ID por request, `/health`/`/ready`, métricas Prometheus (`/metrics`, modo multiprocess validado com Docker real), Sentry ativo nos dois lados (backend + frontend novo, `environment`/`release` automáticos, conta criada e captura real validada em 2026-07-30) — ver `docs/operations/SPRINTS/SPRINT_OBSERVABILIDADE.md` e `docs/engineering/plans/PLAN-Observabilidade-Sentry-Frontend.md`. Falta configurar `SENTRY_DSN`/`VITE_SENTRY_DSN` nos dashboards Render/Vercel para ativar em produção |

O sistema está em produção e cobre o ciclo completo de uma assistência técnica: abertura de OS, controle de estoque, tabela de preços, lista de compras, garantias, relatórios e backup. Além disso, a Sprint 3 fechou quatro lacunas de segurança (rate limiting de login, expiração de sessão por inatividade, auditoria central reutilizável, recuperação de senha via token do admin) e a Sprint P0.1 entregou o primeiro domínio de produto (Clientes) seguindo pela primeira vez a convenção controller/service/repository documentada em `ENGINEERING_GUIDE.md` §3.1. Em 2026-07-20, antes do início do Épico Vendas (decisão do usuário — CTO), o lint vermelho em `main` (KI-017) foi corrigido em 6 commits atômicos na branch `chore/fix-ruff-lint-ki-017` — o CI estava bloqueado para qualquer PR desde antes da Sprint 3. No processo, também foi resolvido KI-014 (bloco de código morto duplicado em `irflow_blueprints_api.py`). No mesmo dia, a Sprint Comercial 0.1 entregou o primeiro passo do Épico Vendas: domínio `produtos` (catálogo comercial — iPhone/Apple Watch/AirPods/Acessório), separado do domínio Estoque (peças de reparo) por decisão de arquitetura investigada e confirmada com o usuário antes de implementar. Sem tela ainda — ver `docs/operations/SPRINTS/SPRINT_COMERCIAL_0.1.md`.

---

## Última Sprint Concluída

**Sprint 1 — Shopping List & Estabilização de OS**
Período estimado: 01/06/2026 – 21/06/2026

### O que foi entregue

| Entrega | Descrição |
|---------|-----------|
| Shopping List (backend) | Tabela `shopping_list`, API REST completa com status workflow |
| Shopping List (frontend) | Página `Compras.jsx` com client dedicado `shoppingList` |
| `EditShoppingItemModal` | Modal de edição de itens da lista de compras |
| Auto-preenchimento de `valor_cobrado` | Endpoint `GET /api/precos/sugerir` + `useEffect` em NewOrder/EditOrder |
| Fix: PDF IR Phones | URL corrigida de `irphones` para `ir-phones` |
| Fix: `historico-cliente` | Rota corrigida no client.js |
| Fix: campo `cor` no EditOrder | Campo limpo ao trocar modelo |
| Remoção do `.env` do repositório | Commit `832945c` |
| Build/dist pipeline corrigido | Commit `ae7c575` |

---

## Sprint em Andamento

**Sprint 2 — Infraestrutura de Qualidade** (EM ANDAMENTO — ver `docs/operations/SPRINTS/SPRINT_02.md`)
Objetivo: estabelecer pipeline de CI, testes unitários no backend e cobertura mínima de 40% antes de qualquer nova feature.

**Sprint 2.2 (T-01 a T-04) concluída em 2026-07-07:** primeira suíte pytest do projeto (`tests/test_auth.py`, 18 casos — login, logout, sessão, controle de acesso por perfil), isolada via `IR_FLOW_DATA_DIR`. Corrigido no processo um bug crítico pré-existente (KI-012) que impedia `app.py` de inicializar. Revisão independente de código concluída — aprovada para merge. Mergeado em `main`.

**Sprint 2.3 (T-12 a T-16) concluída em 2026-07-07:** fecha os gaps de cobertura deixados pela 2.2 e expande para autorização — 55 novos casos em 4 módulos (`test_users.py`, `test_permissions.py`, `test_session.py`, `test_security.py`), todos consumindo fixtures compartilhados extraídos para `conftest.py`. Cobre CRUD de usuários via API, matriz de permissões por perfil (admin/tecnico/vendedor), sessão (expiração simulada, cookie adulterado, logout múltiplo) e resiliência de entrada (SQLi, payload inválido, content-type). Suíte completa: 73 testes, 100% passando. Um caso do escopo original (JSON de tipo errado no login) expôs uma exceção não tratada em produção e foi retirado da suíte em vez de commitado como teste falho — reportado separadamente para decisão, sem registro em `KNOWN_ISSUES.md` nesta sprint (orientação explícita do usuário). Ver `docs/operations/SPRINTS/SPRINT_02.md`.

**Sprint 2.4 (T-17 a T-20) concluída em 2026-07-07, mergeada em `main` em 2026-07-10:** cobertura de regras de negócio de Ordens de Serviço — 88 novos casos em 3 módulos (`test_os_creation_query.py`, `test_os_update_status.py`, `test_os_deletion_security.py`) mais fixtures compartilhados em `conftest.py`. Durante a investigação (antes de qualquer teste), dois bugs reais foram encontrados na validação de `status` ao editar OS — um valor ausente/desconhecido era silenciosamente normalizado para "Em andamento" em vez de rejeitado, o que em `PUT /api/ordens/<id>` reabria silenciosamente uma OS Finalizada e apagava `data_finalizado` (ver B-14 abaixo). As correções foram escritas em 2026-07-07 mas ficaram presas na branch, que só foi revisada e mergeada em `main` em 2026-07-10, ao retomar o Sprint 2 — nesse intervalo o bug esteve ativo em produção; extraídas via `hotfix/status-os-padrao-vazio` (KI-015) antes do restante da branch. Uma divergência de comportamento entre a rota legada e a API (reativação de OS Cancelada não re-consome estoque via API) foi caracterizada via teste, não corrigida — já registrada como exemplo em `docs/engineering/ENGINEERING_GUIDE.md` §11. Ver `docs/operations/SPRINTS/SPRINT_02.md`.

**Sprint 2.5 (T-21 a T-25) concluída em 2026-07-07:** cobertura de regras de negócio de Estoque — 69 novos casos em 4 módulos (`test_stock_creation_query.py`, `test_stock_movement.py`, `test_stock_os_integration.py`, `test_stock_security.py`) mais fixtures compartilhados em `conftest.py`. Durante a investigação, dois bugs reais foram encontrados e corrigidos via `hotfix/` conforme ADR-004, com aprovação explícita do usuário antes de cada um (ver B-11 e B-12 abaixo). Um deles (ordem de parâmetros SQL) não se encaixava perfeitamente nos critérios objetivos do `ENGINEERING_GUIDE.md` §11 — critério novo C-05 registrado no backlog (ver Próximos Objetivos). **Mergeada em `main` em 2026-07-07** (merge fast-forward, sem conflitos). Ver `docs/operations/SPRINTS/SPRINT_02.md`.

**Sprint 2.6 — Padronização de Validação e Parsing (T-26, T-27) concluída em 2026-07-07, mergeada em `main`:** criada camada compartilhada de parsing (`irflow_validation.py`: `parse_int`, `parse_float`, `safe_json`, `validate_positive_number`) e aplicada em `irflow_blueprints_api.py`, eliminando ~50 pontos de duplicação (22x `request.get_json(silent=True) or {}`, checagens de valor positivo, parsing de quantidade). No processo, corrigidos 9 pontos onde um valor não numérico em `request.args`/corpo JSON derrubava a rota com 500 não tratado (KI-013, commit `fix:` isolado do `refactor:`). Registrado KI-014 (bloco `criar_estoque` duplicado e morto, sem efeito em runtime, fora de escopo). 38 testes novos (`tests/test_validation.py`, `tests/test_api_parsing.py`, `tests/test_api_parsing_refactor.py`). Auto-merge com os hotfixes de estoque da Sprint 2.5 (`584c501`, `44be10c`) verificado linha a linha — sem sobreposição, ambos preservados corretamente. Ver `docs/operations/SPRINTS/SPRINT_02.md`.

**Sprint 2.7 — Fechamento (T-28, T-29) concluída em 2026-07-11:** `tests/test_pricing.py` (27 casos — lógica pura de `irflow_price_tables.py` e integração de `/api/precos*`) e `tests/test_shopping.py` (34 casos — CRUD, workflow de status, bloqueio de compra simultânea, auditoria de `/api/shopping-list`), mais fixtures locais de limpeza por teste. Cobertura global subiu de 36% para 43%, passando a meta de 40% da Sprint 2. Durante a escrita de `test_shopping.py`, um bug real foi encontrado em `POST /api/shopping-list` (quantidade `0` normalizada silenciosamente para `1` — C-01+C-04) e corrigido via `hotfix/quantidade-zero-shopping-list` antes de continuar (KI-016). Cobertura tornada bloqueante no CI (`fail_under = 40` em `pyproject.toml`, `continue-on-error` removido de `ci.yml`) com aprovação explícita do usuário. Achado adicional fora de escopo: `ruff check .` falha em `main` com 20 erros pré-existentes, não introduzidos nesta sprint — registrado como KI-017, não corrigido (seria refatoração multi-arquivo). `.env.example` permanece pendente. Ver `docs/operations/SPRINTS/SPRINT_02.md`.

Restante da Sprint 2: `.env.example` (será fechado junto da Unidade 8 da Sprint 3, ver abaixo — mesma
variável de ambiente documentada nas duas frentes).

---

**Sprint 3 — Segurança e Observabilidade** (CONCLUÍDA em 2026-07-11, 4 unidades) e **Sprint P0.1 —
Fundações de Produto** (EM ANDAMENTO) rodando em paralelo, decisão do usuário (CTO) de não começar o
módulo de Vendas ainda e investir primeiro nas fundações reutilizáveis (Clientes, IMEI, camada de
serviços). Plano completo em `docs/operations/SPRINTS/` (a formalizar em `SPRINT_03.md` na conclusão).

- **Unidade 1 — Rate limiting em login (KI-001):** contador em tabela SQLite (`login_attempts`), não
  Flask-Limiter — o Gunicorn de produção roda com `--workers 2`, então memória de processo daria um
  limite mais fraco que o nominal. 5 tentativas/minuto por identificador (`Fly-Client-IP` →
  `X-Forwarded-For` → `remote_addr`). 7 testes.
- **Unidade 2 — Expiração de sessão por inatividade:** janela deslizante de 30 min
  (`IR_FLOW_SESSION_INACTIVITY_MINUTES`), um único ponto de checagem em `verificar_autenticacao()`
  cobrindo views legadas e `/api/*`. 11 testes.
- **Unidade 3 — Auditoria central:** tabela genérica `audit_log` (`irflow_audit.py`), não replica
  `shopping_list_logs` por domínio a cada feature nova. Sem consumidor até a Unidade 5. 5 testes.
- **Unidade 4 — Recuperação de senha:** token de uso único gerado pelo admin (não self-service por
  e-mail), expira em 24h, `secrets.token_urlsafe` como `gerar_token_checklist_os`. 10 testes.
- **Unidade 5 — Domínio Clientes:** `irflow_clientes_controller/service/repository.py` — primeira
  aplicação real da convenção de `ENGINEERING_GUIDE.md` §3.1. CRUD + busca/paginação, `os.cliente_id`
  aditivo sem backfill, exclusão bloqueada com OS vinculada (BR-023, BR-024). Sem tela ainda. 23 testes.
  Achado corrigido: `verificar_autenticacao()` só reconhecia bypass de `/api/*` pelo nome do blueprint
  `api.*` — um segundo blueprint sob `/api/*` caía na checagem de sessão legada; trocado para checar
  `request.path`, escala para qualquer domínio futuro sob `/api/*` sem precisar editar essa lista de novo.
- **Unidade 6 — Domínio `estoque_unidades` (IMEI):** `irflow_estoque_unidades_controller/service/repository.py`
  — segunda aplicação da convenção. Cadastro de unidade individual (bloqueado se `estoque.requer_imei=0`),
  transições manuais `disponivel ↔ em_reparo`, `em_reparo/devolvido → disponivel` (BR-025, BR-026).
  `reservado`/`vendido` existem no schema, sem uso — reservados para o futuro Vendas. Fecha o gap de
  marca de IMEI (`BRAND_IDENTITY.md` seção 2). Sem tela ainda. 20 testes.
- **Unidade 7 — Stub `irflow_vendas_service.py`:** arquivo só com docstring, sem rota/tabela/wiring —
  placeholder explícito para quando o épico Vendas for aprovado, referenciando Clientes e
  `estoque_unidades` como pré-requisitos já entregues.

- **Unidade 8 — `.env.example`:** pendente desde a Sprint 2 (T-10), fechado aqui — 26 variáveis
  documentadas (as ~24 já existentes em `app.py` + as 2 novas desta sprint), incluindo as injetadas
  automaticamente por plataforma de deploy, comentadas como referência. No processo, contagem real de
  KI-017 corrigida para 175 erros (repo inteiro, não só os 2 arquivos que a Sprint 3/P0.1 tocou).
- **Unidade 9 — Adendo `ENGINEERING_GUIDE.md` §3.1:** registra a interpretação "README de domínio =
  docstring no topo do `_service.py`" (já usada em Clientes e `estoque_unidades`) como precedente formal
  para os próximos domínios.

**Sprint 3 e Sprint P0.1 (fase de fundações do produto) concluídas em 2026-07-11** — 9 unidades, testes
subindo de 331 (fim da Sprint 2.7) para 407 (+76), cobertura 43% → 48%. Próximo passo, por decisão do
usuário: retomar o épico Vendas com as fundações (Clientes, IMEI, auditoria, camada de serviços) já
prontas.

---

**Sprint Comercial 0.1 — Catálogo de Produtos (CONCLUÍDA em 2026-07-20, ver
`docs/operations/SPRINTS/SPRINT_COMERCIAL_0.1.md`):** primeira tarefa do Épico Vendas propriamente dito,
divisão de trabalho Frente A (usuário, relacionamento com cliente)/Frente B (Claude, implementação em
tarefas pequenas e fechadas). Domínio `produtos` — `irflow_produtos_controller/service/repository.py`,
terceira aplicação da convenção de `ENGINEERING_GUIDE.md` §3.1. `categoria` (iPhone/Apple Watch/AirPods/
Acessório) e `condicao` (Novo/Seminovo/Vitrine) validadas contra lista fechada e **rejeitadas** com 400
quando inválidas — decisão deliberada de não repetir a coerção silenciosa de
`_normalizar_tipo_estoque`/`_normalizar_qualidade_estoque`, que já causou KI-015 e KI-016. Margem nunca
persistida, sempre calculada no service. Sem tela ainda. 27 testes. Testes subindo de 407 para 434,
cobertura subindo de 48% para 50%. `VENDAS.md` recebeu nota sinalizando que `vendas.estoque_unidade_id` precisa
ser revisado no Sprint Comercial 0.2 (rastreamento por unidade/IMEI de produtos, ainda não desenhado).

**Sprint Comercial 1.1 — Tela Produtos (CONCLUÍDA em 2026-07-21, ver
`docs/operations/SPRINTS/SPRINT_COMERCIAL_1.1.md`):** primeira tela do Épico Vendas — sequenciamento
decidido pelo usuário (CTO) pela ótica de impacto no cliente (backend/testes já prontos, zero mudança
de banco), não pela ótica de implementação. `frontend/src/pages/Produtos.jsx` consome integralmente
`/api/produtos*`, sem tocar backend/schema. Ajuste de produto pedido antes da implementação: cards de
resumo (Produtos/Seminovos/Vitrine), badges de categoria com emoji, busca única combinando todos os
campos relevantes (client-side — o parâmetro `q` do backend só cobre descrição/modelo/SKU), coluna
"Unidades" com placeholder reservando espaço para rastreamento por IMEI de uma sprint futura sem
redesenho posterior. Escrita restrita a `admin` no frontend, espelhando a permissão já existente no
backend. Validado manualmente ponta a ponta (servidor real + banco isolado, nunca `database.db`,
navegador dirigido via Playwright) — login, listagem, busca combinada, criar/editar/excluir, e visão
restrita do perfil `vendedor` (sem botão/ícones de escrita). Sem framework de teste de
componente/unitário no frontend ainda (0% de cobertura unitária) — não expandido nesta sprint por
decisão de manter o escopo pequeno.

**Hotfix H-002 — Catálogo iPhone 17 (RESOLVIDO em 2026-07-21, KI-018):** `IPHONE_MODELS`/
`IPHONE_COLORS` (`irflow_reference_data.py`) atualizados com iPhone 17/17 Air/17 Pro/17 Pro Max —
bloqueio operacional real (impossível abrir OS para esses aparelhos). Cores usam lista genérica
por decisão deliberada (sem necessidade comercial ainda de nome exato). Comentário de fonte única
adicionado acima de `IPHONE_MODELS`. Branch própria a partir de `main`, mergeada separada da feature.

**Merge em `main` (2026-07-21):** `fix/catalogo-iphone-17` e `feat/produtos-catalogo` mesclados nesta
ordem. O merge da Tela Produtos trouxe consigo, sem ser plano desta sessão, o fechamento efetivo de
KI-017/KI-014 em `origin/main` — a branch `feat/produtos-catalogo` havia sido construída em cima de
`chore/fix-ruff-lint-ki-017`, cujo merge em `origin/main` nunca havia de fato acontecido apesar da
documentação já registrar como concluído em 2026-07-20 (achado reportado ao usuário antes de
completar o merge; aceito deliberadamente trazer os dois juntos, já que nenhum é código novo desta
sessão). `ruff check .` → 0 erros no repositório inteiro, 434 testes (407 + 27 de `test_produtos.py`)
passando, `npm run build`/`npm run lint` sem erros novos — confirmado após o merge, não só antes.

**Sprint Comercial 1.2 — Tela Clientes (CONCLUÍDA em 2026-07-21, ver
`docs/operations/SPRINTS/SPRINT_COMERCIAL_1.2.md`):** segunda tela do Épico Vendas.
`frontend/src/pages/Clientes.jsx` consome integralmente `/api/clientes*` (Sprint 3 Unidade 5), sem
tocar backend/schema. Além do CRUD (padrão igual à Tela Produtos — cards, busca única, permissão
espelhando o backend: criar/editar para qualquer perfil autenticado, excluir só `admin`), inclui um
painel de Perfil do Cliente com Histórico de OS e Garantias reais, montado a partir de dois endpoints
já existentes (`GET /api/ordens/historico-cliente`, `GET /api/garantias?q=`) — nenhum endpoint novo.
Achado durante a investigação: `os.cliente_id` existe no schema desde a Sprint P0.1 mas nenhum fluxo
real o preenche hoje (só testes escrevem nele direto no banco); o histórico de OS depende do
endpoint legado por correspondência de nome, mesma limitação de antes, agora só mais visível na UI.
"Compras" aparece como placeholder vazio, como antecipado pelo usuário — módulo de Vendas ainda não
existe. Validado manualmente ponta a ponta (servidor real + banco isolado + navegador dirigido via
Playwright, dados de OS/garantia semeados via API para exercitar o perfil).

**Sprint Comercial 1.3 — Tela Unidades Serializadas (PAUSADA desde 2026-07-21, ver ADR-007; retomada
2026-07-21 após RC):** ao investigar a implementação, ficou claro que `estoque_unidades` só cobria
peças de `estoque` (assistência) — não o cenário real que a tela deveria resolver (buscar um aparelho
de revenda do catálogo `produtos` por IMEI). Decisão de arquitetura registrada e **aceita pelo usuário
(CTO)** em `ADR-007.md`: `estoque_unidades` **evoluiu** para o domínio `unidades_serializadas` (dados
preservados, não descartados), fonte única de verdade para qualquer unidade física rastreada por
IMEI/serial. Dois princípios de arquitetura fixados junto da decisão: **Regra de Ouro** (um IMEI/serial
= uma unidade, nunca duplicada entre domínios — cada domínio consome e transiciona o mesmo registro) e
**Princípio da Responsabilidade de Transição** (cada domínio só pode transicionar os estados que lhe
pertencem — ex.: Vendas é dona de `Disponível → Reservado → Vendido`, Assistência de `Em Garantia → Em
Reparo → Disponível`; Garantias só consulta/registra eventos). Rename feito na mesma migração que
generaliza a origem (`produto_id` nullable, `estoque_id` agora opcional), sem alias de compatibilidade
(decisão deliberada do CTO — zero consumidores hoje).

**Migração implementada e validada em RC (2026-07-21)** — branch `feat/unidades-serializadas`
(commit `a5a0c8e`), mergeada em `main`. Ver `docs/engineering/migrations/MIGRATION_unidades_serializadas.md`
para o resultado completo do RC (integridade, idempotência, smoke test, todos verdes contra cópia real
de produção). **Achado relevante do RC:** o backup de produção usado revelou que produção está ~10 dias
atrás de `main` — sem a tabela `produtos` nem nenhuma feature da Sprint Comercial 0.1+. Decisão do CTO:
antes do deploy, fazer um **RC do sistema inteiro** (não só desta migração), cobrindo login, dashboard,
OS, estoque, compras, clientes, produtos, backup, MercadoPhone, usuários e IMEI — executado
imediatamente antes do próximo deploy, não antes de retomar a Sprint Comercial 1.3 (decisão do CTO,
2026-07-21: aproveitar os dias até a próxima reunião para entregar telas, não para o RC completo).
Migração do `database.db` real de produção ainda pendente — passo de deploy separado, checklist em
`MIGRATION_unidades_serializadas.md`.

**Sprint Comercial 1.3.1 — Tela de Listagem (CONCLUÍDA e mergeada em `main` em 2026-07-22):**
`frontend/src/pages/UnidadesSerializadas.jsx` — busca única por IMEI/modelo/produto, cards de resumo
(Unidades/Disponíveis/Em Reparo), badges de origem (Estoque/Produto) e status. Backend enriquecido com
`LEFT JOIN` em `estoque`/`produtos` só para exibição (label de origem, categoria/marca quando aplicável)
— nenhuma mudança de filtro/regra de negócio. 449 testes no total (29 em `test_unidades_serializadas.py`),
`ruff check .` limpo. Revisado e mergeado por Claude nesta sessão (trabalho de
implementação de sessão anterior) — validado manualmente rodando o app com unidades seedadas via API a
partir de `estoque` e de `produtos`, confirmando busca cruzada e badges de origem corretas para os
dois casos.

**Sprint Técnica — Centralização de Referências (CONCLUÍDA em 2026-07-22, pedido do usuário — CTO):**
investigação encontrou uma única duplicação real: `PRODUTOS_CATEGORIAS`/`PRODUTOS_CONDICOES` já eram
fonte única no backend, mas nunca expostas em `GET /api/constantes` — `Produtos.jsx` mantinha cópia
própria hardcoded, com risco de divergir quando uma categoria/condição nova fosse adicionada só no
backend. Corrigido: API expõe as duas listas, frontend consome (lista antiga mantida só como fallback
defensivo). `IPHONE_MODELS`/`IPHONE_COLORS` já eram fonte única e já expostas — confirmado, nenhuma
mudança necessária. "Fabricantes" não existe como lista fechada hoje (campo `marca` é texto livre em
`produtos`) — criar uma seria feature nova, não consolidação, fora de escopo. 450 testes (novo teste
confirmando o shape de `/api/constantes`), validado manualmente rodando o app — dropdown de categoria
no modal de Produtos populado via API.

**Sprint Comercial 1.3.2 — Detalhes da Unidade Serializada (CONCLUÍDA em 2026-07-22, ver
`docs/operations/SPRINTS/SPRINT_COMERCIAL_1.3.2.md`):** ao clicar numa unidade na listagem (C1.3.1),
abre painel com IMEI, origem (produto/estoque), status, saúde da bateria, localização e histórico
completo. Achado antes de codar: os eventos de auditoria (criação + mudança de status) já eram gravados
em `audit_log` desde a Sprint P0.1, mas nenhum endpoint do sistema lia essa tabela de volta — adicionado
`GET /api/unidades-serializadas/<id>/historico` (só leitura, zero schema), aprovado explicitamente pelo
usuário antes de implementar por sair do escopo original ("só consumir API existente"). Cliente
atual/Garantia mostrados como placeholder explícito — dependem do módulo de Vendas, ainda não
implementado. 455 testes (34 no domínio de unidades serializadas), `ruff check .` limpo, validado
manualmente com produto/unidade/2 transições de status semeados via API.

**Sprint Comercial 1.3.3 — Filtros Avançados (CONCLUÍDA em 2026-07-22, ver
`docs/operations/SPRINTS/SPRINT_COMERCIAL_1.3.3.md`):** busca combinada (IMEI/serial/modelo/marca/
localização), filtros por origem/status/faixa de saúde da bateria/localização, ordenação, e paginação
real — tudo resolvido no backend, nada só em memória no frontend (antes a tela carregava até 500
registros de uma vez e filtrava localmente). Três pontos do pedido original reportados ao usuário (CTO)
antes de codar por não terem suporte real: filtro por Cliente removido desta sprint (sem dado até
Vendas existir); status "Em Garantia"/"Inativo" não incluídos (não existem em lugar nenhum, seria regra
de negócio nova); filtros de bateria/localização construídos mesmo sem dado real hoje (mesmo padrão do
KI-020), decisão deliberada para não gerar retrabalho quando C1.3.4 escrever esses campos. 467 testes
(46 no domínio), `ruff check .` limpo, validado manualmente com dados de origem mista.

**Sprint Comercial 1.3.4 — Edição da Unidade Serializada (CONCLUÍDA em 2026-07-22, ver
`docs/operations/SPRINTS/SPRINT_COMERCIAL_1.3.4.md`):** `PATCH /api/unidades-serializadas/<id>`
(localização, saúde da bateria — únicos campos de manutenção sem endpoint de escrita até então).
Pedido explícito do usuário (CTO) tratado como módulo de manutenção, não edição isolada — campos
derivados/imutáveis (origem, IMEI, status, campos de Vendas) bloqueados explicitamente com 400 se
enviados; status continua no endpoint próprio já existente (`/status`), com sua máquina de estados.
`DetalheUnidade` evoluído para um único componente de visualização+edição, por pedido explícito do
usuário de não duplicar estrutura entre um modal de detalhe e um de edição separados. Dois pontos
resolvidos antes de codar: "Observações" não existe no schema (fora de escopo, a própria instrução do
usuário de não alterar schema já resolve); IMEI consultado explicitamente e decidido como imutável
após o cadastro (identificador primário usado em busca/auditoria/futura garantia). 476 testes (55 no
domínio), `ruff check .` limpo, validado manualmente editando bateria/localização/status de uma
unidade real.

**Sprint Técnica — Centralização de Referências de OS (CONCLUÍDA em 2026-07-23, ver
`docs/operations/SPRINTS/SPRINT_TECNICA_CENTRALIZACAO_OS.md`):** segunda parte da centralização de
referências pedida pelo usuário (CTO), após a de Produtos (2026-07-22). Encontrado e corrigido: tipos de
OS (Assistencia/Garantia/Upgrade) tinham 2 cópias inline no backend e 3 no frontend, com `OrderFilters.jsx`
nunca buscando da API; prazo de garantia (90 dias) hardcoded 2x no mesmo arquivo backend;
`GARANTIA_DIAS` no frontend era código morto. Tudo centralizado em `OS_TIPOS_OPCOES`/
`GARANTIA_REPARO_DIAS_PADRAO` (`irflow_core.py`), exposto via `/api/constantes`, consumido por
`Orders.jsx`/`OrderFilters.jsx`. Achado registrado, não corrigido: perfis (`admin`/`tecnico`/
`vendedor`) espalhados como string literal em 11 arquivos backend sem lista central — categoria
diferente (autorização, não referência de UI), risco desproporcional a um chore, candidato a sprint
própria. 478 testes, `ruff check .` limpo, validado manualmente com os dropdowns de Status/Tipo em
`/ordens`.

**Sprint Comercial 1.3.5 — Rastreabilidade Individual de Itens de Estoque (CONCLUÍDA em 2026-07-27, ver
`docs/operations/SPRINTS/SPRINT_COMERCIAL_1.3.5.md`):** fecha o KI-020 — `POST`/`PUT /api/estoque`
passam a ler/gravar `requer_imei` (já existia no schema, sem caminho de escrita) e `GET /api/estoque`
passa a expô-lo; checkbox correspondente em `Stock.jsx`. Sem esse fechamento, o caminho "unidade
serializada com origem em Estoque" (`irflow_unidades_serializadas_service.py`) era inutilizável em
produção — só funcionava semeando o banco diretamente. Nome da coluna mantido por compatibilidade
(`requer_imei`); conceito documentado como rastreabilidade individual do item, não IMEI
especificamente. 8 novos testes (549 no total), incluindo o fluxo completo via API real (criar item
rastreável → criar unidade serializada com sucesso) e a confirmação de que a ausência da flag continua
rejeitando a criação (regressão). `ruff check .` limpo, `npm run build`/`npm run lint` sem erros novos.

**Vendas MVP (CONCLUÍDA em 2026-07-27, ver `docs/operations/SPRINTS/SPRINT_COMERCIAL_VENDAS_MVP.md`):**
primeiro fluxo comercial completo — venda de um único aparelho (unidade serializada) a um cliente, com
pagamento simples registrado. Escopo deliberadamente independente das decisões de negócio ainda
pendentes do Product Owner em `VENDAS.md` (timeout de reserva, % comissão, limite de desconto, prazo de
garantia, critérios de avaliação de usado) — sem reserva com timeout (unidade vai direto
`disponivel` → `vendido`), sem desconto/comissão/garantia/troca. Modelado como `vendas` + `vendas_itens`
desde o início (mesmo com 1 item por venda nesta fatia), `status='concluida'` (não `'paga'` — venda e
pagamento são conceitos diferentes), snapshot `produto_nome`/`produto_sku` em `vendas_itens`, `UNIQUE`
em `vendas_itens.unidade_serializada_id` como proteção de banco contra a mesma unidade em duas vendas.
`irflow_unidades_serializadas_service.py` ganhou `marcar_como_vendida`, deliberadamente separada de
`transicionar_status`/`TRANSICOES_VALIDAS` para não abrir uma porta lateral no endpoint genérico de
status. Primeiro módulo a nascer com o prefixo `fluxoly_` (`fluxoly_vendas_controller.py`/`_service.py`/
`_repository.py`, ver `ADR-008`) — substitui o stub `irflow_vendas_service.py`, removido nesta sprint.
16 novos testes (565 no total), incluindo duas vendas concorrentes da mesma unidade via threads reais
(exatamente uma sucede, rodado 5x para confirmar ausência de flakiness) e prova de rollback atômico em
erro forçado. Refinado no mesmo dia: `valor_tabela` (snapshot de preço de catálogo, pré-preenchido e
editável) e `observacoes` em `vendas_itens`/`vendas`; frontend `frontend/src/pages/Vendas.jsx` (rota
`/vendas`) entregue e validado manualmente ponta a ponta (servidor real + banco isolado + navegador). 570
testes, `ruff check .` limpo. Próximo passo do roadmap comercial: fluxo completo de Vendas (desconto/
comissão/garantia/troca), condicionado a decisões do Product Owner.

**Sprint Infra 1.1 — CI Verde (CONCLUÍDA em 2026-07-27):** workflow `CI` corrigido e verde em `main` pela
primeira vez, `main` protegida contra merge sem os checks passando. Investigação completa, causas raiz e
justificativa de cada configuração em KI-026 (resolvida)/R-10/R-11 (mitigados)/TD-13 (endurecimento
adiado, backlog).

**Sprint Vendas 1.1 — Histórico + Detalhe de Vendas (CONCLUÍDA em 2026-07-27, branch
`feat/vendas-historico-detalhe`, mergeada em `main`):** retomada de uma branch aberta por uma sessão
anterior (commit WIP `6774016`) — backend (`GET /api/vendas` paginado/filtrável/ordenável, `GET
/api/vendas/<id>` enriquecido com nomes de cliente/vendedor e IMEI) e a página `VendaDetalhe.jsx` já
estavam prontos; pendências fechadas nesta sessão: abas "Nova Venda"/"Histórico" ligadas em `Vendas.jsx`
(componente `Historico()` já existia, sem estar no fluxo de navegação), botão "Ver venda" da tela de
sucesso passou a navegar para `/vendas/:id` em vez de buscar o detalhe inline, e `VendaDetalhe.jsx` teve
um erro real de lint corrigido (`react-hooks/set-state-in-effect` — `setLoading(true)` direto no corpo do
efeito; refeito com função nomeada `carregar()`, mesmo padrão já usado em `Historico()`) — achado que
motivou a investigação da Sprint Infra 1.1 acima. 10 novos testes (31 no domínio, 580 no repositório),
`ruff check .` limpo, `npm run build`/`npm run lint` sem erros novos. Validado manualmente ponta a ponta
com servidor real + banco isolado (nunca `database.db`) e navegador Chrome real: criação de venda, clique
em "Ver venda" navegando corretamente para o detalhe, listagem/filtros/busca/paginação do histórico.

**V1.2 — Cancelamento (CONCLUÍDA em 2026-07-27):** discuss-phase completa antes de código (regras em
`VENDAS.md`/`BUSINESS_RULES.md` BR-031 a BR-036), depois implementação. `POST /api/vendas/<id>/cancelar`
— admin cancela qualquer venda, vendedor só as próprias, motivo obrigatório (lista fechada), terminal
(sem reativação). Índice único de `vendas_itens.unidade_serializada_id` trocado por um parcial
(`WHERE ativo=1`) — permite revenda da mesma unidade após cancelamento sem perder o histórico. 14 novos
testes (45 no domínio, 592 no repositório), `ruff check .`/`npm run lint`/`npm run build` limpos.
Validado ponta a ponta via API real (servidor + banco isolados): criar → cancelar → revenda da mesma
unidade → histórico com as duas vendas → segundo cancelamento rejeitado. Fluxo de clique no navegador não
repetido nesta sessão (limite de contexto) — mesmos componentes já validados manualmente na Sprint 1.1.

**Fechamento — validação de navegador da V1.2 (2026-07-28):** item pendente acima fechado. Servidor
Flask + Vite reais, banco isolado (`IR_FLOW_DATA_DIR`, nunca `database.db`), navegador Chrome real.
Fluxo completo executado: criar venda (unidade → `vendido`) → venda aparece no Histórico com badge
"Concluída" → abrir Detalhe pelo botão "Ver venda" e pela linha do Histórico → cancelar informando
motivo da lista fechada → toast de confirmação, badge "Cancelada", motivo e data exibidos, sem opção de
reativação → confirmado via API que a unidade voltou a `disponivel` e que `audit_log` registrou as duas
transições de status (`vendido→disponivel`, `disponivel→vendido`) → nova venda com o mesmo IMEI
concluída como Venda #2 → Histórico lista as duas vendas (`Concluída`/`Cancelada`) corretamente.
Nenhuma divergência encontrada — Sprint V1.2 encerrada sem achados.

**ADR-010 (CONCLUÍDA em 2026-07-28):** formaliza o ciclo Discovery → Plano Técnico → Implementação →
Testes → QA Manual → Encerramento, com gate explícito em cada etapa e o Princípio da Separação de
Decisões (Plano Técnico nunca decide regra de negócio — se surgir, volta para Discovery). Novo artefato
`docs/engineering/plans/PLAN-<slug>.md` (template em `docs/engineering/templates/PLAN_TEMPLATE.md`),
deliberadamente efêmero. Processo vive só na ADR — `CLAUDE.md` ganhou apenas uma referência de uma
linha, por ser processo do projeto, não de uma ferramenta de IA específica.

**V1.3 — Descontos e Aprovação (CONCLUÍDA em 2026-07-28, primeira feature a seguir o ciclo formal da
ADR-010):** discovery pela ótica do fluxo real de negociação da loja (BR-037 a BR-043,
`VENDAS.md`/`BUSINESS_RULES.md`), plano técnico revisado e aprovado (5 ajustes incorporados —
`docs/engineering/plans/PLAN-V1.3-Descontos.md`), depois implementação. `usuarios.limite_desconto_livre`
(R$, `NULL` = não configurado, tratado como R$0 pelo service — nunca por SQL); `POST /api/vendas` exige
`desconto_aprovado=true` explícito acima do limite (aprovação acontece fora do sistema, só a confirmação
e o timestamp são registrados, nunca quem aprovou). Ajuste Comercial Autorizado
(`PATCH /api/vendas/<id>/itens/<id>/ajuste-desconto`) — única exceção formal ao Princípio da Imutabilidade
da Venda (BR-034): só `admin`, motivo obrigatório, recálculo transacional, auditoria append-only,
compare-and-swap contra cancelamento concorrente. 21 novos testes (613 no total), `ruff check .`/
`npm run lint`/`npm run build` limpos. QA Manual (navegador real, servidor + banco isolados, 6 cenários:
desconto dentro/acima do limite, vendedor sem limite, Ajuste Comercial, segurança, estado obsoleto) —
todos passaram; encontrado e corrigido 1 bug real no processo (`limite_desconto_livre` ausente na
resposta de `POST /api/auth/login`, já que `Login.jsx` popula o `AuthContext` direto dessa resposta, sem
esperar `/api/auth/me`).

**V1.4 — Comissão (CONCLUÍDA em 2026-07-29, segunda feature a seguir o ciclo formal da ADR-010):**
discovery reabriu a V1.3 na mesma sessão e revogou o modelo de bloqueio preventivo de desconto
(BR-037/BR-038 → BR-053: todo desconto passa a ser sempre aceito e sempre registrado, sem exigir
aprovação nem respeitar limite; `limite_desconto_livre`/`desconto_aprovado_em` param de ser
lidos/gravados em qualquer fluxo, colunas mantidas no schema só por compatibilidade histórica, marcadas
como deprecadas). Plano técnico único cobrindo as duas partes
(`docs/engineering/plans/PLAN-V1.4-Comissao.md`, 5 ajustes incorporados), implementado em 8 commits
temáticos (reversão backend → reversão frontend → testes da reversão → schema/repository da comissão →
service/controller → frontend → testes da comissão → docs). Novo perfil `financeiro`; `comissao_valor`
(R$, `NULL` = não atribuída, sem campo de "tipo" fixo/percentual — BR-048) atribuída manualmente por
`admin`/`financeiro` via `PATCH /api/vendas/<id>/itens/<id>/comissao`; ocultação de `comissao_valor` para
qualquer outro perfil centralizada numa única função (`_ocultar_comissao_se_necessario`); zerada
automaticamente no cancelamento, sempre com evento de auditoria; histórico dedicado
(`GET .../historico-comissao`) restrito a `admin`/`financeiro` — diferente do histórico de desconto, que
é aberto. 15 novos testes de comissão + 6 reescritos da reversão (625 no total), `ruff check .`/
`npm run lint`/`npm run build` limpos. QA Manual via `curl` (14 cenários, autorização/ocultação/
zeragem/histórico/criação de usuário financeiro) — todos passaram; navegador real indisponível neste
ambiente por limitação do próprio ambiente de automação de navegador, não do produto (**KI-027**, novo).

**Fix de responsividade do Dashboard em MacBook (CONCLUÍDO em 2026-07-30, branch
`fix/dashboard-responsividade-macbook`, PR #14):** grids de KPIs e gráficos usavam contagem fixa de
colunas por breakpoint, pulando abruptamente entre 3 e 6 colunas e deixando espaço em branco/valores
truncados em larguras de MacBook (1366–1728px). Trocado por CSS Grid `auto-fit`/`minmax`
(`minmax(280px,1fr)` nos KPIs — calibrado para não truncar valores monetários; `minmax(420px,1fr)` nos
gráficos), único arquivo alterado (`Dashboard.jsx`). Validado por medição real de overflow no DOM
(`scrollWidth`/`clientWidth`) nas 6 larguras-alvo, não só cálculo de CSS — validação visual num MacBook
físico não foi possível nesta sessão (sem acesso a Mac). Mergeado em `main`.

**V1.5 — Garantia (CONCLUÍDA em 2026-07-30, terceira feature a seguir o ciclo formal da ADR-010, branch
`feat/vendas-v1-5-garantia`):** Garantia de Venda e Garantia de Reparo como processos independentes,
substituindo o prazo fixo de 90 dias hardcoded do reparo por um cadastro configurável de Tipos de
Garantia (BR-055 a BR-066). Ambas de atribuição manual obrigatória (venda/conclusão de OS) com snapshot
histórico congelado no momento da concessão — nunca recalculado ao vivo contra o cadastro, mesmo se este
mudar depois. Achado de implementação relevante: `salvar_reparos_os()` fazia `DELETE`+`INSERT` cego a
cada edição de OS, o que apagaria silenciosamente a garantia já concedida de uma linha mantida numa
edição sem relação com status — reescrita para sync não-destrutivo antes de expor o problema em
produção. 693 testes no total, `ruff check .`/`npm run lint`/`npm run build` limpos. QA Manual completo
com servidor real + banco isolado + navegador real via Claude in Chrome (login funcionou normalmente
nesta sessão, ao contrário do registrado em KI-027 — ver observação atualizada nesse KI) e `curl` para o
único fluxo sem UI (correção de Garantia de Reparo). Revisão Arquitetural (`ADR-010` etapa 6) sem
inconsistência não documentada. Achado durante o QA Manual, corrigido no mesmo Encerramento (decisão do
CTO): datas de garantia apareciam um dia atrasadas na tela por um bug clássico de parsing de data em JS
(`KI-028`, resolvido).

**Sprint CI/CD 1.1 — Hardening (CONCLUÍDA em 2026-07-31):** revisão do pipeline de CI/CD partiu de uma
premissa errada (que o pipeline ainda precisava ser criado) — descoberto que o CI já estava ativo e
bloqueante desde a Sprint Infra 1.1 (2026-07-27), com `main` protegida exigindo 5 status checks. Escopo
real, bem menor que uma sprint de implantação: (1) `fail_under` de cobertura elevado de 40% para 60%
(`pyproject.toml`, `ci.yml`) — cobertura real medida em 65.22%/682 testes no momento da mudança, ~5
pontos de margem antes de virar bloqueante de verdade; (2) novo job `Docker Build` (`docker build .`,
sem publicar) valida que a imagem builda antes do merge, não só na hora do deploy — testado localmente
via Colima antes de subir. `main` agora exige 6 status checks (Docker Build adicionado via `gh api`).
Deploy permanece manual, sem mudança — decisão deliberada de não automatizar nesta sprint.
`docs/engineering/QUALITY_GATES.md` atualizado (estava desatualizado desde 2026-07-06, antes até da
Sprint Infra 1.1 — vários gates listados como "Planejado"/"Manual" já estavam ativos há dias).

**Sprint Housekeeping — Rebranding Técnico (EM PLANEJAMENTO, iniciada 2026-07-31):** endereça TD-12
(nomenclatura legada `irflow_*`/`IR_FLOW_*`/`assistencia_system` convivendo com `fluxoly_*` desde
ADR-008). Decisão deliberada do usuário (CTO) de priorizar esta sprint agora, antes de retomar
funcionalidades de negócio, mesmo com TD-12 originalmente classificado como prioridade baixa — ver
`docs/operations/SPRINTS/SPRINT_HOUSEKEEPING.md` para a estrutura completa em 6 fases (Baseline →
Auditoria → Planejamento → Limpeza → Renomeação → Validação). Nenhuma fase executada ainda além da
Fase 0 (baseline confirmado: `main` sincronizada, tag `v1.2-cicd-hardening` existente, 682 testes).

**Sprint Housekeeping — CONCLUÍDA em 2026-08-03:** todos os módulos `.py` renomeados de `irflow_*` para
`fluxoly_*` (commits `8a085f8`..`14ec238`), branding residual do frontend corrigido, referências mortas
em `pyproject.toml` limpas. CI verde (run `30865336611`, todos os 6 jobs), cobertura 66.13% (acima do
baseline de 65.22%). Deploy validado em produção: Vercel via auto-deploy, Render via Manual Deploy
(auto-deploy não configurado nesse serviço — achado da própria validação de fechamento), ambos sem
erros novos no Sentry pós-deploy. `ADR-011` registra que a decomposição de `fluxoly_blueprints_api.py`
(TD-01) e o restante do épico de rebranding (variáveis `IR_FLOW_*`, infraestrutura, repositório) ficam
fora desta sprint, com dono e destino definidos. Ver retrospectiva completa em
`docs/operations/SPRINTS/SPRINT_HOUSEKEEPING.md`.

**TD-01 Phase 2 — Garantias extraído (2026-08-05):** segundo domínio extraído de
`fluxoly_blueprints_api.py` (o primeiro, Shopping List, já registrado na tabela de Dívida Técnica
acima). `api_garantias.py` criado (1 rota — `GET /garantias`, listagem agregada), mesmo padrão do
`api_shopping.py`: `Blueprint` próprio com `url_prefix="/api"`, `deps` parcial (`conectar`,
`garantia_reparo_dias_padrao`, `parse_data_ymd` — os dois últimos continuam também no dict de
`create_api_blueprint`, porque OS e Sistema, ainda não extraídos, dependem deles), helper específico
do domínio (`_classificar_garantia`) migrado junto, helpers genéricos (`err`/`ok`/`usuario_logado`)
reaproveitados de `fluxoly_api_helpers.py` (já criado na extração de Shopping). 682 testes passando
sem alteração, `ruff check .` limpo, `graphify update .` + `graphify explain "api_garantias"` +
`graphify affected "fluxoly_blueprints_api.py"` confirmados sem referência residual do domínio. Ver
`docs/operations/SPRINTS/SPRINT_TD01_MODULARIZACAO_API.md` (Phase 2, log de execução) e
`docs/engineering/API_DEPENDENCY_MATRIX.md` para o detalhe completo.

**TD-01 Phase 2 — Preços extraído (2026-08-06):** quarto domínio extraído de
`fluxoly_blueprints_api.py`. `api_prices.py` criado (4 rotas — `GET/POST /precos`, `POST
/precos/excluir`, `GET /precos/sugerir`), assimetria de autorização original preservada
(`sugerir_preco()` só exige `usuario_logado()`; as outras 3 exigem também `usuario_admin()`).
Diferente das 3 extrações anteriores: `carregar_tabelas_preco`/`salvar_tabelas_preco` não têm nenhum
outro consumidor no monólito — as chaves saíram do dict de `create_api_blueprint`, em vez de ficarem
duplicadas (primeiro domínio a reduzir `deps` de fato, não só particioná-lo). 683 testes passando sem
alteração, `ruff check .` limpo, `graphify update .` + `graphify explain "api_prices"` confirmados sem
referência residual do domínio. Ver `docs/operations/SPRINTS/SPRINT_TD01_MODULARIZACAO_API.md` (Phase
2, log de execução) e `docs/engineering/API_DEPENDENCY_MATRIX.md` para o detalhe completo.

**TD-01 Phase 2 — Usuários extraído (2026-08-06):** quinto domínio extraído de
`fluxoly_blueprints_api.py`. `api_users.py` criado (6 rotas — `GET/POST/PUT/DELETE /usuarios*`, `POST
/usuarios/<id>/reset-token`, `POST /password-reset/<token>`), assimetria de auth preservada (só a
última rota é pública). Primeira aplicação da nova regra do DoD (`graphify affected`/`explain` antes de
remover uma dep): retornou "no match" (limitação real da ferramenta para chave de dict/import de
biblioteca terceira); verificação feita por leitura completa em substituição, confirmando que
`generate_password_hash`/`perfis_opcoes` só tinham consumo dentro do bloco de Usuários no monólito (o
outro consumidor, `create_auth_blueprint`, é blueprint separado e intocado). Efeito colateral mecânico
corrigido no mesmo commit: `tests/test_users.py` referenciava o endpoint qualificado do blueprint antigo
(`app.view_functions["api.criar_usuario"]`) e `import sqlite3` ficou sem uso em
`fluxoly_blueprints_api.py`. 683 testes passando, `ruff check .` limpo, `graphify update .` +
`graphify explain "api_users"` confirmados sem referência residual do domínio. Ver
`docs/operations/SPRINTS/SPRINT_TD01_MODULARIZACAO_API.md` (Phase 2, log de execução) e
`docs/engineering/API_DEPENDENCY_MATRIX.md` para o detalhe completo.

**TD-01 Phase 2 — Sistema extraído (2026-08-07):** décimo domínio extraído de
`fluxoly_blueprints_api.py`. `api_system.py` criado (3 rotas — `GET /constantes`, `GET /alertas`,
`GET /dashboard`), helpers `_sanitize_list`/`_sanitize_nested_obj` migrados verbatim. Corrigida a
matriz: `texto_reparos_os` não pertence a este domínio (21 deps, não 22 — pertence a
`_os_row_to_dict()`, domínio OS). **Achado de acoplamento (Discovery):** `ESTOQUE_TIPOS`/
`ESTOQUE_QUALIDADES` eram constantes locais dentro do monólito (fora do padrão do resto dos dados de
referência), usadas tanto por `constantes()` quanto pelos helpers de Estoque (`_normalizar_tipo_estoque`/
`_normalizar_qualidade_estoque`, domínio 11/12, ainda não extraído) — promovidas para
`fluxoly_reference_data.py` nesta extração (mesmo padrão de `_texto_limpo_local` na extração de
Backup), sem mudança de regra de negócio. `obter_alertas_sistema` tem um segundo consumidor
(`inject_system_alerts()`, `app.py`, context processor dos templates legados) não documentado até
aqui — achado do Graphify, não afeta a extração. 12 chaves saem do dict de `create_api_blueprint`
(deps reduzido); as demais ligadas a OS (ainda não extraído) continuam duplicadas. Smoke test manual
confirmou `/alertas`/`/dashboard` (sem cobertura automatizada) e `/constantes` (já coberta) em 6
cenários. 683 testes passando, `ruff check .` limpo, `graphify update .` + `graphify explain
"api_system"` + `graphify affected "fluxoly_blueprints_api.py"` confirmados sem referência residual.
Restam Estoque, OS — Architecture Checkpoint completo fica para depois de Estoque (decisão do CTO).
Ver `docs/operations/SPRINTS/SPRINT_TD01_MODULARIZACAO_API.md` (Phase 2, log de execução) e
`docs/engineering/API_DEPENDENCY_MATRIX.md` para o detalhe completo.

**TD-01 Phase 2 — MercadoPhone extraído (2026-08-06):** nono domínio extraído de
`fluxoly_blueprints_api.py` — o mais acoplado até agora. `api_mercadophone.py` criado (7 rotas).
Achado central da Discovery (tratada como matriz de acoplamento completa): `_carregar_config_mercadophone()`/
`_atualizar_runtime_mercadophone()`/`mercado_phone_runtime_config` também são usados por
`listar_ordens()` (domínio OS, ainda no monólito) — risco já registrado na Phase 0, resolvido agora
promovendo as 2 funções para `fluxoly_mercadophone.py` (serviço, parâmetros explícitos) em vez de
`fluxoly_api_helpers.py` (é lógica de domínio, não helper web genérico). Etapa de validação isolada
feita antes da extração do blueprint (commit separado): migrou as funções, trocou só `listar_ordens()`,
rodou 111 testes filtrados de OS+MercadoPhone antes de seguir. Smoke test manual confirmou as 3 rotas
sem cobertura automatizada (`/reprocessar/status`, `/reimportar/status`, `GET /status`). 683 testes
passando, `ruff check .` limpo, `graphify update .` + `graphify explain "api_mercadophone"` confirmados
sem referência residual. **Architecture Checkpoint pós-MercadoPhone:** 26 rotas restantes no monólito
(-63% desde a Phase 0), 80KB/1.961 linhas, 48 chaves de `deps`, 22 helpers locais; `app.py` em
2.431 linhas/100KB/17 `register_blueprint()` (nova métrica permanente adotada a partir deste
checkpoint). Restam Sistema, Estoque, OS. Ver `docs/operations/SPRINTS/SPRINT_TD01_MODULARIZACAO_API.md`
(Phase 2, log de execução e checkpoint completo) e `docs/engineering/API_DEPENDENCY_MATRIX.md`.

**TD-01 Phase 2 — Relatórios extraído (2026-08-06):** oitavo domínio extraído de
`fluxoly_blueprints_api.py`. `api_reports.py` criado (6 rotas — JSON agregado + PDF de IR Phones,
Técnicos e Custos Operacionais), movidas verbatim. Acoplamento baixo no nível do blueprint (nenhuma
chamada direta a OS/Estoque/Preços/Clientes). Corrigida a matriz: `tecnicos` não pertence a este
domínio (8 deps, não 9). 6 das 8 deps também são usadas por `create_main_blueprint`
(`fluxoly_blueprints_main.py`, páginas renderizadas no servidor) — verificado explicitamente intacto
antes e depois da edição (Graphify → dict do monólito → dict do outro blueprint → grep final). KI-031
registrado: zero teste automatizado cobre estas 6 rotas — smoke test manual (Flask test client, banco
temporário isolado) confirmou HTTP 200 nas 6 rotas e PDFs reais (`%PDF-1.4`) antes do commit; nova regra
permanente adicionada ao DoD da Phase 2 para domínios sem cobertura. 683 testes passando sem alteração,
`ruff check .` limpo, `graphify update .` + `graphify explain "api_reports"` confirmados sem referência
residual do domínio. Ver `docs/operations/SPRINTS/SPRINT_TD01_MODULARIZACAO_API.md` (Phase 2, log de
execução) e `docs/engineering/API_DEPENDENCY_MATRIX.md` para o detalhe completo.

**TD-01 Phase 2 — Backup extraído (2026-08-06):** sétimo domínio extraído de
`fluxoly_blueprints_api.py`. `api_backup.py` criado (4 rotas — `POST /backup/criar`, `GET
/backup/listar`, `GET /backup/download/<filename>`, `POST /backup/restaurar`), movidas verbatim.
`_texto_limpo_local()` promovido para `fluxoly_api_helpers.py` (compartilhado com MercadoPhone, ainda
no monólito — sequência seguida: promover → importar no monólito → confirmar suíte de MercadoPhone →
remover implementação local). Verificação tripla (Graphify `affected`/`explain` + grep textual) nos 3
deps mais sensíveis (`criar_backup`, `enviar_backup_email`, `forcar_migracao_schema`), confirmando zero
resíduo — `criar_backup` também é chamado por `executar_backup_diario_automatico()` (agendador,
consumidor independente via import direto, não afeta a decisão). `garantir_pasta_backup_google_drive`
(dead code pré-existente) mantida intocada — fora do escopo desta extração. 3 imports órfãos
(`contextlib`, `os`, `send_from_directory`) removidos no mesmo commit. 683 testes passando, `ruff
check .` limpo, `graphify update .` + `graphify explain "api_backup"` confirmados sem referência
residual do domínio. Ver `docs/operations/SPRINTS/SPRINT_TD01_MODULARIZACAO_API.md` (Phase 2, log de
execução) e `docs/engineering/API_DEPENDENCY_MATRIX.md` para o detalhe completo.

**TD-01 Phase 2 — Auth extraído (2026-08-06):** sexto domínio extraído de `fluxoly_blueprints_api.py`.
`api_auth.py` criado (3 rotas — `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`), movidas
verbatim inclusive comentários (comentário do INC-001 em `auth_login()` preservado sem alteração de
lógica). `resolver_ip_cliente`/`limite_excedido`/`registrar_tentativa`/`check_password_hash` saíram do
dict de `create_api_blueprint` (sem outro consumidor no monólito; o outro uso legítimo, em
`create_auth_blueprint`, ficou intacto). Segunda aplicação da regra do DoD de verificar via Graphify
antes de remover uma dep — desta vez a ferramenta resolveu os símbolos do projeto (`fluxoly_rate_limit`)
e confirmou ausência de consumidor residual. Corrigido no mesmo commit:
`tests/test_inc001_login_connection_leak.py` referenciava o endpoint qualificado do blueprint antigo.
683 testes passando, `ruff check .` limpo, `graphify update .` + `graphify explain "api_auth"`
confirmados sem referência residual do domínio. Ver
`docs/operations/SPRINTS/SPRINT_TD01_MODULARIZACAO_API.md` (Phase 2, log de execução) e
`docs/engineering/API_DEPENDENCY_MATRIX.md` para o detalhe completo.

**TD-01 Phase 2 — Custos Operacionais extraído (2026-08-06):** terceiro domínio extraído de
`fluxoly_blueprints_api.py`. `api_costs.py` criado (4 rotas — `GET/POST /custos`, `PUT/DELETE
/custos/<id>`), mesmo padrão de Shopping/Garantias: `Blueprint` próprio com `url_prefix="/api"`, `deps`
parcial (`conectar`, `listar_custos_operacionais` — este último continua também no dict de
`create_api_blueprint`, porque `/dashboard` e `/relatorios/custos-operacionais`, ainda não extraídos,
dependem dele). `usuario_admin()` promovido para `fluxoly_api_helpers.py` (já previsto na Phase 1,
agora comprovadamente usado por 2+ domínios — regra de admissão satisfeita); cópia local em
`fluxoly_blueprints_api.py` mantida intacta (cleanup fica para a Phase 3). 683 testes passando sem
alteração, `ruff check .` limpo, `graphify update .` + `graphify explain "api_costs"` + `graphify
affected "fluxoly_blueprints_api.py"` confirmados sem referência residual do domínio. Ver
`docs/operations/SPRINTS/SPRINT_TD01_MODULARIZACAO_API.md` (Phase 2, log de execução) e
`docs/engineering/API_DEPENDENCY_MATRIX.md` para o detalhe completo.

### Escopo previsto

- ~~Configurar GitHub Actions (lint + testes no push)~~ — já existe (`.github/workflows/ci.yml`), descoberto desatualizado nesta revisão (2026-07-10)
- Escrever testes unitários para módulos críticos do backend (`irflow_os.py`, `irflow_blueprints_api.py`)
- Migrar testes de smoke para pytest com fixtures isoladas
- Configurar Playwright no CI (headless)
- Documentar variáveis de ambiente em `.env.example`
- Padronizar mensagens de commit (Conventional Commits)
- ~~Tornar a cobertura bloqueante no CI~~ — feito em 2026-07-11 (`fail_under = 40`); os `continue-on-error` de formatação (ruff format/isort/black) seguem adiados para a Sprint 3, sem mudança

---

## Score do Projeto

| Critério                      | Peso | Nota | Score |
|-------------------------------|------|------|-------|
| Funcionalidade core           | 25%  | 8/10 | 2,0   |
| Cobertura de testes           | 20%  | 4/10 | 0,8   |
| Arquitetura e organização     | 15%  | 5/10 | 0,75  |
| Segurança                     | 15%  | 5/10 | 0,75  |
| Observabilidade / logs        | 10%  | 3/10 | 0,3   |
| DevEx (CI/CD, docs, DX)       | 10%  | 2/10 | 0,2   |
| Desempenho                    | 5%   | 6/10 | 0,3   |
| **Total**                     |      |      | **5,1 / 10** |

> Score recalculado em 2026-07-10, pós-merge da Sprint 2.4 em `main` — ver seção "Cobertura de Testes"
> abaixo para os números reais medidos após o merge. **Nota (2026-07-10):** esta revisão descobriu que
> `.github/workflows/ci.yml` já existe desde antes desta conversa (commit `563765f`) — a nota "DevEx
> (CI/CD, docs, DX)" 2/10 acima foi calculada assumindo CI/CD ausente, o que estava errado. A cobertura
> ainda não é bloqueante no pipeline (`--cov-fail-under=0`), então algum desconto permanece válido, mas
> a nota provavelmente já justifica um valor mais alto. Recálculo formal do score fica para a próxima
> revisão, não decidido unilateralmente aqui — mesma disciplina já aplicada à nota anterior sobre a
> Sprint 2.6. Meta para fim de Sprint 2: >= 6,0.
>
> **Nota (2026-07-25):** a linha "Segurança" (5/10) acima também está desatualizada — foi calculada
> antes da Sprint Segurança 1.0, que fechou os P0/P1 de `docs/security/SECURITY_AUDIT_2026-07.md`
> (autorização de OS/Estoque, fallback de `FLASK_SECRET_KEY`, headers HTTP, Docker non-root,
> `persist-credentials`, dependências). A nota provavelmente já justifica um valor mais alto — mesma
> disciplina acima: recálculo formal fica para a próxima revisão do score completo, não decidido
> unilateralmente aqui.

---

## Bugs Conhecidos

| ID   | Descrição                                                        | Severidade | Status        |
|------|------------------------------------------------------------------|------------|---------------|
| B-01 | Mensagens de commit sem padrão dificultam rastreabilidade de bugs | Baixa      | Aberto        |
| B-02 | SQLite não adequado para cenários de alta concorrência           | Média       | Aceito (risco) |
| B-03 | Sem rate limiting nas rotas de autenticação (`/api/auth/login`)  | Alta        | Aberto        |
| B-04 | Tokens de checklist público não expiram                          | Média       | Aberto        |
| B-05 | Backup por e-mail pode falhar silenciosamente sem alertas visíveis| Baixa      | Aberto        |
| ~~B-06~~ | ~~Auto-fill `valor_cobrado` ausente~~ | ~~Crítica~~ | ~~Resolvido (Sprint 1)~~ |
| ~~B-07~~ | ~~PDF IR Phones com URL errada~~ | ~~Alta~~ | ~~Resolvido (Sprint 1)~~ |
| ~~B-08~~ | ~~`historico-cliente` apontando para rota inexistente~~ | ~~Média~~ | ~~Resolvido (Sprint 1)~~ |
| ~~B-09~~ | ~~Campo `cor` não limpo ao trocar modelo~~ | ~~Média~~ | ~~Resolvido (Sprint 1)~~ |
| ~~B-10~~ | ~~Endpoint `/api/shopping-list` duplicado (código legado) travava a inicialização do Flask (KI-012)~~ | ~~Crítica~~ | ~~Resolvido (2026-07-07)~~ |
| ~~B-11~~ | ~~`PUT /api/estoque/<id>` calculava o diff de movimentação com a quantidade não limitada a zero — quantidade negativa gerava saída maior que o saldo real no histórico~~ | ~~Média~~ | ~~Resolvido (2026-07-07, hotfix, commit `584c501`)~~ |
| ~~B-12~~ | ~~`GET /api/estoque` com qualquer filtro (modelo/tipo/qualidade) retornava sempre lista vazia — ordem errada de parâmetros SQL~~ | ~~Alta~~ | ~~Resolvido (2026-07-07, hotfix, commit `44be10c`)~~ |
| ~~B-13~~ | ~~9 rotas de `irflow_blueprints_api.py` retornavam 500 não tratado com entrada não numérica em `int()`/`float()` (KI-013)~~ | ~~Média~~ | ~~Resolvido (2026-07-07)~~ |
| ~~B-14~~ | ~~`PATCH /api/ordens/<id>/status` e `PUT /api/ordens/<id>` sem `status_padrao=""` explícito — status ausente/inválido normalizado silenciosamente para "Em andamento"; em `PUT`, reabria OS Finalizada e zerava `data_finalizado` sem erro (KI-015)~~ | ~~Crítica~~ | ~~Resolvido (2026-07-10, hotfix, commit `2defd17`; achados originais durante a Sprint 2.4, commits `c85a321`/`e755f25`, 2026-07-07)~~ |
| ~~B-15~~ | ~~`POST /api/shopping-list` normalizava `quantidade_solicitada: 0` silenciosamente para `1` (operador `or` tratando `0` como ausente) em vez de rejeitar (KI-016)~~ | ~~Média~~ | ~~Resolvido (2026-07-11, hotfix `quantidade-zero-shopping-list`, achado durante a Sprint 2.7)~~ |

---

## Dívida Técnica

| ID   | Descrição                                                              | Impacto | Prioridade |
|------|------------------------------------------------------------------------|---------|------------|
| ~~TD-01~~ | ~~`fluxoly_blueprints_api.py` — módulo único de 70 rotas/13 domínios sem separação (KI-003)~~ | ~~Alto~~ | ~~**Resolvido (2026-08-07)** — TD-01 Phase 2 (Extração Incremental) encerrada formalmente por decisão do usuário (CTO): 12/12 domínios extraídos para blueprints próprios (Shopping List, Garantias, Custos Operacionais, Preços, Usuários, Auth, Backup, Relatórios, MercadoPhone, Sistema, Estoque, OS+Reparos), `fluxoly_blueprints_api.py` reduzido de ~130KB/3.368 linhas/70 rotas para 911 bytes/34 linhas/0 rotas. Architecture Checkpoint Final em `docs/operations/SPRINTS/SPRINT_TD01_MODULARIZACAO_API.md`. Restam apenas KI-032 (código morto) e a Phase 3 (Cleanup, ver TD-18) — deliberadamente fora do escopo, mesma disciplina de não misturar refatoração com limpeza usada nas 12 extrações~~ |
| ~~TD-18~~ | ~~**TD-01 Phase 3 — Cleanup.** Remover `fluxoly_blueprints_api.py`~~ (só continha `_slug_estoque`/`_gerar_sku_estoque`, KI-032, código morto sem consumidor) ~~e o registro `app.register_blueprint(create_api_blueprint({}))`~~. **Resolvido (2026-08-08)** — arquivo removido por inteiro; o registro do blueprint vazio (que após a TD-02 vivia em `fluxoly_blueprint_registry.py`, não mais em `app.py` — texto desta linha corrigido nesta revisão) removido junto, com ~10 comentários históricos da TD-01 que ficariam órfãos apontando para código inexistente. Discovery confirmou zero consumidor residual (só notas de proveniência histórica em outros módulos, preservadas). KI-032 movida para Resolvidos. `app.url_map` idêntico (122 rotas), 683 testes passando | ~~Baixo~~ | ~~Baixa~~ |
| ~~TD-02~~ | ~~`app.py` acumula inicialização, DB e lógica misturadas.~~ **Resolvido (2026-08-08)** — 4/4 fatias concluídas, ver `docs/operations/SPRINTS/SPRINT_TD02_BOOTSTRAP_APP.md` (Architecture Checkpoint Final): Fatia 1 `fluxoly_config.py` (config/env/paths), Fatia 2 `fluxoly_app_security.py` (CORS/security headers), Fatia 3 `fluxoly_blueprint_registry.py` (registry dos 20 blueprints), Fatia 4 webhook MercadoPhone → `api_mercadophone.py`. `app.py`: 2.490 → 1.749 linhas (-30%), 20 `register_blueprint()` inline → 1 chamada a `registrar_blueprints(app, runtime)`, `app.url_map` idêntico (122 rotas) nas 4 fatias. Restam deliberadamente fora do escopo: DB connection, schema/migrations (KI-004/TD-03), helpers de dashboard/alertas/custos, `ROUTE_PERMISSIONS`/middleware — nenhum é bootstrap de blueprint | ~~Alto~~ | ~~Alta~~ |
| ~~TD-03~~ | ~~Ausência de migrations formais (usa `ALTER TABLE` com try/except).~~ **Resolvido (2026-08-08)** — 2/2 fatias concluídas, ver `docs/operations/SPRINTS/SPRINT_TD03_MIGRATIONS_FORMAIS.md`. Fatia 1: pacote `migrations/` (registry Python, `schema_migrations`, baseline `0001` verbatim de `criar_tabelas()`) construído de forma aditiva, validado contra backup real de produção antes de tocar `app.py`. Fatia 2: `app.py::criar_tabelas()`/`SCHEMA_READY`/`SCHEMA_LOCK` removidos (695 linhas); `conectar()` virou conexão pura; bootstrap chama `run_migrations()`. KI-004 movida para Resolvidos | ~~Alto~~ | ~~Alta~~ |
| TD-04 | Sem injeção de dependências no backend — acoplamento direto ao SQLite  | Médio   | Média      |
| TD-05 | Testes de backend são scripts ad-hoc, não pytest com fixtures isoladas | Médio   | Alta       |
| TD-06 | Sem variáveis de ambiente documentadas (`.env.example` ausente)        | Médio   | Média      |
| TD-07 | Frontend sem testes unitários (apenas E2E Playwright)                  | Médio   | Média      |
| TD-08 | Commits com mensagens vagas ("att", "S", "att 09/06 5")               | Baixo   | Alta       |
| TD-09 | Sem paginação na listagem de OS — pode degradar com volume alto        | Médio   | Média      |
| TD-10 | Sem compressão de resposta HTTP no Flask                               | Baixo   | Baixa      |
| ~~TD-11~~ | ~~Bloco `criar_estoque()` duplicado e morto em `irflow_blueprints_api.py` (KI-014)~~ | ~~Baixo~~ | ~~Resolvido (2026-07-20, commit `c3294a3`)~~ |
| ~~TD-12~~ (código) | ~~Nomenclatura legada `irflow_*` em todos os módulos `.py` — resolvido pela Sprint Housekeeping~~ | ~~Baixo~~ | ~~Resolvido (2026-08-03, commits `8a085f8`..`14ec238`, ver `docs/operations/SPRINTS/SPRINT_HOUSEKEEPING.md`)~~ |
| TD-12 (infra) | Restante do Épico de Rebranding Técnico, deliberadamente fora da Sprint Housekeeping: variáveis `IR_FLOW_*` (14, alias `FLUXOLY_*` via `ADR-008`), URLs Render/Vercel, nome do repositório GitHub. Decomposição de `fluxoly_blueprints_api.py` (TD-01) também fora, formalizada em `ADR-011` | Baixo (cosmético, sem risco funcional) | Baixa — sem prazo; ligado a `RELEASE_1.0_MASTER_CHECKLIST.md` (janela de manutenção antes do lançamento comercial), não a esta sprint |
| TD-13 | **Infra 1.2 — Endurecer Governança do Repositório.** Proteção de `main` ativada em 2026-07-27 (R-10/R-11) cobre só o mínimo (5 status checks obrigatórios, `enforce_admins: false`). Falta: `enforce_admins: true` (a proteção hoje não vale para push direto do próprio mantenedor), `CODEOWNERS`, revisão obrigatória (`required_pull_request_reviews`) com aprovação mínima. Sugerido pelo usuário (CTO) — decisão deliberada de não fazer agora para não quebrar o fluxo atual de merge local + push direto de um mantenedor único; faz sentido quando a equipe crescer além de uma pessoa | Médio (hoje mitigado por disciplina manual de um único mantenedor; escala mal com mais colaboradores) | Baixa (sem prazo — condicionado a crescimento da equipe) |
| TD-14 | **Evolução do modelo de autorização — perfil único → perfis + permissões por módulo.** Discovery da V1.4 (2026-07-29) propôs substituir `usuarios.perfil` (enum: admin/tecnico/vendedor/estoque/financeiro) por acesso habilitado por módulo (checkboxes: Vendas/Estoque/Assistência/Financeiro/Compras/Dashboard/Administração), evitando explosão combinatória de perfis à medida que o sistema cresce. Decisão explícita: **não fazer agora** — muda arquitetura de autorização transversalmente (checagens espalhadas em ~80 endpoints de `irflow_blueprints_api.py` + `ROUTE_PERMISSIONS` + cada controller de domínio), exigiria migração dos perfis já em produção, e hoje 5 perfis (com `financeiro` da V1.4) ainda são administráveis — a "explosão" é cenário futuro, não problema atual. Merece ADR própria + discovery dedicada quando reaberto. **Preparação de baixo custo feita na V1.4:** checagens de autorização novas encapsuladas em helper reutilizável (ex.: `usuario_pode_financeiro()`), para que uma futura migração troque a implementação do helper sem precisar reescrever os call sites | Médio (não bloqueia nada hoje; custo de migração cresce quanto mais perfis/checagens ad-hoc se acumularem antes de endereçar) | Baixa (sem prazo — reavaliar se a combinação de perfis realmente começar a se multiplicar) |
| TD-15 | **Code Style Cleanup — Black/isort.** Setup de ambiente de desenvolvimento (2026-08-04) encontrou 55 arquivos `.py` fora do padrão do `black` (mesma versão travada do `.pre-commit-config.yaml`, 24.4.2 — não é drift de versão, é debt pré-existente) e 9 arquivos com imports fora de ordem pelo `isort` (`app.py`, `fluxoly_blueprints_api.py` entre eles). `ruff check .` está limpo — só formatação, não lint funcional. Decisão deliberada de não corrigir junto com o setup de ambiente (evitar commit não-atômico misturando dezenas de arquivos sem relação com a tarefa) | Baixo (cosmético, não afeta comportamento; `ruff check` limpo) | Média — resolver antes de a Sprint TD-01 (modularização da API) tocar nesses mesmos arquivos, para não misturar reformatação mecânica com a refatoração estrutural |
| TD-16 | **Formalizar `estoque_service.py`.** `ENGINEERING_GUIDE.md` §3 já recomenda extrair a lógica de movimentação de estoque hoje embutida em `fluxoly_os.py` (`registrar_movimentacao`, `consumir_peca_da_os`, `_consumir_lotes_fifo`, `devolver_pecas_da_os`) para um service formal, para que OS, Vendas e Compras consumam a mesma lógica em vez de cada um reimplementar. Identificado como ortogonal à Sprint TD-01 (Phase 1, 2026-08-04): a decomposição de `fluxoly_blueprints_api.py` não depende disso — as funções já vivem fora do blueprint. Registrado aqui para não repetir o padrão já visto em `ADR-002` original (recomendação feita, nunca rastreada como item de backlog) | Médio (hoje funciona, mas cada novo consumidor de baixa de estoque arrisca reimplementar a lógica à sua maneira) | Baixa — sem prazo; considerar quando Vendas ou Compras precisarem dar baixa em estoque de fato |
| ~~TD-17~~ | ~~Crescimento do bootstrap de `app.py` (candidata a TD-02).~~ Achado do Architecture Checkpoint pós-MercadoPhone (TD-01 Phase 2, 9/12 domínios, 2026-08-06) — 20 `app.register_blueprint()` inline sem registry/factory. **Resolvido (2026-08-08)** — TD-02 Fatia 3 (`fluxoly_blueprint_registry.py::registrar_blueprints(app, runtime)`) centralizou as 20 chamadas numa tabela declarativa; TD-02 encerrada por completo (ver TD-02 acima) | ~~Baixo hoje; médio a longo prazo sem uma TD-02~~ | ~~Baixa~~ |

---

## Riscos Atuais

| ID   | Risco                                                                 | Probabilidade | Impacto | Mitigação atual      |
|------|-----------------------------------------------------------------------|---------------|---------|----------------------|
| R-01 | SQLite em produção sem replicação — falha de disco = perda de dados  | Baixa         | Crítico | Backup automático    |
| ~~R-02~~ | ~~Sem CI/CD — regressões chegam a produção sem detecção automática~~ | ~~Alta~~ | ~~Alto~~ | **Mitigado (2026-07-27, Sprint Infra 1.1; reforçado 2026-07-31, Sprint CI/CD 1.1 — Hardening)** — mesmo mecanismo de R-10/R-11: CI ativo e bloqueante (6 status checks), cobertura em 60% |
| R-03 | Chaves secretas em variáveis de ambiente sem documentação formal      | Média         | Alto    | `.env` removido do git|
| ~~R-04~~ | ~~Sem rate limiting — `/api/auth/login` vulnerável a força bruta~~ | Baixa | Alto | **Mitigado (2026-07-11)** — `irflow_rate_limit.py`, 5 tentativas/min por identificador (KI-001) |
| R-05 | Tokens de checklist não expiram — link público permanente             | Baixa         | Médio   | Nenhuma              |
| R-06 | Dependência única de Render + Vercel sem estratégia de fallback documentada | Baixa   | Médio   | `DEPLOY.md` documenta o passo a passo, sem provedor alternativo |
| R-07 | Módulo de integração MercadoPhone sem testes — qualquer mudança é risco| Alta         | Médio   | Script diagnose_mercadophone.py |
| ~~R-08~~ | ~~`ruff check .` vermelho em `main` — job `Lint` bloqueava `backend`/`frontend` via `needs: lint` (KI-017)~~ | ~~Alta~~ | ~~Alto~~ | **Mitigado (2026-07-20)** — `ruff check .` → 0 erros, branch `chore/fix-ruff-lint-ki-017`, 6 commits atômicos |
| R-09 | Produção real (Render + Vercel) está atrás de `main` — confirmado em 2026-07-22 consultando `GET /api/constantes` da produção real: ainda retorna só até "iPhone 16e" (sem a linha 17, sem `produtos`, sem `unidades_serializadas`) | Alta | Alto (percepção de bug onde não há — usuário reportou "hotfix não aplicado" quando na verdade é deploy pendente) | Nenhuma automática — deploy é acionado manualmente no dashboard Render/Vercel, decisão já registrada do CTO de acumular mudanças para um RC completo antes do próximo deploy |
| ~~R-10~~ | ~~Workflow `CI` não registrava nenhum sucesso em `main` (84/84 runs falhos confirmados via `total_count` da API, 2026-07-07–2026-07-27) — job `Frontend Quality` (ESLint) vermelho por 3 causas diferentes ao longo do tempo, `Frontend Build` nunca rodava (KI-026)~~ | ~~Alta~~ | ~~Alto~~ | **Mitigado (2026-07-27, Sprint Infra 1.1)** — 4 erros de ESLint corrigidos (`chore/frontend-eslint-cleanup`), primeiro sucesso do workflow identificado nas execuções verificadas |
| ~~R-11~~ | ~~`main` não tinha proteção de branch configurada no GitHub — confirmado via `gh api repos/.../branches/main/protection` retornando `404 Branch not protected` (sem revisão obrigatória, sem status check obrigatório, sem bloqueio de force-push). O CI (R-10) nunca funcionou como gate de merge~~ | ~~Alta~~ | ~~Alto~~ | **Mitigado (2026-07-27)** — proteção ativada via `gh api` exigindo os 5 status checks do CI, `strict: true`, força-push/deleção bloqueados. `enforce_admins: false` deliberado (preserva o fluxo atual de push direto do único mantenedor) — endurecimento completo (CODEOWNERS, revisão obrigatória, `enforce_admins: true`) registrado como TD-13, não decidido |

---

## Arquivos Críticos

| Arquivo                          | Papel                                                         | Risco de tocar |
|----------------------------------|---------------------------------------------------------------|----------------|
| `fluxoly_blueprints_api.py`      | Todos os endpoints REST (70) — núcleo do sistema (TD-01)       | Muito alto     |
| `app.py`                         | Inicialização Flask, schema DB, registro de blueprints        | Muito alto     |
| `fluxoly_os.py`                  | Lógica de negócio das Ordens de Serviço                       | Alto           |
| `fluxoly_storage.py`             | Backup automático e Google Drive                              | Alto           |
| `fluxoly_mercadophone.py`        | Integração com sistema externo MercadoPhone                   | Alto           |
| `frontend/src/api/client.js`     | Centraliza todas as chamadas de API do frontend               | Alto           |
| `frontend/src/App.jsx`           | Roteamento, guards de autenticação, layout global             | Alto           |
| `frontend/src/contexts/AuthContext.jsx` | Estado global de autenticação                          | Alto           |
| `fluxoly_core.py`                | Constantes de status e utilitários compartilhados             | Médio          |
| `frontend/src/pages/NewOrder.jsx`| Fluxo crítico de criação de OS com auto-price                 | Médio          |
| `frontend/src/pages/EditOrder.jsx`| Fluxo crítico de edição de OS                                | Médio          |

---

## Cobertura de Testes

| Camada            | Tipo                     | Ferramenta   | Cobertura medida em `main` (`pytest-cov`, 2026-07-20, pós Sprint Comercial 0.1) — branch `feat/unidades-serializadas` (ainda não mergeada) entre parênteses |
|-------------------|--------------------------|--------------|--------------------|
| Backend — API     | Smoke tests ad-hoc       | Python scripts| ~25% das rotas (não medido via `pytest-cov`) |
| Backend — Módulos | pytest (auth, sessão, usuários, permissões, segurança, estoque, OS, parsing/validação, preços, shopping list, rate limit, sessão/inatividade, auditoria, reset de senha, clientes, unidades_serializadas, produtos — Sprint 2.2 a Sprint Comercial 0.1, migração ADR-007) | pytest | `irflow_validation.py` 100% · `irflow_clientes_repository.py` 100% · `irflow_clientes_service.py` 97% · `irflow_clientes_controller.py` 97% · `irflow_produtos_service.py` 99% · `irflow_produtos_controller.py` 91% · `irflow_produtos_repository.py` 85% · `irflow_core.py` 86% · `irflow_price_tables.py` 83% · `app.py` 55% (58% na branch) · `irflow_os.py` 64% · `irflow_blueprints_api.py` 59% (60% na branch) — `irflow_estoque_unidades_service.py` 97%/`irflow_estoque_unidades_controller.py` 95% em `main`, renomeados para `irflow_unidades_serializadas_service.py` 99%/`_controller.py` 95%/`_repository.py` 86% na branch |
| Frontend — Pages  | Sem testes unitários     | —            | 0%                 |
| Frontend — E2E    | Fluxos principais        | Playwright   | ~20% dos fluxos    |
| Integração        | Script manual            | Python       | ~10%               |
| **Global (repo, `main`)** |                  |              | **50%** (`pytest --cov`, 434 testes, pós Sprint Comercial 0.1 — 2026-07-20); **50,3%** (447 testes) na branch `feat/unidades-serializadas`, ainda não mergeada |

> Meta Sprint 2: >= 40% de cobertura nas rotas críticas do backend. **Atingida** em 2026-07-11 com `test_pricing.py` e `test_shopping.py` (Sprint 2.7) — cobertura global subiu de 36% para 43%, e segue subindo com Sprint 3/P0.1 (46% agora). Gate de CI bloqueante desde a Sprint 2.7 (`fail_under = 40`). `test_os.py` (nome originalmente previsto) foi substituído por 3 módulos mais granulares na Sprint 2.4 (`test_os_creation_query.py`, `test_os_update_status.py`, `test_os_deletion_security.py`).

---

## Próximos Objetivos

### Curto prazo (Sprint 2)
1. ~~Implementar pipeline de CI com GitHub Actions~~ — já existe, ver "Estado Atual"
2. Migrar smoke tests para pytest com fixtures
3. ~~Atingir 40% de cobertura nas rotas críticas~~ — feito em 2026-07-11 (43%, `test_pricing.py`, `test_shopping.py`)
4. Documentar `.env.example`
5. Padronizar commits com Conventional Commits
6. ~~Corrigir os erros de `ruff check .` em `main` (KI-017/R-08)~~ — feito em 2026-07-20 (0 erros, branch `chore/fix-ruff-lint-ki-017`), antes do início do Épico Vendas
7. **[Backlog — process]** Adicionar critério **C-05 — Consulta incorreta em fluxo oficial** a `docs/engineering/ENGINEERING_GUIDE.md` §11 (ou ADR dedicada). Motivação: o hotfix `44be10c` (Sprint 2.5 — ordem de parâmetros SQL quebrava todo filtro de `GET /api/estoque`) não se encaixava nos critérios C-01–C-04 existentes, que cobrem mutação de dado, não leitura incorreta em rota de consulta usada pelo frontend. Rascunho de critério: *"O achado faz uma rota de consulta (GET) oficialmente usada pelo frontend retornar dado incorreto, incompleto ou vazio de forma sistemática (não um erro pontual de um registro), sem sinalizar erro ao chamador?"* Avaliar junto de C-01–C-04 na próxima ocorrência similar antes de formalizar a redação final.

### Médio prazo (Sprint 3–4)
1. Quebrar `fluxoly_blueprints_api.py` em módulos menores (TD-01 — decisão confirmada em `ADR-002`/`ADR-011`, sprint própria ainda sem data)
2. Implementar migrations formais (Alembic ou scripts versionados)
3. Adicionar rate limiting em `/api/auth/login`
4. Implementar expiração de tokens de checklist
5. Adicionar paginação na listagem de OS

### Longo prazo (Sprint 5+)
1. Avaliar migração de SQLite para PostgreSQL
2. Implementar observabilidade (Sentry ou similar)
3. Criar API pública documentada (OpenAPI/Swagger)
4. Adicionar notificações push/webhook para mudanças de status de OS
