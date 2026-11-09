"""
Compra de aparelhos para conserto e revenda -- ver
docs/engineering/plans/PLAN-compra-aparelhos.md e BR-083 a BR-093
(docs/product/BUSINESS_RULES.md).

DDL puro e aditivo, sem backfill: tabela nova `compras_aparelhos`, índice
único parcial do Caixa para a saída de compra (BR-086) e a coluna
`os.unidade_serializada_id`, já preparada para a OS interna (BR-090, PR 3)
não precisar de outra migration.
"""

import sqlite3

ID = "0003"
DESCRICAO = "Compra de aparelhos: compras_aparelhos, saída de caixa única por compra, os.unidade_serializada_id"


def _coluna_existe(cursor, tabela, coluna):
    cursor.execute(f"PRAGMA table_info({tabela})")
    return any(row[1] == coluna for row in cursor.fetchall())


def apply(cursor: sqlite3.Cursor, conn: sqlite3.Connection) -> None:
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS compras_aparelhos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        unidade_serializada_id INTEGER NOT NULL,
        produto_id INTEGER NOT NULL,
        origem TEXT NOT NULL,
        cliente_id INTEGER,
        venda_id INTEGER,
        vendedor_nome TEXT,
        vendedor_telefone TEXT,
        valor_pago REAL NOT NULL,
        forma_pagamento TEXT NOT NULL,
        estado TEXT NOT NULL,
        defeito TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT 'ativa',
        motivo_cancelamento TEXT,
        cancelado_por INTEGER,
        cancelado_em TEXT,
        usuario_id INTEGER NOT NULL,
        criado_em TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """
    )
    # Uma unidade tem no máximo uma compra ativa -- guardião no banco, mesmo
    # padrão de idx_vendas_itens_unidade_ativa.
    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_compras_aparelhos_unidade_ativa "
        "ON compras_aparelhos (unidade_serializada_id) WHERE status = 'ativa'"
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_compras_aparelhos_criado_em ON compras_aparelhos (criado_em)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_compras_aparelhos_cliente_id ON compras_aparelhos (cliente_id)")

    # BR-086: uma compra nunca tem duas saídas de caixa ativas -- mesmo
    # guardião de BR-069 (idx_movimentacoes_caixa_venda_ativa).
    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_movimentacoes_caixa_compra_ativa "
        "ON movimentacoes_caixa (origem_id) WHERE origem = 'compra_aparelho' AND estornada = 0"
    )

    # BR-090 (OS interna, PR 3) -- coluna preparada aqui, ainda sem uso.
    if not _coluna_existe(cursor, "os", "unidade_serializada_id"):
        cursor.execute("ALTER TABLE os ADD COLUMN unidade_serializada_id INTEGER")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_os_unidade_serializada_id ON os (unidade_serializada_id)")
