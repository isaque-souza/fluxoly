# PRODUCT_BACKLOG.md — Fila de Evolução do Produto

Diferente de `docs/operations/ROADMAP.md` (que responde **quando** — fases e sprints de engenharia) e de
`docs/company/RELEASE_STRATEGY.md` (que responde **em qual versão** cada coisa sai), este documento
responde **o quê** construir a seguir, em ordem de prioridade de negócio.

**Última revisão:** 2026-11-11 (coluna Status verificada contra o código; prioridades inalteradas)
**Fonte:** priorização de negócio — input direto do Product Owner. Coluna "Status" verificada contra o
estado real do código/documentação (`docs/engineering/DOMAIN_MODEL.md`, `docs/product/features/`) antes
de publicar, não copiada às cegas do exemplo dado.

---

## Fila Priorizada

Coluna **Item do Release 1.0** referencia `docs/company/RELEASE_1.0_MASTER_CHECKLIST.md` (adicionada em
2026-07-25) — todo épico que avança a Release 1.0 deveria apontar para o item de checklist que ele
ajuda a marcar.

| Prioridade | Épico | Status | Valor de Negócio | Item do Release 1.0 | Fonte / Nota |
|---|---|---|---|---|---|
| P0 | Vendas | Em produção com tela (`Vendas.jsx`/`VendaDetalhe.jsx`) — MVP 2026-07-27 (1 aparelho por venda) + V1.2 Cancelamento, V1.3 Descontos, V1.4 Comissão, V1.5 Garantia (2026-07-27 a 2026-07-30). Falta troca/avaliação de usado e reserva de IMEI (`docs/product/features/VENDAS.md`) | Muito Alto | Comercial completo | Prioridade #1 do produto — ver `VENDAS.md` "Por que existe". Fluxo completo condicionado a decisões do Product Owner ainda pendentes (timeout de reserva, % comissão, limite de desconto, prazo de garantia, critérios de avaliação de usado) |
| P0 | Clientes (entidade própria) | Implementado com tela — `fluxoly_clientes_*.py` (2026-07-11, Sprint P0.1) + `frontend/src/pages/Clientes.jsx` (`/clientes`); perfil ainda sem compras (KI-062) | Muito Alto | Comercial completo | Pré-requisito estrutural de Vendas, entregue como fundação antes do módulo em si (`docs/engineering/DOMAIN_MODEL.md` seção 1.12). Tela `/clientes` desde então (cadastro, busca, perfil com OS e garantias). Decisões de negócio pendentes (deduplicação) seguem `TODO`, ver `CLIENTES.md` |
| P0 | IMEI Individual | Implementado com tela — `fluxoly_unidades_serializadas_*.py` (2026-07-11, Sprint P0.1, evoluído de `estoque_unidades` na migração ADR-007, 2026-07-21) + `UnidadesSerializadas.jsx` (`/unidades-serializadas`) | Muito Alto | Comercial completo | Gap de schema resolvido — `docs/engineering/DOMAIN_MODEL.md` seção 1.13. Com tela; `vendido` é marcado pela venda (`marcar_vendida`, mesma transação de `iniciar_venda`), `reservado` segue não implementado. Decisões de negócio pendentes (validação de formato, AirPods/série) seguem `TODO`, ver `IMEI.md` |
| P0 | Produtos (catálogo comercial) | Implementado com tela — `fluxoly_produtos_*.py` (2026-07-20, Sprint Comercial 0.1) + `Produtos.jsx` (`/produtos`) | Muito Alto | Comercial completo | Lacuna real identificada só agora: nenhum documento desenhava um catálogo comercial (categoria/marca/cor/capacidade/condição/preço) antes desta sprint — `estoque` é peça de reparo, não produto de venda. Domínio novo, separado de Estoque. Com tela; rastreamento por unidade/IMEI de produtos entregue via `unidades_serializadas.produto_id` (migração ADR-007, 2026-07-21) |
| P1 | Financeiro (mínimo) | Entregue — 2026-08-10 (BR-067 a BR-069, ciclo ADR-010 encerrado): caixa, contas a pagar/receber, `Financeiro.jsx` (`/financeiro`); item marcado em `RELEASE_1.0_MASTER_CHECKLIST.md` | Alto | Financeiro mínimo | Escopo restrito a caixa/entradas/saídas/contas a pagar-receber (`RELEASE_STRATEGY.md`, 2026-07-25) — "Financeiro avançado" (DRE, conciliação, indicadores) fica fora da 1.0 |
| P1 | Caixa | Entregue — 2026-08-10, junto com Financeiro mínimo (`movimentacoes_caixa`, `/api/caixa`); recebimento de OS no caixa ainda não existe (origem `os` ausente) | Alto | Financeiro mínimo | Mesmo item de checklist que Financeiro mínimo — são o mesmo trabalho, não dois épicos separados |
| P1 | Dashboard Executivo | Parcial | Alto | Dashboard Executivo | **Nota de verificação:** já existe um dashboard básico (`frontend/src/pages/Dashboard.jsx`, KPIs de faturamento/lucro/serviços/técnico) — o que falta é a versão executiva completa descrita na visão original (ticket médio, OS atrasadas, top vendedores, margem) |
| P2 | WhatsApp | Não iniciado | Médio | Fase 4 (Automação) — fora do escopo da 1.0 | Notificação automática de status de OS/venda — pilar "Relacionamento", `BRAND_IDENTITY.md` seção 2 |
| P2 | CRM | Não iniciado | Médio | Fase 4 (Automação) — fora do escopo da 1.0 | Depende de Clientes (P0) existir como entidade primeiro |
| P3 | Multiempresa | ADR pendente | Estratégico | Fase 3 (Multiempresa) — fora do escopo da 1.0, depende da Fase 2 (Infraestrutura SaaS) | `docs/engineering/adr/ADR-005.md` — alternativas técnicas prontas, decisão de negócio ainda não tomada |
| P3 | UX-001 — Preservação de Contexto da Navegação | Em andamento — piloto validado (Orders + Histórico de Vendas) | Médio (usabilidade, não bloqueia receita) | Fora do escopo da 1.0 | Proposto em 2026-07-30 durante revisão da V1.5 (Garantia); piloto implementado e validado em navegador real no mesmo dia. Mecanismo reutilizável (`frontend/src/hooks/useListContext.js`) de preservação de contexto de navegação para listagens — restaura posição de rolagem, paginação, filtros, pesquisa e registro em foco (com destaque temporário) ao retornar de uma tela de visualização/edição/criação, consumindo o snapshot uma única vez (`clearListContext`) para não "grudar" em visitas futuras não relacionadas. Validado ponta a ponta (Chrome real via Claude in Chrome) em `Orders.jsx` e `Vendas.jsx`/Histórico — as duas páginas piloto escolhidas deliberadamente para reduzir risco antes de expandir. **Pendente para concluir**: aplicar o mesmo hook a Clientes, Produtos, Estoque, Compras, Garantias, Unidades Serializadas e futuras listagens; hoje o hook só cobre o clique em "Editar" — ampliar para visualizar/criar/qualquer navegação temporária; considerar evoluir a chave fixa (`"ordens"`, `"vendas-historico"`) para um padrão `módulo:contexto` (ou derivado do `pathname`) que dispense escolher uma string por página. Decisão deliberada de não competir com o roadmap funcional em andamento (Vendas → Financeiro → CRM) — retomar a expansão só depois das prioridades P0/P1 acima |

