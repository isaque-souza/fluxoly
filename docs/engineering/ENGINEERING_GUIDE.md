# ENGINEERING_GUIDE.md — Constituição Técnica

Este documento define os padrões, princípios e convenções que governam o desenvolvimento do Fluxoly Platform.
Ele muda raramente — apenas quando uma decisão arquitetural fundamental é revisada.
Quando houver conflito entre este documento e qualquer outro, este prevalece.

**Última revisão:** 2026-07-08

---

## 1. Princípios Gerais

### SOLID aplicado a este projeto

**S — Single Responsibility**
Cada módulo Flask (`irflow_*.py`) tem um domínio. Nenhuma função de negócio deve vazar entre módulos.
`irflow_os.py` cuida de OS. `irflow_storage.py` cuida de backup. Não misture.

**O — Open/Closed**
Novos tipos de reparo, novos modelos, novos status: adicione via dados (banco), não via código novo.
Evite `if modelo == "X"` espalhados. Use tabelas de configuração.

**L — Liskov Substitution**
Não aplicável diretamente — sem hierarquia de classes. O equivalente aqui: qualquer endpoint que receba
`os_id` deve funcionar com qualquer OS válida, sem casos especiais por tipo ou status.

**I — Interface Segregation**
No frontend: componentes recebem apenas as props que usam. Não passe objetos inteiros quando apenas um campo é necessário.

**D — Dependency Inversion**
Backend: lógica de negócio (`irflow_os.py`) não deve importar diretamente o banco — acessa via funções utilitárias.
Meta para Sprint 4: separar a camada de acesso a dados.

### DRY — Don't Repeat Yourself

- Constantes de status (`EM_ANDAMENTO`, `FINALIZADO`, etc.) vivem em `irflow_core.py`. Nunca redefina em outro lugar.
- Lógica de auto-preenchimento de preço tem um único ponto de verdade: `GET /api/precos/sugerir`.
- No frontend: lógica de negócio repetida em duas páginas → extrair para hook em `src/hooks/`.

### KISS — Keep It Simple, Stupid

- Se uma função tem mais de 40 linhas, pergunte se ela faz duas coisas.
- Se um componente React tem mais de 200 linhas, provavelmente deve ser decomposto.
- Prefira SQL direto com `sqlite3` a ORMs para este projeto — a camada de banco é simples e legível.
- Prefira `if/else` explícito a lógica condicional comprimida em uma linha quando o código é de negócio crítico.

---

## 2. Stack Tecnológica

| Camada | Tecnologia | Versão | Decisão |
|--------|-----------|--------|---------|
| Backend | Flask | >=3.0,<4 | — |
| Servidor WSGI | Gunicorn | >=21,<22 | — |
| Banco de dados | SQLite (WAL mode) | — | ADR-003 |
| Frontend framework | React | ^19 | ADR-001 |
| Build tool | Vite | ^8 | ADR-001 |
| UI components | Radix UI | ^1 | ADR-001 |
| Composição de UI | shadcn/ui (componentes em `components/ui/`, sem pacote npm) | — | ADR-001 (amendment 2026-08-16) |
| Ícones (componentes novos) | Phosphor Icons | ^2 | ADR-001 (amendment 2026-08-16) — coexiste com `lucide-react`, sem migração retroativa |
| Estilização | Tailwind CSS | ^4 | — |
| Gráficos | Recharts | ^3 | — |
| Testes E2E | Playwright | ^1.55 | — |
| Testes backend | pytest | >=8.0 | — |
| Lint backend | Ruff | >=0.5 | Sprint 2 |
| Lint frontend | ESLint | ^9 | — |
| Deploy | Render (backend) + Vercel (frontend) | — | — |

**Antes de adicionar qualquer nova dependência:**
1. Verifique se o problema não pode ser resolvido com o que já existe.
2. Avalie tamanho, manutenção e licença.
3. Adicione ao `requirements-dev.txt` se for dev-only, `requirements.txt` se for produção.
4. Documente a razão no PR.

---

## 3. Padrões Backend (Flask / Python)

### Estrutura de módulos

```
app.py                       — inicialização, schema DB, registro de blueprints
irflow_core.py               — constantes, utilitários compartilhados
irflow_blueprints_api.py     — endpoints REST (a ser decomposto na Sprint 4)
irflow_blueprints_auth.py    — autenticação
irflow_os.py                 — lógica de negócio de OS
irflow_reports.py            — geração de relatórios e PDF
irflow_storage.py            — backup e Google Drive
irflow_mercadophone.py       — integração externa MercadoPhone
irflow_price_tables.py       — lógica de tabela de preços
irflow_reference_data.py     — dados de referência (modelos, cores, técnicos)
```

**Regra:** não crie um novo arquivo `irflow_*.py` sem decisão explícita. Se a lógica é pequena, adicione ao módulo de domínio existente.

### 3.1 Convenção para domínios novos

Esta seção define a estrutura obrigatória para **qualquer domínio de negócio novo** adicionado ao sistema
a partir desta revisão (ex.: Vendas, Caixa, Financeiro). Não se aplica retroativamente aos domínios
existentes listados em `docs/engineering/DOMAIN_MODEL.md` — esses seguem seu próprio plano de decomposição (ADR-002,
Sprint 4).

**Motivação:** sem uma convenção fixada antes da primeira linha de código, cada domínio novo inventa sua
própria organização de pastas durante a sprint em que nasce — o que gera divergência silenciosa entre
módulos e o mesmo tipo de dívida técnica já registrada em TD-01/KI-003 (mas dessa vez em código novo,
sem justificativa de "legado").

**Camadas obrigatórias, nesta ordem de dependência:**

