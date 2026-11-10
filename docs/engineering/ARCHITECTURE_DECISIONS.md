# Architectural Decision Records — Índice

Cada decisão arquitetural vive em arquivo próprio na pasta [`docs/engineering/adr/`](adr/).
Este arquivo é o índice de navegação.

Para criar uma nova ADR: copie [`templates/ADR_TEMPLATE.md`](templates/ADR_TEMPLATE.md) → salve em `docs/engineering/adr/ADR-NNN.md` → adicione uma linha abaixo.

---

## Decisões

| ADR | Título | Status | Data |
|-----|--------|--------|------|
| [ADR-001](adr/ADR-001.md) | Frontend continuará React + Vite | Aceita | 2026-07-06 |
| [ADR-002](adr/ADR-002.md) | Separar API em módulos por domínio | Aceita — escopo desatualizado, ver ADR-011 | 2026-07-06 |
| [ADR-003](adr/ADR-003.md) | SQLite até a versão 2 | Aceita | 2026-07-06 |
| [ADR-004](adr/ADR-004.md) | Bugs em sprints de teste/QA/validação seguem fluxo `hotfix/` obrigatório | Aceita — não retroativa | 2026-07-07 |
| [ADR-005](adr/ADR-005.md) | Estratégia de multiempresa | Proposta — alternativas técnicas prontas, decisão pendente do Product Owner | 2026-07-08 |
| [ADR-006](adr/ADR-006.md) | Reorganização de `docs/` por audiência e adoção da marca Fluxoly | Aceita | 2026-07-10 |
| [ADR-007](adr/ADR-007.md) | Consolidação de rastreamento por IMEI entre Estoque e Produtos — nova tabela `unidades_serializadas` | Aceita | 2026-07-21 |
| [ADR-008](adr/ADR-008.md) | Rebranding técnico incremental — novos módulos nascem como `fluxoly_*`, legado `irflow_*` inalterado | Aceita | 2026-07-27 |
| [ADR-009](adr/ADR-009.md) | Unidade Serializada como agregado raiz do domínio Comercial — estado físico × situação comercial, `origem_tipo`, eventos de processo separados de estado | Aceita | 2026-07-27 |
| [ADR-010](adr/ADR-010.md) | Ciclo obrigatório para features com regra de negócio — Discovery → Plano Técnico → Implementação → Testes → QA Manual → Revisão Arquitetural → Encerramento, com gates explícitos | Aceita | 2026-07-28 |
| [ADR-011](adr/ADR-011.md) | Atualização da ADR-002 — escopo desatualizado (6→13 domínios); rename de `irflow_blueprints_api.py` concluído na Housekeeping, decomposição (TD-01) adiada para sprint própria | Aceita | 2026-08-03 |
| [ADR-012](adr/ADR-012.md) | Ambiente de Demonstração/Homologação — Render+Vercel dedicados, `IR_FLOW_ENVIRONMENT=demo`, KI-037 vira bloqueante, isolamento de credenciais por design (lição do INC-003) | Aceita | 2026-08-11 |
| [ADR-013](adr/ADR-013.md) | "Lista de Aparelhos Disponíveis": app standalone, fonte MercadoPhone, acesso em 2 níveis por senha | Substituída por ADR-014 | 2026-09-03 |
| [ADR-014](adr/ADR-014.md) | Desvincular o Fluxoly da IR Phones (remove app de estoque e OS interna) e desligar a integração MercadoPhone por flag | Aceita | 2026-11-06 |
| [ADR-015](adr/ADR-015.md) | Deploy automático do backend no servidor próprio — CI publica imagem no GHCR, Watchtower (fork `nickfedor`) atualiza o container com backup do banco antes | Aceita | 2026-11-10 |

---

## Conteúdo legado (mantido para referência)

## ADR-001

Data:
2026-07-06

Título:
Frontend continuará React + Vite.

Motivação:
O frontend foi iniciado com React 19 + Vite + Radix UI + Tailwind CSS. Cogitou-se migrar para um framework fullstack (Next.js) para simplificar o deploy e eliminar a necessidade de servidor separado para o frontend. Porém, o backend Flask já está estável em produção e a equipe tem familiaridade com a separação frontend/backend.

