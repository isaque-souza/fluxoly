# GO_LIVE_PLAN.md — Plano de implantação do primeiro cliente pagante

**Status:** 🔵 Rascunho — criado em 2026-07-25, nunca executado (nenhum cliente pagante ainda)
**Última revisão:** 2026-08-11 (Dry-Run 2B — rollback de infraestrutura Render concluído)

---

## Por que este documento é separado do RELEASE_1.0_MASTER_CHECKLIST.md

Sugestão do usuário (CTO), 2026-07-25 — são duas perguntas diferentes:

| Documento | Pergunta que responde |
|---|---|
| `docs/company/RELEASE_1.0_MASTER_CHECKLIST.md` | "O produto está pronto?" — certificação, itens binários (atende / não atende) |
| `GO_LIVE_PLAN.md` (este documento) | "Como colocamos um cliente em produção com segurança?" — plano de execução, com tarefas reais |

**Pré-requisito:** todos os itens do `RELEASE_1.0_MASTER_CHECKLIST.md` concluídos antes de iniciar este
plano. Diferente daquele documento, aqui **é esperado ter tarefas, subtarefas e sequência de execução**
— este é um runbook operacional, não um checklist de certificação.

---

## Contexto importante: não existe multiempresa ainda

Hoje (2026-07-25) o schema não tem conceito de `empresa` — nenhuma tabela, nenhuma coluna `empresa_id`
(confirmado por busca direta no schema, `app.py`). Multiempresa é a Fase 3 do roadmap
(`docs/company/RELEASE_STRATEGY.md`), ainda bloqueada por decisão pendente em `ADR-005.md`. **Isso
significa que, para o primeiro cliente pagante nos moldes de hoje, "colocar um cliente em produção" não
é "criar um registro de empresa dentro do sistema atual" — é provisionar um deployment próprio**
(instância separada: Render + banco + domínio), o mesmo modelo do cliente atual. Os itens abaixo
refletem essa realidade; vários precisarão ser reescritos quando a Fase 3 (Multiempresa) existir.

---

## Fase 1 — Preparação (antes da semana de implantação)

- [ ] Confirmar `RELEASE_1.0_MASTER_CHECKLIST.md` 100% concluído
- [ ] Backup completo do ambiente de referência (template de onde o novo deployment vai partir)
- [ ] Restore testado num ambiente isolado, não em produção (deveria já estar validado pelo item
      "Restore validado" do master checklist — este passo é a repetição operacional, não o primeiro teste)
- [ ] Ambiente de demonstração/homologação preparado para o cliente conhecer o sistema antes do go-live
- [ ] Contrato/dados do cliente confirmados: nome da empresa, domínio desejado, usuários iniciais
- [ ] Time de suporte alinhado sobre o cronograma de implantação

## Fase 2 — Dia da implantação

- [ ] Provisionar o deployment do cliente (Render + banco + domínio — ou empresa isolada, se a Fase 3
      já tiver sido entregue até lá)
- [ ] Deploy da versão 1.0 (ou a versão vigente) neste ambiente
- [ ] Smoke test completo: login, criar OS, criar item de estoque, criar venda, criar movimentação de
      caixa (financeiro mínimo), gerar relatório
- [ ] Criar usuário administrador do cliente
- [ ] Importar dados existentes do cliente, se houver migração de outro sistema: clientes, estoque, OS
      históricas
- [ ] Validar integrações que o cliente vai usar (ex.: Mercado Phone) — configuração e teste de ponta a
      ponta
- [ ] Confirmar backup automático rodando no ambiente do cliente
- [ ] Treinamento da equipe do cliente (perfis admin/técnico/vendedor)

## Fase 3 — Acompanhamento pós-lançamento

- [ ] Acompanhamento diário nos primeiros 7 dias (ajustar o número conforme a experiência do primeiro
      cliente real — não validado ainda)
- [ ] Canal de suporte direto definido e comunicado ao cliente
- [ ] Revisão de logs/erros diária na primeira semana (depende do item "Logs estruturados" e
      "Monitorização" do master checklist estarem prontos — hoje não estão)
- [ ] Checkpoint com o cliente ao final da primeira semana: o que funcionou, o que não funcionou

---

## Plano de rollback

**Política definida em 2026-08-10** (Discovery da Operação Release 1.0 — Parte B, decisão do CTO, uma
pergunta de cada vez, seguindo a separação técnico/política/autoridade/procedimento do `CLAUDE.md`. Ver
também `DEPLOY.md` seção "Rollback" para o procedimento técnico espelhado):

- **Escopo:** rollback coordenado — backend (Render) e frontend (Vercel) são sempre revertidos juntos,
  nunca de forma independente.
- **Critério de acionamento:** bug crítico impedindo operação, perda/corrupção de dados, ou
  indisponibilidade prolongada.
- **Autoridade:** só o CTO autoriza um rollback. Claude nunca executa um rollback sem aprovação explícita
  a cada ocorrência real — esta política não é uma autorização permanente.
