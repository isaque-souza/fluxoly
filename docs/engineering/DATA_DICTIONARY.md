# DATA_DICTIONARY.md — Dicionário de Dados

Complementa `docs/engineering/DATABASE.md` (schema, tipos, índices) com a camada de **governança**: quem
cria, altera, exclui e vê cada dado, de onde ele vem e para onde vai. `DATABASE.md` continua sendo a
fonte de verdade para tipo/constraint SQL — este documento não duplica isso, referencia.

**Última revisão:** 2026-07-25
**Fonte:** leitura direta do código (`irflow_blueprints_api.py`, `irflow_os.py`, `app.py`) — cada
afirmação de "quem pode" é verificada na rota real, não assumida a partir do nome do perfil.

**Correção de registro (2026-07-25 — Sprint Segurança 1.0, `docs/security/SECURITY_AUDIT_2026-07.md`):**
o achado abaixo (revisão de 2026-07-10) motivou uma correção — rotas de mutação de OS agora exigem
perfil `admin`/`tecnico`; rotas de mutação de Estoque exigem `admin`/`estoque` (perfil novo). Texto
original preservado abaixo como registro do estado anterior:

~~a maioria das rotas de mutação da API (`OS`, `Estoque`) checa apenas `usuario_logado()` — qualquer
perfil autenticado (`admin`, `tecnico` ou `vendedor`) pode criar, editar ou excluir uma OS ou um item de
estoque hoje. Não há restrição por perfil nessas rotas, diferente de `Usuários` (admin-only) e
`Shopping List` (`admin`/`tecnico`/`comprador`).~~ Ver `docs/product/BUSINESS_RULES.md` BR-030 para a
regra atual.

---

## `usuarios`

**Quem cria/altera/exclui:** apenas perfil `admin` (`usuario_admin()`, checado em
`listar_usuarios`/`criar_usuario`/`atualizar_usuario`/`deletar_usuario`).
**Quem vê:** apenas `admin` (mesma checagem na listagem).
**Origem:** cadastro manual pelo admin. **Destino:** sessão (`session["usuario_id"]`, `usuario_perfil`),
`ROUTE_PERMISSIONS` (rotas legadas).

| Campo | Tipo | Obrigatório | Editável após criação? | Observação |
|---|---|---|---|---|
| `id` | INTEGER | — (auto) | Não | PK |
| `nome` | TEXT | Sim | Sim | Nome de exibição |
| `usuario` | TEXT | Sim | Sim | `UNIQUE` — login |
| `senha_hash` | TEXT | Sim | Sim (via troca de senha) | **Nunca retornado** em nenhuma resposta de API — verificado em `listar_usuarios` (só retorna `id/nome/usuario/perfil/ativo`) |
| `perfil` | TEXT | Sim | Sim | `admin`\|`tecnico`\|`vendedor`\|`estoque` — sem hierarquia (BR-003); fonte única `irflow_core.py::PERFIS_OPCOES` |
| `ativo` | INTEGER | Sim | Sim | Usuário não pode alterar o próprio (`ativo`/exclusão bloqueados enquanto logado — BR-002) |

---

## `os` — Ordens de Serviço

**Quem cria/altera/exclui:** perfil `admin` ou `tecnico` (desde 2026-07-25, BR-030 — antes era qualquer
perfil autenticado, ver achado no topo do documento).
**Quem vê:** qualquer perfil autenticado.
**Origem:** formulário de nova OS (frontend) ou importação via integração MercadoPhone
(`origem_integracao='mercado_phone'`).
**Destino:** relatórios (Técnicos), dashboard, `shopping_list` (peças sugeridas).

