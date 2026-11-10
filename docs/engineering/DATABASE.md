# DATABASE.md — Schema, Índices e Regras de Migração

Este documento reflete o schema **real** produzido por `criar_tabelas()` em `app.py`, incluindo as
colunas adicionadas posteriormente via `ALTER TABLE` ad-hoc. Em caso de dúvida sobre o estado real
de um ambiente, inspecione o banco diretamente — não assuma que este documento está 100% sincronizado
(ver KI-004: ausência de migrations formais é dívida técnica conhecida, planejada para Sprint 4).

**Última revisão:** 2026-07-20
**Motor:** SQLite, modo WAL (`_configurar_conexao_sqlite(conn, habilitar_wal=True)`)

---

## 1. Regras de Migração (estado atual)

- Todo schema é definido em `app.py`, função `criar_tabelas()`, executada na inicialização da
  aplicação.
- Tabelas são criadas com `CREATE TABLE IF NOT EXISTS` — idempotente.
- Colunas adicionadas após a criação inicial da tabela usam `ALTER TABLE ... ADD COLUMN` dentro de um
  bloco `try/except sqlite3.OperationalError: pass` — também idempotente, mas **sem histórico
  versionado**: não há como saber, olhando o código, em qual ordem/sprint cada `ALTER TABLE` foi
  introduzido sem checar o histórico do Git.
- Não existem migrations formais (Alembic ou scripts numerados). Isso está registrado como KI-004 /
  TD-03 e é o objetivo da Sprint 4 (`migrations/001_initial_schema.sql`, `migrations/002_shopping_list.sql`, etc.).
- **Regra para qualquer alteração futura de schema:** seguir `ENGINEERING_GUIDE.md` seção 5 —
  migrations sempre aditivas em produção, backup verificado antes de aplicar, atualização obrigatória
  deste documento.

---

## 2. Tabelas

### `usuarios`

Autenticação e perfis de acesso.

| Coluna | Tipo | Constraints | Descrição |
|--------|------|-------------|-----------|
| `id` | INTEGER | PK AUTOINCREMENT | |
| `nome` | TEXT | NOT NULL | Nome de exibição |
| `usuario` | TEXT | UNIQUE NOT NULL | Login (usado para autenticação) |
| `senha_hash` | TEXT | NOT NULL | Hash Werkzeug (`generate_password_hash`) |
| `perfil` | TEXT | NOT NULL DEFAULT `'tecnico'` | `admin` \| `tecnico` \| `vendedor` \| `estoque` (desde 2026-07-25, `irflow_core.py::PERFIS_OPCOES`) |
| `ativo` | INTEGER | NOT NULL DEFAULT `1` | `0` desativa o login mesmo com senha correta |

**Regras de negócio:**
- Login só é bem-sucedido se `ativo = 1` e hash confere (`irflow_blueprints_auth.py`,
  `irflow_blueprints_api.py` rota `/api/auth/login`).
- Um usuário não pode desativar (`ativo = 0`) nem deletar a própria conta enquanto logado
  (checagem por `uid == session.get("usuario_id")`).
- Sem índice explícito além do `UNIQUE` em `usuario` (que já cria índice implícito no SQLite).

### `os` — Ordens de Serviço

| Coluna | Tipo | Observação |
|--------|------|------------|
| `id` | INTEGER | PK AUTOINCREMENT |
| `tipo` | TEXT | `Assistencia` \| `Garantia` \| `Interna` (conserto de aparelho comprado, BR-090, desde 2026-11-08 — fora de faturamento, relatórios, dashboard e Garantias) (`Upgrade` removido das opções em 2026-11-06, ADR-014) |
| `cliente` | TEXT | |
| `aparelho` | TEXT | |
| `tecnico` | TEXT | |
| `reparo_id` | INTEGER | legado — reparo único; substituído por `os_reparos` (N:N) |
| `status` | TEXT | ver `irflow_core.py` — `STATUS_OS_VALIDOS` |
| `valor_cobrado` | REAL | |
| `valor_descontado` | REAL | |
| `custo_pecas` | REAL | |
| `data` | TEXT | |
| `data_finalizado` | TEXT | *(ALTER)* |
| `modelo` | TEXT | *(ALTER)* — normalizado via `normalizar_modelo_iphone` |
| `cor` | TEXT | *(ALTER)* |
| `imei` | TEXT | *(ALTER)* — normalizado via `normalizar_imei` |
| `vendedor` | TEXT | *(ALTER)* |
| `observacoes` | TEXT | *(ALTER)* |
| `origem_integracao` | TEXT | *(ALTER)* — origem quando criada via MercadoPhone |
| `id_externo_integracao` | TEXT | *(ALTER)* — id no sistema externo |
| `cliente_id` | INTEGER | *(ALTER, Sprint P0.1)* — FK lógica para `clientes.id`, nullable, **sem backfill**: OS existentes continuam só com `cliente` (texto); novas OS podem ser vinculadas a um cliente, mas nada força isso ainda |
| `unidade_serializada_id` | INTEGER | *(migration `m0003`, 2026-11-08)* — FK lógica para `unidades_serializadas.id`, nullable. Reservada para a OS interna de conserto de aparelho comprado (BR-090): preenchida só quando `tipo='Interna'`, que também grava `cliente='Estoque próprio'`, `vendedor=''`, valores 0 e o IMEI do aparelho. Índice `idx_os_unidade_serializada_id` |

