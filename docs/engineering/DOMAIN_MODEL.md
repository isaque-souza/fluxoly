# DOMAIN_MODEL.md — Mapa de Domínios

Este documento mapeia os domínios de negócio do Fluxoly Platform **como eles existem hoje no código**.
Não descreve estado desejado nem features futuras em detalhe — para isso, ver `PRODUCT_ROADMAP.md` (quando existir)
e os ADRs relevantes. Divergências entre este documento e o código devem ser corrigidas aqui (o código é a fonte
da verdade — mesma regra de `ARCHITECTURE.md`).

**Última revisão:** 2026-07-20
**Fonte:** `app.py` (schema), `docs/engineering/ARCHITECTURE.md` (camadas), `tests/` (arquivos reais em `main`), leitura direta dos módulos `irflow_*.py`.

---

## 1. Domínios existentes

Cada domínio abaixo é descrito por: responsabilidade, tabela(s) de banco, módulo(s) de lógica, blueprint(s) HTTP,
página(s) de frontend, testes existentes e dependências com outros domínios. Um domínio sem serviço/repositório
separado hoje está registrado como está — ver seção 3.

### 1.1 Autenticação

| Aspecto | Hoje |
|---|---|
| Responsabilidade | Login, logout, sessão |
| Tabela(s) | `usuarios` (senha com hash Werkzeug) |
| Lógica | Embutida em `irflow_blueprints_auth.py` (rotas legadas) e em `irflow_blueprints_api.py` (`/api/auth/*`) — duas implementações paralelas, ver `ARCHITECTURE.md` seção 3 |
| HTTP | `irflow_blueprints_auth.py` (form `/login`, `/logout`); `/api/auth/*` dentro de `irflow_blueprints_api.py` |
| Frontend | `AuthContext.jsx`, `pages/Login.jsx` |
| Testes | `tests/test_auth.py`, `tests/test_session.py`, `tests/test_security.py` |
| Depende de | Nenhum outro domínio |
| Dependido por | Todos — toda rota protegida verifica `session.get("usuario_id")` antes de qualquer operação |
| Observação | Nenhuma camada de serviço isolada — lógica de autenticação vive direto no blueprint em ambas as superfícies (legada e API) |

### 1.2 Usuários

| Aspecto | Hoje |
|---|---|
| Responsabilidade | CRUD de usuários do sistema, perfis (`admin`, `tecnico`, `vendedor`) |
| Tabela(s) | `usuarios` |
| Lógica | Embutida em `irflow_blueprints_auth.py` (views legadas) e `irflow_blueprints_api.py` (`/api/usuarios`) |
| HTTP | Ambas as superfícies, sem serviço compartilhado |
| Frontend | Tela de administração de usuários (dentro do fluxo admin) |
| Testes | `tests/test_users.py`, `tests/test_permissions.py` |
| Depende de | Autenticação (sessão para validar quem pode administrar usuários) |
| Dependido por | Nenhum outro domínio diretamente |
| Observação | Perfis são checados por lista explícita em `ROUTE_PERMISSIONS` (`app.py`) — não há hierarquia nem permissão por tela (ver `PRODUCT_REQUIREMENTS.md` para a ambição de permissão granular) |

### 1.3 Ordens de Serviço (OS)