| Campo | Tipo | Obrigatório | Editável após criação? | Observação |
|---|---|---|---|---|
| `id` | INTEGER | — (auto) | Não | PK |
| `tipo` | TEXT | Sim | Sim | `Assistencia`\|`Garantia` (opções exibidas; `Upgrade` removido em 2026-11-06, ADR-014 — o campo continua texto livre) |
| `cliente` | TEXT | Sim | Sim | **Texto solto, não FK** — ver `docs/engineering/DOMAIN_MODEL.md` seção 2; sem valor especial desde 2026-11-06 (ADR-014) |
| `aparelho` | TEXT | Sim (via `modelo`) | Sim | Espelha `modelo` |
| `tecnico` | TEXT | Sim | Sim | Texto solto, não FK para `usuarios` |
| `reparo_id` | INTEGER | Não | Sim (derivado) | Legado — 1 reparo; ver `os_reparos` para o modelo N:N atual |
| `status` | TEXT | Sim | Sim | Ver `irflow_core.py::STATUS_OS_VALIDOS`; mudança para `Cancelado` devolve estoque (BR-010) |
| `valor_cobrado` | REAL | Sim | Sim | Auto-sugerido por `GET /api/precos/sugerir`, sobrescrevível |
| `valor_descontado` | REAL | Sim | Sim | Não pode ser negativo (`ler_valores_financeiros_form`) |
| `custo_pecas` | REAL | Não (calculado) | Recalculado a cada edição | Nunca editado diretamente pelo usuário |
| `data` | TEXT | Sim | Sim | Data da OS, não de criação da linha |
| `data_finalizado` | TEXT | Não | Sim (indireto) | Ver BR-013 — limpo se status muda para não-Finalizado |
| `modelo` | TEXT | Sim | Sim | Normalizado via `normalizar_modelo_iphone` |
| `cor` | TEXT | Não | Sim | — |
| `imei` | TEXT | Não | Sim | Normalizado via `normalizar_imei`; **sem unicidade declarada** — dois registros de `os` podem ter o mesmo IMEI hoje |
| `vendedor` | TEXT | Não | Sim | Deve ser vendedor cadastrado válido (BR-014) |
| `observacoes` | TEXT | Não | Sim | — |
| `origem_integracao` / `id_externo_integracao` | TEXT | Não | Não (setado só na criação via integração) | Usado para deduplicação (`integracao_os_vistas`) |

---

## `estoque`

**Quem cria/altera/exclui:** perfil `admin` ou `estoque` (perfil novo, desde 2026-07-25, BR-030 — antes
era qualquer perfil autenticado, ver achado no topo do documento).
**Quem vê:** qualquer perfil autenticado.
**Origem:** cadastro manual ou devolução automática de peça (BR-006, cria lote de retorno).
**Destino:** `os_pecas` (consumo), `shopping_list` (reposição sugerida), relatórios.

| Campo | Tipo | Obrigatório | Editável após criação? | Observação |
|---|---|---|---|---|
| `id` | INTEGER | — (auto) | Não | PK |
| `descricao` | TEXT | Sim | Sim | — |
| `valor` | REAL | Sim | Sim | Recalculado como custo médio em alguns fluxos (`_recalcular_custo_medio`) |
| `fornecedor` | TEXT | Não | Sim | Texto solto, não FK |
| `quantidade` | INTEGER | Sim | Não diretamente — só via movimentação (BR-004, BR-007) | Nunca fica negativa |
| `sku` | TEXT | Não | Sim | Auto-gerado (`ITEM-<id>`) se ausente; índice `idx_estoque_sku` |
| `modelo`/`tipo`/`qualidade` | TEXT | Não | Sim | Índice composto `idx_estoque_tripla`; usado para achar peça compatível |
| — | — | — | **Exclusão** | Bloqueada se peça em uso em OS aberta (BR-005) |

**Nota de gap de produto:** não há coluna de IMEI individual nesta tabela — ver
`docs/company/BRAND_IDENTITY.md` seção 2 e `docs/company/PRODUCT_REQUIREMENTS.md` (dor "IMEIs perdidos").

## `estoque_lotes`

**Quem altera:** sistema apenas (nunca editado diretamente por usuário — só via consumo/devolução).
**Quem vê:** qualquer perfil autenticado (tela de estoque).

| Campo | Tipo | Obrigatório | Editável após criação? | Observação |
|---|---|---|---|---|
| `quantidade` | INTEGER | Sim | Não | Quantidade original do lote — imutável |
| `quantidade_disponivel` | INTEGER | Sim | Sim (só pelo sistema) | Decrementada por `_consumir_lotes_fifo`, incrementada por devolução |
| `observacoes` | TEXT | Não | Não | `'lote inicial legado'` ou `'retorno <tipo>'` — auto-gerado, não editável pelo usuário |

---

## `os_pecas`

**Quem cria/exclui:** sistema, como efeito colateral de editar/cancelar/excluir uma OS — nunca uma rota
direta de CRUD própria.

| Campo | Tipo | Observação |
|---|---|---|
| `peca_descricao`/`peca_fornecedor`/`peca_modelo` | TEXT | **Snapshot** no momento do consumo — preserva histórico mesmo se o item de `estoque` original for editado ou removido depois |