Sem índice declarado explicitamente (candidato a `idx_os_status_data_tecnico` — ver KI-005/Sprint 5).

### `reparos`

| Coluna | Tipo |
|--------|------|
| `id` | INTEGER PK AUTOINCREMENT |
| `nome` | TEXT |

### `os_reparos` — associação N:N entre OS e reparos

| Coluna | Tipo | Constraint |
|--------|------|------------|
| `os_id` | INTEGER | NOT NULL, parte da PK composta |
| `reparo_id` | INTEGER | NOT NULL, parte da PK composta |

PK composta `(os_id, reparo_id)`. Populada retroativamente a partir de `os.reparo_id` (migração de
dados feita inline em `criar_tabelas()` via `INSERT OR IGNORE`).

### `estoque`

| Coluna | Tipo | Observação |
|--------|------|------------|
| `id` | INTEGER PK AUTOINCREMENT | |
| `descricao` | TEXT | |
| `valor` | REAL | |
| `fornecedor` | TEXT | |
| `quantidade` | INTEGER | quantidade agregada (ver `estoque_lotes` para rastreio por lote) |
| `data_compra` | TEXT | |
| `sku` | TEXT | *(ALTER)* — gerado como `ITEM-<id>` quando ausente |
| `modelo` | TEXT | *(ALTER)* — normalizado via `normalizar_modelo_iphone` |
| `tipo` | TEXT | *(ALTER)* |
| `qualidade` | TEXT | *(ALTER)* |
| `requer_imei` | INTEGER NOT NULL DEFAULT 0 | *(ALTER, Sprint P0.1)* — flag manual (admin/técnico) indicando se este item exige rastreamento por unidade individual via `unidades_serializadas`; peças de reparo continuam agregadas (0) |

**Índices:**
- `idx_estoque_sku` em `(sku)`
- `idx_estoque_tripla` em `(modelo, tipo, qualidade)` — suporta busca de peça compatível por
  modelo/tipo/qualidade

### `unidades_serializadas`

Rastreamento individual por IMEI/serial (Sprint P0.1 — `docs/product/features/IMEI.md`), evoluído de
`estoque_unidades` na migração `docs/engineering/migrations/MIGRATION_unidades_serializadas.md`
(ADR-007, 2026-07-21). Fonte única de verdade para qualquer unidade física da empresa, com origem em
Estoque OU Produtos — nunca os dois (Regra de Ouro, ADR-007). Segue a convenção
controller/service/repository de `docs/engineering/ENGINEERING_GUIDE.md` §3.1
(`irflow_unidades_serializadas_*.py`).

**Exceção à convenção de migração aditiva:** esta tabela foi recriada (`CREATE` → copiar dados →
`DROP` → `RENAME`), não alterada via `ALTER TABLE ... ADD COLUMN` — porque relaxar `estoque_id` de
`NOT NULL` para nullable não é possível via `ALTER TABLE` no SQLite. Ver o plano de migração linkado
acima para a estratégia completa, rollback e checklist de integridade.

| Coluna | Tipo | Observação |
|--------|------|------------|
| `id` | INTEGER PK AUTOINCREMENT | |
| `estoque_id` | INTEGER | FK lógica para `estoque.id`. Nullable — exatamente um de `estoque_id`/`produto_id` deve estar preenchido (invariante validada no service, não no banco) |
| `produto_id` | INTEGER | FK lógica para `produtos.id` (ADR-007). Nullable, mesma invariante acima |
| `lote_id` | INTEGER | FK lógica para `estoque_lotes.id`, opcional |
| `imei` | TEXT UNIQUE | `NULL` permitido (SQLite não colide `NULL`s em `UNIQUE`) — formato não validado nesta sprint (`TODO` em `IMEI.md`) |
| `status` | TEXT NOT NULL DEFAULT `'disponivel'` | Valores no schema: `disponivel \| reservado \| vendido \| em_reparo \| devolvido`. Alcançáveis via `TRANSICOES_VALIDAS` (genérico): `disponivel`/`em_reparo`/`devolvido`. `vendido` só via `fluxoly_vendas_service.py::iniciar_venda` (`marcar_como_vendida`); volta a `disponivel` só via `cancelar_venda` (`liberar_unidade_para_venda`, V1.2, 2026-07-27) — ambas fora de `TRANSICOES_VALIDAS` de propósito, exclusivas do domínio Vendas. `reservado` segue sem uso (reserva com timeout, fase futura) |
| `reservado_por` | INTEGER | Sem uso ainda — reservado para Vendas |
| `reservado_ate` | TEXT | Sem uso ainda — reservado para Vendas |
| `venda_id` | INTEGER | Sem uso ainda — reservado para Vendas |
| `saude_bateria` | TEXT | Adicionado na migração ADR-007 — sem uso ainda |
| `localizacao` | TEXT | Adicionado na migração ADR-007 — sem uso ainda |
| `criado_em` | TEXT NOT NULL | `datetime('now')` |
| `atualizado_em` | TEXT NOT NULL | `datetime('now')` |

**Índices:** `idx_unidades_serializadas_estoque_id`, `idx_unidades_serializadas_produto_id`,
`idx_unidades_serializadas_status`, `idx_unidades_serializadas_imei`.

