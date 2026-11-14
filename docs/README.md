# Documentação — Fluxoly Platform

Bem-vindo à documentação da Fluxoly (nome legado no código e infraestrutura: Assistência System — ver
`company/BRAND_IDENTITY.md` seção 9 para o cronograma de transição de marca).
Se você não sabe por onde começar, siga a ordem abaixo.

`docs/` é organizado por audiência, não por ordem alfabética — ver `engineering/adr/ADR-006.md` para o
critério de cada pasta.

**Regra de governança (2026-07-10, Product Owner):** nenhum documento novo é criado sem responder
primeiro "que decisão ele ajuda a tomar?". Documentação existe para decidir o que fazer, não para
registrar volume — se a resposta a essa pergunta não é clara, o documento provavelmente não deveria
existir ainda.

**Backlog de documentação identificada, ainda não criada:**
- `company/UX_GUIDELINES.md` — consolidar princípios de interface (ex.: interface por perfil, hoje
  duplicado entre `company/VISION.md` e `engineering/ENGINEERING_GUIDE.md` §4.0) em um único lugar.
- `product/features/FEATURE_SPEC_FINANCEIRO.md`, `product/features/FEATURE_SPEC_ESTOQUE.md` — specs no
  formato de `product/features/VENDAS.md`, quando esses módulos começarem a ser especificados.
- Personas Operacionais completas (Técnico, Financeiro, Estoque, Administrador) — ver TODOs dentro de
  `company/PRODUCT_REQUIREMENTS.md` seção "Personas Operacionais".

---

## Começando

Leia nesta ordem:

1. [`../CLAUDE.md`](../CLAUDE.md) — Manual operacional para IA. Define o protocolo de trabalho, regras e filosofia do projeto.
2. [`company/BRAND_IDENTITY.md`](company/BRAND_IDENTITY.md) — Identidade e Constituição da Marca Fluxoly.
3. [`engineering/ENGINEERING_GUIDE.md`](engineering/ENGINEERING_GUIDE.md) — Constituição técnica. Padrões, convenções e arquitetura. Leia uma vez e consulte sempre.
4. [`operations/PROJECT_STATUS.md`](operations/PROJECT_STATUS.md) — Estado atual do projeto. Sprint em andamento, score, bugs abertos.

---

## `company/` — Identidade e Negócio

Decisões de marca, produto e mercado — do Product Owner, não da engenharia:

- [`company/BRAND_IDENTITY.md`](company/BRAND_IDENTITY.md) — Nome, pilares, escopo negativo, promessa, visão 2030.
- [`company/VISION.md`](company/VISION.md) — Missão, visão, valores, critérios de sucesso.
- [`company/PRODUCT_REQUIREMENTS.md`](company/PRODUCT_REQUIREMENTS.md) — Persona (Cliente) e Personas Operacionais (Usuários), mercado-alvo, monetização (parcialmente `TODO`).
- [`company/OPERATION_SYSTEM.md`](company/OPERATION_SYSTEM.md) — Como a loja funciona, ciclo completo (Fornecedor ao Pós-venda); a maioria dos blocos ainda `TODO`.
- [`company/DECISION_LOG.md`](company/DECISION_LOG.md) — Histórico executivo de decisões de produto (distinto de ADR).
- [`company/NON_FUNCTIONAL_REQUIREMENTS.md`](company/NON_FUNCTIONAL_REQUIREMENTS.md) — Capacidade, desempenho, disponibilidade, backup — formulário, majoritariamente `TODO`.
- [`company/RELEASE_STRATEGY.md`](company/RELEASE_STRATEGY.md) — Versionamento decidido (0.8 a 2.0) e as 6 Fases estratégicas de longo prazo (Estabilização → Release 1.0 → Infraestrutura SaaS → Multiempresa → Automação → Inteligência).
- [`company/RELEASE_1.0_MASTER_CHECKLIST.md`](company/RELEASE_1.0_MASTER_CHECKLIST.md) — Checklist de certificação: o que precisa estar `[x]` antes do primeiro cliente pagante.
- [`company/GO_LIVE_PLAN.md`](company/GO_LIVE_PLAN.md) — Plano de execução para colocar o primeiro cliente em produção (diferente do checklist: "como fazemos", não "estamos prontos").
- [`company/CUSTOMER_FEEDBACK.md`](company/CUSTOMER_FEEDBACK.md) — Log de feedback de clientes (Cliente → Pedido → Discussão → Decisão → Sprint); evidência que orienta o backlog funcional.

---

## `product/` — Pesquisa e Planejamento de Produto

