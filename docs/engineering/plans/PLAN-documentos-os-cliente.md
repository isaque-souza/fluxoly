# PLAN-documentos-os-cliente — PDF da OS para o cliente (entrada e entrega) e Dados da Loja

**Data:** 2026-11-10
**Feature:** documentos da OS para o cliente — `docs/product/BUSINESS_RULES.md` BR-094 a BR-098
**Status:** Implementado (PRs 2 e 3) — falta QA manual

> Este documento é efêmero (ver `docs/engineering/adr/ADR-010.md`). Depois que a sprint encerra, ele
> permanece só como histórico da decisão de implementação. O que continuar relevante é promovido para
> `DATABASE.md`, `ARCHITECTURE.md` e `DOMAIN_MODEL.md`.

**Estado**

- [x] Discovery — respostas do CTO em 2026-11-10 (dados da loja em tela; dois documentos, entrada e
  entrega; garantia e termos no PDF), registradas em BR-094 a BR-098
- [x] Plano Técnico — aprovado pelo CTO em 2026-11-10
- [x] Implementação — [x] PR 2 (banco + backend: `m0004`, `fluxoly_dados_loja_*`, rota do documento,
  `tests/test_dados_loja.py` com 12 casos e `tests/test_os_documento.py` com 17); [x] PR 3 (frontend:
  `lib/osPdf.js`, botões na Editar OS, página Dados da Loja)
- [x] Testes — backend e frontend
- [ ] QA Manual
- [ ] Revisão Arquitetural — obrigatória (toca mais de 3 arquivos)
- [ ] Encerramento

---

## Objetivo

Permitir que a loja gere, a partir da tela da OS, um PDF de **entrada** (aparelho deixado na loja) e um
PDF de **entrega** (aparelho retirado, com garantia), com os dados da loja no cabeçalho. Hoje não existe
nenhum documento de OS para o cliente, nem cadastro dos dados da loja.

---

## Escopo

### PR 2 — Banco + backend
- Migration `migrations/versions/m0004_dados_loja.py` (aditiva) + entrada no fim de `migrations/registry.py`.
- Domínio novo `fluxoly_dados_loja_{repository,service,controller}.py` (mesmo padrão de Clientes):
  - `GET /api/dados-loja` — qualquer usuário autenticado (BR-094).
  - `PUT /api/dados-loja` — só `admin`; nome fantasia obrigatório; limites de tamanho por campo
    (`fluxoly_validation.py`); auditoria em `fluxoly_audit.py`, como as demais mutações administrativas.
- Endpoint novo em `api_os.py`: `GET /api/ordens/<id>/documento?tipo=entrada|entrega`. Devolve só o
  conteúdo do documento, montado por **allowlist** (BR-097) — o frontend nunca recebe custo, lucro,
  peças, técnico ou vendedor por essa rota:
  - `loja` (Dados da Loja), `ordem` (id, data, data_finalizado, status, aparelho, modelo, cor, imei,
    técnico, serviços, observações, `valor_total` via `calcular_faturamento_os` — mesma função da
    listagem; ver KI-059), `cliente` (nome; telefone e CPF/CNPJ via `os.cliente_id`, quando houver — CPF/CNPJ só para
    `admin`/`financeiro`, KI-045).
  - `entrega` acrescenta `garantias` (snapshot de `os_reparos`: nome, duração, data de término — BR-062).
  - Erros: 401 sem login; 404 OS inexistente; 400 tipo inválido; 409 OS interna (BR-097), OS Cancelada (BR-095), entrega com
    OS não Finalizada (BR-096), Dados da Loja sem nome fantasia (BR-098).
  - A consulta e a montagem ficam em funções de `fluxoly_os.py` (sem I/O de Flask), a rota só orquestra.
- Registro do blueprint novo em `fluxoly_blueprint_registry.py`.

### PR 3 — Frontend
- `frontend/src/lib/osPdf.js` (novo): função pura `gerarPdfOs(documento, tipo)` usando `jspdf` — que já é
  dependência declarada em `package.json` e hoje não é usada. Import dinâmico (`await import("jspdf")`)
  para não pesar no carregamento inicial. Layout A4: cabeçalho da loja, blocos de cliente/aparelho,
  serviços (com garantia na entrega), valor total (entrega), termos e assinaturas. Fonte padrão do jsPDF
  (Helvetica/WinAnsi) — acentos do português funcionam.
- `EditOrder.jsx`: botões "PDF de entrada" e "PDF de entrega" (este só habilitado para OS Finalizada;
  nenhum dos dois para OS interna ou Cancelada). Sem Dados da Loja, aviso com atalho para o admin (BR-098).
- `frontend/src/pages/DadosLoja.jsx` (nova) + rota `/dados-loja` em `App.jsx` + item "Dados da Loja" no
  menu de administração do `Layout.jsx` (`adminOnly`).
