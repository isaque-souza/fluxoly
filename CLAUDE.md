# CLAUDE.md — Manual Operacional

Este arquivo é o ponto de entrada obrigatório para qualquer sessão de trabalho neste repositório.
Leia-o inteiramente antes de qualquer ação — sem exceções.

---

## O Projeto

**Fluxoly** é uma plataforma de gestão para lojas especializadas em dispositivos móveis premium (nome
legado no código e infraestrutura: Assistência System — ver `docs/company/BRAND_IDENTITY.md`).
Cobre o ciclo completo: abertura de OS, controle de estoque, tabela de preços, lista de compras, garantias, relatórios e backup. Está em produção no Render (backend) + Vercel (frontend).

Stack: **Flask 3 + SQLite** (backend) · **React 19 + Vite** (frontend) · **Render + Vercel** (produção).

---

## Leitura Obrigatória

Antes de qualquer tarefa, leia os documentos abaixo nesta ordem. De cada um, extraia o que está indicado:

| # | Documento | O que extrair |
|---|-----------|---------------|
| 1 | `CLAUDE.md` | Protocolo, regras, filosofia |
| 2 | `docs/company/BRAND_IDENTITY.md` | Identidade de marca (Fluxoly), pilares, escopo negativo, promessa |
| 3 | `docs/engineering/ENGINEERING_GUIDE.md` | Padrões técnicos, convenções, arquitetura |
| 4 | `docs/operations/PROJECT_STATUS.md` | Sprint atual, score, bugs abertos, arquivos críticos |
| 5 | `docs/operations/ROADMAP.md` | Fase e sprint em andamento, objetivos de médio prazo |
| 6 | `docs/operations/KNOWN_ISSUES.md` | Issues abertos — não repita trabalho, não ignore contexto |
| 7 | `docs/engineering/ARCHITECTURE.md` | Camadas, módulos, fluxos de dados |
| 8 | `docs/engineering/DATABASE.md` | Schema, índices, regras de migração |

Após a leitura, descreva o estado do projeto em **exatamente 5 linhas** antes de qualquer ação.
Use o formato:

```
Sistema: <descrição em uma linha>
Sprint atual: <sprint> — <status>
Bugs abertos: <N> (críticos: <N>)
Próximo objetivo: <objetivo>
Risco principal: <risco>
```

---

## Documentos Ausentes

Se qualquer documento da lista acima não existir:

1. **Pare.**
2. Informe exatamente quais documentos estão faltando.
3. Pergunte se deve criá-los antes de continuar.
4. **Não prossiga com a tarefa original até que estejam presentes.**

A ausência de documentação não é um detalhe — é um sinal de que o estado do projeto é desconhecido.

---

## Protocolo de Trabalho

Todo trabalho segue este ciclo obrigatório. Nunca pule etapas.

### 1 — ANALISAR
- Leia os arquivos relevantes. Entenda o impacto.
- Consulte `KNOWN_ISSUES.md`: o problema já foi mapeado?
- Consulte `ARCHITECTURE_DECISIONS.md`: existe uma decisão que afeta isso?
- Nunca implemente sem entender o que pode quebrar.

### 2 — PLANEJAR
- Liste os arquivos que serão modificados.
- Identifique riscos, efeitos colaterais e dependências.
- Para tarefas não-triviais: apresente o plano e aguarde aprovação antes de implementar.
- Se a tarefa altera mais de 3 arquivos: plano obrigatório.
- Para funcionalidades novas com regra de negócio, siga o ciclo com gates definido em
  `docs/engineering/adr/ADR-010.md` (Discovery → Plano Técnico → Implementação → Testes → QA Manual →
  Revisão Arquitetural → Encerramento).

### 3 — IMPLEMENTAR
- Uma mudança por vez. Commits atômicos e descritivos.
- Nunca misture refatoração com feature no mesmo commit.
- Nunca misture correção de bug com feature nova.

### 4 — VALIDAR
- Releia o que foi escrito. Confira coerência com `ENGINEERING_GUIDE.md`.
- Confirme que nenhuma regra de negócio foi violada.
- Confirme que nenhuma dívida técnica foi criada silenciosamente.

### 5 — TESTAR
- Execute os testes relevantes para a mudança.
- Confirme que os testes existentes continuam passando.
- Não marque uma tarefa como concluída com testes falhando.

### 6 — DOCUMENTAR
- Atualize todos os documentos afetados (ver tabela na seção Documentação).

### 7 — ATUALIZAR `PROJECT_STATUS.md`
- Score, cobertura, bugs, arquivos críticos se necessário.

