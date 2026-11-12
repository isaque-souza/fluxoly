# PLAN-alertas-dados — Alertas de margem (venda abaixo do custo, aparelho sem custo)

**Data:** 2026-11-11
**Origem:** `docs/product/PRODUCT_BACKLOG.md` → Proposta do benchmark Mercado Phone, Onda 1 item 5
(Etapa 5); evidência em `MERCADO_PHONE.md` → "Clientes e Relatórios".
**Status:** Aprovado pelo Product Owner (2026-11-11, aprovação geral das etapas)

> Documento efêmero (ADR-010).

**Estado**

- [x] Discovery — o custo por aparelho (BR-092) só existe para unidade de compra; `produtos.preco_custo`
      existe no cadastro mas não é usado em lugar nenhum de lucro; nada avisa venda no prejuízo
- [x] Plano Técnico — este documento
- [x] Implementação — branch `feat/alertas-dados`
- [x] Testes — `TestAlertasDeDados` (`tests/test_compras_custo_lucro.py`, 4),
      `CompraRevendaReport.test.jsx` (+2); ruff e eslint sem erro
- [ ] QA Manual — pendente
- [x] Revisão Arquitetural — abaixo
- [x] Encerramento — `CHANGELOG.md`, BR-099

## Escopo

`GET /api/compras-aparelhos/relatorio?mes=` ganha a chave `alertas` (BR-099):

- `vendas_abaixo_do_custo`: itens de vendas concluídas do mês com `valor_venda < custo`, com `custo`,
  `prejuizo` e `base_custo` (`compra` = custo BR-092; `catalogo` = `produtos.preco_custo`, só quando a
  unidade não veio de compra).
- `aparelhos_sem_custo`: `{total, itens}` — unidades de produto em estoque (disponível/em reparo) sem
  compra ativa e sem `preco_custo`; `itens` limitado a 50.

Tela: bloco "Alertas de margem" no relatório "Compra e revenda" (`CompraRevendaReport.jsx`), escondido
quando não há alerta.

## Regras

1. Só informa, não bloqueia venda (bloquear seria regra nova de venda — decisão do PO).
2. Custo da compra (BR-092) tem prioridade sobre o `preco_custo` do cadastro.
3. Mesma autorização do relatório: admin/financeiro (custo é BR-092/BR-047).
4. Sem mudança de schema. Período sobre `vendas.criado_em` em UTC (KI-061), igual ao resto do relatório.

## Revisão Arquitetural

Coerência: fica no domínio Compra de Aparelhos, que já é dono do custo (BR-092) e do relatório (BR-093);
reaproveita `buscar_vendas_de_aparelhos_comprados` — só a consulta por `preco_custo` e a de estoque sem
custo são novas. Autorização: inalterada. Vazamento: nenhum dado novo além de custo, já restrito.
Risco aceito: loja que não cadastra `preco_custo` nem registra compra verá muitos "sem custo" — o total
e o limite de 50 evitam tela gigante; é justamente o sinal que o alerta quer dar.
