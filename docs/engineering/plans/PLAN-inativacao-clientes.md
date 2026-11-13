# PLAN-inativacao-clientes — Inativação de clientes e preservação do histórico (hotfix P1-3)

**Data:** 2026-11-12
**Origem:** QA pós-benchmark, achado P1-3 (KI-066); alternativa B, escolhida pelo Product Owner (inativação
no lugar de exclusão física).
**Status:** Arquitetura **aguardando revisão do Product Owner**. Implementada na branch
`hotfix/inativacao-clientes-historico`, em PR **sem merge e sem deploy**. **Muda o schema** (`m0007`).

> Documento efêmero (ADR-010).

**Estado**

- [x] Discovery: causa-raiz abaixo
- [x] Plano Técnico: este documento
- [x] Implementação: branch `hotfix/inativacao-clientes-historico`
- [x] Testes: `tests/test_clientes_inativacao.py` (26), `test_migrations.py`, `Clientes.test.jsx` (+3);
      backend 999 passaram (só as 5 falhas de ambiente do KI-030), coverage 76%; frontend 214/214; build,
      ruff e eslint ok
- [ ] QA Manual: E2E local feito (API 29/29 e tela no Playwright, numa cópia do banco de QA, com a
      `m0007` aplicada sem alterar contagens nem hashes). Falta aplicar a `m0007` numa cópia do banco de
      produção (depois da aprovação)
- [ ] Revisão Arquitetural: **pendente com o Product Owner**
- [ ] Encerramento: depende do merge

## Causa-raiz

`fluxoly_clientes_service.excluir_cliente` só verificava `os.cliente_id` (`possui_os_vinculada`).
Sobravam dois vínculos sem verificação:

- `vendas.cliente_id`;
- `compras_aparelhos.cliente_id` (compra por troca).

O schema não declara `FOREIGN KEY` (`DATABASE.md` §3), então o `DELETE FROM clientes` passava e deixava
esses vínculos apontando para um id inexistente. As leituras de vendas e de compras usam `LEFT JOIN
clientes`, então nada quebra com erro; o titular simplesmente some (fica `NULL`) do histórico, do recibo
(BR-103), dos lembretes pós-venda e da troca. A perda é silenciosa e não tem como ser desfeita pela tela.

Mapa de vínculos com cliente (banco de QA, conferido por `PRAGMA table_info`): `os.cliente_id`,
`vendas.cliente_id` e `compras_aparelhos.cliente_id`. Garantias de venda, recibo e lembretes chegam ao
cliente **através de `vendas`**, então ficam protegidos pela mesma checagem. A OS também tem o nome em
texto (`os.cliente`), que não depende do cadastro.

Quem grava `os.cliente_id` hoje: só o `scripts/seed_demo.py`. Nova OS e Editar OS não vinculam o
cadastro, e só o documento da OS (`api_os.py:451`) o lê. Por isso a regra "OS não aceita cliente
inativo" fica **registrada para quando o fluxo passar a vincular**, sem código novo agora; não há caminho
de escrita para proteger.

## Migration `m0007_clientes_ativo`

```sql
ALTER TABLE clientes ADD COLUMN ativo INTEGER NOT NULL DEFAULT 1
```

- **Aditiva:** o SQLite preenche `1` em toda linha existente, então todo cliente atual continua ativo.
  IDs, contagens e vínculos não mudam. Sem backfill e sem tocar outra tabela.
- **Idempotente:** usa `_coluna_existe`, no mesmo padrão da `m0006`.
- Sem índice. A tabela é pequena, e o filtro sempre anda junto com `ORDER BY nome`, que já tem
  `idx_clientes_nome`.
- **Rollback:**
  - **Só do código:** seguro sem mexer no banco. O código antigo lista colunas explicitamente
    (`_COLUNAS`) e ignora `ativo`. O `INSERT` antigo não informa a coluna e recebe o default `1`.
  - **Do schema** (só se for preciso, com backup):
    `ALTER TABLE clientes DROP COLUMN ativo; DELETE FROM schema_migrations WHERE id = '0007';`
    O `DROP COLUMN` exige SQLite ≥ 3.35. Isso **perde quem estava inativo**, que fica registrado no
    `audit_log` como `status_change`, e por isso o caminho preferido é o rollback só do código.
- **Antes do deploy:** backup e aplicação numa cópia do banco de produção, conferindo `COUNT(*)` de
  `clientes`, `vendas`, `os` e `compras_aparelhos` e os ids antes e depois.

## Regras (BR-CLIENTE-01 a 05 → BR-024 revisada e BR-024a a BR-024d)

