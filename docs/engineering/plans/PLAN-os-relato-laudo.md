# PLAN-os-relato-laudo — Relato do cliente, laudo técnico e observação interna

**Data:** 2026-11-11
**Origem:** `docs/product/PRODUCT_BACKLOG.md` → Proposta do benchmark Mercado Phone, Onda 2 item 14
(Etapa 10); evidência em `MERCADO_PHONE.md` → "OS".
**Status:** Aprovado pelo Product Owner (2026-11-11, aprovação geral das etapas) — **muda schema**

> Documento efêmero (ADR-010).

**Estado**

- [x] Discovery — a OS só tinha `observacoes`, que sai no documento do cliente; não havia onde registrar
      o relato do cliente separado do diagnóstico, nem nota só da equipe
- [x] Plano Técnico — este documento
- [x] Implementação — branch `feat/os-relato-laudo`
- [x] Testes — `tests/test_os_relato_laudo.py` (4), `test_migrations.py` atualizado,
      `OrderTextosPanel.test.jsx` (1), `osPdf.test.js` (+1); frontend 203/203; ruff e eslint ok
- [ ] QA Manual — pendente (inclui aplicar `m0006` numa cópia do banco de produção)
- [x] Revisão Arquitetural — abaixo
- [x] Encerramento — `CHANGELOG.md`, BR-102, `DATABASE.md`

## Migration `m0006_os_relato_laudo`

Três `ALTER TABLE os ADD COLUMN ... TEXT` (`relato_cliente`, `laudo_tecnico`, `observacao_interna`) —
aditivas, nullable, sem backfill, idempotentes. **Antes do deploy:** backup e aplicar numa cópia.

## Escopo

- API: `POST/PUT /api/ordens` aceitam os três campos; no `PUT`, campo ausente não mexe no valor (cliente
  antigo não apaga). `GET /api/ordens/<id>` devolve os três. A listagem não devolve (texto longo, não usado).
- Documento do cliente (`/api/ordens/<id>/documento`): leva `relato_cliente` e `laudo_tecnico`; a consulta
  do documento nem lê `observacao_interna`.
- Tela: painel único "Relato, laudo e observações" (`OrderTextosPanel.jsx`) usado por Nova OS e Editar OS
  no lugar do antigo painel "Observações"; PDF desenha relato e laudo quando preenchidos.

## Revisão Arquitetural

Vazamento: a garantia de que a observação interna não sai é estrutural — `buscar_os_para_documento` não
seleciona a coluna — e há teste que procura o texto na resposta inteira do documento. Segurança: o `UPDATE`
por campo usa SQL literal por coluna (`_SQL_GRAVAR_TEXTO_OS`), sem montar nome de coluna em tempo de
execução; teste amarra o mapa à lista `CAMPOS_TEXTO_OS`. Duplicação evitada: o painel é um componente só
para as duas telas. Legado: `api_os.py` segue sem controller/service, como o resto do arquivo.
