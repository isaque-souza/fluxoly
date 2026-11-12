# PLAN-os-data-previsao — Previsão de entrega da OS e OS atrasada

**Data:** 2026-11-11
**Origem:** `docs/product/PRODUCT_BACKLOG.md` → Proposta do benchmark Mercado Phone, Onda 2 item 13
(Etapa 9); evidência em `MERCADO_PHONE.md` → "OS". Item "OS atrasadas" do Dashboard Executivo da
Release 1.0.
**Status:** Aprovado pelo Product Owner (2026-11-11, aprovação geral das etapas) — **muda schema**

> Documento efêmero (ADR-010).

**Estado**

- [x] Discovery — `os` não tinha data de previsão; "atrasada" não existia
- [x] Plano Técnico — este documento
- [x] Implementação — branch `feat/os-data-previsao`
- [x] Testes — `tests/test_os_data_previsao.py` (7), `test_migrations.py` atualizado,
      `OrderAtrasadaBadge.test.jsx` (3), `Orders.test.jsx` (+1); frontend 201/201; ruff e eslint ok
- [ ] QA Manual — pendente (inclui aplicar `m0005` numa cópia do banco de produção)
- [x] Revisão Arquitetural — abaixo
- [x] Encerramento — `CHANGELOG.md`, BR-101, `DATABASE.md`

## Migration `m0005_os_data_previsao`

`ALTER TABLE os ADD COLUMN data_previsao TEXT` — aditiva, nullable, sem backfill, idempotente (checa
`PRAGMA table_info`). Rollback: a coluna pode ficar (nada a lê se o código voltar); SQLite antigo não
remove coluna, e não é preciso.

**Antes do deploy:** backup do banco (regra "o banco é sagrado") e aplicar a migration numa cópia.

## Escopo

- API: `POST/PUT /api/ordens` aceitam `data_previsao` (`AAAA-MM-DD` ou vazio; outro formato → 400).
  No `PUT`, campo ausente **não mexe** na previsão (cliente antigo não apaga); vazio limpa.
  `GET /api/ordens` e `/api/ordens/<id>` devolvem `data_previsao` e `atrasada`.
  `/api/dashboard` devolve `ordens_atrasadas` (mesmo recorte de período/técnico de `ordens_abertas`).
- Tela: campo "Previsão de entrega" em Nova OS e Editar OS; selo "Atrasada" na lista e no Kanban;
  métrica "Atrasadas" na lista de OS e "OS Atrasadas" no Dashboard (só quando > 0).

## Regras (BR-101)

1. Atrasada = status aberto e `data_previsao < hoje`. No dia da previsão ainda não atrasou.
2. Calculado na hora (`fluxoly_core.os_atrasada`), nunca gravado.
3. "Hoje" é a data do servidor (UTC em produção, KI-061).
4. OS importada do Mercado Phone e OS interna nascem sem previsão.

## Revisão Arquitetural

`api_os.py` é legado (sem controller/service); a mudança segue o padrão do arquivo, com a regra pura em
`fluxoly_core.py` testada isoladamente. A coluna entra no fim do `SELECT` de `carregar_os_com_relacoes`
(índice 18) para não deslocar os índices posicionais usados em `api_os.py` e `api_system.py`.
Autorização: inalterada (mesmos perfis que já criam/editam OS). Vazamento: nenhum.
