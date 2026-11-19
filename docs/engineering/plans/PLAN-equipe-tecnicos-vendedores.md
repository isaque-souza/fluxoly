# PLAN-equipe-tecnicos-vendedores — Cadastro de Equipe (técnicos e vendedores da OS)

**Status:** decisões do PO aprovadas (Q1–Q11, 2026-11-18); arquitetura aceita (**ADR-016**); regras
**BR-106 a BR-111** registradas. **Nada implementado, nenhuma migration executada.**
**Data:** 2026-11-18
**Etapa (ADR-010):** Plano Técnico. Não há questões em aberto.
**Migration prevista:** `m0010` (a próxima livre; `m0009` é a última em `main`).

---

## Objetivo

Os técnicos e vendedores da OS são hoje nomes fixos no código. A meta é transformá-los em pessoas
cadastradas no banco, com histórico preservado. Isso não é só trocar texto por id: é criar no Fluxoly o
conceito de **quem trabalha na loja**, que hoje não existe. Esse conceito precisa cobrir:

- quem tem acesso ao sistema e quem não tem;
- quem acumula as duas funções;
- quem foi desligado;
- o que uma OS antiga mostra depois que a pessoa sai ou muda de nome.

## Regra de execução (PO, 2026-11-18)

> Nenhuma migration que afete dados de produção é executada sem **revisão explícita** do PO e **backup
> confirmado**. Cada PR deste plano tem escopo próprio, sem refatorações oportunistas.
>
> Três aprovações distintas, cada uma com revisão própria:
> 1. **Documentação aprovada** não significa implementação aprovada.
> 2. **Código implementado** não significa autorizado para produção (merge na `main` = deploy, ADR-015).
> 3. **Migration preparada** não significa autorizada para execução (§5.1).

---

## Registro das decisões do PO (2026-11-18)

| # | Pergunta | Decisão | Onde vive |
|---|---|---|---|
| Q1 | Técnico obrigatório na OS? | **Não.** A OS pode ficar sem técnico; "Aguardando definição" vira ausência de atribuição; filtros e indicadores mostram as OS sem técnico | BR-108 |
| Q2 | Nomes da lista que nunca apareceram em OS? | **Cadastro manual** pela tela de Equipe após o deploy; a migration só cria a partir dos nomes encontrados nas OS | §5.2 |
| Q3 | Nomes repetidos? | **Homônimos permitidos**; nome não identifica; informação complementar para diferenciar; **aviso** de nome duplicado | BR-106 |
| Q4 | Inativar usuário desliga colaborador? | **Independentes**; o admin inativa os dois quando a pessoa sai | BR-107 |
| Q5 | Quem edita OS finalizada? | **Só admin, com justificativa obrigatória e auditoria** (quem, quando, antes, depois, justificativa) | BR-111 (escopo: técnico/vendedor, ver Q9) |
| Q6 | Unificar duplicados? | **Só admin**, com confirmação, vínculos visíveis, transferência transacional, nomes históricos preservados, auditoria | BR-110 |
| Q7 | Quem acessa a tela de Equipe? | **Admin por padrão**, por uma permissão nomeada que possa ser concedida a outros perfis no futuro; técnico e vendedor comuns não gerenciam | BR-106, §6.2 |
| Q8 | Alternativa C? | **Aprovada** | ADR-016 |
| Q9 | Bloqueio geral de edição de OS finalizada? | **Discovery separada.** Nesta entrega só técnico e vendedor são restritos; troca de reparo, peças, valores, termo (BR-105) e correção de garantia (BR-065) seguem exatamente como hoje | BR-111, §10 |
| Q10 | Finalizar OS sem técnico? | **Bloqueado.** Criar, salvar e editar sem técnico: permitido. Finalizar: exige técnico atribuído, com mensagem explicando que é preciso atribuir um técnico antes | BR-108, §6.4 |
| Q11 | Critério de nome duplicado? | **Nome completo normalizado**: ignora caixa, acentos e espaços excedentes. Sem comparar só o primeiro nome e sem fuzzy matching. O aviso não bloqueia; o admin confirma que são pessoas diferentes | BR-106, §6.3 |
| A | Snapshot do nome | O nome gravado na OS é histórico, não referência dinâmica | BR-109 |
| B | KI-079 | PR próprio; proteção no backend; revisão de todas as exclusões físicas; testes de regressão | KI-079, §10 |

---

## 1. Diagnóstico da estrutura atual

### 1.1 Onde estão as pessoas hoje