---

## Proposta — candidatos do benchmark Mercado Phone (2026-11-11)

> **Status: proposta, decisão pendente do PO.** Nada abaixo entra na Fila Priorizada até o Product Owner
> aprovar. Prioridade, esforço e ordem são **sugestões** derivadas do walkthrough somente leitura em
> `docs/product/research/BENCHMARKS/MERCADO_PHONE.md` (todos os módulos, 2026-11-11) cruzado com o código
> atual — cada linha aponta para a seção do benchmark onde está a evidência.

**Critério usado:** (1) o que avança um item aberto do `RELEASE_1.0_MASTER_CHECKLIST.md`; (2) uso real
observado na conta da loja (recurso que ela usa pesa mais do que recurso que só existe); (3) esforço —
preferência por o que só lê dados que a Fluxoly já grava; (4) dependências.

**Achado transversal:** "formas de pagamento cadastradas (com taxa e prazo) + vários pagamentos por
operação" aparece como pré-requisito em Vendas, OS, Financeiro e Relatórios. Destrava pagamento na OS e
recebimento no caixa, venda PIX + cartão, troca abatendo do valor e lucro líquido de taxa. Por isso está
como fundação, não como item isolado.

### Onda 1 — ganhos rápidos sobre dados que já existem (sem mudança de schema)