### `produtos`

Catálogo comercial de venda (Sprint Comercial 0.1) — iPhone, Apple Watch, AirPods, Acessório. Domínio
novo, **separado** de `estoque` (peças de reparo — `docs/engineering/DOMAIN_MODEL.md` seção 1.4):
`estoque.tipo`/`qualidade` são listas fechadas hardcoded para vocabulário de peça de reparo
(`Tela`/`Bateria`/...) e o frontend (`Stock.jsx`) é inteiramente rotulado "peças", sem campo de preço de
venda/margem/condição — estender `estoque` misturaria dois modelos mentais diferentes na mesma tabela.
Segue a convenção controller/service/repository de `docs/engineering/ENGINEERING_GUIDE.md` §3.1
(`irflow_produtos_controller.py`/`_service.py`/`_repository.py`).

| Coluna | Tipo | Default | Observação |
|--------|------|---------|------------|
| `id` | INTEGER PK AUTOINCREMENT | | |
| `categoria` | TEXT NOT NULL | | Lista fechada: `iPhone`\|`Apple Watch`\|`AirPods`\|`Acessorio` (`PRODUTOS_CATEGORIAS`, `irflow_reference_data.py`). Valor fora da lista é **rejeitado**, não normalizado (BR-027) |
| `marca` | TEXT | | Texto livre — Apple domina, mas acessórios têm outras marcas |
| `modelo` | TEXT | | |
| `cor` | TEXT | | Texto livre nesta sprint (não usa `IPHONE_COLORS`/`COLOR_ALIAS_MAP`, que são iPhone-only) |
| `capacidade` | TEXT | | Ex.: "128GB" — texto livre |
| `condicao` | TEXT NOT NULL | `'Novo'` | Lista fechada: `Novo`\|`Seminovo`\|`Vitrine` (`PRODUTOS_CONDICOES`). Mesma regra de rejeição de `categoria` (BR-027) |
| `descricao` | TEXT | | |
| `sku` | TEXT | | |
| `fornecedor` | TEXT | | |
| `preco_custo` | REAL | `NULL` | Opcional — se ausente, `margem` calculada é `None` |
| `preco_venda` | REAL NOT NULL | | Obrigatório, deve ser `> 0` |
| `quantidade` | INTEGER NOT NULL | `0` | Agregado — usado enquanto o item não tem rastreio por unidade |
| `requer_rastreio_unidade` | INTEGER NOT NULL | `0` | Mesmo padrão de `estoque.requer_imei` — consumido por `unidades_serializadas.produto_id` desde a migração ADR-007 |
| `ativo` | INTEGER NOT NULL | `1` | Visibilidade no catálogo — **não** é o status de unidade em estoque (disponível/reservado/vendido é conceito por unidade física, Sprint Comercial 0.2, não por SKU) |
| `criado_em` | TEXT NOT NULL | `datetime('now')` | |
| `atualizado_em` | TEXT NOT NULL | `datetime('now')` | |

**`margem` não é coluna** — sempre calculada em `irflow_produtos_service.py` (`preco_venda - preco_custo`,
`None` se `preco_custo` ausente), nunca persistida nem editável diretamente (BR-028).

**Índices:** `idx_produtos_categoria`, `idx_produtos_sku`, `idx_produtos_ativo`.

**Relacionamento:** `unidades_serializadas.produto_id` (nullable, FK lógica) desde a migração ADR-007 —
rastreamento por unidade/IMEI de produtos reaproveita a mesma tabela de Estoque, não uma tabela filha
própria. `docs/product/features/VENDAS.md` foi atualizado para apontar `vendas.estoque_unidade_id` para
`unidades_serializadas.id`.

### `estoque_lotes`

Rastreio de lotes de compra por item de estoque (FIFO de custo).

| Coluna | Tipo | Constraint |
|--------|------|------------|
| `id` | INTEGER | PK AUTOINCREMENT |
| `estoque_id` | INTEGER | NOT NULL — FK lógica para `estoque.id` (sem `FOREIGN KEY` declarado) |
| `fornecedor` | TEXT | |
| `valor_compra` | REAL | |
| `quantidade` | INTEGER | quantidade original do lote |
| `quantidade_disponivel` | INTEGER | decrementada ao consumir peça em uma OS |
| `data_compra` | TEXT | |
| `observacoes` | TEXT | |
| `criado_em` | TEXT | |

**Índice:** `idx_lotes_estoque_id` em `(estoque_id)`.

Lotes iniciais são criados retroativamente para itens de `estoque` com `quantidade > 0` que ainda não
tinham lote (migração inline em `criar_tabelas()`, `observacoes = 'lote inicial legado'`).

### `os_pecas` — peças aplicadas a uma OS

| Coluna | Tipo | Observação |
|--------|------|------------|
| `id` | INTEGER PK AUTOINCREMENT | |
| `os_id` | INTEGER | FK lógica para `os.id` |
| `estoque_id` | INTEGER | FK lógica para `estoque.id` |
| `quantidade` | INTEGER | |
| `valor` | REAL | *(ALTER)* |
| `peca_descricao` | TEXT | *(ALTER)* — snapshot da descrição no momento do consumo |
| `peca_fornecedor` | TEXT | *(ALTER)* — snapshot do fornecedor |
| `peca_modelo` | TEXT | *(ALTER)* — snapshot do modelo |