```
controller   — camada HTTP (blueprint Flask). Recebe request, valida entrada, chama service, formata resposta.
                Nunca contém regra de negócio nem acessa o banco diretamente.

service      — regra de negócio pura do domínio. Não conhece Flask, request ou jsonify.
                É o que se testa com testes unitários rápidos, sem subir um servidor.

repository   — único ponto de acesso ao banco para o domínio (queries SQL parametrizadas,
                seguindo o padrão da seção "Acesso ao banco" abaixo). Service nunca executa SQL direto.

tests        — um arquivo de teste por camada relevante (ex.: test_vendas_service.py,
                test_vendas_api.py), seguindo `docs/engineering/TESTING.md`.

README        — um README.md curto (10-20 linhas) na pasta do domínio: o que o domínio faz,
                quais tabelas usa, quais domínios ele depende/é dependido por.
```

**Onde isso vive fisicamente:** enquanto o projeto não migrar para uma pasta por domínio (`domains/vendas/`,
`domains/estoque/`, etc. — fora de escopo desta revisão), a convenção de nomes de arquivo é:

```
fluxoly_<dominio>_controller.py    (ou blueprint dentro de fluxoly_blueprints_<dominio>.py)
fluxoly_<dominio>_service.py
fluxoly_<dominio>_repository.py
```

**Prefixo `fluxoly_` vs. `irflow_` (ADR-008, 2026-07-27):** todo domínio **novo** a partir desta decisão
nasce com o prefixo `fluxoly_` (nome da marca), não `irflow_` (nome legado). Domínios já existentes
(`irflow_clientes_*.py`, `irflow_produtos_*.py`, `irflow_unidades_serializadas_*.py`, `irflow_os.py`,
`irflow_blueprints_api.py`, etc.) **não são renomeados** por esta decisão — permanecem `irflow_*` até
um futuro Épico de Rebranding Técnico (não escopado). A convenção de camadas acima (controller → service
→ repository → tests → README) é a mesma para os dois prefixos — só o nome muda, nunca a estrutura.

**Primeira aplicação real (2026-07-27):** Vendas MVP (`fluxoly_vendas_controller.py`/`_service.py`/
`_repository.py`, `docs/product/features/VENDAS.md`) é o primeiro domínio a nascer com o prefixo novo.

**Adendo — README de domínio sem pasta própria (registrado em 2026-07-11, primeira aplicação real desta
seção):** o item "README" das camadas obrigatórias acima pressupõe uma pasta de domínio (`domains/vendas/README.md`),
que não existe neste layout flat-file. Interpretação aplicada em Clientes (`irflow_clientes_service.py`)
e `estoque_unidades` (`irflow_estoque_unidades_service.py`, renomeado para
`irflow_unidades_serializadas_service.py` na migração ADR-007), primeiros domínios a seguir esta convenção
de fato: o "README curto" vira um **bloco de docstring no topo do arquivo `_service.py`** — mesma
informação (responsabilidade, tabelas usadas, dependências), sem arquivo separado. Usar este padrão para
qualquer domínio novo enquanto o projeto não migrar para pasta por domínio.

**Regra de reuso entre domínios:** se um domínio novo precisa de uma regra que já existe em outro
domínio (ex.: Vendas precisa dar baixa em estoque), ele **importa o service do domínio dono**, nunca
duplica a lógica nem acessa a tabela do outro domínio diretamente. Exemplo concreto já identificado:
a lógica de movimentação de estoque (`registrar_movimentacao`, `consumir_peca_da_os`, `_consumir_lotes_fifo`
em `irflow_os.py`) é a candidata natural a virar `irflow_estoque_service.py` — OS, Vendas e Compras
devem consumir esse mesmo service, nunca reimplementar a baixa de estoque cada um à sua maneira.

**Regra de dependência entre camadas de domínios diferentes (inegociável):** um domínio nunca importa
ou chama o `repository` de outro domínio, mesmo que pareça mais rápido no momento. A única porta de
entrada para o dado de outro domínio é o `service` dele.

```
❌ ERRADO
VendaRepository  ──▶  EstoqueRepository     (acesso direto a dado de outro domínio, sem passar pela regra de negócio dona)

✔ CORRETO
VendaService  ──▶  EstoqueService  ──▶  EstoqueRepository
```

**Por que isso importa:** se `repository` de um domínio pode ser chamado por qualquer outro, a regra
de negócio de quem é dono do dado (ex.: validação de saldo antes de dar baixa, atualização de custo
médio) passa a poder ser contornada por quem chamou direto o banco — o mesmo tipo de acoplamento oculto
que hoje já existe entre `irflow_os.py` e `irflow_blueprints_api.py` (TD-01) e que a convenção de
domínios existe justamente para não repetir em código novo.

Ver `docs/engineering/DOMAIN_MODEL.md` para o inventário de domínios existentes e seu estado atual de camadas.

### Padrão de endpoint REST

Todos os endpoints seguem este padrão de resposta:

```python
# Sucesso
return jsonify({"data": ..., "message": "..."}), 200

# Recurso criado
return jsonify({"data": ..., "id": novo_id}), 201

# Erro de validação (input inválido)
return jsonify({"error": "Descrição do problema"}), 400

# Não autenticado
return jsonify({"error": "Não autenticado"}), 401

# Sem permissão
return jsonify({"error": "Sem permissão"}), 403

# Recurso não encontrado
return jsonify({"error": "OS não encontrada"}), 404

# Erro interno
return jsonify({"error": "Erro interno"}), 500
```

**Nunca retornar stack traces em produção.** Sempre logar o erro e retornar mensagem genérica.

