# PLAN-painel-garantias-unificado — Garantias de reparo e de venda na mesma tela

**Data:** 2026-11-11
**Origem:** `docs/product/PRODUCT_BACKLOG.md` → Proposta do benchmark Mercado Phone, Onda 1 item 3 (Etapa 3);
evidência em `MERCADO_PHONE.md` → "Garantia, Checklist e Auditoria" (monitoramento de garantias por item).
**Status:** Aprovado pelo Product Owner (2026-11-11, aprovação geral das etapas)

> Documento efêmero (ADR-010).

**Estado**

- [x] Discovery — `Garantias.jsx` só mostrava garantia de reparo (`/api/garantias`); a garantia de venda
      (V1.5, snapshot em `vendas_itens`) não aparecia em nenhuma listagem
- [x] Plano Técnico — este documento
- [x] Implementação — branch `feat/painel-garantias-unificado`
- [x] Testes — `TestPainelGarantiasVenda` + `test_classificar_garantia_usa_mesmo_limiar_da_os`
      (`tests/test_vendas.py`), `Garantias.test.jsx` (2); frontend 188/188; ruff ok
- [ ] QA Manual — pendente
- [x] Revisão Arquitetural — abaixo
- [x] Encerramento — `CHANGELOG.md`

## Escopo

- `GET /api/vendas/garantias?q=` (domínio Vendas: controller → service → repository): uma linha por item
  de venda **concluída** com garantia concedida (`garantia_duracao_meses > 0`), com `dias_restantes` e
  `status_garantia` (`ativa` / `vencendo` ≤ 7 dias / `vencida`) e contagem por status. Busca por cliente,
  IMEI ou produto. Ordenado pelo vencimento mais próximo.
- `Garantias.jsx`: abas **Assistência** (como antes) e **Vendas**, contagem de cada aba e resumo
  ativas/vencendo/vencidas da aba aberta.

## Regras

1. Leitura do snapshot gravado (BR-057) — nunca recalcula pelo tipo de garantia atual.
2. Venda cancelada e item "sem garantia" (0 meses, BR-055) não aparecem.
3. Mesmo limiar de "vencendo" da garantia de reparo (`api_garantias.py::_classificar_garantia`, 7 dias),
   para a loja ler as duas abas com a mesma régua.
4. Acesso: qualquer autenticado, igual a `/api/garantias` (consulta de balcão).
5. Sem mudança de schema.

## Revisão Arquitetural

Coerência: leitura pura. Autorização: mesmo nível da listagem de garantia de reparo. Vazamento: devolve
nome do cliente e IMEI, já visíveis a qualquer perfil na listagem de vendas; nenhum valor financeiro.
Duplicação aceita: o limiar de 7 dias existe em dois lugares (`api_garantias.py` legado e
`fluxoly_vendas_service.DIAS_GARANTIA_VENCENDO`), amarrados por teste; unificar quando `api_garantias.py`
migrar para o padrão controller/service.