- **Interação com migrations (TD-03 — roll-forward only):** rollback de código **nunca cruza uma
  migration já aplicada** em produção. Se o deploy problemático incluiu uma migration nova, a correção é
  sempre um hotfix roll-forward — nunca reverter para um commit anterior à migration.
- **Mecanismo técnico:** `git revert` do(s) commit(s) problemático(s) em `main` + `git push` — dispara
  redeploy normal em Render e Vercel a partir do código revertido. Deliberadamente não usa o "redeploy de
  versão anterior" nativo de cada plataforma, que deixaria `main` divergente do que está rodando.
- **Verificação:** smoke test manual mínimo (login + uma operação real por módulo crítico — criar OS,
  criar venda, ver dashboard) contra produção logo após o redeploy.
- **Restauração de dado**, se o gatilho envolveu perda/corrupção: mesmo processo já validado do item
  "Restore validado" do master checklist (`api_backup.py::restaurar_backup_upload`).
- **Conflito durante o revert** (decidido em 2026-08-10, após o Dry-Run 1B — ver
  `docs/operations/PROJECT_STATUS.md`): qualquer conflito em `git revert` durante um rollback de produção
  é **condição de parada** — cobre qualquer tipo de arquivo (código, documentação, testes, configuração,
  migrations, ou qualquer outro). O Dry-Run 1B usou um commit real (`609619f`) e gerou conflito real em
  `docs/operations/KNOWN_ISSUES.md` (arquivo append-only, evoluído por commits posteriores); resolvê-lo
  exigiria decisão de conteúdo (reabrir vs. remover a entrada do KI-028, e propagar a consistência para
  outros documentos que a referenciam) — não é uma operação puramente mecânica de Git.
  - **Não fazer automaticamente:** `git revert --continue`, `git revert --abort`, `git revert --skip`,
    escolher `ours`/`theirs`, apagar documentação para o revert passar, `git reset`, force-push.
  - **Fazer:** parar, preservar a evidência do conflito, informar o CTO, aguardar decisão explícita antes
    de qualquer resolução ou continuação.
  - **Decisões possíveis do CTO:** resolver o conflito de forma controlada; hotfix roll-forward; rollback
    alternativo; abortar o rollback.
- [ ] Comunicação ao cliente em caso de rollback — ainda não definida; só relevante quando houver um
      cliente real em produção, fora do escopo desta decisão

---

## Preview Seguro (pré-requisito do Dry-Run 2B)

**Achado (INC-003, 2026-08-10):** durante a validação de isolamento do Render PR Preview (Dry-Run 2A), um
preview herdou credenciais de integração externa de produção e importou 405 Ordens de Serviço reais via
MercadoPhone. Contido (preview suspenso, banco/disco nunca compartilhados com produção). Ver relatório
completo em `docs/operations/INCIDENTS/INC-003-mercadophone-preview-dados-reais.md`.

**Correção (defesa em profundidade, decisão do CTO):** guard de código (`IS_PULL_REQUEST` desliga
background jobs incondicionalmente em qualquer preview) + configuração (desabilitar manualmente
`MERCADO_PHONE_SYNC_ENABLED`/`IR_FLOW_ENABLE_BACKGROUND_JOBS` ao criar um preview). Procedimento técnico
completo em `DEPLOY.md` seção "Preview Seguro"; plano de implementação em
`docs/engineering/plans/PLAN-preview-seguro-inc003-ki035.md`.

