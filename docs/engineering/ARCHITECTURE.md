# ARCHITECTURE.md — Visão Arquitetural

Este documento descreve a arquitetura real do Fluxoly Platform conforme implementada no código.
Não descreve o estado desejado — para isso, veja `ROADMAP.md`. Divergências entre este documento e o
código devem ser corrigidas neste documento (o código é a fonte da verdade).

**Última revisão:** 2026-07-07

---

## 1. Visão Geral

```
┌─────────────────────┐        HTTP/JSON        ┌──────────────────────────┐
│  Frontend (React 19) │ ───────────────────────▶│  Backend (Flask 3)       │
│  Vite + Radix UI      │◀─────────────────────── │  Gunicorn (produção)     │
│  servido em /app/*    │      cookies de sessão   │                          │
└─────────────────────┘                          └──────────┬───────────────┘
                                                              │
                                                              ▼
                                                   ┌──────────────────────┐
                                                   │ SQLite (WAL mode)     │
                                                   │ database.db          │
                                                   └──────────────────────┘
```

- O Flask serve **duas superfícies simultâneas**: rotas legadas server-rendered (formulários, sessão
  via cookie) e uma API JSON (`/api/*`) consumida pelo frontend React em `/app/*`.
- Não há separação de processos — um único `app.py` inicializa o Flask, garante o schema do banco e
  registra todos os blueprints antes de aceitar requisições.

---

## 2. Camadas do Backend

### 2.1 `app.py` — composition root

Responsabilidades:
- Inicialização da aplicação Flask e configuração (`FLASK_SECRET_KEY`, CORS, sessão).
- `criar_tabelas()` — garante o schema do banco (`CREATE TABLE IF NOT EXISTS` + `ALTER TABLE` ad-hoc
  para colunas novas). Ver `DATABASE.md` para o schema completo.
- Funções utilitárias compartilhadas entre blueprints (ex.: `conectar()`, `carregar_os_com_relacoes()`,
  cálculo de faturamento/lucro).
- Registro de todos os blueprints, injetando dependências via dicionário (`deps`) — não há import
  direto de um blueprint para outro.
- `ROUTE_PERMISSIONS` — mapa de permissões por endpoint para as rotas legadas (ver seção 4).
- Redirecionamento de rotas legadas (`/login`, `/dashboard`, etc.) para o SPA em `/app/*`
  (`LEGACY_REACT_REDIRECTS`).

Este arquivo tem alto risco de alteração (ver `PROJECT_STATUS.md` — Arquivos Críticos) porque
concentra inicialização, schema e composição — mudanças aqui afetam todo o sistema.

### 2.2 Módulos de domínio (`irflow_*.py`)

Cada módulo tem uma responsabilidade única (SRP — ver `ENGINEERING_GUIDE.md` seção 1):

| Módulo | Responsabilidade |
|--------|-------------------|
| `irflow_core.py` | Constantes de status de OS e utilitários puros (normalização de texto/status, cálculo de faturamento/lucro) |
| `irflow_os.py` | Lógica de negócio de Ordens de Serviço (consumo/devolução de peças, validação de reparos) |
| `irflow_price_tables.py` | Tabela de preços por modelo/reparo e endpoint de sugestão de valor |
| `irflow_reference_data.py` | Dados de referência (modelos de iPhone, cores, técnicos, vendedores) |
| `irflow_reports.py` | Geração de relatórios agregados e PDF (Técnicos, Custos Operacionais) |
| `irflow_storage.py` | Backup (local, e-mail, Google Drive) |
| `irflow_mercadophone.py` | Integração externa com o sistema MercadoPhone (importação de OS, sincronização por webhook/polling) |
| `irflow_web.py` | Utilitário de redirecionamento com preservação de query string |

### 2.3 Blueprints (`irflow_blueprints_*.py`)

Camada HTTP — cada blueprint expõe rotas e delega lógica de negócio aos módulos de domínio via
dependências injetadas (`create_*_blueprint(deps: dict)`):