As colunas `peca_*` existem para preservar o histórico mesmo se o item de estoque original for
editado ou removido depois.

### `movimentacoes`

Log de entradas/saídas de estoque.

| Coluna | Tipo |
|--------|------|
| `id` | INTEGER PK AUTOINCREMENT |
| `estoque_id` | INTEGER |
| `tipo` | TEXT |
| `quantidade` | INTEGER |
| `data` | TEXT |

### `custos_operacionais`

| Coluna | Tipo | Constraint |
|--------|------|------------|
| `id` | INTEGER | PK AUTOINCREMENT |
| `descricao` | TEXT | NOT NULL |
| `categoria` | TEXT | |
| `valor` | REAL | NOT NULL |
| `data` | TEXT | |
| `observacoes` | TEXT | |

### `clientes`

Entidade Cliente (Sprint P0.1) — primeiro domínio a seguir a convenção controller/service/repository de
`docs/engineering/ENGINEERING_GUIDE.md` §3.1 (`irflow_clientes_controller.py`,
`irflow_clientes_service.py`, `irflow_clientes_repository.py`).

| Coluna | Tipo | Default |
|--------|------|---------|
| `id` | INTEGER PK AUTOINCREMENT | |
| `nome` | TEXT NOT NULL | |
| `telefone` | TEXT | |
| `email` | TEXT | |
| `cpf_cnpj` | TEXT | |
| `observacoes` | TEXT NOT NULL | `''` |
| `criado_em` | TEXT NOT NULL | `datetime('now')` |
| `atualizado_em` | TEXT NOT NULL | `datetime('now')` |

**Regra de cadastro (service, não schema):** nome obrigatório + ao menos um contato (telefone OU
e-mail) — sem `UNIQUE`/`NOT NULL` em `telefone`/`email`/`cpf_cnpj` porque a deduplicação (por qual campo,
como tratar duplicados existentes) segue `TODO` — decisão de negócio pendente do Product Owner
(`docs/product/features/CLIENTES.md`).

**Índices:** `idx_clientes_nome`, `idx_clientes_telefone`, `idx_clientes_cpf_cnpj`.

### `vendas`

Vendas MVP (2026-07-27, `docs/product/features/VENDAS.md`) — primeiro domínio a nascer com o prefixo
`fluxoly_` (`fluxoly_vendas_controller.py`/`_service.py`/`_repository.py`, ADR-008). Escopo desta fatia:
venda de um único aparelho (unidade serializada) por vez, sem desconto/comissão/garantia/troca/reserva
com timeout — dependem de decisões de negócio ainda pendentes do Product Owner.

| Coluna | Tipo | Default |
|--------|------|---------|
| `id` | INTEGER PK AUTOINCREMENT | |
| `cliente_id` | INTEGER NOT NULL | FK lógica: `clientes.id` |
| `vendedor_id` | INTEGER NOT NULL | FK lógica: `usuarios.id` — sempre o usuário da sessão, nunca escolhido no payload |
| `forma_pagamento` | TEXT NOT NULL | `pix` \| `cartao` \| `dinheiro` \| `transferencia` |
| `valor_total` | REAL NOT NULL | |
| `status` | TEXT NOT NULL | `'concluida'` \| `'cancelada'` (V1.2, 2026-07-27) — `estornada` (financeira) prevista na ADR-009, não implementada ainda |
| `observacoes` | TEXT NOT NULL | `''` — livre (ex.: "retirada amanhã", "venda corporativa") |
| `motivo_cancelamento` | TEXT | *(ALTER, V1.2)* — lista fechada validada no service (BR-032), `NULL` até cancelar |
| `observacao_cancelamento` | TEXT | *(ALTER, V1.2)* — obrigatória quando `motivo_cancelamento='outro'` |
| `cancelado_por` | INTEGER | *(ALTER, V1.2)* — FK lógica: `usuarios.id`, `NULL` até cancelar |
| `cancelado_em` | TEXT | *(ALTER, V1.2)* — `NULL` até cancelar |
| `criado_em` | TEXT NOT NULL | `datetime('now')` |

**Índices:** `idx_vendas_cliente_id`, `idx_vendas_vendedor_id`.

### `vendas_itens`

Modelada como `Venda` + `ItemVenda` desde o início (decisão deliberada, mesmo com exatamente 1 item por
venda nesta fatia) — evita partir a tabela quando a plataforma vender múltiplos itens na mesma operação
(aparelho + acessórios).