**Entrada numérica sempre por `fluxoly_validation.parse_float` / `parse_int`** — nunca `float()`/`int()`
direto no valor do request. Os dois devolvem `None` para entrada inválida, inclusive `Infinity`, `NaN` e
números que estouram o float (`1e400`), e o controller transforma `None` em 400. Campo opcional precisa
distinguir "ausente" de "inválido" (ver `fluxoly_produtos_controller.py`, `preco_custo`). Na saída,
`JSONProviderFinito` (`app.json`) garante que nenhuma resposta saia com `Infinity`/`NaN` — é rede de
segurança para dado antigo, não substitui a validação de entrada (P1-1/KI-065).

### Acesso ao banco

```python
# Padrão obrigatório para conexão
conn = get_db_connection()   # função em app.py ou irflow_core.py
cursor = conn.cursor()
try:
    cursor.execute("SELECT ...", (param,))
    conn.commit()
finally:
    conn.close()

# Nunca construir SQL com f-string ou concatenação de strings
# ERRADO:
cursor.execute(f"SELECT * FROM os WHERE cliente = '{nome}'")  # SQL injection

# CORRETO:
cursor.execute("SELECT * FROM os WHERE cliente = ?", (nome,))
```

### Variáveis de ambiente

- Sempre ler via `os.environ.get("VAR", "default")` — nunca hardcodar valores de produção.
- Todos os defaults devem ser seguros para desenvolvimento local.
- Toda nova variável deve ser adicionada imediatamente ao `.env.example` com comentário.
- Segredos (`FLASK_SECRET_KEY`, tokens, senhas) **nunca** têm valor padrão real — apenas placeholder `change-me`.

### Autenticação e sessão

- Sessões via Flask session (cookie assinado com `FLASK_SECRET_KEY`).
- Toda rota protegida verifica `session.get("usuario_id")` antes de qualquer operação.
- Rotas admin verificam `session.get("perfil") == "admin"`.
- A verificação de autenticação é feita no início da função, antes de qualquer acesso ao banco.

---

## 3.2 Fluxoly Design System (Fase 1 — Fundação)

Formalizado em `docs/engineering/plans/PLAN-design-system-fase1.md` e no amendment de
`docs/engineering/adr/ADR-001.md` (2026-08-16). Radix UI continua a fundação de primitivas; shadcn/ui é o
padrão de composição (componentes vivem em `frontend/src/components/ui/`, editáveis, nunca uma dependência
de runtime opaca); Phosphor Icons é o padrão de ícones para componentes novos, coexistindo com
`lucide-react` já em uso (sem migração retroativa).

### Design Tokens

**Cor** — já formalizada em `frontend/src/index.css` (`@theme`) desde antes desta fase: paleta de marca
(fundo escuro, vermelho `#FF0125` como `--color-primary`, sidebar quase preta), tokens semânticos
(`--color-card`, `--color-muted`, `--color-border`, `--color-sidebar-*`, `--color-chart-1` a `5`). Não
redesenhada nesta fase.

**Spacing, radius e shadow — decisão desta fase: usar a escala padrão do Tailwind, não criar tokens
customizados.** Investigação confirmou que o código já converge nisso organicamente:

- **Spacing:** a escala numérica padrão do Tailwind (`1`=4px, `2`=8px, `3`=12px, `4`=16px, `6`=24px,
  `8`=32px, `12`=48px, `16`=64px) já cobre exatamente os valores 4/8/12/16/24/32/48/64 aprovados — usar
  `p-4`/`gap-6`/`px-8` etc. diretamente, nunca um valor arbitrário (`p-[13px]`).
- **Radius:** `rounded-sm` (pequenos elementos de controle — botão de fechar em `dialog.jsx`), `rounded-lg`
  (padrão — botões, inputs, itens de navegação, já usado em `button.jsx`/`input.jsx`/`Layout.jsx`),
  `rounded-xl` (contêineres maiores — cards, dialogs, popovers, já usado em `dialog.jsx`/`popover.jsx`),
  `rounded-full` (badges, avatares). Sem radius customizado fora dessa escala.
- **Shadow:** uso restrito e intencional (`shadow-sm` em inputs, `shadow-xl` em overlays — dialog, popover
  — já o padrão em uso). Superfícies estáticas (cards de conteúdo, seções de página) não recebem shadow —
  a separação visual vem de `border`/`bg-card` contra `bg-background`, não de elevação. Evita a estética de
  "dashboard genérico de template" (decisão do CTO, `PLAN-design-system-fase1.md`).

**Por que não criar `--spacing-*`/`--radius-*`/`--shadow-*` customizados:** o Tailwind v4 já expõe esses
três eixos como tokens de tema (`--spacing`, `--radius-*`, `--shadow-*` no tema padrão) e o código já os usa
de forma consistente — sobrepor tokens próprios criaria dois vocabulários para a mesma coisa (`p-4` vs.
`p-[var(--spacing-md)]`), o oposto de um Design System coerente. Se uma necessidade real de valor fora da
escala padrão aparecer no futuro (ex.: um radius exclusivo de marca), aí sim vira um token nomeado — não
antecipado aqui.

**Tipografia, breakpoints e tamanhos de componente** seguem o mesmo princípio (escala padrão do Tailwind,
já em uso — `text-sm`/`text-2xl font-bold` no Dashboard, breakpoints `lg:`/lg: 1024px já usado no Shell para
o corte desktop/mobile) — não redecidido nesta fase; formalizado aqui só como confirmação de que não há
divergência a resolver.

### Componentes (shadcn/ui)

