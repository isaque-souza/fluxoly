"""
fluxoly_clientes_service.py

Regra de negócio pura do domínio Clientes — não conhece Flask, `request`
nem `jsonify` (`docs/engineering/ENGINEERING_GUIDE.md` §3.1). Primeira
aplicação real da convenção controller → service → repository neste
projeto.

Responsabilidade: entidade Cliente — cadastro mínimo viável (nome +
telefone ou e-mail), busca/paginação, e a regra de que um cliente com
histórico (OS, venda ou compra por troca vinculada) não pode ser excluído --
é inativado (BR-024, KI-066).

Tabelas usadas: `clientes` (via `fluxoly_clientes_repository.py`), leitura
de `os`/`vendas`/`compras_aparelhos.cliente_id` para checar histórico antes de excluir.

Depende de: `fluxoly_clientes_repository.py` (SQL), `fluxoly_audit.py`
(auditoria — create/update/delete).
"""

import sqlite3

import fluxoly_clientes_repository as repo
from fluxoly_audit import registrar_log_auditoria

PAGINA_PADRAO = 1
POR_PAGINA_PADRAO = 20

# KI-066: situação na listagem. O padrão é "ativos" porque os seletores de nova operação (venda,
# compra por troca) chamam a listagem sem filtro -- a tela de Clientes pede "todos"/"inativos".
STATUS_VALIDOS = ("ativos", "inativos", "todos")
STATUS_PADRAO = "ativos"

MSG_CLIENTE_INATIVO = "Cliente inativo — reative o cadastro para usá-lo em uma nova operação."

# KI-067: venda, compra por troca, inativação/reativação e exclusão disputam a mesma regra (BR-024b).
# Cada uma abre a transação com BEGIN IMMEDIATE, que pega a trava de escrita do SQLite antes da primeira
# leitura: a checagem do cliente e a gravação que depende dela ficam na mesma conexão e transação, e as
# operações concorrentes entram em fila (busy_timeout de app.py). Quem entra depois lê o que o primeiro
# gravou. Se a fila passar do busy_timeout, a operação é recusada com esta mensagem (503), nunca 500.
MSG_ESCRITA_OCUPADA = "O sistema está ocupado com outra operação. Tente novamente em instantes."

# KI-045: sentinel distinto de "" -- quem não pode ver o CPF/CNPJ atual (session sem admin/financeiro)
# não recebe o valor do GET, então "campo ausente na requisição de PUT" precisa significar "preservar o
# valor atual", não "limpar o campo" (que seria uma mutação silenciosa de um dado que essa sessão nunca
# chegou a ver). Só usado por `atualizar_cliente` -- `criar_cliente` não tem valor anterior a preservar.
CPF_NAO_INFORMADO = object()


def _cliente_para_dict(row):
    if not row:
        return None
    return {
        "id": row[0],
        "nome": row[1],
        "telefone": row[2] or "",
        "email": row[3] or "",
        "cpf_cnpj": row[4] or "",
        "observacoes": row[5] or "",
        "criado_em": row[6],
        "atualizado_em": row[7],
        "ativo": bool(row[8]),
    }


def _snapshot_auditoria(row):
    """Snapshot de cadastro para o audit_log -- sem `ativo`, que tem trilha própria (`status_change`)
    e, se entrasse aqui, apareceria como campo alterado em todo `update` (o `depois` não o carrega)."""
    dados = _cliente_para_dict(row)
    dados.pop("ativo", None)
    return dados