| Aspecto | Hoje |
|---|---|
| Responsabilidade | Ciclo de vida completo de uma ordem de serviço: abertura, status, peças, reparos, finalização |
| Tabela(s) | `os`, `os_pecas`, `os_reparos`, `os_checklists`, `reparos` |
| Lógica | `irflow_os.py` — consumo/devolução de peças, FIFO de lotes, validação de reparos |
| HTTP | `irflow_blueprints_orders.py` (views legadas `/ordens*`); `/api/ordens/*` em `irflow_blueprints_api.py` |
| Frontend | `pages/NewOrder.jsx`, `pages/EditOrder.jsx`, `pages/Orders.jsx` |
| Testes | Nenhum arquivo dedicado ainda em `main` — a suíte da Sprint 2.4 (`test/sprint-2-4-regras-negocio-os`, 88 testes) está em branch própria aguardando merge. Cobertura indireta hoje via `tests/test_stock_os_integration.py` (consumo/devolução de peças na OS) |
| Depende de | Estoque (consumo/devolução de peças via `irflow_os.py`), Tabela de Preços (auto-preenchimento de `valor_cobrado`), Dados de Referência (modelos, técnicos), opcionalmente Clientes (`cliente_id`, Sprint P0.1) |
| Dependido por | Relatórios, Integrações MercadoPhone |
| Observação | **`cliente` (texto) continua sendo o campo principal** — coluna `TEXT` solta em `os`. Desde a Sprint P0.1 existe também `os.cliente_id` (aditivo, nullable, sem backfill — ver seção 1.12 Clientes), mas nenhuma rota de criação/edição de OS preenche ou exige esse campo ainda; é infraestrutura pronta para o futuro módulo de Vendas consumir, não uma migração do fluxo atual |

### 1.4 Estoque

| Aspecto | Hoje |
|---|---|
| Responsabilidade | Cadastro de peças/itens, controle de quantidade, custo médio, lotes |
| Tabela(s) | `estoque`, `estoque_lotes`, `movimentacoes` |
| Lógica | CRUD e consulta em `irflow_blueprints_api.py` (`criar_estoque`, `atualizar_estoque`, `listar_estoque`); **movimentação/consumo já vive separada em `irflow_os.py`** (`registrar_movimentacao`, `consumir_peca_da_os`, `_consumir_lotes_fifo`, `devolver_pecas_da_os`) |
| HTTP | `irflow_blueprints_inventory.py` (views legadas `/estoque*`); `/api/estoque/*` em `irflow_blueprints_api.py` |
| Frontend | Páginas de estoque (dentro do fluxo principal) |
| Testes | `tests/test_stock_creation_query.py`, `tests/test_stock_movement.py`, `tests/test_stock_os_integration.py`, `tests/test_stock_security.py` (69 casos, Sprint 2.5) |
| Depende de | Nenhum outro domínio |
| Dependido por | OS (consumo de peças), Compras/Shopping List (reposição sugerida), Relatórios, `unidades_serializadas` (seção 1.13) |
| Observação | Este é o domínio mais próximo de já ter uma "camada de serviço": a lógica de movimentação em `irflow_os.py` é reutilizável e já tem 69 testes cobrindo-a (Sprint 2.5). É o candidato natural a virar `irflow_estoque_service.py` formal quando um novo domínio (ex.: Vendas) precisar consumir a mesma lógica. ~~**Gap de marca:** rastreamento individual por IMEI~~ — resolvido na Sprint P0.1 via `unidades_serializadas` (seção 1.13), extensão do domínio, não substituição — `estoque.quantidade` continua a fonte agregada para itens sem `requer_imei` |

### 1.5 Compras / Lista de Compras (Shopping List)

| Aspecto | Hoje |
|---|---|
| Responsabilidade | Rastrear necessidade de reposição de peças, workflow de status |
| Tabela(s) | `shopping_list`, `shopping_list_logs` |
| Tabela legada morta | `compras` — criada em `app.py`, mas sem rota ativa apontando para ela (ver KI-012, KI-014); candidata a remoção formal na Sprint 4 |
| Lógica | Embutida em `irflow_blueprints_api.py` |
| HTTP | `/api/shopping-list/*` |
| Frontend | `pages/Compras.jsx`, `EditShoppingItemModal.jsx`, `ShoppingModal.jsx` |
| Testes | Nenhum arquivo dedicado ainda (`test_shopping.py` não iniciado — ver `PROJECT_STATUS.md`, "Restante da Sprint 2") |
| Depende de | Estoque (`reposicao_sugerida_estoque`) |
| Dependido por | Nenhum outro domínio |

### 1.6 Tabela de Preços