| Blueprint | Prefixo/escopo | Conteúdo |
|-----------|----------------|----------|
| `irflow_blueprints_auth.py` (`auth_views`) | `/login`, `/logout` | Autenticação legada (formulário) — só login/logout |
| `irflow_blueprints_api.py` (`api`, prefixo `/api`) | `/api/*` | API JSON completa consumida pelo React — auth (`/api/auth/*`), OS, estoque, shopping list, relatórios, integrações, admin, usuários (`/api/usuarios`). ~3100 linhas, ~80+ endpoints (ver KI-003/TD-01) |
| `irflow_blueprints_main.py` (`main_views`) | `/`, `/kanban`, `/garantias`, `/relatorios`, `/backup` | Views legadas GET-only (redirecionam para o SPA) + geração de PDF de relatório + download de backup |

**Removidos em 2026-07-26 (vulnerabilidade de CSRF — ver KNOWN_ISSUES.md):**
`irflow_blueprints_orders.py` (`order_views`), `irflow_blueprints_inventory.py` (`inventory_views`) e
`irflow_blueprints_admin.py` (`admin_views`) faziam mutações reais (criar/editar/excluir OS, estoque,
custos, reparos, tabelas de preço) via formulário HTML sem proteção CSRF. `auth_views` perdeu as views
de gestão de usuário (`/usuarios/novo|editar|deletar`) pelo mesmo motivo — `/usuarios/novo` aceitando
`perfil=admin` era o pior caso (CSRF permitia criar conta admin controlada pelo atacante).
`main_views.backup` perdeu a lógica de escrita (POST — criar backup/enviar e-mail), redundante com
`POST /api/backup/criar`. Todo o comportamento de redirect GET dessas rotas continua idêntico via
`LEGACY_REACT_REDIRECTS`, que não depende da existência da view function.

**Padrão de injeção de dependências:** cada `create_*_blueprint` recebe um dicionário `deps` com
funções e constantes definidas em `app.py`. Isso evita imports circulares e centraliza a composição
em `app.py` (ver ENGINEERING_GUIDE.md seção 1 — Dependency Inversion).

---

## 3. Duas superfícies HTTP: legada vs. API

O sistema está em transição de server-rendered (Flask + Jinja, hoje reduzido a redirecionamentos)
para uma SPA React consumindo API JSON. Estado atual:

- **Rotas legadas** (`auth_views`, `main_views` — só login/logout e GET-only desde 2026-07-26, ver
  seção 2.3): autenticam via `session` (cookie assinado) e são protegidas pelo `before_request` global
  em `app.py` (`verificar_autenticacao`), que consulta `ROUTE_PERMISSIONS`.
- **API JSON** (`/api/*`): autenticação própria por endpoint (`usuario_logado()` dentro do próprio
  blueprint), **não** passa pelo `ROUTE_PERMISSIONS` — o `before_request` ignora explicitamente
  qualquer endpoint que comece com `api.`.
- Requisições `GET`/`HEAD` para paths legados conhecidos (`/`, `/login`, `/ordens`, etc.) são
  redirecionadas para o equivalente em `/app/*` via `LEGACY_REACT_REDIRECTS` /
  `destino_react_legado()`.

**Implicação para testes:** um teste de login pode exercitar dois caminhos distintos e
não-equivalentes:
1. `POST /login` (form, `irflow_blueprints_auth.py`) — usado pelas views legadas.
2. `POST /api/auth/login` (JSON, `irflow_blueprints_api.py`) — usado pelo frontend React em produção.

Ambos escrevem os mesmos campos de sessão (`usuario_id`, `usuario_nome`, `usuario_perfil`), mas são
implementações separadas e podem divergir silenciosamente.

---

## 4. Autenticação e Autorização

- Sessão via Flask session, cookie assinado com `FLASK_SECRET_KEY` (`session.permanent = True` no
  login).
- Perfis: `admin`, `tecnico`, `vendedor`. Nenhuma hierarquia — checagem é sempre por lista explícita
  de perfis permitidos (`ROUTE_PERMISSIONS[endpoint]`).
