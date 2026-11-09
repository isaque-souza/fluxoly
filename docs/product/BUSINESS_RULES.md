# BUSINESS_RULES.md — Livro de Regras de Negócio

Regras de negócio da Fluxoly em um único lugar, numeradas e rastreáveis — não código, não schema, apenas
a regra em si e de onde ela vem. Antes deste documento, essas regras estavam espalhadas entre
`docs/product/features/VENDAS.md`, comportamento implícito do código, e conversas — cada uma reconstruída
do zero sempre que alguém precisava confirmar "isso já é uma regra ou é só o que o código faz hoje?".

**Última revisão:** 2026-07-29
**Regra de escrita:** toda entrada tem status e fonte. Nenhuma regra aqui foi inventada — ou vem do
código real (lido linha a linha, citado com arquivo/função), ou de uma decisão já registrada em
`VENDAS.md`/`BRAND_IDENTITY.md`, ou de input direto do Product Owner nesta conversa.

**Legenda de status:**
- ✅ **Implementado** — o código hoje aplica essa regra; verificado lendo o código-fonte diretamente.
- 📋 **Especificado** — decisão de negócio já tomada (`VENDAS.md` ou Product Owner), mas o domínio ainda
  não existe no código (Vendas).
- 🟡 **Observado, não confirmado como decisão** — comportamento real do código, mas sem registro de que
  foi uma escolha deliberada de negócio (ver nota em cada caso).

---

## Autenticação e Usuários

**BR-001 — ✅ Implementado**
Login só é bem-sucedido se o usuário está ativo (`ativo = 1`) e o hash da senha confere.
*Fonte: `irflow_blueprints_auth.py`, `POST /api/auth/login`; `docs/engineering/DATABASE.md` tabela `usuarios`.*

**BR-002 — ✅ Implementado**
Um usuário não pode desativar nem excluir a própria conta enquanto está logado.
*Fonte: `docs/engineering/DATABASE.md` tabela `usuarios`; `tests/test_users.py`.*

**BR-003 — ✅ Implementado**
Perfis (`admin`, `tecnico`, `vendedor`, `estoque` desde 2026-07-25) não têm hierarquia entre eles — cada
rota checa a lista explícita de perfis permitidos. **Correção de registro (2026-07-25):**
`ROUTE_PERMISSIONS` (`app.py`) só cobre as views legadas server-rendered — bypassa explicitamente toda
rota `/api/*`, que é o que o frontend React realmente usa. Rotas de mutação de OS/Estoque na API checam
perfil individualmente dentro de cada view (ver BR-030), não via `ROUTE_PERMISSIONS`.
*Fonte: `docs/engineering/ARCHITECTURE.md` seção 4; `docs/security/SECURITY_AUDIT_2026-07.md`.*

---

## Estoque

**BR-004 — ✅ Implementado**
Consumo de peça é sempre debitado por lote, do mais antigo para o mais novo (FIFO).
*Fonte: `irflow_os.py::_consumir_lotes_fifo`.*

**BR-005 — ✅ Implementado**
Um item de estoque não pode ser excluído enquanto estiver em uso (`os_pecas`) em uma OS que não esteja
`Finalizado` nem `Cancelado`.
*Fonte: `irflow_blueprints_api.py::deletar_estoque`.*

**BR-006 — ✅ Implementado**
Devolução de peça ao estoque cria um novo lote de retorno — nunca reincorpora silenciosamente ao lote de
origem, preservando rastreabilidade de que aquela quantidade voltou por devolução.
*Fonte: `irflow_os.py::_criar_lote_retorno`.*

**BR-007 — ✅ Implementado**
Quantidade de estoque nunca fica negativa — todo decremento é limitado a zero (`MAX(0, quantidade - 1)`).
*Fonte: `irflow_os.py::consumir_peca_da_os`; corrigido como hotfix B-11 na Sprint 2.5.*

---

## Ordens de Serviço (Assistência)

**BR-008 — ✅ Implementado**
Excluir uma OS que não está `Finalizado` nem `Cancelado` devolve automaticamente todas as peças
consumidas ao estoque.
*Fonte: `irflow_blueprints_api.py::deletar_ordem`.*

**BR-009 — ✅ Implementado**
Excluir uma OS que já está `Finalizado` ou `Cancelado` **não** devolve peças novamente — a devolução já
ocorreu quando o status mudou, evitando duplicar o retorno ao estoque.
*Fonte: mesma função de BR-008.*

**BR-010 — ✅ Implementado**
Mudar o status de uma OS para `Cancelado` (vindo de um status não-cancelado) devolve as peças ao estoque.
*Fonte: `irflow_blueprints_api.py::atualizar_status_os`.*

**BR-011 — ✅ Implementado**
Editar uma OS não-cancelada (`PUT /api/ordens/<id>`) devolve as peças atualmente registradas e reconsome
as peças do novo payload — é uma substituição atômica, não um ajuste incremental.
*Fonte: `irflow_blueprints_api.py::atualizar_ordem`.*

**BR-012 — ✅ Implementado**
Peça incompatível com o modelo da OS bloqueia a atualização inteira (rollback) — nunca é salva
silenciosamente como incompatível.
*Fonte: `irflow_os.py::modelo_compativel`, usado em `atualizar_ordem`.*

**BR-013 — ✅ Implementado (era bug, corrigido em 2026-07-10)**
Editar uma OS (`PUT`) ou mudar seu status (`PATCH .../status`) exige um `status` explícito e válido no
payload — requisição sem `status` ou com valor desconhecido é rejeitada com erro, nunca silenciosamente
aceita. `data_finalizado` só recebe valor quando o **novo** status explicitamente enviado é `Finalizado`
(preservando a data original se já existia); ao mudar deliberadamente para qualquer outro status,
`data_finalizado` é limpo (`NULL`) — mas só quando o chamador de fato pediu essa mudança.
*Fonte: `atualizar_ordem` e `atualizar_status_os`, `irflow_blueprints_api.py`.* **Histórico:** até
2026-07-10 esta regra não existia — `normalizar_status_os()` sem `status_padrao=""` fazia `status`
ausente/inválido ser silenciosamente normalizado para `"Em andamento"`, então editar uma OS Finalizada
sem reenviar `status` a reabria e apagava `data_finalizado` sem erro. Corrigido via
`hotfix/status-os-padrao-vazio` (KI-015, `docs/operations/KNOWN_ISSUES.md`) — as duas correções já
existiam prontas na branch `test/sprint-2-4-regras-negocio-os` desde 2026-07-07 mas nunca haviam chegado
a `main`.