`frontend/src/components/ui/` — convenção: função nomeada exportada (não `default export`), `cn()` de
`@/lib/utils` para merge de classes, `cva` só quando o componente tem variantes reais (`button.jsx`,
`badge.jsx`) — componentes sem variante (`card.jsx`, `skeleton.jsx`) usam classes diretas. Sem
`data-slot`/atributos extras além do que os componentes já existentes usam — mantém o arquivo simples,
mesmo padrão de `dialog.jsx`/`popover.jsx`.

`components.json` na raiz de `frontend/` registra a configuração do CLI shadcn (estilo, alias, ausência de
TypeScript — o projeto usa `.jsx`) para permitir `npx shadcn add <componente>` quando um componente novo for
necessário, sem precisar reconfigurar a cada vez.

### Motion vs. transição CSS — quando usar cada um

Regra fixada durante o PR 3 da Fase 1 (Tooltip/Sheet/Sidebar), para não decidir caso a caso de novo:

- **Componente que envolve `Portal`/ciclo de montagem próprio do Radix** (`Dialog`, `AlertDialog`,
  `Popover`, `Tooltip`, `Sheet`) — usa transição CSS pura via `data-[state=open]:`/`data-[state=closed]:`
  (Tailwind já suporta nativamente, mesmo idioma já usado em `checkbox.jsx`). Motivo: o `Presence` interno
  do Radix decide quando desmontar o nó esperando um evento `transitionend`/`animationend` do DOM — o
  Motion anima via WAAPI/`requestAnimationFrame`, que o `Presence` do Radix não detecta, cortando a
  animação de saída antes do tempo se usado ali.
- **Componente com estado próprio (React puro, sem `Portal` do Radix por trás)** — pode usar Motion
  (`AnimatePresence` + `motion.*`) livremente, controlando o próprio ciclo de montagem/desmontagem. Exemplo:
  o drawer mobile do `Sidebar` (`sidebar.jsx`).
- Sempre respeitar `useReducedMotion()` em qualquer uso de Motion (acessibilidade — ver seção 4 abaixo).

---

## 3.3 Fluxoly Design System (Fase 2 — Foundation)

Formalizado em `docs/engineering/plans/PLAN-design-system-fase2.md`. A Fase 1 (seção 3.2) validou o Design
System em 3 áreas (Shell, Dashboard, Landing); a Fase 2 estende esses padrões às outras 21 páginas do
sistema. O PR 1 dessa fase ("Foundation") criou o vocabulário compartilhado abaixo **sem redesenhar
nenhuma tela** — as fatias seguintes consomem esses componentes conforme cada página é migrada.

**Regra de ouro de toda a Fase 2 (inegociável):** `docs/company/BRAND_IDENTITY.md` é autoridade sobre a
marca. Nenhuma fatia pode alterar `#FF0125`, a fonte Onest, o wordmark, criar paleta/gradiente novo, ou
token de spacing/radius/shadow fora da escala já formalizada na seção 3.2. O trabalho é aplicar a
identidade existente de forma consistente, não redefini-la.

### Badge semântico (`components/ui/badge.jsx`)

Variantes de status — `success`/`warning`/`error`/`info`/`neutral` — estilo "soft" (`bg-X/10 text-X
border-X/30`), mapeadas aos tokens de `index.css` (`--color-success`/`warning`/`destructive`/`info`).
Substituem a prática anterior de sobrescrever `variant="outline"` com `className` de cor Tailwind crua
(`bg-emerald-500/10 text-emerald-300 border-emerald-500/30`, reimplementada em ~13 páginas antes da Fase
2). Cada módulo continua dono do mapeamento status→variante (o Design System não impõe vocabulário de
negócio, só a renderização): `<Badge variant="success">{label}</Badge>` em vez de recriar a cor à mão.
Variantes pré-existentes (`default`/`secondary`/`destructive`/`outline`) preservadas sem mudança.