| Regra | Implementação |
|-------|---------------|
| BR-CLIENTE-01: com histórico, não exclui; inativa | `excluir_cliente` passa a checar OS, vendas e compras (`contar_vinculos`). Se houver algum vínculo, responde **409** com a contagem e a orientação "inative o cliente" |
| BR-CLIENTE-02: inativo fora de novas operações | `criar_venda` e `registrar_compra` (troca) recusam cliente inativo. `GET /api/clientes` lista só ativos por padrão. Consulta, documento e relatórios não filtram |
| BR-CLIENTE-03: reativação auditada | `POST /api/clientes/<id>/reativar` grava `status_change` com `{"ativo": false}` → `{"ativo": true}` e não toca em nenhuma outra tabela |
| BR-CLIENTE-04: sem exclusão física com vínculo | A checagem fica no service, então vale também para o `DELETE` direto na API. Cliente **sem nenhum vínculo** continua podendo ser excluído (compatível e seguro: não há o que ficar órfão) |
| BR-CLIENTE-05: perfis autorizados | `inativar` e `reativar` só para **admin**, a mesma matriz do `DELETE` e do `anonimizar` hoje |

## API

| Rota | Mudança |
|------|---------|
| `GET /api/clientes` | Novo `?status=ativos\|inativos\|todos` (padrão `ativos`; valor inválido → 400). Cada item ganha `ativo: bool` |
| `GET /api/clientes/<id>` | Devolve `ativo`. Continua achando o cliente inativo (consulta histórica) |
| `POST /api/clientes/<id>/inativar` | Novo, só admin. Idempotente: se já está inativo, responde `200` com `alterado: false` e não grava auditoria |
| `POST /api/clientes/<id>/reativar` | Novo, só admin. Mesma idempotência |
| `DELETE /api/clientes/<id>` | Com vínculo → **409** e corpo `{"erro": ..., "vinculos": {"os": n, "vendas": n, "compras_aparelhos": n}}`. Sem vínculo, o comportamento atual se mantém |
| `POST /api/vendas` e `POST /api/compras-aparelhos` (troca) | Cliente inativo → 400 com "Cliente inativo — reative o cadastro para usá-lo em uma nova operação." |
| `PUT /api/clientes/<id>` | Sem mudança: cliente inativo pode ser editado (corrigir telefone de quem já comprou, por exemplo) |

**Por que o padrão da listagem é `ativos`:** os dois seletores de nova operação (Nova Venda e Compra por
troca) chamam essa rota sem filtro. Com o padrão `ativos`, um frontend antigo em cache também deixa de
oferecer o cliente inativo, e a API recusa a operação de qualquer forma. Antes da primeira inativação, a
resposta é idêntica à atual, porque todos estão ativos.

**Auditoria:** a ação é `status_change`, que já existe em `ACOES_VALIDAS` e por isso aparece no filtro da
tela de Auditoria sem mudar o serviço dela. O snapshot é `{"ativo": ...}`, sem PII, e portanto fica fora
da máscara de retenção.

## Frontend

- **Clientes:**
  - filtro Ativos/Inativos/Todos (padrão Ativos);
  - badge "Inativo" na linha e no perfil;
  - o botão Excluir (lixeira) vira **Inativar**, com confirmação explicando que o histórico é preservado;
  - cliente inativo mostra **Reativar**.
  - `clientes.delete` continua em `client.js`, porque a API mantém o DELETE de cliente sem vínculo. Só o
    botão da tela foi substituído.
- **Perfil do cliente:** o histórico de OS, compras e garantias continua igual, com o badge de estado no
  topo.
- **Nova Venda e Compra por troca:** passam `status: "ativos"` explicitamente.

## Fora de escopo (proibido pelo PO neste hotfix)

Anonimização LGPD (`anonimizar_cliente` continua igual), limpeza de dados, alteração de vendas ou
garantias, exclusão de clientes existentes.

## Riscos

1. **Excluir sem histórico some da tela.** O DELETE continua na API para cliente sem vínculo, mas a tela
   só oferece Inativar. Se o PO quiser manter "Excluir" para cadastro duplicado sem uso, basta voltar o
   botão nesse caso específico. **Ponto de revisão.**
2. **Clientes já excluídos antes deste hotfix** deixaram vendas e compras órfãs, e isso não é corrigido
   aqui. Diagnóstico somente leitura para rodar numa cópia da produção:
   `SELECT 'vendas', id, cliente_id FROM vendas WHERE cliente_id IS NOT NULL AND cliente_id NOT IN (SELECT id FROM clientes) UNION ALL SELECT 'compras_aparelhos', id, cliente_id FROM compras_aparelhos WHERE cliente_id IS NOT NULL AND cliente_id NOT IN (SELECT id FROM clientes);`
3. **`status` padrão `ativos`** muda o significado da listagem sem parâmetro depois da primeira inativação.
   Um consumidor externo que dependesse de "todos" precisa passar `status=todos`. Não há consumidor
   externo conhecido.