| Coluna | Tipo | Default |
|--------|------|---------|
| `id` | INTEGER PK AUTOINCREMENT | |
| `venda_id` | INTEGER NOT NULL | FK lógica: `vendas.id` |
| `unidade_serializada_id` | INTEGER NOT NULL | FK lógica: `unidades_serializadas.id` — obrigatório nesta fatia (só aparelhos rastreados por unidade são vendáveis hoje) |
| `produto_id` | INTEGER | Denormalizado de `unidades_serializadas.produto_id`; `NULL` se a origem da unidade é Estoque |
| `produto_nome` | TEXT NOT NULL | Snapshot no momento da venda — preserva o histórico mesmo se o cadastro do produto/estoque mudar depois |
| `produto_sku` | TEXT | Snapshot, nullable |
| `quantidade` | INTEGER NOT NULL | `1` — sempre 1 nesta fatia (unidade serializada não é fungível); existe para quando itens agregados/não serializados forem vendidos |
| `valor_tabela` | REAL | Snapshot do preço de catálogo (`estoque.valor` ou `produtos.preco_venda`) no momento da venda; `NULL` se o item não tinha preço cadastrado |
| `valor_unitario` | REAL NOT NULL | Preço efetivo da venda — pode divergir de `valor_tabela` (negociação); nenhum dos dois sobrescreve o outro |
| `subtotal` | REAL NOT NULL | `valor_unitario * quantidade`, calculado no repository, nunca recebido do chamador |
| `ativo` | INTEGER NOT NULL | *(ALTER, V1.2)* `DEFAULT 1` — `0` quando a venda-mãe é cancelada (BR-033); distingue a venda vigente de uma unidade das suas vendas canceladas no histórico |
| `criado_em` | TEXT NOT NULL | `datetime('now')` |

**Índices:** `idx_vendas_itens_venda_id`; `idx_vendas_itens_unidade_ativa` (**`UNIQUE` parcial**,
`WHERE ativo = 1`, V1.2 — substitui o `UNIQUE` incondicional `idx_vendas_itens_unidade_serializada_id`
da Vendas MVP) — só uma linha *vigente* por unidade, não uma por vida inteira; permite revenda da mesma
unidade após cancelamento sem perder o histórico da venda cancelada. Ver
`fluxoly_vendas_service.py::iniciar_venda`/`cancelar_venda` e
`irflow_unidades_serializadas_service.py::marcar_como_vendida`/`liberar_unidade_para_venda`, que fazem
`UPDATE ... WHERE status=...` como segunda camada de proteção contra corrida.

### `movimentacoes_caixa`

Financeiro Mínimo (2026-08-08, `docs/engineering/plans/PLAN-financeiro-minimo.md`, BR-067 a BR-069) —
primeira tabela de negócio criada pelo mecanismo formal de migrations (`migrations/versions/
m0002_financeiro_minimo.py`, TD-03). `fluxoly_caixa_controller.py`/`_service.py`/`_repository.py`.

| Coluna | Tipo | Default |
|--------|------|---------|
| `id` | INTEGER PK AUTOINCREMENT | |
| `tipo` | TEXT NOT NULL | `'entrada'` \| `'saida'` |
| `valor` | REAL NOT NULL | sempre positivo — o sinal vem de `tipo`, nunca do valor |
| `descricao` | TEXT | |
| `origem` | TEXT NOT NULL | `DEFAULT 'manual'` — `'manual'` \| `'venda'` \| `'conta_pagar'` \| `'conta_receber'` \| `'compra_aparelho'` (saída, BR-086, desde `m0003`) |
| `origem_id` | INTEGER | FK lógica **polimórfica** — aponta para `vendas.id`/`contas_pagar.id`/`contas_receber.id` conforme `origem` |
| `estornada` | INTEGER NOT NULL | `DEFAULT 0` — estorno nunca apaga a linha (preserva auditoria), só remove do cálculo de saldo |
| `usuario_id` | INTEGER | FK lógica: `usuarios.id` |
| `criado_em` | TEXT NOT NULL | `datetime('now')` |

**Índices:** `idx_movimentacoes_caixa_origem` (`origem, origem_id`); `idx_movimentacoes_caixa_tipo_estornada`
(`tipo, estornada`); `idx_movimentacoes_caixa_venda_ativa` (**`UNIQUE` parcial**, `WHERE origem = 'venda'
AND estornada = 0`, BR-069) — guardião real no banco de que uma venda nunca tem duas entradas de caixa
ativas simultâneas, mesmo padrão de `idx_vendas_itens_unidade_ativa`.

Saldo de caixa é sempre `SOMA(entradas não estornadas) − SOMA(saídas não estornadas)`
(`fluxoly_caixa_repository.py::calcular_saldo`).

Desde `m0003` (2026-11-08): **`idx_movimentacoes_caixa_compra_ativa`** (`UNIQUE` parcial, `WHERE origem =
'compra_aparelho' AND estornada = 0`, BR-086) — uma compra de aparelho nunca tem duas saídas ativas.

### `compras_aparelhos`

Compra de aparelhos para conserto e revenda (2026-11-08, migration
`migrations/versions/m0003_compras_aparelhos.py`, BR-083 a BR-089,
`docs/engineering/plans/PLAN-compra-aparelhos.md`). `fluxoly_compras_aparelhos_controller.py`/`_service.py`/
`_repository.py`. A compra, a unidade serializada que ela cria e a saída de caixa nascem na mesma transação.

