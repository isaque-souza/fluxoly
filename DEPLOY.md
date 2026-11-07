
# Deploy IR Flow → Render (backend) & Vercel (frontend)

## Backend (Render.com)

### 1. Crie uma conta em https://render.com

### 2. Novo serviço web
- Clique em **New +** > **Web Service**
- Conecte seu repositório (GitHub/GitLab)
- Escolha o repositório do projeto

### 3. Configuração do serviço
- **Environment**: Docker
- **Docker Build Context**: `.`
- **Dockerfile Path**: `Dockerfile`
- **Start Command**: (deixe em branco, o Dockerfile já define)
- **Port**: 8080

### 4. Variáveis de ambiente
Adicione as variáveis necessárias em **Environment > Add Environment Variable**:
- `FLASK_SECRET_KEY` (obrigatório)
- `MERCADO_PHONE_INTEGRATION_ENABLED` (padrão `0` = integração MercadoPhone desligada, ADR-014 — as variáveis `MERCADO_PHONE_*` abaixo só têm efeito com `1`)
- `MERCADO_PHONE_WEBHOOK_TOKEN` (obrigatório para o webhook de importação de OS funcionar — sem ele, toda requisição é rejeitada com 401)
- `MERCADO_PHONE_API_TOKEN` (opcional)
- `MERCADO_PHONE_SYNC_ENABLED=1` (opcional)
- `MERCADO_PHONE_SYNC_INTERVAL_SECONDS=180` (opcional)
- `MERCADO_PHONE_SYNC_TIMEOUT_SECONDS=20` (opcional)
- `MERCADO_PHONE_SYNC_START_DATE=2026-04-01` (opcional)
- `MERCADO_PHONE_DEFAULT_TECNICO=Aguardando definicao` (opcional)
- `IR_FLOW_HOST=0.0.0.0`
- `IR_FLOW_PORT=8080`
- `IR_FLOW_DATA_DIR=/data` (recomendado)
- `RENDER_DISK_PATH=/data` (alternativa)
- `IR_FLOW_CORS_ORIGINS=https://assistencia-system.vercel.app` (ou uma lista separada por vírgula)
- `SENTRY_DSN` (opcional — Sprint Observabilidade, 2026-07-25; vazio desabilita a integração por completo)
- `METRICS_TOKEN` (recomendado em produção — protege `/metrics`; sem essa variável, o endpoint nega por padrão)

> Dica: se usar preview URLs do Vercel, inclua também esses domínios em `IR_FLOW_CORS_ORIGINS`.
> `PROMETHEUS_MULTIPROC_DIR` não precisa ser configurada manualmente — já vem definida no `Dockerfile`.

### 5. Volume persistente (Disks)
- Em **Disks**, clique em **Add Disk**
- Nome: `irflow_data`
- Mount Path: `/data`
- Size: 1GB (ou mais, conforme necessidade)

### 6. Deploy
- Clique em **Create Web Service**
- O Render irá buildar e subir o backend automaticamente

### 7. Acesso
- O Render fornecerá uma URL pública (ex: `https://irflow-backend.onrender.com`)

---

## Frontend (Vercel)

### 1. Crie uma conta em https://vercel.com

### 2. Novo projeto
- Clique em **Add New... > Project**
- Importe o repositório (ou apenas a pasta `frontend`)

### 3. Configuração
- **Framework Preset**: Vite
- **Root Directory**: `frontend`
- **Build Command**: `npm run build`
- **Output Directory**: `dist`

### 4. Variáveis de ambiente (opcional)
Se precisar apontar para a API do backend Render, adicione:
- `VITE_API_URL=https://irflow-backend.onrender.com/api`

No código, use `import.meta.env.VITE_API_URL` para consumir a URL da API.

### 5. Deploy
- Clique em **Deploy**
- A Vercel irá buildar e publicar o frontend automaticamente

### 6. Acesso
- A Vercel fornecerá uma URL pública (ex: `https://irflow-frontend.vercel.app`)

---

## Observações

- O backend (Render) serve apenas a API e arquivos de dados.
- O frontend (Vercel) serve o app React estático e consome a API do backend.
- Ajuste o CORS no backend se necessário para aceitar requisições do domínio da Vercel.
- Para backups, acesse o disco `/data` no Render via SSH ou painel.
- Backups versionados podem ser criados via `POST /api/backup/criar` enviando `{ "versao": "v2" }`.
- Configuração persistente do Mercado Phone pode ser salva via `POST /api/integracoes/mercadophone/config`.

---

## Rollback

**Política definida em 2026-08-10** (decisão do CTO — Discovery da Operação Release 1.0, Parte B. Ver
`docs/company/GO_LIVE_PLAN.md` seção "Plano de rollback" para o registro completo da decisão).

- **Escopo:** rollback é sempre coordenado — reverte backend (Render) e frontend (Vercel) juntos, nunca
  um sem o outro.
- **Quando acionar:** bug crítico impedindo operação, perda/corrupção de dados, ou indisponibilidade
  prolongada.