### 8 — ATUALIZAR `CHANGELOG.md`
- Registre a mudança com data e versão.

### 9 — ATUALIZAR `ROADMAP.md` (se necessário)
- Apenas se a mudança altera o planejamento ou as fases.

---

## Bugs Encontrados Durante Sprints de Teste, QA ou Validação

*Vigente a partir de 2026-07-07 (ADR-004) — não se aplica retroativamente a sprints já concluídas.*

Qualquer bug real encontrado durante uma sprint de testes, QA ou validação — não apenas "sprint de testes" no sentido estrito — deve ser avaliado contra os **critérios objetivos de interrupção** em `docs/engineering/ENGINEERING_GUIDE.md` (seção 11).

- Se **algum critério for verdadeiro**: a sprint **para**. Siga o fluxo abaixo antes de continuar.
- Se **nenhum critério for verdadeiro**: não pare. Caracterize o comportamento com um teste (nunca um teste deliberadamente falho) e registre o achado no relatório final da sprint.

```
Bug encontrado durante sprint de teste/QA/validação
                    │
                    ▼
   Atende a algum critério objetivo de interrupção?
        (docs/engineering/ENGINEERING_GUIDE.md, seção 11)
                    │
        ┌───────────┴───────────┐
       NÃO                     SIM
        │                       │
        ▼                       ▼
  Caracterizar com        PARAR a sprint
  teste (não falho)              │
        │                        ▼
        ▼              git checkout main
  Reportar no          git checkout -b hotfix/<nome>
  relatório final                │
  da sprint                      ▼
        │              Implementar a correção mínima
        │                        │
        │                        ▼
        │              Rodar os testes relacionados
        │                        │
        │                        ▼
        │              Merge do hotfix em main
        │                        │
        │                        ▼
        │              Atualizar a branch da sprint
        │              (git merge main / git rebase main)
        │                        │
        └───────────┬────────────┘
                     ▼
         Continuar a sprint original
```

**Regras do fluxo `hotfix/`:**
- Branch nova a partir de `main` — nunca commitada direto na branch da sprint em andamento.
- Correção mínima apenas — sem refatoração, sem feature adicional (mesma regra de sempre: uma mudança por vez).
- Testes relacionados rodam e passam antes do merge em `main`.
- A branch da sprint é atualizada a partir de `main` (merge ou rebase) antes de continuar — nunca diverge silenciosamente.
- Ver `docs/engineering/CODE_STYLE.md` para a convenção de nome (`hotfix/<descrição-em-kebab-case>`) e `docs/engineering/QUALITY_GATES.md` (G-18) para o gate correspondente.

**Por que isso importa:** mistura de correção emergencial com trabalho planejado no mesmo histórico dificulta revisão, torna o fix indisponível em produção até a sprint inteira terminar, e impede reverter a correção isoladamente se algo der errado. Ver `docs/engineering/adr/ADR-004.md` para o contexto completo da decisão.

---

## Regras Absolutas — NUNCA

| Regra | Razão |
|-------|-------|
| Nunca modificar o banco sem plano aprovado | Migrations mal feitas corrompem dados reais de clientes |
| Nunca remover código sem confirmar | Pode ser código em uso não rastreado — quebra contrato silenciosamente |
| Nunca quebrar regra de negócio existente | O sistema está em produção — regressões têm custo real imediato |
| Nunca fazer refatoração junto com feature | Mistura dificulta revisão e multiplica risco de regressão |
| Nunca criar duplicação de código | Viola DRY, gera inconsistências que acumulam dívida |
| Nunca ignorar testes falhando | Testes falhos são bugs — não entregar com CI vermelho |
| Nunca commitar segredos ou credenciais | Chaves, senhas, tokens jamais no repositório |
| Nunca usar `--no-verify` ou `--force` sem aprovação explícita | Bypassa gates de qualidade que existem por razão |
| Nunca assumir o estado do banco em produção | O schema real pode divergir — sempre verificar |
| Nunca implementar sem ler os documentos obrigatórios | Decisões sem contexto geram retrabalho e regressões |
| Nunca adicionar feature não solicitada | Escopo deve ser exatamente o que foi pedido |
| Nunca apagar entradas do `KNOWN_ISSUES.md` | Apenas mover para "Resolvidos" com data e commit |

---

## Regras Absolutas — SEMPRE