| Coluna | Tipo | Observação |
|--------|------|------------|
| `id` | INTEGER PK AUTOINCREMENT | |
| `unidade_serializada_id` | INTEGER NOT NULL | FK lógica — unidade criada pela própria compra (origem Produto) |
| `produto_id` | INTEGER NOT NULL | FK lógica — modelo do catálogo (`requer_rastreio_unidade = 1`) |
| `origem` | TEXT NOT NULL | `marketplace` \| `troca` \| `outro` (validado no service) |
| `cliente_id` | INTEGER | FK lógica — obrigatório quando `origem='troca'`, `NULL` nas demais |
| `venda_id` | INTEGER | FK lógica — opcional, só na troca: venda concluída do mesmo cliente |
| `vendedor_nome` / `vendedor_telefone` | TEXT | Opcionais — quem vendeu o aparelho (dado pessoal, BR-088) |
| `valor_pago` | REAL NOT NULL | `> 0`, arredondado em 2 casas |
| `forma_pagamento` | TEXT NOT NULL | `pix` \| `dinheiro` \| `transferencia` \| `cartao` \| `abatido_na_venda` (só troca) |
| `estado` | TEXT NOT NULL | Texto livre curto |
| `defeito` | TEXT NOT NULL | `DEFAULT ''` — vazio = sem defeito (unidade nasce `disponivel`; com defeito, `em_reparo`) |
| `status` | TEXT NOT NULL | `DEFAULT 'ativa'` — `ativa` \| `cancelada` |
| `motivo_cancelamento` / `cancelado_por` / `cancelado_em` | TEXT / INTEGER / TEXT | `NULL` até cancelar |
| `usuario_id` | INTEGER NOT NULL | Sempre o usuário da sessão |
| `criado_em` | TEXT NOT NULL | `datetime('now')` |

**Índices:** `idx_compras_aparelhos_unidade_ativa` (**`UNIQUE` parcial** `WHERE status = 'ativa'` — uma
unidade tem no máximo uma compra ativa), `idx_compras_aparelhos_criado_em`, `idx_compras_aparelhos_cliente_id`.

### `contas_pagar`

Financeiro Mínimo — `fluxoly_contas_pagar_controller.py`/`_service.py`/`_repository.py`.

| Coluna | Tipo | Default |
|--------|------|---------|
| `id` | INTEGER PK AUTOINCREMENT | |
| `descricao` | TEXT NOT NULL | |
| `categoria` | TEXT | |
| `valor` | REAL NOT NULL | |
| `data_vencimento` | TEXT | |
| `status` | TEXT NOT NULL | `DEFAULT 'pendente'` — `'pendente'` \| `'pago'` \| `'cancelado'` |
| `movimentacao_caixa_id` | INTEGER | FK lógica: `movimentacoes_caixa.id` — preenchida só quando `status` vira `'pago'` |
| `criado_em` | TEXT NOT NULL | `datetime('now')` |
| `atualizado_em` | TEXT NOT NULL | `datetime('now')` |

Baixa (`status: pendente -> pago`) é compare-and-swap (`UPDATE ... WHERE status='pendente'`) e lança a
saída de caixa correspondente na mesma transação (`fluxoly_caixa_service.registrar_saida_de_conta_pagar`,
cursor compartilhado).

### `contas_receber`

Financeiro Mínimo — `fluxoly_contas_receber_controller.py`/`_service.py`/`_repository.py`. Espelho de
`contas_pagar`, com **nenhuma FK ou relação com o domínio Vendas** (BR-068, deliberado — representa só
compromissos financeiros gerais, não parcelamento/inadimplência de venda).

| Coluna | Tipo | Default |
|--------|------|---------|
| `id` | INTEGER PK AUTOINCREMENT | |
| `descricao` | TEXT NOT NULL | |
| `categoria` | TEXT | |
| `valor` | REAL NOT NULL | |
| `data_vencimento` | TEXT | |
| `status` | TEXT NOT NULL | `DEFAULT 'pendente'` — `'pendente'` \| `'recebido'` \| `'cancelado'` |
| `movimentacao_caixa_id` | INTEGER | FK lógica: `movimentacoes_caixa.id` — preenchida só quando `status` vira `'recebido'` |
| `criado_em` | TEXT NOT NULL | `datetime('now')` |
| `atualizado_em` | TEXT NOT NULL | `datetime('now')` |

Baixa (`status: pendente -> recebido`) é compare-and-swap e lança a entrada de caixa correspondente na
mesma transação (`fluxoly_caixa_service.registrar_entrada_de_conta_receber`).

### `dados_loja`

Dados da Loja para o cabeçalho dos documentos da OS para o cliente (2026-11-10, migration
`migrations/versions/m0004_dados_loja.py`, BR-094, `docs/engineering/plans/PLAN-documentos-os-cliente.md`).
`fluxoly_dados_loja_controller.py`/`_service.py`/`_repository.py`. **Linha única:** `id = 1` (garantido por
`CHECK`), criada no primeiro `PUT /api/dados-loja` (upsert). Escrita só `admin`, auditada em `audit_log`
(`entidade = 'dados_loja'`).

| Coluna | Tipo | Observação |
|--------|------|------------|
| `id` | INTEGER PK | `CHECK (id = 1)` |
| `nome_fantasia` | TEXT NOT NULL | `DEFAULT ''` — obrigatório no service (até 120); vazio bloqueia os documentos (BR-098) |
| `razao_social` / `cnpj` / `telefone` / `email` / `endereco` | TEXT NOT NULL | `DEFAULT ''` — opcionais (limites 160/30/40/120/300) |
| `termos_entrada` / `termos_garantia` | TEXT NOT NULL | `DEFAULT ''` — até 4000; impressos no comprovante de entrada/entrega |
| `atualizado_por` | INTEGER | FK lógica — `usuarios.id` do último salvamento |
| `atualizado_em` | TEXT NOT NULL | `datetime('now')` |

