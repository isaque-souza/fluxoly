# Fase 3.5 — Administrativo (Tier 4): Audit Visual + Plano de Redesign

> **For agentic workers:** este documento é **audit + direção**, não um plano de execução tarefa-a-tarefa.
> Cada fatia recebe seu próprio bloco de Tasks (`superpowers:subagent-driven-development` /
> `superpowers:executing-plans`) no kickoff da fatia, depois da aprovação do CTO. **Nenhum código antes disso.**

**Data:** 2026-08-27 (audit + direção); §14 (kickoff da 3.5.1) preparado 2026-08-27 para retomar 2026-08-28
**Status:** 🟡 Proposta — aguardando aprovação do CTO. Substitui e descarta em definitivo a abordagem
anterior ("aplicar a Foundation às telas restantes"). **A Fatia 3.5.1 está completamente preparada
(§14): pré-auditoria dos 3 arquivos, composição alvo por tela, decisões pendentes, checklist de kickoff
e primeiro passo — pronta para implementar sem re-análise.**

---

## 1. Premissa corrigida da Fase 3.5

A Fase 3.5 **não é uma migração de componentes.** É um redesign visual real do Tier 4 dentro da linguagem
Fluxoly.

```
                 FLUXOLY
                    │
        ┌───────────┴────────────┐
        │                        │
   FOUNDATION              VISUAL LANGUAGE
   tokens                  hierarquia de superfície
   tipografia              respiro / densidade
   componentes (Radix)     Motion intencional
   estados                 theming (Light/Dark como ambientes)
   acessibilidade          grid assimétrico
        │                        │
        └───────────┬────────────┘
                    │
          COMPOSIÇÃO POR TELA
                    │
   cada tela recebe uma composição própria e deliberada,
   adequada à sua função — mesma linguagem, não o mesmo template
```

**Foundation ≠ template.** A Foundation entrega a linguagem técnica e visual. A composição de cada tela
é um problema de Product Design, resolvido tela a tela.

**Regra de design desta fase (vinculante):**

> Nenhuma tela deve ser redesenhada apenas para "ficar consistente". Cada tela recebe uma composição
> deliberada — hierarquia, densidade, superfície e tratamento de dados próprios — mantendo a linguagem
> visual compartilhada do Fluxoly. O resultado esperado: *"isso claramente é Fluxoly"*, nunca *"mais um
> dashboard que uma IA gerou com Tailwind"*.

**Anti-padrão proibido:** `Título → 3 métricas → card → DataTable`, repetido em 12 telas.

### Restrições herdadas (não negociáveis nesta fase)

- `BRAND_IDENTITY.md` é autoridade. Identidade **Pulse** preservada: `#FF3D5A` (assinatura), `#29E0C9`
  (fluxo ao vivo — só indicador positivo/tempo real), wordmark Space Grotesk, ícone de pulso. **Não**
  importar cor/identidade das referências — traduzir só composição, sofisticação, hierarquia, sensação.
- Backend, API, schema, payloads e regras de permissão **intactos**. Escopo 100% apresentação.
- Light + Dark = requisito central desta fase, projetados como dois ambientes (não inversão).
- Acessibilidade (contraste AA nos 2 modos, foco visível, `aria-*`) não é trade-off pela composição.
- Processo `CLAUDE.md` inalterado: **1 PR por fatia → squash merge**, CI 8/8 (×2) + revisão antes do
  merge. Sem fast-forward local (o desvio da Fase 3.4 não se repete).
- Fonte deste audit: brief textual do CTO + `PLAN-design-system-fase3-visual-experience.md` §1–§12 +
  `BRAND_IDENTITY.md` §10 + inspeção do código real das 12 telas. **Imagens de referência não estão
  disponíveis nesta sessão** — se forem anexadas, este audit deve ser revisto contra elas antes da 3.5.1.

---

## 2. Direção visual geral do Fluxoly (Tier 4)

O Tier 4 é onde o produto fecha a linguagem visual. São telas de baixo tráfego, mas é justamente onde o
"tudo parece igual" fica mais visível hoje (todas são `<h1>` + `<table>` cru dentro de
`bg-card rounded-xl border`).

**O que absorver das referências (princípio, não cópia):**

| Princípio | Tradução para o Fluxoly |
|---|---|
| Composição editorial > sidebar+header+card+tabela | Cada tela abre com um "gesto" próprio — um número que importa, um estado do negócio, uma pergunta que a tela responde — não um `<h1>` genérico seguido de tabela. |
| Espaço e hierarquia forte | Respiro de 32–48px ao redor do elemento dominante. Título de página em escala real (Space Grotesk / Onest, 28–32px, 1 por tela). |
| Blocos com personalidade, não caixas idênticas | `Panel` só para o dominante; listas em `ListBlock` (divisor, sem moldura); métricas de apoio como número solto. Nunca 4 `Panel`s iguais lado a lado. |
| Métricas grandes só onde importam | Número hero (40–56px) reservado para 1 dado por tela — e só nas telas que têm um dado assim (Custos: gasto total; Reports: lucro do período). A maioria do Tier 4 **não** tem métrica hero e não deve inventar uma. |
| Gráficos integrados à narrativa | Reports e Custos ganham visualização (série temporal, breakdown por categoria) a partir dos **dados que já existem** — não como "card de gráfico" solto, mas dentro da leitura da tela. |
| Filtros/ações como parte da composição | Barra de filtro ancorada ao dominante ou ao header de conteúdo, não uma faixa cinza empilhada. Ação primária da tela no header de conteúdo. |
| Tipografia como elemento visual | Dado tabular (IMEI, valores, datas) em fonte monoespaçada — regra da Foundation, não acidente por arquivo. Rótulo de coluna em caixa-alta discreta. |
| Cor de assinatura pontual | Máx. 1–2 elementos `#FF3D5A` "vivos" por tela (CTA primário, ou 1 indicador crítico, ou item ativo). Nunca em borda decorativa, ícone em repouso ou fundo. |
| Light/Dark como ambientes | Ver §4. |

**O que garante coerência entre telas** (para não parecerem de designers diferentes): tokens,
tipografia, o header de conteúdo compartilhado (título + ação primária), a linguagem de Light/Dark, o
Motion (só `Reveal` + transição de número + destaque de filtro), e os critérios de aceitação (§11).

---

## 3. Princípios de composição (aplicáveis às 12 telas)

1. **Cada tela declara sua hierarquia.** No audit (§5), toda tela tem: elemento dominante (ou justificativa
   explícita de "sem dominante"), nível secundário, nível de apoio.
2. **Densidade segue a função.** Tela operacional (Backup, ShoppingList, PriceTables) = densa, escaneável.
   Tela analítica (Reports, Custos) = arejada, com respiro entre blocos de leitura.
3. **Superfície comunica peso.** `Panel` (fundo + elevação/borda) só no dominante. Resto: `ListBlock`
   (divisor), `LooseMetric` (sem moldura), texto solto. Nunca "tudo em card".
4. **Estado vazio é composição, não fallback.** `EmptyState` com uma ação clara e uma frase que explica a
   tela — não "Nenhum registro encontrado." centralizado.