**Severidade vs. taxonomia (Fase 2, PR 5):** `success`/`warning`/`error`/`info`/`neutral` respondem "como
está indo isso" — carregam significado de estado. `tag` (`border-border bg-secondary/60
text-secondary-foreground`) é uma variante à parte, para "que tipo de coisa é isso" — categoria, origem,
qualquer rótulo taxonômico. Deliberadamente uma única cor neutra sem tom por valor: cor não deve carregar
significado de taxonomia arbitrária (diferente de severidade, onde a cor É o significado). Nunca usar as 5
variantes de severidade para taxonomia, nem `tag` para estado — ver decisão completa em
`PLAN-design-system-fase2.md` (fechamento do achado do PR 4).

### Estados de página (`components/ui/empty-state.jsx`, `error-state.jsx`, `loading-state.jsx`)

Generalização do padrão de 4 estados validado em `Dashboard.jsx` (Fase 1, PR #46) para uso em qualquer
página: `EmptyState` (título + descrição + ação opcional), `ErrorState` (bloqueante, tela cheia) e
`ErrorBanner` (não bloqueante, para erro de atualização com dado já carregado na tela), `ListSkeleton`
(linhas — a forma mais comum nas páginas legadas, predominantemente tabela/lista) e `CardGridSkeleton`
(grid de cards, mesma forma já usada no Dashboard).

### Padrão visual de filtros (`components/ui/filter-bar.jsx`)

`FilterBar`/`FilterSelect`/`FilterInput`/`DateRangeFilter`/`ClearFiltersButton` — padronizam a composição
visual de filtros já repetida quase igual em Orders/Vendas/Stock/Dashboard. **Não** encapsulam lógica de
filtragem nem parâmetros de API — o chamador continua responsável pelo estado e pelo mapeamento de valor
(ex.: opção "Todos" → filtro vazio). Migrar a visual de uma tela para esses componentes nunca deve, por si
só, mudar o comportamento de negócio do filtro.

### Motion discreto (`components/ui/reveal.jsx`, `lib/interaction.js`)

- `Reveal`: entrada suave (`opacity`/`y`) para conteúdo que aparece após carregar via fetch (linhas,
  cards, estados vazio/erro), acionada na montagem (`animate`) — distinto de
  `components/landing/FadeInSection.jsx` (`whileInView`, scroll-triggered, exclusivo da Landing). Sempre
  respeita `useReducedMotion()`, mesma regra da seção 3.2. Componente React puro sem `Portal` do Radix por
  trás — a mesma seção 3.2 já autoriza Motion nesse caso.
- `interactiveRowClassName`/`interactiveCardClassName` (`lib/interaction.js`): convenção de hover/foco via
  transição CSS (não Motion) para linha de tabela e card clicável — reutilizar em vez de reescrever a
  combinação a cada página migrada.

### Convenção de ícones para a Fase 2

Phosphor Icons é o padrão para qualquer componente novo desta fase e para qualquer página migrada.
`lucide-react` continua nas páginas ainda não tocadas — **a migração de ícones acontece junto da migração
da tela, nunca como PR isolado de substituição mecânica** (evita PRs grandes só de troca de import, sem
nenhum ganho visual por si só).

---

## 3.4 Fluxoly Design System (Fase 3.1 — Foundation v2)

Formalizado em `docs/engineering/plans/PLAN-design-system-fase3.1-foundation-v2.md`. Evolui a Foundation
da Fase 2 (seção 3.3) para os dois modos de tema (Light+Dark, infra da Fase 3.0) — novos recipientes de
composição, `DataTable` real e tema único de gráfico — **sem redesenhar nenhuma tela** (mesmo princípio da
Fase 2), exceto a correção pontual do KI-050 (troca de classe de cor, não de composição).

### Recipientes de composição (`components/ui/panel.jsx`, `list-block.jsx`, `loose-metric.jsx`)

`Card` deixa de ser o recipiente universal — vira 1 de 4 possíveis, conforme o peso do conteúdo (spec §7):

- **`Panel`** — dominante: borda + sombra, para o único elemento de maior peso de cada tela.
- **`ListBlock`/`ListBlockItem`** — bloco de lista: sem moldura própria, só divisor sutil entre linhas.
- **`LooseMetric`** — métrica solta: número + rótulo, sem moldura nenhuma.
- **`Card`** (já existente) — segue disponível para o caso genérico/elemento flutuante (dropdown/popover
  via Radix), não descontinuado.

Nenhum dos 3 recipientes novos usa o prefixo `dark:` do Tailwind — este projeto não usa esse variant para
tema (ver `index.css`, Fase 3.0); toda diferença visual entre modos vem só de `--color-*`.

### `DataTable` (`components/ui/data-table.jsx`)

Tabela real, substituindo o padrão de HTML cru com bordas manuais repetido por arquivo. `stickyHeader`
(header fixo em listas longas) e `onRowClick` (linha clicável, com suporte a teclado via `Enter`) são
opcionais. Migração de tabelas existentes para `DataTable` é escopo das Fases 3.2+, tela a tela — este
componente só existe a partir da Fase 3.1, ainda não é usado em nenhuma página.

### Tema de gráfico (`lib/chart-theme.js`)

Recharts recebe cor via prop SVG (`stroke`/`fill`), não via classe Tailwind — `chart-theme.js` centraliza
os valores (`var(--color-*)`) para que todo gráfico reaja à troca de tema automaticamente, sem
sincronização manual. `chartColor(index)` cicla a paleta categórica (`--color-chart-1..5`).

### KI-050 — telas hardcoded migradas para tokens de tema

As 9 telas identificadas na revisão final da Fase 3.0 (`KpiCard.jsx`, `Dashboard.jsx`, `Reports.jsx`,
`OperationalCosts.jsx`, `Garantias.jsx`, `Vendas.jsx`, `Users.jsx`, `VendaDetalhe.jsx`,
`TiposGarantia.jsx`) foram migradas de classes Tailwind cruas (`text-emerald-400` etc., calibradas só para
Dark Mode) para os tokens semânticos já existentes (`text-success`/`warning`/`destructive`/`info`).
Exceção registrada: o papel "financeiro" em `Users.jsx` (`text-purple-400`) não tem token semântico
equivalente na paleta Pulse — ver KI-051.

Nota: a correção do KI-050 preservou as opacidades originais de cada tela (`/10`/`/20` em fundo, sempre
`/30` em borda) — 3 receitas de "badge suave" com os mesmos tokens agora coexistem (`Badge`/
`TiposGarantia.jsx` vs. `Garantias.jsx`/`Users.jsx`). Consolidar em uma única receita (ex.: sempre via o
componente `Badge`) é trabalho de composição, fica para a Fase 3.2+.

---

## 3.5 Fluxoly Design System (Fase 3.2 — Vitrine)

Formalizado em `docs/engineering/plans/PLAN-design-system-fase3.2-vitrine.md`. Primeira fase a redesenhar
composição de telas reais (Login, Shell/Sidebar, Dashboard) usando os recipientes da Foundation v2
(Fase 3.1) — prova de conceito da hierarquia de superfície (`PLAN-design-system-fase3-visual-experience.md`
§2) antes de escalar para as Fases 3.3-3.5 (Tiers 2-4).

### Sidebar agrupado pelos 6 Pilares Macrossistêmicos

`Layout.jsx::navSections` substitui o array plano `navItems` — rotas agrupadas em Vendas/Operação/
Financeiro/Relacionamento/Serviços/Inteligência (`BRAND_IDENTITY.md` §2) + uma seção "Administração" fora
dos pilares (Usuários/Backups, operação de sistema, não função de negócio). Uma seção inteira desaparece
quando nenhum item dela é visível para o perfil da sessão — nunca um rótulo de seção órfão. A duplicata
histórica de `/compras` (aparecia como "Compras" e "Lista de Compras") foi removida no mesmo commit,
mantendo só "Lista de Compras".

### Dashboard — 1 métrica dominante, resto secundário

Faturamento do período usa `Panel` com número hero (`text-4xl`/`text-5xl`); os outros 7 KPIs usam
`LooseMetric` (sem moldura); Resumo Financeiro usa `ListBlock` em vez de grade de caixas com fundo próprio.
`KpiCard.jsx` fica sem consumidor após esta fase — registrado como KI-056, decisão de remover fica para o
CTO.

### Login e Landing

`Login.jsx` migra a moldura do form para `Panel`, com respiro adicional acima/abaixo (`py-12`,
`space-y-8`). A Landing Page **não** é redesenhada nesta fase (fora da liberdade criativa total, ver
`PLAN-design-system-fase3-visual-experience.md` §0.1) — auditada por consistência de token/marca, nenhum
achado (já herdava os tokens corretamente).

---

## 4. Padrões Frontend (React / Vite)

### 4.0 Princípio de UX: interface por perfil

**Cada profissional deve enxergar apenas o que precisa para executar seu trabalho com máxima eficiência.**
*(Fonte: Product Owner, 2026-07-10 — ver `docs/company/VISION.md` Valores e
`docs/company/PRODUCT_REQUIREMENTS.md` seção "Personas Operacionais".)*

Este é um critério de decisão, não só uma aspiração: ao desenhar uma tela nova ou decidir o que uma tela
existente exibe, prefira sempre a opção que restringe a visão ao necessário para o perfil de sessão ativo
(`admin`/`tecnico`/`vendedor` hoje — ver `docs/engineering/DOMAIN_MODEL.md` 1.2), em vez de uma tela única
com tudo visível para todos os perfis e apenas alguns campos desabilitados por permissão. Concretamente:

- Um Vendedor não precisa ver configuração de custos operacionais ou administração de usuários.
- Um Técnico não precisa do fluxo de checkout de venda.
- Quando um domínio novo nascer com perfil próprio (ex.: Financeiro, Estoque — hoje sem perfil de login
  distinto, ver `docs/company/PRODUCT_REQUIREMENTS.md` "Personas Operacionais"), sua tela deve ser
  desenhada para esse perfil desde o início, não como uma aba a mais dentro de uma tela genérica.

Isso não substitui a checagem de permissão no backend (`ROUTE_PERMISSIONS`, `usuario_logado()` — seção 3
acima) — é um critério de design de interface, complementar à autorização real, que continua sendo sempre
no servidor.

### Estrutura de arquivos

```
frontend/src/
├── api/
│   └── client.js          — único ponto de acesso à API (nunca fazer fetch direto nas pages)
├── components/
│   ├── ui/                — componentes atômicos (button, input, etc.)
│   ├── dashboard/         — widgets do dashboard
│   ├── orders/            — componentes de OS
│   └── shopping/          — componentes de lista de compras
├── contexts/
│   └── AuthContext.jsx    — estado global de autenticação
├── hooks/                 — hooks customizados (criar a partir da Sprint 5)
├── lib/
│   ├── constants.js       — constantes UI e formatação
│   └── utils.js           — utilitários puros
└── pages/                 — páginas (uma por rota)
```

### Regras de componentes

- **Pages** (`src/pages/`) contêm o layout e orquestram dados. Não contêm lógica de negócio direta.
- **Components** (`src/components/`) são reutilizáveis e não fazem chamadas à API diretamente.
- **Chamadas à API** são feitas exclusivamente via `src/api/client.js` — nunca `fetch()` inline numa page.
- Props tipadas com JSDoc quando o componente é compartilhado.

### Padrão de chamada à API

```javascript
// client.js — padrão de definição
const os = {
  listar: (params = {}) => api.get("/ordens", { params }),
  criar: (data) => api.post("/ordens", data),
  atualizar: (id, data) => api.put(`/ordens/${id}`, data),
  deletar: (id) => api.delete(`/ordens/${id}`),
};