**BR-014 — ✅ Implementado (exceção revogada em 2026-11-06, ADR-014)**
O vendedor informado em uma OS deve ser um vendedor cadastrado válido, sem exceção. Até 2026-11-06 o
cliente `"IR Phones"` (bucket interno de relatório) era isento dessa validação, e o tipo "Upgrade" / campo
`interna_ir_phones` convertiam a OS em OS interna IR Phones (tabela de preço `ir_phones`, fora da lista
de garantias, relatório mensal próprio). Tudo isso foi removido no desvínculo com a IR Phones (ADR-014).
*Fonte: `irflow_os.py::vendedor_valido`, usado em `criar_ordem` e `atualizar_ordem`.*

---

## Compras / Lista de Compras (Shopping List)

**BR-015 — ✅ Implementado**
Todo item de lista de compras segue um workflow de status (`PENDENTE` → outros estados → `RECEBIDO` ou
cancelado), com timestamp próprio por transição (`purchased_at`, `received_at`, `cancelled_at`).
*Fonte: `docs/engineering/DATABASE.md` tabela `shopping_list`.*

**BR-016 — ✅ Implementado**
Toda mudança em um item da lista de compras é auditada — log com valor anterior, valor novo, usuário e
ação.
*Fonte: `docs/engineering/DATABASE.md` tabela `shopping_list_logs`.*

---

## Clientes

**BR-023 — ✅ Implementado**
Cadastro de cliente exige nome e ao menos um contato (telefone ou e-mail) — sem isso o cliente não pode
ser reencontrado depois.
*Fonte: `irflow_clientes_service.py::criar_cliente`/`atualizar_cliente`; `docs/product/features/CLIENTES.md`
"Decisões estruturais".*

**BR-024 — ✅ Implementado**
Cliente com OS vinculada (`os.cliente_id`) não pode ser excluído — mesmo padrão de BR-005 (item de
estoque em uso não pode ser excluído).
*Fonte: `irflow_clientes_service.py::excluir_cliente`, `irflow_clientes_repository.py::possui_os_vinculada`;
`docs/product/features/CLIENTES.md` "Casos de erro".*

---

## Unidades_Serializadas (rastreamento por IMEI/serial)

*Tabela evoluída de `estoque_unidades` na migração ADR-007 (2026-07-21) — mesmas regras abaixo,
estendidas para cobrir origem em `estoque` OU `produtos`.*

**BR-025 — ✅ Implementado**
Uma unidade individual por IMEI só pode ser cadastrada com origem em exatamente um de: um item de
estoque marcado com `requer_imei = 1`, ou um produto marcado com `requer_rastreio_unidade = 1` —
cadastro sem nenhuma origem, com ambas, ou em item/produto não marcado é rejeitado.
*Fonte: `irflow_unidades_serializadas_service.py::criar_unidade`; `docs/product/features/IMEI.md`
"Decisões estruturais"; ADR-007 (Regra de Ouro).*

**BR-026 — ✅ Implementado**
Transição de status de uma unidade só é permitida entre `disponivel`, `em_reparo` e `devolvido`
(`disponivel ↔ em_reparo`, `em_reparo → devolvido`, `devolvido → disponivel` direto) — `reservado` e
`vendido` existem no schema para o futuro módulo de Vendas, mas nenhuma transição desta sprint os
produz ou aceita como destino.
*Fonte: `irflow_unidades_serializadas_service.py::TRANSICOES_VALIDAS`; `docs/product/features/IMEI.md`,
decisão confirmada com o usuário em 2026-07-11 (devolvido → disponivel direto).*

---

## Produtos (catálogo comercial)

Domínio novo, Sprint Comercial 0.1 — catálogo de itens à venda (iPhone, Apple Watch, AirPods,
Acessório), separado do domínio Estoque (peças de reparo). Decisão de arquitetura investigada e
confirmada com o usuário antes de implementar: `estoque.tipo`/`qualidade` são listas fechadas
hardcoded para peça de reparo, incompatíveis com o vocabulário de um catálogo comercial.

**BR-027 — ✅ Implementado**
`categoria` de um produto só pode ser uma das quatro da lista fechada (iPhone, Apple Watch, AirPods,
Acessório) e `condicao` só pode ser uma de (Novo, Seminovo, Vitrine) — valor fora dessas listas é
**rejeitado com 400**, nunca normalizado/mascarado para um valor default.
*Fonte: `irflow_produtos_service.py::_validar_campos`; `PRODUTOS_CATEGORIAS`/`PRODUTOS_CONDICOES` em
`irflow_reference_data.py`. Decisão deliberada: `_normalizar_tipo_estoque`/`_normalizar_qualidade_estoque`
mascaram entrada desconhecida com um default silencioso — esse padrão já causou duas dívidas reais
neste projeto (KI-015, KI-016), não repetido em código novo.*

**BR-028 — ✅ Implementado**
Margem de um produto (preço de venda − preço de custo) nunca é persistida como coluna — é sempre
calculada no momento da leitura, e é `None` quando o preço de custo não foi informado.
*Fonte: `irflow_produtos_service.py::_produto_para_dict`; mesmo princípio de BR-019 (`vendas.margem`).*

**BR-029 — ✅ Implementado**
Criar, editar ou excluir um produto do catálogo é restrito ao perfil `admin` (preço/margem é dado
sensível); listar e consultar é permitido a qualquer usuário autenticado (vendedor precisa consultar o
catálogo numa venda).
*Fonte: `irflow_produtos_controller.py`. Decisão de negócio V1, conservadora — abrir criação/edição
para outros perfis é decisão pendente de validação com cliente real, ver
`docs/company/CUSTOMER_FEEDBACK.md`.*

---

## Vendas (especificado, não implementado)

Decisões já tomadas em conversa entre Product Owner e engenharia (2026-07-09), registradas em
`docs/product/features/VENDAS.md` — nenhuma delas está no código ainda.

**BR-017 — 📋 Especificado**
Um IMEI só pode estar reservado ou vendido em um atendimento por vez; a reserva expira automaticamente se
a venda não fechar, liberando o aparelho.
*Fonte: `VENDAS.md` — "Fluxo completo", "Decisões já tomadas".*

**BR-018 — 📋 Especificado**
Desconto acima do limite do vendedor exige aprovação de um `admin`; sem admin disponível, a venda fica
bloqueada em "aguardando aprovação" — nunca há bypass.
*Fonte: `VENDAS.md` — "Decisões já tomadas", "Casos de erro".*

**BR-019 — 📋 Especificado**
Comissão do vendedor é sempre calculada sobre a margem (venda − custo), nunca sobre o valor bruto.
*Fonte: `VENDAS.md` — "Decisões já tomadas", "Critérios de aceite".*

