"""
fluxoly_clientes_repository.py

Único ponto de acesso SQL do domínio Clientes — segue a convenção de
`docs/engineering/ENGINEERING_GUIDE.md` §3.1 (controller → service →
repository). Nenhuma regra de negócio aqui, só queries parametrizadas.

Tabela: `clientes`. Nenhuma `FOREIGN KEY` declarada, mesma convenção do
resto do schema (`docs/engineering/DATABASE.md` seção 3).

Depende de: nenhum outro módulo de domínio.
"""

_COLUNAS = "id, nome, telefone, email, cpf_cnpj, observacoes, criado_em, atualizado_em, ativo"

# KI-066: filtro de situação da listagem -- SQL literal por valor (nunca montado a partir da entrada).
_FILTRO_STATUS = {"ativos": "ativo = 1", "inativos": "ativo = 0", "todos": "1 = 1"}


def inserir(cursor, nome, telefone, email, cpf_cnpj, observacoes):
    cursor.execute(
        """
        INSERT INTO clientes (nome, telefone, email, cpf_cnpj, observacoes)
        VALUES (?, ?, ?, ?, ?)
        """,
        (nome, telefone, email, cpf_cnpj, observacoes),
    )
    return cursor.lastrowid


def atualizar(cursor, cliente_id, nome, telefone, email, cpf_cnpj, observacoes):
    cursor.execute(
        """
        UPDATE clientes
        SET nome = ?, telefone = ?, email = ?, cpf_cnpj = ?, observacoes = ?,
            atualizado_em = datetime('now')
        WHERE id = ?
        """,
        (nome, telefone, email, cpf_cnpj, observacoes, cliente_id),
    )


def buscar_por_id(cursor, cliente_id):
    cursor.execute(f"SELECT {_COLUNAS} FROM clientes WHERE id = ?", (cliente_id,))
    return cursor.fetchone()


def buscar_paginado(cursor, termo, limit, offset, status="ativos"):
    filtro = _FILTRO_STATUS[status]
    if termo:
        padrao = f"%{termo.lower()}%"
        cursor.execute(
            f"""
            SELECT {_COLUNAS} FROM clientes
            WHERE {filtro}
              AND (lower(nome) LIKE ? OR lower(COALESCE(telefone, '')) LIKE ? OR lower(COALESCE(cpf_cnpj, '')) LIKE ?)
            ORDER BY nome
            LIMIT ? OFFSET ?
            """,
            (padrao, padrao, padrao, limit, offset),
        )
    else:
        cursor.execute(
            f"SELECT {_COLUNAS} FROM clientes WHERE {filtro} ORDER BY nome LIMIT ? OFFSET ?", (limit, offset)
        )
    return cursor.fetchall()


def contar(cursor, termo, status="ativos"):
    filtro = _FILTRO_STATUS[status]
    if termo:
        padrao = f"%{termo.lower()}%"
        cursor.execute(
            f"""
            SELECT COUNT(*) FROM clientes
            WHERE {filtro}
              AND (lower(nome) LIKE ? OR lower(COALESCE(telefone, '')) LIKE ? OR lower(COALESCE(cpf_cnpj, '')) LIKE ?)
            """,
            (padrao, padrao, padrao),
        )
    else:
        cursor.execute(f"SELECT COUNT(*) FROM clientes WHERE {filtro}")
    return cursor.fetchone()[0] or 0


def possui_os_vinculada(cursor, cliente_id):
    cursor.execute("SELECT 1 FROM os WHERE cliente_id = ? LIMIT 1", (cliente_id,))
    return cursor.fetchone() is not None


def contar_vinculos(cursor, cliente_id):
    """KI-066: todo registro que aponta para o cliente -- o schema não declara FOREIGN KEY, então a
    exclusão física só é segura quando os três são zero (BR-024)."""
    vinculos = {}
    for tabela in ("os", "vendas", "compras_aparelhos"):
        cursor.execute(f"SELECT COUNT(*) FROM {tabela} WHERE cliente_id = ?", (cliente_id,))
        vinculos[tabela] = cursor.fetchone()[0] or 0
    return vinculos


def definir_ativo(cursor, cliente_id, ativo):
    cursor.execute(
        "UPDATE clientes SET ativo = ?, atualizado_em = datetime('now') WHERE id = ?",
        (1 if ativo else 0, cliente_id),
    )


def deletar(cursor, cliente_id):
    cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))


def anonimizar(cursor, cliente_id, nome_placeholder):
    """KI-044: mascara PII preservando o id (e, com ele, todo FK em os.cliente_id/vendas.cliente_id) --
    usada para clientes com histórico vinculado, onde `deletar` não é uma opção (`possui_os_vinculada`)."""
    cursor.execute(
        """
        UPDATE clientes
        SET nome = ?, telefone = NULL, email = NULL, cpf_cnpj = NULL, observacoes = '',
            atualizado_em = datetime('now')
        WHERE id = ?
        """,
        (nome_placeholder, cliente_id),
    )