| Conceito | Onde fica | Tipo | Validação |
|---|---|---|---|
| Vendedor da OS | `os.vendedor` (`TEXT`, criado por `ALTER` no baseline) | nome solto | precisa estar em `VENDEDORES` (`fluxoly_os.py:395`), ou vazio |
| Técnico da OS | `os.tecnico` (`TEXT`, tabela original) | nome solto | **só exige não-vazio** (`api_os.py:794`/`:935`); a lista fixa só limita a tela |
| Listas | `fluxoly_reference_data.py:195` `VENDEDORES` (7 nomes) e `:205` `TECNICOS` (2 nomes + `"Aguardando definicao"`) | constante Python | entram via `deps` (`fluxoly_blueprint_registry.py:340`) e saem em `GET /api/constantes` (`api_system.py:75`) |
| Vendedor da Venda | `vendas.vendedor_id` → `usuarios.id` | id do usuário logado | sem FK; nome por `LEFT JOIN usuarios` (`fluxoly_vendas_repository.py:33`) |
| Usuário | `usuarios (id, nome, usuario UNIQUE, senha_hash NOT NULL, perfil TEXT, ativo)` | um perfil só | `PERFIS_OPCOES` (`fluxoly_core.py:44`) |

O resultado são **dois modelos de "vendedor" que não conversam**: na Venda o vendedor é um usuário, na
OS é um nome.

### 1.2 Quem lê `os.tecnico` / `os.vendedor` (inventário completo)

**Backend**

- `api_os.py:305-396`: listagem de OS. Filtros `?tecnico=` e `?vendedor=` comparam o texto exato e a
  busca livre inclui os nomes.
- `api_os.py:426-487`: detalhe da OS.
- `api_os.py:757-1013`: criação e edição da OS (grava os dois textos, exige técnico, valida o vendedor,
  inclusive ao editar, `:943`).
- `api_system.py:133-271`: dashboard. `lucro_por_tecnico` e `resumo_por_vendedor` são agrupados pelo
  texto, e o filtro `?tecnico=` também é por texto. `_ocultar_custo_e_lucro` (BR-100) remove o lucro
  quando o perfil é vendedor.
- `fluxoly_reports.py:226-376`: relatório de técnicos (JSON e PDF) agrupado por texto, com o vazio
  agrupado como `"Tecnico nao informado"`.
- `api_garantias.py:53-106`: painel de garantias exibe o técnico.
- `fluxoly_os.py:573-675`: documento da OS para o cliente (BR-097) leva o técnico.
- `fluxoly_mercadophone.py:520-1230`: `canonicalizar_para_lista` encaixa nomes externos nas listas fixas.
  A integração está desligada por flag (ADR-014).

**Frontend**

- `NewOrder.jsx:307-322` e `EditOrder.jsx:590-605`: selects alimentados por `constants.tecnicos` e
  `constants.vendedores`.
- `Orders.jsx:22-40` e `OrderFilters.jsx`: os filtros são montados com os nomes encontrados nas OS
  carregadas.
- `OrderTable.jsx:37`, `Kanban.jsx:162`, `osPdf.js:56`: exibição do nome.
- `Dashboard.jsx:124-180`: filtro de técnico vindo de `constantes`, além do gráfico de técnicos e do
  bloco de top vendedores.

**Testes que dependem disso:** `tests/conftest.py`, `test_os_*`, `test_permissions.py`,
`test_stock_os_integration.py`, `Dashboard.test.jsx`, `App.test.jsx` e outros.

### 1.3 Problemas encontrados

1. **Mudança na equipe exige deploy.**
2. **Nomes reais no código-fonte** (`fluxoly_reference_data.py`, docstring da linha 342,
   `scripts/seed_demo.py:119`) e no histórico do git.
3. **O histórico depende de grafia.** Renomear divide os relatórios em duas pessoas e faz a edição de OS
   antigas falhar (`Vendedor inválido`).
4. **Ninguém pode sair da lista** sem travar a edição das OS antigas dessa pessoa.
5. **`"Aguardando definicao"` é um técnico fictício** e aparece no gráfico de lucro por técnico.
6. **O técnico não é validado no backend**, só na tela.
7. **Exclusão física de usuário (KI-079)** sem checar referências; sem FK, o banco não impede.
8. **Perfil único:** a tabela de usuários não representa "vendedor que também é técnico".
9. **Sem integridade referencial no banco.** Nenhuma tabela declara `REFERENCES` e `PRAGMA foreign_keys`
   não é ligado. Este plano não muda isso (ADR-016 §8).

### 1.4 Estado do banco de produção

- O banco de produção foi **recriado do zero em 2026-11-06** (servidor próprio, ADR-015), com dados
  criados pela tela atual.
- A integração MercadoPhone está desligada desde o PR #71.
- Expectativa: os nomes em `os.vendedor`/`os.tecnico` são exatamente os da lista. **Isso precisa ser
  confirmado, não presumido**, pelo diagnóstico da §5.1 rodado numa **cópia**.

---

## 2. Alternativas (decidido: C — ADR-016)

| | A: usar `usuarios` | B: equipe sem vínculo | **C: equipe + vínculo opcional** |
|---|---|---|---|
| Funcionário sem acesso | login e senha inventados na tabela de autenticação | ✓ | ✓ |
| Duas funções | não dá (perfil único) | ✓ | ✓ |
| Desligado sem perder histórico | `DELETE` de usuário (KI-079) apagaria o histórico | ✓ | ✓ |
| Unificar OS + Venda no futuro | ✓ | ✗ | ✓ |
| Mexe em autenticação | sim | não | não |