**BR-020 — 📋 Especificado — refinada pela discovery de 2026-07-29, ver BR-055 a BR-066**
Garantia de venda tem prazo próprio, independente do prazo fixo de 90 dias hardcoded do reparo. A
discovery da V1.5 (2026-07-29) substituiu o modelo original "prazo fixo por tipo de aparelho novo/
seminovo" por um cadastro configurável de Tipos de Garantia, atribuído manualmente por item — não uma
regra de prazo fixa por condição do aparelho.
*Fonte: `VENDAS.md` — "Decisões já tomadas"; "V1.5 — Garantia".*

**BR-021 — 📋 Especificado**
Aparelho escolhido sem estoque disponível no momento da confirmação gera erro explícito antes do
pagamento, nunca depois.
*Fonte: `VENDAS.md` — "Casos de erro".*

**BR-022 — ✅ Implementado (pré-requisito pronto; Vendas em si segue não implementado)**
Cliente é uma entidade própria (tabela `clientes`) — implementado na Sprint P0.1 como fundação
reutilizável, antes do módulo de Vendas em si existir. `os.cliente_id` (aditivo, nullable) já permite
vincular uma OS a um cliente, mas nenhuma venda existe ainda para aplicar a regra "nenhuma venda salva
nome como texto solto" — isso será validado quando `VENDAS.md` for implementado.
*Fonte: `irflow_clientes_service.py` (BR-023, BR-024); `VENDAS.md` — "Critérios de aceite";
`docs/engineering/DOMAIN_MODEL.md` seção 1.12.*

### V1.2 — Cancelamento de venda (implementado em 2026-07-27)

Fecha a candidata *"uma venda cancelada devolve o IMEI ao estoque"* (ver histórico abaixo) e as decisões
correspondentes de `ADR-009` deixadas deliberadamente em aberto. Discuss-phase completa, sem código
escrito — ver `VENDAS.md` seção "V1.2 — Cancelamento" para o relato completo do raciocínio.

**BR-031 — ✅ Implementado (2026-07-27, V1.2)**
Cancelamento de venda concluída: `admin` pode cancelar qualquer venda; `vendedor` só pode cancelar vendas
que ele mesmo realizou; `tecnico` e demais perfis não podem cancelar. Sem limite de tempo — segurança vem
de perfil + motivo obrigatório + auditoria, não de janela temporal (janela pode virar configuração por
loja no futuro, não decidida/implementada agora).
*Fonte: `VENDAS.md` — "V1.2 — Cancelamento".*

**BR-032 — ✅ Implementado (2026-07-27, V1.2)**
Cancelamento exige motivo de lista fechada (`cliente_desistiu` \| `erro_lancamento` \| `imei_incorreto` \|
`venda_duplicada` \| `pagamento_nao_concluido` \| `produto_indisponivel` \| `outro`), valor fora da lista
rejeitado (mesmo padrão de `categoria`/`condicao` em Produtos, BR-027) — nunca normalizado. Quando
`outro`, uma descrição complementar é obrigatória. Persistido em dois campos:
`motivo_cancelamento` (lista fechada) + `observacao_cancelamento` (texto, condicional).
*Fonte: `VENDAS.md` — "V1.2 — Cancelamento".*

**BR-033 — ✅ Implementado (2026-07-27, V1.2)**
Cancelar uma venda devolve a Unidade Serializada vendida para `disponivel` — mesma mecânica de
`devolvido → disponivel` já usada em Assistência —, via função de domínio dedicada
(`liberar_unidade_para_venda`), nunca por atribuição direta de `status` espalhada pelo código. Sem
migração para os dois eixos do `ADR-009` (Estado Operacional × Situação Comercial) nesta fase — fica para
quando Garantia/Troca exigirem a ortogonalidade de fato.
*Fonte: `VENDAS.md` — "V1.2 — Cancelamento"; `docs/engineering/adr/ADR-009.md`.*

**BR-034 — ✅ Implementado (2026-07-27, V1.2)**
Princípio da Imutabilidade da Venda: uma venda cancelada é estado terminal — nunca retorna a `concluida`
("reativação" não existe). Uma nova negociação sobre a mesma unidade sempre gera uma venda nova, nunca
reabre a cancelada.
*Fonte: `VENDAS.md` — "V1.2 — Cancelamento".*

**BR-035 — ✅ Implementado (2026-07-27, V1.2)**
`cancelada` (V1.2) é evento comercial, sem nenhuma reversão financeira — Vendas MVP não tem caixa formal.
`estornada` (também prevista na máquina de estados de `vendas.status`, `ADR-009`) só será implementada
junto do Épico Financeiro, quando existir pagamento/caixa reais para reverter.
*Fonte: `VENDAS.md` — "V1.2 — Cancelamento"; `docs/engineering/adr/ADR-009.md`.*

**BR-036 — ✅ Implementado (2026-07-27, V1.2)**
A listagem de histórico de vendas (`GET /api/vendas`, Sprint Vendas 1.1) inclui vendas canceladas por
padrão, identificadas por badge de status — nunca oculta por padrão. Filtro por `status` (já implementado
no backend) permite restringir a visualização quando necessário.
*Fonte: `VENDAS.md` — "V1.2 — Cancelamento".*

**BR-037 — ❌ REVOGADA (2026-07-29) — ver BR-053**
~~Limite de desconto livre (sem aprovação) é em R$ (valor fixo, não percentual) e individual por
vendedor.~~ Implementada em 2026-07-28 (V1.3, `c824958`), revogada no dia seguinte na revisão do modelo de
desconto — a loja não opera com bloqueio preventivo. Ver BR-053 para a regra vigente.
*Fonte: `VENDAS.md` — "V1.3 — Descontos e Aprovação"; "Revisão do modelo de desconto (2026-07-29)".*

**BR-038 — ❌ REVOGADA (2026-07-29) — ver BR-053**
~~Acima do limite livre, a aprovação acontece fora do sistema; o sistema registra apenas a confirmação
de que houve aprovação.~~ Implementada em 2026-07-28 (V1.3, `c824958`), revogada no dia seguinte — não
existe mais bloqueio nem confirmação de aprovação para desconto algum. Ver BR-053.
*Fonte: `VENDAS.md` — "V1.3 — Descontos e Aprovação"; "Revisão do modelo de desconto (2026-07-29)".*

**BR-039 — ✅ Implementado (2026-07-28, V1.3, `c824958`)**
Motivo do desconto na criação da venda é opcional, texto livre — deliberadamente diferente do motivo de
cancelamento (BR-032, lista fechada obrigatória). Não afetado pela revisão de 2026-07-29.
*Fonte: `VENDAS.md` — "V1.3 — Descontos e Aprovação".*

**BR-040 — ✅ Implementado (2026-07-28, V1.3, `c824958`)**
O comprovante/recibo da venda exibe preço de tabela, desconto aplicado e valor final ao cliente —
transparência total, não só informação interna do Detalhe da venda.
*Fonte: `VENDAS.md` — "V1.3 — Descontos e Aprovação".*

