# PLAN-esconder-lucro-vendedor — Vendedor sem custo/lucro no Dashboard

**Data:** 2026-11-11
**Origem:** `docs/product/PRODUCT_BACKLOG.md` → Proposta do benchmark Mercado Phone, Onda 1 item 8
(Etapa 8); evidência em `MERCADO_PHONE.md` → "Tela inicial e Configurações" (permissões por perfil).
**Status:** Aprovado pelo Product Owner (2026-11-11, aprovação geral das etapas) — **parte (b) pendente**

> Documento efêmero (ADR-010). Mexe em autorização: plano obrigatório (CLAUDE.md).

**Estado**

- [x] Discovery — `/api/dashboard` é aberto a qualquer autenticado e devolvia lucro, custo de peças,
      custos operacionais, resultado líquido, valor do estoque, lucro por técnico e lucro por vendedor
      também para o perfil `vendedor`; custo/lucro de aparelho já era só admin/financeiro (BR-092)
- [x] Plano Técnico — este documento
- [x] Implementação — parte (a), branch `feat/esconder-lucro-vendedor`
- [x] Testes — `TestDashboardVendasOS` (+2, `tests/test_vendas.py`), `Dashboard.test.jsx` (+1)
- [ ] QA Manual — pendente (logar como vendedor e conferir o Dashboard)
- [x] Revisão Arquitetural — abaixo
- [x] Encerramento — `CHANGELOG.md`, BR-100

## O candidato tinha duas partes

### (a) Esconder custo/lucro do vendedor — implementado (BR-100)

Para `vendedor`, `/api/dashboard` não devolve `lucro_total`, `custo_consumido_periodo`,
`custos_operacionais_periodo`, `resultado_liquido`, `gasto_total_estoque`, `lucro_por_tecnico`,
`custos_por_categoria`, nem `lucro` dentro de `resumo_por_vendedor` (lista em
`api_system.CHAVES_CUSTO_LUCRO_DASHBOARD`). Continua vendo faturamento, quantidades, ticket médio,
gráficos de faturamento e serviços, e o bloco de vendas sem lucro de aparelho. A tela esconde os blocos
cujas chaves não vieram.

Recorte: só o perfil `vendedor`, exatamente o que o candidato pediu. `tecnico` e `estoque` continuam
vendo o que viam — ampliar para eles é decisão do PO (ver abaixo).

### (b) Vendedor ver só as próprias vendas — **não implementado, decisão pendente do PO**

Hoje qualquer perfil vê o histórico de vendas inteiro (BR-045 deixa a rota aberta). Restringir o
vendedor às próprias vendas tem efeito colateral em telas que já usam essa listagem:

- o perfil do cliente (KI-062) passaria a mostrar só as compras feitas com aquele vendedor;
- a busca de uma venda para troca/garantia no balcão deixaria de achar a venda de um colega.

Perguntas para o PO:
1. O vendedor deve ver só as próprias vendas no **histórico**, mas continuar achando qualquer venda
   pela busca de cliente/IMEI (garantia, troca)?
2. Técnico e estoque também devem deixar de ver lucro/custo no Dashboard?

## Revisão Arquitetural

Autorização: um ponto só, no fim do endpoint (`_ocultar_custo_e_lucro`), com a lista de chaves numa
constante testada. Coerência: mesma linha de BR-047 (vendedor sem comissão) e BR-092 (custo só
admin/financeiro). Compatibilidade: as chaves só somem para vendedor; frontend antigo mostraria
"R$ 0,00" — não há frontend antigo em produção junto com o backend novo (deploy conjunto).
