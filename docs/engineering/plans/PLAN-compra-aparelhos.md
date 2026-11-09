# PLAN-compra-aparelhos — Compra de aparelhos para conserto e revenda

**Data:** 2026-11-08
**Feature:** compra de aparelhos (geralmente quebrados) para consertar e revender — `docs/product/BUSINESS_RULES.md`
BR-083 a BR-093
**Status:** Implementação — PR 2 (banco + backend da compra) concluído

> Este documento é efêmero (ver `docs/engineering/adr/ADR-010.md`). Depois que a sprint encerra, ele
> permanece só como histórico da decisão de implementação. O que continuar relevante é promovido para
> `DATABASE.md`, `ARCHITECTURE.md` e `DOMAIN_MODEL.md`.

**Estado**

- [x] Discovery — aprovada pelo CTO em 2026-11-08 (respostas na conversa de Discovery, registradas em
  BR-083 a BR-093)
- [x] Plano Técnico — este documento (PR 1, só documentação)
- [ ] Implementação — [x] PR 2 (banco + backend da compra: migration `m0003`, domínio
  `fluxoly_compras_aparelhos_*`, hooks de Caixa e Unidades, `tests/test_compras_aparelhos.py` com 30 casos);
  [ ] PR 3 (OS interna); [ ] PR 4 (custo/lucro + relatório); [ ] PR 5 (frontend)
- [ ] Testes
- [ ] QA Manual
- [ ] Revisão Arquitetural
- [ ] Encerramento

---

## Contexto

A loja passa a comprar aparelhos, na maioria quebrados, para consertar e revender. Origem das compras:
marketplace (maioria) e troca, quando o cliente entrega um aparelho como parte do pagamento de outro que
comprou na loja. Hoje o sistema já tem as peças desse fluxo, mas soltas:

| Já existe | Falta |
|-----------|-------|
| `produtos` (catálogo, `condicao` Novo/Seminovo/Vitrine) | Registro da compra (de quem, quanto, como pagou, estado, defeito) |
| `unidades_serializadas` (um aparelho físico por IMEI, status `disponivel`/`em_reparo`/`vendido`/...) | Custo **por aparelho**: `produtos.preco_custo` é por modelo, não por unidade |
| `vendas` + `vendas_itens` (venda de uma unidade, `valor_unitario`) | Ligar o conserto ao aparelho |
| `os` + `os_pecas` (consumo de peças do estoque, `custo_pecas`) | Lucro por aparelho e relatório de compra/revenda |
| `movimentacoes_caixa` (entrada automática de venda, BR-069) | Saída automática de caixa na compra |

A "OS interna IR Phones", removida em 2026-11-06 (ADR-014), fazia parte disso com um atalho (cliente
fixo "IR Phones" e exceção na validação de vendedor). Esta feature **não** reintroduz aquele atalho: a OS
interna nasce como tipo próprio, ligado a uma unidade serializada, sem cliente fictício.

## Fluxo

```
Compra ──► Unidade serializada ──► OS interna (conserto) ──► Venda
 saída de caixa   em_reparo (com defeito)    peças somam no custo     lucro = venda − custo
                  disponivel (sem defeito)   Finalizada → disponivel
```

## Escopo

### PR 2 — Banco + backend da compra
- Migration `migrations/versions/m0003_compras_aparelhos.py` (aditiva, padrão de `m0002`):
  - Tabela nova `compras_aparelhos`:

    | Coluna | Tipo | Observação |
    |--------|------|------------|
    | `id` | INTEGER PK AUTOINCREMENT | |
    | `unidade_serializada_id` | INTEGER NOT NULL | FK lógica — unidade criada pela própria compra (BR-084) |
    | `produto_id` | INTEGER NOT NULL | FK lógica — modelo do catálogo |
    | `origem` | TEXT NOT NULL | `marketplace` \| `troca` \| `outro` (validado no service) |
    | `cliente_id` | INTEGER | FK lógica — obrigatório quando `origem='troca'` (BR-085) |
    | `venda_id` | INTEGER | FK lógica — opcional, venda em que o aparelho entrou como troca |
    | `vendedor_nome` | TEXT | Opcional — quem vendeu no marketplace (BR-088) |
    | `vendedor_telefone` | TEXT | Opcional (BR-088) |
    | `valor_pago` | REAL NOT NULL | `> 0` |
    | `forma_pagamento` | TEXT NOT NULL | `pix` \| `dinheiro` \| `transferencia` \| `cartao` \| `abatido_na_venda` |
    | `estado` | TEXT NOT NULL | Texto curto livre (ex.: "tela trincada, carcaça boa") |
    | `defeito` | TEXT NOT NULL DEFAULT `''` | Vazio = sem defeito |
    | `status` | TEXT NOT NULL DEFAULT `'ativa'` | `ativa` \| `cancelada` |
    | `motivo_cancelamento` | TEXT | Obrigatório ao cancelar |
    | `cancelado_por` / `cancelado_em` | INTEGER / TEXT | |
    | `usuario_id` | INTEGER NOT NULL | Sempre o usuário da sessão |
    | `criado_em` | TEXT NOT NULL | `datetime('now')` |

  - Índices: `idx_compras_aparelhos_unidade` (**UNIQUE parcial** `WHERE status='ativa'` — uma unidade tem no
    máximo uma compra ativa), `idx_compras_aparelhos_criado_em`, `idx_compras_aparelhos_cliente_id`.
  - Índice **UNIQUE parcial** `idx_movimentacoes_caixa_compra_ativa` em `movimentacoes_caixa (origem_id)
    WHERE origem='compra_aparelho' AND estornada=0` — mesmo guardião de BR-069, agora para a compra (BR-086).
  - `ALTER TABLE os ADD COLUMN unidade_serializada_id INTEGER` + índice — preparado aqui para o PR 3 não
    precisar de outra migration.