**BR-041 — ✅ Implementado (2026-07-28, V1.3, `c824958`)**
A base de cálculo de comissão (V1.4) não é decidida pelo sistema — fica configurável por loja/cliente da
plataforma. V1.3 preserva `valor_tabela`/`valor_unitario` separados para não travar nenhuma fórmula
futura. Cumprida concretamente pela V1.4 (BR-048: comissão sempre atribuída manualmente, nunca por
fórmula fixa do sistema).
*Fonte: `VENDAS.md` — "V1.3 — Descontos e Aprovação".*

**BR-042 — ✅ Implementado (2026-07-28, V1.3, `c824958`)**
O desconto é calculado sobre `valor_tabela` (preço de catálogo). "Preço promocional" distinto fica fora do
escopo da V1.3 — registrado como backlog, não decisão pendente.
*Fonte: `VENDAS.md` — "V1.3 — Descontos e Aprovação".*

**BR-043 — ✅ Implementado (2026-07-28, V1.3, `c824958`)**
Ajuste Comercial Autorizado: única exceção formalmente definida ao Princípio da Imutabilidade da Venda
(BR-034, que permanece válido e não é reaberto de forma ampla). Um `admin` pode ajustar o desconto/
`valor_unitario` de uma venda já concluída, e só esse campo — cliente, IMEI/Unidade Serializada, forma de
pagamento, vendedor, data, status e itens continuam imutáveis sem exceção. A operação é append-only
(nunca sobrescrita silenciosa): registra obrigatoriamente valor anterior, valor novo, quem autorizou,
quando, e motivo do ajuste (motivo aqui é **obrigatório**, diferente do motivo opcional do desconto
original em BR-039).
*Fonte: `VENDAS.md` — "V1.3 — Descontos e Aprovação".*

**BR-053 — ✅ Implementado (2026-07-29, V1.4, `7076c79`)**
Revisão do modelo de desconto (revoga BR-037 e BR-038): desconto nunca bloqueia a venda, independente do
valor — sempre permitido e sempre registrado. Modelo passa de preventivo (impede a venda) para analítico
(acompanhamento acontece depois, fora do fluxo de venda). Painel de indicadores de desconto (por
vendedor, ranking, vendas fora do padrão) é explicitamente **fora de escopo** desta sprint — vira uma
sprint própria (V1.4.1 ou V1.5), com discovery dedicada.
*Fonte: `VENDAS.md` — "Revisão do modelo de desconto (2026-07-29)".*

**BR-054 — ✅ Implementado (2026-07-29, V1.4, `7076c79`)**
`usuarios.limite_desconto_livre` e `vendas_itens.desconto_aprovado_em` (colunas da V1.3) deixam de ser
**escritos** por qualquer fluxo a partir desta revisão, mas **permanecem no schema sem remoção** — evita
migração destrutiva agora; dado histórico já gravado (vendas da V1.3) não é apagado. `limite_desconto_livre`
também deixa de ser **lido** em qualquer ponto (nenhuma tela ou resposta de API o expõe mais).
`desconto_aprovado_em` é a única exceção deliberada: continua **lido e exibido** (API e Detalhe da venda)
só para leitura histórica de vendas realizadas durante a vigência da V1.3 — descontinuar a exigência de
aprovação para vendas novas não significa apagar o registro de que vendas antigas passaram por ela. Nenhum
fluxo ativo depende desse valor para decidir comportamento; é dado histórico, não regra de negócio vigente.
*Fonte: `VENDAS.md` — "Revisão do modelo de desconto (2026-07-29)".*

**BR-044 — ✅ Implementado (2026-07-29, V1.4, `7076c79`)**
Novo perfil `financeiro` — não substitui `admin`, representa uma função própria de acompanhamento
financeiro das vendas. **Nota de visão (não escopo desta sprint):** este perfil é o embrião do futuro
domínio Financeiro completo do roadmap de 6 fases (`docs/company/RELEASE_STRATEGY.md`) — caixa, metas,
contas a pagar/receber, painel de indicadores. A V1.4 implementa só o necessário para comissão, não a
visão inteira.
*Fonte: `VENDAS.md` — "V1.4 — Comissão".*

**BR-045 — ✅ Implementado (2026-07-29, V1.4, `7076c79`)**
Escopo de acesso do `financeiro` nesta sprint: histórico e Detalhe de vendas (`GET /api/vendas`,
`GET /api/vendas/<id>` — já existentes, hoje liberados a qualquer perfil autenticado), Dashboard, e os
relatórios já existentes (Técnicos, Custos Operacionais — o relatório IR Phones foi removido em 2026-11-06, ADR-014). Nenhuma rota nova de leitura é criada
para isso — é extensão de permissão sobre rotas já existentes, mais a nova capacidade de atribuir
comissão (BR-048).
*Fonte: `VENDAS.md` — "V1.4 — Comissão".*

**BR-046 — ✅ Implementado (2026-07-29, V1.4, `7076c79`)**
`financeiro` não acessa usuários, permissões, configurações de sistema, estoque, compras, cadastro de
produtos, Ordens de Serviço, nem auditoria técnica. Não cria nem cancela vendas — só visualiza e atribui
comissão.
*Fonte: `VENDAS.md` — "V1.4 — Comissão".*

**BR-047 — ✅ Implementado (2026-07-29, V1.4, `7076c79`)**
Vendedor não tem nenhuma visibilidade sobre comissão em nenhuma tela do sistema — nem a própria.
*Fonte: `VENDAS.md` — "V1.4 — Comissão".*

**BR-048 — ✅ Implementado (2026-07-29, V1.4, `7076c79`)**
Comissão é atribuída manualmente, por `financeiro` ou `admin`, por item de venda (`vendas_itens`) — nunca
calculada automaticamente por uma fórmula fixa do sistema (percentual, valor fixo, categoria, etc.). A
mesma estrutura de dado suporta qualquer política de comissão que a loja adotar.
*Fonte: `VENDAS.md` — "V1.4 — Comissão".*

**BR-049 — ✅ Implementado (2026-07-29, V1.4, `7076c79`)**
Comissão pode ser editada depois de atribuída, por `financeiro` ou `admin`, com auditoria (valor anterior,
valor novo, quem editou, quando) — mesmo princípio append-only já usado no Ajuste Comercial (BR-043).
*Fonte: `VENDAS.md` — "V1.4 — Comissão".*

**BR-050 — ✅ Implementado (2026-07-29, V1.4, `7076c79`)**
Não existe campo de motivo/observação específico para a atribuição de comissão — diferente do desconto
(BR-039).
*Fonte: `VENDAS.md` — "V1.4 — Comissão".*