| # | Candidato | Prioridade sugerida | Esforço | Item Release 1.0 | Evidência (seção do benchmark) / nota |
|---|---|---|---|---|---|
| 1 | Corrigir **KI-062**: compras no perfil do cliente e comprador na unidade | P0 | Baixo | Comercial completo | Clientes e Relatórios — dado já gravado em `vendas.cliente_id` |
| 2 | **Tela de auditoria** sobre `audit_log` (filtros, antes/depois) | P1 | Baixo | Configurações / Segurança | Garantia, Checklist e Auditoria — log já gravado em quase todos os domínios, sem tela |
| 3 | **Painel de garantias unificado** (vendas + OS, dias restantes, vencidas) | P1 | Baixo/médio | Assistência completa | Garantia, Checklist e Auditoria — página Garantias hoje só mostra OS |
| 4 | **Dashboard somando vendas + OS** (faturamento, lucro, ticket médio, top vendedores) | P1 | Médio | Dashboard Executivo | Clientes e Relatórios; Tela inicial — hoje o Dashboard calcula só sobre OS |
| 5 | **Alertas de dados**: venda abaixo do custo, unidade sem custo | P1 | Baixo | Comercial completo | Clientes e Relatórios — protege margem; custo por aparelho já existe (BR-092) |
| 6 | **Pendências na tela inicial**: contas vencendo hoje/vencidas, estoque abaixo do mínimo, IMEI duplicado | P2 | Baixo | Dashboard Executivo | Tela inicial e Configurações; Financeiro (indicadores vencidos) |
| 7 | **Dias em estoque** na lista de unidades | P2 | Baixo | Comercial completo | Compras / Estoque |
| 8 | **Esconder lucro/custo do perfil vendedor** e limitar às próprias vendas | P2 | Baixo/médio | Segurança | Tela inicial e Configurações — mexe em autorização: plano obrigatório (CLAUDE.md) |

### Onda 2 — fundação estrutural (schema, plano aprovado obrigatório)

| # | Candidato | Prioridade sugerida | Esforço | Item Release 1.0 | Evidência / nota |
|---|---|---|---|---|---|
| 9 | **Formas de pagamento cadastradas + vários pagamentos por operação** | P0 | Alto | Comercial completo / Financeiro | Vendas, Financeiro — fundação dos itens 10-12 |
| 10 | **Recebimento da OS no caixa** (origem `os`, parcial/saldo) | P0 | Médio | Assistência completa / Financeiro | OS, Financeiro — hoje o dinheiro da assistência não aparece no caixa |
| 11 | **Troca/upgrade completo** (usado abate do valor, entra no estoque) | P1 | Médio | Comercial completo | Vendas, Compras / Estoque — já existe em parte (`compras_aparelhos` origem troca); decisões pendentes em `VENDAS.md` |
| 12 | **Lucro líquido de taxa** por venda | P2 | Baixo (após 9) | Dashboard Executivo | Clientes e Relatórios |
| 13 | **Data de previsão da OS + destaque de atrasada** | P1 | Médio | Dashboard Executivo ("OS atrasadas") | OS — `os` não tem data de previsão hoje |
| 14 | **Relato do cliente / laudo / observação interna** na OS | P2 | Médio | Assistência completa | OS |
| 15 | **Autorização de gerente na operação** (cancelar, desconto acima do limite, excluir), registrada no `audit_log` | P2 | Médio | Segurança | Tela inicial e Configurações — depende do item 2 para consulta |

### Onda 3 — relacionamento e recompra (versão simples, sem API paga)