// page — padrão de uso
const [loading, setLoading] = useState(false);
const [erro, setErro] = useState(null);

async function carregarOrdens() {
  setLoading(true);
  try {
    const { data } = await os.listar({ status: filtro });
    setOrdens(data.data);
  } catch (err) {
    setErro(err.message);
  } finally {
    setLoading(false);
  }
}
```

### Estado e efeitos

- `useEffect` com array de dependências explícito e correto — sem dependências omitidas.
- Estado derivado (calculado de outro estado) nunca vive em `useState` — calcule inline ou use `useMemo`.
- Cleanup em `useEffect` quando cria subscriptions, timers ou listeners.
- Nunca atualizar estado de componente desmontado — verificar com flags de cleanup.

### Roteamento e proteção

- Rotas privadas verificam autenticação via `AuthContext` em `App.jsx`.
- Rota pública única: `/checklist/:token` (sem autenticação).
- Redirecionamento para `/login` em qualquer rota sem sessão válida.

---

## 5. Banco de Dados

Detalhes completos em `docs/engineering/DATABASE.md`. Regras essenciais:

### Migrations

- **Nunca** executar `ALTER TABLE` ad-hoc sem documentação correspondente.
- Toda alteração de schema deve ter: arquivo de migration versionado + atualização de `DATABASE.md`.
- Migrations são sempre aditivas (adicionar coluna, tabela, índice) — nunca destrutivas em produção sem janela de manutenção.
- Antes de qualquer migration em produção: **backup verificado**.

### Consultas

- Parâmetros sempre por placeholder `?` — nunca por concatenação.
- Queries de listagem com potencial de retornar muitos resultados devem ter `LIMIT`.
- Índices documentados e justificados em `DATABASE.md`.
- `EXPLAIN QUERY PLAN` antes de adicionar índice novo.

### Nomenclatura

- Tabelas: `snake_case` no plural (`os`, `estoque`, `usuarios`, `shopping_list`).
- Colunas: `snake_case` (`criado_em`, `valor_cobrado`, `reparo_id`).
- Foreign keys: `<tabela_singular>_id` (`os_id`, `estoque_id`).
- Índices: `idx_<tabela>_<coluna>` (`idx_estoque_sku`).

---

## 6. Testes

Detalhes completos em `docs/engineering/TESTING.md`. Regras essenciais:

### Hierarquia de testes

| Tipo | Ferramenta | Escopo | Isolamento |
|------|-----------|--------|-----------|
| Unitário / Integração | pytest | Endpoints, lógica de negócio | SQLite in-memory |
| E2E | Playwright | Fluxos completos do usuário | Servidor Flask real |

### Regras inegociáveis

1. **Nenhum teste toca `database.db`** — banco de produção/desenvolvimento é intocável em testes.
2. **Cada teste é independente** — não depende de estado deixado por teste anterior.
3. **Testes falhos bloqueiam o merge** — CI vermelho = PR não entra.
4. **Cobertura não cai** — threshold definido em `pyproject.toml`. Se cair, o CI falha.
5. **Novo bug = novo teste** — ao corrigir um bug, escreva o teste que o teria detectado.

### O que deve ser testado

- Toda rota REST: casos felizes + casos de erro (401, 403, 404, 400).
- Toda transição de status (OS, shopping list).
- Toda regra de negócio crítica (cálculo de preço, validação de campos obrigatórios).
- Fluxos E2E: login, criar OS, editar OS, criar item de estoque.

---

## 7. Segurança

Detalhes completos em `docs/engineering/SECURITY.md`. Regras essenciais:

### SQL Injection
- **Proibido:** `f"SELECT * FROM os WHERE id = {id}"` ou qualquer interpolação em SQL.
- **Obrigatório:** `cursor.execute("SELECT * FROM os WHERE id = ?", (id,))`

### Autenticação
- Senhas armazenadas com hash via Werkzeug (`generate_password_hash` / `check_password_hash`).
- `FLASK_SECRET_KEY` forte e única por ambiente — nunca o valor default em produção.
- Sessões invalidadas no logout via `session.clear()`.

### CORS
- `IR_FLOW_CORS_ORIGINS` define origens permitidas — nunca `*` em produção.
- Cookies com `SameSite=None; Secure` apenas quando necessário para cross-origin (deploy separado).

### Exposição de dados
- Respostas de erro nunca incluem stack traces, paths de arquivo ou detalhes internos.
- Listagens paginadas quando o volume pode ser alto (protege contra dump de dados).

---

## 8. Qualidade de Código

### Lint backend (Ruff)

```bash
ruff check .
```

Regras habilitadas: `E` (pycodestyle), `F` (pyflakes), `W` (warnings), `I` (isort).
Configuração em `pyproject.toml`. Executado no CI — falha bloqueia o merge.

### Lint frontend (ESLint)

```bash
cd frontend && npm run lint
```

Configuração em `frontend/eslint.config.js`. Executado no CI — falha bloqueia o merge.

### Complexidade e legibilidade

- Funções com mais de 40 linhas: candidatas a decomposição.
- Componentes React com mais de 200 linhas: candidatos a decomposição.
- Comentários explicam o **porquê**, não o **o quê**. Código bem escrito não precisa de comentário para dizer o que faz.
- Nomes de variáveis e funções em português para domínio de negócio (`valor_cobrado`, `criarOrdem`), inglês para infraestrutura (`useEffect`, `useState`, `handleSubmit`).

---

## 9. Commits — Conventional Commits

**Formato obrigatório a partir da Sprint 2:**

```
<tipo>(<escopo opcional>): <descrição em minúsculas>