**BR-051 — ✅ Implementado (2026-07-29, V1.4, `7076c79`)**
Cancelamento de venda (V1.2, BR-031 a BR-036) zera automaticamente a comissão associada ao item
cancelado, sem intervenção manual do `financeiro`.
*Fonte: `VENDAS.md` — "V1.4 — Comissão".*

**BR-052 — ✅ Implementado (2026-07-29, V1.4, `7076c79`)**
Ajuste Comercial (BR-043, editar desconto pós-venda) continua exclusivo do perfil `admin` — o novo perfil
`financeiro` não ganha esse direito.
*Fonte: `VENDAS.md` — "V1.4 — Comissão".*

**BR-055 — ✅ Implementado (2026-07-30, V1.5, `789797b`)**
Novo cadastro **Tipos de Garantia** (nome + duração em meses de calendário), CRUD restrito a `admin`.
Distinção de domínio deliberada: **Tipo de Garantia** é a política configurável (o cadastro); **Garantia**
é a instância concreta concedida a um item de venda ou a um reparo específico — os dois nunca devem ser
confundidos no código nem na UI. Representa política comercial desta loja, nunca um valor hardcoded no
sistema. Não existe obrigatoriedade de um tipo "Sem garantia" (0 meses) existir no cadastro — é uma
política comercial que o `admin` cria se fizer sentido para a loja, não uma exigência técnica do sistema.
*Fonte: `VENDAS.md` — "V1.5 — Garantia".*

**BR-056 — ✅ Implementado (2026-07-30, V1.5, `789797b`)**
Garantia de Venda: um Tipo de Garantia é atribuído manualmente, por item de venda, **na criação da
venda** — obrigatório (toda venda concluída precisa ter uma Garantia de Venda atribuída ao item; nenhum
item fica sem seleção, mas o Tipo de Garantia escolhido pode ser aquele que representa "sem cobertura",
se um existir no cadastro). Sem default automático vindo do produto do catálogo — decisão explícita de
manter simples, sem tocar `produtos`.
*Fonte: `VENDAS.md` — "V1.5 — Garantia".*

**BR-057 — ✅ Implementado (2026-07-30, V1.5, `789797b`)**
Ao conceder a Garantia de Venda, o sistema copia para o registro do item: id do Tipo de Garantia, nome
(snapshot), duração em meses (snapshot), data de início e `data_fim_garantia` já calculada — nunca um
JOIN ao vivo com o cadastro. Alterações futuras no cadastro de Tipos de Garantia (ex.: "Seminovo" de 6
para 12 meses) não afetam garantias já concedidas — mesma disciplina já aplicada a `valor_tabela`
(V1.1), histórico de desconto (V1.3) e comissão (V1.4).
*Fonte: `VENDAS.md` — "V1.5 — Garantia".*

**BR-058 — ✅ Implementado (2026-07-30, V1.5, `789797b`)**
Cancelar a venda invalida/zera a Garantia de Venda do item cancelado — mesmo padrão de BR-051 (comissão
zerada no cancelamento).
*Fonte: `VENDAS.md` — "V1.5 — Garantia".*

**BR-059 — ✅ Implementado (2026-07-30, V1.5, `789797b`)**
Corrigir uma Garantia de Venda já concedida é restrito a `admin`, com auditoria append-only (valor
anterior, valor novo, quem concedeu, quem corrigiu, quando) — a correção é mais restrita que a
atribuição original (`admin`/`vendedor`), mesma assimetria do Ajuste Comercial (BR-043). **Sem motivo
obrigatório** — mesmo padrão da edição de comissão (BR-049/BR-050), não do Ajuste Comercial (BR-043,
que exige motivo): valor anterior/novo/quem/quando já bastam como justificativa registrada.
*Fonte: `VENDAS.md` — "V1.5 — Garantia".*

**BR-060 — ✅ Implementado (2026-07-30, V1.5, `789797b`)**
Garantia de Venda cobre apenas vendas de `produtos` (catálogo comercial) — não o caminho legado
`estoque`, fora de escopo desta fase.
*Fonte: `VENDAS.md` — "V1.5 — Garantia".*

**BR-061 — ✅ Implementado (2026-07-30, V1.5, `789797b`)**
Garantia de Reparo: um Tipo de Garantia é atribuído manualmente, por linha de reparo dentro da OS
(`os_reparos`), **na conclusão da OS** (`Finalizado`) — obrigatório, mesmo padrão de exigência de BR-056.
Sem default automático vindo do cadastro de Tipos de Reparo (`reparos`) — decisão explícita, mesma razão
de BR-056. Aplica-se às duas rotas que podem levar uma OS a `Finalizado` (`PATCH /api/ordens/<id>/status`
e `PUT /api/ordens/<id>`, achado durante a implementação — o formulário completo de edição também finaliza
OS, não só o botão de status dedicado).

**Exceção deliberada (decisão do CTO, 2026-07-30):** OS finalizadas automaticamente pela sincronização do
Mercado Phone (`irflow_mercadophone.py::importar_os_mercado_phone`/`reimportar_todas_os_mercado_phone`, que
escrevem `os.status` direto a partir do texto retornado pela API externa) **são isentas** desta exigência —
não há humano no loop nesse fluxo para escolher o Tipo de Garantia por linha de reparo no momento do sync.
Essas linhas ficam com `tipo_garantia_id NULL`, tratadas pelo mesmo fallback de dado histórico que
`listar_garantias()` já usa para OS concluídas antes da V1.5 (ver "Estratégia de Migração" em
`docs/engineering/plans/PLAN-V1.5-Garantia.md`) — nunca inventam uma garantia que não foi de fato
concedida. Se uma OS importada precisar de Garantia de Reparo formal depois, a correção manual
(`PATCH /api/ordens/<id>/reparos/<reparo_id>/garantia`, admin) continua disponível.
*Fonte: `VENDAS.md` — "V1.5 — Garantia".*

**BR-062 — ✅ Implementado (2026-07-30, V1.5, `789797b`)**
Mesma disciplina de snapshot de BR-057 aplicada à Garantia de Reparo, calculada a partir de
`data_finalizado`. Se uma OS combina múltiplos reparos com Tipos de Garantia diferentes, cada linha de
`os_reparos` mantém sua própria Garantia — não existe uma "garantia da OS" única/agregada.
*Fonte: `VENDAS.md` — "V1.5 — Garantia".*

**BR-063 — ✅ Implementado (2026-07-30, V1.5, `789797b`)**
Garantia de Reparo substitui o prazo fixo de 90 dias hardcoded (`GARANTIA_REPARO_DIAS_PADRAO`) — resolve
a dívida técnica já registrada em `VENDAS.md`/`OPERATION_SYSTEM.md`. A tela de Garantias existente e o
alerta de "perto de vencer" passam a ler a Garantia de Reparo de cada linha, não mais o valor fixo.
*Fonte: `VENDAS.md` — "V1.5 — Garantia".*