- [`product/PRODUCT_GLOSSARY.md`](product/PRODUCT_GLOSSARY.md) — Glossário de termos (Produto, Estoque, Unidade Serializada, Venda, Reserva, etc.), extraído do código real, não aspiracional.
- [`product/FEATURE_MATRIX_TEMPLATE.md`](product/FEATURE_MATRIX_TEMPLATE.md) — Funcionalidades atuais e comparação com concorrentes.
- [`product/features/VENDAS.md`](product/features/VENDAS.md) — Spec de feature do módulo de Vendas (rascunho).
- [`product/BUSINESS_RULES.md`](product/BUSINESS_RULES.md) — Livro de regras de negócio (BR-001+), implementadas e especificadas.
- [`product/PRODUCT_BACKLOG.md`](product/PRODUCT_BACKLOG.md) — Fila priorizada de épicos (o quê construir a seguir).
- [`product/features/VENDAS_GAP_ANALYSIS.md`](product/features/VENDAS_GAP_ANALYSIS.md) — Consistência entre `VENDAS.md` e o estado real do código (2026-07-22).
- [`product/research/README.md`](product/research/README.md) — Índice e critérios da pesquisa de produto (benchmark, dores reais, perguntas em aberto, decisões de discuss-phase). Nada nesta pasta é especificação; nunca vira requisito sem passar por `product/features/`.
  - [`product/research/BENCHMARKS/MERCADO_PHONE.md`](product/research/BENCHMARKS/MERCADO_PHONE.md) — Benchmark de concorrente, por módulo (Vendas pendente de walkthrough).
  - [`product/research/VENDAS_QUESTIONS.md`](product/research/VENDAS_QUESTIONS.md) — Perguntas em aberto para o discuss-phase do Épico Vendas, com prioridade proposta.
  - [`product/research/VENDAS_DORES_REAIS.md`](product/research/VENDAS_DORES_REAIS.md) — Dores reais da operação (vazio, aguardando coleta de campo).
  - [`product/research/DISCOVERY_DECISIONS.md`](product/research/DISCOVERY_DECISIONS.md) — Decisões tomadas durante o discuss-phase, com raciocínio (vazio, nenhuma sessão ocorreu ainda).

---

## `engineering/` — Arquitetura e Constituição Técnica

- [`engineering/ENGINEERING_GUIDE.md`](engineering/ENGINEERING_GUIDE.md) — Constituição técnica: princípios, stack, padrões, convenção de domínios.
- [`engineering/ARCHITECTURE.md`](engineering/ARCHITECTURE.md) — Visão arquitetural completa: camadas, módulos, fluxos de dados.
- [`engineering/DOMAIN_MODEL.md`](engineering/DOMAIN_MODEL.md) — Mapa dos domínios de negócio existentes no código, com testes e dependências.
- [`engineering/DATABASE.md`](engineering/DATABASE.md) — Schema do banco, tabelas, índices, regras de migração.
- [`engineering/DATA_DICTIONARY.md`](engineering/DATA_DICTIONARY.md) — Governança de dados: quem cria/altera/exclui/vê cada campo.
- [`engineering/SECURITY.md`](engineering/SECURITY.md) — Política de segurança e checklist OWASP adaptado ao projeto.
- [`engineering/TESTING.md`](engineering/TESTING.md) — Estratégia oficial de testes: pirâmide, ferramentas, quando usar cada tipo.
- [`engineering/ROUTE_COVERAGE_AUDIT_2026-11.md`](engineering/ROUTE_COVERAGE_AUDIT_2026-11.md) — Auditoria de cobertura de rotas (2026-11-14, retrato de `1e9c265`): cada rota com método, autorização e testes HTTP; lacunas em KI-069 a KI-076.
- [`engineering/CODE_STYLE.md`](engineering/CODE_STYLE.md) — Guia de estilo: Python, React, Git. Elimina discussões subjetivas.
- [`engineering/QUALITY_GATES.md`](engineering/QUALITY_GATES.md) — Contrato de qualidade: critérios objetivos para aprovação de PR.
- [`engineering/AI_WORKFLOW.md`](engineering/AI_WORKFLOW.md) — Protocolo de trabalho para qualquer IA.
- [`engineering/CLAUDE_CODE_TOOLING.md`](engineering/CLAUDE_CODE_TOOLING.md) — Implementação do `AI_WORKFLOW.md` específica do ambiente Claude Code: quais plugins/skills/MCPs usar em cada etapa (Superpowers, frontend-design, Playwright, ECC DevTools, Claude-in-Chrome).
- [`engineering/CONTRIBUTING.md`](engineering/CONTRIBUTING.md) — Como contribuir: setup, branches, commits, PRs, revisão.
- [`engineering/FUTURE_TECH_EVALUATIONS.md`](engineering/FUTURE_TECH_EVALUATIONS.md) — Ideias técnicas de longo prazo (Next.js para landing, BetterAuth, Supabase, Redis, Resend, Firebase). **Não são decisões aprovadas** — cada item vira ADR só quando houver decisão real a tomar.