Comparação detalhada e consequências: `docs/engineering/adr/ADR-016.md`.

---

## 3. Modelo de dados

### 3.1 Nova tabela `colaboradores`

```sql
CREATE TABLE IF NOT EXISTS colaboradores (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    nome             TEXT    NOT NULL,
    identificacao    TEXT    NOT NULL DEFAULT '',   -- complemento p/ homônimos: sobrenome, apelido, código interno
    usuario_id       INTEGER,                       -- opcional; vínculo com login
    atua_tecnico     INTEGER NOT NULL DEFAULT 0,    -- 0/1
    atua_vendedor    INTEGER NOT NULL DEFAULT 0,    -- 0/1
    ativo            INTEGER NOT NULL DEFAULT 1,    -- 0 = inativo/desligado
    desligado_em     TEXT,                          -- data informativa do desligamento
    unificado_em_id  INTEGER,                       -- preenchido quando este cadastro foi unificado em outro (BR-110)
    criado_em        TEXT    NOT NULL DEFAULT (datetime('now')),
    atualizado_em    TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_colaboradores_nome ON colaboradores (nome COLLATE NOCASE);
CREATE UNIQUE INDEX IF NOT EXISTS idx_colaboradores_usuario_id ON colaboradores (usuario_id)
    WHERE usuario_id IS NOT NULL;
```

- **`nome` não é único** (Q3, BR-106). O índice serve para a busca de semelhantes.
- `identificacao` é o complemento exibido junto do nome quando há homônimos
  (`"Camila — Centro"`, `"Camila Souza"`).
- `usuario_id` é único e parcial: um usuário corresponde a no máximo um colaborador.
- `unificado_em_id` mantém o rastro da unificação; o cadastro descartado nunca é apagado (BR-110).
- Sem `CHECK` nem FK, seguindo o padrão atual do schema. O padrão de integridade é tema da frente 2.

### 3.2 Colunas novas em `os`

```sql
ALTER TABLE os ADD COLUMN tecnico_id  INTEGER;   -- NULL = sem técnico (BR-108)
ALTER TABLE os ADD COLUMN vendedor_id INTEGER;   -- NULL = sem vendedor (ex.: OS interna)
CREATE INDEX IF NOT EXISTS idx_os_tecnico_id  ON os (tecnico_id);
CREATE INDEX IF NOT EXISTS idx_os_vendedor_id ON os (vendedor_id);
```

As colunas nascem **nulas** e só o backfill da §5 as preenche.

### 3.3 Snapshot histórico (BR-109)

`os.tecnico` e `os.vendedor` continuam existindo e passam a ser o **nome gravado no momento em que a OS
foi salva**, como `vendas_itens.produto_nome` e `os_pecas.peca_descricao`.

- O snapshot é escrito **somente** quando a OS é salva com aquele colaborador (criação, ou troca de
  pessoa na edição).
- Ele **nunca** é reescrito por renomeação, inativação ou unificação do colaborador.
- Editar outros campos da OS **não** atualiza o snapshot: se a pessoa não mudou, o nome histórico fica.

| Momento | Cadastro | OS antiga | OS nova |
|---|---|---|---|
| OS criada | Isaque Souza | Isaque Souza | — |
| Colaborador renomeado | Isaque S. | **Isaque Souza** | Isaque S. |
| Relatório do mês | — | agrupado no `tecnico_id` do Isaque, rótulo "Isaque S." | idem |

| Onde | Usa |
|---|---|
| OS: detalhe, lista, Kanban, PDF de entrada/entrega, painel de garantias | snapshot |
| Relatórios, dashboard, filtros | id; rótulo = nome atual (+ `identificacao` se houver homônimo); sem id → texto do snapshot |

### 3.4 Usuário × colaborador (BR-107)

- `perfil` (acesso) e `atua_tecnico`/`atua_vendedor` (função na OS) são independentes.
- `PERFIS_OPCOES` e as checagens de perfil existentes não mudam.
- Inativar usuário não toca o colaborador, e vice-versa.

---

## 4. Regras de negócio

Aprovadas e registradas em `docs/product/BUSINESS_RULES.md`:

| BR | Resumo |
|---|---|
| BR-106 | Cadastro de colaboradores; funções técnico/vendedor; vínculo opcional; homônimos permitidos com aviso de nome completo duplicado; permissão gerenciar equipe (admin por padrão) |
| BR-107 | Colaborador com OS não é excluído, é inativado; inativo não recebe novas OS; usuário e colaborador independentes |
| BR-108 | OS pode ser criada, salva e editada sem técnico, mas **não finalizada**; atribuição só com colaborador ativo e com a função; na edição, quem já está gravado pode permanecer; indicadores de OS sem técnico |
| BR-109 | Nome na OS é snapshot histórico; relatórios agrupam por pessoa com nome atual |
| BR-110 | Unificação de duplicados: admin, confirmação, transacional, auditada, sem apagar histórico |
| BR-111 | Trocar técnico/vendedor de OS finalizada: só admin, com justificativa obrigatória e auditoria |