**Atualização (2026-08-11 — Encerramento do ciclo `ADR-010`):** a correção acima e a do KI-035 já foram
implementadas, testadas (automatizado + QA manual) e revisadas arquiteturalmente — ver
`docs/engineering/plans/PLAN-preview-seguro-inc003-ki035.md`. Merge confirmado em `main`/`origin/main`
(`6bb2ede`), CI 6/6, deploy confirmado tanto em produção Render (`irflow-backend`, "Deploy live for
6bb2ede") quanto em Vercel Production. O Dry-Run 2B (rollback de infraestrutura Render/Vercel)
**continua bloqueado**, mas não mais por QA/revisão pendente: era uma **decisão separada de autorização
do CTO**, que também precisava considerar o risco residual do KI-037 (endpoints manuais de sincronização
do MercadoPhone ainda alcançáveis por uma sessão `admin`/`tecnico` real dentro de um preview) — decisão
tomada em 2026-08-11, ver abaixo.

### Critérios de autorização do Dry-Run 2B (decisão do CTO, 2026-08-11)

- **Ambiente:** um **preview novo**, provisionado a partir de `main`/`6bb2ede` — nunca o preview suspenso
  da PR #22 (`srv-d9t2ms0u01pc73bmuaqg`), que permanece intocado como evidência pura do INC-003, não
  reaproveitado para nenhum teste novo.
- **KI-037:** aceito como risco residual para este exercício, mitigado operacionalmente (não corrigido em
  código): nenhuma sessão `admin`/`tecnico` real é usada dentro do preview do Dry-Run 2B; o smoke test do
  exercício fica restrito a rotas públicas/leitura. Camada de configuração reforçada manualmente nesse
  preview específico (`MERCADO_PHONE_API_TOKEN` vazio/inválido, `MERCADO_PHONE_SYNC_ENABLED=0`), além do
  guard de código já vigente.
- **Separação de responsabilidade das três frentes** (não confundir): (1) mecanismo `git revert`/Git — já
  validado (Dry-Run 1A/1B); (2) segurança do ambiente Preview contra jobs automáticos — corrigida e
  mergeada; (3) rollback real contra infraestrutura Render/Vercel — é o que o Dry-Run 2B efetivamente
  testa, usando o preview como substituto seguro de produção.

### Dry-Run 2B — executado e concluído (2026-08-11)

As 6 evidências exigidas pelo CTO antes de autorizar o exercício foram confirmadas no Preview da PR #24
(distinto do preview suspenso da PR #22); a configuração operacional (item acima) precisou ser corrigida
e revalidada por redeploy antes da autorização, porque a primeira checagem mostrou que não tinha sido
herdada corretamente — só o guard de código estava protegendo o preview até então.

Ciclo completo executado: commit marcador descartável (`fc972adf`, texto isolado e inofensivo, nenhuma
alteração funcional) → push → Render Auto-Deploy → `git revert` **sem conflito** (`d6cb9aef`) → push →
Render Auto-Deploy → confirmação. `/health`/`/ready` → 200 em cada etapa, logs de boot confirmando as duas
camadas de defesa em profundidade ativas, nenhum log de sincronização MercadoPhone, produção intocada do
início ao fim. Preview suspenso novamente ao final. Registro completo em
`docs/operations/PROJECT_STATUS.md` (seção "Dry-Run 2B").

**Importante — Dry-Run ≠ rollback real de produção:** este exercício prova que o mecanismo funciona contra
infraestrutura Render real, não que um rollback de produção nunca vai encontrar um problema novo. Ele
usou um marcador deliberadamente descartável (nunca uma mudança funcional) e não exercitou nem um
conflito de infraestrutura (só o Dry-Run 1B exercitou conflito, em Git local) nem o lado Vercel/frontend
do rollback coordenado. A regra "conflito durante o revert = condição de parada" (seção "Plano de
rollback" acima) continua valendo integralmente para qualquer rollback real futuro, dry-run ou não.

**Decisões que este Dry-Run não tomou:** destino da PR #24 (descartável) e da PR #22 (evidência
preservada do INC-003); correção de código do KI-037 (risco residual aceito só para este exercício,
mitigado operacionalmente, não corrigido). Todas seguem pendentes, decisão separada do CTO.
**Atualização (2026-11-06):** PR #22 fechada sem merge pelo CTO (branch apagada) — backend Render
retirado do ar; a evidência do INC-003 segue registrada neste documento. PR #24 já estava fechada.

---

## O que este documento ainda não tem (gaps conhecidos)

- A política de rollback está definida e aprovada (2026-08-10). Três exercícios concluídos até
  2026-08-11: Dry-Run 1A validou o mecanismo `git revert` isolado, sem conflito (commit `f5fdb23`, só
  testes, branch `dry-run/rollback-f5fdb23`, preservada); Dry-Run 1B, com um commit real de produção
  (`609619f`), encontrou um conflito real em documentação — o que levou à regra "Conflito durante o
  revert" acima (`git revert --abort` executado com sucesso, `main`/`origin/main` nunca tocadas); Dry-Run
  2B validou o rollback real contra infraestrutura Render (ver seção "Dry-Run 2B" acima). Ainda faltam:
  repetir o Dry-Run 1B sob a nova regra, um dry-run local completo sem interrupção, um dry-run que
  exercite um conflito de infraestrutura (não só de Git local), o lado Vercel/frontend do rollback
  coordenado, e — por definição, nunca substituído por um dry-run — a primeira execução real de rollback
  em produção.
- Comunicação ao cliente em caso de rollback ainda não definida.
- Número de dias de acompanhamento pós-lançamento é um palpite (7 dias), não uma decisão validada.

---

## Documentos relacionados

- `docs/company/RELEASE_1.0_MASTER_CHECKLIST.md` — pré-requisito deste plano
- `docs/company/RELEASE_STRATEGY.md` — Fase 3 (Multiempresa) muda o significado de "provisionar um
  cliente" quando for entregue
- `docs/engineering/adr/ADR-005.md` — decisão pendente que define como multiempresa vai funcionar
- `docs/operations/INCIDENTS/INC-003-mercadophone-preview-dados-reais.md` — incidente que originou a
  seção "Preview Seguro"
- `docs/engineering/plans/PLAN-preview-seguro-inc003-ki035.md` — plano técnico da correção