| Aspecto | Hoje |
|---|---|
| Responsabilidade | Preço sugerido por modelo + reparo |
| Tabela(s) | Sem tabela SQL dedicada — estrutura normalizada em memória/config via `irflow_price_tables.py` (`tabelas_preco_vazias`, `_normalizar_tabela_preco`) |
| Lógica | `irflow_price_tables.py` |
| HTTP | `GET /api/precos/sugerir` em `irflow_blueprints_api.py` |
| Frontend | Consumido via `useEffect` em `NewOrder.jsx`/`EditOrder.jsx` para auto-preencher `valor_cobrado` |
| Testes | Nenhum arquivo dedicado ainda (`test_pricing.py` não iniciado — ver `PROJECT_STATUS.md`, "Restante da Sprint 2") |
| Depende de | Nenhum outro domínio |
| Dependido por | OS (auto-preenchimento de `valor_cobrado`) |

### 1.7 Dados de Referência

| Aspecto | Hoje |
|---|---|
| Responsabilidade | Listas de apoio: modelos, cores, técnicos, vendedores |
| Lógica | `irflow_reference_data.py` |
| HTTP | Endpoints de listagem simples em `irflow_blueprints_api.py` |
| Testes | Nenhum arquivo dedicado conhecido |
| Depende de | Nenhum outro domínio |
| Dependido por | OS (seleção de modelo/técnico) |

### 1.8 Relatórios

| Aspecto | Hoje |
|---|---|
| Responsabilidade | Agregações e exportação em PDF (Técnicos, Custos Operacionais) |
| Lógica | `irflow_reports.py` |
| HTTP | `irflow_blueprints_main.py` (views legadas `/relatorios`); rotas de PDF em `irflow_blueprints_api.py` |
| Frontend | Tela de relatórios |
| Testes | Nenhum arquivo dedicado conhecido |
| Depende de | OS, Estoque (dados agregados de origem) |
| Dependido por | Nenhum outro domínio |

### 1.9 Backup / Persistência

| Aspecto | Hoje |
|---|---|
| Responsabilidade | Backup local, e-mail, Google Drive |
| Lógica | `irflow_storage.py` |
| Testes | Nenhum arquivo dedicado conhecido |
| Depende de | Nenhum domínio específico — opera sobre o banco inteiro |
| Dependido por | Nenhum outro domínio |
| Observação | Falhas de envio apenas logadas, sem alerta visível (KI-006) |

### 1.10 Integrações — MercadoPhone

| Aspecto | Hoje |
|---|---|
| Responsabilidade | Importação de OS e sincronização com sistema externo MercadoPhone |
| Tabela(s) | `integracao_sync_estado`, `integracao_os_vistas` |
| Lógica | `irflow_mercadophone.py` (~1200 linhas) |
| HTTP | Rotas de webhook com autenticação própria por token, fora de `ROUTE_PERMISSIONS` (ver R-07) |
| Testes | Nenhum teste automatizado conhecido — mitigação atual é o script manual `diagnose_mercadophone.py` (ver R-07 em `PROJECT_STATUS.md`) |
| Depende de | OS (cria/sincroniza registros de OS) |
| Dependido por | Nenhum outro domínio |

### 1.11 Núcleo Compartilhado

| Aspecto | Hoje |
|---|---|
| Responsabilidade | Constantes de status de OS, normalização de texto, cálculo de faturamento/lucro |
| Lógica | `irflow_core.py` |
| Testes | Sem arquivo próprio dedicado, mas coberto indiretamente por praticamente toda a suíte (78%+ de cobertura) |
| Depende de | Nenhum outro domínio |
| Dependido por | Todos os domínios que lidam com status de OS ou valores monetários |
| Observação | Único módulo com 78%+ de cobertura de testes hoje — ponto de referência de qualidade para os demais |

### 1.12 Clientes