5. **Filtro e ação pertencem à tela.** Integrados ao header de conteúdo ou ao painel dominante, não uma
   faixa separada.
6. **Motion mínimo e intencional.** `Reveal` na entrada de conteúdo pós-fetch; transição de número quando
   uma métrica muda; destaque temporário nos resultados que mudaram após um filtro. Nada além disso.

---

## 4. Estratégia Light / Dark (transversal à fase)

Projetados como dois ambientes. Espaçamento e tipografia idênticos; muda a **linguagem de profundidade** e
a calibração de contraste.

| Dimensão | Light | Dark |
|---|---|---|
| `background` | Quase-branco (`#F7F7F8`), reserva o branco puro para superfície | Nível mais fundo, quase-preto |
| `surface` (Panel dominante) | `#FFFFFF`, separado por **sombra sutil**, não borda | `--color-card` atual (`#1F1F1F`), separado por **borda visível** + camada |
| `surface-raised` (dropdown/popover/dialog) | Sombra mais pronunciada | Um degrau mais claro que `surface` |
| bordas | `#EDEDEF`, uso mínimo — preferir sombra | ferramenta principal de separação |
| texto | quase-preto (`#1A1A1A`) + secundário | `#EBEBEB` + 2º nível para título vs. corpo |
| tabelas | linhas separadas por divisor claro; header com leve fundo; zebra opcional só se ajudar leitura | divisor sutil; header destacado por cor de fundo, não por borda dupla |
| gráficos | fundo transparente, grid quase invisível, **linha mais grossa** (compensa ausência de glow) | glow/opacidade sutil no dado ativo/selecionado |
| inputs/select | borda sutil, foco com anel `#FF3D5A` discreto | fundo levemente elevado, foco idem |
| badges (status) | recalibrar tokens `success/warning/destructive/info` para AA em fundo claro | tokens atuais já calibrados para escuro — validar |
| hover (linha de tabela) | fundo `#F2F2F4` | `accent/30` atual |
| seleção / item ativo | faixa/indicador `#FF3D5A` à esquerda + fundo tênue | idem, com glow sutil |

**Requisito:** cada fatia entrega as telas **revisadas nos dois modos como ambientes** — não um screenshot
Light gerado por inversão. QA visual real nos 2 modos quando a extensão do Chrome permitir (limitação
KI-027 conhecida; a 3.6 é o gate final de QA visual global).

---

## 5. Audit individual das 12 telas

Estado atual comum a todas: `<h1>` + (às vezes stats em `bg-card` manuais) + `<table>` cru dentro de
`bg-card rounded-xl border`. Nenhuma usa `Panel`/`ListBlock`/`LooseMetric`/`DataTable`. Produtos e
UnidadesSerializadas já usam `FilterBar`/`Badge`/`EmptyState` (Fase 2) — o resto não.

### 5.1 Cluster "Cadastros de referência" — RepairTypes, TiposGarantia

- **Função:** lista curta e estável de valores de domínio (tipos de reparo; políticas de garantia).
  Baixíssima frequência de escrita. Consumidas por Vendas/OS.
- **Elemento dominante:** nenhum — e não deve inventar um. O "gesto" de abertura é a própria lista, tratada
  com cuidado tipográfico.
- **Hierarquia:** título de página + contagem discreta ("8 tipos de reparo") como apoio → lista → ação
  ("Novo") no header de conteúdo.
- **Composição:** `ListBlock` (não `DataTable` — são listas de 1–3 colunas, não tabelas de dados).
  RepairTypes: uma coluna (nome) + ação inline no hover. TiposGarantia: nome + duração + status (Badge
  ativo/inativo) + editar. Dialogs de criar/editar intactos.
- **Densidade:** média-baixa, linha alta, respiro entre linhas — comunica "poucos itens, cada um importa".
- **Superfícies:** lista sem moldura própria (divisor). Sem `Panel`.
- **Dados:** nome em peso médio; duração/status como apoio.
- **Light:** divisores quase invisíveis, hover claro. **Dark:** divisores sutis, hover `accent/30`.
- **O que torna únicas:** são as telas mais "quietas" do sistema — o design deve abraçar isso (editorial,
  espaçado), não disfarçar de dashboard.
- **O que NÃO fazer:** não colocar métrica hero, não usar `Panel`, não transformar 5 linhas numa
  `DataTable` com header sticky e paginação.

### 5.2 PriceTables (Tabelas de Preço)

- **Função:** matriz preço × serviço × modelo, agrupada por tabela (`ir_phones` etc.), com accordion
  (expand/collapse já existe).