- `ROUTE_PERMISSIONS` (`app.py`) mapeia `endpoint → list[perfil] | None`:
  - `[]` — acesso livre, sem sessão.
  - `None` — qualquer perfil autenticado.
  - `["admin"]` (ou outra lista) — apenas perfis listados.
- Logout: `session.clear()` — invalida todos os campos de sessão de uma vez.
- A API (`/api/*`) reimplementa a própria checagem por endpoint (`usuario_logado()`,
  `session.get("usuario_perfil") == "admin"`) — não há um decorator/middleware único compartilhado
  entre a API e as rotas legadas.

---

## 5. Frontend (React 19 + Vite)

```
frontend/src/
├── api/client.js         — único ponto de chamada à API (todas as rotas /api/*)
├── contexts/AuthContext.jsx — estado global de autenticação (user, loading)
├── components/Layout.jsx — layout autenticado (sidebar, header)
├── pages/                — uma página por rota
└── App.jsx                — roteamento e guarda de rotas (ProtectedRoute)
```

- `App.jsx` define duas rotas públicas (`/login`, `/checklist/:token`) e todas as demais atrás de
  `ProtectedRoute`, que redireciona para `/login` se `AuthContext` não tiver `user`.
- `ProtectedRoute` é client-side apenas — a proteção real dos dados é feita pelo backend
  (`/api/*` verificando sessão a cada request). O frontend nunca deve ser tratado como camada de
  segurança.
- `AuthContext` chama `GET /api/auth/me` para hidratar o estado de usuário ao carregar a aplicação.

---

## 6. Integração Externa — MercadoPhone

`irflow_mercadophone.py` (~1200 linhas) integra com o sistema externo MercadoPhone via webhook e
sincronização periódica (polling), controlada por `mercado_phone_runtime_config` (habilitação,
intervalo, timeout, data de início) persistida em arquivo de configuração
(`carregar_configuracoes_integracoes` / `salvar_configuracoes_integracoes`).
Rotas de webhook (`receber_os_mercado_phone`, `sync_os_mercado_phone`, `status_sync_mercado_phone`)
usam autenticação própria por token, fora do `ROUTE_PERMISSIONS` (ver R-07 em `PROJECT_STATUS.md`).

---

## 7. Backup e Persistência

- Banco único SQLite em modo WAL (`database.db`), sem réplica (ver R-01 em `PROJECT_STATUS.md`).
- `irflow_storage.py` gera backups locais, opcionalmente envia por e-mail e/ou sincroniza com Google
  Drive. Falhas de envio são apenas logadas (ver KI-006).
- Testes automatizados **nunca** tocam `database.db` — isolamento via variável de ambiente
  `IR_FLOW_DATA_DIR`, que redireciona o caminho do banco para um diretório temporário antes do
  import de `app.py` (ver `tests/conftest.py`).

---

## 8. Deploy

- Produção: backend Flask (Gunicorn) no Render, frontend estático (build do Vite) na Vercel —
  serviços separados, ver `DEPLOY.md`.
- O Flask também sabe servir o build do Vite como estático em `/app/*` (`serve_react` /
  `serve_react_assets`, isentos de `ROUTE_PERMISSIONS`) — usado no modo processo único (dev local
  ou deploy alternativo), mas não é o que a produção atual (Render + Vercel) usa.

---

## 9. Dívida Arquitetural Conhecida

Ver `KNOWN_ISSUES.md` e `PROJECT_STATUS.md` (seção Dívida Técnica) para o registro vivo. Resumo:

- `irflow_blueprints_api.py` concentra ~80+ endpoints sem separação por domínio (KI-003/TD-01) —
  planejado para decomposição na Sprint 4.
- Schema de banco sem migrations formais, apenas `ALTER TABLE` com `try/except` (KI-004/TD-03) —
  planejado para Sprint 4.
- Duplicação de lógica de autenticação entre rotas legadas e API (`ROUTE_PERMISSIONS` vs.
  `usuario_logado()` por endpoint) — não há ADR registrado sobre unificar; candidato a
  `ARCHITECTURE_DECISIONS.md` se a duplicação gerar divergência de comportamento.