| Aspecto | Hoje |
|---|---|
| Responsabilidade | Entidade Cliente — cadastro mínimo viável (nome + telefone ou e-mail), busca/paginação. Fundação reutilizável para Vendas, CRM, Garantia, Financeiro (`docs/product/features/CLIENTES.md`) |
| Tabela(s) | `clientes` |
| Lógica | `irflow_clientes_service.py` — **primeiro domínio a seguir de fato** a convenção `controller → service → repository` de `ENGINEERING_GUIDE.md` §3.1 (até aqui só documentada, nunca aplicada) |
| HTTP | `irflow_clientes_controller.py` (`clientes_api`, prefixo `/api/clientes`) |
| Frontend | Nenhum ainda — fundação de backend apenas (Sprint P0.1 é explicitamente "sem tela de vendas") |
| Testes | `tests/test_clientes.py` (23 casos) |
| Depende de | `irflow_audit.py` (auditoria de create/update/delete) |
| Dependido por | OS (`os.cliente_id`, opcional, sem uso ainda), futuramente Vendas (`docs/product/features/VENDAS.md`) |
| Observação | Deduplicação (por telefone, CPF, ou ambos) e o que fazer com clientes duplicados já existentes seguem `TODO` — decisão de negócio pendente do Product Owner, por isso não há `UNIQUE` em `telefone`/`cpf_cnpj`/`email` no schema |

### 1.13 Unidades_Serializadas (rastreamento por IMEI/serial)

| Aspecto | Hoje |
|---|---|
| Responsabilidade | Unidade física individual rastreada por IMEI/serial — fonte única de verdade, com origem em Estoque (seção 1.4) OU Produtos (seção 1.14), nunca os dois (Regra de Ouro, `ADR-007`). Evoluído de `estoque_unidades` (Sprint P0.1) na migração `docs/engineering/migrations/MIGRATION_unidades_serializadas.md` |
| Tabela(s) | `unidades_serializadas`; lê (não escreve) `estoque.requer_imei` e `produtos.requer_rastreio_unidade` |
| Lógica | `irflow_unidades_serializadas_service.py` — segunda aplicação da convenção `controller → service → repository` (depois de Clientes, seção 1.12) |
| HTTP | `irflow_unidades_serializadas_controller.py` (`unidades_serializadas_api`, prefixo `/api/unidades-serializadas`) |
| Frontend | `frontend/src/pages/UnidadesSerializadas.jsx` (rota `/unidades-serializadas`, C1.3.1-C1.3.4) |
| Testes | `tests/test_unidades_serializadas.py` (~27 casos), `tests/test_migration_unidades_serializadas.py` (migração) |
| Depende de | Estoque (leitura de `requer_imei`), Produtos (leitura de `requer_rastreio_unidade`), `irflow_audit.py` (auditoria de create/status_change) |
| Dependido por | Vendas (`marcar_como_vendida`, ver seção 1.15); futuramente Garantias/Troca |
| Observação | **Agregado raiz do domínio Comercial (`ADR-009`, 2026-07-27)** — uma linha representa o ativo físico pela vida toda, nunca uma linha nova por revenda/garantia/troca. `ADR-009` decide o modelo-alvo (Estado Operacional do Ativo × Situação Comercial em eixos separados — Princípio da Independência dos Eixos —, `origem_tipo` substituindo a checagem binária de origem, cancelamento/garantia como eventos de processo, não estado da unidade) para as próximas fases do épico Vendas — **implementação ainda no modelo anterior**: `status` continua enum único (`disponivel`/`em_reparo`/`devolvido` alcançáveis via `TRANSICOES_VALIDAS`; `vendido` só via `marcar_como_vendida`, exclusiva de Vendas). Migração para os dois eixos fica para quando cancelamento/garantia forem implementados. Formato de IMEI não validado ainda (`TODO` em `IMEI.md`). Princípio da Responsabilidade de Transição (ADR-007, estendido por ADR-009) — cada domínio futuro só transiciona os estados que lhe pertencem |

### 1.14 Produtos (catálogo comercial)

