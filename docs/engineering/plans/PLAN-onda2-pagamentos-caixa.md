# PLAN-onda2-pagamentos-caixa — Formas de pagamento, recebimento da OS, troca, lucro líquido e autorização de gerente

**Data:** 2026-11-11
**Origem:** `docs/product/PRODUCT_BACKLOG.md` → Proposta do benchmark Mercado Phone, Onda 2 itens 9, 10, 11,
12 e 15; evidência em `MERCADO_PHONE.md` → "Vendas", "Financeiro", "OS", "Tela inicial e Configurações".
**Status:** **Rascunho — aguardando decisões do Product Owner.** Nada implementado.

> Documento efêmero (ADR-010). Fica só no Plano Técnico de propósito: estes itens mexem no dinheiro que
> entra e sai do caixa (vendas, OS, compras de aparelho) e dependem de regras que só o PO decide. Os itens
> 13 e 14 da mesma onda foram implementados (`PLAN-os-data-previsao.md`, `PLAN-os-relato-laudo.md`)
> porque são colunas aditivas sem efeito em dinheiro.

---

## Estado atual (Discovery, 2026-11-11)

- **Venda:** uma única `vendas.forma_pagamento` por venda, lista fechada no código
  (`fluxoly_vendas_service.FORMAS_PAGAMENTO_VALIDAS = {pix, cartao, dinheiro, transferencia}`). A venda
  lança **uma** entrada no caixa pelo valor cheio (`caixa_service.registrar_entrada_de_venda`, BR-069).
- **Compra de aparelho:** forma de pagamento própria, inclui `abatido_na_venda` (só com origem `troca`,
  BR-084/BR-086); sai cheia do caixa. A troca não altera `vendas.valor_total` (BR-034) — o saldo líquido
  é a diferença entre a entrada da venda e a saída da compra.
- **OS:** `valor_cobrado`/`valor_descontado` existem, mas **nenhum dinheiro de OS entra no caixa**.
  `movimentacoes_caixa.origem` não tem `os`.
- **Taxas:** não existe taxa por forma de pagamento nem por parcela; lucro é bruto.
- **Autorização:** só perfil; não existe "liberação pontual por gerente".

---

## Item 9 — Formas de pagamento cadastradas + vários pagamentos por operação (fundação)

### Proposta técnica

Migration aditiva (`m0007`, quando aprovada):

```sql
CREATE TABLE formas_pagamento (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,               -- "Pix", "Crédito 3x Stone"...
    tipo TEXT NOT NULL,               -- pix | dinheiro | debito | credito | transferencia | outro
    taxa_percentual REAL NOT NULL DEFAULT 0,
    taxa_fixa REAL NOT NULL DEFAULT 0,
    parcelas_max INTEGER NOT NULL DEFAULT 1,
    ativo INTEGER NOT NULL DEFAULT 1,
    criado_em TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE pagamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    origem TEXT NOT NULL,             -- venda | os
    origem_id INTEGER NOT NULL,
    forma_pagamento_id INTEGER NOT NULL,
    valor REAL NOT NULL,              -- > 0
    parcelas INTEGER NOT NULL DEFAULT 1,
    taxa_valor REAL NOT NULL DEFAULT 0, -- snapshot da taxa no momento (como a garantia, BR-057)
    movimentacao_caixa_id INTEGER,
    status TEXT NOT NULL DEFAULT 'ativo', -- ativo | estornado
    criado_por INTEGER, criado_em TEXT NOT NULL DEFAULT (datetime('now'))
);
```

- Seed com as 4 formas de hoje (taxa 0), para `vendas.forma_pagamento` antigo continuar legível.
- `vendas.forma_pagamento` fica (histórico); vendas novas gravam `pagamentos` e o caixa recebe **uma
  entrada por pagamento** (hoje é uma por venda).
- Cancelar venda estorna cada pagamento (hoje estorna uma movimentação).

### Riscos

- Muda `iniciar_venda`/`cancelar_venda`, que têm CAS e testes de concorrência (`test_vendas.py`) — PR
  próprio, com os testes de concorrência adaptados antes da mudança.