### `compras` — lista de compras (versão legada/simplificada)

| Coluna | Tipo | Default |
|--------|------|---------|
| `id` | INTEGER PK AUTOINCREMENT | |
| `produto` | TEXT NOT NULL | |
| `os_id` | INTEGER | |
| `quantidade` | INTEGER NOT NULL | `1` |
| `status` | TEXT | `'PENDENTE'` |
| `criado_em` | TEXT | `''` |
| `atualizado_em` | TEXT | `''` |

> Nota: coexiste com `shopping_list` (mais completa, com workflow de status e log). `compras` parece
> ser a versão anterior — confirmar com o time antes de assumir qual é a fonte de verdade atual para
> novas features.

### `shopping_list`

Lista de compras com workflow de status (entregue na Sprint 1).

| Coluna | Tipo | Default |
|--------|------|---------|
| `id` | INTEGER PK AUTOINCREMENT | |
| `os_id` | INTEGER | |
| `produto_id` | INTEGER | |
| `produto_nome` | TEXT | |
| `quantidade_solicitada` | INTEGER NOT NULL | `1` |
| `quantidade_comprada` | INTEGER NOT NULL | `0` |
| `quantidade_recebida` | INTEGER NOT NULL | `0` |
| `prioridade` | TEXT | `'NORMAL'` |
| `status` | TEXT | `'PENDENTE'` |
| `responsavel_id` | INTEGER | |
| `observacao` | TEXT | `''` |
| `created_at` | TEXT NOT NULL | `datetime('now')` |
| `updated_at` | TEXT NOT NULL | `datetime('now')` |
| `purchased_at` | TEXT | |
| `received_at` | TEXT | |
| `cancelled_at` | TEXT | |

**Índice:** `idx_shopping_list_os_produto` em `(os_id, produto_id, produto_nome)`.

### `shopping_list_logs`

Auditoria de mudanças em itens da lista de compras.

| Coluna | Tipo | Constraint |
|--------|------|------------|
| `id` | INTEGER | PK AUTOINCREMENT |
| `shopping_list_id` | INTEGER | NOT NULL |
| `usuario_id` | INTEGER | quem executou a ação |
| `acao` | TEXT | NOT NULL — ex.: `create`, `update` |
| `valor_anterior` | TEXT | snapshot antes da mudança |
| `valor_novo` | TEXT | snapshot depois da mudança |
| `created_at` | TEXT NOT NULL | `datetime('now')` |

### `login_attempts`

Contador de tentativas de login para rate limiting (Sprint 3, KI-001 — `irflow_rate_limit.py`).

| Coluna | Tipo | Default |
|--------|------|---------|
| `id` | INTEGER PK AUTOINCREMENT | |
| `identificador` | TEXT NOT NULL | IP resolvido via `Fly-Client-IP` &gt; `X-Forwarded-For` &gt; `remote_addr` |
| `sucesso` | INTEGER NOT NULL | `0` ou `1` |
| `criado_em` | TEXT NOT NULL | `datetime('now')` |

**Índice:** `idx_login_attempts_identificador_criado_em` em `(identificador, criado_em)`.

### `audit_log`

Auditoria central reutilizável entre domínios (Sprint 3 — `irflow_audit.py::registrar_log_auditoria`).
Distinta de `shopping_list_logs`, que continua própria desse domínio e não foi migrada para cá.

| Coluna | Tipo | Default |
|--------|------|---------|
| `id` | INTEGER PK AUTOINCREMENT | |
| `entidade` | TEXT NOT NULL | `'cliente'` \| `'estoque_unidade'` \| outros domínios futuros |
| `entidade_id` | INTEGER | |
| `usuario_id` | INTEGER | quem executou a ação |
| `acao` | TEXT NOT NULL | `create` \| `update` \| `delete` \| `status_change` |
| `valor_anterior` | TEXT | snapshot JSON antes da mudança |
| `valor_novo` | TEXT | snapshot JSON depois da mudança |
| `criado_em` | TEXT NOT NULL | `datetime('now')` |

**Índice:** `idx_audit_log_entidade` em `(entidade, entidade_id)`.

### `password_reset_tokens`

Recuperação de senha via token de uso único gerado pelo admin (Sprint 3, Unidade 4) — não é
self-service por e-mail, o admin gera e entrega o link manualmente.

| Coluna | Tipo | Default |
|--------|------|---------|
| `id` | INTEGER PK AUTOINCREMENT | |
| `usuario_id` | INTEGER NOT NULL | |
| `token` | TEXT UNIQUE NOT NULL | `secrets.token_urlsafe(24)` |
| `criado_em` | TEXT NOT NULL | `datetime('now')` |
| `expira_em` | TEXT NOT NULL | `criado_em` + `IR_FLOW_PASSWORD_RESET_TOKEN_HOURS` (default 24h) |
| `usado_em` | TEXT | `NULL` até o token ser consumido; também usado para invalidar token anterior ao gerar um novo |
| `criado_por` | INTEGER | admin que gerou o token |

**Índice:** `idx_password_reset_tokens_usuario_id` em `(usuario_id)`.

