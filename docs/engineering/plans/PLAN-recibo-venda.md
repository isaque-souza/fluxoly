# PLAN-recibo-venda — Recibo de venda em PDF

**Data:** 2026-11-11
**Origem:** `docs/product/PRODUCT_BACKLOG.md` → Proposta do benchmark Mercado Phone, Onda 3 (Etapa 12);
evidência em `MERCADO_PHONE.md` → "Vendas" (impressão do pedido). O botão "Imprimir" da venda existia como
placeholder ("Impressão ainda não disponível — em breve").
**Status:** Aprovado pelo Product Owner (2026-11-11, aprovação geral das etapas)

> Documento efêmero (ADR-010).

**Estado**

- [x] Discovery — documentos da OS (BR-095 a BR-098) já geram PDF no navegador a partir de um JSON
      fechado no backend; a venda não tinha nada
- [x] Plano Técnico — este documento
- [x] Implementação — branch `feat/recibo-venda`, dois commits: `refactor:` (extrai primitivas do PDF) e
      `feat:` (recibo)
- [x] Testes — `TestReciboVenda` (`tests/test_vendas.py`, 6), `vendaPdf.test.js` (4), `osPdf.test.js`
      inalterado e passando após o refactor; frontend 207/207; ruff e eslint ok
- [ ] QA Manual — pendente (imprimir um recibo real e conferir layout)
- [x] Revisão Arquitetural — abaixo
- [x] Encerramento — `CHANGELOG.md`, BR-103

## Escopo

- `GET /api/vendas/<id>/recibo` (qualquer autenticado): `montar_recibo_venda` no service de Vendas decide
  o que sai (BR-103); controller aplica a regra de CPF (KI-045) e devolve 409 para venda cancelada ou sem
  Dados da Loja, 404 para venda inexistente.
- `frontend/src/lib/vendaPdf.js`: desenha o recibo com as primitivas de `pdfDocumento.js`;
  `imprimirReciboVenda(id)` busca, baixa e transforma erro em toast (atalho "Cadastrar" para admin).
- Botões "Imprimir recibo" no detalhe da venda (só concluída) e na tela de venda concluída.

## Revisão Arquitetural

Vazamento: o recibo é montado campo a campo (lista positiva), não a partir do dict da venda — teste procura
`custo`, `lucro`, `comissao`, `valor_tabela` e `motivo_desconto` na resposta inteira. Duplicação evitada: o
desenho do PDF foi extraído para `pdfDocumento.js` em commit de refactor separado (CLAUDE.md: nunca
misturar refactor com feature no mesmo commit); `textoGarantia` existe nos dois módulos com textos
diferentes de propósito ("Sem garantia registrada" na OS × "Sem garantia" na venda). Autorização: mesmo
nível do detalhe da venda.