def listar_clientes(conectar, termo="", page=None, per_page=None, status=STATUS_PADRAO):
    """Retorna o dict paginado. `status` precisa estar em STATUS_VALIDOS (o controller valida)."""
    page = page or PAGINA_PADRAO
    per_page = per_page or POR_PAGINA_PADRAO
    offset = (max(1, page) - 1) * per_page

    conn = conectar()
    try:
        cursor = conn.cursor()
        total = repo.contar(cursor, termo, status)
        rows = repo.buscar_paginado(cursor, termo, per_page, offset, status)
    finally:
        conn.close()

    return {
        "items": [_cliente_para_dict(r) for r in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


def iniciar_transacao_de_escrita(cursor):
    """KI-067: abre a transação já com a trava de escrita -- precisa ser o primeiro comando da conexão."""
    cursor.execute("BEGIN IMMEDIATE")


def escrita_ocupada(exc):
    """KI-067: o SQLITE_BUSY que sobra depois do busy_timeout ("database is locked")."""
    return isinstance(exc, sqlite3.OperationalError) and "locked" in str(exc).lower()


def validar_cliente_na_transacao(cursor, cliente_id):
    """BR-024b / KI-067: o cliente existe e está ativo, lido no cursor da transação que vai gravar a
    venda ou a compra por troca. Retorna (row, erro)."""
    row = repo.buscar_por_id(cursor, cliente_id)
    if not row:
        return None, "Cliente não encontrado."
    if not row[8]:
        return row, MSG_CLIENTE_INATIVO
    return row, None


def obter_cliente(conectar, cliente_id):
    conn = conectar()
    try:
        cursor = conn.cursor()
        row = repo.buscar_por_id(cursor, cliente_id)
    finally:
        conn.close()
    return _cliente_para_dict(row)


def criar_cliente(conectar, usuario_id, nome, telefone="", email="", cpf_cnpj="", observacoes=""):
    """
    Retorna (cliente_id, erro). `erro` é None em caso de sucesso.

    Regra de cadastro mínimo viável (CLIENTES.md): nome obrigatório, e ao
    menos um contato (telefone OU e-mail) — sem isso o cliente não pode ser
    reencontrado depois.
    """
    nome = (nome or "").strip()
    telefone = (telefone or "").strip()
    email = (email or "").strip()
    cpf_cnpj = (cpf_cnpj or "").strip()
    observacoes = (observacoes or "").strip()

    if not nome:
        return None, "Nome é obrigatório."
    if not telefone and not email:
        return None, "Informe ao menos um contato (telefone ou e-mail)."

    conn = conectar()
    try:
        cursor = conn.cursor()
        cliente_id = repo.inserir(cursor, nome, telefone, email, cpf_cnpj, observacoes)
        registrar_log_auditoria(
            cursor,
            "cliente",
            cliente_id,
            usuario_id,
            "create",
            depois={"nome": nome, "telefone": telefone, "email": email, "cpf_cnpj": cpf_cnpj},
        )
        conn.commit()
    finally:
        conn.close()

    return cliente_id, None


def atualizar_cliente(
    conectar, usuario_id, cliente_id, nome, telefone="", email="", cpf_cnpj=CPF_NAO_INFORMADO, observacoes=""
):
    """Retorna (sucesso, erro). `erro` é None em caso de sucesso."""
    nome = (nome or "").strip()
    telefone = (telefone or "").strip()
    email = (email or "").strip()
    observacoes = (observacoes or "").strip()

    if not nome:
        return False, "Nome é obrigatório."
    if not telefone and not email:
        return False, "Informe ao menos um contato (telefone ou e-mail)."

    conn = conectar()
    try:
        cursor = conn.cursor()
        antes = repo.buscar_por_id(cursor, cliente_id)
        if not antes:
            return False, "Cliente não encontrado."

        cpf_cnpj = antes[4] or "" if cpf_cnpj is CPF_NAO_INFORMADO else (cpf_cnpj or "").strip()

        repo.atualizar(cursor, cliente_id, nome, telefone, email, cpf_cnpj, observacoes)
        registrar_log_auditoria(
            cursor,
            "cliente",
            cliente_id,
            usuario_id,
            "update",
            antes=_snapshot_auditoria(antes),
            depois={"nome": nome, "telefone": telefone, "email": email, "cpf_cnpj": cpf_cnpj},
        )
        conn.commit()
    finally:
        conn.close()

    return True, None


def excluir_cliente(conectar, usuario_id, cliente_id):
    """Retorna (sucesso, erro, vinculos). `erro` é None em caso de sucesso; `vinculos` é a contagem
    de OS/vendas/compras quando a exclusão foi recusada por histórico (senão None).

    BR-024 / KI-066: exclusão física só para cliente sem nenhum vínculo -- o schema não declara
    FOREIGN KEY, então apagar quem tem venda ou compra por troca deixaria o histórico sem titular
    (as leituras usam LEFT JOIN). Cliente com histórico é inativado (`inativar_cliente`)."""
    conn = conectar()
    try:
        cursor = conn.cursor()
        # KI-067: contagem de vínculos e DELETE na mesma transação de escrita -- uma venda ou compra
        # concorrente espera este commit (e é recusada) ou termina antes (e a contagem a enxerga: 409).
        iniciar_transacao_de_escrita(cursor)
        antes = repo.buscar_por_id(cursor, cliente_id)
        if not antes:
            return False, "Cliente não encontrado.", None

        vinculos = repo.contar_vinculos(cursor, cliente_id)
        if any(vinculos.values()):
            return (
                False,
                "Cliente possui histórico (OS, vendas ou compras) e não pode ser excluído. Inative o cliente.",
                vinculos,
            )

        repo.deletar(cursor, cliente_id)
        registrar_log_auditoria(cursor, "cliente", cliente_id, usuario_id, "delete", antes=_snapshot_auditoria(antes))
        conn.commit()
    except sqlite3.OperationalError as exc:
        conn.rollback()
        if not escrita_ocupada(exc):
            raise
        return False, MSG_ESCRITA_OCUPADA, None
    finally:
        conn.close()

    return True, None, None


def _definir_situacao(conectar, usuario_id, cliente_id, ativo):
    """Retorna (alterado, erro). Idempotente: se o cliente já está na situação pedida, não grava nada
    (nem auditoria) e devolve alterado=False. Só toca `clientes.ativo` -- vendas, OS, compras,
    garantias e recibos ficam exatamente como estavam (BR-024b)."""
    conn = conectar()
    try:
        cursor = conn.cursor()
        # KI-067: leitura da situação atual e UPDATE na mesma transação de escrita.
        iniciar_transacao_de_escrita(cursor)
        row = repo.buscar_por_id(cursor, cliente_id)
        if not row:
            return False, "Cliente não encontrado."
        atual = bool(row[8])
        if atual == ativo:
            return False, None

        repo.definir_ativo(cursor, cliente_id, ativo)
        registrar_log_auditoria(
            cursor,
            "cliente",
            cliente_id,
            usuario_id,
            "status_change",
            antes={"ativo": atual},
            depois={"ativo": ativo},
        )
        conn.commit()
    except sqlite3.OperationalError as exc:
        conn.rollback()
        if not escrita_ocupada(exc):
            raise
        return False, MSG_ESCRITA_OCUPADA
    finally:
        conn.close()
    return True, None


def inativar_cliente(conectar, usuario_id, cliente_id):
    """BR-024a: tira o cliente das novas operações sem apagar nada. Retorna (alterado, erro)."""
    return _definir_situacao(conectar, usuario_id, cliente_id, False)


def reativar_cliente(conectar, usuario_id, cliente_id):
    """BR-024c: devolve o cliente às novas operações, sem alterar o histórico. Retorna (alterado, erro)."""
    return _definir_situacao(conectar, usuario_id, cliente_id, True)


def validar_cliente_para_nova_operacao(conectar, cliente_id):
    """BR-024b: pré-checagem rápida (conexão própria) de quem cria venda/compra por troca, antes das
    demais validações. A checagem que vale é `validar_cliente_na_transacao`, repetida dentro da
    transação de escrita (KI-067). Retorna (cliente, erro)."""
    conn = conectar()
    try:
        row, erro = validar_cliente_na_transacao(conn.cursor(), cliente_id)
    finally:
        conn.close()
    if erro:
        return None, erro
    return _cliente_para_dict(row), None


def anonimizar_cliente(conectar, usuario_id, cliente_id):
    """Retorna (sucesso, erro). KI-044: mascara PII preservando o `id` e o histórico de OS/vendas
    vinculado -- complementa, não substitui, `excluir_cliente` (que continua servindo só para clientes
    órfãos, sem OS/venda vinculada, decisão do CTO em docs/engineering/plans/PLAN-LGPD-Compliance.md)."""
    conn = conectar()
    try:
        cursor = conn.cursor()
        antes = repo.buscar_por_id(cursor, cliente_id)
        if not antes:
            return False, "Cliente não encontrado."

        nome_placeholder = f"Cliente Anonimizado #{cliente_id}"
        repo.anonimizar(cursor, cliente_id, nome_placeholder)
        registrar_log_auditoria(
            cursor,
            "cliente",
            cliente_id,
            usuario_id,
            "anonymize",
            antes=_snapshot_auditoria(antes),
            depois={"nome": nome_placeholder, "telefone": "", "email": "", "cpf_cnpj": "", "observacoes": ""},
        )
        conn.commit()
    finally:
        conn.close()

    return True, None
