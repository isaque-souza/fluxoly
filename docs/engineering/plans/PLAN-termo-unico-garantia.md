# PLAN-termo-unico-garantia — Termo de Garantia = Tipo de Garantia (nome + prazo + texto)

**Data:** 2026-11-18
**Origem:** retorno do PO depois do deploy de `PLAN-termos-garantia-os.md` (PRs #108/#109): "existe agora termo
de garantia e tipo de garantia, o que não faz sentido; o termo é atrelado ao tipo — termo de 3 meses já vem
com a contagem de 3 meses". Respostas do PO: nenhum termo cadastrado em produção; prazo em meses; Nova OS
deve pedir o termo quando a OS é criada já finalizada (correção separada, `fix/`).
**Status:** Aprovado pelo PO (2026-11-18). **Muda o schema** (migration `m0008`).

> Documento efêmero (ADR-010). Substitui a decisão 5 de `PLAN-termos-garantia-os.md` ("termo sem prazo").

**Estado**

- [x] Discovery: acima
- [x] Plano Técnico: este documento
- [x] Implementação: branch `feat/termo-unico-garantia`
- [x] Testes: `tests/test_termos_garantia.py` reescrito (20), `test_migrations.py`; `TiposGarantia.test.jsx`
      (3, novo), `EditOrder.test.jsx` (5 sobre o termo). Backend 998 passed; frontend 219/219; eslint e build ok
- [ ] QA Manual
- [x] Revisão Arquitetural: abaixo
- [x] Encerramento: BR-105 (e nota em BR-061), `DATABASE.md`, `DATA_DICTIONARY.md`, `CHANGELOG.md`,
      `PRODUCT_BACKLOG.md`, `PROJECT_STATUS.md`

## Decisão

Um cadastro só: `tipos_garantia` ganha `texto` e passa a ser chamado **Termos de Garantia** na interface (na
API e no banco segue `tipos_garantia`, para não quebrar Vendas). Na OS, um termo para a OS inteira:
`tipo_garantia_id` → prazo gravado em cada linha de `os_reparos` (BR-062) + snapshot nome/texto em
`os.termo_garantia_*` (colunas da `m0007`, reaproveitadas; agora apontam para `tipos_garantia`).

## Migration `m0008_tipos_garantia_texto`

`ALTER TABLE tipos_garantia ADD COLUMN texto TEXT NOT NULL DEFAULT ''` — aditiva, idempotente.
`termos_garantia_modelos` (m0007) fica sem uso e vazia; não é removida aqui.

## Escopo

- Backend: `tipos_garantia` com texto (`PUT` sem o campo mantém o texto). `PUT /ordens/<id>` e
  `PATCH /ordens/<id>/status` aceitam `tipo_garantia_id` (um por OS); o mapa antigo `garantias` por reparo
  continua aceito, sem termo na OS. `PATCH /ordens/<id>/termo-garantia` recebe `tipo_garantia_id` e regrava o
  termo e o prazo dos reparos (data de início mantida), com auditoria. Removidos
  `fluxoly_termos_garantia_*` e `/api/termos-garantia`.
- Frontend: tela Tipos de Garantia → "Termos de Garantia" com campo de texto; menu único; `/termos-garantia`
  redireciona; diálogo de finalização com um só select obrigatório (`TermoGarantiaSelect`, componente
  compartilhado para a Nova OS no `fix/` seguinte); rótulos de Vendas renomeados.

## Riscos

- OS finalizadas antes desta versão: garantias por reparo intactas; sem termo na OS → PDF com o texto padrão.
- Vendas: mesma lista e mesmos ids; só rótulos mudaram.
- Kanban: arrastar para Finalizado numa OS com reparo continua recusado (não envia termo), como antes.

## Revisão Arquitetural

Um conceito, um cadastro: some a duplicação conceitual e de código (CRUD separado removido). A regra "um
termo por OS" fica num único helper (`_resolver_garantia_da_os`) usado pelas duas rotas que finalizam; a
troca reutiliza `corrigir_garantia_reparo` (BR-065) em vez de SQL novo. Dívida registrada: tabela
`termos_garantia_modelos` sem uso (DATABASE.md).
