# PLAN-termos-garantia-os — Termos de garantia cadastrados e escolhidos na OS

**Data:** 2026-11-17
**Origem:** pedido do PO (2026-11-17): "tem uma função chamada termos de garantia que a gente cria termos
diferentes e dentro da OS escolhemos qual termo usar". Lacuna registrada em `MERCADO_PHONE.md` → "Garantia,
Checklist e Auditoria" e em `PRODUCT_BACKLOG.md` (item 26).
**Status:** Aprovado pelo PO em 2026-11-17, com as decisões 3 a 6 como propostas. **Muda o schema**
(migration `m0007`).

> Documento efêmero (ADR-010).

**Estado**

- [x] Discovery: ver "Situação atual" e "Decisões"
- [x] Plano Técnico: este documento
- [x] Implementação: branch `feat/termos-garantia-os`
- [x] Testes: `tests/test_termos_garantia.py` (22), `test_migrations.py` atualizado; `TermosGarantia.test.jsx`
      (4), `EditOrder.test.jsx` (+4). Backend 1000 passed; frontend 219/219; eslint sem erro; build ok
- [ ] QA Manual: pendente (inclui aplicar `m0007` numa cópia do banco de produção)
- [x] Revisão Arquitetural: abaixo
- [x] Encerramento: `CHANGELOG.md`, BR-105, `DATABASE.md`, `DATA_DICTIONARY.md`, `PRODUCT_BACKLOG.md`

## Situação atual (verificada no código em 2026-11-17)

| Peça | O que guarda | Onde entra |
|---|---|---|
| `tipos_garantia` (BR-055) | nome + `duracao_meses`, sem texto | escolhido **por reparo** ao finalizar a OS (BR-061), com snapshot em `os_reparos` (BR-062) |
| `dados_loja.termos_garantia` (BR-094) | **um único texto** da loja | impresso em todo "PDF de entrega" (`fluxoly_os.py::montar_documento_cliente`, `osPdf.js`) |

A loja não consegue ter "Termo assistência 90 dias", "Termo troca de tela" etc. com textos diferentes, nem
escolher qual sai no comprovante de uma OS.

## Decisões

**Já tomadas pelo PO (2026-11-17):**
1. **Um termo por OS**, não por reparo.
2. Nesta etapa, **só a OS**. A venda fica para uma etapa posterior. O cadastro já nasce sem nada que o
   prenda à OS, para a venda poder reutilizá-lo depois.

**Aprovadas pelo PO em 2026-11-17, como propostas (texto entre parênteses):**
3. **O termo é obrigatório ao finalizar?** (Proposta: **opcional**. Sem termo escolhido, o PDF usa o texto de
   Dados da Loja, como hoje, então nenhuma OS existente nem fluxo atual muda de comportamento.)
4. **Pode trocar o termo de uma OS já finalizada?** (Proposta: **sim, só `admin`, com `audit_log`**, mesmo
   padrão da correção de garantia de reparo, BR-065. Sem isso, um termo escolhido errado só se corrige
   reabrindo a OS.)
5. **Prazo:** o termo **não** tem prazo próprio. O prazo continua no Tipo de Garantia de cada reparo, porque
   uma OS com dois serviços pode ter prazos diferentes e o termo é um só. (Proposta: manter assim. Se o
   texto citar prazo, é texto livre da loja.)
6. **Texto de Dados da Loja:** continua existindo como fallback. (Proposta: manter, e renomear o rótulo na
   tela para "Termos de garantia padrão" para deixar claro o papel.)

## Regra de negócio (BR-105, a registrar no Encerramento)

- A loja cadastra **Termos de Garantia**: nome (obrigatório), texto (obrigatório, até 4000 caracteres, mesmo
  limite de `dados_loja`) e ativo. Só `admin` cria, edita e inativa. Não há exclusão, só inativação, igual a
  Tipos de Garantia.
- Ao **finalizar** uma OS de cliente (não interna), escolhe-se **um** termo ativo, opcional se a decisão 3 for
  aprovada como proposto. Vale para as duas rotas que finalizam (`PUT /api/ordens/<id>` e
  `PATCH /api/ordens/<id>/status`), como na BR-061.
- O termo é gravado na OS como **snapshot** (id, nome e texto do momento). Editar ou inativar o termo depois
  **não muda** OS já finalizadas. Mesmo princípio da BR-062.
- **PDF de entrega:** imprime o texto do snapshot. Sem snapshot, imprime `dados_loja.termos_garantia`. Sem
  nenhum dos dois, o bloco não aparece (como hoje).
- **Cancelar** a OS zera o snapshot do termo, como a BR-064 faz com a garantia de reparo. **Reabrir e
  finalizar de novo** pede o termo outra vez e regrava o snapshot, como já acontece com a garantia de reparo.
- PDF de entrada: inalterado (continua com `termos_entrada`).

## Migration `m0007_termos_garantia`

Aditiva e idempotente, sem backfill:

```sql
CREATE TABLE IF NOT EXISTS termos_garantia_modelos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    texto TEXT NOT NULL,
    ativo INTEGER NOT NULL DEFAULT 1,
    criado_em TEXT NOT NULL DEFAULT (datetime('now')),
    atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
);
ALTER TABLE os ADD COLUMN termo_garantia_id INTEGER;     -- nullable
ALTER TABLE os ADD COLUMN termo_garantia_nome TEXT;      -- snapshot
ALTER TABLE os ADD COLUMN termo_garantia_texto TEXT;     -- snapshot
```