**BR-064 — ✅ Implementado (2026-07-30, V1.5, `789797b`)**
Cancelar a OS invalida/zera a Garantia de Reparo já concedida a qualquer linha de reparo — mesmo padrão
de BR-058.
*Fonte: `VENDAS.md` — "V1.5 — Garantia".*

**BR-065 — ✅ Implementado (2026-07-30, V1.5, `789797b`)**
Corrigir uma Garantia de Reparo já concedida é restrito a `admin`, com auditoria, sem motivo obrigatório
— mesmo padrão de BR-059.
*Fonte: `VENDAS.md` — "V1.5 — Garantia".*

**BR-066 — ✅ Implementado (2026-07-30, V1.5, `789797b`)**
Garantia de Venda e Garantia de Reparo são domínios independentes — nenhum vínculo formal entre uma OS
aberta por defeito coberto por Garantia de Venda e a venda original. A decisão de cobrar ou não a OS
nesse caso fica manual/informal, fora do sistema (candidata a automatizar em sprint futura, se o volume
de casos justificar). O cadastro de Tipos de Garantia é configurável **por esta loja/deploy**, não um
modelo multi-tenant real — `empresa_id` não existe no schema hoje (fica para quando Multiempresa for
escopada, ADR-005).
*Fonte: `VENDAS.md` — "V1.5 — Garantia".*

### Regras candidatas — exemplos citados nesta conversa (2026-07-10), pendentes de confirmação formal

O Product Owner citou estes exemplos ao propor este documento. Onde já existe decisão formal em
`VENDAS.md`, cito o BR correspondente. Onde não existe ainda, registro como candidata — não como regra
confirmada, para não inflar o número de "especificadas" com algo ainda não decidido no spec oficial.

- *"Um IMEI só pode pertencer a um aparelho"* — já coberto por BR-017 (reserva/venda por atendimento).
- *"Uma venda nunca pode existir sem um vendedor"* — **candidata**, não está em `VENDAS.md` "Decisões já
  tomadas" hoje; consistente com `VENDAS.md` "Quem usa" (vendedor conduz a venda), mas não formalizada
  como regra de validação.
- *"Uma reserva expira automaticamente"* — já coberto por BR-017.
- ~~*"Garantia nunca pode ser alterada após emitida"*~~ — **resolvida em 2026-07-29** (discovery V1.5):
  a resposta real é mais nuançada que a candidata original — garantia **pode** ser corrigida depois de
  concedida, mas restrito a `admin`, com auditoria (BR-059/BR-065), mesmo padrão do Ajuste Comercial.
- ~~*"Uma venda cancelada devolve o IMEI ao estoque"*~~ — **formalizada em 2026-07-27** como BR-033
  (discuss-phase de V1.2 — Cancelamento).

---

## Financeiro (Financeiro Mínimo)

Decisões tomadas em Discovery formal (ADR-010) entre CTO e engenharia (2026-08-08), a partir da proposta
de escopo mínimo de `docs/company/RELEASE_STRATEGY.md` ("Financeiro mínimo": Caixa, Entradas, Saídas,
Contas a Pagar, Contas a Receber, Fluxo de Caixa simples). Ver
`docs/engineering/plans/PLAN-financeiro-minimo.md` para o plano técnico e o registro de implementação.

**BR-067 — ✅ Implementado (2026-08-08, commit c1bcc61)**
Custos Operacionais e Caixa são módulos independentes — nenhum lançamento em `custos_operacionais` gera
movimentação de caixa automaticamente. Lançar as duas coisas é responsabilidade manual do usuário quando
fizer sentido. Testes de cobertura para `custos_operacionais` (lacuna pré-existente, sem relação direta
com esta feature) não foram adicionados nesta sprint — não eram critério de aceite do Financeiro Mínimo.
*Fonte: Decisão do CTO, 2026-08-08 (Discovery Financeiro Mínimo / Release 1.0).*

**BR-068 — ✅ Implementado (2026-08-08, commit c1bcc61)**
Contas a Receber representa só compromissos financeiros gerais (ex.: reembolso pendente, aluguel de
equipamento a receber) — sem FK ou qualquer relação com o domínio Vendas. Vendas continua sem conceito de
parcelamento/inadimplência nesta release. `fluxoly_contas_receber_repository.py`/`_service.py` não
importam nem consultam nada do domínio Vendas (isolamento verificado por teste,
`tests/test_contas_receber.py::TestIsolamentoDeVendasBR068`).
*Fonte: Decisão do CTO, 2026-08-08 (Discovery Financeiro Mínimo / Release 1.0).*

**BR-069 — ✅ Implementado (2026-08-08, commit c1bcc61)**
Venda com `status='concluida'` gera automaticamente uma entrada em `movimentacoes_caixa` no valor de
`vendas.valor_total`, vinculada à venda (`origem='venda'`, `origem_id=vendas.id`). Se a venda for
cancelada (BR-031 a BR-036), a entrada correspondente é estornada automaticamente (`estornada=1`) — uma
mesma venda nunca pode ter duas entradas ativas simultâneas, e o hook de criação é idempotente (chamar o
fluxo de conclusão mais de uma vez para a mesma venda nunca duplica a entrada). Saldo de caixa é sempre
`SOMA(entradas não estornadas) − SOMA(saídas não estornadas)`; uma movimentação estornada permanece
registrada no histórico (nunca é apagada), só é excluída do cálculo de saldo — preserva auditoria. O
índice único parcial `idx_movimentacoes_caixa_venda_ativa` (`migrations/versions/m0002_financeiro_minimo.py`)
é o guardião real da regra no banco, não só a checagem em `fluxoly_caixa_service.registrar_entrada_de_venda`.
*Fonte: Decisão do CTO, 2026-08-08 (Discovery Financeiro Mínimo / Release 1.0), consistente com o
Princípio da Imutabilidade da Venda (BR-034) e o padrão de estorno já usado em BR-033.*

---

## Compra de Aparelhos (conserto e revenda)

Decisões tomadas em Discovery (ADR-010) com o CTO em 2026-11-08: a loja compra aparelhos, em geral
quebrados, para consertar e revender. Plano técnico em `docs/engineering/plans/PLAN-compra-aparelhos.md`.
BR-083 a BR-089 implementadas no backend (PR 2, 2026-11-08); BR-090 a BR-093 aprovadas, ainda não implementadas.