| # | Candidato | Prioridade sugerida | Esforço | Item Release 1.0 | Evidência / nota |
|---|---|---|---|---|---|
| 16 | **Lembretes de pós-venda e upgrade** (lista diária 7/30/365 dias + botão `wa.me`) | P2 | Médio | Fora da 1.0 (Fase 4 — WhatsApp/CRM) | Ferramentas e Marketplace — recurso mais usado da conta; depende do item 1 |
| 17 | **Origem e "indicado por" na venda** | P2 | Baixo | Fora da 1.0 | Vendas, Ferramentas — a loja preenche na venda, não no cliente |
| 18 | **Aniversário do cliente + aniversariantes** | P3 | Baixo | Fora da 1.0 | Clientes e Relatórios |
| 19 | **Recibo de venda** (impressão A4/80 mm, envio por WhatsApp) | P1 | Médio | Comercial completo | Vendas; Tela inicial e Configurações — botão "Imprimir" é placeholder (V1.8) |

### Onda 4 — decisões antes de código

| # | Candidato | Nota |
|---|---|---|
| 20 | **Fiscal: emitir ou integrar com emissor externo** | Fiscal — decisão de estratégia (Fase 3 em `RELEASE_STRATEGY.md`); se emitir, começar pela NFC-e da venda |
| 21 | Checklist configurável pela loja | Garantia, Checklist e Auditoria — muda `os_checklists` |
| 22 | Situações de OS configuráveis (Orçamento → Aprovado) | OS; Tela inicial e Configurações — muda máquina de estados |
| 23 | Consulta de IMEI em base de bloqueio/roubo; termo de compra do usado | Compras / Estoque; Garantia — depende de provedor externo pago (custo, contrato, LGPD) |
| 24 | Custos extras na unidade, etiqueta com código de barras, IMEI 2 | Compras / Estoque |
| 25 | Despesas recorrentes, contas bancárias, caixa por sessão | Financeiro — caixa por sessão só se a loja for de fato fechar caixa (na conta observada, a maioria nunca fecha) |

### Sugerido não implementar

Catálogo de dezenas de relatórios sobrepostos; banners de terceiros; horário de acesso; perfis ×
módulos duplicados; aplicação retroativa de termos; catálogo online, score de crédito, assinatura
eletrônica, carteira pré-paga e gerador por IA (baixo ou nenhum uso observado); DRE/conciliação/integração
bancária e multi-loja (fora da 1.0 por `RELEASE_STRATEGY.md`).

### Observação sobre a Fila Priorizada

As colunas "Status" da fila foram verificadas contra o código em 2026-11-11 (Vendas, Clientes, IMEI,
Produtos, Financeiro mínimo e Caixa estavam desatualizadas). Também foram corrigidas as menções factuais "Sem tela" na coluna Fonte / Nota;
prioridades e o restante das notas do PO ficaram como estavam.

---

## Como usar este documento

- **Prioridade (P0–P3)** é ordem de importância de negócio, não ordem de implementação necessariamente —
  dependências técnicas podem exigir sequenciar diferente (ex.: Clientes e IMEI são P0 mas são
  pré-requisitos de Vendas, também P0; não faz sentido implementar Vendas sem eles).
- **Status** reflete o estado real verificado, não a intenção. Atualizar aqui sempre que um épico mudar
  de fase — este documento fica desatualizado rápido se não for mantido junto com
  `docs/operations/PROJECT_STATUS.md`.
- Ao mover um épico de "Não iniciado" para "Especificação", criar o spec em
  `docs/product/features/<EPICO>.md` seguindo o formato de `VENDAS.md`.
- Toda decisão de priorização relevante (por que P0 e não P1) deveria ter uma entrada correspondente em
  `docs/company/DECISION_LOG.md` quando a razão não for óbvia.

---

## Documentos relacionados

- `docs/company/RELEASE_STRATEGY.md` — em qual versão cada épico deste backlog é planejado para sair
- `docs/company/RELEASE_1.0_MASTER_CHECKLIST.md` — checklist de certificação da Release 1.0; cada épico
  P0/P1 acima referencia o item que ajuda a marcar
- `docs/operations/ROADMAP.md` — roadmap de engenharia (fases/sprints técnicas, eixo separado, hoje
  desatualizado — ver aviso no topo daquele documento)
- `docs/company/DECISION_LOG.md` — decisões que justificam prioridade/sequenciamento acima
- `docs/product/features/VENDAS.md`, `CLIENTES.md`, `IMEI.md` — os três épicos P0 com spec hoje (2026-07-11)
- `docs/engineering/adr/ADR-005.md` — decisão pendente que bloqueia Multiempresa