---

## 5. Migration `m0010` e migração dos registros

### 5.1 Pré-condições (bloqueiam o merge do PR 2)

1. **Backup verificável** do banco de produção feito pelo CTO imediatamente antes do merge:
   - cópia com `sqlite3 database.db ".backup backup-pre-m0010.db"`, ou `scripts/backup_pre_update.py`;
   - abrir a cópia e rodar `PRAGMA integrity_check` (deve dar `ok`);
   - conferir `SELECT COUNT(*)` de `os`, `vendas` e `usuarios` contra o banco vivo.

   O backup automático do Watchtower (`pre-update`, ADR-015) continua existindo, mas **não substitui**
   este backup conferido.
2. **Diagnóstico read-only numa cópia**:

```sql
SELECT tecnico, COUNT(*) FROM os GROUP BY tecnico ORDER BY 2 DESC;
SELECT vendedor, COUNT(*) FROM os GROUP BY vendedor ORDER BY 2 DESC;
SELECT upper(trim(tecnico)) n, COUNT(DISTINCT tecnico) FROM os GROUP BY n HAVING COUNT(DISTINCT tecnico) > 1;
SELECT upper(trim(vendedor)) n, COUNT(DISTINCT vendedor) FROM os GROUP BY n HAVING COUNT(DISTINCT vendedor) > 1;
SELECT id, nome, perfil, ativo FROM usuarios ORDER BY nome;
```

3. **Ensaio da `m0010` na cópia** + verificações da §5.5. O resultado é apresentado ao PO.
4. **Revisão explícita do PO** sobre o resultado do ensaio.

Os nomes e resultados ficam com o CTO; não vão para o repositório nem para o PR.

### 5.2 O que a `m0010` faz (aditiva, idempotente, numa transação)

1. `CREATE TABLE colaboradores` + índices, se não existirem.
2. `ALTER TABLE os ADD COLUMN tecnico_id` / `vendedor_id` (nulas) + índices, se não existirem.
3. **Backfill só a partir dos nomes encontrados nas OS** (Q2), sem nenhuma lista embutida:
   - junta os nomes distintos de `os.tecnico` e `os.vendedor`, comparados com `trim` e sem diferenciar
     maiúsculas; **acentos não são unificados**;
   - ignora vazio e `NULL`; `"Aguardando definicao"` (qualquer caixa, com ou sem acento) = sem técnico;
   - cria **um** colaborador por nome normalizado. `nome` recebe a grafia mais frequente;
     `atua_tecnico = 1` se o nome aparece em `os.tecnico`, `atua_vendedor = 1` se aparece em
     `os.vendedor`; `ativo = 1`; `usuario_id` e `identificacao` ficam vazios;
   - preenche `os.tecnico_id`/`vendedor_id` das OS correspondentes. As demais ficam nulas.
4. **Não altera nenhuma outra coluna de `os`** (snapshot, valores e datas intactos) e não toca em nenhuma
   outra tabela.
5. **Não vincula usuários automaticamente.** O vínculo é feito pelo admin na tela.
6. Idempotência: se `colaboradores` já tem linhas, o passo 3 não roda de novo, e só preenche ids
   que estejam nulos.

Uma instalação nova termina com `colaboradores` vazia: os nomes da loja atual não viajam para outra
instalação.

### 5.3 Depois do deploy (checklist do admin)

- Cadastrar as pessoas que estão na lista fixa mas nunca apareceram numa OS (Q2).
- Vincular os colaboradores aos usuários existentes, quando for o caso.
- Preencher `identificacao` onde houver homônimo.
- Unificar eventuais duplicados revelados pelo diagnóstico (BR-110).

### 5.4 Casos especiais do backfill

| Caso | Tratamento |
|---|---|
| `"Aguardando definicao"` | `tecnico_id = NULL`; snapshot mantido |
| Texto vazio ou `NULL` | id `NULL` |
| `"Camila"` e `"camila "` | mesmo colaborador |
| `"Taina"` e `"Tainá"` | dois colaboradores; o admin unifica depois (BR-110) |
| Mesmo nome como técnico e vendedor | um colaborador com as duas flags |
| Duas pessoas reais com o mesmo nome no histórico | indistinguíveis no texto: viram um colaborador; o histórico textual continua igual. Limitação inerente ao dado de origem, registrada aqui |
| OS interna (`vendedor = ''`) | `vendedor_id = NULL` |

### 5.5 Verificação pós-migração (no teste automatizado e no ensaio)