- **Quem autoriza:** só o CTO. Nenhum rollback deve ser executado sem aprovação explícita a cada
  ocorrência real.
- **Regra de migrations (TD-03 — roll-forward only):** se o deploy problemático incluiu uma migration
  nova já aplicada ao banco de produção, **não faça rollback de código para antes dela** — corrija com um
  hotfix roll-forward. Rollback de código nunca deve cruzar uma migration já aplicada.

### Procedimento

1. Identificar o(s) commit(s) problemático(s) em `main`.
2. `git revert <commit>` (nunca `git reset --hard` nem force-push) — preserva o histórico e, seguindo a
   regra acima, nunca reverte para antes de uma migration já aplicada.
   - **Se houver conflito** (em qualquer tipo de arquivo — código, documentação, testes, configuração,
     migrations): **PARE.** Não resolva automaticamente (`--continue`/`--abort`/`--skip`, escolher
     `ours`/`theirs`, apagar conteúdo para o revert passar, `git reset`, force-push). Preserve a evidência
     do conflito e informe o CTO — a resolução pode exigir decisão de conteúdo, não é garantidamente
     mecânica (achado do Dry-Run 1B, 2026-08-10, ver `docs/company/GO_LIVE_PLAN.md` seção "Plano de
     rollback"). Decisões possíveis do CTO: resolver de forma controlada, hotfix roll-forward, rollback
     alternativo, ou abortar.
3. `git push` — dispara redeploy automático em Render (backend) e Vercel (frontend), mesmo fluxo de
   deploy descrito no topo deste documento.
4. Smoke test manual: login, criar OS, criar venda, conferir dashboard — confirma que a funcionalidade
   real voltou, não só que o processo subiu.
5. Se o gatilho envolveu perda/corrupção de dado, restaurar o backup pré-incidente via
   `POST /api/backup/restaurar` (mesmo processo já validado em `tests/test_backup_restore.py`).

**Parcialmente exercitado** — Dry-Run 1A (mecanismo Git/local, sem conflito) concluído; Dry-Run 1B (commit
real de produção) encontrou um conflito real em documentação, que originou a regra do passo 2 acima.
Ainda não há um dry-run local completo sem interrupção, nem um dry-run de infraestrutura (Render/Vercel).

---

## Preview Seguro (Render PR Preview)

**Achado (INC-003, 2026-08-10):** um Render PR Preview herda **todas** as variáveis de ambiente do
serviço-base na criação (comportamento documentado do próprio Render), incluindo credenciais de
integrações externas (`MERCADO_PHONE_SYNC_ENABLED`, `MERCADO_PHONE_API_TOKEN`) e flags de background jobs
(`IR_FLOW_ENABLE_BACKGROUND_JOBS`). Um preview criado sem nenhuma ação adicional executa os mesmos jobs de
produção (sync automático do MercadoPhone, backup automático) contra um banco isolado, mas com dados/
efeitos reais vindos de sistemas externos reais. Ver
`docs/operations/INCIDENTS/INC-003-mercadophone-preview-dados-reais.md` para o relatório completo e
`docs/engineering/plans/PLAN-preview-seguro-inc003-ki035.md` para a correção.

**Defesa em profundidade (decisão do CTO, 2026-08-10) — duas camadas independentes, nenhuma substitui a
outra:**

1. **Guard de código (implementado):** a variável `IS_PULL_REQUEST`, setada automaticamente pelo Render em
   todo PR Preview, desliga `BACKGROUND_JOBS_ENABLED` (`fluxoly_config.py`) incondicionalmente — cobre a
   sync do MercadoPhone e o backup automático, mesmo que as credenciais/flags tenham sido herdadas do
   serviço-base. Um log estruturado (`preview_background_jobs_desativados`) confirma isso em todo boot de
   preview. O `environment` reportado ao Sentry também passa a ser `"preview"`, nunca `"production"`
   (KI-036).
2. **Configuração (recomendação operacional, camada adicional):** ao criar qualquer Render PR Preview
   manualmente pelo painel, sobrescreva explicitamente `MERCADO_PHONE_SYNC_ENABLED=0` e
   `IR_FLOW_ENABLE_BACKGROUND_JOBS=0` nas variáveis de ambiente específicas desse preview, antes do
   primeiro boot. Não é estritamente necessário para a segurança (o guard de código já cobre o caso de
   ninguém fazer isso), mas reduz a superfície e serve como segunda confirmação visível no painel Render de
   que o preview não deveria tocar nada externo. Não existe `render.yaml`/IaC neste repositório — a criação
   de preview é manual, por isso esta camada depende de lembrete humano e nunca deve ser a única linha de
   defesa.

---

## Passo a passo resumido

1. Suba o backend no Render seguindo as instruções acima.
2. Suba o frontend na Vercel seguindo as instruções acima.
3. Teste o fluxo completo: frontend (Vercel) consumindo a API (Render).
4. Ajuste variáveis de ambiente e CORS conforme necessário.
5. `fly.toml` foi removido do repositório — não é mais usado desde a migração para Render + Vercel.