O nome `termos_garantia_modelos` evita confusão com a coluna `dados_loja.termos_garantia`, que continua
existindo. OS antigas ficam com as três colunas `NULL` e seguem imprimindo o texto de Dados da Loja.
**Antes do deploy:** backup verificado e aplicar a migration numa cópia do banco de produção (QA Manual).

## Arquivos

| Arquivo | Mudança |
|---|---|
| `migrations/versions/m0007_termos_garantia.py` | novo (acima) |
| `fluxoly_termos_garantia_repository.py` / `_service.py` / `_controller.py` | novos, no mesmo padrão de `fluxoly_tipos_garantia_*` (listar, criar, editar, inativar; `obter_termo_garantia` para a OS) |
| `fluxoly_blueprint_registry.py` | registra o blueprint `/api/termos-garantia` |
| `fluxoly_os.py` | `resolver_termo_garantia_os`, `gravar_termo_garantia_os` e `zerar_termo_garantia_os`; `buscar_os_para_documento` lê o snapshot; `montar_documento_cliente` usa o snapshot ou o fallback da loja |
| `api_os.py` | as duas rotas de finalização aceitam `termo_garantia_id`; o cancelamento zera; rota admin para trocar o termo (decisão 4); `GET /ordens/<id>` devolve o termo |
| `frontend/src/api/client.js` | `termosGarantiaApi`; `patchStatus` aceita o termo |
| `frontend/src/pages/TermosGarantia.jsx` | nova tela de cadastro (lista, criar, editar, inativar), espelhando `TiposGarantia.jsx` |
| `frontend/src/App.jsx`, `frontend/src/components/Layout.jsx` | rota e item de menu "Termos de Garantia" (só admin) |
| `frontend/src/pages/EditOrder.jsx` | campo "Termo de garantia" no diálogo de finalização que já existe (o mesmo onde se escolhem os tipos por reparo); mostra o termo atual da OS finalizada |
| `frontend/src/pages/DadosLoja.jsx` | só o rótulo (decisão 6) |
| testes | `tests/test_termos_garantia.py` (cadastro e permissões), `tests/test_os_documento.py` (snapshot × fallback, cancelamento zera, edição do termo não altera OS finalizada), `tests/test_migrations.py`; `TermosGarantia.test.jsx`, `osPdf.test.js` |

`osPdf.js` não muda: ele já imprime `documento.termos` como "TERMOS DE GARANTIA". Só a origem do texto muda,
no backend.

São mais de 3 arquivos, há mudança em `api_os.py` e no schema, então o plano precisa ser aprovado
(CLAUDE.md).

## Riscos

- **Schema em produção:** a migration é aditiva (tabela nova e colunas nullable), sem reescrever dados.
  Mitigação: backup e teste numa cópia do banco antes do deploy.
- **Finalização pelo Kanban:** o Kanban chama `patchStatus` sem garantias. Numa OS com reparos, isso já é
  recusado hoje pela BR-061. Com o termo opcional, o Kanban segue igual e a OS finalizada por ali fica sem
  termo (o PDF usa o fallback da loja). Se o termo virar obrigatório (decisão 3), o Kanban também passa a
  recusar OS sem reparos, e isso precisa ser aceito explicitamente.
- **Vazamento no documento (BR-097):** o documento só ganha o texto do termo, que é público por natureza.
  Nenhum campo interno novo.
- **Duplicação:** o CRUD repete o formato de Tipos de Garantia, mas é uma entidade diferente (texto × prazo).
  Juntar as duas tabelas mudaria BR-055/061 e a venda, o que está fora do escopo pedido.

## Fora do escopo

Termo na venda (próxima etapa); termo de compra do usado (backlog item 23); aplicação retroativa de termos
(sugerido não implementar); editor de texto rico ou pré-visualização com cabeçalho (o PDF já monta o
cabeçalho da loja); finalizar pelo Kanban.

## Revisão Arquitetural

- **Camadas:** o cadastro segue controller/service/repository (`fluxoly_termos_garantia_*`). A OS só usa
  `obter_termo_garantia` do service; o SQL do snapshot vive em `fluxoly_os.py`, junto com o resto da OS.
- **Duplicação:** as duas rotas que finalizam (PUT e PATCH) e a rota de troca usam os mesmos dois helpers de
  `api_os.py` (`_resolver_termo_garantia`, `_definir_termo_garantia`), então validação, gravação e auditoria
  ficam num lugar só. O limite do texto vem de `fluxoly_dados_loja_service.LIMITES`, sem número repetido.
- **Auditoria:** `audit_log` com `entidade='os'`, ações `termo_garantia_definido` (finalização) e
  `termo_garantia_alterado` (troca e cancelamento), guardando só id e nome (o texto completo fica na OS).
- **Documento (BR-097):** só o texto do termo entra no comprovante. `GET /ordens/<id>` devolve apenas id e
  nome.
- **Legado:** `api_os.py` segue sem controller/service, como o resto do arquivo. O formatador acusa
  trechos antigos de `fluxoly_os.py` que já estavam assim no `main`; não foram tocados.