- Domínio novo `fluxoly_compras_aparelhos_{controller,service,repository}.py` (convenção
  `ENGINEERING_GUIDE.md` §3.1), registrado em `fluxoly_blueprint_registry.py`.
  - `POST /api/compras-aparelhos` — cria compra + unidade + saída de caixa **numa transação, um cursor**
    (mesma atomicidade de Vendas↔Caixa).
  - `GET /api/compras-aparelhos` (filtros: período, origem, status) e `GET /api/compras-aparelhos/<id>`.
  - `POST /api/compras-aparelhos/<id>/cancelar` — BR-087.
  - Gate de perfil: `admin`, `financeiro`, `vendedor` (BR-089).
- `fluxoly_caixa_service.py`: `registrar_saida_de_compra_aparelho` / `estornar_saida_de_compra_aparelho`
  (espelho de `registrar_entrada_de_venda` / `estornar_entrada_de_venda`). Continua sendo o único caminho de
  escrita em `movimentacoes_caixa`.
- `fluxoly_unidades_serializadas_service.py`: criação da unidade reaproveita o caminho existente (origem
  Produto, Regra de Ouro ADR-007); IMEI obrigatório nesta origem.

### PR 3 — OS interna
- `OS_TIPOS_OPCOES` ganha `"Interna"`.
- `api_os.py` (criar/atualizar): `tipo='Interna'` exige `unidade_serializada_id` de uma unidade com compra
  ativa e status `em_reparo` ou `disponivel` (abrir OS interna em unidade `disponivel` move para
  `em_reparo`). Cliente gravado como texto fixo de exibição `"Estoque próprio"` com `cliente_id NULL`;
  vendedor não exigido **somente** para `Interna` (regra explícita por tipo, não exceção por nome de
  cliente); `valor_cobrado = valor_descontado = 0` forçados no backend.
- Hook de status: OS interna vai para `Finalizado` → unidade `em_reparo → disponivel` (BR-091), via o
  service de unidades (`TRANSICOES_VALIDAS` já permite), na mesma transação.
- Exclusões (BR-090): relatórios de faturamento/lucro de assistência (`fluxoly_reports.py`) e Garantias
  (`api_garantias.py`, `app.py`) ignoram `tipo='Interna'`. `calcular_lucro_os` não muda.
- Mexe em `app.py` → plano aprovado nesta Discovery (2026-11-08).

### PR 4 — Custo, lucro e relatório
- `custo_aparelho(unidade_id) = compras_aparelhos.valor_pago (ativa) + SOMA(os.custo_pecas WHERE
  tipo='Interna' AND unidade_serializada_id = ?)` (BR-092) — calculado, nunca coluna.
- `lucro = vendas_itens.valor_unitario (venda concluída) − custo_aparelho`.
- Expor em `GET /api/vendas/<id>` e `GET /api/unidades-serializadas/<id>` só para `admin`/`financeiro`
  (mesmo critério de ocultação de BR-047).
- `GET /api/relatorios/compra-revenda?mes=AAAA-MM` (BR-093).

### PR 5 — Frontend
- Página nova "Compras de Aparelhos" (lista + formulário + cancelamento), item de navegação para
  `admin`/`financeiro`/`vendedor`.
- Nova OS: tipo "Interna" com busca de aparelho por IMEI no lugar de cliente/vendedor/valores.
- Lucro no detalhe da venda e da unidade (só `admin`/`financeiro`); aba "Compra e revenda" em Relatórios.

## Fora de Escopo
- Consulta automática de IMEI em base de roubo/bloqueio (Anatel/celular seguro).
- Fotos do aparelho e termo de procedência assinado pelo vendedor.
- Mão de obra do técnico no custo do aparelho (só peças entram, BR-092).
- Troca embutida no fluxo de Venda (a compra por troca é registrada à parte e ligada à venda por
  `venda_id`; a venda continua com `valor_total` cheio — ver BR-085/BR-086).
- Cadastro de vendedores de marketplace como entidade (`clientes` não é reaproveitado para eles).

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Caixa com valor errado na troca | Venda entra cheia (BR-069) e a compra sai cheia (BR-086), inclusive `abatido_na_venda`: o saldo líquido é o que o cliente realmente pagou. Teste de ponta a ponta no PR 2 |
| Saída de caixa duplicada | UNIQUE parcial `idx_movimentacoes_caixa_compra_ativa` + hook idempotente |
| Compra sem unidade ou unidade sem compra (falha no meio) | Uma transação, um cursor; teste que força erro após criar a unidade |
| IMEI repetido | `unidades_serializadas.imei` já é UNIQUE; service devolve erro claro antes |
| Dados pessoais do vendedor do marketplace (LGPD) | Opcionais, só para perfis que registram compras, fora de exportações/PDF; entram no inventário de `DISCOVERY_LGPD.md` |
| OS interna contaminando faturamento/garantias | Exclusão por `tipo='Interna'` com teste em cada relatório e em Garantias |
| Reintroduzir o atalho "IR Phones" | Regra por tipo + `unidade_serializada_id`, nunca por nome de cliente |
