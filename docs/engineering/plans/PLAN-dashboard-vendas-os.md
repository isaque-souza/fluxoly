# PLAN-dashboard-vendas-os — Dashboard somando vendas e OS

**Data:** 2026-11-11
**Origem:** `docs/product/PRODUCT_BACKLOG.md` → Proposta do benchmark Mercado Phone, Onda 1 (Etapa 4);
evidência em `MERCADO_PHONE.md` → "Tela inicial e Configurações" (tela inicial soma vendas e serviços).
**Status:** Aprovado pelo Product Owner (2026-11-11, aprovação geral das etapas)

> Documento efêmero (ADR-010).

**Estado**

- [x] Discovery — `/api/dashboard` (`api_system.py`) calculava faturamento, lucro e ticket médio só de OS;
      vendas de aparelho (V1.2+) não apareciam na tela inicial
- [x] Plano Técnico — este documento
- [x] Implementação — branch `feat/dashboard-vendas-os`
- [x] Testes — `TestDashboardVendasOS` (`tests/test_vendas.py`, 3), `Dashboard.test.jsx` (+2); backend
      936 passed / 5 failed (KI-030, só Windows local); frontend 190/190; ruff e eslint sem erro
- [ ] QA Manual — pendente
- [x] Revisão Arquitetural — abaixo
- [x] Encerramento — `CHANGELOG.md`

## Escopo

- `/api/dashboard` ganha duas chaves novas, sem alterar as existentes:
  - `vendas`: `quantidade`, `faturamento` (soma de `valor_total`), `ticket_medio` e `por_vendedor`
    (quantidade e faturamento por vendedor, maior primeiro) das vendas **concluídas** do período;
    `lucro_aparelhos` (`aparelhos_com_custo`, `valor_vendido`, `custo_total`, `lucro`) só para
    admin/financeiro.
  - `consolidado`: `faturamento` (OS + vendas), `faturamento_os`, `faturamento_vendas` e `ticket_medio`
    (faturamento consolidado ÷ OS finalizadas + vendas).
- `Dashboard.jsx`: o número principal passa a ser o faturamento consolidado, com a composição
  "Assistência · Vendas" logo abaixo; novo bloco "Vendas de aparelhos" (vendas realizadas, faturamento,
  ticket médio, lucro de aparelhos quando visível, top 5 vendedores).

Arquivos: `api_system.py`, `fluxoly_vendas_repository.py`, `fluxoly_vendas_service.py`,
`fluxoly_compras_aparelhos_service.py`, `frontend/src/pages/Dashboard.jsx`, testes.

## Regras

1. **Compatibilidade.** `faturamento_total`, `lucro_total` e `ticket_medio` continuam sendo só de OS: outros
   consumidores (gráficos, `test_os_interna.py`) não mudam de significado.
2. **Venda cancelada não conta.** Só `status = 'concluida'`.
3. **Lucro de aparelho = BR-092/BR-093.** Mesma conta do relatório mensal de compra de aparelhos (valor
   vendido − valor pago na compra − peças das OS internas). Aparelho que não veio de compra não tem custo
   conhecido e fica fora do lucro (a tela avisa quantos entraram na conta). Não somado ao `lucro_total` de
   OS para não misturar bases diferentes.
4. **Visibilidade.** Faturamento e quantidade de vendas: qualquer autenticado (como o resto do dashboard).
   Lucro/custo: só admin/financeiro (mesma regra de BR-092).
5. **Período.** `start_date`/`end_date` (YYYY-MM-DD) viram `[início 00:00:00, fim+1 00:00:00)` sobre
   `vendas.criado_em`. `criado_em` é UTC (`CURRENT_TIMESTAMP`) e o filtro não converte fuso — mesmo
   comportamento do resto do sistema, mapeado no **KI-061** (decisão de fuso pendente).
6. Sem mudança de schema.

## Revisão Arquitetural

Coerência: leitura pura; o agregado de vendas mora no domínio Vendas e o lucro no domínio Compra de
Aparelhos — o endpoint compõe os dois, porque `compras_aparelhos_service` já importa `vendas_service`
(importar ao contrário criaria ciclo). Autorização: perfil lido da sessão no próprio endpoint, um único
ponto. Vazamento: `por_vendedor` expõe nome do vendedor e faturamento (já visíveis na listagem de vendas);
nenhum custo para vendedor/técnico/estoque. Risco aceito: o ticket médio consolidado mistura reparo e
aparelho (valores de ordem de grandeza diferente) — por isso o ticket médio de OS e o de vendas seguem
separados na tela, e o consolidado fica só na API.