- **Elemento dominante:** a estrutura agrupada em si. Opcionalmente, um resumo no topo ("3 tabelas · 214
  entradas · última alteração há 2 dias") como apoio — sem número hero.
- **Hierarquia:** título → resumo de apoio → grupos colapsáveis (`Panel` leve por grupo, com o nome da
  tabela como `PanelTitle` e a contagem) → dentro de cada grupo, `DataTable` (serviço / modelo / valor /
  remover). Ação "Adicionar Entrada" no header.
- **Composição:** cada grupo é um `Panel` de peso secundário (não dominante — há vários). Valor em fonte
  monoespaçada, alinhado à direita. O accordion vira parte do design, não um `<button>` com chevron cru.
- **Densidade:** alta dentro do grupo (é tabela de consulta), respiro entre grupos.
- **Superfícies:** `Panel` por grupo; tabela interna sem moldura extra.
- **Dados:** valor é o dado-chave — monoespaçado, peso médio, `#FF3D5A` só se houver destaque de "preço
  desatualizado"/edição, senão neutro.
- **Light:** grupos separados por sombra leve. **Dark:** por borda + leve mudança de nível.
- **O que torna única:** é a única tela do tier com estrutura hierárquica real (grupo → linhas). O design
  deve explorar isso — navegação clara entre tabelas, estado colapsado elegante.
- **O que NÃO fazer:** não achatar os grupos numa tabela única gigante; não usar número hero; não deixar o
  accordion parecer um `<details>` do navegador.

### 5.3 Cluster "Catálogo" — Produtos, UnidadesSerializadas

- **Função:** inventário. Produtos = catálogo de modelos/condição. UnidadesSerializadas = unidades físicas
  rastreadas por IMEI, com status e histórico por unidade.
- **Elemento dominante:** **Produtos** — sem número hero, mas a `FilterBar` + a contagem de resultados é o
  centro de controle da tela; o dominante é a **lista filtrável**, tratada como superfície principal.
  **UnidadesSerializadas** — idem, e o **Dialog de detalhe com timeline de eventos** por unidade é o
  momento premium desta tela (merece design cuidadoso: IMEI em destaque monoespaçado, status como Badge,
  histórico como timeline vertical, não tabela).
- **Hierarquia:** título + ação ("Novo Produto" / gated) → barra de filtro integrada → contadores de apoio
  (`LooseMetric`: total / Seminovos / Vitrine — Produtos; total / por status — Unidades) → `DataTable`
  (header sticky, linha clicável abre o detalhe).
- **Composição:** filtro ancorado ao topo da lista (não faixa separada). Contadores como número solto
  acima da tabela. `Badge` semântico para condição/status (já em uso). Timeline de eventos
  (UnidadesSerializadas) redesenhada como sequência vertical com marcadores, dentro do Dialog.
- **Densidade:** alta (é operação de estoque) — linhas compactas, muitas visíveis.
- **Superfícies:** lista sem `Panel`; `Dialog` de detalhe usa `surface-raised`.
- **Dados:** IMEI e valores monoespaçados; status/condição via `Badge`; nome do produto em peso médio.
- **Light:** tabela com header de leve fundo, hover claro. **Dark:** header por cor, glow sutil na linha
  selecionada.
- **O que torna únicas:** rastreabilidade individual (o pilar "Operação" da marca — IMEI). O design deve
  fazer o IMEI e o histórico parecerem primeira-classe, não colunas escondidas.
- **O que NÃO fazer:** não colocar métrica hero de "valor de estoque" aqui (isso é do Stock, Tier 2); não
  transformar a timeline de eventos numa mini-tabela; não deixar o filtro virar faixa cinza empilhada.

### 5.4 Reports — ver §6 (tratamento próprio)

### 5.5 OperationalCosts (Custos Operacionais)

- **Função:** ledger de despesas do negócio, com categoria e data. Admin-only.
- **Elemento dominante:** **sim** — `total` (gasto acumulado) como número hero em `Panel`, com "este mês"
  e a variação como contexto. Mesmo peso do "Saldo" (Financeiro) / "Valor Total" (Stock) no Tier 2.
- **Hierarquia:** `Panel` dominante (gasto total + este mês + mini-série ou breakdown por categoria) →
  `LooseMetric`s de apoio se necessário → `DataTable` de lançamentos (ordenado por data desc).
- **Composição:** o `Panel` dominante integra a leitura: número grande + um breakdown por categoria
  (barra horizontal simples ou lista proporcional, a partir do `groupByCategory` que já existe) + "este
  mês" como sub-métrica. A tabela abaixo é o detalhe. "Novo Custo" no header.
- **Densidade:** dominante arejado; tabela densa.
- **Superfícies:** 1 `Panel`; tabela sem moldura.
- **Dados:** valores monoespaçados; `destructive` reservado para o total e para valores individuais só se
  o CTO quiser sinalizar "saída" (hoje tudo é `text-destructive` — reavaliar: talvez só o total).
- **Light:** `Panel` branco com sombra, breakdown em tons neutros. **Dark:** `Panel` elevado, breakdown
  com barras de baixa opacidade.
- **O que torna única:** é a única tela puramente de "para onde o dinheiro foi" — merece o tratamento de
  narrativa financeira, não de CRUD.
- **O que NÃO fazer:** não pintar a tela inteira de vermelho (viola o princípio 2); não colocar 3 stat
  boxes iguais como hoje; não adicionar cálculos/agregações novas (só visualizar o que já existe).

### 5.6 Garantias

- **Função:** lista de OS finalizadas e seus prazos de garantia, com status (ativa / vencendo / vencida) e
  dias restantes. Leitura, sem escrita.
- **Elemento dominante:** o **estado agregado da carteira de garantias** — quantas vencendo nos próximos
  X dias. Um `Panel` de apoio no topo ("3 garantias vencem esta semana") funciona como alerta, não como
  métrica hero.
- **Hierarquia:** título → faixa de alerta/resumo (vencendo / vencidas) → `DataTable` agrupável por OS
  (o agrupamento visual por OS que já existe no código vira design real: linha-mãe da OS + sub-linhas de
  reparo recuadas).
- **Composição:** `GarantiaBadge` (já existe: vencida/vencendo/ativa) recalibrado para os 2 modos. A
  contagem de "vencendo" usa `#29E0C9`? Não — vencendo/vencida é alerta, usa `warning`/`destructive`.
  `#FF3D5A` só se houver uma ação crítica.
- **Densidade:** média — é consulta, mas o operador escaneia por urgência.
- **Superfícies:** faixa de resumo em `Panel` leve; tabela sem moldura.
- **Dados:** dias restantes é o dado-chave (peso, cor por status); OS em monoespaçado com link.
- **Light:** badges recalibrados AA; faixa de alerta com fundo tênue. **Dark:** badges atuais; faixa com
  borda.
- **O que torna única:** é orientada a **tempo/urgência**, não a volume. O design deve comunicar "o que
  precisa de atenção agora", não só listar.
- **O que NÃO fazer:** não tratar como tabela neutra sem hierarquia de urgência; não inventar número hero
  de "total de garantias"; não usar `#FF3D5A` para "vencida" (é `destructive`).

### 5.7 Users (Usuários)

- **Função:** CRUD de contas do sistema, com perfil (admin/tecnico/vendedor/estoque/financeiro). Admin-only.
- **Elemento dominante:** nenhum — lista pequena. Contagem por perfil como apoio (`LooseMetric` ou uma
  linha de chips: "2 admin · 3 técnicos · 1 financeiro").
- **Hierarquia:** título + "Novo Usuário" → resumo por perfil (apoio) → `ListBlock` ou `DataTable` compacta
  (nome / e-mail / perfil / ações).
- **Composição:** perfil como `Badge` semântico (ver §7 — KI-051). Linha com avatar/inicial opcional para
  dar rosto. Ações no hover.
- **Densidade:** baixa-média.
- **Superfícies:** lista sem moldura.
- **Dados:** e-mail monoespaçado; perfil via `Badge`.
- **Light/Dark:** badges de perfil recalibrados; ver §7.
- **O que torna única:** é sobre **pessoas e permissão** — o design pode dar um toque mais humano (inicial,
  agrupamento por perfil) sem virar rede social.
- **O que NÃO fazer:** não expor hash de senha nem campos sensíveis; não usar `text-purple-400` cru (§7);
  não colocar métrica hero.

### 5.8 Backup

- **Função:** listar, criar, baixar e **restaurar** backups do banco. Admin-only. Tela de operação
  sensível (restore é destrutivo).
- **Elemento dominante:** o **estado do último backup** — "último backup há 3h · 14 backups · 2,1 MB" em
  `Panel`, com a ação "Criar backup agora" ao lado. É o dado que o operador precisa ver ao entrar.
- **Hierarquia:** `Panel` dominante (status + criar) → zona de restauração claramente separada e sinalizada
  (upload de arquivo, com aviso) → `DataTable` de backups (nome / data / tamanho / baixar / restaurar).
- **Composição:** a ação de restaurar tem tratamento visual de "cuidado" — cor de aviso, confirmação
  explícita, separada visualmente das ações rotineiras. `#FF3D5A` pode marcar o botão de restaurar
  (indicador de operação crítica) — é exatamente o uso pontual que o princípio 2 permite.
- **Densidade:** média.
- **Superfícies:** 1 `Panel` (status); zona de restore em `Panel` de aviso; tabela sem moldura.
- **Dados:** timestamps e tamanhos monoespaçados.
- **Light/Dark:** zona de restore com fundo de aviso tênue (Light) / borda de aviso (Dark).
- **O que torna única:** é a única tela onde uma ação pode **destruir dados** — o design tem
  responsabilidade de sinalizar isso sem virar alarme constante.
- **O que NÃO fazer:** **zero mudança no fluxo de restore/upload** (só o invólucro visual); não banalizar
  o restore como "só mais um botão"; não colocar métrica hero de vaidade.

### 5.9 ShoppingList (Lista de Compras)

- **Função:** fila de solicitações de peças, com prioridade, status (PENDENTE→RECEBIDO), responsável.
  Filtros (status / prioridade / produto) + paginação. Alimentada por EditOrder.
- **Elemento dominante:** a **fila por prioridade** — o dominante é a lista, organizada por urgência. Um
  resumo de apoio ("4 urgentes · 12 pendentes") ancora a leitura.
- **Hierarquia:** título → resumo por prioridade/status (apoio) → filtro integrado → `DataTable`
  (prioridade / produto / OS / qtd / status / responsável / data), header sticky, paginação.
- **Composição:** prioridade como `Badge` com escala de urgência (URGENTE / ALTA / NORMAL / BAIXA); status
  como `Badge` de progresso. Ordenação visual por prioridade. `#FF3D5A` só em "URGENTE".
- **Densidade:** alta (é fila de trabalho).
- **Superfícies:** lista sem moldura; filtro ancorado.
- **Dados:** OS em monoespaçado; qtd em peso médio.
- **Light/Dark:** badges de prioridade recalibrados AA nos 2 modos.
- **O que torna única:** é uma **fila de trabalho priorizada**, não um cadastro. O design deve fazer a
  urgência saltar.
- **O que NÃO fazer:** não tratar como tabela neutra sem sinal de prioridade; não perder os filtros/
  paginação atuais; não mexer na lógica de `fetch`.

### 5.10 Compras — ver §9 (dead code)

---

## 6. Reports — experiência analítica própria

Estado atual: 3 abas (IR Phones / Técnicos / Custos Operacionais), filtro de data, botão "Gerar
Relatório" (resultado é `null` até clicar), export PDF, link para Backups. Cada aba renderiza **só
tabelas** — nenhuma visualização, nenhuma comparação temporal, nenhuma hierarquia. Os dados já vêm
agregados por mês (`results.meses`), com totais (`total_lucro` / `total_os` / `total_custos`) e breakdown
por categoria (`results.categorias`).

**É a maior oportunidade de composição do tier.** Tratamento proposto (sem tocar API/cálculos — só
visualizar o que já existe):

| Zona | Proposta |
|---|---|
| **Entrada da tela** | Header de conteúdo + as 3 abas como navegação real entre relatórios (não `<button>`s num pill cinza). Filtro de data + "Gerar" ancorados ao header. Estado inicial (sem `results`): um `EmptyState` que explica o que cada aba mostra, não um vazio. |
| **Resumo executivo (pós-geração)** | 1 `Panel` dominante por aba com **o número que importa** em hero: IR Phones → Lucro do período; Técnicos → Lucro total / melhor técnico; Custos → Custo total do período. Com a variação vs. período anterior **se derivável dos dados já retornados** (senão, sem variação). |
| **Indicadores de apoio** | `LooseMetric` para os secundários (Total OS, Meses, Média) — sem moldura, número + rótulo. |
| **Comparação temporal** | Uma **série temporal** (barra ou linha) a partir de `results.meses` — faturamento/lucro por mês (IR Phones), custo por mês (Custos). Recharts com o tema único (`lib/chart-theme.js`), integrada à leitura, não um "card de gráfico" isolado. Glow no mês ativo (Dark) / linha grossa (Light). |
| **Breakdown** | Custos: `results.categorias` como barra horizontal proporcional (já existe como lista — vira visualização). |
| **Tabelas detalhadas** | Todas migram para `DataTable` (header sticky — as mensais e a de "Lançamentos Individuais" podem ser longas). A tabela de Técnicos (hoje flat) pode agrupar por mês visualmente. |
| **Export** | "Exportar PDF" continua idêntico (chama o mesmo endpoint). |

**Não** é um novo relatório — são os mesmos 3, com os mesmos dados, apresentados como uma central
analítica em vez de um dump de `<table>`. Se durante a implementação a melhor solução visual pedir
reorganizar a composição de uma aba além do descrito aqui, isso é **proposto ao CTO na fatia**, não
decidido unilateralmente nem barrado de antemão.

**O que NÃO fazer:** não criar novos cálculos/agregações/endpoints; não adicionar uma 4ª aba; não
transformar Reports num clone do Dashboard (Dashboard é visão operacional do agora; Reports é análise
histórica com filtro de período — a composição deve refletir essa diferença).

---

## 7. Tratamento do KI-051 (cor do perfil "financeiro" em Users)

Hoje: `perfilColor` mapeia admin→`text-primary`, tecnico→`text-info`, vendedor→`text-success`,
estoque→`text-warning`, financeiro→`text-purple-400` (classe Tailwind crua, sem token Pulse).

**Decisão do CTO:** opção (b) **se** existir um token semântico que sirva; senão, **remover a exceção** e
reusar uma cor semântica já do sistema com boa diferenciação. **Não criar roxo decorativo.**

**Análise:** a paleta Pulse tem `primary` (`#FF3D5A`), `info`, `success`, `warning`, `destructive`,
`#29E0C9` (chart-5 / fluxo ao vivo). Os 4 outros perfis já ocupam primary/info/success/warning.
`destructive` não cabe (semântica de erro). `#29E0C9` é reservado para "indicador positivo/tempo real" —
não é um papel de perfil.

**Proposta:** não há token semântico livre que "signifique financeiro". Duas saídas para o CTO decidir na
Fatia 3.5.6:
- **(b1)** Tratar o perfil não como cor-por-perfil, mas como `Badge` neutro com o rótulo do perfil — todos
  os 5 perfis viram `Badge` de mesma família visual (variação só no texto), eliminando a necessidade de 5
  cores. Mais alinhado a "sem cor sem função semântica" — a informação é o rótulo, não a cor.
- **(b2)** Se o CTO quiser manter cor-por-perfil, "financeiro" reusa `info` ou `success` com um qualificador
  (ícone/peso) para diferenciar de tecnico/vendedor. Menos limpo.

Recomendação: **(b1)** — fecha o KI-051 removendo a premissa de "cada perfil tem uma cor", que é
decoração sem função. Confirmar com o CTO no kickoff da 3.5.6.

---

## 8. Tratamento do KI-056 (`KpiCard.jsx` órfão)

`KpiCard.jsx` ficou sem consumidor desde a Fase 3.2 (Dashboard migrou para `Panel`/`LooseMetric`). Nenhuma
tela do Tier 4 vai usá-lo.

**Decisão do CTO:** deixar para a **Fase 3.6** (cleanup). Não misturar remoção de código estrutural com o
redesign das telas. Registrado aqui, sai da 3.5.

---

## 9. Duplicata ShoppingList × Compras — achado

**Confirmado no código:** `App.jsx` tem **duas rotas para `/compras`**:
```
linha 77: <Route path="/compras" element={<ShoppingList />} />
linha 87: <Route path="/compras" element={<Compras />} />
```
React Router v6 usa a primeira correspondência → **`ShoppingList` é a tela viva; `Compras.jsx` é código
morto inalcançável.** O Sidebar (`Layout.jsx`) só linka `/compras` → "Lista de Compras". `Compras.jsx`
(70 linhas) consome `shoppingList.list()` esperando `data.compras` (shape legado), enquanto `ShoppingList`
espera `res.items` (shape atual) — é um resquício de uma implementação anterior.

**Nesta fase:** só **registrar** (feito aqui). **Não** remover `Compras.jsx` nem a rota duplicada — é
cleanup estrutural, mesma categoria do KI-056, vai para a **Fase 3.6** ou uma tarefa `chore:` própria.
Não alterar comportamento. A Fatia 3.5.6 redesenha **só `ShoppingList`**.

*(Sugestão para a 3.6: remover `Compras.jsx` + a linha 87 de `App.jsx` + o `lazy(() => import("@/pages/Compras"))`.)*

---

## 10. Sequenciamento das fatias / PRs

6 fatias, **1 PR cada → squash merge**, checkpoint arquitetural somente-leitura antes de cada uma,
CI 8/8 (×2) + revisão whole-branch antes do merge. Ordem: do mais simples/isolado ao de maior lift de
design, para calibrar a linguagem antes de Reports.

| Fatia | Telas | Natureza do redesign | Depende de |
|---|---|---|---|
| **3.5.1** | RepairTypes + TiposGarantia + PriceTables | Cadastros de referência — linguagem "editorial quieta" (`ListBlock`) + a matriz agrupada de PriceTables. Primeira consumidora de `DataTable`/`ListBlock` no tier — auditar os componentes por gaps antes. | 3.4 |
| **3.5.2** | Produtos + UnidadesSerializadas | Catálogo — lista filtrável como superfície principal + o Dialog de detalhe/timeline (Unidades) como momento premium. | 3.5.1 |
| **3.5.3** | OperationalCosts | Narrativa financeira — `Panel` dominante (gasto total + breakdown por categoria como visualização) + tabela de detalhe. | 3.5.1 |
| **3.5.4** | Garantias | Tela orientada a tempo/urgência — resumo de "o que vence" + tabela agrupada por OS. | 3.5.1 |
| **3.5.5** | Users + Backup | Administração de sistema — Users (pessoas/permissão, + decisão KI-051) e Backup (estado do último backup como dominante + zona de restore sinalizada). | 3.5.1 |
| **3.5.6** | ShoppingList | Fila de trabalho priorizada — urgência salta. Registra o achado do `Compras.jsx` morto (sem removê-lo). | 3.5.1 |
| **3.5.7** | Reports | Central analítica — resumo executivo + série temporal + breakdown + `DataTable`s. Maior lift; vem por último para herdar a linguagem já calibrada nas 6 anteriores. | 3.5.1–3.5.6 |

*(Nota: são 7 fatias, não 6 — Reports foi separada de tudo por ser o maior lift de design. 3.5.5 pode ser
quebrada em duas se Users+Backup ficarem grandes demais para uma revisão.)*

Depois da 3.5.7: **Fase 3.6** — QA visual global (coerência entre as 4 fases de tela, contraste AA nos 2
modos ao vivo, performance do bundle com Motion/tema, KI-056 + `Compras.jsx` cleanup, KI-052, KI-055).

---

## 11. Critérios de aceitação visual (por fatia)

Uma fatia só é aprovável se **todas** as telas dela cumprem:

1. **Hierarquia declarada e visível** — ≥3 níveis de peso (dominante / secundário / apoio), OU justificativa
   documentada de "sem dominante" (caso de RepairTypes/TiposGarantia/Users).
2. **Anti-template** — nenhuma tela termina como `Título → 3 métricas → card → DataTable` sem que isso
   seja uma decisão de design registrada (e nenhuma das 12 deve terminar assim por inércia).
3. **Cor de assinatura pontual** — no máx. 1–2 elementos `#FF3D5A` "vivos" por tela (fora hover/foco).
   `#29E0C9` só em indicador positivo/tempo real. Zero vermelho em borda decorativa / ícone em repouso /
   fundo de card.
4. **Light e Dark como ambientes** — cada modo revisado contra a tabela do §4 (sombra vs. camada,
   calibração de contraste, tratamento de tabela/gráfico/input/badge). Não inversão.
5. **Contraste AA** nos dois modos, texto e componentes. Foco visível. `aria-*` preservado ou melhorado.
6. **Densidade coerente com a função** (operacional = densa; analítica = arejada). Respiro de 32–48px ao
   redor de qualquer elemento dominante.
7. **Tabelas longas** com header sticky; dado tabular (IMEI/valores/datas) em fonte monoespaçada.
8. **Motion** só: `Reveal` na entrada pós-fetch + transição de número + destaque de filtro. Nada mais.
9. **Estado vazio** é `EmptyState` com ação + frase que explica a tela.
10. **Zero regressão funcional** — nenhuma mudança de endpoint/payload/regra/permissão (confirmado por
    revisão de diff); fluxos de Dialog/AlertDialog/upload (Backup!) idênticos.
11. **Testes** — suíte completa verde (testes novos por tela migrada), `lint` 0 erros, `build` de produção
    sem erro, CI 8/8 (×2) verde no PR.
12. **QA visual real** nos 2 modos quando a extensão do Chrome permitir; senão, documentar a limitação
    (KI-027) e cobrir por revisão de código + testes.

---

## 12. Riscos

| Risco | Mitigação |
|---|---|
| "Redesign autoral" é subjetivo — implementação pode divergir da intenção | Este audit aprovado antes de qualquer código; critérios de aceitação objetivos (§11); revisão whole-branch por fatia; o CTO aprova cada fatia. |
| Telas parecendo de "designers diferentes" entre fatias | Princípios (§3), estratégia Light/Dark (§4) e critérios (§11) são compartilhados; header de conteúdo + Motion + tipografia comuns; **Fase 3.6 faz o QA de coerência global**. |
| Reports vira over-engineering (dashboard dentro de relatório) | Trava: mesmos 3 relatórios, mesmos dados, mesmos endpoints — só visualização e hierarquia; nenhum cálculo novo; sem 4ª aba. |
| Regressão funcional em Backup (restore destrutivo), Dialogs, upload | Composição só no invólucro externo; fluxos e componentes Radix intactos; testes por tela; revisão de diff foca em "nenhuma linha de lógica mudou". |
| Fase longa (12 telas) perde momentum / consistência | 7 fatias independentes, cada uma entregável e mergeável sozinha; ordem calibra a linguagem antes do maior lift (Reports). |
| Light Mode nunca exercitado ao vivo em telas autenticadas (KI-027) | Cada fatia tenta QA real; a 3.6 é o gate final de QA visual global nos 2 modos; a estratégia do §4 reduz achados tardios. |
| `Compras.jsx` morto — risco de mexer sem querer, ou de "aproveitar e remover" | Registrado (§9); remoção é decisão à parte (3.6 / `chore:`); a 3.5.6 toca só `ShoppingList`. |
| `DataTable`/`ListBlock` podem ter gaps (como `getRowProps`/KI-053 na 3.3.1) | 3.5.1 é a primeira consumidora no tier — auditar os componentes e corrigir gaps lá, em commit separado, antes de escalar. |
| KI-051: (b1) muda a UX de Users (perfil sem cor) | É uma decisão de design consciente (cor sem função = decoração); confirmada com o CTO no kickoff da 3.5.5. |

---

## 13. Gate de aprovação

**Nenhum código, componente, página, dependência ou PR antes de:**
1. O CTO aprovar este audit + plano (§1–§12), com ou sem ajustes.
2. Para cada fatia: kickoff com bloco de Tasks detalhado + checkpoint arquitetural somente-leitura +
   aprovação do CTO das decisões de composição específicas daquela fatia.

Este documento substitui qualquer versão anterior do plano da Fase 3.5. A abordagem de "migração de
componentes" está **descartada**.

---

## 14. Kickoff da Fatia 3.5.1 — detalhamento (preparado 2026-08-27, para retomar 2026-08-28)

> **Objetivo desta seção:** amanhã começamos a implementar a 3.5.1 direto, sem gastar sessão descobrindo
> estrutura ou rediscutindo direção. Tudo abaixo é preparação — **nenhum código foi escrito**.

### 14.1 Escopo e objetivo visual da 3.5.1

**Telas:** `RepairTypes.jsx`, `TiposGarantia.jsx`, `PriceTables.jsx` — os "cadastros de referência" do
sistema (valores de domínio consumidos por OS/Vendas: tipos de reparo, políticas de garantia, tabela de
preços).

**Objetivo visual da fatia:** estabelecer a linguagem "cadastro editorial" do Fluxoly — telas quietas,
espaçadas, com cuidado tipográfico, que **não fingem ser dashboards**. É a fatia mais simples do tier de
propósito: calibra `ListBlock`/`DataTable`/`Panel` e a estratégia Light/Dark antes das telas de maior
lift. É também a **primeira consumidora de `ListBlock` e `DataTable` no Tier 4** — qualquer gap nesses
componentes é corrigido aqui, em commit separado (precedente: `getRowProps`/KI-053 na Fatia 3.3.1).

### 14.2 Pré-auditoria dos arquivos (estado atual — 2026-08-27)

| Arquivo | Linhas | Estrutura atual | API | Guarda de perfil | Testes |
|---|---|---|---|---|---|
| `frontend/src/pages/RepairTypes.jsx` | 184 | `<h1>`+subtítulo / botão "Novo Reparo" (admin) ou aviso `Lock` / loading (`Loader2`) → empty (`bg-card` centralizado) → `<table>` cru 1 col (Nome) + ações no hover / `Dialog` criar-editar / `AlertDialog` excluir | `reparos.list()`→`{ok,reparos:[]}`, `.create`, `.update`, `.delete` | escrita = admin; leitura = qualquer | **não existe** |
| `frontend/src/pages/TiposGarantia.jsx` | 186 | idem RepairTypes / `<table>` cru 3 col (Nome / Duração / Status via `<span>` badge manual) + editar (sem excluir) / só `Dialog` (sem AlertDialog) | `tiposGarantia.list(params)`→`{ok,items:[]}`, `.create`, `.update` — **sem delete** (desativa via `ativo=false`) | idem | **não existe** |
| `frontend/src/pages/PriceTables.jsx` | 247 | `<h1>` / botão "Adicionar Entrada" / loading → 2 grupos fixos (`ir_phones`, `clientes`) em `bg-card rounded-xl`, cada um com header (`<h2>` + contagem) e lista de serviços; cada serviço é um `<button>` accordion (`ChevronDown/Right`) que expande um `<table>` cru (Modelo / Preço em `text-primary` / excluir) / `Dialog` adicionar (Tabela+Serviço+Modelo selects, Preço) / `AlertDialog` remover | `precos.list()`→`{ok,tabelas:{[id]:{[servico]:{[modelo]:valor}}}}`, `precos.save({tabela,servico,modelo,valor})`, `precos.remove({tabela,servico,modelo})`; `reparos.list()` (select de serviço), `constantes.get()`→`iphone_models` (select de modelo) | escrita+leitura = admin (não-admin vê `Lock`) | **não existe** |

**Shapes de dados confirmados:**
- `reparos`: `[{ id, nome }]`
- `tiposGarantia`: `[{ id, nome, duracao_meses, ativo }]` — `duracao_meses === 0` = "sem garantia"; `list({ incluir_inativos: 1 })` para admin
- `precos`: `tabelas[tabelaId][servico][modelo] = valor(number)` — 2 tabelas fixas em `TABELAS` (`ir_phones`/`clientes`), serviços e modelos são chaves dinâmicas

**Nenhum dos 3 arquivos tem teste.** A 3.5.1 precisa **criar** `RepairTypes.test.jsx`,
`TiposGarantia.test.jsx`, `PriceTables.test.jsx` (template: `pages/Stock.test.jsx` — vitest,
`vi.mock("@/api/client")`, `vi.mock("sonner")`, `vi.mock("@/contexts/AuthContext")`, `render` + `waitFor`).

### 14.3 Inventário de componentes disponíveis (API exata)

| Componente | Import | API |
|---|---|---|
| `Panel` | `@/components/ui/panel` | `Panel` = `Card` + `shadow-sm`. `PanelHeader`/`PanelTitle`/`PanelDescription`/`PanelContent` (aliases de `Card*`). Borda+sombra sempre. |
| `ListBlock` / `ListBlockItem` | `@/components/ui/list-block` | `ListBlock` = `<div className="divide-y divide-border">`. `ListBlockItem` = flex row `items-center justify-between gap-3 py-3`; prop `interactive` adiciona hover/foco (`interactiveRowClassName`). |
| `LooseMetric` | `@/components/ui/loose-metric` | `{ label, value, className, valueClassName, labelClassName }`. Value `text-2xl font-bold text-card-foreground`; label `text-xs text-muted-foreground`. Para "contagem de apoio" menor, passar `valueClassName="text-base font-semibold"`. |
| `DataTable` | `@/components/ui/data-table` | `{ columns: [{ key, header, render?(row), className?, headerClassName? }], rows, getRowKey(row), getRowProps?(row), stickyHeader?, onRowClick?, className? }`. Já envolve em `overflow-x-auto rounded-xl border border-border`. Linha: Enter+Espaço quando `onRowClick`. |
| `EmptyState` | `@/components/ui/empty-state` | `{ icon?, title, description?, action?, className? }`. Ícone Phosphor `Tray` por default; envolve em `Card`. |
| `Badge` | `@/components/ui/badge` | variantes semânticas `success`/`warning`/`error`/`info`/`neutral` + `tag` (taxonômico). Já usado em Produtos/Unidades. |
| `FilterBar`/`FilterSelect`/`FilterInput` | `@/components/ui/filter-bar` | composição visual de filtro (sem lógica). 3.5.1 não tem filtro — não usar. |
| `Reveal` | `@/components/ui/reveal` | Motion de entrada pós-fetch. Uso opcional, discreto. |

Tokens de tema, tipografia (`.font-wordmark` = Space Grotesk; corpo = `system-ui`), `formatCurrency`
(`@/lib/constants`), `interactiveRowClassName` (`@/lib/interaction`), `cn` (`@/lib/utils`) — já existem.

### 14.4 Plano por tela (3.5.1)

#### RepairTypes.jsx

- **Objetivo visual:** o cadastro mais "quieto" do sistema — uma lista curta e legível, tratada como
  conteúdo editorial, não como grid de dados.
- **Hierarquia:** (1) header de conteúdo: título `Tipos de Reparo` + subtítulo + ação "Novo Reparo"
  (admin) / aviso `Lock` (não-admin); (2) apoio: contagem discreta ("N tipos"); (3) corpo: a lista.
- **Composição:** `ListBlock` + `ListBlockItem` (`interactive` no hover). Cada item: nome (peso médio,
  `text-card-foreground`) à esquerda; ações (editar/excluir, `Button variant="ghost" size="icon"`)
  reveladas no hover à direita. Sem `Panel`, sem `DataTable`, sem moldura de card ao redor da lista.
- **Light/Dark:** Light — divisores `border-border` quase invisíveis, hover `bg-muted`/`accent` claro,
  respiro vertical generoso (`py-3`→considerar `py-3.5`); Dark — divisores sutis mas visíveis, hover
  `accent/30`. Nenhuma sombra (não há `Panel`).
- **Componentes:** `ListBlock`/`ListBlockItem`, `EmptyState` (ícone: um Phosphor de ferramenta —
  `Wrench`/`Toolbox`), `Button`, `Dialog`/`AlertDialog` (intactos), `Loader2` ou um skeleton de lista.
- **Criar especificamente:** `RepairTypes.test.jsx`; ícone de `EmptyState` adequado; possivelmente um
  skeleton de lista curto (3–4 linhas) em vez do `Loader2` centralizado, para casar com a composição.
- **NÃO mudar:** `reparosApi` (list/create/update/delete); o fluxo de `Dialog`/`AlertDialog`; o payload
  `{ nome }`; a guarda `isAdmin`; o comportamento de `handleDelete` (remove local + toast).
- **Critérios (além dos gerais §11):** a lista lê como conteúdo, não como tabela; 0 uso de `Panel`/
  `DataTable`; ação só no hover (ou sempre visível se decisão do CTO — ver §14.5); AA nos 2 modos.

#### TiposGarantia.jsx

- **Objetivo visual:** igual RepairTypes (mesma família "cadastro editorial"), com 2 atributos extras
  (duração, status ativo/inativo) integrados à linha sem virar tabela.
- **Hierarquia:** header (título `Tipos de Garantia` + subtítulo + "Novo Tipo"/`Lock`) → apoio (contagem;
  opcionalmente "N ativos") → lista.
- **Composição:** `ListBlock`/`ListBlockItem`. Linha: nome à esquerda; à direita, um grupo com duração
  (`text-sm text-muted-foreground` — "12 meses" / "Sem garantia") + `Badge` de status
  (`variant="success"` ativo / `variant="neutral"` inativo — substitui o `<span>` manual atual, linhas
  122–127) + ação editar (hover). Sem coluna de "excluir" (a API não tem delete — desativa via `ativo`).
- **Light/Dark:** idem RepairTypes; `Badge` recalibrado (o `Badge` semântico já trata os 2 modos).
- **Componentes:** `ListBlock`/`ListBlockItem`, `Badge`, `EmptyState` (ícone: `ShieldCheck`), `Button`,
  `Dialog` (intacto — inclui o `Checkbox` "Ativo" só no modo edição), skeleton opcional.
- **Criar:** `TiposGarantia.test.jsx`; ícone `EmptyState`.
- **NÃO mudar:** `tiposGarantiaApi` (list/create/update); a ausência de delete; `list({ incluir_inativos: 1 })`
  para admin; a validação `duracao_meses >= 0`; o texto "0 representa sem garantia"; o `Dialog`.
- **Critérios:** status via `Badge` semântico (não `<span>` manual); duração legível sem coluna dedicada;
  mesma linguagem visual de RepairTypes (o CTO deve reconhecer que são "irmãs"); AA nos 2 modos.

#### PriceTables.jsx

- **Objetivo visual:** a única tela do tier com estrutura hierárquica real (tabela → serviço → modelos).
  O design deve tornar a navegação entre as 2 tabelas e os serviços clara e elegante — não um
  `<details>` de navegador.
- **Hierarquia:** header (título `Tabelas de Preço` + subtítulo + "Adicionar Entrada") → apoio (resumo
  global: "2 tabelas · N entradas") → 2 grupos de tabela, cada um um `Panel` de **peso secundário**
  (há 2 — nenhum é "o dominante"): `PanelHeader` com `PanelTitle` (nome da tabela) + contagem; dentro,
  a lista de serviços.
- **Composição:** cada serviço continua um item colapsável (`ListBlockItem interactive` como o "trigger"
  do accordion — chevron + nome + contagem de modelos), e ao expandir mostra um `DataTable` compacto
  (colunas: Modelo / Preço / ação-remover). `stickyHeader` não necessário (listas curtas). Preço em
  fonte monoespaçada, alinhado à direita.
- **Light/Dark:** Light — os 2 `Panel`s separados por sombra sutil; Dark — por borda + leve nível.
  `DataTable` interno: header com leve fundo (Light) / cor de fundo (Dark).
- **Componentes:** `Panel`/`PanelHeader`/`PanelTitle`/`PanelContent`, `ListBlock`/`ListBlockItem`,
  `DataTable`, `EmptyState` por tabela vazia (ícone: `CurrencyDollar`/`Tag`), `Dialog`/`AlertDialog`
  (intactos), `ChevronDown/Right` (mantidos como indicador de accordion).
- **Criar:** `PriceTables.test.jsx`; a ponte accordion↔`DataTable` (o `DataTable` não tem modo
  "aninhado" — o accordion abre/fecha a renderização do `DataTable`, controlado pelo `expanded` state
  atual, que não muda).
- **NÃO mudar:** `precosApi` (list/save/remove); os shapes (`tabelas[id][servico][modelo]`); os 2
  ids fixos em `TABELAS`; o `expanded` state e `toggleExpand`; o `Dialog` de adicionar (selects de
  serviço via `reparos`, modelo via `constantes.iphone_models`); `handleAdd`/`handleDelete`; `.toUpperCase()`
  no serviço.
- **Critérios:** navegação entre tabelas/serviços clara; accordion não parece `<details>` cru; preço
  monoespaçado; 0 `<table>` cru remanescente; AA nos 2 modos; skeleton/loading coerente com a composição.

### 14.5 Decisões de design pendentes (para o CTO no kickoff da 3.5.1 — **não resolver sozinho**)

1. **`ListBlock` vs `DataTable` para RepairTypes/TiposGarantia.** O audit propõe `ListBlock` (são listas
   de 1–3 colunas, não tabelas de dados). Alternativa: `DataTable` para consistência com as telas de
   catálogo. **Recomendação: `ListBlock`** — mas é decisão de composição do CTO.
2. **Ações inline: só no hover ou sempre visíveis?** Hoje RepairTypes/TiposGarantia revelam editar/excluir
   no hover (via CSS). Em telas de baixo volume, ação sempre visível pode ser mais clara. **Recomendação:
   manter hover** (menos ruído visual), mas confirmar.
3. **Preço em PriceTables: `#FF3D5A` ou neutro?** Hoje todo preço usa `text-primary` (a cor de assinatura).
   O princípio 2 (§3) diz "cor de assinatura pontual, não decoração" — todo preço em vermelho viola isso.
   **Recomendação: preço neutro** (`text-card-foreground`, peso médio, monoespaçado), `#FF3D5A` reservado
   para um estado futuro ("preço desatualizado"). Mudança visível — CTO decide.
4. **Grupos de tabela em PriceTables: `Panel` ou `ListBlock`?** São 2 grupos fixos. `Panel` (secundário)
   dá presença; `ListBlock` é mais leve. **Recomendação: `Panel` secundário** — a tela precisa de alguma
   estrutura de container para separar "IR Phones" de "Clientes". CTO decide.
5. **Skeleton de loading:** trocar o `Loader2` centralizado por skeleton de lista nas 3 telas? Casa melhor
   com a composição, mas é escopo adicional. **Recomendação: sim, skeleton curto** — barato e melhora a
   percepção. CTO decide se entra na 3.5.1 ou fica para a 3.6.

Nenhuma dessas é bloqueio absoluto — a 3.5.1 pode começar pela pré-auditoria/testes enquanto o CTO
responde. Mas as decisões 1, 3 e 4 mudam a composição entregue e devem ser respondidas antes do commit
de composição.

### 14.6 Dependências / inconsistências / bloqueios registrados

| Item | Natureza | Impacto na 3.5.1 | Ação |
|---|---|---|---|
| `ListBlock`/`DataTable` sem consumidor no Tier 4 | dependência | possível gap só descoberto no uso (precedente: `getRowProps`/KI-053) | 1º passo da 3.5.1 é o checkpoint arquitetural somente-leitura desses componentes; gap → commit de correção separado antes da composição |
| 3 telas sem teste | dependência | critério §11.11 exige suíte verde com testes novos | criar os 3 `*.test.jsx` como 1ª tarefa de cada tela (RED/GREEN por comportamento preservado) |
| Decisões de design 1/3/4 (§14.5) | decisão pendente (CTO) | mudam a composição entregue | responder no kickoff, antes do commit de composição |
| `LooseMetric` value fixo em `text-2xl` | inconsistência menor | "contagem de apoio" ficaria grande demais | usar `valueClassName` override, ou não usar `LooseMetric` para a contagem (texto solto) |
| KI-027 (QA visual ao vivo) | limitação conhecida | Light Mode não verificável ao vivo com sessão autenticada | cobrir por teste + revisão de código; QA visual real onde a extensão permitir; gate final na 3.6 |
| `Badge` — 3 receitas de "badge suave" coexistindo (nota `ENGINEERING_GUIDE` §3.4) | dívida pré-existente | TiposGarantia deve usar `Badge` (não `<span>` manual) — consolidar aqui | usar sempre `Badge`; não criar 4ª receita |

**Nenhum bloqueio impede começar a 3.5.1 amanhã.** As decisões pendentes são de composição, não de
viabilidade, e podem ser respondidas no kickoff sem custo de sessão.

### 14.7 Checklist de kickoff da 3.5.1 (fluxo `CLAUDE.md` + gates do projeto)

- [ ] **1. Branch:** `git checkout main && git pull --ff-only && git checkout -b feat/design-system-fase3.5.1-cadastros-referencia`
- [ ] **2. Aprovação do CTO** deste plano (§1–§14) — sem isso, não prosseguir.
- [ ] **3. Responder as decisões de design pendentes** (§14.5, itens 1/3/4 no mínimo).
- [ ] **4. Checkpoint arquitetural somente-leitura** de `ListBlock`/`ListBlockItem`/`DataTable`/`Panel` —
      confirmar que suportam os usos da §14.4 sem alteração; se houver gap, corrigir em **commit próprio**
      (`fix(design-system): <gap>`) antes de qualquer composição.
- [ ] **5. Bloco de Tasks detalhado** da 3.5.1 (via `superpowers:subagent-driven-development` ou
      `superpowers:executing-plans`) — 1 tela por vez, ordem: RepairTypes → TiposGarantia → PriceTables.
- [ ] **6. Por tela:** criar `*.test.jsx` cobrindo o comportamento atual (RED se aplicável / GREEN) →
      implementar a composição → testes verdes → `npm run lint` 0 erros → `npm run build` ok.
- [ ] **7. Commits atômicos:** composição e (se houver) correção de componente em commits separados;
      nunca misturar. Conventional Commits (`feat(design-system): ...`).
- [ ] **8. Revisão whole-branch** antes do merge (precedente 3.3/3.4: revisor dedicado, achados
      Important corrigidos antes do merge).
- [ ] **9. QA visual** nos 2 modos onde a extensão do Chrome permitir; documentar a limitação (KI-027) se
      não for possível.
- [ ] **10. PR → CI 8/8 (×2) verde → squash merge** (sem fast-forward local).
- [ ] **11. Docs:** `CHANGELOG.md` (entrada da 3.5.1), `PROJECT_STATUS.md` (seção da fatia +
      "Última revisão"), `KNOWN_ISSUES.md` se algum KI mudar, e marcar a 3.5.1 como concluída neste plano.
- [ ] **12. Próxima fatia:** só após merge + docs.

### 14.8 Primeiro passo, amanhã

**Assim que o CTO aprovar este plano:** criar a branch `feat/design-system-fase3.5.1-cadastros-referencia`
e fazer o **checkpoint arquitetural somente-leitura** de `ListBlock`/`ListBlockItem`/`DataTable`/`Panel`
contra os usos da §14.4 (item 4 do checklist). Em paralelo, o CTO responde as decisões de design
pendentes (§14.5). Depois: bloco de Tasks e implementação de `RepairTypes.jsx` (1ª tela), começando pelo
`RepairTypes.test.jsx`.

Nenhuma re-análise necessária — este documento tem o estado atual dos 3 arquivos, os shapes de dados, a
API dos componentes, a composição alvo por tela, o que não mudar e os critérios.

---

## Ver também

- `docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md` — direção geral (§1–§12),
  princípios de composição, Light/Dark, §0.1 (liberdade criativa), §0.2 (identidade Pulse).
- `docs/company/BRAND_IDENTITY.md` §10 — identidade visual (autoridade).
- `docs/engineering/ENGINEERING_GUIDE.md` §3.4/§3.5 — Foundation v2 e o que a Vitrine (3.2) estabeleceu.
- `docs/engineering/plans/PLAN-design-system-fase3.3-operacao.md` / `…fase3.4-formularios.md` — precedentes
  de execução (subagent-driven-development, revisão whole-branch, PR+squash por fatia).
- `docs/operations/KNOWN_ISSUES.md` — KI-027 (QA visual), KI-051, KI-052, KI-055, KI-056.