**BR-083 — ✅ Implementado no backend (2026-11-08; tela no PR 5)**
Uma compra de aparelho registra: modelo do catálogo (`produtos`), IMEI (obrigatório), origem
(`marketplace` | `troca` | `outro`), valor pago (`> 0`), forma de pagamento (`pix` | `dinheiro` |
`transferencia` | `cartao` | `abatido_na_venda`), estado (texto curto obrigatório) e defeito (texto,
vazio = sem defeito). O usuário que registra é sempre o da sessão.
*Fonte: Decisão do CTO, 2026-11-08.*

**BR-084 — ✅ Implementado no backend (2026-11-08; tela no PR 5)**
Registrar a compra cria, na mesma operação, a unidade serializada do aparelho (origem Produto, ADR-007):
com defeito preenchido ela nasce `em_reparo`; sem defeito, `disponivel`. IMEI já cadastrado em outra
unidade é rejeitado. Compra e unidade nascem juntas ou não nascem (uma transação).
*Fonte: Decisão do CTO, 2026-11-08.*

**BR-085 — ✅ Implementado no backend (2026-11-08; tela no PR 5)**
Compra com origem `troca` exige o cliente que entregou o aparelho e pode ser ligada à venda em que ele
entrou como parte do pagamento. A forma de pagamento `abatido_na_venda` só é aceita com origem `troca`.
A venda continua registrada pelo valor cheio — a troca não altera `vendas.valor_total` (BR-034).
*Fonte: Decisão do CTO, 2026-11-08.*

**BR-086 — ✅ Implementado no backend (2026-11-08; tela no PR 5)**
Toda compra ativa gera automaticamente uma saída em `movimentacoes_caixa` no valor pago
(`origem='compra_aparelho'`, `origem_id=compras_aparelhos.id`), inclusive quando a forma é
`abatido_na_venda`: a venda entra cheia (BR-069) e a compra sai cheia, então o saldo líquido é o que o
cliente realmente pagou. Uma compra nunca tem duas saídas ativas (índice único parcial, mesmo padrão de
BR-069) e o hook é idempotente.
*Fonte: Decisão do CTO, 2026-11-08.*

**BR-087 — ✅ Implementado no backend (2026-11-08; tela no PR 5)**
Uma compra pode ser cancelada com motivo obrigatório, desde que o aparelho não tenha sido vendido. O
cancelamento estorna a saída de caixa (nunca apaga — BR-069) e a unidade vai para `devolvido`. A compra
cancelada permanece no histórico.
*Fonte: Decisão de engenharia dentro do escopo aprovado pelo CTO, 2026-11-08 — revisável no QA.*

**BR-088 — ✅ Implementado no backend (2026-11-08; tela no PR 5)**
Na compra é possível guardar nome e telefone de quem vendeu o aparelho (opcionais), para comprovar a
procedência caso o aparelho apareça como roubado. São dados pessoais (LGPD): visíveis só para os perfis
que registram compras (BR-089), fora de exportações e PDFs.
*Fonte: Decisão do CTO, 2026-11-08.*

**BR-089 — ✅ Implementado no backend (2026-11-08; tela no PR 5)**
Registrar, listar e cancelar compras de aparelhos: perfis `admin`, `financeiro` e `vendedor`.
*Fonte: Decisão do CTO, 2026-11-08.*

**BR-090 — 🟡 Aprovada (2026-11-08)**
O conserto de um aparelho comprado é feito numa **OS interna** (`tipo='Interna'`), ligada à unidade
serializada. Ela não tem cliente nem vendedor e não tem valor cobrado; as peças saem do estoque como em
qualquer OS. OS interna não entra no faturamento nem no lucro de assistência e não aparece em Garantias.
Abrir OS interna para um aparelho `disponivel` o move para `em_reparo`. Quem abre e altera OS segue
BR-030 (`admin`, `tecnico`). A regra é por tipo e por unidade — nunca por nome de cliente (o atalho
"IR Phones" removido na ADR-014 não volta).
*Fonte: Decisão do CTO, 2026-11-08.*

**BR-091 — 🟡 Aprovada (2026-11-08)**
Quando uma OS interna é finalizada, o aparelho passa sozinho de `em_reparo` para `disponivel`.
*Fonte: Decisão do CTO, 2026-11-08.*

**BR-092 — 🟡 Aprovada (2026-11-08)**
Custo do aparelho = valor pago na compra ativa + custo de peças de todas as OS internas dele (mão de obra
não entra). Lucro do aparelho = valor unitário na venda concluída − custo. Ambos são calculados, nunca
gravados, e visíveis só para `admin` e `financeiro` (mesmo critério de BR-047).
*Fonte: Decisão do CTO, 2026-11-08 (lucro por aparelho); visibilidade por decisão de engenharia,
consistente com BR-047 — revisável no QA.*

**BR-093 — 🟡 Aprovada (2026-11-08)**
Relatório mensal de compra e revenda (`admin`/`financeiro`): aparelhos comprados, vendidos e parados no
mês, total investido (compras + peças), total vendido e lucro.
*Fonte: Decisão do CTO, 2026-11-08.*

---

## Segurança e Permissões

**BR-030 — ✅ Implementado (2026-07-25)**
Mutação de OS (`POST/PUT/DELETE /api/ordens`, `PATCH /api/ordens/<id>/status`) exige perfil `admin` ou
`tecnico`. Mutação de Estoque (`POST/PUT/DELETE /api/estoque`) exige perfil `admin` ou `estoque`
(perfil novo, criado junto desta regra). Antes, ambas aceitavam qualquer perfil autenticado — achado da
Sprint Segurança 1.0, decisão de negócio do usuário (CTO) sobre quais perfis operam cada domínio.
*Fonte: `docs/security/SECURITY_AUDIT_2026-07.md`; `irflow_blueprints_api.py` (`criar_ordem`,
`atualizar_ordem`, `deletar_ordem`, `atualizar_status_os`, `criar_estoque`, `atualizar_estoque`,
`deletar_estoque`); `tests/test_stock_security.py::TestPermissaoPorPerfil`,
`tests/test_os_deletion_security.py::TestExcluirOrdem::test_vendedor_nao_pode_excluir_os`.*

---

## Lista de Aparelhos Disponíveis (ferramenta interna — `apps/lista-aparelhos-disponiveis/`)

> **⛔ REVOGADAS (2026-11-06, ADR-014):** BR-070 a BR-082 estão revogadas. O app foi removido do
> repositório por decisão do CTO (desvínculo do Fluxoly com a IR Phones). As regras abaixo ficam apenas
> como registro histórico.

Ferramenta **fora do Fluxoly-plataforma** (ADR-013), consulta ao estoque de aparelhos da loja IR
Phones. Fonte: API nova do MercadoPhone. Duas áreas atrás de senha compartilhada: **Geral** (vendedores)
e **Estoque** (organizador). Ciclo ADR-010 completo, mergeada em `main` via PR #68 (`eb13e836`,
2026-09-04). Discovery: `docs/product/research/DISCOVERY_LISTA_PRECOS_PUBLICA.md`.

