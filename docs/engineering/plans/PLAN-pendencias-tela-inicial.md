# PLAN-pendencias-tela-inicial — Pendências de hoje no Dashboard

**Data:** 2026-11-11
**Origem:** `docs/product/PRODUCT_BACKLOG.md` → Proposta do benchmark Mercado Phone, Onda 1 item 6
(Etapa 6); evidência em `MERCADO_PHONE.md` → "Tela inicial e Configurações" e "Financeiro".
**Status:** Aprovado pelo Product Owner (2026-11-11, aprovação geral das etapas)

> Documento efêmero (ADR-010).

**Estado**

- [x] Discovery — ver "Recorte" abaixo
- [x] Plano Técnico — este documento
- [x] Implementação — branch `feat/pendencias-tela-inicial`
- [x] Testes — `tests/test_pendencias.py` (6), `PendenciasHoje.test.jsx` (3); ruff e eslint sem erro
- [ ] QA Manual — pendente
- [x] Revisão Arquitetural — abaixo
- [x] Encerramento — `CHANGELOG.md`

## Recorte (o que o candidato pedia × o que entrou)

| Pedido no backlog | Decisão | Motivo |
|---|---|---|
| Contas vencendo hoje / vencidas | **Entrou** | Dado já existe (`contas_pagar`/`contas_receber.data_vencimento`) |
| Estoque abaixo do mínimo | **Fora** | Não existe coluna de estoque mínimo — precisa de schema (vai para a Onda 2). O sino de alertas já avisa peça com ≤ 2 unidades (limite fixo, `app.py::obter_alertas_sistema`) |
| IMEI duplicado | **Fora** | `unidades_serializadas.imei` é `UNIQUE`: o banco já impede duplicata; não há o que alertar |

## Escopo

- `GET /api/pendencias` (admin/financeiro; 401/403 nos demais): `contas_pagar` e `contas_receber`, cada um
  com `vencidas` e `vencem_hoje` (`quantidade`, `total`). Só contas `pendente` com vencimento preenchido.
- `PendenciasHoje.jsx` no topo do Dashboard: aparece só para admin/financeiro e só quando há pendência;
  link "Abrir Financeiro".

## Regras

1. Vencida = vencimento < hoje; vence hoje = vencimento = hoje. Paga/recebida/cancelada não conta.
2. "Hoje" é a data do servidor — UTC em produção (KI-061): entre 21h e 0h de Brasília o painel já
   considera o dia seguinte. Mesmo comportamento do resto do sistema até a decisão de fuso.
3. Informativo; não bloqueia nada. Sem mudança de schema.

## Revisão Arquitetural

Coerência: cada repository resume a própria tabela; o endpoint fica em `api_system.py` (agregados da
tela inicial). Duplicação aceita: a consulta é espelhada em `contas_pagar` e `contas_receber`, mesmo
padrão de espelho dos dois módulos (DATABASE.md). Autorização: um ponto só, no endpoint, com o mesmo
conjunto de perfis do Financeiro; o frontend nem chama para outros perfis. Vazamento: nenhum.
