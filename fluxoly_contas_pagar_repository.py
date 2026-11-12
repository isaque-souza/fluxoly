"""
fluxoly_contas_pagar_repository.py

Único ponto de acesso SQL do domínio Contas a Pagar -- segue a convenção de
docs/engineering/ENGINEERING_GUIDE.md §3.1 (controller → service →
repository). Nenhuma regra de negócio aqui, só queries parametrizadas.

Tabela: `contas_pagar`. Nenhuma `FOREIGN KEY` declarada, mesma convenção do
resto do schema.

Depende de: nenhum outro módulo de domínio.
"""

_COLUNAS = "id, descricao, categoria, valor, data_vencimento, status, movimentacao_caixa_id, criado_em, atualizado_em"


def inserir(cursor, descricao, categoria, valor, data_vencimento):
    cursor.execute(
        """
        INSERT INTO contas_pagar (descricao, categoria, valor, data_vencimento)
        VALUES (?, ?, ?, ?)
        """,
        (descricao, categoria, valor, data_vencimento),
    )
    return cursor.lastrowid


def atualizar(cursor, conta_id, descricao, categoria, valor, data_vencimento):
    cursor.execute(
        """
        UPDATE contas_pagar
        SET descricao = ?, categoria = ?, valor = ?, data_vencimento = ?, atualizado_em = datetime('now')
        WHERE id = ? AND status = 'pendente'
        """,
        (descricao, categoria, valor, data_vencimento, conta_id),
    )
    return cursor.rowcount


def buscar_por_id(cursor, conta_id):
    cursor.execute(f"SELECT {_COLUNAS} FROM contas_pagar WHERE id = ?", (conta_id,))
    return cursor.fetchone()


def buscar_paginado(cursor, status, limit, offset):
    if status:
        cursor.execute(
            f"SELECT {_COLUNAS} FROM contas_pagar WHERE status = ? "
            "ORDER BY data_vencimento IS NULL, data_vencimento, id LIMIT ? OFFSET ?",
            (status, limit, offset),
        )
    else:
        cursor.execute(
            f"SELECT {_COLUNAS} FROM contas_pagar "
            "ORDER BY data_vencimento IS NULL, data_vencimento, id LIMIT ? OFFSET ?",
            (limit, offset),
        )
    return cursor.fetchall()


def contar(cursor, status):
    if status:
        cursor.execute("SELECT COUNT(*) FROM contas_pagar WHERE status = ?", (status,))
    else:
        cursor.execute("SELECT COUNT(*) FROM contas_pagar")
    return cursor.fetchone()[0] or 0


def marcar_como_pago(cursor, conta_id, movimentacao_caixa_id):
    cursor.execute(
        """
        UPDATE contas_pagar
        SET status = 'pago', movimentacao_caixa_id = ?, atualizado_em = datetime('now')
        WHERE id = ? AND status = 'pendente'
        """,
        (movimentacao_caixa_id, conta_id),
    )
    return cursor.rowcount


def cancelar(cursor, conta_id):
    cursor.execute(
        "UPDATE contas_pagar SET status = 'cancelado', atualizado_em = datetime('now') "
        "WHERE id = ? AND status = 'pendente'",
        (conta_id,),
    )
    return cursor.rowcount


def deletar(cursor, conta_id):
    cursor.execute("DELETE FROM contas_pagar WHERE id = ? AND status = 'pendente'", (conta_id,))
    return cursor.rowcount


def resumir_pendentes_por_vencimento(cursor, hoje):
    """Pendências da tela inicial (PLAN-pendencias-tela-inicial.md): (qtd, total) das contas pendentes
    vencidas (vencimento < hoje) e (qtd, total) das que vencem hoje. Conta sem vencimento fica fora."""
    cursor.execute(
        """
        SELECT COALESCE(SUM(data_vencimento < ?), 0),
               COALESCE(SUM(CASE WHEN data_vencimento < ? THEN valor END), 0),
               COALESCE(SUM(data_vencimento = ?), 0),
               COALESCE(SUM(CASE WHEN data_vencimento = ? THEN valor END), 0)
        FROM contas_pagar
        WHERE status = 'pendente' AND COALESCE(data_vencimento, '') != ''
        """,
        (hoje, hoje, hoje, hoje),
    )
    return cursor.fetchone()