**BR-070 — ✅ Implementado (2026-09-04)**
A área **Geral** expõe modelo, armazenamento, cor, estado, saúde de bateria, preço de venda e
disponibilidade. **Nunca** custo, margem, fornecedor, nome de cliente, IMEI completo, campos fiscais nem
texto livre. Os snapshots são montados por **allowlist** de campos (nunca blocklist).

**BR-071 — ✅ Implementado (2026-09-04)**
A área **Estoque** acrescenta custo, margem e dias parado em estoque; é a única que registra reservas e
edita o campo Detalhes. Também **não** expõe nome de cliente/fornecedor.

**BR-072 — ✅ Implementado (2026-09-04)**
Unidades vindas de fontes diferentes são deduplicadas pelo IMEI completo; sem IMEI real (`0`/vazio),
pelo `id` interno do MercadoPhone. Em empate, vence o registro de `dataModificacao` mais recente.

**BR-073 — ✅ Implementado (2026-09-04)**
O identificador visível de uma unidade são os últimos 4 dígitos do IMEI, estendido um dígito por vez
(5, 6, …) **apenas nas unidades cujo identificador colidiria** com o de outra unidade exibida. Sem IMEI
→ `#<id>`. O IMEI completo nunca chega ao navegador.

**BR-074 — ✅ Implementado (2026-09-04)**
Só entram aparelhos Apple serializados: `snAcessorio == 0` e `tipoProduto ∈ {IPHONE, IPAD, MACBOOK,
APPLE WATCH}`. Acessórios, peças, serviços, brindes, AirPods e Apple Pencil nunca entram.

**BR-075 — ✅ Implementado (2026-09-04)**
Só aparecem unidades cuja situação de estoque tem `snExibirPdv == 1` no MercadoPhone (hoje "Disponível
para venda" e "Disponível com detalhe"). "Laboratório" e "ANALISE" ficam de fora. "Disponível com
detalhe" recebe a etiqueta "(com detalhe)".

**BR-076 — ✅ Implementado (2026-09-04)**
Uma unidade reservada (na área Estoque) sai da área Geral e some da lista "Disponíveis" (BR-081) — segue
visível na aba do seu Estoque 1/2, marcada com o vendedor. A reserva **não expira**: sai por ação do
organizador (ou automaticamente, no caso da reserva Estela — BR-082) ou quando a unidade some do estoque
do MercadoPhone (venda).

**BR-077 — ✅ Implementado (2026-09-04)**
A reserva registra apenas vendedor + data. **Nunca** nome ou qualquer dado do cliente.

**BR-078 — ✅ Implementado (2026-09-04)**
O MercadoPhone não tem status "Reservado". A reserva é um registro exclusivo desta ferramenta (Redis
próprio) e **não** é escrita de volta no MercadoPhone.

**BR-079 — ✅ Implementado (2026-09-04)**
O campo "Detalhes" é uma nota de condição curada manualmente na área Estoque (ex.: "marca de uso leve
na traseira", "tela trocada — original"), exibida nas **duas** áreas. A responsabilidade de não incluir
dado pessoal é de quem edita — a ferramenta não sanitiza. O campo `obs` do MercadoPhone (nota interna,
com PII observada) fica deliberadamente fora dos snapshots.

**BR-080 — ✅ Implementado (2026-09-04; critério de desempate revisado em 2026-09-11, duas vezes)**
A lista é ordenada por tipo (iPhone → iPad → MacBook → Apple Watch) → modelo em ordem natural
(`IPHONE 9` < `11` < `11 PRO` < `11 PRO MAX` < …) → estado (Lacrado/Novo/Open box/CPO antes de Seminovo;
"com detalhe" por último) → cor (ordem alfabética) → GB crescente → saúde de bateria decrescente (maior %
primeiro). O mesmo critério vale nas duas áreas; a área Estoque tem um desempate a mais só para ela: dias
parado em estoque decrescente (quem está parado há mais tempo aparece primeiro), depois de cor/GB/bateria.
Substitui o desempate por preço crescente da versão original.

**BR-081 — ✅ Implementado (2026-09-11)**
Toda unidade tem uma localização manual, **Estoque 1** ou **Estoque 2** (default: Estoque 1 para
unidade nova, sem precisar popular nada). A área **Geral** só mostra unidades do Estoque 1 (além de
excluir as reservadas, BR-076) — Estoque 2 nunca aparece para o vendedor. Na área Estoque, o organizador
vê 3 abas: "Estoque 1", "Estoque 2" (cada uma com todas as unidades daquele local, reservadas inclusive)
e "Disponíveis" (união dos dois locais, só as não reservadas) — e tem um botão por unidade para mover
entre os dois locais a qualquer momento.

**BR-082 — ✅ Implementado (2026-09-11)**
Toda unidade cuja situação de estoque no MercadoPhone é "Disponível com detalhe" é reservada
automaticamente, no sync, para a vendedora fictícia **"Estela"** (reaproveita o mecanismo de reserva do
BR-076/077/078 — nenhum filtro novo foi necessário para sumir da Geral). Se a situação deixar de ser "com
detalhe" num sync seguinte, a reserva Estela é liberada automaticamente. Uma reserva feita por um vendedor
humano **nunca** é criada, sobrescrita ou removida por este mecanismo.

*Fonte: `apps/lista-aparelhos-disponiveis/` (`lib/snapshot.ts`, `lib/filter.ts`, `lib/dedup.ts`,
`lib/short-id.ts`, `lib/ordenar.ts`, `lib/inventory-view.ts`, `lib/estela.ts`, `lib/store.ts`, `api/`);
testes em `apps/lista-aparelhos-disponiveis/test/` (101 casos, `snapshot.test.ts` garante 0 vazamento de
custo/PII/IMEI na Geral); `docs/engineering/plans/PLAN-lista-aparelhos-disponiveis.md`.*

---

## Documentos relacionados

- `docs/product/features/VENDAS.md` — fonte das regras de Vendas (BR-017 a BR-022, BR-031 a BR-066)
- `docs/product/features/CLIENTES.md` — fonte das regras de Clientes (BR-023, BR-024)
- `docs/engineering/plans/PLAN-compra-aparelhos.md` — plano técnico de Compra de Aparelhos (BR-083 a BR-093)
- `docs/engineering/DOMAIN_MODEL.md` — domínios e arquivos onde cada regra implementada vive
- `docs/engineering/DATABASE.md` — schema citado nas regras de Estoque/Compras
- `docs/operations/KNOWN_ISSUES.md` — bugs já corrigidos que originaram alguma regra (ex.: BR-007 ↔ B-11)