| Aspecto | Hoje |
|---|---|
| Responsabilidade | Catálogo de itens à venda (iPhone, Apple Watch, AirPods, Acessório) — domínio **novo e separado** de Estoque (seção 1.4), não uma extensão. `estoque.tipo`/`qualidade` são vocabulário de peça de reparo (hardcoded, coerção silenciosa para valor default), incompatível com um catálogo comercial |
| Tabela(s) | `produtos` — standalone nesta sprint, sem tabela filha ainda |
| Lógica | `irflow_produtos_service.py` — terceira aplicação da convenção `controller → service → repository`. `categoria`/`condicao` validadas contra lista fechada (`PRODUTOS_CATEGORIAS`/`PRODUTOS_CONDICOES`, `irflow_reference_data.py`) e **rejeitadas** (não normalizadas) quando inválidas |
| HTTP | `irflow_produtos_controller.py` (`produtos_api`, prefixo `/api/produtos`) |
| Frontend | Nenhum ainda — fundação de backend apenas (Sprint Comercial 0.1) |
| Testes | `tests/test_produtos.py` (27 casos) |
| Depende de | `irflow_reference_data.py` (listas fechadas), `irflow_audit.py` (auditoria de create/update/delete) |
| Dependido por | `unidades_serializadas` (seção 1.13, origem `produto_id`) desde a migração ADR-007; futuramente Vendas |
| Observação | `requer_rastreio_unidade` (schema desde a Sprint Comercial 0.1) passou a ser consumido pela primeira vez na migração `unidades_serializadas` (ADR-007) — a ambiguidade sinalizada em `VENDAS.md` sobre onde a unidade vendida vive está resolvida |

### 1.15 Vendas (MVP)

| Aspecto | Hoje |
|---|---|
| Responsabilidade | Venda de um único aparelho (unidade serializada) por vez — sem desconto, comissão, garantia, troca ou reserva com timeout (`docs/product/features/VENDAS.md`, dependem de decisões do Product Owner ainda pendentes). Primeiro domínio a nascer com o prefixo `fluxoly_`, não `irflow_` (`ADR-008`) |
| Tabela(s) | `vendas`, `vendas_itens` (modelada como Venda + ItemVenda desde o início, mesmo com 1 item por venda nesta fatia — evita partir a tabela quando itens múltiplos existirem) |
| Lógica | `fluxoly_vendas_service.py` — quarta aplicação da convenção `controller → service → repository`, primeira com o prefixo novo |
| HTTP | `fluxoly_vendas_controller.py` (`vendas_api`, prefixo `/api/vendas`) — só `POST` (criar) e `GET /<id>` (consultar) |
| Frontend | `frontend/src/pages/Vendas.jsx` (rota `/vendas`, sidebar `admin`/`vendedor`) |
| Testes | `tests/test_vendas.py` (21 casos, incluindo corrida real com threads) |
| Depende de | Clientes (validação de `cliente_id`), Unidades Serializadas (validação + transição para `vendido` via `marcar_como_vendida`, exclusiva deste domínio por ADR-007), `irflow_audit.py` |
| Dependido por | Nenhum domínio ainda (Garantias/Financeiro, quando existirem, provavelmente consumirão `vendas.id`) |
| Observação | `marcar_como_vendida` (`irflow_unidades_serializadas_service.py`) é deliberadamente separada de `transicionar_status`/`TRANSICOES_VALIDAS` — evita que o endpoint genérico `PATCH /api/unidades-serializadas/<id>/status` aceite `{"status": "vendido"}` sem uma `venda` real por trás. `UNIQUE` em `vendas_itens.unidade_serializada_id` é a proteção de banco contra a mesma unidade em duas vendas — mantida por ora; `ADR-009` propõe um índice único parcial (`WHERE ativo=1` ou equivalente) como candidato para quando cancelamento (V1.2) for implementado, decisão ainda em aberto. Roadmap das próximas fases (histórico → cancelamento → desconto → comissão → garantia/troca → reserva → financeiro mínimo → documentos) e o modelo de estado-alvo (Estado Operacional do Ativo × Situação Comercial da unidade, venda com máquina de estados própria) definidos em `ADR-009` — reserva manual precede desconto/aprovação (mesmo mecanismo: unidade `reservada`) |

### 1.16 Compra de Aparelhos