### `os_checklists`

Checklist de diagnóstico do aparelho, acessível publicamente via token (rota
`/checklist/:token` no frontend, sem autenticação — ver `ARCHITECTURE.md` seção 5).

| Coluna | Tipo | Default |
|--------|------|---------|
| `id` | INTEGER PK AUTOINCREMENT | |
| `os_id` | INTEGER NOT NULL UNIQUE | uma checklist por OS |
| `access_token` | TEXT UNIQUE | token de acesso público — **não expira** (ver KI-002) |
| `status_touch` | TEXT NOT NULL | `'nao_testado'` |
| `status_audio` | TEXT NOT NULL | `'nao_testado'` |
| `status_microfone` | TEXT NOT NULL | `'nao_testado'` |
| `status_camera` | TEXT NOT NULL | `'nao_testado'` |
| `status_botoes` | TEXT NOT NULL | `'nao_testado'` |
| `observacoes` | TEXT NOT NULL | `''` |
| `executado_por` | TEXT NOT NULL | `''` |
| `origem` | TEXT NOT NULL | `''` |
| `resultado_json` | TEXT NOT NULL | `'{}'` |
| `criado_em` | TEXT NOT NULL | `''` |
| `atualizado_em` | TEXT NOT NULL | `''` |

### `integracao_sync_estado`

Estado key-value da sincronização com integrações externas (MercadoPhone).

| Coluna | Tipo | Constraint |
|--------|------|------------|
| `chave` | TEXT | PK |
| `valor` | TEXT | |

### `integracao_os_vistas`

Deduplicação de OS já importadas de sistemas externos.

| Coluna | Tipo | Constraint |
|--------|------|------------|
| `origem` | TEXT | NOT NULL, parte da PK composta |
| `id_externo` | TEXT | NOT NULL, parte da PK composta |
| `primeira_visualizacao` | TEXT | |

PK composta `(origem, id_externo)`.

---

## 3. Relacionamentos (lógicos — sem `FOREIGN KEY` declarado no schema)

```
usuarios ──< shopping_list.responsavel_id
usuarios ──< shopping_list_logs.usuario_id

os ──< os_pecas.os_id
os ──< os_checklists.os_id (1:1, UNIQUE)
os ──< compras.os_id
os ──< shopping_list.os_id
os >─< reparos  (via os_reparos, N:N)
os ── reparos.reparo_id (legado, 1:N — ver os_reparos para o modelo atual)

estoque ──< estoque_lotes.estoque_id
estoque ──< os_pecas.estoque_id
estoque ──< movimentacoes.estoque_id
estoque ──< shopping_list.produto_id

clientes ──< os.cliente_id (Sprint P0.1 — nullable, sem backfill)
usuarios ──< audit_log.usuario_id
usuarios ──< password_reset_tokens.usuario_id
estoque ──< unidades_serializadas.estoque_id (Sprint P0.1, opcional desde ADR-007)
produtos ──< unidades_serializadas.produto_id (ADR-007, opcional)
estoque_lotes ──< unidades_serializadas.lote_id (opcional)

clientes ──< vendas.cliente_id (Vendas MVP, 2026-07-27)
usuarios ──< vendas.vendedor_id (Vendas MVP)
vendas ──< vendas_itens.venda_id (Vendas MVP)
unidades_serializadas ──< vendas_itens.unidade_serializada_id (Vendas MVP, UNIQUE — 1:1 efetivo, nunca a mesma unidade em duas vendas)
produtos ──< vendas_itens.produto_id (Vendas MVP, denormalizado, opcional)
```

`login_attempts` não tem relacionamento com `usuarios` — `identificador` é o IP resolvido do cliente, não
um `usuario_id` (a tentativa é registrada mesmo sem o login ter sido bem-sucedido).

**Nota:** nenhuma constraint `FOREIGN KEY` é declarada no schema — integridade referencial é mantida
apenas pela lógica da aplicação. Isso é dívida técnica implícita não listada individualmente em
`KNOWN_ISSUES.md`; ao adicionar `FOREIGN KEY` no futuro, documentar como ADR (mudança de schema com
potencial de rejeitar dados legados órfãos).

---

## 4. Isolamento em Testes

- Testes **nunca** usam `database.db`. `tests/conftest.py` define `IR_FLOW_DATA_DIR` como um
  diretório temporário (`tempfile.mkdtemp()`) **antes** de importar `app.py`, já que `DB_PATH` é
  resolvido na carga do módulo.
- `criar_tabelas()` é chamada explicitamente na fixture `app` (escopo `session`) para garantir o
  schema no banco temporário.
- Isso significa que os testes usam SQLite em arquivo (dentro de um diretório temp), não
  `:memory:` — mas o isolamento de `database.db` real está garantido.

---

## 5. Convenções (ver também `ENGINEERING_GUIDE.md` seção 5)

- Tabelas: `snake_case` no plural.
- Colunas: `snake_case`.
- Foreign keys lógicas: `<tabela_singular>_id`.
- Índices: `idx_<tabela>_<coluna(s)>`.
- Datas armazenadas como `TEXT` (não há tipo `DATE`/`DATETIME` nativo usado) — formato observado:
  `YYYY-MM-DD HH:MM:SS` ou `datetime('now')` (UTC, formato SQLite padrão).