Alternativas:
- Next.js com API Routes: eliminaria o Flask, mas exigiria reescrever toda a camada de negócio em JavaScript e migrar o banco de dados.
- SvelteKit: menor bundle, mas sem familiaridade no time e ecossistema menor para os componentes UI utilizados (Radix).
- Manter React + Vite (escolhida).

Decisão:
Manter React + Vite. O custo de migração supera o benefício. O deploy separado (frontend estático + backend Flask) é bem suportado por Fly.io e pelas alternativas documentadas em DEPLOY.md.

Consequências:
- O build do frontend continua gerando um `dist/` servido pelo Flask em produção.
- Qualquer nova página segue o padrão de arquivos em `frontend/src/pages/`.
- Dependências de UI continuam no ecossistema Radix + Tailwind.

---

## ADR-002

Data:
2026-07-06

Título:
Separar API em módulos por domínio.

Motivação:
`irflow_blueprints_api.py` acumulou ~130KB e mais de 80 endpoints sem separação de responsabilidades. Qualquer alteração nesse arquivo aumenta o risco de regressão e dificulta onboarding de novos colaboradores. A situação foi identificada como dívida técnica TD-01 no PROJECT_STATUS.

Alternativas:
- Manter o monolito e apenas adicionar comentários de seção: resolve superficialmente, não elimina o acoplamento.
- Migrar para FastAPI com routers: traria tipagem e docs automáticas (OpenAPI), mas exigiria reescrever toda a camada de API.
- Decompor em blueprints Flask por domínio (escolhida): menor risco, compatível com a arquitetura atual.

Decisão:
Decompor `irflow_blueprints_api.py` em módulos de blueprint Flask separados por domínio de negócio, planejada para Sprint 4:
- `irflow_api_os.py` — Ordens de Serviço
- `irflow_api_estoque.py` — Estoque
- `irflow_api_shopping.py` — Shopping List
- `irflow_api_relatorios.py` — Relatórios
- `irflow_api_admin.py` — Usuários, backup, configurações
- `irflow_api_integracoes.py` — MercadoPhone

Consequências:
- `app.py` registrará múltiplos blueprints ao invés de um único.
- Todos os testes existentes devem passar sem alteração após a decomposição.
- O arquivo original será removido após migração completa.
- Novos endpoints devem ser adicionados no módulo do domínio correspondente.

---

## ADR-003

Data:
2026-07-06

Título:
SQLite continuará sendo utilizado até a versão 2.

Motivação:
O sistema está em produção com SQLite em modo WAL. Cogitou-se migrar para PostgreSQL para ganhar replicação, conexões concorrentes robustas e suporte a tipos mais ricos. Porém, o volume atual de dados e a carga de usuários simultâneos não justificam a complexidade operacional de gerenciar um servidor PostgreSQL.

Alternativas:
- PostgreSQL: mais robusto para concorrência e replicação, mas adiciona infraestrutura e custo operacional. Necessário se o volume de OS ultrapassar ~50.000 registros ou se houver mais de 10 usuários simultâneos.
- SQLite com Litestream para replicação: mantém a simplicidade com replicação contínua para S3. Avaliado como alternativa intermediária.
- Manter SQLite + backup automático (escolhida para v1.x).

Decisão:
Manter SQLite até a versão 2.0. A migração para PostgreSQL será reavaliada quando qualquer uma das condições abaixo for atingida:
- Volume > 50.000 Ordens de Serviço
- Mais de 10 usuários simultâneos em horário de pico
- Latência de query > 500ms em operações de listagem
- Necessidade de múltiplas instâncias do backend

Consequências:
- O backup automático é a principal linha de defesa contra perda de dados — deve permanecer operacional.
- Migrations devem continuar compatíveis com SQLite (sem usar tipos ou funções exclusivos de PostgreSQL).
- A abstração do banco deve ser mantida em `app.py` e módulos de acesso para facilitar futura migração.
- Risco R-01 do PROJECT_STATUS permanece aceito até a versão 2.