- Sempre seguir Conventional Commits: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`
- Sempre criar branch de feature antes de implementar: `feat/nome`, `fix/nome`, `refactor/nome`
- Sempre manter testes isolados — nenhum teste pode tocar `database.db`
- Sempre atualizar `KNOWN_ISSUES.md` ao identificar novo bug, mesmo que não corrigirá agora
- Sempre verificar `KNOWN_ISSUES.md` antes de começar uma correção
- Sempre preferir editar arquivos existentes a criar novos
- Sempre confirmar antes de qualquer ação destrutiva (delete, drop, force push, truncate)
- Sempre documentar decisões arquiteturais em `ARCHITECTURE_DECISIONS.md`
- Sempre manter o escopo exato do que foi pedido
- Sempre criar `SPRINTS/SPRINT_NN.md` ao iniciar uma nova sprint, usando o template
- Sempre interromper uma sprint de testes/QA/validação e abrir `hotfix/...` quando um achado atender a algum critério objetivo de interrupção (ver seção "Bugs Encontrados Durante Sprints de Teste, QA ou Validação" e `docs/engineering/ENGINEERING_GUIDE.md` seção 11)

---

## Critérios para Aprovar Alterações

Avalie antes de implementar qual nível de aprovação é necessário:

### Pode prosseguir sem aprovação explícita
- Correção de bug com escopo claro e isolado (um arquivo, sem mudança de schema)
- Adição de teste sem mudança de lógica
- Atualização de documentação
- Refatoração dentro de um único arquivo com testes cobrindo

### Requer apresentar plano e aguardar aprovação
- Qualquer mudança em `app.py` ou `fluxoly_blueprints_api.py`
- Qualquer alteração no schema do banco de dados
- Adição ou remoção de dependências (`requirements.txt`, `package.json`)
- Mudança em qualquer fluxo de autenticação ou autorização
- Qualquer mudança que afete mais de 3 arquivos simultaneamente
- Feature nova, mesmo que pequena

### Requer aprovação explícita + ADR documentado
- Mudança de banco de dados (ex: SQLite → PostgreSQL)
- Mudança de framework ou biblioteca principal
- Mudança de estratégia de deploy
- Alteração na estrutura de pastas do projeto
- Qualquer decisão irreversível ou de alto custo para desfazer

---

## Responsabilidade de Documentação

Ao concluir qualquer tarefa, verifique esta tabela:

| Tipo de mudança | Documentos a atualizar |
|-----------------|------------------------|
| Nova feature | `CHANGELOG.md`, `PROJECT_STATUS.md`, sprint atual em `SPRINTS/` |
| Bug corrigido | `KNOWN_ISSUES.md` (mover para Resolvidos), `CHANGELOG.md` |
| Nova vulnerabilidade identificada | `KNOWN_ISSUES.md`, `SECURITY.md` |
| Decisão arquitetural tomada | `ARCHITECTURE_DECISIONS.md`, `ARCHITECTURE.md` se estrutural |
| Mudança no schema do banco | `DATABASE.md` |
| Mudança em processo de desenvolvimento | `CONTRIBUTING.md`, `ENGINEERING_GUIDE.md` |
| Conclusão de sprint | `PROJECT_STATUS.md`, `ROADMAP.md`, sprint file em `SPRINTS/` |
| Início de nova sprint | Criar `SPRINTS/SPRINT_NN.md` a partir de `templates/SPRINT_TEMPLATE.md` |
| Novo ADR | Adicionar em `ARCHITECTURE_DECISIONS.md` com numeração sequencial |

---

## Estrutura de Documentos

`docs/` é organizado por audiência desde 2026-07-10 (ver ADR-006). Critério de cada pasta: `company/` só
recebe decisão do Product Owner; `engineering/` descreve como o sistema é construído, independente da
feature do momento; `product/` é pesquisa/planejamento do que construir a seguir; `operations/` é o
estado vivo que muda a cada sprint.

```
CLAUDE.md                                    ← este arquivo (manual operacional — lido primeiro)
docs/
├── README.md                                ← índice de navegação de toda a documentação
├── company/                                 ← identidade e negócio (decisão do Product Owner)
│   ├── BRAND_IDENTITY.md                    ← nome, pilares, escopo negativo, promessa (Fluxoly)
│   ├── VISION.md                            ← missão, visão, valores, critérios de sucesso
│   ├── PRODUCT_REQUIREMENTS.md              ← persona, mercado-alvo, monetização (parcialmente TODO)
│   ├── OPERATION_SYSTEM.md                  ← como a loja funciona (ciclo completo, maioria TODO)
│   ├── DECISION_LOG.md                      ← histórico executivo de decisões (distinto de ADR)
│   ├── NON_FUNCTIONAL_REQUIREMENTS.md        ← capacidade, desempenho, disponibilidade (formulário, maioria TODO)
│   ├── RELEASE_STRATEGY.md                  ← versionamento 0.8-2.0 e as 6 Fases estratégicas (decidido)
│   ├── RELEASE_1.0_MASTER_CHECKLIST.md      ← checklist de certificação: pronto para o 1º cliente pagante?
│   └── GO_LIVE_PLAN.md                      ← plano de execução para colocar um cliente em produção
├── product/                                 ← pesquisa e planejamento de produto
│   ├── FEATURE_MATRIX_TEMPLATE.md           ← funcionalidades atuais e comparação com concorrentes
│   ├── BUSINESS_RULES.md                    ← livro de regras de negócio (BR-001+)
│   ├── PRODUCT_BACKLOG.md                   ← fila priorizada de épicos (o quê construir a seguir)
│   └── features/                            ← specs de feature em rascunho (ex.: VENDAS.md)
├── engineering/                             ← constituição técnica (padrões que raramente mudam)
│   ├── ENGINEERING_GUIDE.md                 ← constituição técnica central
│   ├── ARCHITECTURE.md                      ← visão arquitetural completa (camadas, módulos, fluxos)
│   ├── ARCHITECTURE_DECISIONS.md            ← índice de ADRs
│   ├── adr/                                 ← decisões arquiteturais individuais (ADR-001 a ADR-006+)
│   ├── DOMAIN_MODEL.md                      ← mapa dos domínios de negócio existentes no código
│   ├── DATABASE.md                          ← schema, tabelas, índices, regras de migração
│   ├── DATA_DICTIONARY.md                   ← governança de dados: quem cria/altera/exclui/vê cada campo
│   ├── SECURITY.md                          ← política de segurança permanente e checklist OWASP
│   ├── TESTING.md                           ← estratégia oficial de testes
│   ├── CODE_STYLE.md                        ← guia de estilo
│   ├── QUALITY_GATES.md                     ← contrato de qualidade
│   ├── AI_WORKFLOW.md                       ← protocolo de trabalho para IA
│   ├── CLAUDE_CODE_TOOLING.md               ← implementação do AI_WORKFLOW.md no ambiente Claude Code (plugins/skills/MCPs)
│   ├── CONTRIBUTING.md                      ← processo de desenvolvimento e PR
│   └── templates/ADR_TEMPLATE.md
├── security/                                ← auditorias pontuais (distinto de engineering/SECURITY.md, que é a política permanente)
│   └── SECURITY_AUDIT_2026-07.md            ← triagem do scan Aikido — P0/P1 validados no código, não às cegas
└── operations/                              ← estado vivo (atualizado a cada sprint)
    ├── PROJECT_STATUS.md                    ← estado atual
    ├── ROADMAP.md                           ← evolução planejada (fases e sprints)
    ├── KNOWN_ISSUES.md                      ← bugs e issues conhecidos (nunca apagar)
    ├── CHANGELOG.md                         ← histórico de versões
    ├── SPRINTS/
    │   ├── SPRINT_00.md                     ← retrospectiva
    │   ├── SPRINT_01.md                     ← retrospectiva
    │   └── SPRINT_02.md                     ← plano ativo
    └── templates/
        ├── SPRINT_TEMPLATE.md
        └── ISSUE_TEMPLATE.md
```

---

## Filosofia do Projeto

**Qualidade acima de velocidade.**
Uma feature entregue com testes e documentação vale mais do que três features entregues sem cobertura. Velocidade sem qualidade é dívida disfarçada de progresso.

**Contexto antes de código.**
Os documentos existem para eliminar suposições. Suposições geram bugs. Bugs em produção têm custo real — clientes, dados, confiança.

**Escopo cirúrgico.**
Cada PR faz uma coisa. Cada commit conta uma história. Cada mudança tem razão documentada. Código que ninguém pediu não entra.

**Dívida técnica é visível.**
Nada é varrido para debaixo do tapete. Se algo não está certo, vai para `KNOWN_ISSUES.md` imediatamente. Problemas ocultos são piores do que problemas conhecidos.

**O banco é sagrado.**
Dados de clientes e ordens de serviço têm valor real para o negócio. Qualquer operação no banco de dados é tratada com cautela máxima — plano, revisão, backup verificado.

**Documentação é entrega.**
Uma feature não está concluída até que seus efeitos estejam refletidos nos documentos relevantes. Código sem documentação é conhecimento privado — e conhecimento privado se perde.