- `COUNT(*) FROM os` igual antes e depois.
- Checksum de todas as colunas pré-existentes de `os` igual antes e depois.
- Toda OS com texto preenchido e diferente do placeholder tem id.
- Totais do dashboard e do relatório de técnicos do mês corrente iguais antes e depois. Exceção: o
  placeholder sai do gráfico de técnicos e passa a "OS sem técnico".

---

## 6. Impacto no backend (PR 2)

### 6.1 Arquivos

| Arquivo | Mudança |
|---|---|
| `migrations/versions/m0010_colaboradores.py` + `migrations/registry.py` | migration (§5) |
| `fluxoly_colaboradores_{repository,service,controller}.py` (novos) | camadas no padrão de `clientes`/`tipos_garantia` (§6.3) |
| `fluxoly_core.py` | permissão nomeada (§6.2) |
| `fluxoly_blueprint_registry.py` | registra o blueprint; `vendedores`/`tecnicos` passam a vir do banco |
| `api_os.py` | criação e edição por id (§6.4); técnico deixa de ser obrigatório para salvar, mas é exigido ao finalizar (BR-108) nas três rotas que finalizam (`POST /ordens`, `PUT /ordens/<id>`, `PATCH /ordens/<id>/status`); BR-111; filtros por id e "sem técnico"; resposta com ids |
| `fluxoly_os.py` | `vendedor_valido` passa a consultar colaboradores; documento usa o snapshot |
| `api_system.py` | dashboard por id com fallback por texto; nova contagem `os_sem_tecnico`; payload mantém as chaves atuais e acrescenta `id`; `/constantes` mantém `tecnicos`/`vendedores` (strings, ativos, vindas do banco) e acrescenta `equipe_tecnicos`/`equipe_vendedores` `[{id, nome, identificacao}]` |
| `fluxoly_reports.py` | relatório de técnicos por id, nome atual; vazio = "Sem técnico" |
| `fluxoly_mercadophone.py` | recebe a lista de nomes vinda do banco no lugar da constante; nada mais |
| `fluxoly_reference_data.py` | `VENDEDORES`/`TECNICOS` deixam de ser usados; remoção só no PR 4 |
| `api_users.py` | não muda no PR 2 (o KI-079 está no PR 1) |

### 6.2 Permissão `gerenciar_equipe` (Q7)

O sistema hoje só tem perfis fixos, sem tabela de permissões. Para não criar agora um modelo de
permissões completo (fora de escopo), o PR 2 introduz o mínimo extensível:

```python
# fluxoly_core.py
PERMISSOES_POR_PERFIL = {
    "gerenciar_equipe": frozenset({"admin"}),
}

def tem_permissao(perfil, permissao):
    return perfil in PERMISSOES_POR_PERFIL.get(permissao, frozenset())
```

- As rotas de escrita da Equipe checam `tem_permissao(perfil, "gerenciar_equipe")`, nunca
  `perfil == "admin"`.
- Conceder a outro perfil = acrescentar no conjunto. Torná-lo configurável em tela é um passo futuro
  (ADR-016, condição de revisão).
- A leitura da lista **ativa** fica liberada para qualquer perfil autenticado, porque é preciso para
  montar os selects da OS. A listagem completa (inativos, vínculos) exige a permissão.

### 6.3 Endpoints da Equipe

| Método e rota | Permissão | Comportamento |
|---|---|---|
| `GET /api/colaboradores?ativos=1&funcao=tecnico` | autenticado | lista ativa para selects |
| `GET /api/colaboradores?todos=1` | gerenciar_equipe | lista completa com status e vínculo |
| `GET /api/colaboradores/<id>/vinculos` | gerenciar_equipe | nº de OS como técnico/vendedor, usuário vinculado |
| `POST /api/colaboradores` | gerenciar_equipe | cria; se houver nome duplicado e o corpo não trouxer `confirmar_duplicado: true`, responde **409** com `duplicados: [{id, nome, identificacao, ativo}]` |
| `PUT /api/colaboradores/<id>` | gerenciar_equipe | edita nome, identificacao, funções, vínculo; mesma regra de duplicado ao renomear (o próprio registro é ignorado); `usuario_id` precisa existir e estar livre |
| `POST /api/colaboradores/<id>/inativar` e `/reativar` | gerenciar_equipe | `ativo` + `desligado_em` |
| `DELETE /api/colaboradores/<id>` | gerenciar_equipe | só sem OS (contagem e exclusão na mesma transação, como no KI-067); com OS → 409 "inative" |
| `POST /api/colaboradores/<id>/unificar` `{manter_id, confirmar: true}` | gerenciar_equipe | BR-110 (§6.5) |

Toda escrita é auditada (`registrar_log_auditoria`, entidade `colaborador`, ações existentes:
`create`/`update`/`delete`/`status_change`).

**Nome duplicado (BR-106, Q11):** os dois nomes completos são iguais depois de normalizados, e só isso.
A normalização:

