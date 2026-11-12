# CHANGELOG

Todas as mudanças notáveis neste projeto serão documentadas aqui.

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/).
Versionamento segue [Semantic Versioning](https://semver.org/lang/pt-BR/).

---

## [Não lançado]

### Documentação (2026-11-11 — status da Fila Priorizada do backlog)
- **docs: atualiza a coluna Status do `PRODUCT_BACKLOG.md`** — Vendas (V1.2-V1.5 com tela), Clientes,
  IMEI e Produtos (com tela), Financeiro mínimo e Caixa (entregues em 2026-08-10) estavam desatualizados.
  Prioridades e notas do PO inalteradas.

### Documentação (2026-11-11 — proposta de backlog a partir do benchmark Mercado Phone)
- **docs: proposta de candidatos no `PRODUCT_BACKLOG.md`** — 25 candidatos consolidados de todos os
  módulos do benchmark, em quatro ondas (dados existentes, fundação de pagamentos, relacionamento,
  decisões antes de código), cada um com prioridade/esforço sugeridos, item da Release 1.0 e evidência.
  Marcada como pendente do PO; a Fila Priorizada não foi alterada.

### Documentação (2026-11-11 — benchmark Mercado Phone: Garantia, Checklist e Auditoria)
- **docs: análise de Garantia, Checklist e Auditoria do Mercado Phone** — termos de garantia e de compra
  com cálculo de vencimento, monitoramento de garantias por item, checklist configurável, log de auditoria
  com antes/depois e logs de acesso. Registra que o `audit_log` da Fluxoly é gravado em quase todos os
  domínios mas não tem tela de consulta. Sem mudança de código.

### Documentação (2026-11-11 — benchmark Mercado Phone: Ferramentas e Marketplace)
- **docs: análise de Ferramentas e Marketplace do Mercado Phone** — automações de pós-venda por WhatsApp,
  programa de indicação, catálogo online, assinatura digital, consulta de score/IMEI, loja de integrações
  (API, MCP, webhooks) e carteira pré-paga. Encerra o walkthrough de todos os módulos. Sem mudança de
  código.

### Documentação (2026-11-11 — benchmark Mercado Phone: Tela inicial e Configurações)
- **docs: análise de Tela inicial e Configurações do Mercado Phone** — avisos de pendências, widgets,
  parâmetros gerais, gestão de acesso (visibilidade de vendas, horário), senhas mestras, situações de OS
  configuráveis, notificações e modelos de documentos. Corrige a seção Clientes e Relatórios: o Dashboard
  da Fluxoly já tem lucro e ticket médio, mas só de OS. Sem mudança de código.

### Documentação (2026-11-11 — benchmark Mercado Phone: Clientes e Relatórios)
- **docs: análise de Clientes e Relatórios do Mercado Phone** — ficha com histórico de compras, índice de
  recompra, catálogo de relatórios, dashboard de alertas de dados e dashboard diário. Novo **KI-062**:
  perfil do cliente e detalhe da unidade ainda mostram "módulo de Vendas em construção". Sem mudança de
  código.

### Documentação (2026-11-11 — benchmark Mercado Phone: Fiscal)
- **docs: análise do Fiscal do Mercado Phone** — score fiscal, NF-e de entrada do usado, captura de XML,
  notas a partir de venda/OS/estoque; recomendações condicionadas a discovery e escolha de provedor. Sem
  mudança de código.

### Documentação (2026-11-11 — benchmark Mercado Phone: Financeiro)
- **docs: análise do Financeiro do Mercado Phone** — contas a pagar/receber, despesas fixas, caixa por
  sessão, contas bancárias, formas de pagamento com prazo, conciliação e DRE; lacunas da Fluxoly como
  candidatos com "Decisão pendente do PO". Sem mudança de código.

### Documentação (2026-11-11 — benchmark Mercado Phone: Compras/Estoque)
- **docs: análise de Compras/Estoque do Mercado Phone** — estoque por unidade com dias em estoque, busca
  consolidada de IMEI, custos extras, certificado de procedência; seção de Vendas corrigida (a troca já
  existe em parte via Compra de aparelhos). Sem mudança de código.

### Documentação (2026-11-11 — benchmark Mercado Phone: Vendas)
- **docs: análise de Vendas do Mercado Phone** no mesmo documento — PDV multi-item/multi-pagamento,
  simulador de upgrade (aparelho na troca), trocas e devoluções, histórico por item; lacunas da Fluxoly
  como candidatos com "Decisão pendente do PO". Sem mudança de código.

### Documentação (2026-11-11 — benchmark Mercado Phone: OS)
- **docs: análise da OS do Mercado Phone** em `docs/product/research/BENCHMARKS/MERCADO_PHONE.md` —
  listagem, ações, formulário (8 abas), Kanban, garantias e dashboard, observados em modo leitura; lacunas
  da Fluxoly listadas como candidatos com "Decisão pendente do PO". Sem mudança de código.

### Alterado (2026-11-10 — PDF da OS no formato de ordem de serviço)
- **feat: PDF de entrada e de entrega da OS em quadros e tabelas** — cabeçalho com o nome da loja, os dados
  dela no centro e "Ordem de serviço Nº" à direita; quadros "Dados do Cliente" e "Dados da OS" lado a lado;
  tabelas de aparelho e de serviços (na entrega, com garantia e validade); valor total em destaque;
  observação em quadro; termos com subtítulos centralizados (linhas em maiúsculas) e "Cláusula Nª:" em
  negrito; nome do cliente e da loja sob as assinaturas; rodapé com número da OS e paginação. O documento
  passa a trazer o e-mail do cliente vinculado (BR-095). Sem mudança de banco.

### Corrigido (2026-11-10)
- **fix: migrations não rodam mais em paralelo nos 2 workers (KI-060)** — `run_migrations()` toma uma trava
  exclusiva em `database.db.migrations-lock` antes de aplicar e só solta no fim; o outro worker espera e
  encontra tudo aplicado. Fecha a família de corridas no boot (KI-035, KI-058), que passou a importar com
  o deploy automático (ADR-015).

### Alterado (2026-11-10 — compose do servidor)
- **chore: `deploy/docker-compose.yml` igual ao do servidor** — serviço `backend`, `./data:/data` e porta
  `127.0.0.1:5080`, como roda em `/opt/fluxoly`. `DEPLOY.md` descreve a instalação feita. O fuso do
  container (`TZ`) ficou de fora de propósito: o app grava datas em UTC e trocar o fuso misturaria dois
  fusos no banco (KI-061, novo).

### Adicionado (2026-11-10 — deploy automático do backend, ADR-015)
- **chore: deploy automático do backend no servidor próprio** — novo job `publish_image` no CI (só em push
  na `main`, depois de todos os gates bloqueantes) publica `ghcr.io/isaque-souza/fluxoly:latest` e `:<sha>`.
  `deploy/docker-compose.yml` sobe o backend e o Watchtower (fork `nickfedor/watchtower:1.24.0`), que
  atualiza o container quando sai imagem nova. Antes de cada troca, `scripts/backup_pre_update.py` copia o
  banco para `/data/backups/backup-pre-update-*.db` (últimos 20); se o backup falhar, a atualização é
  adiada. `aplicar_retencao_backups_automaticos` ganha o parâmetro `prefixo` (padrão inalterado).
  `DEPLOY.md` reescrito para o servidor próprio. Risco das migrations automáticas registrado no KI-060.

### Adicionado (2026-11-10 — Documentos da OS para o cliente)
- **feat: PDF de entrada e de entrega da OS (BR-095 a BR-098)** — na tela **Editar OS**, botões
  **PDF de entrada** (qualquer status, menos Cancelada) e **PDF de entrega** (só OS Finalizada, com a
  garantia de cada serviço e a data de término). Nenhum dos dois para OS interna. O PDF traz dados da
  loja, cliente, aparelho, técnico, serviços, valor, observações, termos e assinaturas — nunca custo,
  lucro, peças, fornecedor ou vendedor; CPF/CNPJ só quando quem gera é `admin`/`financeiro` (KI-045).
  Backend: `GET /api/ordens/<id>/documento?tipo=entrada|entrega` (conteúdo por allowlist). O PDF é gerado
  no navegador com `jspdf` (já dependência, carregado sob demanda).
- **feat: Dados da Loja (BR-094)** — página **Dados da Loja** (menu Administração, só `admin` edita):
  nome fantasia, razão social, CNPJ, telefone, e-mail, endereço e termos de entrada/garantia.
  Migration `m0004` (tabela `dados_loja`, linha única) e `GET/PUT /api/dados-loja`.

### Corrigido (2026-11-10)
- **fix: Valor com Desconto passa a valer no valor da OS quando preenchido (KI-059)** — antes, com Valor
  Cobrado e Valor com Desconto preenchidos, o desconto era ignorado. Afeta listagem, relatórios, lucro e os
  comprovantes para o cliente; relatórios de períodos passados com OS nessa situação mostram valores
  menores ao serem gerados de novo.

### Corrigido (2026-11-09 — hotfix)
- **fix: corrida entre workers na migration 0003 derrubava o boot (KI-058)** — no primeiro boot com a m0003
  pendente, os 2 workers do Gunicorn tentavam criar `os.unidade_serializada_id` ao mesmo tempo e o segundo
  caía com `duplicate column name`. Esse erro específico agora é ignorado no `ALTER`.

### Adicionado (2026-11-08 — Compra de Aparelhos, PR 5/5: telas)
- **feat: telas da compra de aparelhos (BR-083 a BR-093)** — página **Compras de Aparelhos** (menu
  Operação, perfis `admin`/`financeiro`/`vendedor`): registrar compra (modelo, IMEI, origem, estado,
  defeito, cliente e venda na troca ou nome/telefone de quem vendeu, valor e forma de pagamento) e histórico
  com filtros e cancelamento com motivo. **Nova OS** ganha o tipo **Interna**: escolhe o aparelho comprado
  (busca por IMEI/modelo) no lugar de cliente, vendedor e valores; **Editar OS** de uma OS interna não pede
  Garantia de Reparo nem deixa trocar o tipo. Custo e lucro aparecem no detalhe da venda e do aparelho
  (`admin`/`financeiro`), e **Relatórios** ganha a aba **Compra e revenda** (mês). No Financeiro a saída
  aparece como "Compra de aparelho". Backend: `GET /api/unidades-serializadas?origem=compra` (unidades com
  compra ativa) e `Interna` em `os_tipos`. Corrigido também o destaque do menu lateral, que acendia
  "Compras" ao abrir "Compras de Aparelhos".

### Adicionado (2026-11-08 — Compra de Aparelhos, PR 4/5: custo, lucro e relatório)
- **feat: custo e lucro por aparelho comprado e relatório mensal (BR-092, BR-093)** — custo = valor pago +
  peças das OS internas não canceladas, sempre calculado. `GET /api/unidades-serializadas/<id>` ganha
  `custo_aparelho` e `GET /api/vendas/<id>` ganha `custo_aparelho`/`lucro` por item, só para
  `admin`/`financeiro`. Novo `GET /api/compras-aparelhos/relatorio?mes=AAAA-MM` (compras e peças do mês,
  aparelhos vendidos com lucro de cada um, aparelhos parados e capital parado). `tests/test_compras_custo_lucro.py`
  (14 casos).

### Adicionado (2026-11-08 — Compra de Aparelhos, PR 3/5: OS interna)
- **feat: OS interna para consertar aparelho comprado (BR-090, BR-091)** — `POST/PUT /api/ordens` aceitam
  `tipo='Interna'` com `unidade_serializada_id` de um aparelho com compra ativa; o backend força cliente
  "Estoque próprio", sem vendedor e valores 0, e grava o IMEI do aparelho. Abrir move o aparelho
  `disponivel → em_reparo`; finalizar (status ou formulário completo) devolve para `disponivel` sem exigir
  Garantia de Reparo, se não houver outra OS interna aberta; reabrir volta para `em_reparo`. Uma OS não
  troca entre interna e de cliente. OS interna sai do dashboard, dos relatórios, de Garantias e do alerta de
  garantia vencendo. `GET /api/ordens/<id>` passa a devolver `unidade_serializada_id`.
  `tests/test_os_interna.py` (18 casos).

### Adicionado (2026-11-08 — Compra de Aparelhos, PR 2/5: banco + backend)
- **feat: registrar compra de aparelho (BR-083 a BR-089)** — migration `m0003_compras_aparelhos` (tabela
  `compras_aparelhos`, índice único parcial `idx_movimentacoes_caixa_compra_ativa`, coluna
  `os.unidade_serializada_id` reservada para a OS interna). Domínio novo `fluxoly_compras_aparelhos_*` com
  `/api/compras-aparelhos` (listar, registrar, detalhar, cancelar) para `admin`/`financeiro`/`vendedor`.
  Registrar cria, numa transação, a compra, a unidade serializada (`em_reparo` com defeito, `disponivel`
  sem) e a saída de caixa (`origem='compra_aparelho'`, inclusive na troca "abatido na venda"); cancelar
  estorna a saída e devolve a unidade (`devolvido`), só se o aparelho não foi vendido.
  `tests/test_compras_aparelhos.py` (30 casos).

### Documentação (2026-11-08 — Discovery de Compra de Aparelhos)
- **docs: regras e plano da compra de aparelhos para conserto e revenda** — BR-083 a BR-093 em
  `docs/product/BUSINESS_RULES.md` (aprovadas, não implementadas) e
  `docs/engineering/plans/PLAN-compra-aparelhos.md` (compra → unidade → OS interna → venda, saída de caixa
  automática, custo e lucro por aparelho, relatório mensal). Implementação em 4 PRs seguintes.

### Alterado (2026-11-08 — sidebar sem barra de rolagem visível)
- **fix: esconder a barra de rolagem da sidebar** — `SidebarContent` (`frontend/src/components/ui/sidebar.jsx`)
  continua rolável (`overflow-y-auto`, roda do mouse/toque) em telas baixas, mas a barra não aparece
  mais (`scrollbar-width: none` + `::-webkit-scrollbar { display: none }`).

### Removido (2026-11-06 — destinos externos de backup, KI-043)
- **feat: remover backup para Google Drive e por e-mail** — decisão do CTO. Saem `enviar_backup_email`
  e as funções de Google Drive (`fluxoly_storage.py`), as variáveis `IR_FLOW_GOOGLE_DRIVE_BACKUP_DIR`,
  `IR_FLOW_BACKUP_EMAIL`, `IR_FLOW_BACKUP_EMAIL_SENHA` e `IR_FLOW_BACKUP_EMAIL_DESTINO`, e a contenção
  `EXTERNAL_BACKUP_DESTINATIONS_ENABLED` (sem destino externo, não há o que conter). O backup manual,
  o diário automático e a retenção de 90 seguem iguais, só no disco local.
- `POST /api/backup/criar` deixa de devolver `destino_drive`/`erro_drive` (a tela de Backup não usava).
- `tests/test_backup_contencao_externa.py` substituído por `tests/test_backup_somente_local.py`.

### Alterado (2026-11-06 — integração MercadoPhone desligada por padrão, ADR-014 PR 3/3)
- **feat: flag `MERCADO_PHONE_INTEGRATION_ENABLED` (padrão `0`)** — com a flag desligada, todas as
  rotas `/api/integracoes/mercadophone/*` (inclusive o webhook `/os`) respondem 404 e o sync em
  background não inicia, mesmo com token no ambiente ou em `integrations.json`. O código da integração
  permanece no repositório; religar com `MERCADO_PHONE_INTEGRATION_ENABLED=1`.
- Frontend: removido o objeto `integracoes.mercadophone` de `client.js` (não era usado por nenhuma tela).
- 6 testes novos (`tests/test_mercadophone_integracao_desligada.py`); a suíte liga a flag no
  `conftest.py` para manter a cobertura das rotas existentes.

### Removido (2026-11-06 — OS interna IR Phones, ADR-014 PR 2/3)
- **feat: remover a OS interna "IR Phones"** — sai a conversão do tipo "Upgrade" (e do campo
  `interna_ir_phones`) em OS interna com cliente "IR Phones"; o tipo "Upgrade" sai das opções
  (`OS_TIPOS_OPCOES`, `OS_TYPES_FALLBACK`). A validação de vendedor (BR-014) passa a valer para todo
  cliente. OS com cliente "IR Phones" deixam de ser excluídas da lista de garantias.
- **Tabela de preço `ir_phones` removida** — `/api/precos` só aceita `clientes`; Nova/Editar OS sempre
  sugerem preço pela tabela `clientes`; uma chave `ir_phones` legada no arquivo é descartada na leitura.
- **Relatório mensal IR Phones removido** — rotas `/api/relatorios/ir-phones`,
  `/api/relatorios/pdf/ir-phones` e `/relatorios/pdf/ir-phones`, funções em `fluxoly_reports.py` e a aba
  em `Reports.jsx` (a tela agora abre em "Técnicos").
- **E-mail de backup sem padrão da IR Phones** — `IR_FLOW_BACKUP_EMAIL`/`IR_FLOW_BACKUP_EMAIL_DESTINO`
  deixam de ter `ir.phones.flow@gmail.com` como padrão (vazio = envio desligado).
- `installer.iss`: publisher passa de "IR Phones" para "Fluxoly".

### Removido (2026-11-06 — app "Lista de Aparelhos Disponíveis", ADR-014)
- **chore: remover `apps/lista-aparelhos-disponiveis/`** — o app standalone de estoque da IR Phones
  (ADR-013) sai do repositório, junto com o job de CI `estoque_app` e o workflow `estoque-sync.yml`
  (sync 20/20min). Primeiro de 3 PRs do desvínculo do Fluxoly com a IR Phones (ADR-014). ADR-013 vira
  "Substituída"; BR-070..082 viram "Revogadas". Sem impacto no Fluxoly-plataforma (o app não
  compartilhava código com ele).

### Alterado (2026-09-11 — ordem do desempate corrigida para cor → GB → bateria, `apps/lista-aparelhos-disponiveis/`)
- **fix(estoque): cor decide antes do GB (BR-080)** — troca a ordem: cor (alfabética) → GB crescente →
  saúde de bateria decrescente. Correção sobre o ajuste anterior do mesmo dia, que tinha GB antes de cor.

### Alterado (2026-09-11 — ordenação por GB/cor/bateria, `apps/lista-aparelhos-disponiveis/`)
- **fix(estoque): critério de desempate da lista vira GB → cor → bateria (BR-080)** — substitui o
  desempate por preço crescente. GB crescente, cor em ordem alfabética, saúde de bateria decrescente
  (maior % primeiro). Mesmo critério nas duas áreas.
- **feat(estoque): área Estoque ganha desempate extra por dias parado (BR-080)** — depois de GB/cor/
  bateria, quem está parado há mais tempo aparece primeiro. Só na área Estoque — a Geral não conhece
  `diasEmEstoque`. `lib/snapshot.ts` passa a ordenar os dois snapshots separadamente (antes a Geral só
  herdava a ordem da Estoque).
- 6 testes novos em `test/ordenar.test.ts` (100 no total).

### Adicionado (2026-09-11 — Estoque 1/Estoque 2 + reserva automática Estela, `apps/lista-aparelhos-disponiveis/`)
- **feat(estoque): localização manual Estoque 1/Estoque 2 por unidade (BR-081)** — nova coleção no Redis
  (`estoque_local`, ausência = Estoque 1). Área Estoque ganha 3 abas: "Estoque 1", "Estoque 2" (cada uma
  com todas as unidades daquele local) e "Disponíveis" (união dos dois locais, só não reservadas),
  substituindo as abas antigas "Disponíveis"/"Reservados". Novo `POST /api/migrar-estoque` (role=estoque)
  move uma unidade entre os dois locais; botão correspondente em cada linha da tabela.
- **feat(estoque): área Geral só mostra Estoque 1 (BR-081)** — filtro adicional em `montarResposta`, além
  do filtro de reservado já existente (BR-076).
- **feat(estoque): reserva automática para a vendedora "Estela" (BR-082)** — toda unidade com situação
  "Disponível com detalhe" no MercadoPhone é reservada automaticamente no sync (reaproveita o mecanismo
  de reserva do BR-076/077/078, sem filtro novo para sumir da Geral); liberada automaticamente se deixar
  de ter essa situação. Nunca mexe em reserva de vendedor humano — `lib/estela.ts` (função pura,
  totalmente coberta por teste) decide os ajustes, `lib/sync.ts` os aplica após cada sync.
- A funcionalidade de reserva por vendedor (BR-076/077/078) continua existindo sem alteração de
  comportamento, agora em paralelo e independente da localização Estoque 1/2.
- BR-081/082 formalizadas em `docs/product/BUSINESS_RULES.md`. 94 testes vitest (17 novos) + typecheck.

### Adicionado (2026-09-04 — Lista de Aparelhos Disponíveis, ferramenta interna IR Phones — PR #68)
- **feat(estoque): app standalone `apps/lista-aparelhos-disponiveis/`** — ferramenta interna de consulta
  ao estoque de aparelhos (fonte: API nova do MercadoPhone), **fora do Fluxoly-plataforma** (ADR-013).
  Não toca `app.py`, `database.db` nem os projetos Render/Vercel do Fluxoly. Deploy próprio na Vercel
  (Hobby) + Upstash Redis; sync a cada 20 min via GitHub Actions.
- Duas áreas atrás de senha compartilhada (cookie HMAC por papel): **Geral** (vendedores — modelo,
  atributos, saúde de bateria, preço, disponibilidade) e **Estoque** (organizador — + custo/margem/dias
  parado, reserva de unidade, campo Detalhes editável). Snapshots por allowlist de campos — custo/PII/
  IMEI completo nunca alcançam a Geral (teste sobre o JSON inteiro).
- Ciclo ADR-010 completo: Discovery + ADR-013 + Plano Técnico aprovados; QA Manual aprovado; Revisão
  Arquitetural (`/code-review high`) — propriedade central sã, 8 achados corrigidos antes do merge.
- BR-070 a BR-080 formalizadas em `docs/product/BUSINESS_RULES.md`. 77 testes vitest + typecheck no CI
  (job `estoque_app`). Ver `docs/engineering/plans/PLAN-lista-aparelhos-disponiveis.md`.

### Adicionado (2026-08-26 — Fase 3.4 do Fluxoly Design System, Formulários/Detalhe — Tier 3 completo)
- **feat(design-system): NewOrder/EditOrder migram para Panel/LooseMetric (Fatia 3.4.1)** — seis seções
  em `Panel`/`PanelHeader`/`PanelTitle`/`PanelContent`, sem dominante; "Sugestão de serviço" vira
  `LooseMetric`. `NewOrder.jsx` e `EditOrder.jsx` mantidos genuinamente paralelos, única divergência
  intencional (o `.catch()` de `EditOrder` também navega para `/ordens`) documentada em comentário no
  ponto de divergência.
- **fix(design-system): NewOrder/EditOrder tratam rejeição de promise na carga inicial (KI-048)** —
  guarda defensiva `if (loading || !form)` também cobre o branch pré-existente `!osRes?.ok`.
- **feat(design-system): VendaDetalhe migra para Panel/DataTable, Total da venda vira dominante (Fatia
  3.4.2)** — tabela de Itens (7 colunas) migra de `<td>` manual para `DataTable` via `ITENS_COLUMNS`.
- **fix(design-system): VendaDetalhe trata rejeição de promise ao carregar tipos de garantia (KI-048)** —
  3º e último ponto do KI, mesma mensagem de `Vendas.jsx::NovaVenda`.
- **feat(design-system): ChecklistDevice troca Card por Panel (Fatia 3.4.3)** — troca pura de recipiente,
  visualmente neutra (única tela pública/não autenticada do sistema).
- **KI-048 fecha por completo** — todos os pontos do Tier 2 (Fase 3.3) e do Tier 3 (Fase 3.4) corrigidos.
- Ver `docs/engineering/plans/PLAN-design-system-fase3.4-formularios.md` para o registro completo (3
  fatias, revisão final whole-branch: 2 Important + 2 Minor corrigidos antes do merge).

### Adicionado (2026-08-26 — Fase 3.3 do Fluxoly Design System, Fatia 3.3.5: Clientes — Tier 2 completo)
- **feat(design-system): Clientes migra para DataTable/LooseMetric** — contadores viram `LooseMetric`
  (sem dominante); tabela migra para `DataTable` com `onRowClick` abrindo o perfil.
- **fix(design-system): Clientes ganha estado de erro dedicado (KI-049)** — `loadError` + `ErrorState`
  com retry.
- **fix(design-system): PerfilCliente trata rejeição de promise (KI-048)** — último ponto do Tier 2;
  KI-048 fecha por completo no Tier 2, resta só o Tier 3 (Fase 3.4).
- Ver `docs/engineering/plans/PLAN-design-system-fase3.3-operacao.md` para o registro completo (5 fatias,
  Fase 3.3 encerrada).

### Adicionado (2026-08-26 — Fase 3.3 do Fluxoly Design System, Fatia 3.3.4: Financeiro)
- **feat(design-system): Financeiro migra para DataTable/Panel** — Saldo em caixa vira métrica dominante
  (`Panel`, saiu do header); Movimentações/Contas a Pagar/Contas a Receber migram para `DataTable`.
- **fix(design-system): Financeiro trata rejeição de promise ao carregar saldo (KI-048)** — achado fora do
  escopo original do KI (auditoria anterior não cobriu a busca de saldo do componente pai).
- Ver `docs/engineering/plans/PLAN-design-system-fase3.3-operacao.md` para o registro completo.

### Adicionado (2026-08-26 — Fase 3.3 do Fluxoly Design System, Fatia 3.3.3: Stock)
- **feat(design-system): Stock migra para DataTable/Panel/LooseMetric** — Valor Total vira métrica
  dominante (`Panel`); Lotes/Unidades/Críticos viram `LooseMetric`; Reposição sugerida e lista principal
  migram para `DataTable`.
- **fix(design-system): Stock trata rejeição de promise ao carregar itens (KI-048)** — `fetchItems` sem
  `try/catch`.
- Ver `docs/engineering/plans/PLAN-design-system-fase3.3-operacao.md` para o registro completo.

### Adicionado (2026-08-26 — Fase 3.3 do Fluxoly Design System, Fatia 3.3.2: Vendas)
- **feat(design-system): Vendas Histórico migra para DataTable** — sem métrica dominante, `getRowProps`
  preserva `data-testid`/`data-context-row` do `nav-context-highlight`.
- **feat(design-system): Nova Venda usa Panel no resumo/pagamento e na confirmação** — único elemento
  dominante desta tela, total em destaque.
- **fix(design-system): Nova Venda trata rejeição de 3 promises sem `.catch` (KI-048)** —
  `tiposGarantiaApi`/`clientesApi`/`unidadesApi`.
- Ver `docs/engineering/plans/PLAN-design-system-fase3.3-operacao.md` para o registro completo.

### Adicionado (2026-08-26 — Fase 3.3 do Fluxoly Design System, Fatia 3.3.1: DataTable + Orders + Kanban)
- **feat(design-system): DataTable ganha `getRowProps`** — propaga atributos por linha (ex.:
  `data-testid`/`data-context-row` do `nav-context-highlight`) sem sobrescrever `className`/`onClick`/
  `tabIndex` fixos do componente.
- **fix(design-system): DataTable corrige acessibilidade da linha clicável (KI-053)** — responde a Espaço
  além de Enter, `role="button"` quando `onRowClick` está presente.
- **feat(design-system): Orders migra para DataTable/LooseMetric** — stats bar vira `LooseMetric` (sem
  dominante), `OrderTable.jsx` migra de HTML cru para `DataTable` (primeiro consumidor real).
- Kanban auditado contra os 5 princípios de composição — nenhum achado.
- **fix(design-system): Kanban trata rejeição de promise ao carregar ordens (KI-048)** — `fetchOrdens`
  ganhou `.catch()`, mesmo padrão de `Orders.jsx`.
- Ver `docs/engineering/plans/PLAN-design-system-fase3.3-operacao.md` para o registro completo (5 fatias).

### Adicionado (2026-08-25 — Fase 3.2 do Fluxoly Design System, Vitrine)
- **feat(design-system): Login usa Panel da Foundation v2, respiro real** — form migra da moldura manual
  para `Panel`/`PanelContent`.
- **feat(design-system): Sidebar agrupado pelos 6 Pilares Macrossistêmicos** — 18 itens de navegação
  organizados em seções (Vendas/Operação/Financeiro/Relacionamento/Serviços/Inteligência + Administração),
  seção some quando vazia para o perfil da sessão. Duplicata histórica de `/compras` removida.
- **feat(design-system): Dashboard com hierarquia real** — Faturamento vira métrica dominante (`Panel`,
  número hero), outros 7 KPIs viram `LooseMetric`, Resumo Financeiro vira `ListBlock`. `KpiCard.jsx` fica
  sem consumidor — **KI-056** registrado, não removido (decisão do CTO).
- Landing auditada por consistência de marca — nenhum achado.
- 2 gaps reais do próprio plano corrigidos durante a execução (colisão de texto duplicado em testes do
  Sidebar/Dashboard) — ver `docs/operations/PROJECT_STATUS.md` para o detalhe de cada ruling.
- **fix(design-system): skeleton do Dashboard e contraste do rótulo do Sidebar** — 2 achados Important da
  revisão final whole-branch, corrigidos antes do merge: `DashboardSkeleton` atualizado para a composição
  nova (Panel dominante + `LooseMetric`s, em vez do grid antigo de 8 KPIs); rótulos de seção do Sidebar
  ajustados de `/40` (~3.3:1) para `/50` (~4.65:1), acima do piso WCAG AA de 4.5:1.
- Ver `docs/engineering/plans/PLAN-design-system-fase3.2-vitrine.md` para o registro completo.
- **Mergeado em `main` (PR #62, squash, commit `deb460c5`, 2026-08-25)** — CI 8/8 (×2) verde, produção
  saudável pós-merge.

### Docs (2026-08-24 — KI-055 decidido: manter `system-ui` no corpo de texto)
- Achado na revisão de código do PR #61: `BRAND_IDENTITY.md` §10.2 afirmava que Onest era "mantida" para
  UI/corpo de texto — nunca foi verdade (`body` sempre usou `system-ui`), e com a troca do wordmark para
  Space Grotesk nesta mesma branch, Onest passou a ter zero uso em todo o código. Decisão (CTO): não
  aplicar Onest ao corpo de texto por ora — escopo desproporcional (afetaria toda tela do produto),
  decisão original de 2026-08-18 anterior à reinvenção de marca "Pulse", sem queixa de UX registrada
  contra `system-ui`. `BRAND_IDENTITY.md` §10.2 e `KNOWN_ISSUES.md` (KI-055) atualizados para refletir a
  decisão explícita; revisitável na Fase 3.2 (Vitrine) com uma tela de referência concreta.

### Corrigido (2026-08-24 — ícone Pulse aplicado, KI-054 resolvido)
- **fix(brand): substituir o monograma "F" pelo ícone Pulse real** — os 5 arquivos em `frontend/public/
  brand/fluxoly-icon-*.svg` e `favicon.svg` usavam o monograma "F" da decisão de identidade anterior
  (2026-08-18), nunca substituídos pela direção "Pulse" (traço de batimento/ECG + seta ascendente)
  decidida em 2026-08-20. O path SVG real foi recuperado do artifact de exploração "Fluxoly Identity
  Directions" (Claude Design) e aplicado às 5 variações de cor da tabela `BRAND_IDENTITY.md` §10.1
  (`red`/`white`/`cyan`/`gray`/`inverted` — `cyan` é novo, substitui o arquivo `black` que não fazia
  parte da tabela oficial). QA visual confirmada em `/login` e `/` (Chrome real).
- Achado reportado pelo usuário (CTO): a verificação anterior desta mesma sessão (ver entrada abaixo)
  havia checado só a existência/uso dos arquivos, não o conteúdo do SVG, e concluído erroneamente que o
  ícone já estava correto.

### Corrigido (2026-08-24 — wordmark em Space Grotesk)
- **fix(brand): aplicar Space Grotesk no wordmark** — `BRAND_IDENTITY.md` §10.2 já decidia em 2026-08-20
  trocar a fonte do logotipo "Fluxoly" de Onest para Space Grotesk Bold, mas o código (`.font-wordmark`
  em `index.css`) continuava usando Onest 700. `frontend/index.html` passa a carregar Space Grotesk:700
  via Google Fonts; `.font-wordmark` usa a fonte nova. Sem mudança de lógica — só troca de fonte no
  wordmark (Login, Sidebar); corpo de texto do app não é afetado (usa `system-ui`, não Onest). QA visual
  confirmada em `/login` (`document.fonts.check` + inspeção visual, Chrome real).
- **docs(brand): corrigir nota de "pendente" desatualizada sobre a cor em `BRAND_IDENTITY.md` §10.3** —
  cor de assinatura `#FF3D5A` já estava implementada desde a Fase 3.0 (PR #59), mas o documento ainda a
  descrevia como pendente.
- **KI-054 registrado:** o ícone da marca ainda é o monograma "F" da decisão anterior (2026-08-18), não
  o traço Pulse (ECG + seta) decidido em 2026-08-20 — nenhuma arte vetorial do ícone novo foi produzida.
  Achado ao investigar um relato do usuário; a primeira verificação desta mesma sessão havia concluído
  erroneamente que o ícone já estava correto (corrigido antes do commit).

### Adicionado (2026-08-22 — Fase 3.1 do Fluxoly Design System, Foundation v2)
- **Recipientes de composição** `Panel`/`ListBlock`/`LooseMetric` em `components/ui/` — evoluem `Card`
  como recipiente universal (dominante/bloco de lista/métrica solta), ainda não usados em nenhuma página.
- **`DataTable`** real da Foundation (header sticky opcional, linha clicável com suporte a teclado).
- **Tema único de gráfico** (`lib/chart-theme.js`) — os 3 gráficos do Dashboard passam a usar
  `var(--color-*)` para grade/eixo/cursor (reagem à troca de tema); as cores categóricas das séries
  (`--color-chart-1..5`) permanecem fixas nos dois modos, por design (ver `index.css`).
- **KI-050 resolvido** — 9 telas migradas de classe Tailwind crua para tokens de tema
  (`text-success`/`warning`/`destructive`/`info`).
- Ver `docs/engineering/plans/PLAN-design-system-fase3.1-foundation-v2.md` para o registro completo.

### Adicionado (2026-08-20 — Fase 3.0 do Fluxoly Design System, infraestrutura de tema)
- **feat(design-system): infraestrutura de tema (Fase 3.0)** — Light Mode e Dark Mode, toggle
  automático/claro/escuro, persistência de preferência.
- **`ThemeContext`/`useTheme()`** com persistência em `localStorage` (chave `fluxoly-theme`) e sincronia
  com a preferência do sistema (`prefers-color-scheme`).
- **`index.css` restruturado em duas camadas** — tokens de Light Mode como base, overrides de Dark Mode via
  `@media (prefers-color-scheme)` + `data-theme` manual. Identidade Pulse (`#FF3D5A` vermelho-sinal,
  `#29E0C9` ciano de fluxo) aplicada aos tokens de cor; cores semânticas de estado recalibradas para WCAG
  AA em fundo claro.
- **Script anti-FOUC** em `index.html`, evitando flash da cor errada no primeiro paint ao recarregar com
  tema fixado.
- **Toggle de 3 estados** (automático/claro/escuro) na Sidebar.
- **Nenhum componente redesenhado** — só infraestrutura de tema; Fase 3.1 (Foundation v2) trata a
  composição visual dos componentes.
- **Decisão do CTO (revisão final, 2026-08-20):** o tema padrão para quem não tem preferência salva
  permanece Dark (não segue o SO) até a Fase 3.1 migrar as 9 telas com classes Tailwind hardcoded
  listadas em KI-050.
- Mergeado em `main` (PR #59, commit `5b6237df`).
- Ver `docs/engineering/plans/PLAN-design-system-fase3.0-theme-infra.md` para o registro completo.

### Adicionado (2026-08-20 — Fase 2 do Fluxoly Design System, PR 5/Vendas+VendaDetalhe+Financeiro+Clientes)
- **Variante taxonômica `variant="tag"` no `Badge` da Foundation** — distinta das 5 variantes de
  severidade (`success`/`warning`/`error`/`info`/`neutral` = "como está indo"; `tag` = "que tipo de coisa é
  isso"). Cor neutra única, sem tom por valor (perda intencional da diferenciação cromática que existia
  antes). Resolve a pendência do PR 4: `ORIGEM_BADGE` (duplicado em `Vendas.jsx`/`UnidadesSerializadas.jsx`,
  centralizado em `lib/constants.js`) e `CATEGORIA_BADGE` (`Produtos.jsx`) migrados.
- **Status genuíno migrado para o Badge semântico** em `Vendas.jsx`/`VendaDetalhe.jsx`
  (`vendaStatusVariant`, compartilhado via `lib/constants.js`), `Financeiro.jsx` (`tipoVariant`/
  `statusContaVariant`, local) e `Clientes.jsx` (`GarantiaBadge`, antes nem usava o componente `Badge`).
- **`FilterBar`/`FilterSelect`/`FilterInput`** nas 3 listas; `EmptyState`/`ErrorState`/`ListSkeleton` nos
  fluxos de carga; `interactiveRowClassName`; ícones lucide → Phosphor nos 4 arquivos.
- **Nenhuma lógica de negócio alterada** — confirmado por diff isolado de todos os handlers de cada
  arquivo contra `main`.
- **Testes:** 18 novos (`Vendas`/`Financeiro`/`Clientes` nunca tinham teste antes). Suíte completa 89/89,
  lint 0 erros, build ok. `VendaDetalhe.jsx` sem teste novo — mudança puramente visual, mesmo critério do
  PR 3.
- Ver `docs/engineering/plans/PLAN-design-system-fase2.md` (seção "PR 5") para o registro completo.

### Adicionado (2026-08-20 — Fase 2 do Fluxoly Design System, PR 4/Estoque+Unidades+Produtos)
- **Status genuíno migrado para o Badge semântico** em `Stock.jsx` (disponibilidade de estoque + prioridade
  de reposição), `Produtos.jsx` (disponibilidade + condição) e `UnidadesSerializadas.jsx` (5 estados) —
  cada domínio com sua própria função de mapeamento local, mesma disciplina do `getStatusVariant` de OS.
- **Badges categóricos (`CATEGORIA_BADGE` em `Produtos.jsx`, `ORIGEM_BADGE` em `UnidadesSerializadas.jsx`,
  duplicado em `Vendas.jsx`) deliberadamente não migrados** — não têm variante de severidade
  correspondente no `Badge`. Decisão do CTO após checkpoint arquitetural: fica pendente para antes do PR 5.
- **`FilterBar`/`FilterSelect`/`FilterInput`** nas 3 barras de filtro; `EmptyState`/`ErrorState`/
  `ListSkeleton` nos 3 fluxos de carga; `Checkbox` do design system; ícones lucide → Phosphor.
- **Nenhuma lógica de negócio alterada** — confirmado por busca no diff completo por handler de negócio e
  diff isolado byte-a-byte de `handleSubmit`/`handleDelete`/`carregar`/`salvar` contra `main`.
- **Testes:** 12 novos (as 3 páginas nunca tinham teste antes). Suíte completa 70/70. Lint 0 erros.
- Ver `docs/engineering/plans/PLAN-design-system-fase2.md` (seção "PR 4") para o registro completo.

### Adicionado (2026-08-19 — Fase 2 do Fluxoly Design System, PR 3/Orders+Kanban+NewOrder+EditOrder)
- **Cor de status de OS unificada**: `getStatusVariant` (`lib/constants.js`) substitui `getStatusColor`
  como fonte única de verdade, consumida por `OrderStatusBadge` (Orders/EditOrder) e pelo `Kanban.jsx` —
  que antes redefinia cor por coluna de forma independente e divergente.
- **`OrderFilters.jsx` migrado** para `FilterBar`/`FilterSelect`/`FilterInput` da Foundation — primeira
  aplicação real desses componentes desde o PR 1.
- **`Orders.jsx`/`Kanban.jsx`**: `ListSkeleton`/`ErrorState` com retry na carga inicial; card do Kanban
  ganhou `OrderStatusBadge` (import que já existia, nunca usado).
- **Ícones lucide → Phosphor**, `rose-500` (fora da paleta) → `text-primary` em `NewOrder.jsx`/
  `EditOrder.jsx`; 2 desvios de radius/shadow corrigidos no Kanban.
- **Nenhuma lógica de negócio alterada** — confirmado por busca no diff por toda função de regra de
  negócio (submit, drag-and-drop, reparo/peça, `create`/`update`/`delete`/`patchStatus`).
- **Testes:** 13 novos (`OrderStatusBadge`/`Orders`/`Kanban` nunca tinham teste antes). Suíte completa
  58/58. Lint 0 erros.
- Ver `docs/engineering/plans/PLAN-design-system-fase2.md` (seção "PR 3") para o registro completo.

### Adicionado (2026-08-19 — Fase 2 do Fluxoly Design System, PR 2/ChecklistDevice golden standard)
- **`ChecklistDevice.jsx` redesenhado** para os tokens Fluxoly — única tela pública do sistema, sem login.
  Paleta própria (gradiente slate/azul) substituída por `bg-background`/`bg-card`/`border-border`; radius
  fora da escala (`rounded-3xl`/`rounded-2xl`) substituído por `rounded-xl`; ícones lucide → Phosphor; cor
  decorativa fora da paleta (`cyan-300`) → `text-primary`; `ErrorState`/`Badge`/`Checkbox` da Foundation
  aplicados; header com ícone + wordmark Fluxoly (mesmo padrão de `Login.jsx`); `Reveal` no conteúdo.
- **Nenhuma lógica de negócio alterada** — handlers de áudio/microfone/câmera e payload de
  `saveChecklist` idênticos ao original.
- **Dependência resolvida antes deste PR:** PR #53 (aplicação da marca — Onest + ícone corrigido) foi
  mergeado primeiro, por decisão do CTO, já que o golden standard depende da marca estar de fato aplicada.
- **Testes:** 5 novos (Vitest), suíte completa 45/45. Lint 0 erros.
- Ver `docs/engineering/plans/PLAN-design-system-fase2.md` (seção "PR 2") para o registro completo.

### Adicionado (2026-08-19 — Fase 2 do Fluxoly Design System, PR 1/Foundation)
- **Vocabulário visual compartilhado** para migrar as 21 páginas operacionais ainda fora do Design System
  (auditoria completa em `docs/engineering/plans/PLAN-design-system-fase2.md`): `Badge` com variantes
  semânticas (`success`/`warning`/`error`/`info`/`neutral`), `EmptyState`/`ErrorState`/`ErrorBanner`/
  `ListSkeleton`/`CardGridSkeleton`, `FilterBar`/`FilterSelect`/`FilterInput`/`DateRangeFilter`/
  `ClearFiltersButton`, `Reveal` (Motion discreto) e `lib/interaction.js`.
- **Nenhuma tela redesenhada neste PR** — só `components/ui/` e `lib/`. Migração real das 24 páginas fica
  para os PRs 2-8, um de cada vez, conforme o plano aprovado pelo CTO.
- **Testes:** 26 novos (Vitest), suíte completa 40/40. Lint 0 erros.
- Ver `docs/engineering/ENGINEERING_GUIDE.md` §3.3 para as convenções e
  `docs/engineering/plans/PLAN-design-system-fase2.md` para o plano completo de 8 PRs.

### Adicionado (2026-08-17 — Landing Page institucional, PR #49)
- **Implementação em código das 14 seções** especificadas em `docs/product/features/LANDING_PAGE.md`
  (PR #44, doc-only): `Landing.jsx` + `components/landing/` (mapeamento 1:1 com a spec), copy centralizada
  em `content.js` — extraída literalmente da spec, itens `[DEFINIR]` (preço, prova social, trial)
  preservados como placeholder, nenhum dado comercial inventado.
- **Roteamento:** único ponto de mudança em `ProtectedRoute` (`App.jsx`) — `/` deslogado renderiza a
  Landing pública; `/` autenticado continua o Dashboard no `Layout`, sem regressão; todas as outras rotas
  protegidas continuam redirecionando para `/login` normalmente. `AuthContext`/`Login.jsx`/backend/banco
  não foram alterados.
- **Design System aditivo:** `Accordion` novo (`@radix-ui/react-accordion`, único pacote novo) e
  `size="lg"` no `Button`. Mockups de Hero/"Visão do sistema" usam Card/Skeleton reais, não screenshot nem
  banco de imagens.
- **Testes:** 18/18 (7 novos — `App.test.jsx`/`Landing.test.jsx`); `IntersectionObserver` (ausente em
  jsdom) recebeu stub em `test/setup.js` para o `whileInView` do Motion.
- **CI:** primeira execução falhou por lockfile desatualizado (`@emnapi/core`/`@emnapi/runtime` — mesma
  causa já vista em KI-026), corrigido em commit próprio; segunda execução 8/8 verde.
- Ver `docs/engineering/plans/PLAN-landing-page-implementacao.md` para o registro completo.

### Adicionado (2026-08-16 — Fase 1 do Fluxoly Design System, PRs #41-#47)
- **Design System formalizado:** amendment do ADR-001 (shadcn/ui como padrão de composição sobre o Radix
  UI já adotado, sem substituí-lo) e `ENGINEERING_GUIDE.md` §3.2 documentam a decisão de reaproveitar a
  escala padrão do Tailwind para spacing/radius/shadow (sem tokens customizados) e a paleta de marca já
  existente (`#FF0125` + fundo escuro) — nada derivado do site de um concorrente usado como referência de
  mercado (`docs/product/features/LANDING_PAGE.md`, especificação, sem implementação).
- **Componentes novos:** `Card`, `Skeleton`, `Tooltip`, `Sheet`, `Sidebar` (`frontend/src/components/ui/`)
  seguindo o padrão já em uso (`cva` + `cn()`, sem `data-slot`), `components.json` do CLI shadcn.
- **Phosphor Icons** adotado para componentes novos/migrados (Shell, Dashboard); `lucide-react` permanece
  no resto do frontend, sem migração retroativa.
- **Motion** adotado para microinterações isoladas — drawer mobile do Sidebar (`AnimatePresence`,
  `useReducedMotion` respeitado). Tooltip/Sheet usam transição CSS via `data-state`, não Motion (Radix
  `Presence` não detecta a animação via WAAPI do Motion — regra registrada em `ENGINEERING_GUIDE.md` §3.2).
- **Shell migrado:** `Layout.jsx` reescrito sobre `SidebarProvider`/`Sidebar`, elimina a duplicação de
  markup entre desktop/mobile que existia antes. Comportamento de filtro por perfil e rota ativa
  preservado 1:1. Ganhou `aria-label="Sair"` no botão de logout (gap de acessibilidade corrigido).
- **Dashboard migrado:** 4 estados explícitos — loading (skeleton no formato do layout final), success
  (preservado), empty (novo, quando não há nenhum indicador no período) e error (novo, banner/tela cheia
  com "Tentar novamente", substituindo o `toast.error` que desaparecia sozinho).
- **Testes de componente inaugurados:** Vitest + Testing Library (0% → 11 testes, `Layout.test.jsx` e
  `Dashboard.test.jsx`), job `Frontend Unit Tests` no CI (não-bloqueante nesta fase).
- **QA Manual** (3 perfis — admin/técnico/vendedor, backend real e descartável, nunca `database.db`):
  Shell renderiza corretamente e filtra o menu por perfil em todos os três (confirmado contra contas reais
  seedadas, não só o teste automatizado); navegação por teclado com foco visível confirmada. Achado de
  ambiente, não de código: sessão de login não persistiu no navegador de automação usado nesta QA —
  reprodução do `KI-027` já documentado, confirmado via `curl` que backend/proxy/sessão funcionam
  corretamente fora do navegador de automação; o estado de erro do Dashboard acabou sendo validado
  organicamente por esse mesmo achado. Resize de viewport da ferramenta de automação não afetou o
  viewport real da página nesta sessão — o drawer mobile não pôde ser clicado interativamente, validado
  só por revisão de código + teste automatizado do hook `useIsMobile`.
- **Bundle:** chunk principal (Shell, não-lazy) cresceu de 115 kB para 167 kB gzip — Motion agora faz parte
  do carregamento inicial; chunk do Dashboard (lazy, por rota) não teve impacto no bundle principal.
  Otimização futura possível (não implementada): lazy-load do caminho mobile-only do Sidebar.
- Ver `docs/engineering/plans/PLAN-design-system-fase1.md` para o registro completo de todas as etapas.

### Adicionado/Corrigido (2026-08-17 — feat/lgpd-compliance-fase1, KI-029 Fase 1/KI-043/KI-044/KI-045)
- Ciclo `ADR-010` completo (Discovery → Decisões do CTO → Plano Técnico → Implementação → Testes → QA
  Manual → Revisão Arquitetural → Encerramento) para a Fase 1 de LGPD/Compliance — ver
  `docs/product/research/DISCOVERY_LGPD.md` e `docs/engineering/plans/PLAN-LGPD-Compliance.md`.
  **Branch auditada e com CI 6/6 verde, ainda não mergeada em `main`** — merge é decisão separada do CTO.
- **KI-029 Fase 1:** os dois arquivos `.db` reais ainda rastreados em `main` (`backup-20260429-015724.db`,
  `database-pre-cleanup-20260517-123834.db`) removidos do índice (`git rm --cached`, não do histórico);
  `.gitignore` reforçado para impedir qualquer `*.db`/`*.db-shm`/`*.db-wal` novo na raiz do repositório.
  Fase 2 (reescrita de histórico) permanece separada, não executada, exige autorização própria.
- **KI-043:** `GOOGLE_DRIVE_BACKUP_DIR`/`BACKUP_EMAIL_SENHA_APP` (`fluxoly_config.py`) passam a ficar
  vazios independente do ambiente enquanto `EXTERNAL_BACKUP_DESTINATIONS_ENABLED` (hardcoded `False`) não
  for reativado por decisão de produto — backup local não afetado, log de aviso estruturado no boot se um
  destino externo configurado for ignorado. Criptografia de backup em repouso fica pós-release.
- **KI-044:** novo `POST /api/clientes/<id>/anonimizar` (admin-only) mascara PII preservando o `id` do
  cliente e toda FK em `os.cliente_id`/`vendas.cliente_id` — complementa, não substitui, o `DELETE`
  existente (que continua só para clientes órfãos, sem histórico vinculado). `audit_log` registra a ação.
- **KI-045:** `GET /api/clientes`/`GET /api/clientes/<id>` omitem `cpf_cnpj` da resposta para quem não é
  `admin`/`financeiro`; escrita permanece liberada a todo perfil (decisão explícita do CTO). Edição por
  perfil restrito sem `cpf_cnpj` no payload preserva o valor existente em vez de apagá-lo (sentinel
  `CPF_NAO_INFORMADO`, `fluxoly_clientes_service.py`) — achado durante a própria implementação, corrigido
  antes de virar bug real.
- Mecanismo parametrizável de mascaramento/expurgo de `audit_log` (`fluxoly_audit.py`) implementado e
  testado, mas **inativo em produção**: sem `AUDIT_LOG_PII_MASK_APOS_DIAS`/`AUDIT_LOG_EXPURGO_APOS_DIAS`
  configuradas (sem default), a thread de manutenção nunca é iniciada — prazos reais aguardam orientação
  jurídica/operacional, não são decisão de engenharia.
- 33 testes novos (`test_backup_contencao_externa.py`, `test_clientes_anonimizacao.py`,
  `test_clientes_pii_acesso.py`, `test_audit_log_retencao.py`); suíte completa 798 passed / 5 failed
  (KI-030, pré-existente, ambiente Windows local, não relacionado); QA Manual 14/14 contra backend real e
  descartável; Revisão Arquitetural aprovada com ressalva (**KI-046**, novo — busca de clientes por CPF
  vaza sinal de match/no-match antes do filtro de leitura do KI-045 decidir a visibilidade, baixo impacto,
  pós-release, não bloqueia este ciclo).
- **Fora de escopo deste ciclo, deliberadamente:** KI-029 Fase 2, criptografia completa de backup, prazos
  reais de retenção do `audit_log`, documento de privacidade, validação jurídica formal, KI-046.

### Corrigido (2026-08-15 — fix/seed-demo-tipo-garantia, KI-041)
- `scripts/seed_demo.py` não criava nenhum registro em `tipos_garantia`, bloqueando **Finalizar OS** e
  **Registrar Venda** (campo obrigatório) para qualquer perfil no Ambiente Demo. Achado durante a
  Homologação Interna Controlada (2026-08-15, ver `docs/engineering/plans/
  ROTEIRO-homologacao-interna-controlada.md`). Correção: nova função `seed_tipos_garantia()`, 1 registro
  sintético ("Garantia Padrão", 3 meses) — decisão Discovery/Plano Técnico do CTO, auditada na PR #37
  (documentação) antes da implementação. Sem checagem de duplicata: `_garantir_banco_vazio()` já garante
  banco limpo no início do seed. Testado localmente contra banco descartável (nunca `database.db`):
  1 linha criada em `tipos_garantia`, `ruff check` limpo, 56/56 testes de garantia passando. PR #38, CI
  6/6 verde. Reexecução pós-fix confirmada no Demo real, não só localmente: Finalizar OS e Registrar
  Venda concluídos com sucesso, novo backup `seed-inicial` gerado, Demo restaurado a esse estado limpo,
  produção intocada durante toda a operação. KI-041 fechado (`KNOWN_ISSUES.md`)

### Adicionado
- `docs/company/BRAND_IDENTITY.md` — Constituição da Marca Fluxoly V1.0 (Product Owner): nome, 6 pilares macrossistêmicos, escopo negativo, promessa de mercado, visão 2030, cronograma de transição técnica de marca. Registra gap conhecido: promessa de rastreamento por IMEI sem suporte na tabela `estoque` hoje
- `docs/engineering/adr/ADR-006.md` — decisão de reorganizar `docs/` em `company/`, `engineering/`, `product/`, `operations/` por audiência, com mapeamento completo arquivo-a-arquivo e cronograma de rename
- Preenchidos a partir de `BRAND_IDENTITY.md`: `docs/company/VISION.md` (Missão, Visão, Valores, Objetivo de Longo Prazo, Critérios de Sucesso) e `docs/company/PRODUCT_REQUIREMENTS.md` (Mercado-alvo, O que NÃO faz, Diferenciais, parte de Problemas Resolvidos) — Persona, Quem Decide a Compra e Modelo de Monetização seguem `TODO`, não respondidos pelo documento de marca
- `docs/product/FEATURE_MATRIX_TEMPLATE.md` seção 1 atualizada com os seis pilares e o gap de rastreamento por IMEI

### Adicionado (cont.)
- `docs/company/PRODUCT_REQUIREMENTS.md` — Persona Primária (Cliente: Dono de Loja de Dispositivos Móveis Premium) preenchida com input direto do Product Owner: perfil, como trabalha hoje, dores, objetivos, o que compra, critérios de compra, objeções, e por que escolhe a Fluxoly. Confirma na prática o gap de rastreamento por IMEI já registrado (dor "IMEIs perdidos ou difíceis de localizar")
- `docs/company/PRODUCT_REQUIREMENTS.md` — "Quem Decide a Compra" respondido (dono da loja); "Modelo de Monetização" parcialmente respondido (assinatura mensal confirmada, estrutura de precificação segue `TODO`); "Problemas Resolvidos" e "Diferenciais" complementados com dados reais de objeção de venda
- `docs/company/PRODUCT_REQUIREMENTS.md` — substituída a ideia de uma única "Persona Secundária" por seção própria "Personas Operacionais" (Usuários, distintos do Cliente que compra): Vendedor preenchido com objetivo/responsabilidades/dores/expectativas; Técnico, Financeiro, Estoque e Administrador registrados como `TODO`, com nota sobre quais já existem como perfil no código hoje (`admin`, `tecnico`, `vendedor`) e quais não existem ainda (Financeiro, Estoque como perfil de usuário). Tabela "Perfil → Interface" registrada como visão de produto, não feature implementada
- `docs/company/VISION.md` — novo valor: "cada profissional deve enxergar apenas o que precisa para executar seu trabalho com máxima eficiência" (princípio de UX derivado do diferencial de interfaces por perfil)
- `docs/engineering/ENGINEERING_GUIDE.md` — critério de UX correspondente adicionado às decisões de frontend (interface por perfil, não tela única para todos)
- `docs/product/BUSINESS_RULES.md` — livro de regras de negócio (BR-001 a BR-022): regras implementadas extraídas linha a linha do código (Autenticação, Estoque, OS, Compras — 16 regras, todas com fonte no arquivo/função) e regras especificadas de Vendas extraídas de `VENDAS.md` (6 regras). Registra achado: `data_finalizado` é limpo ao reabrir uma OS (BR-013), comportamento observado mas não confirmado como decisão deliberada. Registra 3 regras candidatas citadas em conversa, ainda não formalizadas em `VENDAS.md`
- `docs/engineering/DATA_DICTIONARY.md` — governança de dados campo a campo, complementar a `DATABASE.md`: quem cria/altera/exclui/vê cada tabela. Achado: rotas de mutação de OS e Estoque na API aceitam qualquer perfil autenticado, sem restrição — diferente de Usuários (admin-only) e Shopping List (`admin`/`tecnico`/`comprador`). Achado adicional: perfil `"comprador"` checado no código de Shopping List não é um valor de `perfil` documentado no schema (`admin`\|`tecnico`\|`vendedor`) — candidato a esclarecimento com o Product Owner
- `docs/company/OPERATION_SYSTEM.md` — ciclo completo da loja (Fornecedor → Pós-venda). Blocos fundamentados no código/spec existente: Venda, Entrada de Estoque, Assistência, Reserva, Troca (parcial), Garantia (parcial), Compra (parcial). Blocos deixados `TODO` por ausência total de informação: Fornecedor, Cadastro, Anúncio, Entrega, Motoboy, Pós-venda, Financeiro e Caixa (estes dois últimos por decisão explícita de adiamento já registrada em `VENDAS.md`, não por lacuna de documentação)
- `docs/company/DECISION_LOG.md` — histórico executivo de decisões de produto, distinto de ADR (arquitetural). Populado com 10 decisões já tomadas e catalogadas de suas fontes originais (7 de `VENDAS.md`, 2026-07-09; 3 de marca/documentação/UX, 2026-07-10) — nenhuma decisão nova, só indexação cronológica
- `docs/company/NON_FUNCTIONAL_REQUIREMENTS.md` — formulário de requisitos não-funcionais (capacidade, desempenho, timeout de reserva de IMEI, disponibilidade, RTO/RPO de backup, upload, offline, navegadores) — majoritariamente `TODO`, com referências existentes citadas como contexto (gatilhos de revisão de `ADR-003.md`, meta de latência pontual da Sprint 5), nunca como resposta
- Regra de governança de documentação registrada em `docs/README.md`: nenhum documento novo sem responder "que decisão ele ajuda a tomar?"; backlog de documentação futura identificada (`UX_GUIDELINES.md`, `FEATURE_SPEC_FINANCEIRO.md`, `FEATURE_SPEC_ESTOQUE.md`)
- `docs/product/PRODUCT_BACKLOG.md` — fila priorizada de épicos (P0 a P3): Vendas/Clientes/IMEI Individual (P0), Financeiro/Caixa/Dashboard Executivo (P1), WhatsApp/CRM (P2), Multiempresa (P3). Status de cada épico verificado contra o código real antes de publicar (ex.: Dashboard já existe parcialmente — distinção feita entre o básico atual e o "Dashboard Executivo" completo)
- `docs/company/RELEASE_STRATEGY.md` — proposta de versionamento (1.0 já em produção, 1.1 a 2.0 propostas), reconciliando o esboço original desta conversa com as decisões já tomadas desde então (Vendas desacoplado de Caixa/Financeiro). Marcado como proposta técnica — decisão final de nomes/escopo por versão é do Product Owner, mesmo padrão do ADR-005
- `docs/engineering/FUTURE_TECH_EVALUATIONS.md` (2026-08-05) — ideias técnicas de longo prazo (Next.js para landing/marketing, BetterAuth, PostgreSQL, Supabase, Redis, Resend, Firebase), extraídas de uma proposta externa de evolução do Fluxoly para SaaS, cada uma com contexto/benefícios/riscos/momento recomendado de avaliação. Explicitamente não-vinculante — nasce ADR só quando houver decisão real a tomar. Indexado em `docs/README.md`

### Modificado
- Toda a árvore `docs/` reorganizada por audiência (ver `docs/engineering/adr/ADR-006.md` para o mapeamento completo e critério de cada pasta); todos os links relativos entre documentos corrigidos
- `CLAUDE.md`: árvore de "Estrutura de Documentos" e tabela "Leitura Obrigatória" atualizadas para os novos caminhos; `BRAND_IDENTITY.md` adicionado como leitura fundacional
- Rename "Assistência System" → "Fluxoly" (camada de negócio: `README.md`, `CLAUDE.md`, `docs/product/FEATURE_MATRIX_TEMPLATE.md`) e → "Fluxoly Platform" (camada técnica: `docs/engineering/*.md`, `docs/operations/PROJECT_STATUS.md`, `docs/operations/ROADMAP.md`), conforme cronograma de `BRAND_IDENTITY.md` seção 9. Repositório Git, domínio de produção (`assistencia-system.fly.dev`), módulos `irflow_*.py` e `database.db` não foram alterados nesta etapa — fora de escopo até janela de manutenção planejada. `.TESTING_REPORT.md` (registro histórico) não foi tocado
- `docs/engineering/DOMAIN_MODEL.md` — mapa dos domínios de negócio existentes, extraído do código (schema `app.py` + `ARCHITECTURE.md` + `tests/` reais em `main`); cada domínio inclui testes existentes e dependências com outros domínios; registra que "Clientes" não é uma entidade própria hoje (campo texto solto em `os`)
- `docs/engineering/adr/ADR-005.md` — estratégia de multiempresa: alternativas técnicas avaliadas (banco por empresa / `empresa_id` / schema por empresa), decisão pendente do Product Owner
- `docs/engineering/ENGINEERING_GUIDE.md` seção 3.1 — convenção obrigatória de camadas (`controller → service → repository → tests → README`) para domínios de negócio novos, com regra de reuso entre domínios (ex.: `irflow_estoque_service.py` como candidato a serviço compartilhado) e regra inegociável de que um domínio nunca acessa o repository de outro diretamente (só o service do dono)
- `docs/company/PRODUCT_REQUIREMENTS.md` — formulário de requisitos de produto (persona, dores, diferenciais, quem decide a compra, escopo negativo, monetização, mercado-alvo) com perguntas-guia objetivas por seção, seções marcadas `TODO` até decisão do Product Owner
- `docs/company/VISION.md` — formulário de missão, visão, valores e critérios de sucesso do produto, seções marcadas `TODO`
- `docs/product/FEATURE_MATRIX_TEMPLATE.md` — seção 1 (funcionalidades atuais do sistema) completa e extraída do código; seção 2 (comparação com concorrentes) vazia, a preencher após pesquisa de mercado real
- `docs/engineering/ARCHITECTURE.md` e `docs/engineering/DATABASE.md` — documentação obrigatória ausente, extraída do estado real do código
- `tests/test_auth.py` — primeira suíte pytest do projeto (Sprint 2.2): login, logout, sessão e controle de acesso por perfil, isolada via `IR_FLOW_DATA_DIR`
- `irflow_validation.py` (Sprint 2.6): camada compartilhada de parsing de entrada — `parse_int`, `parse_float`, `safe_json`, `validate_positive_number` — usada pelos endpoints JSON de `irflow_blueprints_api.py`
- `tests/test_users.py` — cobertura de CRUD de usuários via `/api/usuarios` (Sprint 2.3): listar, criar, editar, excluir; duplicado, campos obrigatórios, perfil desconhecido, auto-desativação/auto-exclusão bloqueadas
- `tests/test_os_creation_query.py` — cobertura de criação e consulta de Ordens de Serviço via `/api/ordens` (Sprint 2.4): criação válida, campos obrigatórios, dependências (reparo, vendedor, peça), status/valores/data padrão, listagem com filtros, obter por id, histórico de cliente
- `tests/test_os_update_status.py` — cobertura de atualização (`PUT /api/ordens/<id>`) e transição de status (`PATCH /api/ordens/<id>/status`) de OS (Sprint 2.4): matriz completa de transições entre os 4 status válidos, troca de peças
- `tests/test_os_deletion_security.py` — cobertura de exclusão (`DELETE /api/ordens/<id>`) e resiliência de entrada em rotas de OS (Sprint 2.4): SQL injection, payload vazio, JSON malformado
- `tests/test_permissions.py` — matriz de acesso por perfil (admin/tecnico/vendedor) em rotas admin-only legadas e API, cobrindo 200/401/403/404 (Sprint 2.3)
- `tests/test_session.py` — cobertura de sessão: expiração (cookie forjado), cookie adulterado/não assinado, logout múltiplo, acesso após logout (Sprint 2.3)
- `tests/test_security.py` — cobertura de resiliência de entrada em `/api/auth/login`: SQL injection, campos obrigatórios, payload vazio, JSON malformado, Content-Type incorreto (Sprint 2.3)
- `tests/test_stock_creation_query.py` — cobertura de cadastro e consulta de itens de estoque via `/api/estoque` (Sprint 2.5): criação, campos obrigatórios, normalização de tipo/qualidade/modelo, filtros de listagem
- `tests/test_stock_movement.py` — cobertura de movimentação de estoque (Sprint 2.5): entrada/saída via ajuste, saldo final, consumo FIFO de lotes
- `tests/test_stock_os_integration.py` — cobertura de integração estoque × Ordem de Serviço (Sprint 2.5): consumo automático, múltiplas peças, mesma peça em mais de uma OS, devolução (cancelamento/exclusão), alteração/remoção/substituição de peças, compatibilidade por modelo
- `tests/test_stock_security.py` — cobertura de segurança e exclusão de estoque (Sprint 2.5): sem sessão, SQL injection, payload inválido, exclusão bloqueada quando peça em uso em OS aberta
- `tests/test_pricing.py` — cobertura de tabela de preços (restante da Sprint 2): testes unitários de `irflow_price_tables.py` (normalização de modelo/serviço, `sugerir_preco_tabela`, `encontrar_servico_tabela` com correspondência fuzzy) e testes de integração de `GET/POST /api/precos`, `GET /api/precos/sugerir`, `POST /api/precos/excluir`
- `tests/test_shopping.py` — cobertura completa de `/api/shopping-list` (restante da Sprint 2): CRUD, paginação/filtros, workflow de transição de status (matriz de transições válidas/inválidas, idempotência, estado terminal `CANCELADO`), bloqueio de compra simultânea, cancelamento (soft delete), agrupamento (`/grouped`) e auditoria (`/logs`, BR-016)
- `docs/product/features/CLIENTES.md` — spec do épico P0 Clientes: fluxo, modelo de dados (`clientes` + migração aditiva `os.cliente_id`), wireframes conceituais, casos de erro, critérios de aceite. Decisões de negócio pendentes (deduplicação, campos adicionais) marcadas `TODO`, sem validação do Product Owner ainda
- `docs/product/features/IMEI.md` — spec do épico P0 IMEI Individual: fluxo, modelo de dados (`estoque_unidades` + `estoque.requer_imei`), wireframes conceituais, casos de erro, critérios de aceite. Mesma ressalva de `CLIENTES.md` sobre decisões pendentes
- `irflow_rate_limit.py` (Sprint 3, Unidade 1): rate limiting de login via tabela SQLite `login_attempts` (KI-001) — 5 tentativas/minuto por identificador em `POST /api/auth/login` e `POST /login`. Contador em SQLite em vez de memória de processo porque o Gunicorn de produção roda com `--workers 2`; identificador resolvido via `Fly-Client-IP`/`X-Forwarded-For`/`remote_addr` (nenhum desses headers era lido antes). `tests/test_rate_limit_login.py` (7 casos) e fixture autouse `_limpar_login_attempts` em `tests/conftest.py`
- `irflow_core.py::sessao_ainda_ativa` (Sprint 3, Unidade 2): expiração de sessão por inatividade — janela deslizante de 30 min (`IR_FLOW_SESSION_INACTIVITY_MINUTES`), aplicada uma única vez em `verificar_autenticacao()` (`app.py`) e cobrindo tanto views legadas quanto `/api/*` (achado: as duas superfícies passavam pelo mesmo `before_request` global antes de qualquer bypass de endpoint). `tests/test_session_inactivity.py` (11 casos)
- `irflow_audit.py::registrar_log_auditoria` + tabela `audit_log` (Sprint 3, Unidade 3): auditoria central reutilizável (entidade/entidade_id/ação/antes/depois) para novos domínios, em vez de replicar o padrão `shopping_list_logs` por domínio a cada feature nova — esse padrão existente não foi tocado/migrado. Primeiros consumidores: Clientes e `estoque_unidades` (Sprint P0.1, ainda a implementar). `tests/test_audit_log.py` (5 casos, nível de service)
- `POST /api/usuarios/<id>/reset-token` e `POST /api/password-reset/<token>` (Sprint 3, Unidade 4): recuperação de senha via token de uso único gerado pelo admin — mecanismo escolhido no lugar de self-service por e-mail (menor escopo, sem infraestrutura de e-mail transacional nova). Token expira em 24h (`IR_FLOW_PASSWORD_RESET_TOKEN_HOURS`), gerar um novo invalida o anterior, mesmo padrão de `secrets.token_urlsafe` já usado em `gerar_token_checklist_os`. `tests/test_password_reset.py` (10 casos)
- Domínio Clientes completo (Sprint P0.1, Unidade 5): `irflow_clientes_controller.py`/`irflow_clientes_service.py`/`irflow_clientes_repository.py` — primeira aplicação real da convenção controller/service/repository de `ENGINEERING_GUIDE.md` §3.1. `GET/POST/PUT/DELETE /api/clientes*` (busca por nome/telefone/CPF, paginação, exclusão bloqueada com OS vinculada — BR-023/BR-024), tabela `clientes` + `os.cliente_id` (aditivo, sem backfill). Sem tela — fundação de backend para o futuro módulo de Vendas. `tests/test_clientes.py` (23 casos). Achado corrigido no processo: `verificar_autenticacao()` (`app.py`) só reconhecia o bypass de `/api/*` pelo nome do blueprint (`api.*`), então um segundo blueprint sob `/api/*` (como `clientes_api`) caía na checagem de sessão legada em vez de deixar o próprio blueprint responder 401 — trocado para checar por `request.path`, cobre qualquer blueprint futuro sob `/api/*` sem precisar atualizar essa lista a cada domínio novo
- Domínio `estoque_unidades` — rastreamento individual por IMEI (Sprint P0.1, Unidade 6): `irflow_estoque_unidades_controller.py`/`_service.py`/`_repository.py`, segunda aplicação da convenção de `ENGINEERING_GUIDE.md` §3.1. `GET/POST /api/estoque-unidades*` e `PATCH /api/estoque-unidades/<id>/status` (transições manuais `disponivel ↔ em_reparo`, `em_reparo/devolvido → disponivel` — BR-025/BR-026), tabela `estoque_unidades` + `estoque.requer_imei`. `reservado`/`vendido` existem no schema mas nenhum endpoint desta sprint os produz/aceita — reservados para o futuro módulo de Vendas. Fecha o gap de marca de rastreamento por IMEI (`BRAND_IDENTITY.md` seção 2). `tests/test_estoque_unidades.py` (20 casos)
- `irflow_vendas_service.py` (Sprint P0.1, Unidade 7): stub vazio (só docstring), placeholder explícito para o futuro domínio Vendas — sem rota, sem tabela, sem wiring em `app.py`, pedido explícito do usuário
- `.env.example` (Sprint 3, Unidade 8): pendente desde a Sprint 2 (T-10) — 26 variáveis documentadas com comentários e defaults seguros, incluindo as 2 novas desta sprint (`IR_FLOW_SESSION_INACTIVITY_MINUTES`, `IR_FLOW_PASSWORD_RESET_TOKEN_HOURS`) e 6 injetadas automaticamente pela plataforma de deploy (Fly.io/Render/Vercel), documentadas como referência
- `docs/engineering/ENGINEERING_GUIDE.md` §3.1 (Sprint P0.1, Unidade 9): adendo registrando a interpretação de "README de domínio = docstring no topo do `_service.py`" quando não há pasta própria — já aplicada em Clientes e `estoque_unidades`, formalizada como precedente para os próximos domínios (Financeiro, Vendas)
- Domínio Produtos — catálogo comercial de venda (Sprint Comercial 0.1, 2026-07-20): `irflow_produtos_controller.py`/`_service.py`/`_repository.py`, terceira aplicação da convenção controller/service/repository de `ENGINEERING_GUIDE.md` §3.1. `GET/POST/PUT/DELETE /api/produtos*` (categoria — iPhone/Apple Watch/AirPods/Acessório —, marca, modelo, cor, capacidade, condição — Novo/Seminovo/Vitrine —, preço de custo/venda, margem calculada, quantidade agregada), tabela `produtos`, domínio **novo e separado** de Estoque (peças de reparo) — decisão investigada e confirmada com o usuário antes de implementar. `categoria`/`condicao` rejeitadas com 400 quando fora da lista fechada, nunca normalizadas silenciosamente (BR-027). Margem nunca persistida (BR-028). Criar/editar/excluir restrito a `admin` (BR-029). Sem tela — fundação de backend para o Épico Vendas. `tests/test_produtos.py` (27 casos)
- `frontend/src/pages/Produtos.jsx` — tela do catálogo comercial (Sprint Comercial 1.1, 2026-07-21): primeira tela do Épico Vendas, consome integralmente `/api/produtos*` sem alterar backend/schema. Cards de resumo (Produtos/Seminovos/Vitrine), badges por categoria com emoji (🟦 iPhone, ⌚ Apple Watch, 🎧 AirPods, 🔌 Acessório), busca client-side combinando descrição/categoria/marca/modelo/cor/capacidade/SKU/condição em uma única caixa (o filtro `q` do backend só cobre descrição/modelo/SKU), coluna "Unidades" com placeholder `—` reservando espaço para o rastreamento por IMEI de uma sprint futura sem precisar mudar o layout depois, status derivado (Disponível/Esgotado/Inativo) a partir de `ativo`+`quantidade`. Escrita (criar/editar/excluir) restrita a `admin` no frontend, espelhando a permissão já existente no backend — leitura liberada para qualquer perfil autenticado (ex.: vendedor). Nova rota `/produtos` e item de menu em `Layout.jsx`. Validado manualmente end-to-end (login, listagem, busca, criar/editar/excluir, visão restrita do perfil vendedor) via app rodando localmente com banco isolado — sem suíte de teste de frontend automatizada (convenção do projeto ainda é só E2E Playwright para fluxos principais, não expandida nesta sprint)
- `frontend/src/pages/Clientes.jsx` — tela de Clientes (Sprint Comercial 1.2, 2026-07-21): segunda tela do Épico Vendas, consome integralmente `/api/clientes*` já existente (Sprint 3 Unidade 5), sem alterar backend/schema. Listagem, busca única (nome/telefone/e-mail/CPF-CNPJ, client-side — o `q` do backend só cobre nome/telefone/cpf_cnpj), cards de resumo, CRUD (criar/editar para qualquer perfil autenticado, excluir restrito a `admin`, espelhando `irflow_clientes_controller.py`). Painel de Perfil do Cliente ao clicar numa linha: dados cadastrais e observações, Histórico de OS via `GET /api/ordens/historico-cliente` (endpoint legado por nome — `os.cliente_id` existe no schema mas nenhum fluxo real o preenche hoje, achado durante a investigação), Garantias via `GET /api/garantias?q=` (parâmetro já suportado pelo backend, só não exposto antes no client `garantias.list`, agora aceita `params`), e Compras como placeholder vazio ("módulo de Vendas em construção") — nenhum endpoint novo criado. Nova rota `/clientes` e item de menu em `Layout.jsx`. Validado manualmente end-to-end (login, listagem, busca, criar/editar/excluir, perfil com histórico de OS e garantia reais a partir de dados semeados via API)

<!-- Sprint 2.4 (testes de OS) segue em branch própria aguardando revisão de
     merge — a entrada de "Adicionado" só entra aqui quando a branch for de
     fato mergeada em main. -->

### Corrigido
- Removido endpoint duplicado `GET/POST/PUT/DELETE /api/shopping-list` legado (baseado na tabela `compras`) em `irflow_blueprints_api.py` — colidia com a implementação atual (tabela `shopping_list`) e causava `AssertionError` do Flask na inicialização, impedindo a aplicação e a suíte de testes de rodar (KI-012)
- Nove rotas de `irflow_blueprints_api.py` (`shopping_list`, `reposicao_sugerida_estoque`, `criar_ordem`, `atualizar_ordem`, `criar_estoque`, `atualizar_estoque`, `criar_custo`, `atualizar_custo`, `salvar_preco`) retornavam 500 não tratado ao receber um valor não numérico em campos parseados com `int()`/`float()`; agora retornam 400 com mensagem de validação (KI-013)
- `PUT /api/estoque/<id>` calculava o diff de movimentação com a quantidade não limitada a zero — enviar quantidade negativa gerava um registro de saída maior que o saldo real no histórico de movimentações (Sprint 2.5, achado durante investigação de testes, hotfix)
- `GET /api/estoque` com qualquer filtro (modelo, tipo ou qualidade) sempre retornava lista vazia, por ordem errada de parâmetros SQL (Sprint 2.5, achado durante investigação de testes, hotfix)
- `PATCH /api/ordens/<id>/status` e `PUT /api/ordens/<id>` aceitavam `status` ausente ou desconhecido e o normalizavam silenciosamente para "Em andamento" em vez de rejeitar — em `PUT`, isso reabria uma OS Finalizada e zerava `data_finalizado` sem erro; ambas as rotas agora exigem `status` explícito e válido (KI-015, hotfix `2defd17`, achado ao retomar o Sprint 2 e revisar a branch `test/sprint-2-4-regras-negocio-os` para merge)
- `POST /api/shopping-list` calculava `quantidade` com `body.get("quantidade_solicitada") or body.get("quantidade")` — como `0` é falsy em Python, enviar `quantidade_solicitada: 0` caía no `or` e virava o default `1` do `parse_int`, antes mesmo de chegar na validação `quantidade <= 0`; o item era criado silenciosamente com quantidade `1` em vez de ser rejeitado (KI-016, hotfix `quantidade-zero-shopping-list`, achado durante a escrita de `test_shopping.py`, C-01+C-04 — ver `ENGINEERING_GUIDE.md` §11)
- `IPHONE_MODELS`/`IPHONE_COLORS` (`irflow_reference_data.py`) desatualizados até iPhone 16e — não permitiam abrir OS para iPhone 17/17 Air/17 Pro/17 Pro Max, únicos dispositivos usados nessa tela (fonte única, sem duplicação, confirmada antes da mudança). Adicionados os 4 modelos; cores usam lista genérica (`Preto`/`Branco`/`Azul`/`Verde`/`Rosa`) em vez de nomes específicos do catálogo oficial Apple — decisão deliberada em revisão para não arriscar nome de cor incorreto sem necessidade comercial ainda (campo não bloqueia a criação da OS; trocar pelos nomes oficiais quando houver essa demanda). Regex de extração de modelo por descrição livre (`extrair_modelo_da_descricao_aparelho`) ajustado para reconhecer o sufixo "air", nunca usado antes nesta lista — sem o ajuste, uma descrição livre como "iPhone 17 Air" seria extraída incorretamente como "iPhone 17" (Hotfix H-002, `fix/catalogo-iphone-17`, branch a partir de `main`). Comentário adicionado acima de `IPHONE_MODELS` documentando os 5 consumidores da lista (Nova OS, Editar OS, Estoque, Tabela de Preços, `API /api/constantes`), para reduzir o risco de desatualização silenciosa no futuro. Nenhuma mudança de schema/endpoint/regra de negócio. Validado com a suíte completa (407 testes, sem regressão) e manualmente: criação real de OS com modelo "iPhone 17 Pro Max" via API e via tela `NewOrder.jsx`
- `ruff check .` estava vermelho em `main` com 175 erros, bloqueando o job `Lint` do CI e, por `needs: lint`, os jobs `backend`/`frontend` para qualquer PR (KI-017). Resolvido em 6 commits atômicos na branch `chore/fix-ruff-lint-ki-017`: 11 scripts de debug/smoke pré-pytest movidos da raiz para `scripts/` (95 erros, zero mudança de conteúdo), auto-fixes seguros do ruff nos módulos de produção, 28 idiomas `try/except/pass` convertidos para `contextlib.suppress` (mesmo comportamento), remoção de bindings `deps[...]` não usados, e 17 correções pontuais (loop vars não usadas, `raise ... from`, simplificações de `if`/builtin). `ruff check .` → 0 erros. 407 testes, 100% passando, cobertura 48%. Esta branch só chegou a `origin/main` em 2026-07-21, junto do merge da Sprint Comercial 1.1 (Tela Produtos) — apesar de já registrada aqui como concluída em 2026-07-20, o merge efetivo em `origin/main` não havia acontecido até então
- Removido bloco morto duplicado de `criar_estoque()` em `irflow_blueprints_api.py` (linhas ~224–272, sem `@api.route`, nunca roteado, sobrescrito pela versão real mais abaixo) — resíduo do mesmo merge que originou KI-012 (KI-014, achado durante a correção de KI-017). Nenhum efeito em runtime
- `getOrderDisplayNumber` (`frontend/src/lib/constants.js`) sempre exibia o `id` interno da OS, mesmo para Ordens de Serviço importadas do MercadoPhone — deveriam mostrar `os.id_externo_integracao` (número real da integração), já existente no schema e já retornado por `GET /api/ordens`, só nunca usado pela função de exibição. Regressão de 2026-06-09 (commit `fda0929`, "fix shopping list mismatch") que removeu a preferência pelo número externo inteira ao corrigir um truncamento (`.slice(-5)`) que era o bug real da época. Restaurada a preferência pelo número externo quando `origem_integracao === "mercado_phone"`, sem reintroduzir o truncamento (KI-021, Hotfix H-003, pedido do usuário — CTO). Nenhuma mudança de schema/backend. Validado manualmente: OS nativa exibe id interno, OS de origem MercadoPhone exibe o número externo

### Modificado
- `irflow_blueprints_api.py` (Sprint 2.6): ~30 pontos de parsing/validação já protegidos (20x `request.get_json(silent=True) or {}`, checagens de valor positivo em estoque/custos, parsing de quantidade em shopping-list e config do MercadoPhone) substituídos pela camada compartilhada de `irflow_validation.py` — sem mudança de comportamento observável
- `pyproject.toml`/`.github/workflows/ci.yml` — cobertura tornada bloqueante no CI (`fail_under = 40`, removido `continue-on-error`), antecipando o cronograma original que só previa bloqueio a partir da Sprint 3 (20%) — cobertura real medida (43%) já passava da meta de 40% da Sprint 2, decisão explícita do usuário de não segurar o gate abaixo do que a suíte já garante
- `docs/product/features/VENDAS.md` — adicionadas as seções "Modelo de dados", "Wireframes conceituais" e "Dependências" (faltantes desde a criação em 2026-07-09); nenhuma decisão já tomada foi alterada
- `docs/product/PRODUCT_BACKLOG.md` — Clientes e IMEI Individual atualizados de "Não iniciado" para "Especificação", apontando para `CLIENTES.md`/`IMEI.md`
- Removidas referências operacionais ao Fly.io (`CLAUDE.md`, `README.md`, `DEPLOY.md`, `docs/engineering/ARCHITECTURE.md`, `ENGINEERING_GUIDE.md`, `SECURITY.md`, `docs/operations/PROJECT_STATUS.md`, `ROADMAP.md`, `docs/company/BRAND_IDENTITY.md`, `.env.example`, `.gitignore`) e removido `fly.toml` — produção já migrada para Render (backend) + Vercel (frontend) desde antes desta sprint; achado ao investigar erro real de webhook do Mercado Phone apontando para o domínio antigo do Fly. Comentários em `irflow_rate_limit.py` e `Dockerfile` atualizados (sem mudança de comportamento). Documentos históricos (`.TESTING_REPORT.md`, entradas antigas deste changelog, `KNOWN_ISSUES.md`, sprints já fechadas, ADRs aceitos) preservados sem alteração de propósito

### Adicionado (2026-07-21 — migração ADR-007)
- `docs/engineering/adr/ADR-007.md` — decisão de arquitetura (Aceita): consolidação de rastreamento por IMEI entre Estoque e Produtos. `estoque_unidades` evolui para `unidades_serializadas`, fonte única de verdade para qualquer unidade física da empresa, com origem em Estoque OU Produtos (nunca os dois — Regra de Ouro). Formaliza também o Princípio da Responsabilidade de Transição (cada domínio futuro só transiciona os estados que lhe pertencem)
- `docs/engineering/migrations/MIGRATION_unidades_serializadas.md` — plano técnico de execução da migração (objetivo, impacto arquitetural, estratégia SQLite de recriação de tabela, rollback, checklist de integridade, testes obrigatórios, critérios de aceite, checklist de deploy, riscos, fora de escopo), aprovado pelo usuário (CTO)
- `scripts/migrate_unidades_serializadas.py` — script idempotente de migração (recria a tabela dentro de uma única transação, valida contagem antes de remover a tabela antiga, corrige `sqlite_sequence`); testado contra bancos SQLite descartáveis, nunca executado contra `database.db` real nesta sessão
- `tests/test_migration_unidades_serializadas.py` — suíte dedicada à migração: preservação de dados linha a linha, remoção da tabela antiga, recriação de índices, `sqlite_sequence` sem colisão de PK, idempotência (rodar duas vezes é no-op seguro)

### Modificado (2026-07-21 — migração ADR-007)
- `estoque_unidades` → `unidades_serializadas`: schema em `app.py::criar_tabelas()` (novas colunas `produto_id`, `saude_bateria`, `localizacao`; `estoque_id` relaxado para nullable); `irflow_estoque_unidades_{repository,service,controller}.py` renomeados para `irflow_unidades_serializadas_{repository,service,controller}.py`; rota `/api/estoque-unidades` → `/api/unidades-serializadas`; `tests/test_estoque_unidades.py` → `tests/test_unidades_serializadas.py` (~27 casos, incluindo os novos cenários de origem por `produto_id`). Sem alias de compatibilidade — decisão deliberada do CTO (zero consumidores hoje). Migração implementada e testada apenas contra bancos de teste/locais nesta sessão — a migração do `database.db` de produção é um passo de deploy separado, ainda pendente, seguindo o checklist do plano técnico
- `docs/engineering/DATABASE.md`, `DOMAIN_MODEL.md`, `ENGINEERING_GUIDE.md`, `SECURITY.md` e `docs/product/BUSINESS_RULES.md` (BR-025/BR-026), `docs/product/features/IMEI.md`/`VENDAS.md` (nota pendente da Sprint Comercial 0.1 resolvida) e `docs/product/PRODUCT_BACKLOG.md` — atualizados para refletir o novo nome de tabela/arquivos/rota

### Adicionado (2026-07-22 — Sprint Comercial 1.3.1)
- `frontend/src/pages/UnidadesSerializadas.jsx` — tela de listagem de Unidades Serializadas (busca única por IMEI/modelo/produto, cards de resumo — Unidades/Disponíveis/Em Reparo —, badges de origem Estoque/Produto e de status). Consome `GET /api/unidades-serializadas`, enriquecido com `LEFT JOIN` em `estoque`/`produtos` só para exibição (label de origem, categoria/marca do produto quando aplicável) — nenhuma mudança de filtro ou regra de negócio. Implementada em sessão anterior (branch `feat/tela-unidades-serializadas`), revisada e mergeada nesta sessão: 449 testes (29 em `test_unidades_serializadas.py`) passando, `ruff check .` limpo, lint/build do frontend sem erros novos, validado manualmente rodando o app com unidades seedadas via API a partir de `estoque` e de `produtos` — busca cruzada e badges de origem confirmadas corretas para os dois casos

### Adicionado (2026-07-22 — Sprint Técnica: Centralização de Referências)
- `GET /api/constantes` agora expõe `produtos_categorias`/`produtos_condicoes` (`PRODUTOS_CATEGORIAS`/`PRODUTOS_CONDICOES`, `irflow_reference_data.py`) — existiam como fonte única no backend desde a Sprint Comercial 0.1, mas nunca tinham sido expostas via API; `frontend/src/pages/Produtos.jsx` mantinha uma cópia própria hardcoded (`CATEGORIA_OPTIONS`/`CONDICAO_OPTIONS`) que corria o risco de divergir da lista real toda vez que uma categoria/condição fosse adicionada só no backend. Frontend passou a consumir a API (com a lista antiga mantida só como fallback defensivo, mesmo padrão de `Stock.jsx` para tipo/qualidade de estoque). `tests/test_produtos.py` — novo teste confirmando que `/api/constantes` retorna as listas corretas. Investigação (pedido do usuário — CTO) confirmou que `IPHONE_MODELS`/`IPHONE_COLORS` já eram fonte única e já expostas (nenhuma mudança necessária ali); "fabricantes" não existe como lista fechada em lugar nenhum hoje (campo `marca` é texto livre) — criar uma seria feature nova, não consolidação, fora de escopo desta sprint técnica

### Adicionado (2026-07-22 — Sprint Comercial 1.3.2)
- `GET /api/unidades-serializadas/<id>/historico` — endpoint de leitura novo, expõe `audit_log` (entidade `unidade_serializada`) já gravado desde a Sprint P0.1 mas nunca lido de volta por nenhum endpoint. `GET /api/unidades-serializadas/<id>` passou a incluir os campos de origem (produto/estoque) que a listagem (C1.3.1) já usava. `frontend/src/pages/UnidadesSerializadas.jsx` — painel de detalhe ao clicar numa unidade (IMEI, origem, status, saúde da bateria, localização, histórico completo com autor e data/hora); Cliente atual/Garantia mostrados como placeholder explícito (dependem do módulo de Vendas, ainda não implementado). Zero mudança de schema. 5 novos testes (34 no domínio), `ruff check .` limpo, validado manualmente com produto/unidade/2 transições de status semeados via API

### Adicionado (2026-07-22 — Sprint Comercial 1.3.3)
- Filtros avançados de Unidades Serializadas, todos resolvidos no backend (`irflow_unidades_serializadas_repository.py`/`_service.py`/`_controller.py`): busca combinada (`q`, IMEI/serial/modelo/descrição/marca/localização via `LEFT JOIN`, parâmetro legado `imei` mantido por compatibilidade), filtro por origem (`origem=estoque|produto`), por status (todos os alcançáveis hoje — Disponível/Em Reparo/Devolvido/Reservado/Vendido), por faixa de saúde da bateria (`saude_bateria_faixa`, 5 faixas incluindo "não informado", via `CAST`), por localização, e ordenação (`sort`: recente/antigo/imei/modelo/status, whitelist SQL). `frontend/src/pages/UnidadesSerializadas.jsx` reescrita: busca com debounce, 5 controles de filtro, paginação real server-side (20/página, substituindo o `per_page: 500` + filtro em memória de C1.3.1). Antes de implementar, três pontos do pedido original foram reportados ao usuário (CTO) por não terem suporte real: filtro por Cliente removido desta sprint (nenhuma unidade tem relação com cliente até o Épico Vendas existir); status "Em Garantia"/"Inativo" não incluídos (não existem em lugar nenhum — seria regra de negócio nova, não filtro); filtros de saúde da bateria/localização construídos mesmo sem dado real hoje (mesmo padrão do KI-020 — campo existe, ninguém grava ainda), decisão deliberada para não gerar retrabalho quando C1.3.4 vier a escrever esses campos. 12 novos testes (46 no domínio, 467 no total), `ruff check .` limpo, validado manualmente com dados de origem mista (produto/estoque) semeados via API

### Adicionado (2026-07-22 — Sprint Comercial 1.3.4)
- `PATCH /api/unidades-serializadas/<id>` — edita `localizacao`/`saude_bateria` (únicos campos de manutenção sem endpoint de escrita até então). Saúde da bateria validada como percentual 0-100, rejeitada com erro explícito se inválida (nunca coagida silenciosamente). Campos derivados/imutáveis (origem, IMEI, status, campos de Vendas) explicitamente bloqueados e rejeitados com 400 se enviados — status continua usando `PATCH /<id>/status` já existente. `frontend/src/pages/UnidadesSerializadas.jsx`: `DetalheUnidade` evoluído para um único componente de visualização+edição (não dois modais separados) — decisão explícita do usuário para não duplicar estrutura entre detalhe e edição. IMEI/Origem sempre somente-leitura; Status vira `<Select>` limitado às transições válidas a partir do status atual; Localização/Saúde da bateria viram inputs. Antes de implementar: confirmado que "Observações" não existe no schema (nunca foi criada) — fora de escopo por decisão já dada pelo próprio usuário ("não alterar schema"); IMEI consultado explicitamente com o usuário e decidido como imutável após o cadastro (identificador primário usado em busca/auditoria/futura garantia). 9 novos testes (55 no domínio, 476 no total), `ruff check .` limpo, validado manualmente editando bateria/localização/status de uma unidade real, com histórico refletindo os 2 eventos gravados

### Adicionado (2026-07-22 — Auditoria de branches)
- `docs/company/CUSTOMER_FEEDBACK.md` — log de feedback de cliente (72 linhas), mergeado da branch `docs/customer-feedback-log` após auditoria das branches do repositório (19+ branches locais/remotas revisadas uma a uma contra `origin/main` real, não por suposição de nome)

### Corrigido (2026-07-22 — Auditoria de branches)
- `app.py`: `PUBLIC_BASE_URL` agora normaliza o protocolo (adiciona `https://` quando ausente) e usa `VERCEL_URL` como fallback quando `IR_FLOW_PUBLIC_BASE_URL` não está definida. Fix já existia há mais de um mês na branch `ajuste-render-webhook`, nunca mergeada — trazido via cherry-pick após revisão de uso (só consumido em um outro ponto do arquivo, sem outros pontos do código dependendo do formato antigo). Sem mudança de comportamento quando `IR_FLOW_PUBLIC_BASE_URL` já está definida corretamente; 476 testes passando

### Adicionado (2026-07-22 — Preparação do Épico Vendas)
- `docs/product/features/VENDAS_GAP_ANALYSIS.md` — análise de consistência entre `VENDAS.md` (rascunho de 09/jul) e o estado real do código, a pedido do usuário (CTO), antes de abrir o `discuss-phase` do Épico Vendas. Não altera `VENDAS.md` nem ADR-007 (ambos continuam fonte de verdade). Conclusão: fluxo de negócio, casos de erro, critérios de aceite e modelo de dados continuam 100% válidos (o próprio `VENDAS.md` já havia se autocorrigido para o ADR-007 em 20/21-jul). Dois gaps técnicos identificados para entrar no discuss-phase: (1) `VENDAS.md` não cita `irflow_audit.py` como dependência, apesar de `unidades_serializadas` já reutilizar esse padrão de auditoria; (2) `TRANSICOES_VALIDAS` em `irflow_unidades_serializadas_service.py` ainda não implementa `disponivel→reservado`/`reservado→vendido` — as colunas `venda_id`/`reservado_por`/`reservado_ate` já existem no schema (ADR-007), só falta o wiring. Nenhuma decisão de Product Owner pendente foi respondida (mesmas 5 de 09/jul, mais a definição do cliente piloto levantada nesta conversa)

### Adicionado (2026-07-22 — Discovery de Vendas)
- `docs/product/research/` — nova subárvore de pesquisa de produto, separada de `product/features/` (especificação aprovada) por decisão explícita do usuário (CTO): nada em `research/` vira requisito sem passar pela pasta de features
- `docs/product/research/BENCHMARKS/MERCADO_PHONE.md` — esqueleto de benchmark de concorrente por módulo, com critérios acordados (fato antes de interpretação, observação separada de recomendação, decisão pendente do PO nunca assumida, contexto/data/versão registrados). Seção Vendas deliberadamente vazia — só houve visão geral de menus até esta data, não um walkthrough de fluxo
- `docs/product/research/VENDAS_QUESTIONS.md` — ~20 perguntas em aberto para o discuss-phase do Épico Vendas, cruzadas uma a uma contra `VENDAS.md`: várias já têm resposta de política (ex. "gera comissão sobre margem? sim", "existe aprovação de desconto? sim"), faltando só o valor exato (decisão do PO); outras são genuinamente novas (upgrade, acessórios, seguro, cancelamento, devolução, quando exatamente o estoque é baixado)
- `docs/product/research/VENDAS_DORES_REAIS.md` — template vazio para dores reais da operação, propositalmente sem dados fabricados — aguarda coleta de campo real
- `docs/product/FEATURE_MATRIX_TEMPLATE.md` — linha "Vendas" da comparação com concorrentes atualizada para apontar à nova pasta de benchmark; nota "Concorrentes a Pesquisar" registra que a lista original (Mercado Phone, Nextsi, SisAssist) e a lista mencionada em conversa posterior (CellStore, Mobix, Tiny, Bling) ainda não foram reconciliadas pelo PO

### Adicionado (2026-07-22 — Discovery de Vendas, refinamento estrutural)
- `docs/product/research/README.md` — índice e critérios da pasta de pesquisa, a pedido do usuário (CTO), para não deixar os documentos "soltos"
- `docs/product/research/VENDAS_QUESTIONS.md` — coluna "Prioridade" adicionada (🔴 Obrigatória/🟠 Importante/🟡 Depois/🔵 Futuro), derivada do checklist de MVP discutido em conversa; marcada explicitamente como proposta, não decisão fechada
- `docs/product/research/DISCOVERY_DECISIONS.md` — template vazio para registrar decisão + motivo + alternativas descartadas durante o discuss-phase, antes da formalização em `VENDAS.md`/ADR
- **Decisão deliberada de não criar ainda:** pastas `INTERVIEWS/` e subpastas por concorrente além de Mercado Phone — mesma regra de não criar estrutura vazia sem conteúdo real, já aplicada a `VENDAS_DORES_REAIS.md`

### Adicionado (2026-07-23)
- `docs/product/PRODUCT_GLOSSARY.md` — glossário de termos do produto (Produto, Estoque, Unidade Serializada, IMEI, Origem, Cliente, Venda, Reserva, Garantia — nos dois sentidos distintos, de reparo e de venda —, Comissão), extraído do código/docs reais, não aspiracional. Pedido do usuário (CTO) após confusão recorrente de terminologia na semana (Produto vs. Estoque, Aparelho usado de forma ambígua). Marca explicitamente "Aparelho" como termo a evitar em spec/código por ambiguidade, e lista Venda/Reserva/Garantia de venda/Comissão como "especificado, não implementado" — nenhum deles existe no sistema hoje. `docs/README.md` atualizado com a entrada no índice de `product/`

### Adicionado (2026-07-23 — Sprint Técnica: Centralização de Referências de OS)
- `OS_TIPOS_OPCOES`/`GARANTIA_REPARO_DIAS_PADRAO` (`irflow_core.py`) — antes eram literais soltos duplicados: tipos de OS apareciam inline em 2 lugares do backend e em 3 cópias no frontend (`lib/constants.js`, fallback em `NewOrder.jsx`, fallback em `EditOrder.jsx`), com `OrderFilters.jsx` nunca buscando da API; prazo de garantia (90 dias) estava hardcoded 2x no mesmo arquivo backend, e `GARANTIA_DIAS` no frontend era código morto (nunca importado). `frontend/src/pages/Orders.jsx` passa a buscar `/api/constantes`; `OrderFilters.jsx` consome `status_opcoes`/`os_tipos` da API com fallback. Achado registrado, não corrigido: perfis (`admin`/`tecnico`/`vendedor`) espalhados como string literal em 11 arquivos backend sem lista central — categoria diferente (autorização, não referência de UI), fora de escopo por risco desproporcional a um chore. 2 novos testes (478 no total), `ruff check .` limpo, validado manualmente com os dropdowns de Status/Tipo em `/ordens` populados pela API real

### Adicionado (2026-07-23 — INC-001)
- `docs/operations/INCIDENTS/INC-001-database-is-locked.md` — investigação do incidente P0 `database is locked` reportado pelo usuário (CTO) ao criar/editar OS e cadastrar/alterar estoque. Por pedido explícito, só investigação nesta sessão, nenhuma correção. Descartado como causa: WAL desabilitado, timeout pequeno, e as 4 rotas citadas como sintoma (que já têm `try/except/finally` corretos). Causa raiz mais provável: 14 pontos de código ativo escrevem no banco sem proteção contra exceção — uma conexão vazada com transação de escrita aberta bloqueia todo escritor seguinte em WAL até o processo coletar o objeto via GC. Maior risco identificado: `POST /api/auth/login` (maior frequência de chamada do sistema, já é escrita, sem proteção). Também confirmadas ativas e sem proteção: 4 rotas de `/api/shopping-list*` e `POST /api/checklist/<token>` (rota pública). Marcado como prioridade máxima do projeto, à frente de KIs e do Épico Vendas — decisão do usuário

### Corrigido (2026-07-23 — hotfix/conexao-login-database-locked)
- `POST /api/auth/login` (`irflow_blueprints_api.py::auth_login`) — conexão agora protegida com
  `try/except/finally`: qualquer exceção entre `conectar()` e o fim da função faz `rollback()` e
  `close()` antes de retornar erro, em vez de vazar a conexão com a transação de escrita aberta (causa
  raiz de maior risco identificada em `docs/operations/INCIDENTS/INC-001-database-is-locked.md`).
  Correção isolada e mínima, por decisão explícita do usuário (CTO) — os outros 13 pontos de risco
  identificados na mesma investigação seguem em aberto, não fazem parte deste hotfix. 2 novos testes
  (`tests/test_inc001_login_connection_leak.py`) provam o mecanismo exato via injeção de falha real no
  ponto da causa raiz, confirmados falhando contra o código anterior e passando contra a correção. 480
  testes no total, `ruff check .` limpo, zero regressão

### Adicionado (2026-07-23 — INC-001, correções de registro e reprodução por carga)
- `docs/operations/INCIDENTS/INC-001-database-is-locked.md` corrigido: causa raiz reformulada de "confirmada" para "hipótese principal, ainda não comprovada em runtime" (revisão do usuário/CTO); hipótese de conexão aninhada em OS/Estoque investigada e descartada por leitura de código; releitura completa das 13 rotas "sem proteção" reclassifica as 4 de `/api/shopping-list*` como risco estrutural (fecham em todo caminho via `except` amplo, não vazamento confirmado) — as 4 rotas de checklist (incluindo a pública) seguem como risco confirmado
- Instrumentação temporária de conexões implementada em `app.py::conectar()` (branch `chore/inc-001-instrumentacao-conexoes`, não mergeada), gated por `IR_FLOW_DEBUG_CONN_TRACE=1`, zero impacto desligada (480 testes + `ruff check .` sem mudança). Validada detectando corretamente uma conexão vazada em teste isolado. Duas rodadas de reprodução por carga concorrente local (`gunicorn --workers 2`, igual produção — 40 threads/45s e 120 threads/60s, ~16 mil escritas) não reproduziram o erro nem o aviso de vazamento — resultado negativo, causa raiz segue não confirmada

### Adicionado (2026-07-23 — INC-002)
- `docs/operations/INCIDENTS/INC-002-os-duplicada-mercado-phone.md` — investigação do incidente P0 de possível duplicação de Ordens de Serviço importadas do Mercado Phone (OS "1072" reportada pelo usuário/CTO). Causa estrutural encontrada por leitura de código, alta confiança: schema sem `UNIQUE` em `(origem_integracao, id_externo_integracao)`; importador confia só num `SELECT`-antes-de-`INSERT`; thread de sincronização inicia uma vez por processo do Gunicorn (`--workers 2` em produção, sem `--preload`) sem nenhuma coordenação entre processos — corrida clássica (TOCTOU) que pode duplicar a OS. Mesma classe de bug já corrigida em KI-001 (rate limiting) para outro recurso, nunca aplicada a este fluxo. Também identificado como candidato a causa de INC-001 (transação longa e concorrente por processo). Confirmação em produção e resposta do usuário sobre onde a duplicidade aparece (listagem vs. dashboard) pendentes — nenhuma correção de código feita, investigação apenas

### Corrigido (2026-07-23 — hotfix/mercado-phone-sync-lock-cross-processo, INC-002)
- `irflow_mercadophone.py` — lock cross-processo (`adquirir_lock_sync_mercado_phone`/`liberar_lock_sync_mercado_phone`, lease de 300s via `integracao_sync_estado`, tabela já existente, sem mudança de schema) impedindo que os 2 workers do Gunicorn rodem a sincronização do Mercado Phone ao mesmo tempo — causa estrutural de possível duplicação de OS (`docs/operations/INCIDENTS/INC-002-os-duplicada-mercado-phone.md`). `sincronizar_mercado_phone()` retorna `lock_ocupado=True` sem tocar em API/banco quando outro worker já está sincronizando. Ajustado `reprocessar_todas_os_mercado_phone()` para tratar lock ocupado como motivo de retry, não como "nada para importar" (evita reimportação completa terminar vazia após apagar tudo). 5 novos testes (485 no total, incluindo corrida real entre 2 threads), `ruff check .` limpo, zero regressão. `UNIQUE INDEX` deliberadamente não adicionado ainda — depende de confirmar/resolver duplicatas pré-existentes em produção primeiro

### Modificado (2026-07-24 — hotfix/mercado-phone-sync-lock-ajustes-revisao, INC-002)
- `irflow_mercadophone.py` — ajustes de revisão (usuário/CTO) ao lock cross-processo: TTL reduzido de 300s para 90s (`LOCK_SYNC_TTL_SEGUNDOS_PADRAO`, 3x o intervalo padrão de sync, evita espera excessiva pós-crash); log `[MercadoPhone] Sincronização ignorada: lock ocupado por outro worker.` adicionado quando o lock está ocupado, para diagnóstico. Teste de corrida escalado de 2 para 100 threads simultâneas; novo teste de estresse com 300 aquisições reais e contador de seção crítica clássico, confirmando atomicidade do `UPDATE ... WHERE` que sustenta o lock. 486 testes no total, suíte rodada 3x seguidas, `ruff check .` limpo, zero regressão

### Corrigido (2026-07-24 — fix/os-unique-index-mercado-phone-inc002, INC-002 resolvido)
- `app.py::criar_tabelas()` — `CREATE UNIQUE INDEX IF NOT EXISTS idx_os_origem_id_externo ON os (origem_integracao, id_externo_integracao)`, aplicado automaticamente no próximo deploy (mesmo padrão de todas as migrações aditivas do projeto). Proteção definitiva contra duplicação de OS por integração, independente do lock cross-processo (`docs/operations/INCIDENTS/INC-002-os-duplicada-mercado-phone.md`) — OS nativas (sem integração, campos `NULL`) não são afetadas, SQLite trata cada `NULL` como distinto num índice `UNIQUE`. 3 novos testes (489 no total), `ruff check .` limpo, zero regressão
- Confirmado em produção pelo usuário (CTO): 3 pares de OS duplicadas (`id_externo_integracao` 1083, 1093, 832). Analisados registros filhos de cada par (`os_pecas`, `os_reparos`, `os_checklists`) antes de decidir — 2 pares eram duplicatas idênticas sem filhos (limpeza segura), 1 par (832) tinha as duas linhas editadas de forma divergente após a duplicação (peça consumida duas vezes do estoque, reparo extra, checklist próprio em cada uma), exigindo decisão humana sobre qual linha refletia a realidade. Duplicatas removidas em produção (3 linhas + filhos órfãos), verificado `[]` na consulta de contagem pós-limpeza. INC-002 encerrado

### Adicionado (2026-07-25 — Release Readiness)
- `docs/company/RELEASE_1.0_MASTER_CHECKLIST.md` — checklist de certificação para o primeiro cliente pagante (Produto, Confiabilidade, Segurança/Compliance, Observabilidade, Operação). Cada item verificado contra o estado real do código/docs antes de publicar, não copiado do exemplo dado — vários gaps confirmados por busca direta: sem Financeiro (nenhuma tela/rota), sem teste automatizado de restore de backup, sem logging estruturado, sem Sentry/monitorização, sem doc de deploy/rollback, sem manual do usuário, sem LGPD. Inclui a tabela dos "3 níveis de planejamento" (Visão/Releases/Sprints) sugerida pelo usuário (CTO) para separar `RELEASE_STRATEGY.md`, `PRODUCT_BACKLOG.md` e `ROADMAP.md` por propósito
- `docs/product/PRODUCT_BACKLOG.md` — nova coluna "Item do Release 1.0" ligando cada épico ao item do master checklist que ele avança

### Adicionado (2026-07-25 — visão executiva e plano de go-live)
- `docs/company/RELEASE_1.0_MASTER_CHECKLIST.md` — adicionada visão executiva (% por área, barra de progresso geral ~25%), derivada das próprias seções do checklist (sem categorização nova), com metodologia explícita (média simples ❌≈0-15%/🟡≈30-70%/✅=100%, não pesada por esforço). Adicionado guardrail explícito contra o documento virar um segundo backlog
- `docs/company/GO_LIVE_PLAN.md` — plano de execução para colocar o primeiro cliente em produção, deliberadamente separado do master checklist ("como fazemos" vs. "estamos prontos"). Documenta que o sistema não tem multiempresa/`empresa_id` hoje — onboarding de cliente novo significa provisionar deployment próprio, não criar registro dentro do sistema atual. Rascunho nunca executado — marcado com os gaps conhecidos (critério de rollback não definido, nenhum dry-run feito)

### Adicionado (2026-07-25 — SECURITY_AUDIT_2026-07)
- `docs/security/SECURITY_AUDIT_2026-07.md` — triagem completa do scan Aikido rodado pelo usuário (CTO). Cada alerta validado no código antes de classificar (regra explícita: SAST gera falsos positivos, não corrigir às cegas). Resultado: SQL Injection, File Inclusion (`irflow_storage`) e SSRF confirmados como **falsos positivos** (evidência documentada por item); segredo `FLASK_SECRET_KEY` no histórico do Git **confirmado**, com achado adicional fora do relatório original — fallback hardcoded inseguro em `app.py:229`, mais grave que o vazamento histórico pois está visível no código atual; Gunicorn (`21.2.0`, preso em `<22`, CVE-2024-1135), CSP/X-Frame-Options ausentes, Docker rodando como root, e `actions/checkout` sem `persist-credentials: false` confirmados como P1. DOMPurify avaliado como não aplicável (projeto não usa `CUSTOM_ELEMENT_HANDLING`). Fecha a ação pendente desde 2026-07-06 em `docs/engineering/SECURITY.md` seção 3
- `docs/engineering/SECURITY.md` atualizado nas seções 3 (SQL Injection, agora ✅), 6 (headers HTTP), 8 (segredos — `FLASK_SECRET_KEY` escalado de ⚠️ para ❌) e 11 (dependências) para refletir os achados
- `docs/company/RELEASE_1.0_MASTER_CHECKLIST.md` — item "Segurança revisada" atualizado com o resultado da auditoria
- Nenhuma correção de código aplicada nesta sessão — investigação e classificação apenas, aguardando decisão do usuário sobre abrir a Sprint Segurança 1.0

### Adicionado (2026-07-25 — Sprint Segurança 1.0: perfil `estoque` e permissões de OS/Estoque)
- `irflow_core.py::PERFIS_OPCOES` — fonte única dos perfis válidos (`admin`/`tecnico`/`vendedor`/`estoque`, novo), substituindo tuplas duplicadas em `irflow_blueprints_api.py` (2 ocorrências) e `irflow_blueprints_auth.py` (2 ocorrências)
- Rotas de mutação de OS (`POST/PUT/DELETE /api/ordens`, `PATCH /api/ordens/<id>/status`) agora exigem perfil `admin` ou `tecnico`; rotas de mutação de Estoque (`POST/PUT/DELETE /api/estoque`) exigem `admin` ou `estoque` — antes qualquer perfil autenticado tinha acesso (achado já documentado em `DATA_DICTIONARY.md` desde 2026-07-10, corrigido agora via `docs/security/SECURITY_AUDIT_2026-07.md` item 14, decisão do usuário/CTO)
- `frontend/src/pages/Users.jsx` — novo perfil `estoque` na tela de gestão de usuários (dropdown + cor de exibição), validado visualmente via Playwright
- `docs/product/BUSINESS_RULES.md` BR-030 (nova regra); BR-003 corrigida (`ROUTE_PERMISSIONS` não cobre `/api/*`, achado anterior estava impreciso)
- `docs/engineering/DATA_DICTIONARY.md`, `DATABASE.md`, `docs/company/PRODUCT_REQUIREMENTS.md`, `docs/company/DECISION_LOG.md` atualizados
- Testes que caracterizavam o comportamento antigo (`test_tecnico_pode_excluir_item_de_estoque`, `test_vendedor_pode_excluir_item_de_estoque`, `test_vendedor_pode_excluir_qualquer_os`) reescritos para confirmar 403; novos testes cobrindo o acesso correto de `admin`/`estoque`. 494 testes no total, `ruff check .` limpo, zero regressão

### Corrigido (2026-07-25 — Sprint Segurança 1.0: itens P1)
- `app.py` — headers de segurança (`Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`) aplicados a todas as respostas via `@app.after_request`; nenhuma existia antes (`SECURITY_AUDIT_2026-07.md` itens 10, 11). 5 novos testes em `tests/test_security_headers.py`
- `Dockerfile` + novo `docker-entrypoint.sh` — container não roda mais como root; usuário de sistema `appuser` + entrypoint que ajusta a posse do disco `/data` do Render em runtime antes de trocar de privilégio via `gosu` (item 12). Não validado com `docker build`/`docker run` neste ambiente (sem Docker disponível) — validação local pendente antes do merge em `main`, por decisão explícita do usuário
- `.github/workflows/ci.yml` — `persist-credentials: false` adicionado aos 5 usos de `actions/checkout@v4` (item 13)
- `requirements.txt` — `gunicorn` `>=21,<22` → `>=22,<23` (`21.2.0` → `22.0.0`, corrige CVE-2024-1135); testado via suíte completa e smoke test manual do boot (item 6)
- `frontend/package-lock.json` — `npm audit fix` (sem `--force`) atualiza `immer`, DOMPurify, `js-yaml`, `postcss`, `vite` dentro dos ranges já aceitos por `package.json` (itens 8, 9)
- `react-router-dom` mantido em `7.18.1` — decisão explícita de não fazer downgrade para `7.11.0` (única correção oferecida pelo `npm audit fix --force`): a CVE remanescente é de modo servidor/RSC, não aplicável a este projeto (`BrowserRouter` client-side); ver `SECURITY_AUDIT_2026-07.md` item 7
- `docs/security/SECURITY_AUDIT_2026-07.md`, `docs/engineering/SECURITY.md` atualizados refletindo os itens corrigidos; novo achado `brace-expansion`/ReDoS (devDependency de lint) registrado como risco aceite (item 16)
- Pendente: rotação de `FLASK_SECRET_KEY` em produção (item 2 — ação manual do usuário no Render, fora do alcance deste agente)

### Corrigido (2026-07-25 — Sprint Segurança 1.0: fechamento e 2º scan Aikido)
- `FLASK_SECRET_KEY` rotacionada em produção no Render pelo usuário/CTO — item 2 fechado
- Docker non-root validado com `docker build`/`docker run` reais (instalado `colima` + `docker` CLI para isso, sem `docker` disponível neste ambiente antes): usuário real do processo do gunicorn confirmado `appuser` (uid 999) via `/proc/*/status`, nunca root; posse de `/data`/`/app` corretas; testado dentro do container: login, criar/editar OS, criar item de estoque, criar backup, restaurar backup, headers de segurança presentes, frontend (`/app`) responde 200, zero erros nos logs. Branch `security/sprint-1.0-p1-headers-docker-ci` mesclada em `main` (`ebe710b`)
- 2º scan Aikido rodado pelo usuário pós-sprint: confirmou o essencial resolvido. Achados novos triados com a mesma disciplina do 1º scan (`docs/security/SECURITY_AUDIT_2026-07.md`, seção "Segundo scan Aikido"):
  - `irflow_os.py::carregar_os_com_relacoes` — parâmetro `order_by` interpolado via f-string sem validação dentro da função; não explorável hoje (os 2 únicos chamadores sempre passam o mesmo literal fixo), mas corrigido preventivamente com whitelist (`_ORDENACOES_OS`, mesmo padrão de `irflow_unidades_serializadas_repository.py`). 3 novos testes em `tests/test_os_order_by_whitelist.py`
  - `gunicorn` `22.0.0` → `26.0.0` — 2ª CVE distinta da 1ª (CVE-2024-6827, contrabando de requisição TE.CL, corrigida na 23.0.0+); confirmado sem breaking change relevante (projeto não usa o worker `eventlet` removido na 26.0.0)
  - Docker root — o scan ainda mostrava esse item; já corrigido e validado com `docker build`/`docker run` reais antes desse 2º scan, provável cache/lag do scanner (evidência no audit doc)
  - `immer`, `enhanced-resolve` — `npm audit` local não reproduz vulnerabilidade nas versões instaladas; classificado como "não reproduzido neste momento", não como falso positivo definitivo — reavaliar se surgir CVE nova ou se a base do Aikido divergir de novo
- 502 testes no total, `ruff check .` limpo, zero regressão

### Adicionado (2026-07-25 — Sprint Observabilidade)
- `irflow_logging.py` — logging estruturado em JSON (`JSONFormatter`, `configurar_logging()`, `get_logger()`), sem dependência nova (stdlib `logging`). Cada linha carrega `request_id` quando emitida dentro de uma request Flask
- `app.py` — correlation ID por request (`X-Request-Id`, gerado ou ecoado do cliente se vier num formato válido) e log de acesso JSON (`method`/rota via `url_rule.rule`/status/duração/usuário) em todo request
- `/health` (liveness, sempre 200) e `/ready` (readiness, checa o banco via `SELECT 1`, 503 se falhar) — sem autenticação, bypass explícito no `before_request` de auth
- `/metrics` (Prometheus): `http_requests_total` e `http_request_duration_seconds`, labels `method`/`route`/`status` (rota via `url_rule.rule`, nunca `request.path`, evita cardinalidade sem limite). Protegido por `METRICS_TOKEN` quando `IS_SERVER_RUNTIME`, nega por padrão se a variável não estiver configurada
- Modo multiprocess do `prometheus_client` (Gunicorn roda `--workers 2` — registry padrão daria números por processo, mesma classe de bug de INC-001/INC-002/rate limiting): novo `gunicorn.conf.py` com hooks `on_starting`/`child_exit`; `Dockerfile` define `PROMETHEUS_MULTIPROC_DIR` via `ENV`, herdada pelos workers. Validado com `docker build`/`docker run` reais (via `colima`): 20 requests distribuídos entre os 2 workers agregados corretamente em `/metrics`
- Sentry (`sentry-sdk[flask]`) inicializado só quando `SENTRY_DSN` está definida (vazia por padrão — usuário ainda não tem conta). `send_default_pii=False` explícito (dado real de cliente não pode vazar em breadcrumb), `traces_sample_rate=0` (só captura de erro, sem tracing)
- Migração dos `print()` que já carregavam sinal operacional real para `logger.*` estruturado: `app.py` (admin padrão, token de webhook Mercado Phone), `irflow_storage.py` (thread de backup, relacionado a KI-006), `irflow_mercadophone.py` (sincronização) — 22 ocorrências no total, não os outros ~220 (a maioria em `scripts/` avulsos fora do processo do servidor)
- Achado durante a validação real com Docker: Gunicorn ≥25 liga por padrão um socket de controle que falhava com "Permission denied" no container non-root (`$HOME` do `appuser` não é gravável por ele) — desabilitado via `control_socket_disable=True`, não usamos essa feature
- 30 novos testes (`test_logging_json.py`, `test_health_ready.py`, `test_request_id.py`, `test_metrics.py`, `test_sentry_init.py`). 526 testes no total, `ruff check .` limpo, zero regressão
- `docs/operations/SPRINTS/SPRINT_OBSERVABILIDADE.md` — plano e retrospectiva completos

### Segurança (2026-07-26 — Auditoria AppSec, Fase 1: integração MercadoPhone)
- `POST /api/integracoes/mercadophone/{sincronizar,reprocessar,reimportar}` (KI-022) exigiam só sessão ativa, qualquer perfil — `/reimportar` apaga e reimporta em massa todas as OS de origem MercadoPhone, mesmo efeito de um `DELETE /api/ordens` em massa, mas por um caminho que ficou fora da restrição a `admin`/`tecnico` já aplicada a `/api/ordens*` na Sprint Segurança 1.0. Corrigido com a mesma checagem de perfil já usada em `criar_ordem`/`atualizar_ordem`/`deletar_ordem`. Módulo não tinha nenhum teste de autorização antes — 4 novos testes (`tests/test_mercadophone_permissions.py`). 529 testes, `ruff check .` limpo

### Segurança (2026-07-26 — Auditoria AppSec, Fase 1: Auth/Middleware)
- `app.py`: `autenticar_integracao_mercado_phone()` tinha um early-return quando `MERCADO_PHONE_WEBHOOK_TOKEN` estava vazio, deixando `POST /api/integracoes/mercadophone/os` aberto sem autenticação nesse caso (fail-open) — `.env.example`/`DEPLOY.md` chegavam a documentar isso como aceitável em dev. Corrigido para negar por padrão (fail secure) quando o token não está configurado; comparação do token trocada de `in`/`==` para `hmac.compare_digest` (constant-time). Produção já tinha a variável configurada com valor forte (confirmado com o CTO) — não foi um incidente ativo. 3 novos testes (`tests/test_mercadophone_webhook_auth.py`)
- `app.py`: `verificar_autenticacao()` usava `ROUTE_PERMISSIONS.get(endpoint)`, que não distinguia "endpoint cadastrado com `None`" (qualquer perfil logado) de "endpoint ausente do dict" — um endpoint legado novo sem entrada correspondente ficava liberado por padrão em vez de negado. Corrigido com um sentinel que nega por padrão endpoints ausentes. Confirmadas 6 entradas mortas já existentes no dict (`sync_os_mercado_phone`, `status_sync_mercado_phone`, `order_views.autocomplete_clientes`/`api_buscar_pecas`/`api_remover_peca`/`api_adicionar_peca`) apontando para funções que não existem mais — evidência de que o dict já divergia do código real; nenhum endpoint ativo hoje foi afetado (verificado um a um). 3 novos testes (`tests/test_route_permissions_fail_secure.py`)
- 6 novos testes sobre a base já existente (529 → 535), `ruff check app.py` limpo

### Segurança (2026-07-26 — Auditoria AppSec, Fase 1: API endpoints/banco — CSRF)
- Removidas por completo as rotas legadas de escrita vulneráveis a CSRF (KI-025): `irflow_blueprints_orders.py`, `irflow_blueprints_inventory.py`, `irflow_blueprints_admin.py` deletados; `irflow_blueprints_auth.py` perdeu as views de gestão de usuário (`/usuarios/novo|editar|deletar` — o pior caso, permitia criar conta admin via CSRF); `irflow_blueprints_main.py::backup()` perdeu a lógica de escrita (POST), redundante com `POST /api/backup/criar` já usado pelo frontend. Causa raiz: `SESSION_COOKIE_SAMESITE="None"` em produção (necessário para o deploy cross-origin Vercel/Render) envia o cookie de sessão em requisições cross-site, e o projeto nunca teve `flask-wtf`/`CSRFProtect` — só uma config `WTF_CSRF_ENABLED=False` sem efeito nenhum em `tests/conftest.py`. Todo redirecionamento GET dessas rotas continua idêntico via `LEGACY_REACT_REDIRECTS` (independente da view function existir). Testes das rotas removidas removidos (cobertura equivalente já existe em `test_users.py`/`TestInatividadeSessaoApi`) — 524 testes no total, `ruff check .` limpo

### Corrigido (2026-07-27 — INC-001, rotas de checklist)
- `irflow_blueprints_api.py`: as 4 rotas de checklist (`GET/POST /api/ordens/<id>/checklist[/token]`, `GET/POST /api/checklist/<token>` — as duas últimas públicas, sem login) não tinham `try/except/finally` em torno da conexão SQLite, mesmo risco já corrigido em `auth_login()` — uma exceção entre abrir e fechar a conexão vazava a transação de escrita ainda aberta, bloqueando escritores seguintes em WAL. Envolvidas no mesmo padrão do hotfix de login, sem alterar contrato HTTP. 8 novos testes (`tests/test_inc001_checklist_connection_leak.py`) provam fechamento da conexão (confirmado que travam contra o código anterior) e contrato HTTP inalterado. 533 testes, `ruff check .` limpo

### Adicionado (2026-07-27 — INC-001, instrumentação transparente de conexões)
- `app.py`: `_ConexaoRastreada`, instrumentação estritamente observacional para diagnosticar o INC-001 em runtime — desligada por padrão (`IR_FLOW_DEBUG_CONN_TRACE=1` para ligar), loga OPEN/COMMIT/ROLLBACK/CLOSE via o logger estruturado já existente (`irflow_logging.py`, sem tocar nesse arquivo) e avisa via `weakref.finalize` (com stack resumida) se uma conexão for coletada pelo GC sem `close()`. `__getattr__`/`__setattr__` delegam à conexão real qualquer atributo/método não instrumentado — wrapper transparente, totalmente removível (vive só dentro de `conectar()`). Critérios de aceitação C-1 a C-9 documentados em `docs/operations/INCIDENTS/INC-001-database-is-locked.md`. Thread de sync do MercadoPhone nomeada `mercadophone-sync` (era `Thread-N`) para identificação nos logs. 8 novos testes (`tests/test_inc001_conn_trace_instrumentation.py`). 541 testes, `ruff check .` limpo. Substitui a branch `chore/inc-001-instrumentacao-conexoes` (2026-07-23, nunca mergeada, usava `print()`)

### Adicionado (2026-07-27 — C1.3.5, Rastreabilidade Individual de Itens de Estoque)
- `irflow_blueprints_api.py`: `requer_imei` (coluna já existente desde a Sprint P0.1, sem caminho de escrita) agora lido/gravado em `POST/PUT /api/estoque` e exposto em `GET /api/estoque` (KI-020). O nome da coluna é histórico (IMEI) — o conceito é rastreabilidade individual do item (IMEI hoje, outros identificadores no futuro), mesmo padrão já usado por `produtos.requer_rastreio_unidade`. Fecha o loop UI → API → banco → `unidades_serializadas` que antes só funcionava semeando o banco diretamente
- `frontend/src/pages/Stock.jsx`: checkbox "Requer rastreabilidade (IMEI / Nº de série)" no formulário de criar/editar item
- 8 novos testes: criação/listagem/atualização da flag via API (`test_stock_creation_query.py`, `test_stock_movement.py`) e fluxo completo — item marcado como rastreável via API permite criar `unidade_serializada` a partir dele; item sem a flag continua rejeitado (regressão, `test_unidades_serializadas.py::TestIntegracaoEstoqueViaApiC135`). 549 testes, `ruff check .` limpo, `npm run build`/`npm run lint` sem erros novos

### Adicionado (2026-07-27 — ADR-008, prefixo `fluxoly_` para módulos novos)
- `docs/engineering/adr/ADR-008.md`: decisão de rebranding técnico incremental — a partir de agora, todo domínio novo nasce com o prefixo `fluxoly_` (nome da marca), não `irflow_` (legado). Módulos existentes não são renomeados; ficam para um futuro Épico de Rebranding Técnico, registrado como dívida técnica (TD-12, sem prazo). `ENGINEERING_GUIDE.md` §3.1 atualizado com a nota do novo prefixo. Nenhum código alterado — só documentação/decisão

### Adicionado (2026-07-27 — Vendas MVP, primeiro fluxo comercial completo)
- `fluxoly_vendas_controller.py`/`_service.py`/`_repository.py` (novo, primeiro módulo com o prefixo `fluxoly_`, ver ADR-008): `POST /api/vendas` e `GET /api/vendas/<id>`. Venda de um único aparelho (unidade serializada) por vez — sem desconto, comissão, garantia, troca ou reserva com timeout, deliberadamente independente das decisões de negócio ainda pendentes do Product Owner em `docs/product/features/VENDAS.md`
- `app.py`: tabelas `vendas` e `vendas_itens` — modeladas como Venda + ItemVenda desde o início (mesmo com 1 item por venda nesta fatia, para não exigir refatoração estrutural quando vendas com múltiplos itens existirem); `status='concluida'` (não `'paga'` — venda e pagamento são conceitos diferentes); `vendas_itens.produto_nome`/`produto_sku` são snapshot no momento da venda; `UNIQUE` em `vendas_itens.unidade_serializada_id` garante no banco que a mesma unidade nunca aparece em duas vendas
- `irflow_unidades_serializadas_repository.py`/`_service.py`: `marcar_como_vendida` (nova, recebe `cursor` para viver na mesma transação de `iniciar_venda`) — deliberadamente separada de `transicionar_status`/`TRANSICOES_VALIDAS` para o endpoint genérico `PATCH .../status` continuar rejeitando `{"status": "vendido"}`, evitando uma porta lateral para marcar unidade vendida sem nenhuma `venda` real por trás. SKU adicionado às colunas de origem para o snapshot de `vendas_itens`
- Removido `irflow_vendas_service.py` (stub da Sprint 3 Unidade 7, nunca importado) — substituído pelos módulos reais
- 16 novos testes (`tests/test_vendas.py`), incluindo duas vendas concorrentes da mesma unidade via threads reais (exatamente uma sucede, confirmado 5x sem flakiness) e prova de rollback atômico em dois pontos distintos da transação (erro na criação do item; erro em `marcar_como_vendida`) — nenhuma venda órfã, unidade sempre volta a `disponivel`. Auditoria (`registrar_log_auditoria`) inclui `venda_id`/`vendedor_id` explícitos no JSON, além de `cliente_id`/`unidade_serializada_id`, para filtragem direta
- Refinamento (mesmo dia): `vendas_itens.valor_tabela` (snapshot do preço de catálogo — `estoque.valor`/`produtos.preco_venda`, exposto como `preco_catalogo` em `irflow_unidades_serializadas_service.py`, checagem explícita `is not None` em vez de `or` para não tratar preço `0` como ausente) e `vendas.observacoes`. `frontend/src/pages/Vendas.jsx` (rota `/vendas`, sidebar `admin`/`vendedor`): busca de cliente, busca combinada de aparelho com preço/SKU visíveis no resultado, preço pré-preenchido e editável com "preço de catálogo" sempre visível ao lado, resumo automático, tela de sucesso com Nova venda/Ver venda (busca real via `GET /api/vendas/<id>`)/Imprimir (placeholder). Validado manualmente ponta a ponta (servidor real + banco isolado, navegador dirigido via Chrome). 5 testes adicionais (21 no total do domínio). 570 testes, `ruff check .` limpo, `npm run build`/`npm run lint` sem erros novos

### Adicionado (2026-07-27 — Sprint Infra 1.1, CI Verde)
- Corrigidos 4 erros de ESLint que impediam o workflow `CI` de concluir com sucesso (`Compras.jsx`, `ShoppingModal.jsx`, `ServicesChartCard.jsx`, `TechnicianProfitChartCard.jsx`) — zero mudança de comportamento
- Pipeline validado e verde; proteção de branch ativada em `main` exigindo os 5 status checks do CI antes de merge
- Investigação completa (causas raiz históricas, ausência de proteção de branch) em KI-026/R-10/R-11; endurecimento adicional de governança (CODEOWNERS, revisão obrigatória) registrado como TD-13

### Adicionado (2026-07-27 — Sprint Vendas 1.1, Histórico + Detalhe de Vendas)
- `GET /api/vendas` (`fluxoly_vendas_controller.py`/`_service.py`/`_repository.py`): histórico paginado/filtrável (cliente, vendedor, forma de pagamento, status, intervalo de data) e ordenável (mais recente/mais antigo), com busca única por nome do cliente, IMEI ou nome do produto vendido. `GET /api/vendas/<id>` enriquecido com nome/telefone do cliente, nome do vendedor e IMEI do item via `LEFT JOIN` só para exibição — sem mudança de schema
- `frontend/src/pages/VendaDetalhe.jsx` (rota `/vendas/:id`): tela de detalhe estilo recibo (cabeçalho, cliente/vendedor/pagamento, observações, itens com valor de tabela/vendido/desconto/total), estrutura pensada para ser reaproveitada pela futura feature de Imprimir (V1.8 do roadmap)
- `frontend/src/pages/Vendas.jsx`: abas "Nova Venda"/"Histórico" (mesmo padrão de `Reports.jsx`); componente `Historico()` com busca, filtros, ordenação e paginação; botão "Ver venda" da tela de sucesso passa a navegar para `/vendas/:id` em vez de buscar o detalhe inline
- 10 novos testes (`tests/test_vendas.py`, 31 no total do domínio). 580 testes no repositório, `ruff check .` limpo, `npm run build`/`npm run lint` sem erros novos. Validado manualmente ponta a ponta (servidor real + banco isolado, navegador dirigido via Chrome): criação de venda, navegação "Ver venda" → detalhe, listagem/filtros/busca/paginação do histórico

### Adicionado (2026-07-27 — V1.2, Cancelamento de Venda)
- `POST /api/vendas/<id>/cancelar` — admin cancela qualquer venda, vendedor só as próprias, motivo obrigatório (lista fechada), cancelamento é terminal (sem reativação)
- Índice único de `vendas_itens.unidade_serializada_id` trocado por um parcial (`WHERE ativo=1`) — permite revenda da mesma unidade após cancelamento sem apagar o histórico da venda cancelada
- Histórico de vendas ganhou filtro e badge de status (Concluída/Cancelada)
- Regras de negócio fechadas antes do código (BR-031 a BR-036, `VENDAS.md`/`BUSINESS_RULES.md`); 14 novos testes (592 no total)

### Adicionado (2026-07-28 — ADR-010, ciclo de feature com regra de negócio)
- `docs/engineering/adr/ADR-010.md`: formaliza o processo Discovery → Plano Técnico → Implementação → Testes → QA Manual → Encerramento, cada etapa com gate de aprovação explícito, e o Princípio da Separação de Decisões (Plano Técnico nunca decide regra de negócio)
- Novo artefato `docs/engineering/plans/PLAN-<slug>.md` (template em `docs/engineering/templates/PLAN_TEMPLATE.md`), deliberadamente efêmero — histórico da decisão de implementação, não documentação viva

### Adicionado (2026-07-28 — V1.3, Descontos e Aprovação)
- `usuarios.limite_desconto_livre` (R$, `NULL` = não configurado — o service, nunca uma query SQL, trata isso como limite efetivo R$0); `POST /api/vendas` exige `desconto_aprovado=true` explícito quando o desconto excede o limite do vendedor — aprovação acontece fora do sistema, o backend só registra a confirmação e o timestamp (`vendas_itens.desconto_aprovado_em`), nunca quem aprovou (BR-037, BR-038)
- Ajuste Comercial Autorizado (`PATCH /api/vendas/<id>/itens/<id>/ajuste-desconto`) — única exceção formal ao Princípio da Imutabilidade da Venda (BR-034): só `admin`, motivo obrigatório, recálculo transacional (item → soma dos itens ativos → `valor_total`), auditoria append-only via `audit_log`, compare-and-swap contra cancelamento concorrente (BR-043)
- Regras de negócio fechadas antes do código pela ótica do fluxo real de negociação da loja, não uma lista de perguntas técnicas isoladas (BR-037 a BR-043); primeira feature a seguir o ciclo formal de `ADR-010`
- 21 novos testes (613 no total). QA Manual (navegador real, servidor real, banco isolado, 6 cenários) encontrou e corrigiu 1 bug real: `limite_desconto_livre` ausente na resposta de `POST /api/auth/login` (`Login.jsx` populava o `AuthContext` direto dessa resposta, sem esperar `/api/auth/me`)

### Removido (2026-07-29 — reversão do bloqueio de desconto da V1.3, BR-053)
- Bloqueio preventivo de desconto (BR-037/BR-038, revogadas): `limite_desconto_livre` e `desconto_aprovado_em` parados de ler/gravar em qualquer fluxo (Vendas/Usuários) e removidos das respostas de `POST /api/auth/login` e `GET /api/auth/me`; todo desconto passa a ser sempre aceito e sempre registrado, sem exigir aprovação. Colunas mantidas no schema, marcadas como deprecadas em comentário — só compatibilidade histórica com vendas já feitas na V1.3
- UI correspondente no frontend: aviso de "desconto excede o limite" e checkbox de confirmação de aprovação em `Vendas.jsx`; campo "Limite de desconto livre" em `Users.jsx`

### Adicionado (2026-07-29 — V1.4, Comissão)
- Novo perfil de usuário `financeiro` (`PERFIS_OPCOES`), ao lado de `admin`/`tecnico`/`vendedor`/`estoque` — acompanhamento financeiro das vendas, não substitui `admin`
- `vendas_itens.comissao_valor` (R$, `NULL` = ainda não atribuída) — atribuição manual por `admin`/`financeiro` via `PATCH /api/vendas/<id>/itens/<id>/comissao`, sempre em R$, sem campo de "tipo" (fixo/percentual): o valor final gravado é sempre o que importa, independente de como financeiro chegou nele (BR-044 a BR-048)
- `GET /api/vendas/<id>/itens/<id>/historico-comissao` — histórico de alterações via `audit_log`, restrito a `admin`/`financeiro` (diferente do histórico de desconto, que é aberto a qualquer autenticado) (BR-049)
- `comissao_valor` ocultado de qualquer perfil que não seja `admin`/`financeiro`, centralizado numa única função (`_ocultar_comissao_se_necessario`) aplicada em `GET /api/vendas/<id>` e na listagem — para uma rota de leitura nova não vazar o campo por esquecimento (BR-047)
- Comissão zerada automaticamente no cancelamento da venda, mesma transação, sempre com evento de auditoria (BR-051)
- Discovery revisitou e revogou o modelo de bloqueio da V1.3 na mesma sessão (ver acima); segunda feature a seguir o ciclo formal de `ADR-010`
- 15 novos testes de comissão + 6 reescritos da reversão (625 no total). QA Manual via `curl` (14 cenários, `docs/engineering/plans/PLAN-V1.4-Comissao.md`) — navegador real indisponível neste ambiente por limitação do ambiente de automação, não do produto (KI-027)

### Corrigido (2026-07-30 — responsividade do Dashboard em telas de notebook/MacBook)
- `frontend/src/pages/Dashboard.jsx`: grids de KPIs e gráficos usavam contagem fixa de colunas por breakpoint (`lg:grid-cols-3 xl:grid-cols-6`, `lg:grid-cols-2`), pulando abruptamente entre 3 e 6 colunas e deixando espaço em branco em larguras intermediárias (1366–1728px, faixa típica de MacBook). Trocado por CSS Grid `auto-fit`/`minmax` (KPIs: `minmax(280px,1fr)`; gráficos: `minmax(420px,1fr)`), que ajusta o número de colunas ao espaço real disponível. Mobile (`grid-cols-2` abaixo de `sm`) preservado sem alteração
- `minmax(280px,1fr)` nos KPIs (não 200px): validado que 200px truncava valores monetários de notebook ("R$ 128.450,90"); medido via `scrollWidth`/`clientWidth` (não só cálculo de grid) que 280px não trunca em nenhuma das 6 larguras-alvo (1280/1366/1440/1512/1728/1920px) com valores realistas
- `KpiCard.jsx` e os 3 cartões de gráfico já eram fluidos (`ResponsiveContainer width="100%"`, truncamento de valor do fix de 2026-07-26) — não precisaram de mudança
- Validação visual num MacBook real não foi possível nesta sessão (sem acesso físico a Mac); validação por medição real de overflow no DOM (`scrollWidth`/`clientWidth`), não só cálculo de CSS

### Adicionado (2026-07-30 — V1.5, Garantia de Venda e Garantia de Reparo)
- Novo cadastro **Tipos de Garantia** (nome + duração em meses), `admin`-only para escrita, leitura aberta a qualquer autenticado — compartilhado entre Vendas e Assistência (`fluxoly_tipos_garantia_controller/service/repository.py`, BR-055)
- Garantia de Venda: `tipo_garantia_id` obrigatório em `POST /api/vendas` (BR-056); snapshot completo (nome/duração/datas) congelado no momento da venda, nunca recalculado ao vivo (BR-057); cancelamento zera o snapshot com auditoria (BR-058); correção restrita a `admin`, sem motivo (`PATCH /api/vendas/<id>/itens/<id>/garantia`, BR-059)
- Garantia de Reparo: `tipo_garantia_id` obrigatório por linha de reparo (`os_reparos`) na transição da OS para `Finalizado` (BR-061), mesmo padrão de snapshot (BR-062) e correção admin-only (`PATCH /api/ordens/<id>/reparos/<reparo_id>/garantia`, BR-065). `salvar_reparos_os()` reescrita de `DELETE`+`INSERT` cego para sync não-destrutivo — necessário para não apagar a garantia já concedida de uma linha mantida ao editar a OS sem mexer no status
- `irflow_core.py::calcular_data_fim_garantia()` — soma meses de calendário tratando dia inexistente no mês de destino (ex.: 31/01 + 1 mês → 28/02), função pura compartilhada entre Vendas e Assistência
- `listar_garantias()` (`/api/garantias`) reescrita para gerar uma entrada por linha de reparo (não mais por OS inteira), substituindo o prazo fixo de 90 dias (`GARANTIA_REPARO_DIAS_PADRAO`) para dados novos — fallback preservado para dados históricos (`tipo_garantia_id NULL`), nunca inventa garantia que não foi concedida
- Frontend: página **Tipos de Garantia** (CRUD, `admin`-only); campo obrigatório em `Vendas.jsx`; seção de garantia + correção + histórico em `VendaDetalhe.jsx`; dialog de seleção por reparo em `EditOrder.jsx` ao concluir OS; `Garantias.jsx` reagrupada por linha de reparo (OS/Cliente/Modelo não repetidos em linhas consecutivas da mesma OS); `Clientes.jsx` ajustado ao novo formato
- Ciclo completo do ADR-010 (Discovery → Plano Técnico → Implementação → Testes → QA Manual → Revisão Arquitetural → Encerramento), plano em `docs/engineering/plans/PLAN-V1.5-Garantia.md`. QA Manual com servidor real + banco isolado + navegador real (login funcionou normalmente nesta sessão — ver observação em KI-027); Revisão Arquitetural sem inconsistência não documentada
- 693 testes no total, `ruff check .` limpo, `npm run lint`/`npm run build` sem erros novos

### Corrigido (2026-07-30 — KI-028, datas de garantia exibidas um dia atrasadas)
- `VendaDetalhe.jsx`: `garantia_data_fim` era formatado com `new Date(string).toLocaleDateString("pt-BR")` — para datas puras (`YYYY-MM-DD`, sem horário), o JS interpreta como UTC-meia-noite e o navegador renderiza no fuso local, voltando um dia em fusos negativos (`America/Sao_Paulo`). Corrigido reaproveitando `formatDateTime()`, helper já existente no mesmo arquivo que faz o parse manual de ano/mês/dia. Escopo restrito ao campo novo da V1.5 — mesmo padrão em outras telas (`Garantias.jsx`, `Clientes.jsx`, `OperationalCosts.jsx`, `Reports.jsx`, `Stock.jsx`) registrado, não corrigido (fora do escopo desta feature)

### Adicionado (2026-07-30 — Observabilidade: Sentry completo no backend + frontend novo)
- `app.py`: `sentry_sdk.init()` (já existente desde 2026-07-25, inativo) ganha `environment` (produção/dev via `IS_SERVER_RUNTIME`) e `release` (`RENDER_GIT_COMMIT`, injetada automaticamente pelo Render). Fecha TD-02
- Frontend (novo): `@sentry/react` inicializado em `main.jsx`, condicional a `VITE_SENTRY_DSN`; `App` envolvido em `Sentry.ErrorBoundary` com fallback simples em vez de tela branca crashada; `release` via `vite.config.js` (`VERCEL_GIT_COMMIT_SHA`, injetada automaticamente pela Vercel)
- `send_default_pii=False`/`traces_sample_rate=0` (backend, já decidido em 2026-07-25) espelhados no frontend — sem PII de cliente, sem tracing de performance
- QA Manual: exceção proposital real disparada nos dois lados contra os DSNs reais — backend confirmado via log de debug do SDK (`Sending envelope ... project:<id do projeto backend>`); frontend confirmado via 3 requisições `POST` reais (200) ao endpoint de ingest do Sentry, capturadas na aba de rede do navegador. Nenhum gatilho de teste permanece no código
- Plano em `docs/engineering/plans/PLAN-Observabilidade-Sentry-Frontend.md`. 693 testes (+2 novos em `test_sentry_init.py`), `ruff check .`/`npm run lint`/`npm run build` sem erros novos

### Adicionado (2026-07-31 — Sprint CI/CD 1.1 — Hardening)
- Cobertura mínima elevada de 40% para 60% (`pyproject.toml`, `ci.yml`) — cobertura real medida em 65.22%/682 testes no momento da mudança
- Novo job `Docker Build` no CI (`docker build .`, sem publicar) — valida que a imagem builda antes do merge, não só na hora do deploy; testado localmente via Colima
- `main` passa a exigir 6 status checks obrigatórios (era 5): Lint, Backend Tests, Frontend Quality, Frontend Build, Coverage Report, Docker Build
- Revisão corrigiu uma premissa equivocada: o pipeline de CI/CD já existia e já era bloqueante desde a Sprint Infra 1.1 (2026-07-27) — esta sprint só fortalece o que já funcionava (threshold de cobertura + gate de Docker), não cria o pipeline do zero
- `docs/engineering/QUALITY_GATES.md` atualizado — estava desatualizado desde 2026-07-06 (antes da Sprint Infra 1.1), com vários gates listados como "Planejado"/"Manual" que já estavam ativos em CI há dias
- Deploy continua manual — decisão deliberada de não automatizar nesta sprint

### Refatorado (2026-08-03 — Sprint Housekeeping, Rebranding Técnico TD-12)
- Todos os módulos `.py` renomeados de `irflow_*` para `fluxoly_*` (18 módulos + 2 hubs de risco médio + `fluxoly_blueprints_api.py`, o último com prefixo legado), um lote por commit, cada um validado com Graphify, `ruff` e suíte completa antes de avançar
- Branding residual "IR Flow" corrigido em frontend (README, `index.css`, `client.js`), `app.py` e demais módulos (docstrings, nomes de logger, texto de e-mail de backup)
- Referência morta `irflow_vendas_service` em `pyproject.toml` corrigida para `fluxoly_vendas_service` (nunca existiu com esse nome — escapou da limpeza inicial)
- `ADR-011` registra que a decomposição de `fluxoly_blueprints_api.py` (TD-01) — decisão já existente na `ADR-002` desde 2026-07-06, nunca executada — fica formalmente fora desta sprint, com escopo atualizado (6→13 domínios reais, 70 rotas, 78 dependências injetadas)
- Fora do escopo, adiados com dono definido: senha de seed `irflow@2024` (toca `app.py`, muda comportamento de login — tarefa de segurança própria), variáveis `IR_FLOW_*` e infraestrutura Render/Vercel (janela de manutenção ligada a `RELEASE_1.0_MASTER_CHECKLIST.md`)
- Achado no fechamento: auto-deploy não estava configurado no serviço Render (todos os deploys históricos eram manuais) — Manual Deploy disparado para validar o rename em produção

### Adicionado (2026-08-05 — Avaliação de proposta externa de evolução SaaS)
- `docs/engineering/FUTURE_TECH_EVALUATIONS.md` — ideias técnicas de longo prazo (Next.js para landing/marketing, BetterAuth, PostgreSQL, Supabase, Redis, Resend, Firebase Cloud Messaging), extraídas de uma proposta externa de evolução do Fluxoly para SaaS. Proposta contestada antes de qualquer registro: verificado que `ADR-001` já rejeita Next.js para o sistema interno, que não existe `ADR-012` nem `frontend-next/` no repositório, e que nenhuma das tecnologias citadas tem decisão aprovada em nenhum ADR/roadmap. Cada item registrado com contexto/benefícios/riscos/momento recomendado de avaliação — documento explicitamente não-vinculante, ADR só nasce quando houver decisão real. `docs/README.md` recebeu entrada de índice

### Modificado (2026-08-05 — reordenação das 6 Fases estratégicas)
- `docs/company/RELEASE_STRATEGY.md` — Multiempresa move de Fase 3 para Fase 5, depois de Automação (Fase 3) e Inteligência (Fase 4). Decisão de priorização de negócio (validar produto via Automação/IA antes de investir em billing/planos multiempresa), não dependência técnica — a única dependência técnica de Multiempresa continua sendo a Fase 2 (Infraestrutura SaaS) pronta e a decisão pendente em `ADR-005.md`. Nova subseção "Decisão: Multiempresa adiada para depois de Automação e Inteligência" documenta o motivo
- `docs/company/DECISION_LOG.md` — entrada de 2026-08-05 registrando as duas decisões desta sessão (reordenação das Fases 3-5; proposta de stack SaaS tratada como planejamento, não ADR)

### Adicionado (2026-08-05 — TD-01 Phase 2, 2º domínio extraído: Garantias)
- `api_garantias.py` — `Blueprint` próprio para `GET /api/garantias` (listagem agregada de garantias),
  extraído de `fluxoly_blueprints_api.py` seguindo exatamente o padrão já validado em `api_shopping.py`
  (1º domínio, 2026-08-04): `deps` parcial (só `conectar`/`garantia_reparo_dias_padrao`/`parse_data_ymd`,
  as duas últimas continuam também no dict do monólito porque OS e Sistema ainda dependem delas — mesma
  regra "duplicar referência, nunca lógica" da Phase 1), helper específico do domínio
  (`_classificar_garantia`) migrado junto, `err`/`ok`/`usuario_logado` reaproveitados de
  `fluxoly_api_helpers.py`. 682 testes passando sem alteração (incluindo `test_listar_garantias.py`
  intacto), `ruff check .` limpo, `graphify update .` + `explain`/`affected` confirmados sem referência
  residual do domínio no monólito. Ver `docs/operations/SPRINTS/SPRINT_TD01_MODULARIZACAO_API.md` e
  `docs/engineering/API_DEPENDENCY_MATRIX.md`

### Adicionado (2026-08-06 — TD-01 Phase 2, 3º domínio extraído: Custos Operacionais)
- `api_costs.py` — `Blueprint` próprio para o CRUD de custos operacionais (`GET/POST /api/custos`,
  `PUT/DELETE /api/custos/<id>`), extraído de `fluxoly_blueprints_api.py` seguindo o mesmo padrão de
  `api_shopping.py`/`api_garantias.py`: `deps` parcial (`conectar`, `listar_custos_operacionais` — este
  último continua também no dict do monólito porque `/dashboard` e `/relatorios/custos-operacionais`
  ainda dependem dele — mesma regra "duplicar referência, nunca lógica"). `usuario_admin()` promovido
  para `fluxoly_api_helpers.py` (previsto desde a Phase 1, agora comprovadamente usado por 2+ domínios);
  cópia local no monólito mantida intacta (cleanup fica para a Phase 3). 683 testes passando sem
  alteração, `ruff check .` limpo, `graphify update .` + `explain`/`affected` confirmados sem referência
  residual do domínio no monólito. Ver `docs/operations/SPRINTS/SPRINT_TD01_MODULARIZACAO_API.md` e
  `docs/engineering/API_DEPENDENCY_MATRIX.md`

### Adicionado (2026-08-06 — TD-01 Phase 2, 4º domínio extraído: Preços)
- `api_prices.py` — `Blueprint` próprio para o CRUD de tabelas de preço (`GET/POST /api/precos`,
  `POST /api/precos/excluir`, `GET /api/precos/sugerir`), extraído de `fluxoly_blueprints_api.py`.
  Assimetria de autorização original preservada verbatim (`sugerir_preco()` só exige
  `usuario_logado()`, as outras 3 exigem também `usuario_admin()`). Diferente das 3 extrações
  anteriores: `carregar_tabelas_preco`/`salvar_tabelas_preco` não têm outro consumidor no monólito, então
  as chaves saíram do dict de `create_api_blueprint` em `app.py` em vez de ficarem duplicadas — primeiro
  domínio da Phase 2 a reduzir `deps` de fato. 683 testes passando sem alteração, `ruff check .` limpo,
  `graphify update .` + `explain "api_prices"` confirmados sem referência residual do domínio no
  monólito. Ver `docs/operations/SPRINTS/SPRINT_TD01_MODULARIZACAO_API.md` e
  `docs/engineering/API_DEPENDENCY_MATRIX.md`

### Adicionado (2026-08-06 — TD-01 Phase 2, 5º domínio extraído: Usuários)
- `api_users.py` — `Blueprint` próprio para o CRUD de usuários e reset de senha (`GET/POST/PUT/DELETE
  /api/usuarios*`, `POST /api/usuarios/<id>/reset-token`, `POST /api/password-reset/<token>`), extraído
  de `fluxoly_blueprints_api.py`. Assimetria de autorização preservada verbatim (só
  `consumir_token_reset_senha` é pública). `generate_password_hash`/`perfis_opcoes` saíram do dict de
  `create_api_blueprint` em `app.py` (sem outro consumidor no monólito — o outro uso legítimo, em
  `create_auth_blueprint`, ficou intacto). Primeira aplicação da nova regra do DoD
  (`graphify affected`/`explain` antes de remover uma dep): a ferramenta não indexa chave de dict/import
  de biblioteca terceira como nó próprio, verificação feita por leitura completa em substituição.
  Corrigidos no mesmo commit: `tests/test_users.py` (referenciava o endpoint qualificado do blueprint
  antigo) e `import sqlite3` órfão em `fluxoly_blueprints_api.py`. 683 testes passando, `ruff check .`
  limpo, `graphify update .` + `explain "api_users"` confirmados sem referência residual do domínio no
  monólito. Ver `docs/operations/SPRINTS/SPRINT_TD01_MODULARIZACAO_API.md` e
  `docs/engineering/API_DEPENDENCY_MATRIX.md`

### Adicionado (2026-08-06 — TD-01 Phase 2, 6º domínio extraído: Auth)
- `api_auth.py` — `Blueprint` próprio para autenticação JSON (`POST /api/auth/login`, `POST
  /api/auth/logout`, `GET /api/auth/me`), extraído de `fluxoly_blueprints_api.py` **verbatim, inclusive
  comentários** — o comentário do INC-001 em `auth_login()` explicando o `try/except/finally` foi
  preservado sem nenhuma alteração de lógica, por regra explícita do plano (não misturar refatoração
  estrutural com mudança de comportamento em rota de autenticação). `resolver_ip_cliente`/
  `limite_excedido`/`registrar_tentativa`/`check_password_hash` saíram do dict de `create_api_blueprint`
  em `app.py` (sem outro consumidor no monólito; uso legítimo em `create_auth_blueprint` ficou intacto).
  Segunda aplicação da regra do DoD de verificar via Graphify antes de remover uma dep — desta vez a
  ferramenta resolveu os símbolos do projeto (`fluxoly_rate_limit.py`) e confirmou ausência de
  consumidor residual (`check_password_hash`, de `werkzeug`, seguiu sem match, mesma limitação já vista
  em Usuários). Corrigido no mesmo commit: `tests/test_inc001_login_connection_leak.py` referenciava o
  endpoint qualificado do blueprint antigo. 683 testes passando, `ruff check .` limpo, `graphify
  update .` + `explain "api_auth"` confirmados sem referência residual do domínio no monólito. Ver
  `docs/operations/SPRINTS/SPRINT_TD01_MODULARIZACAO_API.md` e
  `docs/engineering/API_DEPENDENCY_MATRIX.md`

### Adicionado (2026-08-06 — TD-01 Phase 2, 7º domínio extraído: Backup)
- `api_backup.py` — `Blueprint` próprio para backup/restauração do banco (`POST /api/backup/criar`,
  `GET /api/backup/listar`, `GET /api/backup/download/<filename>`, `POST /api/backup/restaurar`),
  extraído de `fluxoly_blueprints_api.py` verbatim. `_texto_limpo_local()` promovido para
  `fluxoly_api_helpers.py` — diferente das extrações anteriores, o outro consumidor
  (`MercadoPhone`) ainda vive dentro do próprio monólito, não em um blueprint separado; sequência
  seguida: promover → importar no monólito → confirmar suíte filtrada de MercadoPhone → remover
  implementação local. Verificação tripla (Graphify `affected`/`explain` + grep textual) nos deps mais
  sensíveis, confirmando zero resíduo (`criar_backup` também é chamado por
  `executar_backup_diario_automatico()`, agendador independente, não afetado).
  `garantir_pasta_backup_google_drive` (dead code pré-existente) mantida intocada, fora de escopo.
  3 imports órfãos (`contextlib`, `os`, `flask.send_from_directory`) removidos no mesmo commit. 683
  testes passando, `ruff check .` limpo, `graphify update .` + `explain "api_backup"` confirmados sem
  referência residual do domínio no monólito. Ver
  `docs/operations/SPRINTS/SPRINT_TD01_MODULARIZACAO_API.md` e
  `docs/engineering/API_DEPENDENCY_MATRIX.md`

### Adicionado (2026-08-06 — TD-01 Phase 2, 8º domínio extraído: Relatórios)
- `api_reports.py` — `Blueprint` próprio para relatórios agregados e PDF (`GET
  /api/relatorios/{ir-phones,tecnicos,custos-operacionais}` + `GET
  /api/relatorios/pdf/{ir-phones,tecnicos,custos-operacionais}`), extraído de
  `fluxoly_blueprints_api.py` verbatim. Acoplamento baixo no nível do blueprint (nenhuma chamada direta
  a OS/Estoque/Preços/Clientes — toda a lógica já vive em `fluxoly_reports.py`). Corrigida a matriz:
  `tecnicos` não pertence a este domínio (8 deps, não 9). 6 das 8 deps também são usadas por
  `create_main_blueprint` (páginas renderizadas no servidor) — verificado explicitamente intacto antes e
  depois da edição. KI-031 registrado: zero teste automatizado cobre estas 6 rotas; smoke test manual
  (Flask test client, banco temporário isolado) confirmou HTTP 200 e PDFs reais (`%PDF-1.4`) antes do
  commit — nova regra permanente adicionada ao DoD da Phase 2 para domínios sem cobertura. 683 testes
  passando sem alteração, `ruff check .` limpo, `graphify update .` + `explain "api_reports"`
  confirmados sem referência residual do domínio no monólito. Ver
  `docs/operations/SPRINTS/SPRINT_TD01_MODULARIZACAO_API.md` e
  `docs/engineering/API_DEPENDENCY_MATRIX.md`

### Adicionado (2026-08-06 — TD-01 Phase 2, 9º domínio extraído: MercadoPhone)
- `api_mercadophone.py` — `Blueprint` próprio para a integração MercadoPhone (`sincronizar`,
  `reprocessar`+`/status`, `reimportar`+`/status`, `status`, `config`), extraído de
  `fluxoly_blueprints_api.py`. Domínio mais acoplado extraído até agora: Discovery tratada como matriz
  de acoplamento completa revelou que `_carregar_config_mercadophone()`/`_atualizar_runtime_mercadophone()`/
  `mercado_phone_runtime_config` também são usados por `listar_ordens()` (domínio OS, ainda no
  monólito) — risco já registrado na Phase 0. Resolvido promovendo as 2 funções para
  `fluxoly_mercadophone.py` (serviço com parâmetros explícitos, não `fluxoly_api_helpers.py` — é lógica
  de domínio, não helper web genérico), em etapa de validação isolada antes da extração do blueprint
  (commit `59c26c6`), com 111 testes filtrados de OS+MercadoPhone confirmando a migração antes de
  seguir. Smoke test manual confirmou as 3 rotas sem cobertura automatizada
  (`/reprocessar/status`, `/reimportar/status`, `GET /status`). `import threading` órfão removido do
  monólito. 683 testes passando, `ruff check .` limpo, `graphify update .` + `explain
  "api_mercadophone"` confirmados sem referência residual. **Architecture Checkpoint pós-MercadoPhone:**
  26 rotas restantes (-63% desde a Phase 0), 80KB/1.961 linhas em `fluxoly_blueprints_api.py`; `app.py`
  em 2.431 linhas/100KB/17 `register_blueprint()` — nova métrica permanente de acompanhamento. Ver
  `docs/operations/SPRINTS/SPRINT_TD01_MODULARIZACAO_API.md` e
  `docs/engineering/API_DEPENDENCY_MATRIX.md`

### Adicionado (2026-08-07 — TD-01 Phase 2, 10º domínio extraído: Sistema)
- `api_system.py` — `Blueprint` próprio para `GET /constantes`, `GET /alertas`, `GET /dashboard`,
  extraído de `fluxoly_blueprints_api.py`. Corrigida a matriz: `texto_reparos_os` não pertence a este
  domínio (21 deps, não 22 — pertence a `_os_row_to_dict()`, domínio OS). Achado de acoplamento:
  `ESTOQUE_TIPOS`/`ESTOQUE_QUALIDADES` eram constantes locais dentro do monólito, usadas também pelos
  helpers de Estoque (`_normalizar_tipo_estoque`/`_normalizar_qualidade_estoque`, domínio 11/12, ainda
  não extraído) — promovidas para `fluxoly_reference_data.py` (mesmo lugar de `IPHONE_MODELS`/
  `VENDEDORES`/`TECNICOS`), sem mudança de regra de negócio. 12 chaves saem do dict de
  `create_api_blueprint` (deps reduzido); as ligadas a OS continuam duplicadas. Smoke test manual
  confirmou `/alertas`/`/dashboard` (sem cobertura automatizada). 683 testes passando, `ruff check .`
  limpo, `graphify update .` + `explain "api_system"` + `affected "fluxoly_blueprints_api.py"`
  confirmados sem referência residual. Restam Estoque, OS. Ver
  `docs/operations/SPRINTS/SPRINT_TD01_MODULARIZACAO_API.md` e
  `docs/engineering/API_DEPENDENCY_MATRIX.md`

### Adicionado (2026-08-07 — TD-01 Phase 2, 11º domínio extraído: Estoque)
- `api_stock.py` — `Blueprint` próprio para `GET/POST /estoque`, `PUT/DELETE /estoque/<id>`,
  `GET /estoque/reposicao-sugerida`, `GET /estoque/movimentacoes`, extraído de
  `fluxoly_blueprints_api.py`. Cobertura automatizada já existente (77 testes) — sem necessidade de
  smoke test manual. Corrigida a matriz: deps reais são 5, não 3 (`conectar`,
  `normalizar_modelo_iphone`, `registrar_movimentacao`, `estoque_tipos`, `estoque_qualidades` — as duas
  últimas só passaram a existir como deps compartilhadas depois da extração de Sistema, no mesmo dia).
  Achado de código morto (não capturado pela matriz, registrado em KI-032): `_slug_estoque`/
  `_gerar_sku_estoque` (geração automática de SKU) definidos no monólito mas nunca chamados por nenhuma
  rota real — não migrados, permanecem em `fluxoly_blueprints_api.py` para não misturar refatoração com
  limpeza de código, candidatos a remoção na Phase 3. Acoplamento OS↔Estoque confirmado como
  unidirecional (vive inteiramente do lado de OS) — extração sem bloqueio de acoplamento cruzado real.
  4 chaves saem do dict de `create_api_blueprint` (deps reduzido); `conectar` continua duplicada — OS
  (12/12, último domínio) depende dela. Ruff removeu 3 imports órfãos (`math`, `datetime.timedelta`,
  `validate_positive_number`) após a extração. 683 testes passando, `ruff check .` limpo em todo o
  repositório, `graphify update .` + `explain "api_stock"` + `affected "fluxoly_blueprints_api.py"`
  confirmados sem referência residual. Resta apenas OS. Ver
  `docs/operations/SPRINTS/SPRINT_TD01_MODULARIZACAO_API.md` e
  `docs/engineering/API_DEPENDENCY_MATRIX.md`

### Adicionado (2026-08-07 — TD-01 Phase 2 CONCLUÍDA, 12º e último domínio extraído: OS + Reparos)
- `api_os.py` — `Blueprint` próprio para as 13 rotas de Ordens de Serviço (CRUD, checklist público e
  autenticado, garantia por reparo, histórico de cliente) e as 4 rotas do catálogo de Reparos, extraído
  de `fluxoly_blueprints_api.py`. Corrigida a matriz: deps reais são 35, não 32 (faltavam
  `public_base_url`, `integrations_config_path`, `carregar_configuracoes_integracoes`). Único ponto de
  todo o domínio fora do padrão puro `deps[...]`: `listar_ordens()` importa
  `carregar_config_mercadophone`/`atualizar_runtime_mercadophone` diretamente de
  `fluxoly_mercadophone.py`. Achado de dep morta pré-existente (`status_em_andamento`/
  `status_aguardando_peca`, nunca lidas por nenhuma rota) removida do dict de `app.py` junto desta
  extração. Bug de transcrição (corte de linha via `sed`) introduzido e corrigido durante a extração —
  `deletar_reparo()` perdeu temporariamente o `return ok()` final, pego pelo smoke test manual do
  catálogo de Reparos (KI-033, registrada antes da extração) e revalidado com diff linha a linha contra
  o código original (zero divergência). 1 teste ajustado por consequência mecânica do rename do
  blueprint (`api` → `api_os`, `tests/test_inc001_checklist_connection_leak.py`). 683 testes passando
  (mesmo total), `ruff check .` limpo em todo o repositório, `graphify update .` +
  `explain "api_os"` + `affected "fluxoly_blueprints_api.py"` confirmados sem referência residual.
  **`fluxoly_blueprints_api.py` reduzido a 911 bytes/34 linhas/0 rotas** — só resta código morto
  (`_slug_estoque`/`_gerar_sku_estoque`, KI-032) e um `Blueprint` vazio, ainda registrado por `app.py`.
  **TD-01 Phase 2 (Extração Incremental) formalmente concluída — 12/12 domínios.** Architecture
  Checkpoint Final registrado em `docs/operations/SPRINTS/SPRINT_TD01_MODULARIZACAO_API.md`
  (`fluxoly_blueprints_api.py`: 70 rotas/~130KB → 0 rotas/911 bytes; `app.py`: 20 `register_blueprint()`
  hoje, candidato central para uma futura TD-02). **Decisão do usuário (CTO): TD-01 encerrada
  formalmente aqui** — Phase 3 (Cleanup, remover `fluxoly_blueprints_api.py`/
  `create_api_blueprint({})`, resolver KI-032) registrada como TD-18, backlog sem prazo, separada de
  uma futura TD-02. KI-003 movida para Resolvidos. Ver
  `docs/operations/SPRINTS/SPRINT_TD01_MODULARIZACAO_API.md` e
  `docs/engineering/API_DEPENDENCY_MATRIX.md`

### Adicionado (2026-08-07 — TD-02 Phase 2, Fatia 1/4: `fluxoly_config.py`)
- `fluxoly_config.py` — constantes de ambiente/paths/feature-flags (bloco B de `app.py`, ~98 linhas)
  extraídas para módulo próprio: `os.environ`/derivação de constantes puras, zero import de Flask,
  testável por importação direta. `app.py` passa a importar 22 nomes de `fluxoly_config`; `import
  shutil` removido de `app.py` por ter ficado sem uso. `app.url_map` idêntico (122 rotas), 682 testes
  passando (1 falha pré-existente/ambiental confirmada contra `main`, sem relação com a mudança), `ruff
  check`/`black --check` limpos, `graphify update .` rodado. Ver
  `docs/operations/SPRINTS/SPRINT_TD02_BOOTSTRAP_APP.md`

### Adicionado (2026-08-07 — TD-02 Phase 2, Fatia 2/4: `fluxoly_app_security.py`)
- `fluxoly_app_security.py` — factory `configurar_seguranca(app, cors_origins)`: CORS, headers de
  segurança (CSP/X-Frame-Options) e os dois `@app.after_request` associados, extraídos do bloco C de
  `app.py`. `FLASK_SECRET_KEY`, cookie de sessão e cálculo de `cors_origins` permanecem em `app.py`
  (bootstrap real, único lugar que lê `IR_FLOW_CORS_ORIGINS`/`VERCEL_URL`). `app.url_map` idêntico (122
  rotas), 682 testes passando, `ruff check`/`black --check` limpos, `graphify update .` rodado. Ver
  `docs/operations/SPRINTS/SPRINT_TD02_BOOTSTRAP_APP.md`

### Adicionado (2026-08-08 — TD-02 Phase 2, Fatia 3/4: `fluxoly_blueprint_registry.py`)
- `fluxoly_blueprint_registry.py` — núcleo da sprint. As 20 chamadas `app.register_blueprint(...)`
  inline (bloco K de `app.py`) movidas para `registrar_blueprints(app, runtime)`: mesma ordem, mesmos
  dicts de `deps`, nenhuma factory `create_*_blueprint` mudou. `RuntimeDeps` (dataclass, 9 campos) carrega
  os valores construídos em runtime dentro de `app.py` que não podem ser importados direto sem criar
  import circular: `conectar`, `carregar_tabelas_preco`, `salvar_tabelas_preco`,
  `forcar_migracao_schema`, `mercado_phone_runtime_config`, `mercado_phone_helpers`,
  `listar_custos_operacionais`, `obter_alertas_sistema`, e `parse_data_ymd` — 9º campo, achado durante a
  implementação (função pura definida em `app.py`, fora do mapeamento original de 8 campos da Phase 1,
  consumida por `main_views`/`api_garantias`/`api_os`; decisão do usuário — CTO — de adicionar como campo
  em vez de mover a função de lugar nesta fatia). `app.py`: 2.341 → 1.923 linhas (-418, -18%), termina só
  montando o `RuntimeDeps` e chamando `registrar_blueprints(app, runtime)`. `app.url_map` idêntico (122
  rotas), 683 testes passando, `ruff`/`black`/`isort` limpos, `graphify update .` rodado, CI verde (6/6
  checks). Ver `docs/operations/SPRINTS/SPRINT_TD02_BOOTSTRAP_APP.md`

### Adicionado (2026-08-08 — TD-02 Phase 2, Fatia 4/4 CONCLUÍDA: webhook MercadoPhone → `api_mercadophone.py`)
- `api_mercadophone.py` ganha `POST /integracoes/mercadophone/os` (webhook), movido verbatim de `app.py`
  — `receber_os_mercado_phone()` + `autenticar_integracao_mercado_phone()`, URL efetiva idêntica. Zero
  chave nova em `deps`: `MERCADO_PHONE_WEBHOOK_TOKEN` (`fluxoly_config`) e `importar_os_mercado_phone`/
  `detalhar_os_mercado_phone` (`fluxoly_mercadophone`) importados direto no topo do arquivo, mesmo padrão
  já usado ali para `atualizar_runtime_mercadophone`/`carregar_config_mercadophone`; `mercado_phone_
  runtime_config`/`mercado_phone_helpers` reaproveitados dos já existentes em `deps`. **Único ponto do
  blueprint que não autentica por sessão** — token compartilhado (`hmac.compare_digest`), comentário
  explícito marcando o modelo de auth distinto (decisão do usuário — CTO — de manter no mesmo arquivo por
  ser o mesmo domínio, não bootstrap). Logger próprio (`get_logger("api_mercadophone")`), não injetado via
  `deps`. `ROUTE_PERMISSIONS["receber_os_mercado_phone"]` removida de `app.py` (código morto — bypass por
  `request.path` já a tornava inalcançável). `tests/test_mercadophone_webhook_auth.py`: monkeypatch
  retargetado de `app` para `api_mercadophone` (token agora é global de módulo lá — necessário porque a
  fixture `app` de `conftest.py` é session-scoped e o valor seria capturado em closure se fosse passado
  via `deps`), sem alterar asserts/cenários. `app.py`: 1.923 → 1.749 linhas (bloco do webhook + imports
  órfãos `hmac`/`abort`/`MERCADO_PHONE_WEBHOOK_TOKEN`/`importar_os_mercado_phone`/
  `detalhar_os_mercado_phone` removidos). `app.url_map` idêntico (122 rotas), 683 testes passando, smoke
  test manual com servidor real + token sintético (sem token/errado/correto → 401/401/201), `ruff`/`black`
  limpos, `graphify update .` rodado, CI verde (6/6 checks). **TD-02 encerrada — 4/4 fatias.**
  `app.py`: 2.490 → 1.749 linhas (-30%) desde o início da sprint. Ver
  `docs/operations/SPRINTS/SPRINT_TD02_BOOTSTRAP_APP.md` (Architecture Checkpoint Final) e
  `docs/engineering/API_DEPENDENCY_MATRIX.md`

### Removido (2026-08-08 — TD-18, TD-01 Phase 3 — Cleanup)
- `fluxoly_blueprints_api.py` — monólito residual da TD-01, removido por inteiro. Continha só um
  `Blueprint("api")` vazio (0 rotas registradas) e os dois helpers mortos de KI-032
  (`_slug_estoque`/`_gerar_sku_estoque`, geração de SKU nunca chamada — `api_stock.py` já usa
  `body.get("sku")` direto). Único consumidor (`app.register_blueprint(create_api_blueprint({}))` em
  `fluxoly_blueprint_registry.py`) removido junto, com ~10 comentários históricos da TD-01 que
  documentavam decisões de duplicação de `deps` contra o dict (agora inexistente) de
  `create_api_blueprint` — ficariam órfãos, apontando para código removido. Histórico da TD-01
  preservado sem alteração em ADRs/sprint docs/`API_DEPENDENCY_MATRIX.md` (só um addendum datado
  apontando para o estado atual). Busca final confirmou zero consumidor residual — as únicas menções
  remanescentes são notas de proveniência histórica ("Extraído de `fluxoly_blueprints_api.py`") já
  existentes nos módulos `api_*.py`, legítimas e não tocadas. `app.url_map` idêntico (122 rotas,
  esperado — o blueprint removido nunca teve rota), 683 testes passando, `ruff`/`black` limpos,
  `graphify update .` rodado. KI-032 movida para Resolvidos. Ver `docs/operations/PROJECT_STATUS.md`
  (TD-18)

### Adicionado (2026-08-08 — TD-03 Phase 2, Fatia 1/2: pacote `migrations/`)
- `migrations/` (`registry.py`, `runner.py`, `versions/m0001_baseline.py`) — sistema formal de migrations
  (Opção C aprovada, registry Python, ver `docs/operations/SPRINTS/SPRINT_TD03_MIGRATIONS_FORMAIS.md`).
  `m0001_baseline.py` (698 linhas) é cópia verbatim de `app.py::criar_tabelas()` (24 `CREATE TABLE`, 37
  `ALTER TABLE` aditivos, 22 `CREATE INDEX`, 1 `DROP`+`CREATE INDEX`, 4 blocos de backfill de dados) — não
  colapsada nas colunas finais, para converger corretamente em banco vazio, atrasado, ou já atualizado.
  Confirmado por teste dedicado que o schema gerado bate byte-a-byte (após normalizar espaços) com o
  schema real de `criar_tabelas()`. `runner.py` implementa `schema_migrations`, execução ordenada via
  registry explícito, idempotência, commit por migration, e o mesmo tratamento de "database is locked"
  já usado hoje. **Rede de segurança da Fatia 1 mantida integralmente: `app.py` não foi alterado** —
  `criar_tabelas()`/`SCHEMA_READY`/`SCHEMA_LOCK` continuam sendo o mecanismo real, chamado por
  `conectar()` exatamente como antes; `migrations/` é aditivo e isolado, exercitado só pela própria suíte
  (`tests/test_migrations.py`, 12 testes). Achado da implementação: contrato de migration ajustado de
  `apply(cursor)` para `apply(cursor, conn)` — necessário para preservar o `conn.commit()` intermediário
  do `criar_tabelas()` original entre o DDL e os backfills. 695 testes no total (683 + 12), `ruff`/`black`
  limpos, `graphify update .` rodado, `git diff --stat app.py` confirmado vazio antes do commit, CI verde.
  Fatia 2 (wireing em `app.py` + remoção do mecanismo antigo) fica para depois de validação em produção.

### Removido (2026-08-08 — TD-03 Phase 2, Fatia 2/2 CONCLUÍDA: mecanismo antigo de schema)
- `app.py::criar_tabelas()`/`SCHEMA_READY`/`SCHEMA_LOCK` removidos (695 linhas) — autorizado só após validar
  a Fatia 1 contra um backup real de produção (não sintético): cópias isoladas em três estados
  (`producao-before` intocada, `migration-test` via `run_migrations()`, `legacy-test` via `criar_tabelas()`
  legado), zero divergência de schema, zero divergência de contagem de linhas nas 24 tabelas de dado real,
  idempotência confirmada na segunda execução, original nunca tocado (checksum idêntico do início ao fim).
  Achado real da validação: o backup tinha 25 tabelas, não 24 — `estoque_unidades` (nome legado
  pré-ADR-007) coexistindo com `unidades_serializadas`, confirmando que produção estava de fato "atrasada"
  em relação a `main` — nenhum dos dois mecanismos toca essa tabela órfã, comportamento idêntico. `conectar()`
  vira conexão pura (schema deixa de ser responsabilidade dela); bootstrap de módulo chama `run_migrations()`
  no lugar onde chamava `criar_tabelas()`; `forcar_migracao_schema()` vira wrapper de `run_migrations()`,
  mesmo contrato zero-args — `api_backup.py`/`fluxoly_blueprint_registry.py` não mudaram nenhuma linha.
  `tests/conftest.py`: removida a chamada `_app.criar_tabelas()` (já redundante). `tests/test_migrations.py`:
  `TestEquivalenciaComOMecanismoAntigo` (Fatia 1, comparava contra `criar_tabelas()`) substituído por
  `TestBootstrapDeAppUsaRunMigrations` — a premissa de comparação deixou de existir nesta fatia. Validado
  ponta a ponta: banco vazio → `import app` → `run_migrations()` → app funcional (`schema_migrations`,
  admin padrão, reparos sincronizados, `GET /health` real). 696 testes passando, `ruff`/`black`/`isort`
  limpos, `graphify update .` rodado. Nenhuma limpeza adicional fora do escopo desta fatia. **TD-03
  encerrada — 2/2 fatias. KI-004 resolvido.** Ver
  `docs/operations/SPRINTS/SPRINT_TD03_MIGRATIONS_FORMAIS.md` (Architecture Checkpoint Final)

### Adicionado (2026-08-08 — Financeiro Mínimo, backend: BR-067 a BR-069)
- `migrations/versions/m0002_financeiro_minimo.py` — primeira migration de negócio sobre o mecanismo
  formal da TD-03: tabelas `movimentacoes_caixa`, `contas_pagar`, `contas_receber` e o índice único
  parcial `idx_movimentacoes_caixa_venda_ativa` (guardião de BR-069 no banco).
- `fluxoly_caixa_controller.py`/`_service.py`/`_repository.py` — CRUD de movimentação manual, saldo
  (`SOMA(entradas não estornadas) − SOMA(saídas não estornadas)`), relatório de fluxo de caixa simples, e
  os hooks cursor-based `registrar_entrada_de_venda`/`estornar_entrada_de_venda` usados por Vendas (nunca
  abrem conexão própria — mesma transação do chamador).
- `fluxoly_contas_pagar_*.py` / `fluxoly_contas_receber_*.py` — CRUD, transição de status, baixa lança a
  movimentação de caixa correspondente na mesma transação. Contas a Receber sem qualquer FK ou relação
  com o domínio Vendas (BR-068, isolamento verificado por teste).
- `fluxoly_vendas_service.py::iniciar_venda()`/`cancelar_venda()` — chamam os hooks de caixa antes do
  `conn.commit()`: venda concluída sempre gera entrada, cancelamento sempre estorna, nunca uma transação
  separada (BR-069). Achado da revisão final do plano: precisava seguir o mesmo padrão cursor-based já
  usado para `unidades_service.marcar_como_vendida`/`liberar_unidade_para_venda`.
- `fluxoly_blueprint_registry.py` — registro dos blueprints `/api/caixa`, `/api/contas-pagar`,
  `/api/contas-receber` (gate `admin`/`financeiro`, `usuario_pode_financeiro()`).
- 38 testes novos (`tests/test_caixa.py`, `tests/test_contas_pagar.py`, `tests/test_contas_receber.py`):
  hook de Vendas (criação, idempotência, índice único parcial no banco, cancelamento/estorno, saldo),
  CRUD e baixa de Contas a Pagar/Receber, isolamento de Contas a Receber em relação a Vendas. 734 testes
  no total do projeto, `ruff`/`black`/`isort` limpos, `graphify update .` rodado. QA manual de ponta a
  ponta via requisição HTTP real contra servidor isolado confirmando venda→entrada de caixa,
  cancelamento→estorno, saldo recalculado, e baixa de Contas a Pagar/Receber. Ver
  `docs/engineering/plans/PLAN-financeiro-minimo.md` e `docs/product/BUSINESS_RULES.md` (seção
  Financeiro, BR-067 a BR-069). **Pendente:** tela no frontend, Revisão Arquitetural e Encerramento
  formal (ADR-010).

### Adicionado (2026-08-09 — Financeiro Mínimo, frontend: Fatia 2 + validação Fatia 3)
- `frontend/src/pages/Financeiro.jsx` — tela nova (`/financeiro`, visível só a `admin`/`financeiro`, mesmo
  gate de `usuario_pode_financeiro()`) com três abas: Movimentações (lançamento manual + estorno, filtros
  por tipo/origem/data, paginação), Contas a Pagar e Contas a Receber (CRUD + baixa/cancelamento,
  compartilham o mesmo componente `ContasTab` parametrizado por domínio). Card de saldo no topo,
  recarregado após qualquer mutação. Sem o relatório de fluxo de caixa (`GET /api/caixa/relatorio`) —
  deliberadamente fora do escopo desta fatia (decisão do CTO), fica para uma evolução futura de
  dashboard/relatórios financeiros.
- `frontend/src/api/client.js` — módulos `caixa`/`contasPagar`/`contasReceber`, mesmo padrão de
  `custos`/`vendas` já existentes.
- `frontend/src/components/Layout.jsx`/`App.jsx` — item de navegação e rota `/financeiro`.
- QA manual de ponta a ponta via navegador real (banco isolado, nunca `database.db`): lançar
  entrada/saída manual, estornar, CRUD + pagar/receber/cancelar/excluir de Contas a Pagar/Receber, saldo
  recalculado em cada mutação, filtros, e o gate de perfil confirmado nos dois sentidos (perfil `tecnico`
  bloqueado — some da sidebar e rota direta mostra tela de bloqueio; perfil `financeiro` com acesso pleno).
  Achado durante o QA e corrigido no mesmo ciclo: `ContasTab` não atualizava o contador `total` após
  excluir um item (só removia da lista local) — trocado para refazer a busca paginada (`buscar()`) após
  qualquer exclusão, mesmo padrão das outras mutações da tela.
- Validação formal da integração Vendas ↔ Caixa (Fatia 3, exigida antes da Revisão Arquitetural): venda
  concluída via fluxo real → exatamente uma movimentação `origem='venda'` com `origem_id`/`valor`
  corretos → saldo sobe; cancelamento → `estornada=1`, permanece no histórico, sai do saldo; revenda da
  mesma unidade após cancelamento gera uma nova movimentação distinta sem colidir com a antiga
  (`idx_movimentacoes_caixa_venda_ativa` provado em uso real); dois ciclos completos sem duplicação.
  Suíte automatizada (`tests/test_caixa.py`, `tests/test_contas_pagar.py`, `tests/test_contas_receber.py`,
  38 testes) re-executada e confirmada verde, incluindo os testes de idempotência do hook. Achado
  positivo confirmado no código: `fluxoly_caixa_service.py::estornar_movimentacao_manual` já rejeita
  estornar diretamente qualquer movimentação com `origem != 'manual'` — proteção deliberada contra
  contornar o cancelamento de venda pelo Caixa.
- Corrigido no mesmo ciclo (achado da validação da Fatia 3): botão "Estornar" em `Financeiro.jsx`
  aparecia para qualquer movimentação ativa, inclusive as automáticas (`venda`/`conta_pagar`/
  `conta_receber`), que o backend sempre rejeita com 400 — condicionado agora a
  `!m.estornada && m.origem === "manual"`. Confirmado visualmente: entrada manual continua com o botão,
  entradas automáticas não mostram mais.
- Pendente: Revisão Arquitetural e Encerramento formal (ADR-010) do ciclo do Financeiro Mínimo.

### Adicionado (2026-08-10 — Financeiro Mínimo, Revisão Arquitetural + Encerramento ADR-010)
- Revisão Arquitetural do ciclo (`ADR-010.md` seção "Etapa 6") percorrida contra o código real de `main`
  pós-merge do PR #20: (1) coerência do domínio — confirmado por grep um único caminho de escrita em
  `movimentacoes_caixa`, sem caminhos paralelos; (2) autorização centralizada — `usuario_pode_financeiro()`
  duplicada em 4 controllers, risco já aceito e documentado como TD-14, nada implícito; (3) vazamento de
  dado — as 12 rotas do Financeiro checadas uma a uma, todas protegidas; (4) consistência da máquina de
  estados — achado real (ver `docs/operations/KNOWN_ISSUES.md` KI-034).
- `docs/operations/KNOWN_ISSUES.md` (KI-034) — `fluxoly_vendas_service.py::ajustar_desconto_item()`
  (BR-043, já existente desde V1.3) recalcula `vendas.valor_total` após a venda concluída, mas não
  resincroniza a movimentação de caixa correspondente (`origem='venda'`) — o saldo do Caixa e um estorno
  posterior ficam com o valor original, não o corrigido. Interação nova entre uma regra antiga e o
  Financeiro Mínimo, não uma regressão desta sprint. Decisão do CTO: não bloqueia o Encerramento,
  correção fica para sprint própria, preservando a mesma atomicidade já estabelecida no domínio.
- `docs/engineering/plans/PLAN-financeiro-minimo.md` — marcado como Encerrado; `PROJECT_STATUS.md` —
  Financeiro Mínimo movido de 🟡 para ✅ ENCERRADO;
  `docs/company/RELEASE_1.0_MASTER_CHECKLIST.md` — item "Financeiro mínimo" marcado como entregue.

### Adicionado (2026-08-10 — Operação Release 1.0: Restore de Backup validado)
- `tests/test_backup_restore.py` — 7 cenários cobrindo `POST /api/backup/restaurar`
  (`api_backup.py::restaurar_backup_upload`), que nunca teve teste automatizado: restore de arquivo
  válido altera o banco de fato, backup `pre-restore-*.db` criado com o estado anterior, rejeita
  extensão/header/corrupção sem alterar o banco, 403 sem sessão/sem perfil admin. Fixture de isolamento
  local ao arquivo (não altera `tests/conftest.py` global) preserva o banco real da sessão de pytest via
  `PRAGMA wal_checkpoint(FULL)` + snapshot/restore.
- QA manual de ponta a ponta (11/11 cenários) contra um backend descartável isolado (`IR_FLOW_DATA_DIR`
  próprio, nunca `database.db` de desenvolvimento/produção): ciclo positivo completo e 5 cenários
  negativos, banco original inalterado em todos os casos negativos.
- `docs/company/RELEASE_1.0_MASTER_CHECKLIST.md` — item "Restore validado" (seção Confiabilidade)
  marcado como entregue; visão executiva recalculada (Confiabilidade ~44% → ~66%, geral ~55% → ~59%).
- `docs/operations/PROJECT_STATUS.md` — nova seção "Restore de Backup — validado (Operação Release 1.0)".
- Achado de portabilidade entre builds de SQLite, não bloqueante (`ENGINEERING_GUIDE.md` §11 — nenhum
  critério objetivo de interrupção se aplica): `PRAGMA integrity_check` retorna erro limpo (400) no
  Windows/Python 3.12 local, mas levanta `sqlite3.DatabaseError` direto no runner Linux do CI para o
  mesmo arquivo corrompido — teste ajustado para aceitar os dois desfechos reais, sempre provando que o
  banco original permanece inalterado.
- Achado operacional, registrado para o futuro ambiente de demonstração (não é bug): `IS_SERVER_RUNTIME`
  (ativado por `IR_FLOW_DATA_DIR`) força `SESSION_COOKIE_SECURE=True`, exigindo HTTPS para o cookie de
  sessão ser reenviado.
- Merge via PR #21 (commit `f73f6f86`), CI 6/6 verde. Nenhum código de produção alterado.

### Adicionado (2026-08-10 — Operação Release 1.0: política de Rollback definida)
- `docs/company/GO_LIVE_PLAN.md` (seção "Plano de rollback") e `DEPLOY.md` (nova seção "Rollback") —
  política de rollback coordenado (backend + frontend sempre juntos) decidida pelo CTO, uma pergunta de
  cada vez, seguindo a separação técnico/política/autoridade/procedimento do `CLAUDE.md` §11: critério de
  acionamento (bug crítico impedindo operação, perda/corrupção de dados, ou indisponibilidade
  prolongada), autoridade (só o CTO autoriza, Claude nunca executa sem aprovação explícita), regra de
  interação com migrations (nunca cruza uma migration já aplicada — TD-03 roll-forward only, correção
  nesse caso é sempre hotfix roll-forward), mecanismo (`git revert` + `git push`, não o redeploy nativo
  da plataforma) e verificação (smoke test manual mínimo).
- `docs/company/RELEASE_1.0_MASTER_CHECKLIST.md` — item "Rollback testado" atualizado de ❌ para 🟡
  (política definida e aprovada, nunca exercitada em dry-run real); visão executiva de Operação
  recalculada (~23% → ~30%, geral ~59% → ~61%).
- `docs/operations/PROJECT_STATUS.md` — nova seção "Rollback — política definida (Operação Release 1.0)".
- Nenhum código de produção alterado — decisão de processo/documentação apenas.

### Adicionado (2026-08-10 — Operação Release 1.0: política de conflito em rollback)
- `docs/company/GO_LIVE_PLAN.md` (seção "Plano de rollback") e `DEPLOY.md` (seção "Rollback") — nova
  regra: qualquer conflito durante um `git revert` de rollback de produção é condição de parada, cobrindo
  qualquer tipo de arquivo (código, documentação, testes, configuração, migrations). Proibido resolver
  automaticamente (`--continue`/`--abort`/`--skip`, escolher `ours`/`theirs`, apagar conteúdo, `reset`,
  force-push) — exige informar o CTO e aguardar decisão explícita (resolver de forma controlada, hotfix
  roll-forward, rollback alternativo, ou abortar).
- Motivado por evidência real: Dry-Run 1A (branch `dry-run/rollback-f5fdb23`, preservada) reverteu
  `tests/test_backup_restore.py` (`f5fdb23`) sem conflito, validando o mecanismo isoladamente. Dry-Run 1B,
  com um commit real de produção (`609619f`), reverteu `frontend/src/pages/VendaDetalhe.jsx` limpo mas
  encontrou conflito real em `docs/operations/KNOWN_ISSUES.md` (arquivo append-only, evoluído por commits
  posteriores — KI-029 a KI-034) — a resolução exigiria decisão de conteúdo sobre a entrada do KI-028 e
  sua propagação para outros documentos que a referenciam, não é operação puramente mecânica. `git revert
  --abort` executado, `main`/`origin/main` nunca alteradas em nenhum momento.
- `docs/company/RELEASE_1.0_MASTER_CHECKLIST.md` — item "Rollback testado" atualizado com o registro dos
  dois Dry-Runs e da nova regra; percentual mantido em 40% (política mais robusta, mas rollback ainda não
  testado de ponta a ponta — cálculo justificado no próprio item, sem inflar automaticamente por causa de
  documentação nova).
- `docs/operations/PROJECT_STATUS.md` — seção "Rollback" ampliada com o registro do Dry-Run 1A/1B.
- Nenhum código de produção alterado — decisão de processo/documentação apenas; o revert de
  `VendaDetalhe.jsx` no Dry-Run 1B existiu só na branch temporária, nunca chegou a `main`.

### Adicionado (2026-08-10 — Operação Release 1.0: INC-003, dado real importado no Render PR Preview)
- `docs/operations/INCIDENTS/INC-003-mercadophone-preview-dados-reais.md` — relatório completo do
  incidente encontrado durante o Dry-Run 2A (validação de isolamento do Render PR Preview antes do
  Dry-Run 2B de rollback de infraestrutura): um preview de teste (PR #22) herdou
  `MERCADO_PHONE_SYNC_ENABLED`/`MERCADO_PHONE_API_TOKEN` do serviço-base de produção (comportamento
  documentado do Render) e importou 405 Ordens de Serviço reais da API externa do MercadoPhone em 4
  ciclos de sincronização (~18 minutos), via thread disparada incondicionalmente no boot de `app.py`
  sem checagem de `IS_PULL_REQUEST`. Disco/banco do preview permaneceram fisicamente isolados de
  produção o tempo todo (Service ID, disco e `schema_migrations` próprios) — o problema foi herança de
  credenciais de integração externa, não vazamento de disco. Busca exaustiva por call sites de
  `chamar_api_mercado_phone()` confirma só 2 usos no código, ambos de leitura — nenhuma evidência de
  escrita de volta ao MercadoPhone. KI-035 (condição de corrida em migrations) foi reproduzido de forma
  independente no primeiro boot deste mesmo preview.
- Contenção: preview suspenso via painel Render (confirmado por evento + URL pública), PR #22 mantida
  aberta para preservar evidência, nenhum dado apagado, produção confirmada intocada (`/health` → `ok`
  antes e depois).
- `docs/operations/PROJECT_STATUS.md` — nova seção "INC-003", linha de sequência do topo atualizada.
- **Dry-Run 2B (rollback de infraestrutura) bloqueado** por dois achados independentes: INC-003
  (integrações externas herdadas em preview) e KI-035 (condição de corrida em migrations).
- Nenhum código alterado — só documentação e uma ação de contenção operacional (suspensão do preview).

### Corrigido (2026-08-11 — Preview Seguro: INC-003 Frente B, KI-035, KI-036)
- `fluxoly_config.py` — nova constante `IS_PULL_REQUEST` (setada automaticamente pelo Render em todo PR
  Preview); `BACKGROUND_JOBS_ENABLED` passa a incorporar `and not IS_PULL_REQUEST`, desligando
  incondicionalmente a sync automática do MercadoPhone e o backup automático em qualquer preview, mesmo
  com credenciais/flags herdadas do serviço-base (INC-003 Frente B).
- `app.py` — log estruturado `preview_background_jobs_desativados` no boot quando `IS_PULL_REQUEST` é
  detectado; `environment` do Sentry passa a distinguir `"preview"` de `"production"`/`"development"`
  (antes, `IS_SERVER_RUNTIME` sozinha marcava qualquer preview como produção — KI-036).
- `migrations/runner.py::run_migrations()` — `sqlite3.IntegrityError` capturado por migration (não pela
  função inteira), tratado como no-op **só** quando a mensagem confirma a constraint
  `schema_migrations.id` (corrida entre workers); qualquer outro `IntegrityError` continua propagando, sem
  mascarar falha real de dado (KI-035, condição de corrida reproduzida 2× em produção e no preview do
  INC-003).
- Testes novos: `tests/test_ambiente_preview.py` (8 casos, subprocesso isolado) e +2 casos em
  `tests/test_migrations.py` (regressão do KI-035, confirmada falhando contra o código anterior). 751
  testes existentes + 10 novos, todos passando; `ruff check .` limpo.
- QA manual (backend real, banco/disco descartáveis, nunca `database.db`) e Revisão Arquitetural (4 eixos
  do `ADR-010`) concluídas — achado residual fora do escopo aprovado (endpoints manuais de
  `api_mercadophone.py` ainda alcançáveis por sessão `admin`/`tecnico` real dentro de um preview, sem
  checagem de `IS_PULL_REQUEST`) registrado como **KI-037**, decisão do CTO de não expandir o escopo agora.
- `docs/operations/KNOWN_ISSUES.md` — KI-035 e KI-036 movidos para Resolvidos; KI-037 registrado.
- `docs/operations/INCIDENTS/INC-003-mercadophone-preview-dados-reais.md` — status atualizado para
  Resolvido (nova seção 12).
- `DEPLOY.md`/`docs/company/GO_LIVE_PLAN.md` — nova seção "Preview Seguro" documentando a defesa em
  profundidade (guard de código + configuração).
- Ver `docs/engineering/plans/PLAN-preview-seguro-inc003-ki035.md` para o plano técnico completo.
- Reativar o preview suspenso ou autorizar o Dry-Run 2B continuam sendo decisões separadas do CTO, não
  automáticas por esta correção.

### Corrigido (2026-08-08 — modernização isolada, achado durante o Financeiro Mínimo)
- `fluxoly_vendas_service.py` — `isinstance(x, (int, float))` substituído por `isinstance(x, int | float)`
  (UP038): o hook local de pre-commit (`ruff-pre-commit` pinado em v0.5.0) ainda sinaliza essa regra,
  removida do ruff moderno (0.16.x, usado localmente e no CI) e por isso nunca aparecia no
  `ruff check .`. Correção mecânica isolada, sem mudança de comportamento, commitada separadamente do
  Financeiro Mínimo para não misturar cleanup com feature nova.

### Corrigido (2026-08-05 — INC-001, causa raiz confirmada em produção)
- `fluxoly_mercadophone.py::_sincronizar_mercado_phone_sem_lock()` mantinha uma única transação de
  escrita aberta durante todo o loop de sincronização (até centenas de registros, cada um com uma
  chamada HTTP síncrona para a API externa do Mercado Phone), só comitando no final — qualquer outro
  escritor (ex.: `POST /api/auth/login`) esperava o `busy_timeout` inteiro (30s) e falhava com
  "database is locked" enquanto o ciclo estivesse em andamento. Confirmado em produção pelo usuário
  (CTO) tentando logar como admin: dois logins falharam com 400, cada um levando ~30.2s, exatamente
  coincidindo com logs de `mercadophone_sync_falha_inesperada` na mesma janela (`OperationalError:
  database is locked`, incluindo uma falha dupla — exceção durante o `finally` de liberação do lock).
  Corrigido movendo o commit para dentro do loop (`finally` por registro), preservando a atomicidade de
  cada registro (já isolado pelo `try/except` existente) enquanto libera o lock entre uma chamada
  externa e a próxima. Novo teste (`tests/test_inc001_mercadophone_commit_por_registro.py`) prova o
  mecanismo exato — confirmado que falha contra o código anterior à correção e passa depois (mesmo
  rigor dos hotfixes anteriores deste incidente). 683 testes no total, `ruff check .` limpo. Ver
  `docs/operations/INCIDENTS/INC-001-database-is-locked.md` para o relatório completo

### Adicionado (2026-08-12 — Ambiente de Demonstração/Homologação: Implementação, Testes, QA Manual, Revisão Arquitetural, Encerramento)
- `docs/engineering/adr/ADR-012.md` (2026-08-11) — arquitetura do Ambiente de Demonstração: serviço Render
  dedicado + projeto Vercel dedicado, nova flag `IR_FLOW_ENVIRONMENT=demo`, KI-037 promovido a bloqueante
  para acesso externo, isolamento de credenciais por design (lição do INC-003). `docs/engineering/plans/
  PLAN-ambiente-demo-homologacao.md` (2026-08-11) — plano técnico aprovado pelo CTO com 3 ajustes de
  escopo.
- `fluxoly_config.py` — `IR_FLOW_ENVIRONMENT`/`IS_DEMO_ENVIRONMENT`, coexistindo com `IS_PULL_REQUEST` sem
  substituí-lo (Preview mantém precedência); `integracao_externa_bloqueada_neste_ambiente()` como ponto
  único de verdade do guard do **KI-037**.
- `api_mercadophone.py` — guard do KI-037 aplicado nos 4 endpoints de escrita/ação
  (`sincronizar`/`reprocessar`/`reimportar`/`config`), inserido depois das checagens de permissão já
  existentes, sem alterá-las; `status_mercadophone` (leitura) permanece intocado.
- `app.py` — log de boot `demo_background_jobs_desativados`; `environment="demo"` no Sentry, com Preview
  mantendo precedência quando as duas flags estão setadas juntas.
- `scripts/seed_demo.py` — seed sintético standalone: "loja modelo" 100% fictícia (18 clientes, 10
  produtos/unidades, 24 OS, 8 vendas com caixa) e as 3 contas de demonstração
  (`admin.demo`/`tecnico.demo`/`vendedor.demo`), senhas só via variável de ambiente sem default (lição do
  KI-029), guard de idempotência contra banco já populado.
- `tests/test_ambiente_demo.py`, `tests/test_ki037_guard_integracoes.py` — 20 testes novos. CI 6/6 verde
  no Linux (branch `feat/ambiente-demo-homologacao`, commits `59597bd8`/`a14db05e`).
- QA manual de ponta a ponta contra backend Flask real e descartável (nunca `database.db`): guard do
  KI-037 nos 4 endpoints em Demo, regressão zero em produção/dev, login real das 3 contas, reset/restore
  (backup `seed-inicial` → mutação → restore), CORS explícito sem fallback permissivo.
- Revisão Arquitetural (4 eixos do `ADR-010`) concluída sem inconsistência não documentada — achado
  documental (não código): `MERCADO_PHONE_WEBHOOK_TOKEN` ausente do Runbook de Provisionamento,
  adicionado à tabela (já fail-secure por design quando ausente, KI-023).
- `docs/operations/KNOWN_ISSUES.md` — **KI-037 movido para Resolvidos**; **KI-038 registrado** (aberto):
  `criar_admin_padrao()` cria uma 4ª conta `admin`/`irflow@2024` padrão sempre que `usuarios` está vazia
  — comportamento pré-existente (também em produção), fora do escopo deste plano, pendência real antes de
  qualquer acesso externo ao Demo.
- Ciclo `ADR-010` completo (Discovery → ADR → Plano Técnico → Implementação → Testes → QA Manual →
  Revisão Arquitetural → Encerramento). Ainda não autorizados: PR/merge em `main`, provisionamento real
  Render/Vercel, homologação externa (14 critérios do Definition of Done do `ADR-012`).

### Corrigido (2026-08-13 — hotfix/usuarios-senha-nao-persiste, KI-039)
- `PUT /api/usuarios/<id>` espera `senha_nova` para trocar a senha; a tela de Usuários
  (`frontend/src/pages/Users.jsx`) sempre enviava `senha` — mesmo campo do `POST /api/usuarios` de
  criação. Resultado: trocar a senha de qualquer usuário pela tela de edição era silenciosamente
  ignorado pelo backend, que respondia sucesso mesmo assim. Achado durante a Discovery do KI-038, ao
  tentar trocar a senha da conta `admin` de produção como mitigação imediata da credencial hardcoded
  exposta. Correção mínima, um arquivo (payload do caminho de edição passa a usar `senha_nova`; criação
  inalterada). `pytest tests/test_users.py` 22/22, lint/build limpos, CI 6/6 verde. PR #25, commit
  `ba2d6294`, merge `ccf94baa`, hotfix a partir de `main` (KI-039)

### Adicionado (2026-08-13 — feat/ki-038-admin-senha-configuravel, KI-038, ciclo ADR-010 completo)
- `app.py::criar_admin_padrao()` deixa de usar a senha fixa `irflow@2024` em qualquer ambiente que se
  pareça com servidor real. Passa a exigir `IR_FLOW_ADMIN_PASSWORD` fora de dev local
  (`IS_SERVER_RUNTIME`) — mesmo padrão já usado para `FLASK_SECRET_KEY` (`SECURITY_AUDIT_2026-07.md` item
  3): ausente nesse caso, o boot falha com erro claro em vez de criar um admin com senha conhecida. Em dev
  local mantém o fallback histórico, documentado em `.env.example`, sem quebrar onboarding. Produção atual
  não é afetada (admin já existe, senha já trocada manualmente pelo CTO — KI-039); o guard passa a valer
  para o próximo ambiente que subir com banco vazio (Demo, `ADR-012`). Achado registrado durante a Revisão
  Arquitetural, não um bug: `scripts/seed_demo.py` herda o mesmo `criar_admin_padrao()` — o Runbook de
  Provisionamento do Demo vai precisar de `IR_FLOW_ADMIN_PASSWORD` além de `DEMO_SEED_ADMIN_PASSWORD`. 3
  testes novos (`tests/test_ki038_admin_senha_configuravel.py`), suíte completa 751/754 (3 falhas
  pré-existentes de ambiente Windows, confirmadas via `git stash` — não é regressão), `black`/`ruff`
  limpos, CI 6/6 verde. Ciclo `ADR-010` completo (Discovery → decisão arquitetural → Plano Técnico →
  Implementação → Testes → Revisão Arquitetural → Encerramento). Ver
  `docs/engineering/plans/PLAN-ki038-admin-senha-configuravel.md`. PR #26, commit `303c05c3` (KI-038)

---

## [1.1.0] — 2026-06-21

### Adicionado
- Módulo de lista de compras (`shopping_list`): tabela no banco, API REST completa com workflow de status (PENDENTE → EM_COTACAO → EM_COMPRA → COMPRADO → RECEBIDO)
- Endpoint `GET /api/precos/sugerir`: retorna preço total sugerido com base em modelo + reparos selecionados
- Página `Compras.jsx` no frontend com listagem e gestão da lista de compras
- `EditShoppingItemModal`: modal de edição de itens da lista de compras
- `ShoppingModal`: modal de adição de novos itens
- Client dedicado `shoppingList` em `frontend/src/api/client.js`
- Logs de atividade por item de shopping list com exportação

### Corrigido
- `valor_cobrado` agora é auto-preenchido ao selecionar modelo + reparo em nova OS
- `valor_cobrado` não sobrescreve valor existente ao abrir OS para edição (flag `initialized.current`)
- URL do endpoint de PDF IR Phones corrigida (`/irphones` → `/ir-phones`)
- Rota `historico-cliente` apontava para endpoint inexistente em `client.js`
- Campo `cor` agora é limpo ao trocar modelo em `EditOrder.jsx`
- Pipeline de build/dist do frontend corrigido

### Segurança
- Arquivo `.env` removido do repositório (credenciais não mais expostas no histórico git)

---

## [1.0.0] — 2026-05-01

### Adicionado
- Sistema completo de gestão de Ordens de Serviço (OS): criação, edição, exclusão, histórico
- Controle de estoque com movimentações por lotes e SKU
- Tabela de preços por modelo e tipo de reparo
- Kanban board para visualização de OS por status
- Checklist público de dispositivo com token (sem autenticação)
- Rastreamento de garantias com contagem de dias restantes
- Relatórios: IR Phones, Técnicos, Custos Operacionais
- Exportação de relatórios em PDF
- Backup manual e automático com notificação por e-mail
- Integração Google Drive para armazenamento de backups
- Integração MercadoPhone para importação de OS externas
- Gestão de usuários com perfis: admin, vendedor, técnico
- Autenticação via sessão com hash de senha (Werkzeug)
- Deploy em Fly.io com Dockerfile e configuração de produção
- Suporte a build para executável Windows (PyInstaller + InnoSetup)
- CORS configurado para deploy separado frontend/backend

---

## Guia de Versões

| Versão | Sprint | Status |
|--------|--------|--------|
| 1.2.0 (futura) | Sprint 2 | Infraestrutura de qualidade |
| 1.3.0 (futura) | Sprint 3 | Segurança e observabilidade |
| 2.0.0 (futura) | Sprint 4-5 | Refatoração arquitetural |
| 1.1.0 | Sprint 1 | Lançado |
| 1.0.0 | Sprint 0 | Lançado |

---

*Para mudanças em andamento, consulte [`docs/operations/SPRINTS/`](SPRINTS/) e [`docs/operations/PROJECT_STATUS.md`](PROJECT_STATUS.md).*