- Relatórios que leem `vendas.forma_pagamento` (filtro da listagem) precisam olhar `pagamentos`.

### Decisões do PO

1. A soma dos pagamentos pode ser **menor** que o total (fica saldo a receber → conta a receber
   automática?) ou tem de fechar exato?
2. A taxa é custo da loja (reduz lucro, item 12) ou repassada ao cliente (aumenta o valor cobrado)?
3. Quem cadastra formas de pagamento: só admin, ou também financeiro?

---

## Item 10 — Recebimento da OS no caixa

### Proposta técnica

Depende do item 9 (`pagamentos.origem = 'os'`). Nova origem `os` em `movimentacoes_caixa`. Ação
"Receber" na OS (parcial permitido se o PO aprovar), saldo = `valor_cobrado − valor_descontado −
recebido`. Cancelar OS com recebimento exige estorno explícito.

### Decisões do PO

1. O recebimento acontece **na finalização**, na **retirada** ou a qualquer momento (sinal/entrada)?
2. OS finalizada sem recebimento: alerta? Bloqueia o comprovante de entrega?
3. OS de garantia (`tipo = Garantia`, sem cobrança) fica fora do caixa — confirmar.
4. O faturamento do Dashboard continua por OS finalizada (competência) ou passa a ser por dinheiro
   recebido (caixa)?

---

## Item 11 — Troca/upgrade completo

Já existe em parte: compra com origem `troca` ligada à venda e `abatido_na_venda` (BR-084/BR-086). Falta o
fluxo de **uma tela só** (vender o novo e receber o usado no mesmo atendimento).

### Proposta técnica

Sem schema novo além do item 9: na Nova Venda, bloco "Aparelho na troca" que cria a compra de aparelho
(origem `troca`, `abatido_na_venda`) **na mesma transação** da venda; o valor da troca vira um
"pagamento" do tipo troca (item 9), e o caixa só sente a diferença.

### Decisões do PO (de `docs/product/features/VENDAS.md` → "O que ainda está em aberto")

1. Critérios do checklist de avaliação de usado e tabela de referência por modelo.
2. Quem avalia (técnico, como diz `VENDAS.md`) e se a venda espera a avaliação.
3. Avaliação recusada: segue venda sem troca ou cancela (VENDAS.md lista as duas).

---

## Item 12 — Lucro líquido de taxa por venda

Depende do item 9 (`pagamentos.taxa_valor`). Lucro líquido = lucro bruto (BR-092) − soma das taxas dos
pagamentos. Exibição só admin/financeiro (BR-092/BR-100). Sem schema próprio.

Decisão do PO: igual à pergunta 2 do item 9 (taxa é custo da loja?).

---

## Item 15 — Autorização de gerente na operação

### Proposta técnica

- Operações sensíveis (cancelar venda, desconto acima do limite, excluir OS/registro) pedem a **senha de
  um usuário admin** num diálogo, sem trocar a sessão de quem está no balcão.
- Backend: `POST` da operação aceita `autorizacao: {usuario_id, senha}`; valida com o mesmo hash do login,
  com o rate limit do login; registra no `audit_log` quem pediu e quem autorizou (a tela de auditoria do
  PR #88 já mostra).
- Sem schema novo (usa `usuarios` e `audit_log`).

### Riscos

- Mexe em autenticação/autorização transversalmente — ADR obrigatório antes (CLAUDE.md, "Requer
  aprovação explícita + ADR"). Senha digitada no balcão em tela compartilhada: avaliar PIN separado.

### Decisões do PO

1. Quais operações exigem autorização (lista fechada).
2. Senha do admin ou PIN de gerente separado (novo campo em `usuarios` → schema).
3. Limite de desconto do vendedor (já pendente em `VENDAS.md`).

---

## Ordem sugerida quando aprovado

9 → 10 → 12 → 11 → 15. Cada um em PR próprio, com migration revisada e backup verificado antes do deploy.