### Decisões Arquiteturais (ADRs)

Decisões técnicas importantes, com contexto e alternativas avaliadas:

- [`engineering/adr/ADR-001.md`](engineering/adr/ADR-001.md) — Frontend continuará React + Vite
- [`engineering/adr/ADR-002.md`](engineering/adr/ADR-002.md) — Separar API em módulos por domínio
- [`engineering/adr/ADR-003.md`](engineering/adr/ADR-003.md) — SQLite até a versão 2
- [`engineering/adr/ADR-004.md`](engineering/adr/ADR-004.md) — Fluxo `hotfix/` obrigatório em sprints de teste/QA/validação
- [`engineering/adr/ADR-005.md`](engineering/adr/ADR-005.md) — Estratégia de multiempresa (proposta, decisão pendente)
- [`engineering/adr/ADR-006.md`](engineering/adr/ADR-006.md) — Reorganização de `docs/` e adoção da marca Fluxoly

→ Índice completo: [`engineering/ARCHITECTURE_DECISIONS.md`](engineering/ARCHITECTURE_DECISIONS.md)
→ Template para novas decisões: [`engineering/templates/ADR_TEMPLATE.md`](engineering/templates/ADR_TEMPLATE.md)

---

## `security/` — Auditorias Pontuais

Distinto de `engineering/SECURITY.md` (política de segurança permanente, checklist OWASP): esta pasta
guarda auditorias de um momento específico, disparadas por evento (scan de ferramenta, revisão externa).

- [`security/SECURITY_AUDIT_2026-07.md`](security/SECURITY_AUDIT_2026-07.md) — Triagem do scan Aikido de 2026-07-25: cada alerta validado no código antes de classificar (3 falsos positivos, 2 P0 confirmados, vários P1 confirmados).

---

## `operations/` — Estado Vivo de Execução

- [`operations/PROJECT_STATUS.md`](operations/PROJECT_STATUS.md) — Score, cobertura, riscos, arquivos críticos. Atualizado a cada sprint.
- [`operations/ROADMAP.md`](operations/ROADMAP.md) — Roadmap de sprints de engenharia. Desatualizado desde 2026-07-06 (ver aviso no topo do arquivo) — para o horizonte estratégico atual, ver `company/RELEASE_STRATEGY.md`.
- [`operations/KNOWN_ISSUES.md`](operations/KNOWN_ISSUES.md) — Bugs e issues conhecidos. Nunca apagar — apenas mover para Resolvidos.
- [`operations/CHANGELOG.md`](operations/CHANGELOG.md) — Histórico de versões e mudanças (formato Keep a Changelog).

### Histórico de Sprints

- [`operations/SPRINTS/SPRINT_00.md`](operations/SPRINTS/SPRINT_00.md) — MVP em Produção (concluída)
- [`operations/SPRINTS/SPRINT_01.md`](operations/SPRINTS/SPRINT_01.md) — Correções Críticas e Shopping List (concluída)
- [`operations/SPRINTS/SPRINT_02.md`](operations/SPRINTS/SPRINT_02.md) — Infraestrutura de Qualidade (em andamento)
- [`operations/SPRINTS/SPRINT_COMERCIAL_0.1.md`](operations/SPRINTS/SPRINT_COMERCIAL_0.1.md) — Catálogo de Produtos (concluída)

→ Template para novas sprints: [`operations/templates/SPRINT_TEMPLATE.md`](operations/templates/SPRINT_TEMPLATE.md)

---

## Templates

- [`operations/templates/SPRINT_TEMPLATE.md`](operations/templates/SPRINT_TEMPLATE.md) — Template de sprint
- [`engineering/templates/ADR_TEMPLATE.md`](engineering/templates/ADR_TEMPLATE.md) — Template de decisão arquitetural
- [`engineering/templates/PLAN_TEMPLATE.md`](engineering/templates/PLAN_TEMPLATE.md) — Template de Plano Técnico (ciclo de feature com regra de negócio, `engineering/adr/ADR-010.md`); artefatos vivem em `engineering/plans/`, efêmeros por definição
- [`operations/templates/ISSUE_TEMPLATE.md`](operations/templates/ISSUE_TEMPLATE.md) — Template de issue/bug