| Aspecto | Hoje |
|---|---|
| Responsabilidade | Compra de aparelhos (geralmente quebrados) para conserto e revenda — origem marketplace, troca ou outro (BR-083 a BR-093, `docs/engineering/plans/PLAN-compra-aparelhos.md`) |
| Tabela(s) | `compras_aparelhos` (migration `m0003`) |
| Lógica | `fluxoly_compras_aparelhos_service.py` — registrar (compra + unidade + saída de caixa numa transação), listar, obter, cancelar (estorno + unidade `devolvido`) |
| HTTP | `fluxoly_compras_aparelhos_controller.py` (`compras_aparelhos_api`, prefixo `/api/compras-aparelhos`) — perfis `admin`/`financeiro`/`vendedor` (BR-089); `GET /relatorio?mes=AAAA-MM` só `admin`/`financeiro` (BR-093). Custo/lucro (BR-092) também aparecem em `GET /api/unidades-serializadas/<id>` e `GET /api/vendas/<id>` para `admin`/`financeiro` |
| Frontend | Ainda não (PR 5 da feature) |
| Testes | `tests/test_compras_aparelhos.py` |
| Depende de | Unidades Serializadas (`criar_unidade_de_compra`/`devolver_unidade_de_compra`, cursor-based, exclusivas deste domínio), Caixa (`registrar_saida_de_compra_aparelho`/`estornar_saida_de_compra_aparelho`), Clientes e Vendas (só leitura, para validar a troca), `fluxoly_audit.py` |
| Dependido por | OS interna (`api_os.py`, `abrir_reparo_interno`), controllers de Vendas e Unidades (custo/lucro, BR-092) |

---

## 2. O que ainda não é um domínio isolado

- **Financeiro / Caixa** — não existe hoje. Custos operacionais (`custos_operacionais`) e valores de OS existem,
  mas não há conceito de caixa, sangria, suprimento ou fluxo de caixa consolidado.
- ~~Clientes~~ — resolvido na Sprint P0.1, ver seção 1.12 acima.
- ~~Vendas~~ — MVP resolvido em 2026-07-27, ver seção 1.15 acima. Fluxo completo (desconto, comissão, garantia, troca) segue como especificação, não implementado.

---

## 3. Convenção para novos domínios

A partir de agora, todo domínio novo (ex.: Vendas) segue a convenção formalizada em
`docs/engineering/ENGINEERING_GUIDE.md` seção 3.1 — camadas `controller → service → repository → tests → README`,
incluindo a regra de que **nenhum domínio acessa o repository de outro domínio diretamente** (só o service
do domínio dono) — mesmo que o domínio inicialmente viva no mesmo diretório dos módulos existentes.

**Clientes (seção 1.12) é a primeira aplicação real dessa convenção** (Sprint P0.1, 2026-07-11) — sem
pasta de domínio própria (`irflow_clientes_*.py` soltos na raiz, mesma convenção dos módulos existentes),
o requisito de README curto virou um bloco de docstring no topo de `irflow_clientes_service.py` (adendo
registrado em `ENGINEERING_GUIDE.md` §3.1). `unidades_serializadas` (rastreamento por IMEI/serial)
segue o mesmo padrão logo em seguida.

Este mapa deve ser atualizado a cada novo domínio adicionado ou reestruturado — é o inventário vivo,
não um documento estático.

---

## Documentos relacionados

- `docs/engineering/ARCHITECTURE.md` — visão arquitetural completa (camadas, fluxos)
- `docs/engineering/DATABASE.md` — schema completo
- ADR-002 — decomposição da API por domínio (camada HTTP)
- ADR-005 — estratégia de multiempresa (afeta todos os domínios listados acima)
- `docs/engineering/ENGINEERING_GUIDE.md` seção 3.1 — convenção de camadas para domínio novo
- `docs/BUSINESS_RULES.md` (backlog, ainda não criado) — regras de negócio implícitas hoje em código/testes (ex.: cancelar/excluir OS devolve estoque, garantia não gera comissão) que este documento não cobre — este mapeia estrutura, não regra de negócio