1. remove acentos (`unicodedata` NFKD, descartando as marcas combinantes);
2. converte para minúsculas;
3. remove espaços nas pontas e reduz espaços internos repetidos a um só.

A comparação inclui colaboradores ativos e inativos. Não compara primeiro nome, não usa fuzzy matching
nem procura um nome contido no outro.

| Existente | Novo | Resultado |
|---|---|---|
| Isaque Souza | ISAQUE SOUZA | avisa |
| Isaque Souza | Isáque  Souza | avisa |
| Camila Santos | Camila Oliveira | não avisa |
| Camila Santos | Camila Santos Silva | não avisa |

`fluxoly_core.normalizar_busca_texto` **não** é reaproveitado sem ajuste, porque também troca `-` e `/`
por espaço. O PR 2 decide entre usar uma função própria de nome ou parametrizar a existente (sem
duplicar a lógica de remover acento) e cobre os quatro exemplos acima em teste.

### 6.4 OS: criação e edição

- Aceita `tecnico_id`/`vendedor_id`, ambos opcionais para criar, salvar e editar (BR-108).
- **Finalizar exige técnico (Q10, BR-108).** Vale para toda transição para "Finalizado" sem técnico
  atribuído (`tecnico_id` nulo):
  - `POST /ordens` já com status finalizado;
  - `PUT /ordens/<id>` mudando o status para finalizado;
  - `PATCH /ordens/<id>/status` (inclui o Kanban);
  - reabrir e finalizar de novo.

  Responde **400** com "Atribua um técnico à OS antes de finalizá-la." e não altera nada (nem status,
  nem garantia, nem estoque). A checagem vem **antes** de qualquer efeito da finalização (concessão de
  garantia, BR-105, baixa de peças).
  - Vale também para OS interna (BR-090): a regra é sobre o serviço executado, não sobre o cliente.
  - OS que **já estão finalizadas** sem técnico (antigas, "Aguardando definicao") não são bloqueadas:
    editar outros campos continua permitido, porque a regra é sobre a transição. Atribuir técnico a uma
    delas segue a BR-111.
- Valida que o colaborador existe, está ativo e tem a função. **Exceção:** na edição, o id já gravado é
  aceito mesmo inativo.
- Grava o id e o snapshot do nome, mas o snapshot só é atualizado quando o id muda (BR-109).
- **BR-111:** se a OS está finalizada e `tecnico_id` ou `vendedor_id` muda:
  - exige perfil `admin` (403 para os demais);
  - exige `justificativa` não vazia (400);
  - registra a auditoria `update` da OS com `antes`/`depois` = `{tecnico_id, tecnico, vendedor_id,
    vendedor}` e `depois.justificativa`;
  - a justificativa vai dentro do JSON da auditoria, sem coluna nova em `audit_log`.

  As demais edições de OS finalizada seguem **exatamente como hoje** (Q9): troca e acréscimo de reparo
  (KI-078), peças, valores, termo (BR-105), correção de garantia (BR-065). O teste de regressão confirma
  que esses fluxos não passaram a pedir justificativa nem admin.
- **Transição** (até o PR 4): continua aceitando `tecnico`/`vendedor` por nome. O backend resolve para o
  id de um colaborador ativo com aquele nome. Se houver homônimo ambíguo ou nenhum, responde
  `400` pedindo o id. É a ponte com o frontend atual.

### 6.5 Unificação (BR-110), numa transação

1. Valida: dois ids distintos e existentes, `confirmar: true`, descartado ainda não unificado, sem
   conflito de usuários (os dois com usuários diferentes → 409).
2. `UPDATE os SET tecnico_id = :manter WHERE tecnico_id = :descartado` e o mesmo para `vendedor_id`.
   **Os textos de snapshot não são tocados.**
3. O mantido herda as funções (OU lógico) e o `usuario_id` se só o descartado tinha.
4. O descartado fica `ativo = 0`, `unificado_em_id = :manter`.
5. Auditoria nos dois cadastros: quem, quando, ids, quantas OS foram transferidas.
6. Erro em qualquer passo → rollback total.

---

## 7. Impacto no frontend (PR 3)

- **Tela Equipe**, visível só para quem tem a permissão: o backend informa isso, e o frontend não decide
  sozinho. Inclui:
  - lista com filtro ativo/inativo;
  - criar e editar com aviso de nome duplicado e confirmação ("são pessoas diferentes");
  - vínculo com usuário (select dos usuários sem vínculo);
  - inativar, reativar e excluir (só sem OS);
  - unificar, com os dois cadastros lado a lado, contagem de OS e confirmação.
- `NewOrder.jsx`: selects por id, só ativos, com a opção "Sem técnico".
- `EditOrder.jsx`:
  - a pessoa gravada aparece como "Nome (inativo)" se inativa e é mantida (BR-108);
  - em OS finalizada, trocar técnico ou vendedor só é possível para admin e abre um campo de
    justificativa obrigatória (BR-111).