[corpo opcional]

[rodapé opcional]
```

### Tipos permitidos

| Tipo | Quando usar |
|------|-------------|
| `feat` | Nova funcionalidade |
| `fix` | Correção de bug |
| `refactor` | Refatoração sem mudança de comportamento |
| `test` | Adição ou correção de testes |
| `docs` | Documentação apenas |
| `chore` | Manutenção (deps, config, CI) |
| `perf` | Melhoria de performance |
| `style` | Formatação, espaços, ponto-e-vírgula |

### Exemplos corretos

```
feat(os): adicionar auto-preenchimento de valor_cobrado via tabela de preços
fix(auth): corrigir redirecionamento após logout em sessão expirada
refactor(api): mover endpoints de shopping list para módulo separado
test(pricing): adicionar cobertura para endpoint sugerir com múltiplos reparos
docs(claude): adicionar protocolo de trabalho obrigatório
chore(ci): configurar GitHub Actions com lint e testes
```

### Exemplos proibidos

```
att                     ← sem tipo, sem descrição
fix bug                 ← sem escopo, sem contexto
S                       ← incompreensível
att 09/06 5             ← data não pertence ao commit message
```

**Breaking changes** são indicados com `!` após o tipo: `feat!: remover endpoint legado`.

---

## 10. Fluxo de PR e Revisão

### Criando uma branch

```bash
git checkout -b feat/nome-da-feature
git checkout -b fix/nome-do-bug
git checkout -b refactor/nome-da-refatoracao
git checkout -b docs/nome-da-documentacao
```

### Antes de abrir o PR

- [ ] CI local passando (`pytest tests/`, `ruff check .`, `npm run lint`)
- [ ] Testes novos escritos para a mudança
- [ ] `KNOWN_ISSUES.md` atualizado se bug foi corrigido
- [ ] `CHANGELOG.md` atualizado
- [ ] Nenhum arquivo de debug ou temporário commitado
- [ ] Nenhum `console.log` ou `print()` de debug no código

### Template de PR

Use `docs/engineering/templates/PR_TEMPLATE.md` como base. Inclua obrigatoriamente:
- **O que muda:** descrição clara do que foi implementado
- **Por que muda:** motivação, contexto ou issue relacionado
- **Como testar:** passos para validar a mudança
- **Checklist:** itens de qualidade verificados

### Critérios de merge

- CI verde (todos os jobs bloqueantes passando)
- Revisão aprovada (quando houver mais de um colaborador)
- Nenhum comentário de revisão aberto
- Documentação atualizada

---

## 11. Bugs Encontrados Durante Sprints de Teste, QA ou Validação

Escrever testes, validar comportamento ou rodar QA frequentemente revela bugs reais no código de produção — não só lacunas de cobertura. Esta seção define quando um achado desses **interrompe a sprint** e exige um `hotfix/` imediato (ver `CLAUDE.md` para o fluxo completo e `docs/engineering/QUALITY_GATES.md` — G-18), e quando ele deve apenas ser **caracterizado por teste e reportado** para decisão posterior, sem parar o trabalho planejado.

Não há espaço para julgamento subjetivo aqui — mesmo espírito de `QUALITY_GATES.md`: cada critério é verdadeiro ou falso.

### Critérios objetivos de interrupção

Pare a sprint e abra um `hotfix/` se **qualquer um** dos critérios abaixo for verdadeiro:

| # | Critério | Pergunta objetiva |
|---|----------|---------------------|
| C-01 | Mutação silenciosa de dado persistido | O comportamento grava, apaga ou altera uma linha no banco **sem retornar erro** e sem que o chamador tenha pedido essa mudança? |
| C-02 | Perda de dado irreversível | Uma operação normal (não destrutiva por design) causa perda de dado que não pode ser recuperada a partir do próprio sistema? |
| C-03 | Bypass de autenticação/autorização | O achado permite acessar, alterar ou excluir dado de outro usuário, ou executar uma ação sem a permissão exigida pela regra de negócio? |
| C-04 | Caminho real de produção | O comportamento está na rota/função que o frontend em produção efetivamente usa (não uma rota legada morta ou código não referenciado)? |

Se **nenhum** critério for verdadeiro — por exemplo, uma exceção não tratada que resulta em `500` mas não escreve nenhum dado incorreto, ou um comportamento equivalente numa rota legada sem uso real — **não interrompa**: escreva o teste que caracteriza o comportamento atual, não o commite como falha, e reporte o achado ao final da sprint para decisão (registrar em `KNOWN_ISSUES.md`, corrigir depois, ou aceitar como está).

### Exemplos já observados no projeto

- **Interrompeu (C-01 + C-04):** `PATCH /api/ordens/<id>/status` aceitava um status desconhecido e o normalizava silenciosamente para "Em andamento" em vez de rejeitar — grava estado errado sem erro, na rota que o frontend usa. Corrigido via commit direto na sprint (antes desta política existir — ver ADR-004 sobre não-retroatividade).
- **Interrompeu (C-01 + C-02 + C-04):** `PUT /api/ordens/<id>` sem `status` reabria uma OS Finalizada e apagava `data_finalizado` silenciosamente — perda do dado de finalização sem qualquer erro.
- **Não interrompeu (nenhum critério):** `POST /api/auth/login` com um array JSON no lugar de um objeto derrubava a rota com `AttributeError` (500). Falha alto e visível, não persiste nenhum dado incorreto — caracterizado como comportamento a evitar no teste (removido da suíte, não commitado como falha) e reportado separadamente.
- **Não interrompeu (C-04 falso):** divergência entre `POST /atualizar_status` (rota legada) e `PATCH /api/ordens/<id>/status` (API) na reativação de OS Cancelada — a rota legada não é a que o frontend em produção usa; caracterizado por teste e reportado, sem hotfix.

---

## 12. Ciclo de Feature com Regra de Negócio

Para qualquer feature nova que envolva regra de negócio (não uma correção de bug isolada ou chore), o
processo obrigatório é definido em `docs/engineering/adr/ADR-010.md`: Discovery → Plano Técnico →
Implementação → Testes → QA Manual → Revisão Arquitetural → Encerramento, cada etapa com um gate de
aprovação explícito antes da seguinte. Revisão Arquitetural é obrigatória quando a sprint combina
reversão de comportamento com feature nova, ou toca mais de 3 arquivos.

**Princípio da Separação de Decisões** (`ADR-010`): cada decisão é tomada exatamente na etapa responsável
por ela — Discovery decide regra de negócio, ADR decide arquitetura, Plano Técnico decide implementação,
Código decide execução, QA decide validação. Em particular, o Plano Técnico (template em
`docs/engineering/templates/PLAN_TEMPLATE.md`) **nunca** decide regra de negócio — se uma pergunta de
negócio surgir durante o planejamento técnico, ela vai para a seção "Questões em Aberto" do plano e o
trabalho volta para Discovery antes de prosseguir.

Ver `docs/engineering/CONTRIBUTING.md` seção 9 para o passo a passo de como criar um Plano Técnico.
