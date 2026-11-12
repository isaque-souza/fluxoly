# PLAN-tela-auditoria — Tela de consulta do `audit_log`

**Data:** 2026-11-11
**Origem:** `docs/product/PRODUCT_BACKLOG.md` → "Proposta — candidatos do benchmark Mercado Phone", Onda 1
item 2 (Etapa 2); evidência em `docs/product/research/BENCHMARKS/MERCADO_PHONE.md` → "Garantia, Checklist e
Auditoria".
**Status:** Aprovado pelo Product Owner (2026-11-11: "pode seguir com todas as etapas… eu permito tudo")

> Documento efêmero (ADR-010). Depois do merge fica só como histórico da decisão de implementação.

**Estado**

- [x] Discovery — `audit_log` já é gravado por OS, caixa, vendas/itens, contas a pagar/receber, clientes,
      produtos, unidades, compras de aparelho e dados da loja; não existe tela nem rota de leitura geral
- [x] Plano Técnico — este documento
- [x] Implementação — branch `feat/tela-auditoria`
- [x] Testes — `tests/test_auditoria.py` (11), `Auditoria.test.jsx` (3); suíte backend 929 passed / 5
      failed (KI-030, só Windows local); frontend 186/186; ruff e eslint sem erro; build ok
- [ ] QA Manual — pendente (servidor)
- [x] Revisão Arquitetural — ver seção abaixo
- [x] Encerramento — `CHANGELOG.md`

---

## Escopo

- `GET /api/auditoria` — filtros `entidade`, `entidade_id`, `usuario_id`, `acao`
  (`create`/`update`/`delete`/`status_change`), `data_inicio`, `data_fim`; paginação `page`/`per_page`
  (máximo 100); ordenação mais recente primeiro; devolve também a lista de entidades existentes (para o
  filtro) e, por registro, `alteracoes` = diff campo a campo de `valor_anterior` × `valor_novo`.
- Tela `/auditoria` (`Auditoria.jsx`): filtros, tabela paginada, detalhe antes/depois. Menu
  "Administração" → "Auditoria".

Arquivos: `fluxoly_auditoria_{repository,service,controller}.py` (novos), `fluxoly_blueprint_registry.py`,
`frontend/src/pages/Auditoria.jsx` (novo), `frontend/src/App.jsx`, `frontend/src/components/Layout.jsx`,
`frontend/src/api/client.js`, testes.

## Regras

1. **Só leitura.** Nenhuma rota de escrita (POST/PUT/PATCH/DELETE respondem 405). A escrita continua
   exclusiva de `fluxoly_audit.py::registrar_log_auditoria`.
2. **Acesso admin/financeiro**, checado no controller (mesmo conjunto de `usuario_pode_financeiro()` de
   Vendas); vendedor/técnico/estoque recebem 403, anônimo 401. Item de menu com o mesmo filtro.
3. **LGPD:** o snapshot é devolvido como gravado — se já foi mascarado pela retenção
   (`mascarar_audit_log_pii_expirado`), a tela mostra mascarado. Nada é remontado.
4. Sem mudança de schema.

## Revisão Arquitetural (4 eixos do ADR-010)

1. Coerência do domínio — leitura pura; não cria regra nova.
2. Autorização centralizada — uma checagem só, no único endpoint.
3. Vazamento de dado — `audit_log` pode conter dado pessoal de clientes (snapshot); por isso o acesso é
   restrito a admin/financeiro, os mesmos perfis que já veem CPF/CNPJ (KI-045).
4. Máquina de estados — não se aplica.

Risco aceito: volume do `audit_log` cresce; consulta paginada e o índice existente
`idx_audit_log_entidade (entidade, entidade_id)` cobrem o filtro mais comum. Filtro só por data faz scan —
aceitável no volume atual; reavaliar se a tabela passar de centenas de milhares de linhas.