## `movimentacoes`

**Quem cria:** sistema, nunca diretamente pelo usuário — log de entrada/saída de estoque.
**Quem vê:** qualquer perfil autenticado (`GET /api/estoque/movimentacoes`).

---

## `shopping_list` / `shopping_list_logs`

**Quem cria:** qualquer perfil autenticado.
**Quem altera status / exclui:** apenas perfil em `("admin", "tecnico", "comprador")`
(`shopping_status`, `shopping_delete`).

> **Achado:** `"comprador"` é checado no código como perfil autorizado, mas **não é um valor de `perfil`
> documentado no schema** (`docs/engineering/DATABASE.md` lista apenas `admin`\|`tecnico`\|`vendedor` para
> a coluna `usuarios.perfil`). Na prática, hoje só `admin`/`tecnico` conseguem satisfazer essa checagem —
> `"comprador"` é inalcançável a menos que exista fora do fluxo normal de criação de usuário. Não
> corrigido aqui — é achado de documentação, não código; candidato a `KNOWN_ISSUES.md` ou confirmação
> com o Product Owner sobre se `comprador` deveria ser um perfil real.

| Campo | Tipo | Obrigatório | Observação |
|---|---|---|---|
| `responsavel_id` | INTEGER | Não | FK lógica para `usuarios.id` |
| `status` | TEXT | Sim | Workflow com timestamp próprio por transição (BR-015) |

`shopping_list_logs`: **quem vê** — não exposto por rota própria hoje (auditoria interna); toda mudança
gera log automaticamente (BR-016), nunca editável.

---

## `os_checklists`

**Quem cria:** sistema, ao abrir uma OS. **Quem altera:** qualquer pessoa com o `access_token` —
**rota pública, sem autenticação** (`/checklist/:token`, ver `docs/engineering/ARCHITECTURE.md` seção 5).
**Quem vê:** idem — o token **não expira** (KI-002, `docs/operations/KNOWN_ISSUES.md`).

| Campo | Tipo | Observação |
|---|---|---|
| `access_token` | TEXT | `UNIQUE`, gerado na criação — nunca regenerado hoje |
| `status_touch`/`status_audio`/`status_microfone`/`status_camera`/`status_botoes` | TEXT | Preenchidos via a própria rota pública, sem validação de perfil |

---

## Tabelas de referência e integração (governança simples)

| Tabela | Quem cria/altera | Quem vê | Observação |
|---|---|---|---|
| `reparos` | Qualquer usuário autenticado (via criação implícita ao salvar OS) | Todos | `obter_ou_criar_reparo` cria sob demanda |
| `os_reparos` | Sistema (reflexo de `os.reparo_ids`) | Todos | PK composta, sem coluna própria além das FKs |
| `custos_operacionais` | Qualquer usuário autenticado | Todos | Sem regra de negócio própria identificada além de CRUD simples |
| `compras` (legado) | Nenhuma rota ativa aponta para esta tabela hoje | — | Candidata a remoção (KI-014); ver `docs/engineering/DATABASE.md` |
| `dados_loja` | Só `admin` (`PUT /api/dados-loja`, auditado) | Todo usuário autenticado; impresso nos documentos da OS para o cliente | Linha única (BR-094) |
| `integracao_sync_estado` / `integracao_os_vistas` | Sistema apenas (sincronização MercadoPhone) | Não exposto por rota própria | Autenticação por token, fora de `ROUTE_PERMISSIONS` (R-07) |

---

## Relacionamentos

Ver `docs/engineering/DATABASE.md` seção 3 — nenhuma `FOREIGN KEY` é declarada no schema; toda
integridade referencial listada ali (e resumida acima como "FK lógica") é mantida apenas pela lógica da
aplicação, não pelo banco.

---

## Documentos relacionados

- `docs/engineering/DATABASE.md` — schema completo, tipos e índices (fonte de verdade para SQL)
- `docs/product/BUSINESS_RULES.md` — regras citadas aqui (BR-002 a BR-016)
- `docs/company/PRODUCT_REQUIREMENTS.md` — dor "funcionário vender abaixo do preço permitido", relevante ao achado de ausência de restrição por perfil em OS/Estoque
- `docs/company/VISION.md` — princípio de interface por perfil, relevante à falta de granularidade de acesso hoje