- `client.js`: `dadosLojaApi.obter/salvar` e `ordensApi.documento(id, tipo)`.

---

## Fora de Escopo

- Logotipo da loja no PDF (exige upload e armazenamento de arquivo — feature à parte, se pedida).
- Envio do PDF por WhatsApp/e-mail; registro ou cópia de documentos emitidos (BR-098).
- Exportação em lote (CSV/planilha) de OS — discutida e trocada pelo PDF para o cliente nesta discovery.
- Checklist do aparelho (`/ordens/<id>/checklist`) dentro do PDF de entrada — pode entrar depois.

---

## Impacto no Banco

Tabela nova, linha única:

```sql
CREATE TABLE IF NOT EXISTS dados_loja (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    nome_fantasia TEXT NOT NULL DEFAULT '',
    razao_social TEXT NOT NULL DEFAULT '',
    cnpj TEXT NOT NULL DEFAULT '',
    telefone TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL DEFAULT '',
    endereco TEXT NOT NULL DEFAULT '',
    termos_entrada TEXT NOT NULL DEFAULT '',
    termos_garantia TEXT NOT NULL DEFAULT '',
    atualizado_por INTEGER,
    atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
);
```

Migração puramente aditiva: sem `ALTER` em tabela existente, sem backfill. A linha `id = 1` é criada no
primeiro `PUT` (upsert). Nenhuma outra tabela muda.

---

## Impacto no Backend

Ver Escopo/PR 2. Camadas: controller → service → repository (`ENGINEERING_GUIDE.md` §3.1). O documento da
OS lê Dados da Loja pelo **service** de Dados da Loja, nunca pelo repository dele direto.

---

## Impacto no Frontend

Ver Escopo/PR 3. Nenhuma dependência nova.

---

## Estratégia de Migração

`m0004` roda no boot pelo runner existente (`migrations/runner.py`), como `m0002`/`m0003`. Antes do deploy,
backup do banco de produção (rotina de backup existente). Sem janela de manutenção.

---

## Testes

- `tests/test_dados_loja.py`: GET autenticado/401; PUT admin ok, não-admin 403, nome fantasia vazio 400,
  campo acima do limite 400, upsert (segundo PUT atualiza a mesma linha), auditoria registrada.
- `tests/test_os_documento.py`: entrada e entrega no caso feliz; allowlist — a resposta **não** contém
  `custo_pecas`, `lucro`, `pecas_usadas`, `vendedor` (BR-097) e contém o técnico; cliente vinculado traz
  telefone (e CPF só para admin/financeiro), sem vínculo só o nome; garantia vem do snapshot mesmo após editar o tipo de garantia
  (BR-062); valor total pela mesma regra da listagem; 409 para interna, cancelada, entrega não finalizada e loja
  sem nome; 404; 401.
- `migrations`: teste do runner aplicando `m0004` em banco novo e em banco já na `m0003`.
- Frontend: `osPdf.test.js` (gera PDF de entrada e de entrega sem erro; texto contém os campos esperados e
  não contém custo/lucro), `DadosLoja.test.jsx` (carrega, salva, validação), `EditOrder.test.jsx` (botões
  habilitados/desabilitados por status e tipo; aviso sem Dados da Loja).

---

## Critérios de Aceite

- Admin cadastra os Dados da Loja e eles aparecem no cabeçalho dos dois PDFs.
- PDF de entrada sai em qualquer status exceto Cancelada; PDF de entrega só em OS Finalizada.
- PDF de entrada mostra o valor previsto; o de entrega lista cada serviço com sua garantia e data de
  término, e o valor total. Os dois mostram o técnico.
- Nenhum PDF contém custo, lucro, peças, fornecedor ou vendedor.
- Acentos corretos no PDF.
- Suíte backend e frontend verdes (exceto KI-030, só no Windows local); lint e build ok.

---

## Riscos

- **Vazamento de dado interno no PDF** — mitigado pela allowlist no backend + teste explícito da ausência
  dos campos.
- **Mudança em `api_os.py`** (arquivo crítico) — só uma rota nova, aditiva; `obter_ordem` não muda.
- **Peso do `jspdf` no bundle** — import dinâmico, carregado só ao gerar o PDF.

---

## Rollback

Reverter os PRs 2 e 3. A tabela `dados_loja` pode ficar no banco sem efeito (nada mais a lê); a migration
não altera dados existentes.

---

## Questões em Aberto

Nenhuma. Respondidas pelo CTO em 2026-11-10: o PDF de entrada mostra o valor previsto; o técnico aparece
nos dois documentos; vendedor fora; OS interna sem documento; sem Dados da Loja o PDF não sai. CPF/CNPJ
segue a restrição de leitura de KI-045 (decisão de engenharia, revisável no QA).