- Finalizar sem técnico (formulário ou arraste no Kanban): exibe a mensagem do backend ("Atribua um
  técnico à OS antes de finalizá-la."). A tela pode avisar antes, mas **a regra vive no backend** (Q10).
- `Orders.jsx` / `OrderFilters.jsx`: filtros por id, com opções vindas da Equipe, mais a opção "Sem
  técnico".
- `Dashboard.jsx`: filtro de técnico por id; indicador "OS sem técnico".
- `OrderTable`, `Kanban`, `osPdf`: continuam exibindo o snapshot; OS sem técnico mostra "Sem técnico".
- **Fallback:** sem `equipe_*` (backend antigo), usa as listas de strings. Vercel e Watchtower não
  atualizam juntos.
- `scripts/seed_demo.py`: colaboradores **fictícios** no lugar dos nomes reais.

---

## 8. Rollback

O ponto central do desenho é que **o código anterior funciona sobre o banco migrado**: a migration só
acrescenta, e o código novo continua gravando o snapshot, que é tudo o que o código antigo lê.

| Situação | Ação |
|---|---|
| Problema no backend | fixar a imagem anterior (`:<sha>` no GHCR, ADR-015) ou revert do PR; o banco fica; o código antigo ignora as colunas novas |
| Problema no frontend | reverter o deploy na Vercel; o backend novo aceita o payload antigo |
| Desfazer o schema (último caso, com backup e aprovação do PO) | `DROP TABLE colaboradores; DROP INDEX idx_os_tecnico_id; DROP INDEX idx_os_vendedor_id; ALTER TABLE os DROP COLUMN tecnico_id; ALTER TABLE os DROP COLUMN vendedor_id;` (SQLite ≥ 3.35) e `DELETE FROM schema_migrations WHERE id = '0010'` |
| Erro grave de dados | restaurar o backup verificado da §5.1 |

**Limitações conhecidas do rollback de código:**

1. Um colaborador **novo** usado numa OS depois do deploy faz o código antigo recusar a edição dessa OS
   ("Vendedor inválido"), porque o nome não está na constante. O efeito é contido e por isso as
   constantes só saem no PR 4.
2. OS salvas **sem técnico** (BR-108) depois do deploy não podem ser editadas pelo código antigo sem
   escolher um técnico, porque o código antigo exige técnico. Também é contido.
3. O código antigo não tem a trava de finalizar sem técnico (Q10). Na prática a trava continua valendo,
   porque o código antigo já exige técnico para qualquer gravação.

---

## 9. Testes automatizados

Banco temporário; nenhum teste toca `database.db`.

**`tests/test_migration_m0010.py`**
- banco vazio → tabela criada, 0 colaboradores;
- backfill: distinct, trim e caixa, grafia mais frequente, flags, pessoa nas duas funções;
- placeholder e vazio → `NULL`;
- acentos distintos → dois registros;
- idempotência: rodar duas vezes não duplica nem reescreve;
- **contagem e checksum das colunas pré-existentes de `os` inalterados**;
- nenhuma outra tabela alterada;
- OS interna sem vendedor.

**`tests/test_colaboradores.py`**
- CRUD;
- permissões: sem sessão 401; perfis sem `gerenciar_equipe` 403 nas escritas e na lista completa; lista
  ativa liberada; `tem_permissao` com perfil concedido;
- homônimos aceitos;
- aviso de duplicado (409 sem confirmação, 201 com confirmação) nos quatro exemplos da §6.3: caixa e
  acento avisam; sobrenome diferente e nome contido não avisam; espaços excedentes avisam; renomear o
  próprio registro não avisa;
- `usuario_id` inexistente ou já vinculado recusado;
- inativar e reativar sem tocar no usuário, e inativar usuário sem tocar no colaborador (BR-107);
- exclusão recusada com OS e permitida sem;
- auditoria em toda escrita.

**`tests/test_colaboradores_unificacao.py`**
- transfere as OS e preserva os snapshots;
- herda funções e usuário;
- descartado inativo e marcado;
- recusa sem confirmação, com conflito de usuários, com o mesmo id ou já unificado;
- rollback total se um passo falhar;
- auditoria nos dois cadastros.

**`tests/test_os_equipe.py`**
- criar com ids e sem técnico;
- **Q10:** finalizar sem técnico → 400 com a mensagem, sem nenhum efeito (status, garantia, estoque
  inalterados) nas três rotas: `POST` já finalizada, `PUT` com status finalizado, `PATCH /status`;
  reabrir e finalizar de novo sem técnico → 400; OS interna também bloqueada; finalizar com técnico →
  200; OS antiga já finalizada sem técnico continua editável em outros campos;
- recusar colaborador inativo ou sem a função;
- manter inativo na edição e recusar troca por inativo;
- snapshot gravado na criação e não reescrito por renomeação nem por edição de outros campos;
- BR-111: técnico 403 ao trocar em OS finalizada; admin sem justificativa 400; admin com justificativa
  200 + auditoria com antes, depois e justificativa;
- **regressão Q9:** em OS finalizada, troca de reparo (KI-078), termo (BR-105) e correção de garantia
  (BR-065) seguem com as mesmas permissões de hoje e sem justificativa;
- payload legado por nome aceito e ambiguidade → 400;
- filtros por id e "sem técnico".

**Dashboard e relatórios**
- agrupamento por id;
- fallback por texto;
- renomeação unifica o histórico e mantém o snapshot;
- `os_sem_tecnico`;
- vendedor continua sem lucro (BR-100);
- chaves antigas preservadas.

**Outros**
- `/api/constantes`: chaves antigas e novas, só ativos;
- ajuste de `tests/conftest.py` e dos testes que criam OS com nomes da constante.

**Frontend (vitest)**
- tela Equipe: lista, semelhante, vínculo, inativar, unificar;
- NewOrder e EditOrder: id, "Sem técnico", inativo exibido, justificativa em OS finalizada, mensagem ao
  finalizar sem técnico (formulário e Kanban);
- filtros;
- fallback sem `equipe_*`;
- Dashboard e App ajustados.

**Gates:** suíte completa backend e frontend, ruff/isort/black, eslint e build. As 5 falhas do KI-030 só
no Windows local, como hoje.

---

## 10. Sequência de PRs

| PR | Branch | Conteúdo | Condição de merge |
|---|---|---|---|
| 1 | `fix/bloquear-exclusao-usuario-referenciado` | **KI-079 apenas**: guarda no backend contra exclusão física de usuário com qualquer referência (inventário no KI-079), mensagem orientando a inativar, testes de regressão. Revisão dos outros pontos de exclusão física; cada problema confirmado vira KI próprio, **sem correção neste PR** | testes verdes + revisão do PO |
| 2 | `feat/equipe-backend` | `m0010`, colaboradores, permissão, OS, dashboard e relatórios por id, compatibilidade com o frontend atual | **§5.1 completa** (backup verificado, diagnóstico, ensaio, revisão explícita do PO) |
| 3 | `feat/equipe-frontend` | tela Equipe, selects e filtros por id, justificativa, seed fictício | PR 2 estável em produção |
| 4 | `refactor/remover-listas-fixas-equipe` | remover `VENDEDORES`/`TECNICOS`, chaves legadas de `/constantes`, payload por nome | estabilização + confirmação do PO |

Os PRs 2 e 3 vão para produção na hora do merge (Watchtower e Vercel). Por isso o PR 2 precisa funcionar
sozinho, com o frontend atual.

**Fora de escopo** (frentes próprias):
- Venda apontando para colaborador;
- comissão de OS;
- FKs e `PRAGMA foreign_keys`;
- remoção do MercadoPhone;
- política geral de edição de OS finalizada (Q9: Discovery separada, aprovada);
- modelo de permissões configurável em tela.

---

## 11. Riscos e impactos em produção

| Risco | Prob. | Impacto | Mitigação |
|---|---|---|---|
| Migration roda no boot assim que o PR 2 é mergeado | certa | alto se falhar | §5.1 obrigatória; migration transacional e idempotente; trava entre workers (KI-060); backup `pre-update` do Watchtower como segunda rede |
| Variante de nome divide uma pessoa | baixa | baixo | diagnóstico antes; unificação (BR-110) depois; snapshot intacto |
| Frontend e backend em versões diferentes | média | baixo | payload legado aceito; fallback no frontend |
| Totais do dashboard ou relatório mudam | baixa | médio | teste de equivalência; conferência no ensaio (§5.5) |
| OS sem técnico some de algum indicador | média | médio | indicador `os_sem_tecnico` e opção de filtro explícitos |
| Trava de finalização (Q10) surpreende a loja no Kanban | média | baixo | mensagem clara do backend; OS com "Aguardando definicao" aberta precisa de técnico antes de finalizar (comunicar no deploy) |
| Trava de finalização aplicada depois de algum efeito colateral | baixa | alto | checagem antes de garantia e estoque; teste confirma "nenhum efeito" nas três rotas |
| Admin troca técnico de OS finalizada sem contexto | baixa | baixo | justificativa obrigatória + auditoria (BR-111) |
| Unificação errada | baixa | médio | confirmação com vínculos visíveis; descartado preservado e marcado; auditoria |
| Rollback de código após uso de colaborador novo ou OS sem técnico | baixa | baixo | constantes mantidas até o PR 4; limitações descritas na §8 |
| Exclusão de usuário vinculado | baixa | médio | KI-079 resolvido antes (PR 1) |
| Desempenho | desprezível | — | consultas indexadas; o dashboard já carrega todas as OS (KI-005) |

---

## Questões em Aberto

Nenhuma. Q9, Q10 e Q11 foram decididas pelo PO em 2026-11-18 (ver "Registro das decisões do PO").
Pendência fora deste plano: Discovery da política geral de edição de OS finalizada (Q9).
